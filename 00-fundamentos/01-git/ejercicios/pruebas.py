#!/usr/bin/env python3
"""Comprueba un ejercicio de git en tu equipo con las mismas comprobaciones que el corrector.

Uso, desde la carpeta de tu repositorio de entregas:

    py ../documentacion-hacking-etico/00-fundamentos/01-git/ejercicios/pruebas.py e1         (Windows)
    python3 ../documentacion-hacking-etico/00-fundamentos/01-git/ejercicios/pruebas.py e1    (macOS / Linux)

Sin ejercicio, los comprueba todos. Evalúa lo mismo que el corrector y con el mismo código: la etiqueta
entrega-fundamentos-git-eN si existe y, si no, la rama del ejercicio (main, o la suya en E5, E6 y E8).
Lo que no está en un commit no cuenta. El corrector mira GitHub y esto mira tu equipo: si lo que tienes
no coincide con lo que hay en GitHub, te avisa. Lo que solo sabe GitHub (el autor de los commits de E1,
el commit filtrado de E8 y la hora de la etiqueta) lo pregunta con el GitHub CLI (gh) si tienes sesión
iniciada; sin gh, lo salta y avisa. No cambia nada de tu repositorio.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import preparar as p  # noqa: E402
from comprobar_git.ejercicios import COMPROBACIONES, Contexto  # noqa: E402
from comprobar_git.entrega import FUERA_DE_PLAZO, NO_ANOTADA, PLAZO, fuera_de_plazo, que_evaluar  # noqa: E402
from comprobar_git.repo import Repo  # noqa: E402


class GitHubLocal:
    """Lo poco que las comprobaciones preguntan a GitHub, con tu sesión de gh."""

    def _api(self, ruta: str) -> object | None:
        r = subprocess.run(["gh", "api", ruta], capture_output=True, text=True, encoding="utf-8")
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None

    def commit(self, repo: str, sha: str) -> dict | None:
        return self._api(f"repos/{repo}/commits/{sha}")

    def ultimo_push(self, repo: str, ref: str) -> str | None:
        datos = self._api(f"repos/{repo}/activity?ref={ref}&direction=desc&per_page=1")
        return datos[0]["timestamp"] if datos else None


def con_gh() -> GitHubLocal | None:
    if shutil.which("gh") is None:
        return None
    return GitHubLocal() if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0 else None


def en_github(repo: Repo) -> dict[str, str] | None:
    """ref -> commit de lo que hay en GitHub (las etiquetas, ya resueltas a su commit); None si no responde."""
    r = repo._run("ls-remote", "origin")
    if r.returncode:
        return None
    refs: dict[str, str] = {}
    for linea in r.stdout.splitlines():
        sha, ref = linea.split("\t")
        refs[ref.removesuffix("^{}")] = sha  # la línea ^{} (el commit de la etiqueta anotada) va después
    return refs


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    pedidos = argv or list(p.EJERCICIOS)
    if any(e not in p.EJERCICIOS for e in pedidos):
        print(f"uso: pruebas.py [{' '.join(p.EJERCICIOS)}]", file=sys.stderr)
        return 2
    try:
        raiz = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                                   check=True).stdout.strip())
        remoto = subprocess.run(["git", "remote", "get-url", "origin"], cwd=raiz, capture_output=True, text=True,
                                check=True).stdout.strip()
        usuario = p.usuario_de(remoto)
    except (subprocess.CalledProcessError, p.Error) as e:
        print(f"Ejecútalo desde tu repositorio entregas-<usuario>: {e}", file=sys.stderr)
        return 2
    repo = Repo(raiz)
    nombre = f"Oceano-Atlantico-Ciber/entregas-{usuario}"
    api = con_gh()
    ctx = Contexto(repo, nombre, usuario, api)
    remoto_refs = en_github(repo)
    plazo_cerrado = datetime.now(timezone.utc) > PLAZO
    mal = 0
    for ej in pedidos:
        ev = que_evaluar(repo, ej)
        etiqueta = p.etiqueta(ej)
        avisos = []
        if remoto_refs is not None and ev.estado != "Entregado" and f"refs/tags/{etiqueta}" in remoto_refs:
            avisos.append(f"en GitHub ya existe {etiqueta} y no la tienes aquí: el corrector evalúa la de GitHub. "
                          "Tráela con git fetch --tags")
        if ev.estado == "Sin empezar":
            print(f"{ej.upper()} · sin empezar: no hay etiqueta {etiqueta} ni trabajo en {p.RAIZ}/{ej}/")
            for a in avisos:
                print(f"  ! {a}")
            continue
        try:
            fallos = COMPROBACIONES[ej](ctx, ev.sha)
        except Exception as e:  # un fallo de las pruebas no es un fallo tuyo
            fallos = [f"las pruebas no han podido terminar ({e}); avisa al docente"]
        if not ev.anotada:
            fallos.append(NO_ANOTADA)
        arriba = None if remoto_refs is None else remoto_refs.get(ev.ref if ev.ref.startswith("refs/") else f"refs/heads/{ev.ref}")
        if remoto_refs is None:
            avisos.append("no he podido consultar GitHub (git ls-remote origin): no sé si lo que hay allí coincide")
        elif arriba is None:
            avisos.append(f"{ev.ref.removeprefix('refs/tags/')} aún no está en GitHub: el corrector no lo verá hasta que lo subas")
        elif arriba != ev.sha:
            avisos.append(f"en GitHub {ev.ref.removeprefix('refs/tags/')} apunta a {arriba[:7]}, no a tu {ev.sha[:7]}: "
                          "el corrector evaluará el de GitHub. Sube el tuyo (si lo has reescrito o movido la etiqueta, "
                          "con git push --force-with-lease o git push -f origin <etiqueta>)")
        if ev.estado == "Entregado":
            if arriba == ev.sha and api is not None:
                if fuera_de_plazo(api.ultimo_push(nombre, ev.ref)):
                    fallos.append(FUERA_DE_PLAZO)
            elif arriba == ev.sha and plazo_cerrado:
                avisos.append(f"el plazo cerró el {PLAZO:%d/%m/%Y a las %H:%M}: sin gh no sé a qué hora subiste la "
                              "etiqueta; si fue después, el corrector la marcará fuera de plazo")
            elif arriba != ev.sha and plazo_cerrado:
                fallos.append(f"{FUERA_DE_PLAZO} si la subes ahora: el plazo cerró el {PLAZO:%d/%m/%Y a las %H:%M}")
        que = f"etiqueta {etiqueta}" if ev.estado == "Entregado" else f"rama {ev.ref}, todavía sin etiqueta (provisional)"
        print(f"{ej.upper()} · {que} · {ev.sha[:7]}")
        if fallos:
            mal += 1
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ superado")
        for a in avisos:
            print(f"  ! {a}")
    if api is None:
        print("\nAviso: sin el GitHub CLI con sesión iniciada (gh auth login) no se ha comprobado lo que solo sabe "
              "GitHub: el autor de los commits de E1, el commit filtrado de E8 y la hora de las etiquetas. "
              "El corrector sí lo comprueba.")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
