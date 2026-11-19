#!/usr/bin/env python3
"""Comprueba un ejercicio de Terraform y AWS en tu equipo con las mismas comprobaciones que el corrector.

Uso, desde cualquier carpeta de tu repositorio de entregas y con Docker Desktop en marcha:

    py ../documentacion-hacking-etico/00-fundamentos/04-iac/ejercicios/pruebas.py e3    (Windows)
    py ../documentacion-hacking-etico/00-fundamentos/04-iac/ejercicios/pruebas.py           (todos)

Se evalúa lo mismo que evaluará el corrector: lo que hay en la etiqueta entrega-fundamentos-iac-eN
si ya existe y, si no, lo que hay en main. Lo que no tienes en un commit no cuenta. Se trabaja sobre una
copia, así que tu carpeta no cambia. Cada ejercicio se prueba en una Floci nueva y vacía (el contenedor
iac-comprobar-floci), no en la tuya: lo que tengas en tu Floci de la unidad no se toca.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import preparar as p  # noqa: E402
from comprobar_iac.floci import BASE, Fallo, docker  # noqa: E402
from comprobar_iac.ejercicios import COMPROBACIONES, Caso  # noqa: E402

def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    pedidos = argv or list(p.EJERCICIOS)
    if any(e not in p.EJERCICIOS for e in pedidos):
        print(f"uso: py pruebas.py [{' '.join(p.EJERCICIOS)}]", file=sys.stderr)
        return 2
    try:
        raiz = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()))
        usuario = p.usuario_de(git("remote", "get-url", "origin", cwd=raiz))
    except Exception as e:
        print(f"Ejecútalo desde tu repositorio entregas-<usuario>: {e}", file=sys.stderr)
        return 2
    if docker("info").codigo:
        print("Docker no responde: arranca Docker Desktop y vuelve a probar.", file=sys.stderr)
        return 2
    for imagen in BASE:  # las imágenes del curso, una vez; si ya las tienes, no se descargan
        docker("pull", "-q", imagen, espera=600)
    mal = 0
    for ej in pedidos:
        etiqueta = p.etiqueta(ej)
        ref, que = (etiqueta, f"etiqueta {etiqueta}") if git("tag", "-l", etiqueta, cwd=raiz) else ("main", "main, todavía sin etiqueta")
        archivo = subprocess.run(["git", "archive", "--format=tar", ref, p.RAIZ], cwd=raiz, capture_output=True)
        if archivo.returncode:
            print(f"{ej.upper()} · sin empezar: {ref} no tiene {p.RAIZ}/")
            continue
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            copia = Path(tmp) / "repo"
            tarfile.open(fileobj=io.BytesIO(archivo.stdout)).extractall(copia, filter="data")
            # git archive pone a cada fichero la hora de su commit; con dos ejercicios subidos en el mismo segundo,
            # Docker puede reaprovechar el contexto del anterior y construir código viejo. Se les pone la hora de ahora.
            for f in Path(copia).rglob("*"):
                if not f.is_symlink():
                    os.utime(f)
            if not (copia / p.RAIZ / ej).is_dir():
                print(f"{ej.upper()} · sin empezar: {ref} no tiene {p.RAIZ}/{ej}/")
                continue
            print(f"{ej.upper()} · {que} · comprobando…", flush=True)
            fallos: list[str] = []
            try:
                fallos.extend(COMPROBACIONES[ej](Caso(usuario, copia, ej)))
            except Fallo as e:
                fallos.append(str(e))
            except Exception as e:  # un fallo de las pruebas no es un fallo tuyo
                fallos.append(f"las pruebas no han podido terminar ({e}); avisa al docente")
        if fallos:
            mal += 1
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ superado")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
