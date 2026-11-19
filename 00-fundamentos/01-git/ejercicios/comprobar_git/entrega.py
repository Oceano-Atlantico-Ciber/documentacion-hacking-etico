"""Qué se evalúa de cada ejercicio y cuándo una entrega queda fuera de plazo.

Lo usan igual el corrector y pruebas.py, para que los dos den el mismo veredicto sobre el mismo commit.
"""

from __future__ import annotations

from datetime import datetime
from typing import NamedTuple

import preparar as p

from .ejercicios import RAMAS
from .repo import Repo

# Fecha límite de las etiquetas de git. El corrector la puede cambiar con --fecha-limite.
PLAZO = datetime.fromisoformat("2026-11-05T23:59:59+01:00")

NO_ANOTADA = "la etiqueta no es anotada: bórrala y créala con git tag -a (paso «Sube y etiqueta»)"
FUERA_DE_PLAZO = "entregada fuera de plazo"


class Evaluable(NamedTuple):
    estado: str  # "Entregado" (hay etiqueta), "Provisional" (solo la rama) o "Sin empezar"
    ref: str | None  # la ref evaluada: refs/tags/<etiqueta> o la rama del ejercicio
    sha: str | None
    anotada: bool = True


def que_evaluar(repo: Repo, ej: str) -> Evaluable:
    """La etiqueta si existe; si no, la rama del ejercicio, siempre que el ejercicio se haya empezado.

    En main, «empezado» quiere decir que main ya tiene ficheros en fundamentos/git/eN: así un ejercicio sin
    preparar sale como «Sin empezar» y no como una lista de fallos."""
    tag = f"refs/tags/{p.etiqueta(ej)}"
    if sha := repo.sha(tag):
        return Evaluable("Entregado", tag, sha, repo.tipo(tag) == "tag")
    rama = RAMAS[ej]
    if (sha := repo.sha(rama)) and (rama != p.RAMA_PRINCIPAL or repo.ficheros(sha, f"{p.RAIZ}/{ej}")):
        return Evaluable("Provisional", rama, sha)
    return Evaluable("Sin empezar", None, None)


def fuera_de_plazo(hora: str | None, plazo: datetime = PLAZO) -> bool:
    """hora: ISO 8601 del último push que creó o movió la etiqueta."""
    return bool(hora) and datetime.fromisoformat(hora.replace("Z", "+00:00")) > plazo
