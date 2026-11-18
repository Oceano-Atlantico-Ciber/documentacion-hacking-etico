#!/usr/bin/env python3
"""Deja los ficheros de partida de un ejercicio del RA1 en tu repositorio de entregas.

Uso, desde cualquier carpeta de tu repositorio:

    py ../documentacion-hacking-etico/01-hacking-etico/preparar.py u1-e1     (Windows; en Linux o macOS, python3)

Escribe en ra1/<ejercicio>/ y no hace commits. Cada alumno tiene su propio escenario (casos, direcciones,
fechas, registros…), generado a partir de su usuario de GitHub, que se deduce del remoto origin
(entregas-<usuario>). Este mismo módulo es el que usan el corrector y pruebas.py para saber qué esperar, de
modo que no hay que tocarlo.
"""

from __future__ import annotations

import hashlib
import random
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Mapping

AQUI = Path(__file__).resolve().parent
RAIZ = "ra1"
UNIDADES = {
    "u1": "01-que-es-el-hacking-etico",
    "u2": "02-permisos-y-alcance",
    "u3": "03-vulnerabilidades-y-ataques",
    "u4": "04-herramientas-y-monitorizacion",
}
EJERCICIOS = ("u1-e1", "u1-e2", "u2-e1", "u2-e2", "u3-e1", "u3-e2", "u3-e3", "u4-e1", "u4-e2", "u4-e3")


def etiqueta(ejercicio: str) -> str:
    return f"entrega-ra1-{ejercicio}"


def plantilla(ejercicio: str) -> Path:
    unidad, ej = ejercicio.split("-")
    return AQUI / UNIDADES[unidad] / "ejercicios" / "plantillas" / ej


