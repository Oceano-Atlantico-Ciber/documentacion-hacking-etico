#!/usr/bin/env python3
"""Deja los ficheros de partida de cada ejercicio de API REST en tu repositorio de entregas.

Uso, desde cualquier carpeta de tu repositorio:

    py preparar.py e1                     (Windows; en Linux o macOS, python3)
    py preparar.py e3 --lenguaje go       (go, python o node)

Escribe en fundamentos/api/<ejercicio>/ y no hace commits. Los datos de la API (incidencias,
técnicos, usuarios) dependen de tu usuario de GitHub, que se deduce del remoto origin
(entregas-<usuario>): cada alumno tiene los suyos. En E1 además construye y arranca con Docker
la API de incidencias del laboratorio. Este mismo módulo es el que usa el corrector para saber
qué esperar, de modo que no hay que tocarlo.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

RAIZ = "fundamentos/api"
EJERCICIOS = tuple(f"e{n}" for n in range(1, 9))
LENGUAJES = ("go", "python", "node")
PLANTILLAS = Path(__file__).resolve().parent / "plantillas"

PRIORIDADES = ("baja", "media", "alta", "critica")
ESTADOS = ("abierta", "en-curso", "cerrada")
TECNICOS = ("lucia", "marcos", "sara", "ivan", "noa")
ASUNTOS = (
    "La VPN se corta cada pocos minutos", "No arranca el portátil", "Impresora sin tóner",
    "Contraseña caducada", "El correo no sincroniza", "Pantalla parpadea", "Alta de usuario nuevo",
    "Baja de usuario", "Sin acceso a la carpeta compartida", "El wifi no conecta",
    "Certificado del servidor web caducado", "Copia de seguridad fallida", "Teclado sin respuesta",
    "Actualizar el antivirus", "Licencia de ofimática caducada", "Correo sospechoso recibido",
    "Disco casi lleno", "Proyector de la sala no detecta el portátil", "Cambio de puesto",
    "Teléfono IP sin línea",
)
LUGARES = ("recepción", "contabilidad", "almacén", "sala de reuniones", "dirección", "soporte",
           "laboratorio", "planta 2", "planta 3", "teletrabajo")
COMENTARIOS = ("Reiniciado el equipo, sigue igual.", "Pedido el repuesto.", "Llamado al usuario, no contesta.",
               "Revisado en remoto.", "Pendiente de proveedor.", "Funciona tras actualizar.")


def etiqueta(ejercicio: str) -> str:
    return f"entrega-fundamentos-api-{ejercicio}"


def _azar(usuario: str, que: str) -> random.Random:
    return random.Random(hashlib.sha256(f"{usuario.lower()}:api-{que}".encode()).digest())


def huella(usuario: str, que: str = "") -> str:
    return hashlib.sha256(f"{usuario.lower()}:api-{que}".encode()).hexdigest()[:12]


def datos(usuario: str, cuantas: int = 12) -> dict:
    """Las incidencias y comentarios de partida de la API de un alumno."""
    azar = _azar(usuario, f"datos-{cuantas}")
    incidencias, comentarios = [], []
    for i in range(1, cuantas + 1):
        incidencias.append({
            "id": i,
            "titulo": f"{azar.choice(ASUNTOS)} ({azar.choice(LUGARES)})",
            "prioridad": azar.choice(PRIORIDADES),
            "estado": azar.choice(ESTADOS),
            "tecnico": azar.choice(TECNICOS + (None,)),
        })
        for _ in range(azar.choice((0, 0, 1, 2))):
            comentarios.append({"id": len(comentarios) + 1, "incidencia": i, "texto": azar.choice(COMENTARIOS)})
    return {"incidencias": incidencias, "comentarios": comentarios}


def incidencia_e1(usuario: str) -> int:
    return _azar(usuario, "e1").randint(1, 12)


def usuarios(usuario: str) -> dict:
    """Los usuarios del E8: un administrador y dos técnicos que ya tienen incidencias asignadas."""
    def secreto(que: str) -> str:
        return hashlib.sha256(f"{usuario.lower()}:api-e8-{que}".encode()).hexdigest()[:24]
    filas = [("admin", "Administración", "admin"), ("lucia", "Lucía", "tecnico"), ("marcos", "Marcos", "tecnico")]
    return {"usuarios": [{"usuario": u, "nombre": n, "rol": r, "clave": secreto(f"clave-{u}"), "token": secreto(f"token-{u}")}
                         for u, n, r in filas]}


def _json(objeto: object) -> str:
    return json.dumps(objeto, ensure_ascii=False, indent=2) + "\n"


def _plantilla(*ruta: str) -> str:
    return (PLANTILLAS.joinpath(*ruta)).read_text(encoding="utf-8")


def _carpeta(*ruta: str) -> dict[str, str]:
    base = PLANTILLAS.joinpath(*ruta)
    return {f.relative_to(base).as_posix(): f.read_text(encoding="utf-8") for f in sorted(base.rglob("*")) if f.is_file()}


# --- Ficheros de cada ejercicio ----------------------------------------------------------

def e1(usuario: str, lenguaje: str | None) -> dict[str, str]:
    ficheros = {f"laboratorio/{k}": v for k, v in _carpeta("laboratorio").items()}
    ficheros["laboratorio/incidencias.json"] = _json(datos(usuario))
    ficheros["enviar.py"] = _plantilla("e1", "enviar.py")
    ficheros["LEEME.md"] = _plantilla("e1", "LEEME.md").replace("{N}", str(incidencia_e1(usuario)))
    return ficheros


def e2(usuario: str, lenguaje: str | None) -> dict[str, str]:
    return _carpeta("e2")


def e3(usuario: str, lenguaje: str | None) -> dict[str, str]:
    ficheros = _carpeta(lenguaje)
    ficheros["incidencias.json"] = _json(datos(usuario))
    ficheros["contrato.yaml"] = _plantilla("contrato.yaml")
    ficheros["pruebas.py"] = _plantilla("pruebas.py")
    ficheros["lenguaje.txt"] = lenguaje + "\n"
    return ficheros


def e6(usuario: str, lenguaje: str | None) -> dict[str, str]:
    return {"casos.txt": _plantilla("e6", "casos.txt")}


def e7(usuario: str, lenguaje: str | None) -> dict[str, str]:
    return {"incidencias.json": _json(datos(usuario, 500))}


def e8(usuario: str, lenguaje: str | None) -> dict[str, str]:
    return {"usuarios.json": _json(usuarios(usuario))}


# E4 y E5 no traen ficheros nuevos: E4 sigue en la carpeta de E3 y E5 la copia (ver copiar()).
ESCENARIOS: dict[str, Callable[[str, str | None], dict[str, str]]] = {
    "e1": e1, "e2": e2, "e3": e3, "e6": e6, "e7": e7, "e8": e8,
}
CON_LENGUAJE = {"e3"}


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


def _docker(*args: str, cwd: Path) -> None:
    r = subprocess.run(["docker", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise Error(f"docker {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}  ¿Está Docker Desktop en marcha?")


def arrancar_laboratorio(carpeta: Path) -> None:
    """Construye la API del laboratorio y la deja escuchando en http://localhost:8080."""
    _docker("build", "-t", "api-incidencias:e1", "laboratorio", cwd=carpeta)
    subprocess.run(["docker", "rm", "-f", "api-e1"], capture_output=True)
    _docker("run", "-d", "--name", "api-e1", "-p", "8080:8080", "api-incidencias:e1", cwd=carpeta)


