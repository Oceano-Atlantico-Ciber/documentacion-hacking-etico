#!/usr/bin/env python3
"""Comprueba un ejercicio de Terraform y AWS en tu equipo con las mismas comprobaciones que el corrector.

Uso, desde la carpeta de tu repositorio de entregas y con Docker Desktop en marcha:

    py ../documentacion-hacking-etico/00-fundamentos/04-iac/ejercicios/pruebas.py e3        (Windows)
    python3 ../documentacion-hacking-etico/00-fundamentos/04-iac/ejercicios/pruebas.py e3   (macOS / Linux)

Sin ejercicio, los comprueba todos. Se evalúa lo mismo que evaluará el corrector: la etiqueta
entrega-fundamentos-iac-eN si ya existe y, si no, main (si main ya tiene fundamentos/iac/eN/). Lo que no
está en un commit no cuenta. Se trabaja sobre una copia del commit sacada como la saca el corrector (con
saltos de línea LF, aunque tu git en Windows los convierta a CRLF), así que tu carpeta no cambia. Cada
ejercicio se prueba en una Floci nueva y vacía (el contenedor iac-comprobar-floci), no en la tuya: lo que
tengas en tu Floci de la unidad no se toca. El corrector mira GitHub y esto mira tu equipo: si no
coinciden, te avisa. No hay fecha límite.
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
from comprobar_iac.floci import BASE, Fallo, docker  # noqa: E402
from comprobar_iac.ejercicios import COMPROBACIONES, Caso  # noqa: E402

NO_ANOTADA = "la etiqueta no es anotada (git tag -a)"  # el mismo texto que pone el corrector


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def que_evaluar(raiz: Path, ej: str) -> tuple[str, str, str] | None:
    """(ref, sha, descripción) como el corrector: la etiqueta si existe; si no, main si ya tiene el ejercicio."""
    etiqueta = p.etiqueta(ej)
    if (r := git("rev-parse", "-q", "--verify", f"refs/tags/{etiqueta}^{{commit}}", cwd=raiz)).returncode == 0:
        return f"refs/tags/{etiqueta}", r.stdout.strip(), f"etiqueta {etiqueta}"
    if (r := git("rev-parse", "-q", "--verify", "refs/heads/main^{commit}", cwd=raiz)).returncode == 0:
        sha = r.stdout.strip()
        if git("ls-tree", "-r", "--name-only", sha, "--", f"{p.RAIZ}/{ej}", cwd=raiz).stdout.strip():
            return "main", sha, "main, todavía sin etiqueta (provisional)"
    return None


def copia_del_commit(raiz: Path, sha: str, destino: Path, clon: Path) -> None:
    """El árbol entero del commit, igual que lo saca el corrector: sin core.autocrlf ni .gitattributes que
    cambien los ficheros (git archive los obedece; en Windows, autocrlf los pasaría a CRLF)."""
    subprocess.run(["git", "clone", "--mirror", "--quiet", str(raiz), str(clon)], check=True, capture_output=True)
    (clon / "info").mkdir(exist_ok=True)
    (clon / "info" / "attributes").write_text("* -export-ignore -export-subst -text\n")
    archivo = subprocess.run(["git", "-c", "core.autocrlf=false", "archive", "--format=tar", sha],
                             cwd=clon, capture_output=True, check=True)
    tarfile.open(fileobj=io.BytesIO(archivo.stdout)).extractall(destino, filter="data")


def en_github(raiz: Path) -> dict[str, str] | None:
    """ref -> commit de lo que hay en GitHub (las etiquetas anotadas, ya resueltas a su commit)."""
    r = git("ls-remote", "origin", cwd=raiz)
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
        raiz = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).stdout.strip() or "?")
        usuario = p.usuario_de(git("remote", "get-url", "origin", cwd=raiz).stdout.strip())
    except (OSError, p.Error) as e:
        print(f"Ejecútalo desde tu repositorio entregas-<usuario>: {e}", file=sys.stderr)
        return 2
    if docker("info").codigo:
        print("Docker no responde: arranca Docker Desktop y vuelve a probar.", file=sys.stderr)
        return 2
    for imagen in BASE:  # las imágenes del curso, una vez; si ya las tienes, no se descargan
        docker("pull", "-q", imagen, espera=600)
    remoto = en_github(raiz)
    mal = 0
    for ej in pedidos:
        etiqueta = p.etiqueta(ej)
        avisos: list[str] = []
        evaluable = que_evaluar(raiz, ej)
        if remoto is not None and (evaluable is None or not evaluable[0].startswith("refs/tags/")) \
                and f"refs/tags/{etiqueta}" in remoto:
            avisos.append(f"en GitHub ya existe {etiqueta} y no la tienes aquí: el corrector evalúa la de GitHub. "
                          "Tráela con git fetch --tags")
        if evaluable is None:
            print(f"{ej.upper()} · sin empezar: no hay etiqueta {etiqueta} ni trabajo en {p.RAIZ}/{ej}/ de main")
            for a in avisos:
                print(f"  ! {a}")
            continue
        ref, sha, que = evaluable
        print(f"{ej.upper()} · {que} · {sha[:7]} · comprobando…", flush=True)
        fallos: list[str] = []
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:  # Terraform deja ficheros de root
            copia = Path(tmp) / "repo"
            try:
                copia_del_commit(raiz, sha, copia, Path(tmp) / "clon")
                fallos.extend(COMPROBACIONES[ej](Caso(usuario, copia, ej)))
            except Fallo as e:
                fallos.append(str(e))
            except tarfile.FilterError as e:
                fallos.append(f"el repositorio tiene un fichero o enlace que sale de su carpeta: {e}")
            except Exception as e:  # un fallo de las pruebas no es un fallo tuyo
                fallos.append(f"las pruebas no han podido terminar ({e}); avisa al docente")
        if ref.startswith("refs/tags/") and git("cat-file", "-t", ref, cwd=raiz).stdout.strip() != "tag":
            fallos.append(NO_ANOTADA)
        nombre = ref.removeprefix("refs/tags/")
        arriba = None if remoto is None else remoto.get(ref if ref.startswith("refs/") else f"refs/heads/{ref}")
        if remoto is None:
            avisos.append("no he podido consultar GitHub (git ls-remote origin): no sé si lo que hay allí coincide")
        elif arriba is None:
            avisos.append(f"{nombre} aún no está en GitHub: el corrector no lo verá hasta que lo subas")
        elif arriba != sha:
            avisos.append(f"en GitHub {nombre} apunta a {arriba[:7]}, no a tu {sha[:7]}: el corrector evaluará el de "
                          "GitHub. Sube el tuyo (si has movido la etiqueta, con git push -f origin <etiqueta>)")
        if fallos:
            mal += 1
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ superado")
        for a in avisos:
            print(f"  ! {a}")
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
