"""Lectura del historial de un repositorio con el CLI de git. No ejecuta código del alumno."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class Repo:
    def __init__(self, ruta: Path):
        self.ruta = ruta

    def _run(self, *args: str, entrada: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-c", "core.excludesFile=/dev/null", *args], cwd=self.ruta,
                              input=entrada, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def git(self, *args: str, entrada: str | None = None) -> str:
        r = self._run(*args, entrada=entrada)
        if r.returncode:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def codigo(self, *args: str) -> int:
        return self._run(*args).returncode

    def sha(self, ref: str) -> str | None:
        r = self._run("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        return r.stdout.strip() if r.returncode == 0 else None

    def tipo(self, ref: str) -> str:
        return self.git("cat-file", "-t", ref)

    def commits(self, ref: str, *opciones: str, rutas: tuple[str, ...] = ()) -> list[str]:
        salida = self.git("rev-list", *opciones, ref, "--", *rutas)
        return salida.split() if salida else []

    def con_mensaje(self, ref: str, mensaje: str) -> list[str]:
        """Commits alcanzables desde ref cuyo asunto es exactamente mensaje."""
        return [s for s, asunto in self._asuntos(ref) if asunto == mensaje]

    def asuntos(self, ref: str) -> list[str]:
        return [asunto for _, asunto in self._asuntos(ref)]

    def _asuntos(self, ref: str) -> list[tuple[str, str]]:
        salida = self.git("log", "--format=%H %s", ref)
        return [tuple(linea.split(" ", 1)) if " " in linea else (linea, "") for linea in salida.splitlines()]

    def asunto(self, sha: str) -> str:
        return self.git("log", "-1", "--format=%s", sha)

    def padres(self, sha: str) -> list[str]:
        return self.git("rev-list", "--parents", "-n1", sha).split()[1:]

    def ancestro(self, a: str, b: str) -> bool:
        return self.codigo("merge-base", "--is-ancestor", a, b) == 0

    def fichero(self, ref: str, ruta: str) -> str | None:
        r = self._run("show", f"{ref}:{ruta}")
        return r.stdout.replace("\r\n", "\n") if r.returncode == 0 else None

    def ficheros(self, ref: str, carpeta: str) -> set[str]:
        """Rutas, relativas a carpeta, de los ficheros versionados en ref."""
        salida = self.git("ls-tree", "-r", "--name-only", ref, "--", carpeta)
        return {r.removeprefix(carpeta + "/") for r in salida.splitlines()}

    def cambiados(self, sha: str) -> set[str]:
        salida = self.git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha)
        return set(salida.splitlines())

    def patch_id(self, desde: str, hasta: str) -> str | None:
        diff = self.git("diff", desde, hasta)
        salida = self.git("patch-id", "--stable", entrada=diff + "\n")
        return salida.split()[0] if salida else None

    def conflicto(self, a: str, b: str) -> bool:
        return self.codigo("merge-tree", "--write-tree", "--name-only", "--no-messages", a, b) == 1

    def ignorados(self, ref: str, rutas: list[str], gitignore: str) -> set[str]:
        """Cuáles de rutas ignora el fichero gitignore tal como está en ref, él solo.

        No cuentan los .gitignore de otras carpetas, ni .git/info/exclude ni la configuración del equipo: así el
        resultado es el mismo en el equipo del alumno que en el corrector."""
        contenido = self.fichero(ref, gitignore)
        if contenido is None:
            return set()
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp, gitignore)
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(contenido, encoding="utf-8")
            aislado = Repo(Path(tmp))
            aislado.git("init", "-q", "--template=")  # sin plantilla: sin info/exclude
            r = aislado._run("check-ignore", "--no-index", *rutas)
        return set(r.stdout.splitlines())
