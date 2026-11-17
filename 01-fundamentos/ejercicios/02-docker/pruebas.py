#!/usr/bin/env python3
"""Comprueba un ejercicio de Docker en tu equipo con las mismas comprobaciones que el corrector.

Uso, desde cualquier carpeta de tu repositorio de entregas y con Docker Desktop en marcha:

    py ../documentacion-hacking-etico/01-fundamentos/ejercicios/02-docker/pruebas.py e2    (Windows)
    py ../documentacion-hacking-etico/01-fundamentos/ejercicios/02-docker/pruebas.py        (todos)

Se evalúa lo mismo que evaluará el corrector: lo que hay en la etiqueta entrega-fundamentos-docker-eN
si ya existe y, si no, lo que hay en main. Lo que no tienes en un commit no cuenta. Se trabaja sobre una
copia, así que tu carpeta no cambia, pero las pruebas construyen y levantan contenedores de verdad: antes
y después de cada ejercicio quitan los contenedores, redes y volúmenes del laboratorio de ese ejercicio
(e5-db, e6-red, el proyecto e7-lab…) para empezar como en un equipo limpio. No tocan nada más.
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
from comprobar_docker.docker import BASE, Fallo, docker  # noqa: E402
from comprobar_docker.ejercicios import COMPROBACIONES, Caso  # noqa: E402

# Lo que cada ejercicio crea en tu Docker: se quita antes y después de comprobarlo.
LABORATORIO = {
    "e2": {"contenedores": ["e2-diana"], "redes": ["corrector-e2"]},
    "e5": {"contenedores": ["e5-db", "e5-web"], "volumenes": ["e5-datos"]},
    "e6": {"contenedores": ["e6-web", "e6-datos"], "redes": ["e6-red"]},
    "e7": {"proyectos": ["e7-lab"]},
    "e8": {"proyectos": ["e8"]},
}


def limpiar(ej: str) -> None:
    lab = LABORATORIO.get(ej, {})
    for proyecto in lab.get("proyectos", []):
        docker("compose", "-p", proyecto, "down", "-v", "--remove-orphans")
    if lab.get("contenedores"):
        docker("rm", "-f", "-v", *lab["contenedores"])
    for red in lab.get("redes", []):
        docker("network", "rm", red)
    for volumen in lab.get("volumenes", []):
        docker("volume", "rm", volumen)
    docker("rmi", "-f", f"corrector-{ej}")


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
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            tarfile.open(fileobj=io.BytesIO(archivo.stdout)).extractall(copia, filter="data")
            if not (copia / p.RAIZ / ej).is_dir():
                print(f"{ej.upper()} · sin empezar: {ref} no tiene {p.RAIZ}/{ej}/")
                continue
            print(f"{ej.upper()} · {que} · comprobando…", flush=True)
            limpiar(ej)
            fallos: list[str] = []
            try:
                fallos.extend(COMPROBACIONES[ej](Caso(usuario, copia, ej)))
            except Fallo as e:
                fallos.append(str(e))
            except Exception as e:  # un fallo de las pruebas no es un fallo tuyo
                fallos.append(f"las pruebas no han podido terminar ({e}); avisa al docente")
            finally:
                limpiar(ej)
        if fallos:
            mal += 1
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ superado")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
