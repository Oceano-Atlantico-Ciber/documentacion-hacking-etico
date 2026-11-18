"""Lo común: el caso que se evalúa, el fallo que corta la comprobación y la lectura de tablas Markdown."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import preparar as p


class Fallo(Exception):
    """Lo entregado no permite seguir comprobando este ejercicio."""


@dataclass(frozen=True)
class Caso:
    usuario: str
    raiz: Path  # el repositorio del alumno, extraído del commit evaluado (una copia)
    ej: str

    @property
    def carpeta(self) -> Path:
        return self.raiz / p.RAIZ / self.ej

    def leer(self, nombre: str) -> str:
        f = self.carpeta / nombre
        if not f.is_file():
            raise Fallo(f"falta {p.RAIZ}/{self.ej}/{nombre}")
        datos = f.read_bytes()
        codificacion = "utf-16" if datos[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
        return datos.decode(codificacion, "replace").replace("\r\n", "\n")


def normal(texto: str) -> str:
    """Minúsculas, sin tildes, sin marcas de Markdown y con un solo espacio entre palabras."""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[`*_]", "", texto).lower()
    return re.sub(r"\s+", " ", texto).strip()


def _celdas(linea: str) -> list[str]:
    linea = linea.strip()
    if linea.startswith("|"):
        linea = linea[1:]
    if linea.endswith("|"):
        linea = linea[:-1]
    return [c.strip() for c in linea.split("|")]


def tablas(texto: str) -> list[list[list[str]]]:
    """Cada tabla Markdown del texto como lista de filas; la primera fila es la cabecera."""
    resultado: list[list[list[str]]] = []
    actual: list[list[str]] = []
    for linea in texto.split("\n") + [""]:
        if linea.strip().startswith("|"):
            celdas = _celdas(linea)
            separador = any(celdas) and all(re.fullmatch(r":?-{3,}:?", c) for c in celdas if c)
            if not separador:
                actual.append(celdas)
        elif actual:
            resultado.append(actual)
            actual = []
    return resultado


def tabla(texto: str, fichero: str, *columnas: str) -> list[dict[str, str]]:
    """Las filas de la primera tabla que tenga todas esas columnas, como diccionarios por columna normalizada."""
    buscadas = [normal(c) for c in columnas]
    for t in tablas(texto):
        cabecera = [normal(c) for c in t[0]]
        if all(c in cabecera for c in buscadas):
            filas = []
            for fila in t[1:]:
                fila = fila + [""] * (len(cabecera) - len(fila))
                filas.append({c: v for c, v in zip(cabecera, fila)})
            return filas
    raise Fallo(f"{fichero} no tiene la tabla con las columnas {', '.join(columnas)}: no cambies la cabecera de la plantilla")


def campos(texto: str, fichero: str) -> dict[str, str]:
    """Una tabla «| Campo | Valor |» como diccionario campo normalizado -> valor."""
    return {normal(f["campo"]): f["valor"].strip() for f in tabla(texto, fichero, "Campo", "Valor")}


def palabras(texto: str) -> int:
    return len(re.findall(r"\w+", texto))


def vacio(valor: str) -> bool:
    return normal(valor) in ("", "...", "…", "-", "?")


def fecha(valor: str) -> date | None:
    """dd/mm/aaaa, como en la plantilla."""
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", valor.strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
