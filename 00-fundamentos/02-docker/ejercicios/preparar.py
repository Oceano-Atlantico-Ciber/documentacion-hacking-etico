#!/usr/bin/env python3
"""Deja los ficheros de partida de cada ejercicio de Docker en tu repositorio de entregas.

Uso, desde cualquier carpeta de tu repositorio:

    py preparar.py e1        (Windows; en Linux o macOS, python3)

Escribe en fundamentos/docker/<ejercicio>/ y no hace commits. Algunos ficheros dependen de tu
usuario de GitHub (se deduce del remoto origin, entregas-<usuario>), así que cada alumno tiene
los suyos. En E4 además construye con Docker la imagen que vas a auditar. Este mismo módulo es
el que usa el corrector para saber qué esperar, de modo que no hay que tocarlo.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping

RAIZ = "fundamentos/docker"
EJERCICIOS = tuple(f"e{n}" for n in range(1, 9))


def etiqueta(ejercicio: str) -> str:
    return f"entrega-fundamentos-docker-{ejercicio}"


def _semilla(usuario: str, ejercicio: str) -> bytes:
    return hashlib.sha256(f"{usuario.lower()}:docker-{ejercicio}".encode()).digest()


def huella(usuario: str, ejercicio: str) -> str:
    return _semilla(usuario, ejercicio).hex()[:12]


def _pagina(usuario: str, ejercicio: str, titulo: str) -> str:
    return (f'<!doctype html>\n<html lang="es">\n<meta charset="utf-8">\n<title>{titulo}</title>\n'
            f"<h1>{titulo}</h1>\n<p>Puesto de {usuario} · referencia {huella(usuario, ejercicio)}</p>\n</html>\n")


# --- E1 · Ciclo de vida ------------------------------------------------------------------

def e1_pagina(usuario: str) -> str:
    return _pagina(usuario, "e1", "Servidor web de la empresa")


def e1(usuario: str) -> Mapping[str, str]:
    return {"index.html": e1_pagina(usuario)}


# --- E2 · Tu primera imagen --------------------------------------------------------------

SONDEO = '''"""Sondeo de puertos TCP: dice qué puertos de un equipo aceptan conexiones.

Uso: python sondeo.py EQUIPO PUERTO [PUERTO...]
"""

import socket
import sys


def abierto(ip: str, puerto: int, espera: float = 1.0) -> bool:
    try:
        with socket.create_connection((ip, puerto), timeout=espera):
            return True
    except OSError:
        return False


def main(argv: list[str]) -> int:
    if len(argv) < 2 or not all(p.isdigit() for p in argv[1:]):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    equipo, *puertos = argv
    try:
        ip = socket.gethostbyname(equipo)
    except OSError:
        print(f"{equipo}: no existe ese equipo", file=sys.stderr)
        return 1
    for puerto in map(int, puertos):
        print(f"{equipo}:{puerto} {'abierto' if abierto(ip, puerto) else 'cerrado'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def e2(usuario: str) -> Mapping[str, str]:
    return {"sondeo.py": SONDEO}


# --- E3 · Capas, caché y .dockerignore ---------------------------------------------------

E3_DOCKERFILE = """FROM python:3.12-alpine
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
"""
E3_APP = """# Cliente de la API de la empresa.
import requests

