"""Una Floci limpia para comprobar, y la CLI de AWS y Terraform contra ella, todo en contenedores.

Lo usan igual el corrector (en Linux, en GitHub Actions) y pruebas.py (en el Windows del alumno, con
Docker Desktop). EC2 y RDS van simulados (sin arrancar contenedores): se comprueba lo que la API dice
que existe y cómo está configurado, que es lo que describe el Terraform.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

FLOCI = "floci/floci:2.4.0"
AWS = "amazon/aws-cli:2.22.0"
TERRAFORM = "hashicorp/terraform:1.16.7"
BASE = (FLOCI, AWS, TERRAFORM)
RED = "iac-comprobar"
NOMBRE = "iac-comprobar-floci"
ENDPOINT = f"http://{NOMBRE}:4566"
REGION = "eu-west-1"
RAIZ = ("test", "test")  # la clave de administrador de Floci
# Solo lo imprescindible del entorno: en Linux, PATH y HOME; en Windows, además, lo que Docker Desktop necesita.
ENTORNO = {k: os.environ[k] for k in ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
                                      "SYSTEMROOT", "TEMP", "TMP") if k in os.environ}


class Fallo(Exception):
    """Lo entregado no permite seguir comprobando. El mensaje va tal cual al informe del alumno."""


@dataclass(frozen=True)
class Salida:
    codigo: int
    salida: str
    error: str

    @property
    def motivo(self) -> str:
        lineas = [l.strip() for l in self.error.splitlines() if l.strip() and not l.strip().startswith("│ ")] \
            or [l.strip(" │") for l in self.error.splitlines() if l.strip(" │")]
        return lineas[-1] if lineas else f"código {self.codigo}"

    @property
    def json(self):
        try:
            return json.loads(self.salida)
        except ValueError:
            return None


def docker(*args: str, espera: int = 300) -> Salida:
    try:
        r = subprocess.run(["docker", *args], env=ENTORNO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=espera)
    except subprocess.TimeoutExpired:
        return Salida(124, "", f"docker {args[0]}: más de {espera} s sin terminar")
    return Salida(r.returncode, r.stdout, r.stderr)


def obligatorio(r: Salida) -> Salida:
    """Para órdenes del propio corrector: si fallan, es un error del corrector, no del alumno."""
    if r.codigo:
        raise RuntimeError(r.motivo)
    return r


def preparar_motor() -> None:
    for imagen in BASE:
        obligatorio(docker("pull", "-q", imagen, espera=600))


def _montaje(carpeta: Path) -> str:
    return f"{Path(carpeta).resolve()}:/work"


class Floci:
    """Una cuenta AWS emulada nueva, con los permisos de IAM aplicados. Se usa con «with»."""

    def __enter__(self) -> "Floci":
        self.cerrar()
        obligatorio(docker("network", "create", RED))
        obligatorio(docker("run", "-d", "--name", NOMBRE, "--network", RED,
                           "-e", f"FLOCI_HOSTNAME={NOMBRE}", "-e", f"FLOCI_DEFAULT_REGION={REGION}",
                           "-e", "FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true",
                           "-e", "FLOCI_SERVICES_EC2_MOCK=true", "-e", "FLOCI_SERVICES_RDS_MOCK=true", FLOCI))
        limite = time.monotonic() + 90
        while self.aws("sts", "get-caller-identity").codigo:
            if time.monotonic() > limite:
                raise RuntimeError("Floci no arranca: " + docker("logs", "--tail", "5", NOMBRE).salida.strip())
            time.sleep(2)
        return self

    def __exit__(self, *_) -> None:
        self.cerrar()

    @staticmethod
    def cerrar() -> None:
        docker("rm", "-f", "-v", NOMBRE)
        docker("network", "rm", RED)

    def aws(self, *args: str, clave: tuple[str, str] = RAIZ, carpeta: Path | None = None) -> Salida:
        """La CLI de AWS contra esta Floci, como administrador o con la clave que se le dé."""
        montaje = ["-v", _montaje(carpeta), "-w", "/work"] if carpeta else []
        return docker("run", "--rm", "--network", RED, *montaje,
                      "-e", f"AWS_ACCESS_KEY_ID={clave[0]}", "-e", f"AWS_SECRET_ACCESS_KEY={clave[1]}",
                      "-e", f"AWS_DEFAULT_REGION={REGION}", "-e", f"AWS_ENDPOINT_URL={ENDPOINT}",
                      "-e", "AWS_PAGER=", AWS, *args, "--output", "json", espera=120)

    def terraform(self, carpeta: Path, *args: str, espera: int = 600) -> Salida:
        """Terraform en la carpeta del alumno, con el proveedor apuntando a esta Floci."""
        return docker("run", "--rm", "--network", RED, "-v", _montaje(carpeta), "-w", "/work",
                      "-v", "iac-comprobar-plugins:/plugins", "-e", "TF_PLUGIN_CACHE_DIR=/plugins",
                      "-e", "TF_IN_AUTOMATION=1", "-e", "TF_INPUT=0", "-e", "TF_VAR_floci=" + ENDPOINT,
                      "-e", "AWS_ACCESS_KEY_ID=test", "-e", "AWS_SECRET_ACCESS_KEY=test",
                      "-e", f"AWS_DEFAULT_REGION={REGION}", TERRAFORM, *args, espera=espera)

