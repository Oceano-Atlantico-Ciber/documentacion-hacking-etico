"""El laboratorio de Suricata del U4·E2, levantado con las reglas del alumno y con un recorrido fijo.

Nunca se usa el docker-compose.yml del alumno: se monta un laboratorio propio, con la web de la plantilla, y
del repositorio solo se toma suricata/local.rules. El recorrido repite los pasos del enunciado: primero
portada, robots.txt y /admin/; después, la visita al directorio de copias de su escenario
(/copias-<huella>/). La regla del alumno tiene que saltar solo con la segunda parte.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path

import preparar as p

from .base import Fallo

PROYECTO = "ra1-comprobar-suricata"
IMAGENES = ("jasonish/suricata:7.0", "nginx:1.27-alpine", "curlimages/curl:8.11.1")
COMPOSE = """name: {proyecto}
services:
  web:
    image: nginx:1.27-alpine
    volumes:
      - ./web:/usr/share/nginx/html:ro
  suricata:
    image: jasonish/suricata:7.0
    network_mode: "service:web"
    cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]
    command: -i eth0 -S /reglas/local.rules -l /var/log/suricata
    volumes:
      - ./local.rules:/reglas/local.rules:ro
      - ./salidas:/var/log/suricata
    depends_on: [web]
  curl:
    image: curlimages/curl:8.11.1
    profiles: [herramientas]
"""
PRIMERA = ("/", "/robots.txt", "/admin/")


def _docker(*args: str, cwd: Path | None = None, espera: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], cwd=cwd, capture_output=True, text=True, timeout=espera,
                          encoding="utf-8", errors="replace")


def disponible() -> bool:
    try:
        return _docker("info", espera=60).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def cerrar() -> None:
    _docker("compose", "-p", PROYECTO, "down", "-v", "--remove-orphans", espera=120)


def _alertas(eve: Path) -> list[dict]:
    if not eve.exists():
        return []
    resultado = []
    for linea in eve.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue  # la última línea puede estar a medio escribir
        if evento.get("event_type") == "alert":
            resultado.append(evento)
    return resultado


def _esperar(condicion, segundos: int) -> bool:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(1)
    return condicion()


def _visitar(carpeta: Path, rutas: tuple[str, ...]) -> None:
    for ruta in rutas:
        r = _docker("compose", "run", "--rm", "curl", "-s", "-o", "/dev/null", f"http://web{ruta}", cwd=carpeta, espera=120)
        if r.returncode:
            raise Fallo(f"el laboratorio de comprobación no responde ({r.stderr.strip()[-200:]}); avisa al docente")


def comprobar(reglas: str, usuario: str) -> list[str]:
    """Los fallos de la regla del alumno en un laboratorio nuevo; [] si salta justo con la visita a sus copias."""
    if not disponible():
        raise Fallo("Docker no responde: arranca Docker Desktop y vuelve a probar")
    ruta = p.u4_e2_ruta(usuario)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        carpeta = Path(tmp)
        for nombre, contenido in p.u4_e2_web(usuario).items():
            (carpeta / nombre).parent.mkdir(parents=True, exist_ok=True)
            (carpeta / nombre).write_text(contenido, encoding="utf-8", newline="\n")
        (carpeta / "salidas").mkdir()
        (carpeta / "salidas").chmod(0o777)  # Suricata escribe con su propio usuario dentro del contenedor
        (carpeta / "local.rules").write_text(reglas, encoding="utf-8", newline="\n")
        (carpeta / "docker-compose.yml").write_text(COMPOSE.format(proyecto=PROYECTO), encoding="utf-8")
        cerrar()
        try:
            prueba = _docker("run", "--rm", "-v", f"{carpeta}:/r:ro", IMAGENES[0], "-T", "-S", "/r/local.rules", espera=300)
            if prueba.returncode:
                errores = [l for l in (prueba.stdout + prueba.stderr).splitlines() if "rror" in l]
                return ["Suricata no acepta suricata/local.rules: " + (errores[-1].strip() if errores else "revisa la sintaxis")]
            r = _docker("compose", "up", "-d", "web", "suricata", cwd=carpeta, espera=600)
            if r.returncode:
                raise Fallo(f"no arranca el laboratorio de comprobación ({r.stderr.strip()[-200:]}); avisa al docente")
            eve = carpeta / "salidas" / "eve.json"
            con_curl = lambda: sum(a["alert"]["signature_id"] == 1000004 for a in _alertas(eve))  # noqa: E731
            # Listo cuando una petición con curl deja su alerta de la plantilla (sid 1000004): no depende del texto del registro.
            limite = time.monotonic() + 150
            while not con_curl() and time.monotonic() < limite:
                _visitar(carpeta, ("/",))
                _esperar(con_curl, 5)
            if not con_curl():
                registro = _docker("compose", "logs", "--tail", "8", "suricata", cwd=carpeta)
                ultimas = " | ".join(l.strip() for l in (registro.stdout + registro.stderr).splitlines()[-4:])
                raise Fallo(f"Suricata no anota nada en el laboratorio de comprobación ({ultimas[-300:]}); avisa al docente")
            base = con_curl()
            _visitar(carpeta, PRIMERA)
            # Las reglas de la plantilla saltan con curl: cuando están las tres, Suricata ya ha procesado esa parte.
            if not _esperar(lambda: con_curl() >= base + len(PRIMERA), 60):
                raise Fallo("Suricata no anota las visitas de la primera parte: ¿has borrado o cambiado las reglas de la plantilla?")
            propias = lambda: [a for a in _alertas(eve) if a["alert"]["signature_id"] >= 1000100]  # noqa: E731
            antes = len(propias())
            _visitar(carpeta, (ruta,))
            _esperar(lambda: len(propias()) > antes, 45)
            fallos = []
            if antes:
                fallos.append("tu regla salta también con la portada, robots.txt o /admin/: hazla más precisa")
            if len(propias()) == antes:
                fallos.append(f"tu regla no salta al visitar {ruta}")
            return fallos
        finally:
            cerrar()