print(f"cliente de la API listo (requests {requests.__version__})")
"""


def e3_token(usuario: str) -> str:
    return f"oa-{_semilla(usuario, 'e3-token').hex()[:32]}"


def e3(usuario: str) -> Mapping[str, str]:
    return {
        "Dockerfile": E3_DOCKERFILE,
        "app.py": E3_APP,
        "requirements.txt": "requests==2.32.3\n",
        ".env": f"API_TOKEN={e3_token(usuario)}\n",
        "notas/pendiente.md": "# Pendiente\n\n- Pedir al cliente la lista de equipos fuera del alcance.\n",
    }


# --- E4 · El secreto de la capa ----------------------------------------------------------

E4_IMAGEN = "e4-informe:1.0"
E4_CLAVE = "api.key"
E4_DOCKERFILE = f"""# Generador de informes de la empresa. Lo construyó el equipo anterior.
FROM python:3.12-alpine
WORKDIR /app
COPY informe.py .
COPY {E4_CLAVE} .
RUN python informe.py --comprobar {E4_CLAVE} && rm {E4_CLAVE}
CMD ["python", "informe.py"]
"""
E4_INFORME = '''"""Generador de informes de la empresa. Con --comprobar RUTA valida la clave de la API."""

import re
import sys
from pathlib import Path


def comprobar(ruta: str) -> int:
    if not re.fullmatch(r"oa-[0-9a-f]{32}", Path(ruta).read_text(encoding="utf-8").strip()):
        print("clave de la API con formato incorrecto", file=sys.stderr)
        return 1
    print("clave de la API válida")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--comprobar":
        sys.exit(comprobar(sys.argv[2]))
    print("informe de la empresa: sin hallazgos nuevos")
'''


def e4_clave(usuario: str) -> str:
    return f"oa-{_semilla(usuario, 'e4-clave').hex()[:32]}"


def e4(usuario: str) -> Mapping[str, str]:
    return {"Dockerfile": E4_DOCKERFILE, "informe.py": E4_INFORME, ".gitignore": "*.tar\ncapas/\n"}


def e4_construir(carpeta: Path, usuario: str) -> None:
    """Construye la imagen con la clave dentro y borra la clave: al alumno solo le queda la imagen."""
    clave = carpeta / E4_CLAVE
    _escribir(clave, e4_clave(usuario) + "\n")
    try:
        r = subprocess.run(["docker", "build", "-q", "-t", E4_IMAGEN, str(carpeta)], capture_output=True, text=True)
    finally:
        clave.unlink()
    if r.returncode:
        raise Error(f"docker build: {r.stderr.strip()}. ¿Está Docker Desktop en marcha?")


# --- E5 · Datos que sobreviven -----------------------------------------------------------

def e5_pagina(usuario: str) -> str:
    return _pagina(usuario, "e5", "Portal de la empresa")


def e5(usuario: str) -> Mapping[str, str]:
    return {"web/index.html": e5_pagina(usuario)}


# --- E8 · Auditar un compose -------------------------------------------------------------

E8_COMPOSE = """# Panel de administración de la empresa. Lo dejó así el equipo anterior.
name: e8-panel
services:
  web:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./:/usr/share/nginx/html

  panel:
    build: ./panel
    ports:
      - "8000:8000"
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      ADMIN_PASSWORD: admin123

  datos:
    image: postgres:alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: admin123
"""
E8_PANEL_DOCKERFILE = """FROM python:alpine
WORKDIR /app
COPY panel.py .
EXPOSE 8000
CMD ["python", "panel.py"]
"""
E8_PANEL = '''"""Panel de administración mínimo: responde en el puerto 8000 si tiene contraseña configurada."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer

if not os.environ.get("ADMIN_PASSWORD"):
    raise SystemExit("falta ADMIN_PASSWORD")


class Panel(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        cuerpo = "panel de administración: acceso restringido\\n".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


HTTPServer(("0.0.0.0", 8000), Panel).serve_forever()
'''


def e8(usuario: str) -> Mapping[str, str]:
    return {
        "docker-compose.yml": E8_COMPOSE,
        "panel/Dockerfile": E8_PANEL_DOCKERFILE,
        "panel/panel.py": E8_PANEL,
        "web/index.html": _pagina(usuario, "e8", "Intranet de la empresa"),
    }


# E6 y E7 no tienen ficheros de partida: se escriben desde cero.
ESCENARIOS: Mapping[str, Callable[[str], Mapping[str, str]]] = {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e8": e8}
DESPUES: Mapping[str, Callable[[Path, str], None]] = {"e4": e4_construir}


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
    fichero.write_text(contenido, encoding="utf-8", newline="\n")  # LF: los lee Linux, dentro del contenedor


def usuario_de(remoto: str) -> str:
    m = re.search(r"/entregas-([A-Za-z0-9-]+?)(?:\.git)?/?$", remoto)
    if not m:
        raise Error(f"el remoto origin ({remoto}) no es un repositorio entregas-<usuario>")
    return m.group(1).lower()


def preparar(ejercicio: str, cwd: Path) -> None:
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    usuario = usuario_de(_git("remote", "get-url", "origin", cwd=raiz))
    carpeta = raiz / RAIZ / ejercicio
    if carpeta.exists():
        raise Error(f"{ejercicio} ya está preparado (existe {carpeta})")
    for nombre, contenido in ESCENARIOS[ejercicio](usuario).items():
        _escribir(carpeta / nombre, contenido)
    if ejercicio in DESPUES:
        DESPUES[ejercicio](carpeta, usuario)
    print(f"{ejercicio} preparado para {usuario} en {RAIZ}/{ejercicio}/. Sigue el enunciado.")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ESCENARIOS:
        print(f"uso: py preparar.py {{{','.join(ESCENARIOS)}}}  (E6 y E7 no necesitan preparación)", file=sys.stderr)
        return 2
    try:
        preparar(argv[0], Path.cwd())
    except Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
