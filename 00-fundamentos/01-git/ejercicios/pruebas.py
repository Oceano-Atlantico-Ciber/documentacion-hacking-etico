#!/usr/bin/env python3
"""Comprueba un ejercicio de git en tu equipo con las mismas comprobaciones que el corrector.

Uso, desde cualquier carpeta de tu repositorio de entregas:

    py ../documentacion-hacking-etico/00-fundamentos/01-git/ejercicios/pruebas.py e1     (Windows)
    py ../documentacion-hacking-etico/00-fundamentos/01-git/ejercicios/pruebas.py         (todos)

Se evalúa lo mismo que evaluará el corrector: la etiqueta entrega-fundamentos-git-eN si ya existe y,
si no, la rama del ejercicio (main, o la suya en E5, E6 y E8) tal como está en tu repositorio. Lo que
no tienes en un commit no cuenta. Dos comprobaciones preguntan a GitHub (el autor de los commits de E1
y el commit filtrado de E8): las hace con el GitHub CLI (gh) si lo tienes; si no, las salta y avisa.
No cambia nada de tu repositorio.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import preparar as p  # noqa: E402
from comprobar_git.ejercicios import COMPROBACIONES, RAMAS, Contexto  # noqa: E402
from comprobar_git.repo import Repo  # noqa: E402


class GitHubLocal:
    """Lo poco que las comprobaciones preguntan a GitHub, con tu sesión de gh. Sin gh, no se comprueba."""

    def __init__(self):
        self.disponible = shutil.which("gh") is not None and subprocess.run(
            ["gh", "auth", "status"], capture_output=True).returncode == 0
        self.saltadas: set[str] = set()

    def commit(self, repo: str, sha: str) -> dict | None:
        if not self.disponible:
            self.saltadas.add(sha)
            return None
        r = subprocess.run(["gh", "api", f"repos/{repo}/commits/{sha}"], capture_output=True, text=True, encoding="utf-8")
        return json.loads(r.stdout) if r.returncode == 0 else None

    def autor(self, repo: str, sha: str) -> str | None:
        datos = self.commit(repo, sha)
        return (datos.get("author") or {}).get("login") if datos else None


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
        raiz = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                                   check=True).stdout.strip())
        remoto = subprocess.run(["git", "remote", "get-url", "origin"], cwd=raiz, capture_output=True, text=True,
                                check=True).stdout.strip()
        usuario = p.usuario_de(remoto)
    except (subprocess.CalledProcessError, Exception) as e:
        print(f"Ejecútalo desde tu repositorio entregas-<usuario>: {e}", file=sys.stderr)
        return 2
    repo = Repo(raiz)
    nombre = f"Oceano-Atlantico-Ciber/entregas-{usuario}"
    api = GitHubLocal()
    ctx = Contexto(repo, nombre, usuario, api)
    mal = 0
    for ej in pedidos:
        etiqueta = p.etiqueta(ej)
        if sha := repo.sha(f"refs/tags/{etiqueta}"):
            que = f"etiqueta {etiqueta}"
            if repo.tipo(f"refs/tags/{etiqueta}") != "tag":
                print(f"{ej.upper()} · {que}\n  ✗ la etiqueta no es anotada: créala con git tag -a")
                mal += 1
        elif sha := repo.sha(RAMAS[ej]):
            que = f"rama {RAMAS[ej]}, todavía sin etiqueta"
        else:
            print(f"{ej.upper()} · sin empezar: no hay etiqueta ni rama {RAMAS[ej]}")
            continue
        try:
            fallos = COMPROBACIONES[ej](ctx, sha)
        except Exception as e:  # un fallo de las pruebas no es un fallo tuyo
            fallos = [f"las pruebas no han podido terminar ({e}); avisa al docente"]
        if not api.disponible:  # lo que depende de GitHub no se ha podido mirar: no se da por fallo
            fallos = [f for f in fallos if "GitHub no asocia" not in f and "no es el commit que subió la clave" not in f]
        print(f"{ej.upper()} · {que} · {sha[:7]}")
        if fallos:
            mal += 1
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ superado")
    if api.saltadas:
        print("\nAviso: sin el GitHub CLI con sesión iniciada (gh auth login) no se ha comprobado lo que depende "
              "de GitHub: el autor de los commits de E1 y el commit filtrado de E8. El corrector sí lo comprueba.")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
