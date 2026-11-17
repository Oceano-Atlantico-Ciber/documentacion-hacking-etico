"""Órdenes de Docker con límite de tiempo y sin heredar el entorno, y limpieza del motor entre ejercicios."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Imágenes del curso: se descargan una vez por ejecución y sobreviven a la limpieza entre ejercicios.
BASE = ("nginx:1.27-alpine", "postgres:16-alpine", "python:3.12-alpine", "curlimages/curl:8.11.1", "aquasec/trivy:0.58.0")
# Solo PATH y HOME: ninguna variable del corrector puede acabar interpolada en un compose del alumno.
# En Windows (pruebas.py en el equipo del alumno) docker necesita además las carpetas del usuario y del
# sistema para encontrar Docker Desktop; en el corrector, que corre en Linux, no existen.
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
        """Última línea de error, que es la que explica el fallo."""
        lineas = [l for l in self.error.splitlines() if l.strip()]
        return lineas[-1].strip() if lineas else f"código {self.codigo}"


def docker(*args: str, cwd: Path | None = None, espera: int = 300) -> Salida:
    try:
        r = subprocess.run(["docker", *args], cwd=cwd, env=ENTORNO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=espera)
    except subprocess.TimeoutExpired:
        return Salida(124, "", f"docker {args[0]}: más de {espera} s sin terminar")
    return Salida(r.returncode, r.stdout, r.stderr)


def obligatorio(r: Salida) -> Salida:
    """Para órdenes del propio corrector: si fallan, es un error del corrector, no del alumno."""
    if r.codigo:
        raise RuntimeError(r.motivo)
    return r


def reintentar(orden: Callable[[], Salida], vale: Callable[[Salida], bool], segundos: int = 30) -> Salida:
    """Repite la orden hasta que vale o se agota el tiempo: los servicios tardan en aceptar conexiones."""
    limite = time.monotonic() + segundos
    while not vale(r := orden()) and time.monotonic() < limite:
        time.sleep(1)
    return r


def contenedor(nombre: str) -> dict | None:
    r = docker("container", "inspect", nombre)
    return json.loads(r.salida)[0] if r.codigo == 0 else None


def http(url: str, segundos: int = 20) -> tuple[int, str]:
    """(código, cuerpo) de un GET desde el equipo que corrige; (0, motivo) si nadie responde."""
    limite = time.monotonic() + segundos
    while True:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except OSError as e:
            if time.monotonic() > limite:
                return 0, str(e)
            time.sleep(1)


def preparar_motor() -> None:
    for imagen in BASE:
        obligatorio(docker("pull", "-q", imagen, espera=600))


def limpiar() -> None:
    """Deja el motor como al empezar: sin contenedores, redes ni volúmenes, y solo con las imágenes BASE.
    Así un ejercicio no ve lo que dejó el anterior, ni una imagen sondeo:1.0 construida por otro alumno."""
    if ids := docker("ps", "-aq").salida.split():
        docker("rm", "-f", "-v", *ids)
    docker("network", "prune", "-f")
    docker("volume", "prune", "-af")
    refs = docker("image", "ls", "--format", "{{.Repository}}:{{.Tag}}").salida.split()
    if sobran := [r for r in refs if r not in BASE and "<none>" not in r]:
        docker("rmi", "-f", *sobran)  # por nombre: una imagen BASE con otro nombre más solo pierde ese nombre
    docker("image", "prune", "-f")
