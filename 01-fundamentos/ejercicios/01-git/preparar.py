#!/usr/bin/env python3
"""Prepara el punto de partida de cada ejercicio de git en tu repositorio de entregas.

Uso, desde cualquier carpeta de tu repositorio y con el árbol de trabajo limpio:

    python3 preparar.py e3

Crea las ramas, commits y ficheros de partida del ejercicio. El contenido depende de tu
usuario de GitHub (se deduce del remoto origin, entregas-<usuario>), así que cada alumno
tiene su propio escenario. Este mismo módulo es el que usa el corrector para saber qué
esperar, de modo que no hay que tocarlo.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, NamedTuple

RAIZ = "fundamentos/git"
RAMA_PRINCIPAL = "main"
EJERCICIOS = tuple(f"e{n}" for n in range(1, 9))
CONVENTIONAL = re.compile(r"^(feat|fix|docs|style|refactor|test|chore)(\([\w-]+\))?!?: \S")


class Commit(NamedTuple):
    mensaje: str
    cambios: Mapping[str, str | None]  # ruta dentro de la carpeta del ejercicio -> contenido (None borra)


class Rama(NamedTuple):
    nombre: str | None  # None: los commits van en main; si no, la rama sale de main en ese momento
    commits: tuple[Commit, ...]


class Escenario(NamedTuple):
    sueltos: Mapping[str, str]  # ficheros que se dejan sin commitear
    ramas: tuple[Rama, ...]  # se aplican en orden


def ruta(ejercicio: str, nombre: str) -> str:
    return f"{RAIZ}/{ejercicio}/{nombre}"


def etiqueta(ejercicio: str) -> str:
    return f"entrega-fundamentos-git-{ejercicio}"


def _semilla(usuario: str, ejercicio: str) -> bytes:
    return hashlib.sha256(f"{usuario.lower()}:{ejercicio}".encode()).digest()


def _huella(usuario: str, ejercicio: str, n: int = 12) -> str:
    return _semilla(usuario, ejercicio).hex()[:n]


def _elegir(opciones: tuple, usuario: str, ejercicio: str, k: int) -> list:
    """k elementos distintos de opciones, en un orden que depende del alumno."""
    semilla = _semilla(usuario, ejercicio)
    return sorted(opciones, key=lambda o: hashlib.sha256(semilla + str(o).encode()).digest())[:k]


# --- Escenarios ---------------------------------------------------------------------------

PUERTOS = {21: "ftp", 22: "ssh", 25: "smtp", 53: "dns", 80: "http", 110: "pop3", 143: "imap",
           443: "https", 445: "smb", 3306: "mysql", 3389: "rdp", 5432: "postgresql",
           6379: "redis", 8080: "http-alt", 9200: "elasticsearch"}
HERRAMIENTAS = ("nmap", "Wireshark", "Burp Suite", "Metasploit", "Trivy", "Suricata", "hashcat",
                "John the Ripper", "sqlmap", "ffuf", "Nikto", "Hydra")


def _lineas(puertos) -> str:
    return "".join(f"{p} {PUERTOS[p]}\n" for p in puertos)


def e1(usuario: str) -> Escenario:
    h = _huella(usuario, "e1")
    uno, dos, tres = _elegir(HERRAMIENTAS, usuario, "e1", 3)
    return Escenario(sueltos={
        "objetivo.md": f"# Objetivo\n\nAuditar la empresa ficticia en la cuenta emulada de {usuario}.\nReferencia: {h}\n",
        "herramientas.md": f"# Herramientas\n\n- {uno}\n- {dos}\n- {tres}\n",
        "notas.md": f"# Notas\n\nTodo lo que se haga queda dentro del alcance firmado ({h[:6]}).\n",
    }, ramas=())


E2_COMMITEAR = ("app.py",)
E2_IGNORAR = ("build/salida.bin", "depuracion.log", ".env")


def e2(usuario: str) -> Escenario:
    h = _huella(usuario, "e2")
    return Escenario(sueltos={
        "app.py": f'"""Inventario de la empresa ({h})."""\n\nprint("inventario listo")\n',
        "build/salida.bin": f"binario generado {h}\n",
        "depuracion.log": f"DEBUG arranque {h}\n",
        ".env": f"DB_PASSWORD=oa-{h}\n",
    }, ramas=())


E3_FF, E3_NOFF = "feat(e3): rama para fast-forward", "feat(e3): rama para merge con commit"


def e3(usuario: str) -> Escenario:
    h = _huella(usuario, "e3")
    return Escenario(sueltos={}, ramas=(
        Rama("git/e3-ff", (Commit(E3_FF, {"ff.txt": f"fast-forward {h}\n"}),)),
        Rama("git/e3-noff", (Commit(E3_NOFF, {"noff.txt": f"merge con commit {h}\n"}),)),
    ))


E4_BASE, E4_A, E4_B = "feat(e4): inventario de puertos", "feat(e4): puerto encontrado por A", "feat(e4): puerto encontrado por B"
E4_FICHERO = "puertos.txt"


def _e4_puertos(usuario: str) -> tuple[list[int], int, int]:
    *base, a, b = _elegir(tuple(PUERTOS), usuario, "e4", 5)
    return sorted(base), a, b


def e4_resuelto(usuario: str) -> str:
    """Contenido esperado tras resolver el conflicto: todas las líneas, ordenadas por puerto."""
    base, a, b = _e4_puertos(usuario)
    return _lineas(sorted([*base, a, b]))


def e4(usuario: str) -> Escenario:
    base, a, b = _e4_puertos(usuario)
    return Escenario(sueltos={}, ramas=(
        Rama(None, (Commit(E4_BASE, {E4_FICHERO: _lineas(base)}),)),
        Rama("git/e4-a", (Commit(E4_A, {E4_FICHERO: _lineas(base) + _lineas([a])}),)),
        Rama("git/e4-b", (Commit(E4_B, {E4_FICHERO: _lineas(base) + _lineas([b])}),)),
    ))


E5_F1, E5_F2, E5_MAIN = "feat(e5): escaneo de la red", "feat(e5): informe del escaneo", "chore(e5): cambio publicado en main"


def e5(usuario: str) -> Escenario:
    h = _huella(usuario, "e5")
    return Escenario(sueltos={}, ramas=(
        Rama("git/e5-feature", (
            Commit(E5_F1, {"escaneo.txt": f"nmap -sn 172.28.0.0/24  # {h}\n"}),
            Commit(E5_F2, {"informe.txt": f"Tres equipos activos ({h[:6]}).\n"}),
        )),
        Rama(None, (Commit(E5_MAIN, {"main.txt": f"cambio de otro compañero {h}\n"}),)),
    ))


E6_WIP = "wip(e6)"
E6_MENSAJE = "docs(e6): informe de alcance"
E6_FICHERO = "informe.md"


def _e6_versiones(usuario: str) -> list[str]:
    h = _huella(usuario, "e6")
    partes = ["# Informe de alcance\n", f"\nObjetivo: cuenta emulada de {usuario}.\n",
              "\nPermitido: reconocimiento y enumeración.\n", f"\nAutoriza: el docente. Ref. {h}\n"]
    return ["".join(partes[:i]) for i in range(1, len(partes) + 1)]


def e6_final(usuario: str) -> str:
    return _e6_versiones(usuario)[-1]


def e6(usuario: str) -> Escenario:
    return Escenario(sueltos={}, ramas=(Rama("git/e6-wip", tuple(
        Commit(f"{E6_WIP}: paso {i}", {E6_FICHERO: v}) for i, v in enumerate(_e6_versiones(usuario), 1)
    )),))


E7_C1, E7_C2, E7_C3 = "feat(e7): configuración del servidor", "feat(e7): activar modo depuración", "docs(e7): instrucciones de despliegue"
E7_FICHERO = "config.ini"


def e7_config(usuario: str) -> str:
    return f"[servidor]\npuerto = 8443\ndebug = false\nid = {_huella(usuario, 'e7')}\n"


def e7(usuario: str) -> Escenario:
    buena = e7_config(usuario)
    return Escenario(sueltos={}, ramas=(Rama(None, (
        Commit(E7_C1, {E7_FICHERO: buena}),
        Commit(E7_C2, {E7_FICHERO: buena.replace("debug = false", "debug = true")}),
        Commit(E7_C3, {"README.md": "Desplegar con: python3 servidor.py\n"}),
    )),))


E8_A1, E8_A2, E8_A3, E8_A4 = ("feat(e8): cliente de la API", "feat(e8): conexión con clave",
                              "chore(e8): no versionar .env", "docs(e8): instrucciones")
E8_HALLAZGO = "hallazgo.txt"


def e8_clave(usuario: str) -> str:
    return f"oa-{_semilla(usuario, 'e8-clave').hex()[:32]}"


E8_APP = 'import os\n\nCLAVE = os.environ["API_KEY"]\nprint("conectado")\n'


def e8(usuario: str) -> Escenario:
    return Escenario(sueltos={}, ramas=(Rama("git/e8-app", (
        Commit(E8_A1, {"app.py": 'print("conectado")\n'}),
        Commit(E8_A2, {"app.py": E8_APP, ".env": f"API_KEY={e8_clave(usuario)}\n"}),
        Commit(E8_A3, {".env": None, ".gitignore": ".env\n"}),
        Commit(E8_A4, {"README.md": "Exporta API_KEY antes de ejecutar app.py.\n"}),
    )),))


ESCENARIOS = {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e6": e6, "e7": e7, "e8": e8}


# --- Aplicación en el repositorio del alumno ----------------------------------------------

class Error(Exception):
    pass


def _git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise Error(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def _escribir(fichero: Path, contenido: str) -> None:
    fichero.parent.mkdir(parents=True, exist_ok=True)
    fichero.write_text(contenido, encoding="utf-8", newline="\n")


def usuario_de(remoto: str) -> str:
    m = re.search(r"/entregas-([A-Za-z0-9-]+?)(?:\.git)?/?$", remoto)
    if not m:
        raise Error(f"el remoto origin ({remoto}) no es un repositorio entregas-<usuario>")
    return m.group(1).lower()


def preparar(ejercicio: str, cwd: Path) -> None:
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    usuario = usuario_de(_git("remote", "get-url", "origin", cwd=raiz))
    if _git("branch", "--show-current", cwd=raiz) != RAMA_PRINCIPAL:
        raise Error(f"cámbiate a {RAMA_PRINCIPAL} antes de preparar el ejercicio")
    if _git("status", "--porcelain", cwd=raiz):
        raise Error("tienes cambios sin commitear: haz commit o descártalos antes")
    escenario = ESCENARIOS[ejercicio](usuario)
    carpeta = raiz / RAIZ / ejercicio
    existentes = [r.nombre for r in escenario.ramas if r.nombre and _git("branch", "--list", r.nombre, cwd=raiz)]
    if existentes or (escenario.sueltos and carpeta.exists()):
        raise Error(f"{ejercicio} ya está preparado (existe {', '.join(existentes) or carpeta})")

    for nombre, contenido in escenario.sueltos.items():
        _escribir(carpeta / nombre, contenido)
    for rama in escenario.ramas:
        if rama.nombre:
            _git("switch", "-c", rama.nombre, cwd=raiz)
        for commit in rama.commits:
            for nombre, contenido in commit.cambios.items():
                fichero = carpeta / nombre
                if contenido is None:
                    _git("rm", "-q", str(fichero), cwd=raiz)
                else:
                    _escribir(fichero, contenido)
                    _git("add", "-f", str(fichero), cwd=raiz)  # -f: la plantilla ya ignora .env
            _git("commit", "-q", "-m", commit.mensaje, cwd=raiz)
        if rama.nombre:
            _git("switch", RAMA_PRINCIPAL, cwd=raiz)
    print(f"{ejercicio} preparado para {usuario} en {RAIZ}/{ejercicio}/. Sigue el enunciado.")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ESCENARIOS:
        print(f"uso: python3 preparar.py {{{','.join(EJERCICIOS)}}}", file=sys.stderr)
        return 2
    try:
        preparar(argv[0], Path.cwd())
    except Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
