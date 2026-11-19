#!/usr/bin/env python3
"""Comprueba un ejercicio de Docker en tu equipo con las mismas comprobaciones que el corrector.

Uso, desde cualquier carpeta de tu repositorio de entregas y con Docker Desktop en marcha:

    py ../documentacion-hacking-etico/00-fundamentos/02-docker/ejercicios/pruebas.py e2    (Windows)
    py ../documentacion-hacking-etico/00-fundamentos/02-docker/ejercicios/pruebas.py        (todos)

En macOS o Linux, python3 en lugar de py.

Se evalúa lo mismo que evaluará el corrector: lo que hay en la etiqueta entrega-fundamentos-docker-eN
si ya existe y, si no, lo que hay en main. Lo que no tienes en un commit no cuenta. Se trabaja sobre una
copia del repositorio entero, sacada como la saca el corrector (con saltos de línea LF, aunque tu git en
Windows los convierta a CRLF), así que tu carpeta no cambia. Pero las pruebas construyen y levantan
contenedores de verdad: antes y después de cada ejercicio quitan los contenedores, redes y volúmenes del
laboratorio de ese ejercicio (e5-db, e6-red, el proyecto de tu compose en E7 y E8…) para empezar como en
un equipo limpio. No tocan nada más.
"""

from __future__ import annotations

import io
import re
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
    "e8": {"proyectos": ["e8-panel", "e8"]},
}


def limpiar(ej: str, carpeta: Path) -> None:
    lab = LABORATORIO.get(ej, {})
    proyectos = list(lab.get("proyectos", []))
    if lab.get("proyectos") and (compose := carpeta / "docker-compose.yml").is_file():
        # el corrector levanta el proyecto con el name: de tu compose; si lo cambiaste, también se quita ese
        if (m := re.search(r"^name:\s*['\"]?([\w.-]+)", compose.read_text(encoding="utf-8", errors="replace"), re.M)):
            proyectos.append(m[1].lower())
    for proyecto in dict.fromkeys(proyectos):
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


def copia_del_commit(raiz: Path, ref: str, destino: Path, clon: Path) -> None:
    """El árbol del commit, igual que lo saca el corrector: el repositorio entero, sin core.autocrlf ni
    .gitattributes que cambien los ficheros (git archive los obedece; en Windows, autocrlf los pasaría a CRLF)."""
    subprocess.run(["git", "clone", "--mirror", "--quiet", str(raiz), str(clon)], check=True, capture_output=True)
    (clon / "info").mkdir(exist_ok=True)
    (clon / "info" / "attributes").write_text("* -export-ignore -export-subst -text\n")
    archivo = subprocess.run(["git", "-c", "core.autocrlf=false", "archive", "--format=tar", ref],
                             cwd=clon, capture_output=True, check=True)
    tarfile.open(fileobj=io.BytesIO(archivo.stdout)).extractall(destino, filter="data")


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
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            copia = Path(tmp) / "repo"
            try:
                copia_del_commit(raiz, ref, copia, Path(tmp) / "clon")
            except subprocess.CalledProcessError:
                print(f"{ej.upper()} · sin empezar: no hay {ref}")
                continue
            if not (copia / p.RAIZ / ej).is_dir():
                print(f"{ej.upper()} · sin empezar: {ref} no tiene {p.RAIZ}/{ej}/")
                continue
            print(f"{ej.upper()} · {que} · comprobando…", flush=True)
            carpeta = copia / p.RAIZ / ej
            limpiar(ej, carpeta)
            fallos: list[str] = []
            try:
                fallos.extend(COMPROBACIONES[ej](Caso(usuario, copia, ej)))
            except Fallo as e:
                fallos.append(str(e))
            except Exception as e:  # un fallo de las pruebas no es un fallo tuyo
                fallos.append(f"las pruebas no han podido terminar ({e}); avisa al docente")
            finally:
                limpiar(ej, carpeta)
        if ref == etiqueta and git("cat-file", "-t", etiqueta, cwd=raiz) != "tag":
            fallos.append("la etiqueta no es anotada (git tag -a)")  # el corrector la marca igual
        if fallos:
            mal += 1
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ superado")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