def preparar(ejercicio: str, lenguaje: str | None, cwd: Path) -> None:
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    usuario = usuario_de(_git("remote", "get-url", "origin", cwd=raiz))
    destino = raiz / RAIZ / ejercicio
    if ejercicio in ("e6", "e7", "e8"):
        # Cada uno sigue sobre las tres APIs del anterior: E6 sobre E5, E7 sobre E6 y E8 sobre E7.
        anterior = f"e{int(ejercicio[1]) - 1}"
        base = raiz / RAIZ / anterior
        if not base.exists():
            raise Error(f"primero hay que tener hecho el {anterior.upper()} ({RAIZ}/{anterior}/)")
        if destino.exists():
            raise Error(f"{ejercicio} ya está preparado (existe {destino})")
        shutil.copytree(base, destino, ignore=shutil.ignore_patterns("node_modules", ".venv", "__pycache__"))
        for nombre, contenido in ESCENARIOS[ejercicio](usuario, None).items():
            if ejercicio == "e6":
                _escribir(destino / nombre, contenido)
            else:
                for leng in LENGUAJES:
                    _escribir(destino / leng / nombre, contenido)
        print(f"{ejercicio} preparado para {usuario}: copia de {anterior}/ en {RAIZ}/{ejercicio}/ con los ficheros nuevos.")
        return
    if destino.exists():
        raise Error(f"{ejercicio} ya está preparado (existe {destino})")
    for nombre, contenido in ESCENARIOS[ejercicio](usuario, lenguaje).items():
        _escribir(destino / nombre, contenido)
    if ejercicio == "e1":
        arrancar_laboratorio(destino)
        print(f"La API del laboratorio escucha en http://localhost:8080. Tu incidencia es la {incidencia_e1(usuario)}.")
    print(f"{ejercicio} preparado para {usuario} en {RAIZ}/{ejercicio}/. Sigue el enunciado.")


