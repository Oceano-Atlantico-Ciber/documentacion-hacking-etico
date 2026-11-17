#!/usr/bin/env python3
"""Deja los ficheros de partida de cada ejercicio de Terraform y AWS en tu repositorio de entregas.

Uso, desde cualquier carpeta de tu repositorio:

    py preparar.py e1        (Windows; en Linux o macOS, python3)

Escribe en fundamentos/iac/<ejercicio>/ y no hace commits. Los nombres de los recursos (buckets,
usuarios…) llevan una huella de tu usuario de GitHub, que se deduce del remoto origin
(entregas-<usuario>): cada alumno tiene los suyos. Este mismo módulo es el que usan el corrector y
pruebas.py para saber qué esperar, de modo que no hay que tocarlo.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = "fundamentos/iac"
EJERCICIOS = tuple(f"e{n}" for n in range(1, 9))
PLANTILLAS = Path(__file__).resolve().parent / "plantillas"
REGION = "eu-west-1"


def etiqueta(ejercicio: str) -> str:
    return f"entrega-fundamentos-iac-{ejercicio}"


def huella(usuario: str, que: str = "") -> str:
    """Ocho caracteres en minúscula que distinguen los recursos de cada alumno."""
    return hashlib.sha256(f"{usuario.lower()}:iac{que}".encode()).hexdigest()[:8]


# --- Lo esperado de cada alumno -----------------------------------------------------------

def e1_nombres(usuario: str) -> dict[str, str]:
    h = huella(usuario)
    return {"bucket": f"e1-notas-{h}", "objeto": "notas.txt", "usuario": f"lector-{h}"}


def e1_notas(usuario: str) -> str:
    return f"Notas de la auditoría de {usuario}\nReferencia: {huella(usuario, 'notas')}\n"


def empresa(usuario: str) -> dict[str, str]:
    """Nombres de la empresa ficticia del E2, E7 y E8."""
    h = huella(usuario)
    return {"copias": f"copias-{h}", "informes": f"informes-{h}", "secretos": f"secretos-{h}",
            "operaciones": f"operaciones-{h}", "becario": f"becario-{h}", "web": f"web-{h}"}


def e4_deriva(usuario: str) -> str:
    """La orden que «un compañero» lanza a mano en el E4: borra la política del lector."""
    n = e1_nombres(usuario)
    return f"aws iam delete-user-policy --user-name {n['usuario']} --policy-name lectura-notas"


def e5_pagina(usuario: str) -> str:
    return f"Laboratorio de {usuario} · {huella(usuario, 'lab')}"


# --- Ficheros de cada ejercicio ----------------------------------------------------------

def _plantilla(*ruta: str) -> str:
    return PLANTILLAS.joinpath(*ruta).read_text(encoding="utf-8")


def _empresa_tf(usuario: str) -> str:
    texto = _plantilla("empresa", "empresa.tf")
    for clave, valor in empresa(usuario).items():
        texto = texto.replace(f"{{{clave}}}", valor)
    return texto


def comunes() -> dict[str, str]:
    """Una sola Floci para toda la unidad, en fundamentos/iac/: lo del E1 sigue ahí en el E3."""
    return {"docker-compose.yml": _plantilla("docker-compose.yml"), ".gitignore": _plantilla("gitignore")}


def e1(usuario: str) -> dict[str, str]:
    n = e1_nombres(usuario)
    return {"notas.txt": e1_notas(usuario),
            "LEEME.md": _plantilla("e1", "LEEME.md").format(**n)}


def e2(usuario: str) -> dict[str, str]:
    return {"empresa/empresa.tf": _empresa_tf(usuario), "empresa/proveedor.tf": _plantilla("proveedor.tf")}


def e3(usuario: str) -> dict[str, str]:
    return {"proveedor.tf": _plantilla("proveedor.tf"),
            "LEEME.md": _plantilla("e3", "LEEME.md").format(**e1_nombres(usuario))}


def e4(usuario: str) -> dict[str, str]:
    return {"LEEME.md": _plantilla("e4", "LEEME.md").format(deriva=e4_deriva(usuario))}


def e5(usuario: str) -> dict[str, str]:
    return {"proveedor.tf": _plantilla("proveedor.tf"),
            "LEEME.md": _plantilla("e5", "LEEME.md").format(pagina=e5_pagina(usuario))}


def e6(usuario: str) -> dict[str, str]:
    return {}


def e7(usuario: str) -> dict[str, str]:
    return {"empresa/empresa.tf": _empresa_tf(usuario), "empresa/proveedor.tf": _plantilla("proveedor.tf"),
            "LEEME.md": _plantilla("e7", "LEEME.md").format(**empresa(usuario))}


def e8(usuario: str) -> dict[str, str]:
    return {}


ESCENARIOS = {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e6": e6, "e7": e7, "e8": e8}
# Los que siguen sobre el anterior: se copia su carpeta y se añaden los ficheros nuevos.
COPIA = {"e4": "e3", "e6": "e5", "e8": "e7"}


# --- Aplicación en el repositorio del alumno ----------------------------------------------

class Error(Exception):
    pass


def _git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise Error(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def _escribir(fichero: Path, contenido: str) -> None:
    fichero.parent.mkdir(parents=True, exist_ok=True)
    fichero.write_text(contenido, encoding="utf-8", newline="\n")


def usuario_de(remoto: str) -> str:
    m = re.search(r"/entregas-([A-Za-z0-9-]+?)(?:\.git)?/?$", remoto)
    if not m:
        raise Error(f"el remoto origin ({remoto}) no es un repositorio entregas-<usuario>")
    return m.group(1).lower()


def preparar(ejercicio: str, cwd: Path) -> None:
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    usuario = usuario_de(_git("remote", "get-url", "origin", cwd=raiz))
    destino = raiz / RAIZ / ejercicio
    if destino.exists():
        raise Error(f"{ejercicio} ya está preparado (existe {destino})")
    if anterior := COPIA.get(ejercicio):
        origen = raiz / RAIZ / anterior
        if not origen.exists():
            raise Error(f"primero hay que tener hecho el {anterior.upper()} ({RAIZ}/{anterior}/)")
        shutil.copytree(origen, destino, ignore=shutil.ignore_patterns(".terraform", "*.tfstate*", ".terraform.lock.hcl"))
    for nombre, contenido in ESCENARIOS[ejercicio](usuario).items():
        _escribir(destino / nombre, contenido)
    for nombre, contenido in comunes().items():
        if not (raiz / RAIZ / nombre).exists():
            _escribir(raiz / RAIZ / nombre, contenido)
    print(f"{ejercicio} preparado para {usuario} en {RAIZ}/{ejercicio}/. Sigue el enunciado.")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ESCENARIOS:
        print(f"uso: py preparar.py {{{','.join(ESCENARIOS)}}}", file=sys.stderr)
        return 2
    try:
        preparar(argv[0], Path.cwd())
    except Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
