"""levantar.sh sin bash: se traduce a una lista de órdenes docker y solo se ejecuta si todas son de las
permitidas. Así el script del alumno nunca corre en el equipo que corrige.

Admite las líneas del principio que pide el enunciado (set y el cd a su carpeta), comentarios y órdenes
docker volume create, network create, run, rm, stop y pull. El enunciado pide una orden completa por línea,
para que el mismo fichero se lance también desde PowerShell; por las entregas anteriores se siguen
admitiendo export MSYS_NO_PATHCONV=1, continuaciones con \\, redirecciones a /dev/null y un «|| true»
final. Las carpetas montadas tienen que estar dentro de la del ejercicio.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from .docker import Fallo, docker

NOMBRE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*")
CD_PROPIA = re.compile(r'\$\(dirname (?:-- )?(?:\$0|\$\{?BASH_SOURCE(?:\[0\])?\}?)\)')
PWD = re.compile(r"\$\(pwd\)|\$\{PWD\}|\$PWD\b")
DESCARTES = {">/dev/null", "2>/dev/null", "&>/dev/null", "2>&1", "1>/dev/null"}
REDIRIGE = {">", "1>", "2>", "&>"}
SET = re.compile(r"-[euxo]+|pipefail|\+[eux]+")
# Opciones de docker run y qué es su valor: "" si no llevan; "libre" si no hay nada que validar.
RUN = {"-d": "", "--detach": "", "--rm": "", "--name": "nombre", "-p": "libre", "--publish": "libre",
       "-v": "montaje", "--volume": "montaje", "-e": "libre", "--env": "libre", "--network": "red", "--net": "red",
       "--restart": "libre"}


def ordenes(texto: str, carpeta: Path, imagenes: set[str]) -> list[list[str]]:
    """Las órdenes docker de levantar.sh, ya validadas, o Fallo con la primera línea que no se admite."""
    logicas = re.sub(r"\\\n", " ", texto.replace("\r\n", "\n")).split("\n")
    resultado = []
    for n, linea in enumerate(logicas, 1):
        try:
            t = shlex.split(PWD.sub(lambda _: carpeta.as_posix(), linea), comments=True)
        except ValueError:
            raise Fallo(f"levantar.sh, línea {n}: comillas sin cerrar") from None
        if not t or _preambulo(t):
            continue
        try:
            resultado.append(_docker(_sin_redirecciones(t), carpeta, imagenes))
        except ValueError as e:
            raise Fallo(f"levantar.sh, línea {n} («{linea.strip()}»): {e}. El corrector solo admite órdenes "
                        "docker de las del enunciado, una por línea") from None
    if not resultado:
        raise Fallo("levantar.sh no tiene ninguna orden docker")
    return resultado


def ejecutar(carpeta: Path, imagenes: set[str]) -> None:
    script = carpeta / "levantar.sh"
    for orden in ordenes(script.read_text(encoding="utf-8", errors="replace"), carpeta, imagenes):
        if (r := docker(*orden[1:], cwd=carpeta)).codigo:
            raise Fallo(f"levantar.sh falla en un equipo limpio, en «{shlex.join(orden)}»: {r.motivo}")


def _preambulo(t: list[str]) -> bool:
    return ((t[0] == "set" and all(SET.fullmatch(x) for x in t[1:]))
            or t == ["export", "MSYS_NO_PATHCONV=1"]
            or (t[0] == "cd" and len(t[1:]) in (1, 2) and t[-1] != "--" and bool(CD_PROPIA.fullmatch(t[-1]))))


def _sin_redirecciones(t: list[str]) -> list[str]:
    if t[-2:] == ["||", "true"]:
        t = t[:-2]
    limpio, i = [], 0
    while i < len(t):
        if t[i] in DESCARTES:
            i += 1
        elif t[i] in REDIRIGE and t[i + 1:i + 2] == ["/dev/null"]:
            i += 2
        else:
            limpio.append(t[i])
            i += 1
    return limpio


def _docker(t: list[str], carpeta: Path, imagenes: set[str]) -> list[str]:
    if t[0] != "docker":
        raise ValueError(f"«{t[0]}» no es docker")
    if any(set(x) & set(";|&`$<>") for x in t):
        raise ValueError("lleva variables o caracteres de la shell")
    match t[1:3]:
        case ["volume" | "network", "create"]:
            if len(t) != 4 or not NOMBRE.fullmatch(t[3]):
                raise ValueError(f"docker {t[1]} create admite solo un nombre")
            return t
        case ["rm" | "stop", *_]:
            if not all(NOMBRE.fullmatch(x) or x == "-f" for x in t[2:]):
                raise ValueError(f"docker {t[1]} admite solo -f y nombres")
            return t
        case ["pull", *_]:
            if len(t) != 3 or t[2] not in imagenes:
                raise ValueError(f"docker pull admite solo {', '.join(sorted(imagenes))}")
            return t
        case ["run", *_]:
            return _run(t, carpeta, imagenes)
    raise ValueError(f"docker {' '.join(t[1:2])} no es una de las órdenes admitidas")


def _run(t: list[str], carpeta: Path, imagenes: set[str]) -> list[str]:
    salida, i = ["docker", "run"], 2
    while i < len(t) and t[i].startswith("-"):
        opcion, igual, valor = t[i].partition("=")
        if opcion not in RUN:
            raise ValueError(f"docker run no admite aquí la opción {opcion}")
        tipo = RUN[opcion]
        if not tipo:
            if igual:
                raise ValueError(f"{opcion} no lleva valor")
            salida.append(opcion)
            i += 1
            continue
        if not igual:
            i += 1
            if i == len(t):
                raise ValueError(f"falta el valor de {opcion}")
            valor = t[i]
        match tipo:
            case "nombre" if not NOMBRE.fullmatch(valor):
                raise ValueError(f"«{valor}» no es un nombre válido")
            case "red" if valor == "host" or valor.startswith("container:"):
                raise ValueError(f"--network {valor} comparte la red del equipo o de otro contenedor")
            case "montaje":
                valor = _montaje(valor, carpeta)
        salida += [opcion, valor]
        i += 1
    if i == len(t) or t[i] not in imagenes:
        raise ValueError(f"la imagen tiene que ser una de {', '.join(sorted(imagenes))}")
    return salida + t[i:]


def _montaje(valor: str, carpeta: Path) -> str:
    # En Windows, $(pwd) da C:\...: la letra de la unidad no separa origen y destino.
    unidad = valor[:2] if re.match(r"[A-Za-z]:[\\/]", valor) else ""
    origen, _, resto = valor[len(unidad):].partition(":")
    origen = unidad + origen
    destino, _, modo = resto.partition(":")
    if not destino.startswith("/") or modo not in ("", "ro", "rw"):
        raise ValueError(f"-v {valor} no tiene la forma origen:/ruta[:ro]")
    if not unidad and "/" not in origen and not origen.startswith("."):
        if not NOMBRE.fullmatch(origen):
            raise ValueError(f"«{origen}» no es un nombre de volumen válido")
        return valor
    ruta = (carpeta / origen).resolve()  # una ruta absoluta sustituye a carpeta
    if not ruta.is_relative_to(carpeta.resolve()):
        raise ValueError(f"-v monta {origen}, que está fuera de la carpeta del ejercicio")
    return ":".join([str(ruta), destino, *([modo] if modo else [])])