def copiar(origen: str, destino: str, cwd: Path) -> None:
    """E4 continúa en e3 copiado a e4; E5 reparte el E4 en su carpeta de lenguaje."""
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    de, a = raiz / RAIZ / origen, raiz / RAIZ / destino
    if not de.exists():
        raise Error(f"primero hay que tener hecho el {origen.upper()} ({RAIZ}/{origen}/)")
    if a.exists():
        raise Error(f"{destino} ya está preparado (existe {a})")
    ignorar = shutil.ignore_patterns("node_modules", ".venv", "__pycache__")
    if destino == "e5":
        lenguaje = (de / "lenguaje.txt").read_text(encoding="utf-8").strip()
        shutil.copytree(de, a / lenguaje, ignore=ignorar)
        usuario = usuario_de(_git("remote", "get-url", "origin", cwd=raiz))
        for otro in LENGUAJES:
            if otro != lenguaje:
                for nombre, contenido in e3(usuario, otro).items():
                    _escribir(a / otro / nombre, contenido)
        print(f"e5 preparado: tu API de {lenguaje} en {RAIZ}/e5/{lenguaje}/ y los esqueletos de los otros dos.")
    else:
        shutil.copytree(de, a, ignore=ignorar)
        print(f"{destino} preparado: copia de {origen}/ en {RAIZ}/{destino}/.")


def main(argv: list[str]) -> int:
    uso = "uso: py preparar.py {e1,e2,e3,e4,e5,e6,e7,e8} [--lenguaje go|python|node]  (--lenguaje solo en e3)"
    if not argv or argv[0] not in EJERCICIOS:
        print(uso, file=sys.stderr)
        return 2
    ejercicio, resto = argv[0], argv[1:]
    lenguaje = None
    if ejercicio in CON_LENGUAJE:
        if len(resto) != 2 or resto[0] != "--lenguaje" or resto[1] not in LENGUAJES:
            print(uso, file=sys.stderr)
            return 2
        lenguaje = resto[1]
    elif resto:
        print(uso, file=sys.stderr)
        return 2
    try:
        if ejercicio == "e4":
            copiar("e3", "e4", Path.cwd())
        elif ejercicio == "e5":
            copiar("e4", "e5", Path.cwd())
        else:
            preparar(ejercicio, lenguaje, Path.cwd())
    except Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