def _semilla(usuario: str, ejercicio: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{usuario.lower()}:ra1-{ejercicio}".encode()).digest()[:8], "big")


def huella(usuario: str, ejercicio: str) -> str:
    return hashlib.sha256(f"{usuario.lower()}:ra1-{ejercicio}".encode()).hexdigest()[:6]


def _azar(usuario: str, ejercicio: str) -> random.Random:
    return random.Random(_semilla(usuario, ejercicio))


def _leer(ejercicio: str, nombre: str) -> str:
    return (plantilla(ejercicio) / nombre).read_text(encoding="utf-8")


# --- U1·E1 · ¿Hacking ético o delito? ------------------------------------------------------------
# El banco es público; qué figura y qué artículo corresponden a cada caso solo lo sabe el corrector.

CASOS = {
    "A01": "Una consultora firma un contrato con una cadena de gimnasios para probar la seguridad de su web durante dos semanas. Prueba solo las direcciones del contrato y entrega un informe.",
    "A02": "Un estudiante adivina la contraseña del correo de su expareja, entra y lee sus mensajes.",
    "A03": "Un colectivo deja sin servicio la web de un ministerio durante una tarde, con miles de peticiones, como protesta por una ley.",
    "A04": "Una investigadora encuentra un fallo en una aplicación de una empresa con programa de recompensas, sigue sus reglas y lo comunica por el canal del programa.",
    "A05": "Alguien vende en un foro un programa que graba lo que se teclea en un ordenador ajeno y envía las contraseñas a quien lo compra.",
    "A06": "Un administrador de sistemas, el día que lo despiden, borra la base de datos de clientes de la empresa.",
    "A07": "Un auditor contratado para probar la web de una tienda entra en el servidor de correo de su proveedor, que no estaba en el contrato, para ver si era vulnerable.",
    "A08": "Un grupo ecologista entra sin permiso en el servidor de una petrolera para leer sus correos internos.",
    "A09": "En una cafetería, alguien captura el tráfico de la wifi para leer los mensajes de los demás clientes.",
    "A10": "La responsable de informática de un instituto, con la autorización firmada del director, escanea la red del centro buscando equipos sin actualizar.",
    "A11": "Un alumno satura la plataforma de exámenes del instituto con peticiones para que no se pueda hacer un examen.",
    "A12": "Un ransomware cifra los ficheros de una empresa y deja una nota pidiendo un rescate.",
    "A13": "Un grupo animalista borra la base de datos de clientes de una empresa de caza como protesta.",
    "A14": "Un equipo rojo contratado por la dirección de un banco simula durante tres semanas un ataque real, dentro de lo firmado.",
    "A15": "Alguien publica en un foro listas de usuarios y contraseñas robadas para que otros puedan entrar en esas cuentas.",
    "A16": "Un técnico entra sin permiso en el ordenador de un compañero para leer sus documentos.",
    "A17": "Un grupo inunda con tráfico la web de una empresa de armamento hasta tumbarla, en protesta por una guerra.",
    "A18": "Una empresa contrata a un auditor para probar la wifi de su hotel; lo hace en las fechas y redes acordadas.",
    "A19": "Un exempleado entra con su antigua contraseña, que nadie desactivó, en el programa de nóminas de la empresa.",
    "A20": "Un empleado enfadado borra los ficheros del servidor compartido de su departamento antes de irse de vacaciones.",
}


def u1_e1_casos(usuario: str) -> list[str]:
    return sorted(_azar(usuario, "u1-e1").sample(sorted(CASOS), 8))


def u1_e1(usuario: str) -> Mapping[str, str]:
    filas = "\n".join(f"| {c} | | |" for c in u1_e1_casos(usuario))
    lista = "\n".join(f"- **{c}.** {CASOS[c]}" for c in u1_e1_casos(usuario))
    return {"casos.md": _leer("u1-e1", "casos.md").format(lista=lista, filas=filas)}


# --- U1·E2 · El security.txt de la empresa --------------------------------------------------------

def u1_e2_datos(usuario: str) -> dict[str, str]:
    h = huella(usuario, "u1-e2")
    dominio = f"empresa-{h}.test"
    return {"dominio": dominio, "contacto": f"mailto:seguridad-{h}@{dominio}",
            "politica": f"https://{dominio}/seguridad", "canonica": f"https://{dominio}/.well-known/security.txt"}


def u1_e2(usuario: str) -> Mapping[str, str]:
    return {"LEEME.md": _leer("u1-e2", "LEEME.md").format(**u1_e2_datos(usuario)),
            "docker-compose.yml": _leer("u1-e2", "docker-compose.yml"),
            "web/index.html": _leer("u1-e2", "web/index.html").format(**u1_e2_datos(usuario))}


# --- U2·E1 · El alcance de la clínica -------------------------------------------------------------

def u2_e1_encargo(usuario: str) -> dict:
    r = _azar(usuario, "u2-e1")
    web = r.randrange(10, 240)
    red = r.randrange(10, 250)
    inicio = datetime(2027, 2, 1) + timedelta(days=r.randrange(0, 10))
    desde, hasta = r.choice((("20:00", "07:00"), ("21:00", "06:00"), ("22:00", "07:00")))
    return {
        "web": f"203.0.113.{web}", "citas": f"203.0.113.{web + 1}", "red": f"192.168.{red}.0/24",
        "datafono": f"192.168.{red}.{r.randrange(200, 250)}", "otra": f"198.51.100.{r.randrange(1, 250)}",
        "inicio": inicio.strftime("%Y-%m-%d"), "fin": (inicio + timedelta(days=11)).strftime("%Y-%m-%d"),
        "desde": desde, "hasta": hasta,
    }


def u2_e1(usuario: str) -> Mapping[str, str]:
    e = u2_e1_encargo(usuario)
    inicio, fin = datetime.fromisoformat(e["inicio"]), datetime.fromisoformat(e["fin"])
    texto = {**e, "inicio_texto": f"{inicio.day} de febrero de 2027", "fin_texto": f"{fin.day} de febrero de 2027"}
    return {"LEEME.md": _leer("u2-e1", "LEEME.md").format(**texto),
            "alcance.json": _leer("u2-e1", "alcance.json"),
            "en_alcance.py": _leer("u2-e1", "en_alcance.py")}


# --- U2·E2 · Un alcance con fallos ----------------------------------------------------------------
# Doce cláusulas; cuáles tienen fallo y de qué tipo solo lo sabe el corrector. Cada alumno las ve en otro orden.

CLAUSULAS = (
    "El cliente es Transportes Atlántico SL, con sede en Vigo.",
    "La prueba la autoriza el becario del departamento de sistemas, que lo comentó de palabra en una reunión.",
    "Se prueba la red de la empresa, la web y lo que el auditor vaya encontrando conectado a ellas.",
    "No se prueba la centralita telefónica, 10.0.5.20.",
    "La prueba durará unas dos semanas, a partir de cuando el auditor tenga hueco.",
    "Se permite el escaneo de puertos, la búsqueda de vulnerabilidades y la explotación sin modificar ni borrar datos.",
    "Para medir la resistencia de la web, se lanzará una denegación de servicio un martes a mediodía.",
    "Como prueba de acceso, el auditor descargará la base de datos de clientes completa a su portátil.",
    "En caso de incidencia se llama a Ana Pérez, responsable de sistemas, en el 600 111 222, disponible las 24 horas durante la prueba.",
    "La web está en un servidor que la empresa alquila a HostingCo. No hace falta avisarles.",
    "El informe se entrega cifrado y solo a la dirección.",
    "Firman el auditor y el director general, el 10/01/2027.",
)


def u2_e2_orden(usuario: str) -> list[int]:
    """Qué cláusula original es la C1, C2…: un índice de CLAUSULAS por posición."""
    orden = list(range(len(CLAUSULAS)))
    _azar(usuario, "u2-e2").shuffle(orden)
    return orden


def u2_e2(usuario: str) -> Mapping[str, str]:
    lista = "\n".join(f"- **C{n}.** {CLAUSULAS[i]}" for n, i in enumerate(u2_e2_orden(usuario), 1))
    return {"fallos.md": _leer("u2-e2", "fallos.md").format(clausulas=lista)}


# --- U3·E1 · Ficha de Hackea el ranking -----------------------------------------------------------

def u3_e1(usuario: str) -> Mapping[str, str]:
    return {"ranking.md": _leer("u3-e1", "ranking.md")}


# --- U3·E2 · Ficha de un CVE real -----------------------------------------------------------------
# Antiguos y estables: sus datos en KEV y NVD ya no cambian. El corrector guarda una copia.

CVES = (
    "CVE-2021-44228", "CVE-2017-0144", "CVE-2014-6271", "CVE-2021-26855", "CVE-2019-0708", "CVE-2018-13379",
    "CVE-2019-19781", "CVE-2020-1472", "CVE-2021-34527", "CVE-2022-22965", "CVE-2023-34362", "CVE-2017-5638",
    "CVE-2021-41773", "CVE-2022-30190", "CVE-2023-4966", "CVE-2024-3400", "CVE-2018-7600", "CVE-2019-11510",
    "CVE-2022-1388", "CVE-2023-22515",
)


def u3_e2_cve(usuario: str) -> str:
    return CVES[_semilla(usuario, "u3-e2") % len(CVES)]


def u3_e2(usuario: str) -> Mapping[str, str]:
    return {"ficha.json": _leer("u3-e2", "ficha.json").replace("{cve}", u3_e2_cve(usuario))}


# --- U3·E3 · El registro de un incidente ----------------------------------------------------------

EMPLEADOS = ("marta", "luis", "carmen", "jorge", "lucia", "pablo", "elena", "raul")
SOSPECHOSOS = ("administrador", "admin", "contabilidad", "soporte", "backup", "usuario", "test", "recepcion")


def u3_e3_incidente(usuario: str) -> dict:
    """Lo que hizo el atacante en el escenario de este alumno y el registro que lo cuenta."""
    r = _azar(usuario, "u3-e3")
    atacante = f"198.51.100.{r.randrange(2, 250)}"
    otros = [f"203.0.113.{r.randrange(2, 250)}" for _ in range(3)]
    oficina = [f"10.0.0.{r.randrange(10, 60)}" for _ in EMPLEADOS]
    victima = r.choice(EMPLEADOS)
    creado = f"soporte{r.randrange(2, 99)}"
    servicio = r.choice(("AnyDesk", "TeamViewer", "RustDesk"))
    eventos: list[tuple[datetime, str, int, str, str, str]] = []
    t = datetime(2026, 11, 1, 8, 0, 0)
    for _ in range(40):  # el día normal
        t += timedelta(minutes=r.randrange(5, 15), seconds=r.randrange(60))
        i = r.randrange(len(EMPLEADOS))
        eventos.append((t, "Seguridad", 4624, oficina[i], EMPLEADOS[i], "Inicio de sesión correcto (tipo 2)"))
        if r.random() < 0.15:
            eventos.append((t - timedelta(seconds=20), "Seguridad", 4625, oficina[i], EMPLEADOS[i], "Error de inicio de sesión: contraseña incorrecta"))
        if r.random() < 0.2:
            eventos.append((t, "Cortafuegos", 5152, r.choice(otros), "", f"Paquete bloqueado al puerto {r.choice((22, 80, 445))}"))
    escaneo = datetime(2026, 11, 2, 1, r.randrange(0, 20), r.randrange(60))
    for k, puerto in enumerate(r.sample((21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 1433, 3306, 5432, 5900, 8080, 8443), 15)):
        eventos.append((escaneo + timedelta(seconds=k), "Cortafuegos", 5152, atacante, "", f"Paquete bloqueado al puerto {puerto}"))
    eventos.append((escaneo + timedelta(seconds=16), "Cortafuegos", 5156, atacante, "", "Conexión permitida al puerto 3389"))
    fallidos = r.randrange(18, 45)
    t = escaneo + timedelta(minutes=r.randrange(10, 40))
    for _ in range(fallidos):
        t += timedelta(seconds=r.randrange(2, 9))
        eventos.append((t, "Seguridad", 4625, atacante, r.choice(SOSPECHOSOS + (victima,)), "Error de inicio de sesión: contraseña incorrecta (tipo 10)"))
    acceso = t + timedelta(seconds=r.randrange(2, 9))
    eventos.append((acceso, "Seguridad", 4624, atacante, victima, "Inicio de sesión correcto (tipo 10, escritorio remoto)"))
    t = acceso + timedelta(minutes=r.randrange(3, 12))
    eventos.append((t, "Seguridad", 4720, atacante, victima, f"Se creó la cuenta de usuario {creado}"))
    eventos.append((t + timedelta(seconds=30), "Seguridad", 4732, atacante, victima, f"Se agregó {creado} al grupo Administradores"))
    t += timedelta(minutes=r.randrange(5, 20))
    eventos.append((t, "Sistema", 7045, "", victima, f"Se instaló el servicio {servicio}"))
    borrado = t + timedelta(minutes=r.randrange(30, 90))
    eventos.append((borrado, "Seguridad", 1102, "", creado, "Se borró el registro de auditoría"))
    for _ in range(6):  # la mañana siguiente
        borrado += timedelta(minutes=r.randrange(20, 60))
        i = r.randrange(len(EMPLEADOS))
        eventos.append((borrado.replace(hour=max(borrado.hour, 8)), "Seguridad", 4624, oficina[i], EMPLEADOS[i], "Inicio de sesión correcto (tipo 2)"))
    eventos.sort(key=lambda e: e[0])
    return {
        "atacante": atacante, "fallidos": fallidos, "acceso": acceso.strftime("%Y-%m-%d %H:%M:%S"),
        "victima": victima, "creado": creado, "servicio": servicio,
        "borrado": next(e[0] for e in eventos if e[2] == 1102).strftime("%Y-%m-%d %H:%M:%S"),
        "eventos": eventos,
    }


def u3_e3(usuario: str) -> Mapping[str, str]:
    inc = u3_e3_incidente(usuario)
    lineas = ["Fecha,Origen,Id,Ip,Usuario,Mensaje"]
    lineas += [f"{t:%Y-%m-%d %H:%M:%S},{o},{i},{ip},{u},\"{m}\"" for t, o, i, ip, u, m in inc["eventos"]]
    return {"registro.csv": "\n".join(lineas) + "\n", "respuestas.json": _leer("u3-e3", "respuestas.json")}


# --- U4·E1 · Elige su monitorización --------------------------------------------------------------

def u4_e1(usuario: str) -> Mapping[str, str]:
    return {"herramientas.md": _leer("u4-e1", "herramientas.md")}


# --- U4·E2 · Un sensor vigilando la web -----------------------------------------------------------

def u4_e2_ruta(usuario: str) -> str:
    """El directorio de copias olvidado en la web de este alumno."""
    return f"/copias-{huella(usuario, 'u4-e2')}/"


def u4_e2_web(usuario: str) -> Mapping[str, str]:
    ruta = u4_e2_ruta(usuario)
    return {"web/index.html": _leer("u4-e2", "web/index.html"),
            "web/admin/index.html": _leer("u4-e2", "web/admin/index.html"),
            "web/robots.txt": _leer("u4-e2", "web/robots.txt").replace("{ruta}", ruta),
            f"web{ruta}index.html": _leer("u4-e2", "web/copias/index.html").replace("{ruta}", ruta)}


def u4_e2(usuario: str) -> Mapping[str, str]:
    ficheros = {n: _leer("u4-e2", n) for n in ("docker-compose.yml", "etiquetar.py", "suricata/local.rules", ".gitignore")}
    return {**ficheros, **u4_e2_web(usuario), "salidas/.gitkeep": ""}


# --- U4·E3 · Cuatro darknets ----------------------------------------------------------------------

def u4_e3(usuario: str) -> Mapping[str, str]:
    return {"darknets.md": _leer("u4-e3", "darknets.md")}


ESCENARIOS: dict[str, Callable[[str], Mapping[str, str]]] = {
    "u1-e1": u1_e1, "u1-e2": u1_e2, "u2-e1": u2_e1, "u2-e2": u2_e2, "u3-e1": u3_e1,
    "u3-e2": u3_e2, "u3-e3": u3_e3, "u4-e1": u4_e1, "u4-e2": u4_e2, "u4-e3": u4_e3,
}


# --- Aplicación en el repositorio del alumno ------------------------------------------------------

class Error(Exception):
    pass


def _git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise Error(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def usuario_de(remoto: str) -> str:
    m = re.search(r"/entregas-([A-Za-z0-9-]+?)(?:\.git)?/?$", remoto)
    if not m:
        raise Error(f"el remoto origin ({remoto}) no es un repositorio entregas-<usuario>")
    return m.group(1).lower()


def preparar(ejercicio: str, cwd: Path) -> None:
    raiz = Path(_git("rev-parse", "--show-toplevel", cwd=cwd))
    usuario = usuario_de(_git("remote", "get-url", "origin", cwd=raiz))
    destino = raiz / RAIZ / ejercicio
    if destino.exists():
        raise Error(f"{ejercicio} ya está preparado (existe {RAIZ}/{ejercicio}/)")
    for nombre, contenido in ESCENARIOS[ejercicio](usuario).items():
        fichero = destino / nombre
        fichero.parent.mkdir(parents=True, exist_ok=True)
        fichero.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"{ejercicio} preparado para {usuario} en {RAIZ}/{ejercicio}/. Sigue el enunciado.")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in EJERCICIOS:
        print(f"uso: py preparar.py {{{','.join(EJERCICIOS)}}}", file=sys.stderr)
        return 2
    try:
        preparar(argv[0], Path.cwd())
    except Error as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
