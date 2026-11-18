#!/usr/bin/env python3
"""Deja los ficheros de partida de un ejercicio del RA1 en tu repositorio de entregas.

Uso, desde cualquier carpeta de tu repositorio:

    py ../documentacion-hacking-etico/01-hacking-etico/preparar.py u1-e1     (Windows; en Linux o macOS, python3)

Copia la plantilla del ejercicio a ra1/<ejercicio>/ y no hace commits. Este mismo módulo es el que usan el
corrector y pruebas.py para saber dónde está cada ejercicio, de modo que no hay que tocarlo.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = "ra1"
UNIDADES = {
    "u1": "01-que-es-el-hacking-etico",
    "u2": "02-permisos-y-alcance",
    "u3": "03-vulnerabilidades-y-ataques",
    "u4": "04-herramientas-y-monitorizacion",
}
EJERCICIOS = ("u1-e1", "u1-e2", "u2-e1", "u2-e2", "u3-e1", "u3-e2", "u3-e3", "u4-e1", "u4-e2", "u4-e3")


def etiqueta(ejercicio: str) -> str:
    return f"entrega-ra1-{ejercicio}"


def plantilla(ejercicio: str) -> Path:
    unidad, ej = ejercicio.split("-")
    return AQUI / UNIDADES[unidad] / "ejercicios" / "plantillas" / ej


class Error(Exception):
    pass


def _git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise Error(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def usuario_de(remoto: str) -> str:
    m = re.search(r"/entregas-([A-Za-z0-9-]+?)(?:\.git)?/?$", remoto)
    if not m:
        raise Error(f"el remoto origin ({remoto}) no es un repositorio entregas-<usuario>")
    return m.group(1).lower()


def preparar(ejercicio: str, cwd: Path) -> None:
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    usuario_de(_git("remote", "get-url", "origin", cwd=raiz))  # que sea tu repositorio de entregas
    destino = raiz / RAIZ / ejercicio
    if destino.exists():
        raise Error(f"{ejercicio} ya está preparado (existe {RAIZ}/{ejercicio}/)")
    shutil.copytree(plantilla(ejercicio), destino)
    for f in destino.rglob("*"):  # finales de línea de Linux también en Windows
        if f.is_file() and f.suffix in (".md", ".rules", ".yml", ".py", ".txt", ".html"):
            f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n"))
    print(f"{ejercicio} preparado en {RAIZ}/{ejercicio}/. Sigue el enunciado.")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in EJERCICIOS:
        print(f"uso: py preparar.py {{{','.join(EJERCICIOS)}}}", file=sys.stderr)
        return 2
    try:
        preparar(argv[0], Path.cwd())
    except Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
