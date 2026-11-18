#!/usr/bin/env python3
"""Comprueba un ejercicio del RA1 en tu equipo con las mismas comprobaciones públicas que el corrector.

Uso, desde cualquier carpeta de tu repositorio de entregas:

    py ../documentacion-hacking-etico/01-hacking-etico/pruebas.py u1-e1    (Windows)
    py ../documentacion-hacking-etico/01-hacking-etico/pruebas.py          (todos)

Se evalúa lo mismo que evaluará el corrector: lo que hay en la etiqueta entrega-ra1-<ejercicio> si ya existe
y, si no, lo que hay en main. Lo que no tienes en un commit no cuenta. Se trabaja sobre una copia, así que tu
carpeta no cambia.

Comprueba el formato y todo lo que sale de tu escenario (direcciones, fechas, registros, rutas). Lo que va con
clave (figuras, tipos de fallo, CWE, datos del CVE, técnicas…) lo compara el corrector: aquí no se dice si es
lo correcto. El U4·E2 necesita Docker Desktop en marcha; los demás, nada más que Python.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import preparar as p  # noqa: E402
from comprobar_ra1.base import Caso, Fallo  # noqa: E402
from comprobar_ra1.ejercicios import COMPROBACIONES  # noqa: E402


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
    mal = 0
    for ej in pedidos:
        etiqueta = p.etiqueta(ej)
        ref, que = (etiqueta, f"etiqueta {etiqueta}") if git("tag", "-l", etiqueta, cwd=raiz) else ("main", "main, todavía sin etiqueta")
        archivo = subprocess.run(["git", "archive", "--format=tar", ref, f"{p.RAIZ}/{ej}"], cwd=raiz, capture_output=True)
        if archivo.returncode:
            print(f"{ej.upper()} · sin empezar: {ref} no tiene {p.RAIZ}/{ej}/")
            continue
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            copia = Path(tmp) / "repo"
            tarfile.open(fileobj=io.BytesIO(archivo.stdout)).extractall(copia, filter="data")
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
            print("  ✓ formato correcto; las respuestas con clave las revisa el corrector")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
