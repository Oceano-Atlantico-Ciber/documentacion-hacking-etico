"""Pruebas de caja negra del contrato de incidencias: hablan con tu API solo por HTTP.

Uso, con tu API recién arrancada (las pruebas crean y borran datos). Del E5 en adelante, las tres a la vez,
en el orden Go, Python y Node: así es exactamente lo que hace el corrector.

    py pruebas.py e3 http://localhost:8000
    py pruebas.py e4 http://localhost:8000
    py pruebas.py e5 http://localhost:8001 http://localhost:8002 http://localhost:8003
    py pruebas.py e6 http://localhost:8001 http://localhost:8002 http://localhost:8003
    py pruebas.py e7 http://localhost:8001 http://localhost:8002 http://localhost:8003
    py pruebas.py e8 http://localhost:8001 http://localhost:8002 http://localhost:8003
    py pruebas.py e2 contrato.yaml            (necesita: py -m pip install pyyaml)

Da igual en qué lenguaje esté la API: estas pruebas no ven el código, solo lo que responde.
Lee incidencias.json (y en el E8 usuarios.json) de su misma carpeta para saber qué esperar.
El corrector pasa exactamente estas pruebas, con las mismas explicaciones: si aquí sale todo ✓, allí también.
Al final, «Qué arreglar» agrupa los fallos por causa, con el arreglo, la orden para repetirlo y el paso del enunciado.
"""

from __future__ import annotations

import http.client
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

AQUI = Path(__file__).resolve().parent
PRIORIDADES = ("baja", "media", "alta", "critica")
ESTADOS = ("abierta", "en-curso", "cerrada")
FUGAS = re.compile(r"Traceback|File \"|\.py\b|\.go:\d|goroutine|node_modules|\bat .*\(|/app/|/src/|Exception|stack", re.I)
TECNOLOGIA = re.compile(r"express|uvicorn|python|starlette|fastapi|node|go\b|golang|werkzeug|gunicorn", re.I)


# --- Cliente HTTP mínimo -------------------------------------------------------------------

class Respuesta:
    def __init__(self, codigo: int, cabeceras: dict[str, str], texto: str):
        self.codigo, self.cabeceras, self.texto = codigo, cabeceras, texto

    def cab(self, nombre: str) -> str | None:
        return self.cabeceras.get(nombre.lower())

    @property
    def tipo(self) -> str:
        return (self.cab("Content-Type") or "").split(";")[0].strip().lower()

    @property
    def json(self):
        try:
            return json.loads(self.texto)
        except ValueError:
            return None


class Api:
    def __init__(self, base: str, token: str | None = None):
        u = urlsplit(base)
        equipo = u.hostname or "localhost"
        # localhost puede resolver primero a ::1 y tardar segundos en caer a IPv4: se va directo.
        self.equipo = "127.0.0.1" if equipo == "localhost" else equipo
        self.puerto, self.token = u.port or 80, token
        self.base = base.rstrip("/")

    def pedir(self, metodo: str, ruta: str, cuerpo=None, cabeceras: dict | None = None, crudo: str | None = None,
              token: str | None = "") -> Respuesta:
        global ULTIMA
        cab = dict(cabeceras or {})
        token = self.token if token == "" else token
        if token:
            cab["Authorization"] = f"Bearer {token}"
        datos = None
        if crudo is not None:
            datos = crudo.encode()
        elif cuerpo is not None:
            datos = json.dumps(cuerpo, ensure_ascii=False).encode()
        if datos is not None:
            cab.setdefault("Content-Type", "application/json")
        ULTIMA = (metodo, ruta, dict(cab), datos.decode() if datos else None)
        c = http.client.HTTPConnection(self.equipo, self.puerto, timeout=10)
        try:
            c.request(metodo, ruta, body=datos, headers=cab)
            r = c.getresponse()
            return Respuesta(r.status, {k.lower(): v for k, v in r.getheaders()}, r.read().decode("utf-8", "replace"))
        finally:
            c.close()


ULTIMA: tuple | None = None  # la última petición: de ahí sale la orden para repetir lo que falló


# --- Qué significa cada fallo y cómo se arregla ----------------------------------------------
#
# Cada prueba tiene una pista: la causa, qué cambiar y el paso del enunciado donde se explica. El corrector
# usa estas mismas pistas y la misma forma de agrupar y escribir los fallos, así que lo que lees aquí es,
# palabra por palabra, lo que sale en el check de tu repositorio y en la tabla de entregas.

WEB = "https://oceano-atlantico-ciber.github.io/documentacion-hacking-etico/00-fundamentos/03-api-rest/ejercicios/"


class Pista:
    def __init__(self, id: str, patron: str, causa: str, arreglo: str, paso: str, orden: bool = True):
        self.id, self.patron, self.causa, self.arreglo, self.paso, self.orden = id, re.compile(patron), causa, arreglo, paso, orden

    @property
    def enlace(self) -> str:
        pagina, _, paso = self.paso.partition("#")
        return f"{WEB}{pagina}.html" + (f"#paso-{paso}" if paso else "")


PROBLEM = ("Responde con Content-Type application/problem+json y un cuerpo con type, title, status (el mismo número "
           "que el código) y detail, sin trazas, rutas ni nombres de fichero.")
PISTAS = [
    # E5 · las tres iguales
    Pista("e5-iguales", r": misma respuesta en las tres$", "Las tres APIs no responden igual",
          "Lanza esa petición a las tres y compara código, Content-Type, Location, Allow, ETag y cuerpo; corrige la que se "
          "aparta y apunta la diferencia y su arreglo en diferencias.md.", "e5#4", False),
    Pista("e5-diferencias", r"^diferencias\.md", "Falta explicar las diferencias",
          "En diferencias.md, un apartado o elemento de lista por cada diferencia encontrada, con su arreglo (al menos tres).",
          "e5#5", False),
    # E2 · contrato
    Pista("e2-yaml", r"^contrato\.yaml es YAML válido", "contrato.yaml no se puede leer",
          "Ábrelo en el editor y corrige la línea que da el error: casi siempre es una sangría o unos dos puntos.", "e2#3", False),
    Pista("e2-openapi", r"^Es un OpenAPI 3", "No es un contrato OpenAPI 3", "La primera línea tiene que ser openapi: 3.0.3 (o 3.1.0).", "e2#3", False),
    Pista("e2-rutas", r"^(Todas las rutas empiezan|Ninguna ruta lleva un verbo|Las colecciones van en plural|Hay una ruta para leer)",
          "Las rutas no siguen las reglas de REST",
          "Rutas con /api/v1/, nombres en plural y sin verbos: la acción la dice el método (GET /api/v1/incidencias, no /listarIncidencias).",
          "e2#2", False),
    Pista("e2-metodos", r"^(Usa los cinco métodos|Cada POST que crea|Cada DELETE responde|Ningún GET lleva cuerpo)",
          "Faltan operaciones o códigos en el contrato",
          "Declara GET, POST, PUT, PATCH y DELETE; POST responde 201, DELETE 204 y ningún GET lleva requestBody.", "e2#3", False),
    Pista("e2-errores", r"^(Cada operación declara sus errores|Toda ruta con \{id\} declara el 404)", "El contrato no declara los errores",
          "Cada operación declara al menos un 4xx, y toda ruta con {id} declara el 404.", "e2#3", False),
    # E3 · lectura
    Pista("e3-salud", r"^GET /api/v1/salud", "Falta la ruta de salud",
          'Añade GET /api/v1/salud que responda 200 con {"estado": "ok"}.', "e3#2"),
    Pista("e3-lista", r"^La lista (es JSON|tiene la forma|trae todas)", "La lista de incidencias no es la que pide el contrato",
          'GET /api/v1/incidencias responde 200, Content-Type application/json y {"datos": [...], "siguiente": null} con todas '
          "las de incidencias.json, ordenadas por id y sin cambiarlas. Arranca la API de nuevo antes de pasar las pruebas: "
          "las de escritura crean datos.", "e3#2"),
    Pista("e3-una", r"^GET /api/v1/incidencias/\{id\} devuelve", "Leer una incidencia no la devuelve tal cual",
          "GET /api/v1/incidencias/{id} devuelve el objeto de incidencias.json sin añadir, quitar ni renombrar campos.", "e3#2"),
    Pista("e3-comentarios", r"^GET \.\.\./comentarios devuelve", "Los comentarios no salen como pide el contrato",
          'GET /api/v1/incidencias/{id}/comentarios devuelve {"datos": [sus comentarios], "siguiente": null}.', "e3#2"),
    Pista("e3-404", r"(no existe da 404|no existe: 404|de una incidencia que no existe dan 404|Lo borrado ya no existe|Borrar otra vez da 404)",
          "Un recurso que no existe no da 404",
          "Si el id no existe (o ya se borró), responde 404 con un cuerpo JSON; nunca 200 vacío ni 500.", "e3#2"),
    # E4 · escritura
    Pista("e4-crear", r"^(POST crea y responde 201|La nueva nace abierta|El id nuevo no reutiliza|Un id borrado no se reutiliza)",
          "Crear una incidencia no responde como pide el contrato",
          "POST /api/v1/incidencias responde 201 con la incidencia completa: estado abierta, tecnico null y un id mayor "
          "que todos los que ha habido, aunque se hayan borrado.", "e4#2"),
    Pista("e4-location", r"^(Location apunta|Lo que dice Location|Location del comentario|El comentario se puede leer)",
          "Falta Location al crear",
          "Al responder 201, añade la cabecera Location con la ruta de lo creado (/api/v1/incidencias/{id} o "
          "/api/v1/incidencias/{id}/comentarios/{id}) y comprueba que esa ruta se puede leer con GET.", "e4#2"),
    Pista("e4-validar", r"^(POST sin un campo obligatorio|PUT sin todos los campos)", "Acepta datos incompletos",
          "Si falta un campo obligatorio, responde 400 o 422 y no guardes nada.", "e4#2"),
    Pista("e4-put", r"^PUT (sustituye|es idempotente)", "PUT no sustituye la incidencia entera",
          "PUT recibe la incidencia completa y la guarda tal cual, conservando el id; repetirlo deja lo mismo.", "e4#2"),
    Pista("e4-patch", r"^PATCH cambia solo lo enviado", "PATCH cambia más de lo enviado",
          "PATCH cambia solo los campos que llegan en el cuerpo y deja el resto como estaba.", "e4#2"),
    Pista("e4-comentar", r"^POST de un comentario", "Comentar no responde como pide el contrato",
          "POST /api/v1/incidencias/{id}/comentarios responde 201 con el comentario, incluidos incidencia y texto.", "e4#2"),
    Pista("e4-borrar", r"^DELETE responde 204", "Borrar no responde 204",
          "DELETE responde 204 sin cuerpo: ni JSON, ni un mensaje.", "e4#2"),
    Pista("e4-405", r"da 405 con Allow", "Un método que la ruta no admite no da 405",
          "Responde 405 con la cabecera Allow y los métodos que esa ruta sí admite, separados por comas.", "e4#2"),
    # E6 · errores
    Pista("e6-problem", r"→ \d{3} en problem\+json$", "Un error no responde en problem+json",
          "Valida el cuerpo antes de usarlo: JSON roto da 400; tipo, valor o campo de más da 422; ruta o id que no existe "
          "da 404; método no admitido da 405. " + PROBLEM, "e6#3"),
    Pista("e6-caida", r"^Tras los casos, la API sigue respondiendo", "Algún caso de error tumba la API",
          "Captura los errores de JSON y de validación y responde el error; el servidor no debe caerse ni reiniciarse.", "e6#3"),
    # E7 · paginación, filtros, caché y concurrencia
    Pista("e7-paginar", r"^(Sin limit, la página trae 20|Recorrer con limit=50)", "La lista no pagina",
          'Sin limit, devuelve 20; con limit=N, N (de 1 a 100). «siguiente» es el id de la última fila, como texto, '
          'o null en la última página, y cursor=ese id sigue desde ahí.', "e7#2"),
    Pista("e7-consulta", r"^\?(limit|cursor|estado|prioridad)=.* da 400", "La lista acepta parámetros inválidos",
          "limit fuera de 1-100 o no numérico, cursor no numérico, o un estado o prioridad que no existe: 400 en "
          "problem+json. " + PROBLEM, "e7#2"),
    Pista("e7-filtro", r"^\?estado=abierta&prioridad=alta", "Los filtros no filtran",
          "estado= y prioridad= se pueden combinar y la lista trae solo las que cumplen los dos, paginadas igual.", "e7#2"),
    Pista("e7-etag", r"^(POST devuelve ETag|GET de una incidencia devuelve ETag|Con If-None-Match)", "Falta el ETag o el 304",
          'Cada incidencia lleva una versión; POST, GET, PUT y PATCH devuelven ETag con ella entre comillas ("1"). '
          "Si If-None-Match coincide con el ETag actual, responde 304 sin cuerpo.", "e7#3"),
    Pista("e7-if-match", r"^(PATCH con If-Match|PUT con If-Match antiguo|Tras los 412)", "If-Match no protege de pisar cambios",
          "Si llega If-Match y no coincide con el ETag actual, responde 412 en problem+json y no cambies nada; si "
          "coincide, cambia, sube la versión y devuelve el ETag nuevo.", "e7#3"),
    Pista("e7-escenario", r"^escenario\.md", "Falta el escenario de concurrencia",
          "En escenario.md, las dos peticiones con If-Match, el 412 que da la segunda y por qué (más de 40 palabras).",
          "e7#4", False),
    # E8 · seguridad
    Pista("e8-token", r"^(Sin token: 401|Con un token que no existe|Una cabecera X-User|/api/v1/salud sigue sin pedir token)",
          "La API no exige un token válido",
          "Todo salvo GET /api/v1/salud y POST /api/v1/sesiones exige Authorization: Bearer <token> de usuarios.json; "
          "sin él o con uno que no existe, 401 con WWW-Authenticate: Bearer. Ninguna otra cabecera sustituye al token.",
          "e8#2"),
    Pista("e8-sesiones", r"^POST /api/v1/sesiones", "Iniciar sesión no devuelve el token",
          "POST /api/v1/sesiones con usuario y clave correctos responde 201 con el token de ese usuario.", "e8#2"),
    Pista("e8-intentos", r"^(Cinco claves malas|La sexta: 429|Durante el bloqueo)", "No hay límite de intentos",
          "Tras cinco claves malas seguidas de un usuario, responde 429 con Retry-After en segundos, también con la clave "
          "buena, hasta que pase ese tiempo.", "e8#4"),
    Pista("e8-bola", r"^(Un técnico solo ve sus incidencias|Una incidencia de otro|Cambiar una de otro|Los comentarios de una de otro)",
          "Un técnico ve o toca incidencias de otro (BOLA)",
          "Con el token de un técnico, filtra la lista a las suyas y responde 404 a las de otro, también al cambiarlas o al "
          "leer sus comentarios. El administrador lo ve todo.", "e8#3"),
    Pista("e8-propias", r"^(Lo que crea un técnico|Un técnico no crea incidencias para otro|Un técnico no reasigna)",
          "Un técnico puede asignar incidencias a otro",
          "Lo que crea un técnico queda a su nombre; si intenta crear o pasar una incidencia a otro técnico, 403.", "e8#3"),
    Pista("e8-bfla", r"^(Un técnico no borra|Un administrador sí borra)", "Borrar no comprueba el rol (BFLA)",
          "DELETE solo lo puede hacer el administrador (204); un técnico recibe 403 aunque la incidencia sea suya.", "e8#3"),
    Pista("e8-masiva", r"^(PATCH /api/v1/usuarios/yo con rol|Ni mezclado con nombre|Y el rol sigue|Cambiar solo el nombre)",
          "Un usuario puede cambiarse el rol (asignación masiva)",
          "PATCH /api/v1/usuarios/yo admite solo nombre; si llega rol (aunque sea junto a nombre), 422 y no cambies nada.",
          "e8#3"),
    Pista("e8-huella", r"^Ninguna respuesta dice el lenguaje", "Las respuestas delatan la tecnología",
          "Quita X-Powered-By y las cabeceras Server que nombran el lenguaje o el framework (en Express, "
          "app.disable('x-powered-by'); en uvicorn, --no-server-header).", "e8#4"),
    Pista("e8-controles", r"^controles\.md", "Faltan controles por documentar",
          "En controles.md, cada control con su CWE: BOLA CWE-639, asignación masiva CWE-915, permisos por rol (BFLA) "
          "CWE-285 y límite de intentos CWE-307.", "e8#5", False),
    # Lo que comprueba el corrector al construir y arrancar (también lo hace levantar las APIs a mano)
    Pista("lenguaje", r"(lenguaje\.txt|tiene una API en|no tiene go\.mod|van las tres)", "La API no está donde se espera",
          "Cada API en su carpeta (go/, python/ o node/) con go.mod, requirements.txt o package.json, y lenguaje.txt con "
          "el lenguaje elegido en E3 y E4.", "e3#1", False),
    Pista("docker", r"(Dockerfile no construye|se ejecuta como root|no responde en el puerto 8000|no arranca|no vuelve a arrancar)",
          "La imagen no se construye o no arranca",
          "Construye y arranca tu imagen como en el enunciado (docker build y docker run -p 8000:8000) y mira el error; "
          "la imagen termina con USER y un usuario sin privilegios y la API escucha en 0.0.0.0:8000.", "e3#4", False),
    Pista("parada", r"^la API dejó de responder", "La API se cayó durante las pruebas",
          "Mira el registro del contenedor (docker logs) para ver qué petición la tumba y captura ese error.", "e6#3", False),
    Pista("faltan", r"^falta ", "Faltan ficheros de la entrega",
          "Sube todos los ficheros que pide el apartado «Qué entregas» del enunciado, en su carpeta.", "", False),
    Pista("enlace", r"fichero o enlace que sale de su carpeta", "El repositorio tiene un enlace que sale de su carpeta",
          "Quita ese enlace simbólico del repositorio: el corrector solo lee ficheros normales.", "", False),
    Pista("etiqueta", r"^la etiqueta no es anotada", "La etiqueta no es anotada",
          "Bórrala (git tag -d y git push origin --delete) y créala otra vez con git tag -a y -m.", "", False),
    Pista("corrector", r"^(error del corrector|pendiente de corregir)", "Error del corrector",
          "No es culpa tuya: avisa al docente.", "", False),
    # E1 · HTTP a mano (lo comprueba el corrector con el laboratorio)
    Pista("e1-get", r"^peticion-get\.txt", "La petición GET no lee tu incidencia",
          "Primera línea GET /api/v1/incidencias/<tu número> HTTP/1.1, cabecera Host y una línea en blanco al final.", "e1#2", False),
    Pista("e1-post", r"^peticion-post\.txt", "La petición POST no crea la incidencia",
          "Método y ruta de crear, Content-Type: application/json y Content-Length con el tamaño exacto del cuerpo (enviar.py te avisa si no cuadra).", "e1#3", False),
    Pista("e1-salidas", r"^(respuesta|curl)-(get|post)\.txt", "Falta una salida o no es la de la petición",
          "Guarda la salida de enviar.py y de curl.exe -v de cada petición, sin editarla.", "e1#4", False),
    Pista("e1-comparacion", r"^comparacion\.md", "La comparación está incompleta",
          "comparacion.md con los tres apartados con su título (##) y lo que dice la cabecera Server.", "e1#5", False),
]
SIN_PISTA = Pista("otra", r"", "Prueba sin pista", "Avisa al docente: esta prueba no tiene explicación todavía.", "", False)
ESTRICTO = False  # las pruebas del corrector lo activan: una prueba sin pista es un error del corrector, no del alumno


def pista(nombre: str) -> Pista:
    for p in PISTAS:
        if p.patron.search(nombre):
            return p
    if ESTRICTO:
        raise LookupError(f"prueba sin pista: {nombre}")
    return SIN_PISTA


def _ps(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _sh(texto: str) -> str:
    return "'" + texto.replace("'", "'\\''") + "'"


def orden(base: str, peticion: tuple | None) -> dict | None:
    """La misma petición escrita para PowerShell (curl.exe) y para macOS/Linux (curl), lista para copiar.

    En PowerShell 5.1, las comillas dobles de un argumento no llegan a curl.exe: el cuerpo y las cabeceras que las
    llevan van a un fichero, como en los enunciados. El token nunca se escribe: se dice de quién es."""
    if not peticion:
        return None
    metodo, ruta, cab, cuerpo = peticion
    url = base.rstrip("/") + ruta
    ps_antes, ps, sh = [], ["curl.exe", "-i"], ["curl", "-i"]
    if metodo != "GET":
        ps += ["-X", metodo]
        sh += ["-X", metodo]
    ps.append(f'"{url}"')
    sh.append(_sh(url))
    for k, v in cab.items():
        if k == "Authorization":
            v = "Bearer " + _de_quien(v.removeprefix("Bearer "))
        linea = f"{k}: {v}"
        sh += ["-H", _sh(linea)]
        if '"' in linea:
            nombre = f"cabecera-{k.lower()}.txt"
            ps_antes.append(f"New-Item {nombre} -Force -Value {_ps(linea)} | Out-Null")
            ps += ["-H", f'"@{nombre}"']
        else:
            ps += ["-H", f'"{linea}"']
    if cuerpo is not None:
        try:
            datos = json.loads(cuerpo)
            if isinstance(datos, dict) and "clave" in datos:
                datos["clave"] = f"<clave de {datos.get('usuario', 'ese usuario')} en usuarios.json>"
                cuerpo = json.dumps(datos, ensure_ascii=False)
        except ValueError:
            pass
        ps_antes.append(f"New-Item cuerpo.json -Force -Value {_ps(cuerpo)} | Out-Null")
        ps += ["--data-binary", '"@cuerpo.json"']
        sh += ["--data-binary", _sh(cuerpo)]
    return {"ps": "\n".join(ps_antes + [" ".join(ps)]), "unix": " ".join(sh)}


def _de_quien(token: str) -> str:
    try:
        for u in _datos("usuarios.json")["usuarios"]:
            if u["token"] == token:
                return f"<token de {u['usuario']} en usuarios.json>"
    except (SystemExit, OSError, ValueError, KeyError):
        pass
    return "<token>"


# --- Registro de resultados ----------------------------------------------------------------

class Resultado:
    """Cuenta las pruebas, pinta ✓ y ✗ al momento y guarda cada ✗ con su pista y la petición que la provocó."""

    def __init__(self, base: str = "http://localhost:8000"):
        self.bien = self.mal = 0
        self.base = base
        self.fallos: list[dict] = []

    def comprobar(self, nombre: str, condicion: bool, detalle: str = "") -> bool:
        p = pista(nombre)
        if condicion:
            self.bien += 1
            print(f"  ✓ {nombre}")
        else:
            self.mal += 1
            print(f"  ✗ {nombre}" + (f"  ({detalle})" if detalle else ""))
            self.fallos.append({"pista": p.id, "prueba": nombre, "obtenido": detalle,
                                "orden": orden(self.base, ULTIMA) if p.orden else None})
        return condicion


RECORTE = 160  # lo obtenido se recorta: basta para ver el fallo, no para publicar lo que devuelve tu API entera


def agrupar(por_api: dict[str, list[dict]]) -> list[dict]:
    """Junta los fallos por causa: una entrada por pista, con todas las pruebas que fallan por ella y en qué APIs.

    por_api es {"go": [...], "python": [...], "node": [...]}, o {"": [...]} con una sola API. Así una API que no
    pagina da una sola entrada, «La lista no pagina», en vez de nueve pruebas repetidas en tres lenguajes."""
    grupos: dict[str, dict] = {}
    for nombre_api, fallos in por_api.items():
        for f in fallos:
            p = next((x for x in PISTAS if x.id == f["pista"]), SIN_PISTA)
            g = grupos.setdefault(p.id, {"pista": p.id, "causa": p.causa, "arreglo": p.arreglo, "enlace": p.enlace if p.paso else "",
                                         "pruebas": [], "apis": [], "obtenido": "", "orden": None})
            if f["prueba"] not in g["pruebas"]:
                g["pruebas"].append(f["prueba"])
            if nombre_api and nombre_api not in g["apis"]:
                g["apis"].append(nombre_api)
            # Lo obtenido y la orden salen de la misma prueba: la primera que dejó algo que enseñar.
            if not g["obtenido"] and f.get("obtenido"):
                g["obtenido"] = f"{f['prueba']}: {f['obtenido']}"[:RECORTE]
                g["orden"] = f.get("orden") or g["orden"]
            elif not g["obtenido"] and not g["orden"]:
                g["orden"] = f.get("orden")
    cuantas = len([n for n in por_api if n])
    for g in grupos.values():
        g["resumen"], g["texto"] = resumen(g, cuantas), texto(g, cuantas)
    return list(grupos.values())


def donde(g: dict, cuantas: int) -> str:
    if not g["apis"]:
        return ""
    return "en las tres" if cuantas == 3 and len(g["apis"]) == 3 else "en " + ", ".join(g["apis"])


def resumen(g: dict, cuantas: int = 1) -> str:
    """La causa, dónde y cuántas pruebas: «La lista no pagina en las tres (9 pruebas)»."""
    lugar = donde(g, cuantas)
    n = len(g["pruebas"])
    return f"{g['causa']}{' ' + lugar if lugar else ''}{f' ({n} pruebas)' if n > 1 else ''}"


def texto(g: dict, cuantas: int = 1) -> str:
    """Una línea con el resumen y el arreglo: la que guarda el registro."""
    return f"{resumen(g, cuantas)}. {g['arreglo']}"


def informe(grupos: list[dict], cuantas: int = 1) -> str:
    """Lo mismo que el check y la tabla de entregas, para la terminal."""
    lineas = []
    for g in grupos:
        lineas.append(f"✗ {g.get('resumen') or resumen(g, cuantas)}")
        lineas.append("  Falla:     " + "; ".join(g["pruebas"][:4]) + (f"; y {len(g['pruebas']) - 4} más" if len(g["pruebas"]) > 4 else ""))
        if g["obtenido"]:
            lineas.append(f"  Obtenido:  {g['obtenido']}")
        lineas.append(f"  Arreglo:   {g['arreglo']}")
        if g["orden"]:
            ps = g["orden"]["ps"].replace("\n", "\n             ")
            lineas.append(f"  Pruébalo (PowerShell):\n             {ps}")
            lineas.append(f"  Pruébalo (macOS/Linux):\n             {g['orden']['unix']}")
        if g["enlace"]:
            lineas.append(f"  Enunciado: {g['enlace']}")
        lineas.append("")
    return "\n".join(lineas)


def _datos(fichero: str = "incidencias.json") -> dict:
    ruta = AQUI / fichero
    if not ruta.exists():
        raise SystemExit(f"No encuentro {ruta}: pruebas.py tiene que estar junto a tu API")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _allow(r: Respuesta) -> set[str]:
    return {m.strip().upper() for m in (r.cab("Allow") or "").split(",") if m.strip()} - {"HEAD", "OPTIONS"}


def _es_json(r: Respuesta) -> bool:
    return r.tipo in ("application/json", "application/problem+json")


def _todas(api: Api, consulta: str = "", limite: int | None = None) -> tuple[list, int, str]:
    """Recorre la lista siguiendo «siguiente». Devuelve los elementos, las páginas y un error."""
    filas, paginas, cursor = [], 0, None
    while True:
        partes = [p for p in (consulta, f"limit={limite}" if limite else "", f"cursor={cursor}" if cursor else "") if p]
        r = api.pedir("GET", "/api/v1/incidencias" + ("?" + "&".join(partes) if partes else ""))
        paginas += 1
        if r.codigo != 200 or not isinstance(r.json, dict) or "datos" not in r.json or "siguiente" not in r.json:
            return filas, paginas, f"página {paginas}: {r.codigo} {r.texto[:120]}"
        filas += r.json["datos"]
        cursor = r.json["siguiente"]
        if cursor is None:
            return filas, paginas, ""
        if paginas > 200:
            return filas, paginas, "más de 200 páginas: ¿«siguiente» no avanza?"


# --- Suites --------------------------------------------------------------------------------

def suite_e3(api: Api, res: Resultado) -> None:
    print("E3 · Lectura")
    datos = _datos()
    r = api.pedir("GET", "/api/v1/salud")
    res.comprobar("GET /api/v1/salud responde 200 {\"estado\": \"ok\"}", r.codigo == 200 and r.json == {"estado": "ok"}, f"{r.codigo} {r.texto[:80]}")
    r = api.pedir("GET", "/api/v1/incidencias")
    res.comprobar("La lista es JSON con Content-Type application/json", r.codigo == 200 and r.tipo == "application/json", f"{r.codigo} {r.cab('Content-Type')}")
    filas, _, error = _todas(api)
    esperado = sorted(datos["incidencias"], key=lambda i: i["id"])
    res.comprobar("La lista tiene la forma {\"datos\": [...], \"siguiente\": ...}", not error, error)
    res.comprobar("La lista trae todas las incidencias, ordenadas por id y sin cambios", filas == esperado,
                  "¿has reiniciado la API? las pruebas de E4 en adelante crean datos" if filas else "lista vacía")
    malas = []
    for inc in esperado[:15]:
        r = api.pedir("GET", f"/api/v1/incidencias/{inc['id']}")
        if r.codigo != 200 or r.json != inc or r.tipo != "application/json":
            malas.append(f"{inc['id']}: {r.codigo}")
    res.comprobar("GET /api/v1/incidencias/{id} devuelve cada incidencia tal cual", not malas, ", ".join(malas[:5]))
    r = api.pedir("GET", "/api/v1/incidencias/999999")
    res.comprobar("Una incidencia que no existe da 404 en JSON", r.codigo == 404 and _es_json(r), f"{r.codigo} {r.cab('Content-Type')}")
    malas = []
    for inc in esperado[:15]:
        r = api.pedir("GET", f"/api/v1/incidencias/{inc['id']}/comentarios")
        suyos = [c for c in datos["comentarios"] if c["incidencia"] == inc["id"]]
        if r.codigo != 200 or r.json != {"datos": suyos, "siguiente": None}:
            malas.append(f"{inc['id']}: {r.codigo}")
    res.comprobar("GET .../comentarios devuelve {\"datos\": [sus comentarios], \"siguiente\": null}", not malas, ", ".join(malas[:5]))
    r = api.pedir("GET", "/api/v1/incidencias/999999/comentarios")
    res.comprobar("Los comentarios de una incidencia que no existe dan 404", r.codigo == 404, str(r.codigo))


def suite_e4(api: Api, res: Resultado) -> None:
    print("E4 · Escritura")
    maximo = max(i["id"] for i in _datos()["incidencias"])
    r = api.pedir("POST", "/api/v1/incidencias", {"titulo": "Prueba: monitor roto", "prioridad": "alta"})
    nueva = r.json if isinstance(r.json, dict) else {}
    res.comprobar("POST crea y responde 201", r.codigo == 201, f"{r.codigo} {r.texto[:100]}")
    res.comprobar("La nueva nace abierta y sin técnico", nueva.get("estado") == "abierta" and "tecnico" in nueva and nueva["tecnico"] is None, str(nueva))
    res.comprobar("El id nuevo no reutiliza ninguno existente", isinstance(nueva.get("id"), int) and nueva["id"] > maximo, str(nueva.get("id")))
    loc = r.cab("Location") or ""
    res.comprobar("Location apunta a la incidencia creada", loc == f"/api/v1/incidencias/{nueva.get('id')}" or loc.endswith(f"/api/v1/incidencias/{nueva.get('id')}"), loc)
    n = nueva.get("id", 0)
    r = api.pedir("GET", f"/api/v1/incidencias/{n}")
    res.comprobar("Lo que dice Location se puede leer con GET", r.codigo == 200 and r.json == nueva, f"{r.codigo}")
    r = api.pedir("POST", "/api/v1/incidencias", {"titulo": "Sin prioridad"})
    res.comprobar("POST sin un campo obligatorio da 400 o 422", r.codigo in (400, 422), str(r.codigo))
    completa = {"titulo": "Prueba: monitor sustituido", "prioridad": "baja", "estado": "en-curso", "tecnico": "sara"}
    r1 = api.pedir("PUT", f"/api/v1/incidencias/{n}", completa)
    r2 = api.pedir("PUT", f"/api/v1/incidencias/{n}", completa)
    res.comprobar("PUT sustituye entera la incidencia y responde 200", r1.codigo == 200 and r1.json == {"id": n, **completa}, f"{r1.codigo} {r1.texto[:100]}")
    res.comprobar("PUT es idempotente: repetirlo deja lo mismo", r2.codigo == 200 and r2.json == r1.json, f"{r2.codigo}")
    r = api.pedir("PUT", f"/api/v1/incidencias/{n}", {"titulo": "Solo el título"})
    res.comprobar("PUT sin todos los campos da 400 o 422", r.codigo in (400, 422), str(r.codigo))
    r = api.pedir("PATCH", f"/api/v1/incidencias/{n}", {"prioridad": "critica"})
    res.comprobar("PATCH cambia solo lo enviado", r.codigo == 200 and r.json == {"id": n, **completa, "prioridad": "critica"}, f"{r.codigo} {r.texto[:100]}")
    r = api.pedir("PATCH", "/api/v1/incidencias/999999", {"prioridad": "baja"})
    res.comprobar("PATCH de una incidencia que no existe da 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("POST", f"/api/v1/incidencias/{n}/comentarios", {"texto": "Prueba: revisado"})
    com = r.json if isinstance(r.json, dict) else {}
    res.comprobar("POST de un comentario responde 201 con incidencia y texto", r.codigo == 201 and com.get("incidencia") == n and com.get("texto") == "Prueba: revisado", f"{r.codigo} {r.texto[:100]}")
    loc = r.cab("Location") or ""
    res.comprobar("Location del comentario apunta a él", loc.endswith(f"/api/v1/incidencias/{n}/comentarios/{com.get('id')}"), loc)
    r = api.pedir("GET", f"/api/v1/incidencias/{n}/comentarios/{com.get('id')}")
    res.comprobar("El comentario se puede leer en su ruta", r.codigo == 200 and r.json == com, str(r.codigo))
    r = api.pedir("DELETE", f"/api/v1/incidencias/{n}")
    res.comprobar("DELETE responde 204 sin cuerpo", r.codigo == 204 and r.texto == "", f"{r.codigo} {r.texto[:60]!r}")
    r = api.pedir("GET", f"/api/v1/incidencias/{n}")
    res.comprobar("Lo borrado ya no existe: 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("DELETE", f"/api/v1/incidencias/{n}")
    res.comprobar("Borrar otra vez da 404 y el servidor queda igual", r.codigo == 404, str(r.codigo))
    r = api.pedir("POST", "/api/v1/incidencias", {"titulo": "Prueba: otra", "prioridad": "baja"})
    res.comprobar("Un id borrado no se reutiliza", isinstance(r.json, dict) and r.json.get("id", 0) > n, str(r.json))
    if isinstance(r.json, dict) and "id" in r.json:
        api.pedir("DELETE", f"/api/v1/incidencias/{r.json['id']}")
    r = api.pedir("DELETE", "/api/v1/incidencias")
    res.comprobar("DELETE sobre la colección da 405 con Allow: GET, POST", r.codigo == 405 and _allow(r) == {"GET", "POST"}, f"{r.codigo} Allow: {r.cab('Allow')}")
    r = api.pedir("POST", "/api/v1/incidencias/1")
    res.comprobar("POST sobre una incidencia da 405 con Allow: GET, PUT, PATCH, DELETE", r.codigo == 405 and _allow(r) == {"GET", "PUT", "PATCH", "DELETE"}, f"{r.codigo} Allow: {r.cab('Allow')}")
    r = api.pedir("POST", "/api/v1/incidencias/999999/comentarios", {"texto": "Prueba"})
    res.comprobar("comentar una incidencia que no existe da 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("PUT", "/api/v1/incidencias/999999", {"titulo": "x", "prioridad": "baja", "estado": "abierta", "tecnico": None})
    res.comprobar("PUT de una incidencia que no existe da 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("GET", "/api/v1/incidencias/1/comentarios/999999")
    res.comprobar("un comentario que no existe da 404", r.codigo == 404, str(r.codigo))


def _secuencia(api: Api) -> list[tuple]:
    """La misma serie de peticiones para comparar las tres APIs del E5."""
    pasos = [
        ("GET", "/api/v1/salud", None), ("GET", "/api/v1/incidencias", None), ("GET", "/api/v1/incidencias/1", None),
        ("GET", "/api/v1/incidencias/1/comentarios", None), ("GET", "/api/v1/incidencias/999999", None),
        ("POST", "/api/v1/incidencias", {"titulo": "Comparar", "prioridad": "media"}),
        ("PATCH", "/api/v1/incidencias/1", {"estado": "cerrada"}),
        ("PUT", "/api/v1/incidencias/2", {"titulo": "Igual en las tres", "prioridad": "alta", "estado": "abierta", "tecnico": None}),
        ("POST", "/api/v1/incidencias/2/comentarios", {"texto": "Hola"}),
        ("DELETE", "/api/v1/incidencias/3", None), ("GET", "/api/v1/incidencias/3", None),
        ("DELETE", "/api/v1/incidencias", None), ("POST", "/api/v1/incidencias/1", None),
        ("GET", "/api/v1/incidencias", None),
    ]
    salida = []
    for metodo, ruta, cuerpo in pasos:
        r = api.pedir(metodo, ruta, cuerpo)
        cuerpo_r = r.json if 200 <= r.codigo < 300 else None
        salida.append((f"{metodo} {ruta}", r.codigo, r.tipo if r.texto else "", r.cab("Location"),
                       sorted(_allow(r)) or None, r.cab("ETag"), cuerpo_r))
    return salida


def suite_e5(apis: list[Api], res: Resultado) -> None:
    print("E5 · Las tres responden igual")
    resultados = [_secuencia(a) for a in apis]
    nombres = ("código", "Content-Type", "Location", "Allow", "ETag", "cuerpo")
    for i, paso in enumerate(resultados[0]):
        distintos = [nombres[k - 1] for k in range(1, 7) if len({json.dumps(r[i][k], sort_keys=True) for r in resultados}) > 1]
        res.comprobar(f"{paso[0]}: misma respuesta en las tres", not distintos,
                      "distinto: " + ", ".join(distintos) + " · " + " | ".join(str(r[i][1]) for r in resultados))


def suite_e6(api: Api, res: Resultado) -> None:
    print("E6 · Errores")
    casos = [[p.strip() for p in linea.split("|")] for linea in CASOS]
    for peticion, cuerpo, esperado in casos:
        metodo, ruta = peticion.split(" ", 1)
        cuerpo = cuerpo.replace("<121 caracteres>", "x" * 121)
        r = api.pedir(metodo, ruta, crudo=cuerpo if cuerpo else None)
        p = r.json if isinstance(r.json, dict) else {}
        forma = r.tipo == "application/problem+json" and isinstance(p.get("type"), str) and isinstance(p.get("title"), str) \
            and p.get("status") == r.codigo and isinstance(p.get("detail"), str)
        fuga = FUGAS.search(r.texto)
        res.comprobar(f"{peticion} {cuerpo[:40]} → {esperado} en problem+json", r.codigo == int(esperado) and forma and not fuga,
                      f"{r.codigo} {r.tipo} {r.texto[:90]}" + (f" · filtra «{fuga.group(0)}»" if fuga else ""))
    for metodo, ruta, cuerpo, codigo in (
        ("PATCH", "/api/v1/incidencias/1", '{"tecnico": 5}', 422),
        ("POST", "/api/v1/incidencias/1/comentarios", '{"texto": "Hola", "autor": "yo"}', 422),
        ("POST", "/api/v1/incidencias/1/comentarios", '{"texto": "Hola"', 400),
        ("PUT", "/api/v1/incidencias/1", '{"titulo": "x", "prioridad": "baja", "estado": "abierta", "tecnico": null, "id": 9}', 422),
    ):
        r = api.pedir(metodo, ruta, crudo=cuerpo)
        forma = r.tipo == "application/problem+json" and isinstance(r.json, dict) and r.json.get("status") == r.codigo
        res.comprobar(f"{metodo} {ruta} {cuerpo} → {codigo} en problem+json", r.codigo == codigo and forma, f"{r.codigo} {r.tipo}")
    r = api.pedir("GET", "/api/v1/incidencias/1")
    res.comprobar("Tras los casos, la API sigue respondiendo", r.codigo == 200, str(r.codigo))


# Los mismos casos que casos.txt, que se entrega con el E6.
CASOS = [
    'POST /api/v1/incidencias | {"titulo": "Sin cerrar" | 400',
    "POST /api/v1/incidencias | ['titulo', 'baja'] | 400",
    'POST /api/v1/incidencias | [1, 2, 3] | 422',
    'POST /api/v1/incidencias | {"titulo": "Falta la prioridad"} | 422',
    'POST /api/v1/incidencias | {"titulo": "", "prioridad": "baja"} | 422',
    'POST /api/v1/incidencias | {"titulo": "Prioridad inventada", "prioridad": "urgentisima"} | 422',
    'POST /api/v1/incidencias | {"titulo": 42, "prioridad": "alta"} | 422',
    'POST /api/v1/incidencias | {"titulo": "Con un campo de más", "prioridad": "baja", "rol": "admin"} | 422',
    'POST /api/v1/incidencias | {"titulo": "<121 caracteres>", "prioridad": "baja"} | 422',
    'PATCH /api/v1/incidencias/1 | {"estado": "olvidada"} | 422',
    'PATCH /api/v1/incidencias/1 | {"id": 999} | 422',
    'PUT /api/v1/incidencias/1 | {"titulo": "Solo el título"} | 422',
    'POST /api/v1/incidencias/1/comentarios | {"texto": ""} | 422',
    'GET /api/v1/incidencias/abc | | 404',
    'GET /api/v1/no-existe | | 404',
    'DELETE /api/v1/incidencias | | 405',
]


def suite_e7(api: Api, res: Resultado) -> None:
    print("E7 · Paginación, filtros, caché y concurrencia")
    datos = sorted(_datos()["incidencias"], key=lambda i: i["id"])
    r = api.pedir("GET", "/api/v1/incidencias")
    pagina = r.json if isinstance(r.json, dict) else {}
    res.comprobar("Sin limit, la página trae 20 y «siguiente» es el id de la última", len(pagina.get("datos", [])) == 20 and pagina.get("siguiente") == str(datos[19]["id"]),
                  f"{len(pagina.get('datos', []))} filas, siguiente={pagina.get('siguiente')!r}")
    filas, paginas, error = _todas(api, limite=50)
    res.comprobar("Recorrer con limit=50 trae todas, en orden y sin repetir", not error and [f["id"] for f in filas] == [d["id"] for d in datos],
                  error or f"{len(filas)} filas en {paginas} páginas")
    for malo in ("limit=0", "limit=101", "limit=diez", "cursor=xyz", "estado=olvidada", "prioridad=urgente"):
        r = api.pedir("GET", f"/api/v1/incidencias?{malo}")
        res.comprobar(f"?{malo} da 400 en problem+json", r.codigo == 400 and r.tipo == "application/problem+json", f"{r.codigo} {r.tipo}")
    filas, _, error = _todas(api, "estado=abierta&prioridad=alta", 100)
    esperado = [d["id"] for d in datos if d["estado"] == "abierta" and d["prioridad"] == "alta"]
    res.comprobar("?estado=abierta&prioridad=alta trae exactamente esas", not error and [f["id"] for f in filas] == esperado, error or f"{len(filas)} de {len(esperado)}")
    r = api.pedir("POST", "/api/v1/incidencias", {"titulo": "Prueba: caché", "prioridad": "media"})
    n = r.json.get("id") if isinstance(r.json, dict) else None
    res.comprobar("POST devuelve ETag", r.codigo == 201 and bool(r.cab("ETag")), f"{r.codigo} ETag={r.cab('ETag')}")
    r = api.pedir("GET", f"/api/v1/incidencias/{n}")
    etag = r.cab("ETag")
    res.comprobar("GET de una incidencia devuelve ETag entre comillas", r.codigo == 200 and bool(etag) and etag.startswith('"') and etag.endswith('"'), str(etag))
    r = api.pedir("GET", f"/api/v1/incidencias/{n}", cabeceras={"If-None-Match": etag or '""'})
    res.comprobar("Con If-None-Match igual: 304 sin cuerpo", r.codigo == 304 and r.texto == "", f"{r.codigo} {r.texto[:40]!r}")
    r = api.pedir("PATCH", f"/api/v1/incidencias/{n}", {"estado": "en-curso"}, cabeceras={"If-Match": etag or '""'})
    nuevo = r.cab("ETag")
    res.comprobar("PATCH con If-Match vigente: 200 y ETag nuevo", r.codigo == 200 and bool(nuevo) and nuevo != etag, f"{r.codigo} {etag} -> {nuevo}")
    r = api.pedir("GET", f"/api/v1/incidencias/{n}", cabeceras={"If-None-Match": etag or '""'})
    res.comprobar("Con If-None-Match antiguo: 200 con los datos nuevos", r.codigo == 200 and isinstance(r.json, dict) and r.json.get("estado") == "en-curso", str(r.codigo))
    r = api.pedir("PATCH", f"/api/v1/incidencias/{n}", {"estado": "cerrada"}, cabeceras={"If-Match": etag or '""'})
    res.comprobar("PATCH con If-Match antiguo: 412 en problem+json", r.codigo == 412 and r.tipo == "application/problem+json", f"{r.codigo} {r.tipo}")
    r = api.pedir("PUT", f"/api/v1/incidencias/{n}", {"titulo": "Pisado", "prioridad": "baja", "estado": "cerrada", "tecnico": None}, cabeceras={"If-Match": etag or '""'})
    res.comprobar("PUT con If-Match antiguo: 412", r.codigo == 412, str(r.codigo))
    r = api.pedir("GET", f"/api/v1/incidencias/{n}")
    res.comprobar("Tras los 412, la incidencia no ha cambiado", isinstance(r.json, dict) and r.json.get("estado") == "en-curso", str(r.json))
    api.pedir("DELETE", f"/api/v1/incidencias/{n}")


def suite_e8(api: Api, res: Resultado) -> None:
    print("E8 · Seguridad")
    usuarios = {u["usuario"]: u for u in _datos("usuarios.json")["usuarios"]}
    admin, lucia, marcos = usuarios["admin"], usuarios["lucia"], usuarios["marcos"]
    datos = _datos()["incidencias"]
    r = api.pedir("GET", "/api/v1/incidencias", token=None)
    res.comprobar("Sin token: 401 con WWW-Authenticate: Bearer", r.codigo == 401 and (r.cab("WWW-Authenticate") or "").startswith("Bearer"), f"{r.codigo} {r.cab('WWW-Authenticate')}")
    r = api.pedir("GET", "/api/v1/incidencias", token="inventado")
    res.comprobar("Con un token que no existe: 401", r.codigo == 401, str(r.codigo))
    r = api.pedir("GET", "/api/v1/incidencias", token=None, cabeceras={"X-User": "admin"})
    res.comprobar("Una cabecera X-User no sustituye al token: 401", r.codigo == 401, str(r.codigo))
    r = api.pedir("GET", "/api/v1/salud", token=None)
    res.comprobar("/api/v1/salud sigue sin pedir token", r.codigo == 200, str(r.codigo))
    r = api.pedir("POST", "/api/v1/sesiones", {"usuario": "lucia", "clave": lucia["clave"]}, token=None)
    res.comprobar("POST /api/v1/sesiones con la clave buena: 201 y su token", r.codigo == 201 and isinstance(r.json, dict) and r.json.get("token") == lucia["token"], f"{r.codigo}")
    codigos = [api.pedir("POST", "/api/v1/sesiones", {"usuario": "marcos", "clave": "mala"}, token=None).codigo for _ in range(5)]
    res.comprobar("Cinco claves malas: 401 cada vez", codigos == [401] * 5, str(codigos))
    r = api.pedir("POST", "/api/v1/sesiones", {"usuario": "marcos", "clave": "mala"}, token=None)
    espera = r.cab("Retry-After") or ""
    res.comprobar("La sexta: 429 con Retry-After en segundos", r.codigo == 429 and espera.isdigit() and int(espera) > 0, f"{r.codigo} Retry-After={espera!r}")
    r = api.pedir("POST", "/api/v1/sesiones", {"usuario": "marcos", "clave": marcos["clave"]}, token=None)
    res.comprobar("Durante el bloqueo, ni la clave buena entra: 429", r.codigo == 429, str(r.codigo))

    tl = lucia["token"]
    suyas = sorted(d["id"] for d in datos if d["tecnico"] == "lucia")
    ajena = next(d["id"] for d in datos if d["tecnico"] != "lucia")
    filas = []
    cursor = None
    while True:
        r = api.pedir("GET", "/api/v1/incidencias?limit=100" + (f"&cursor={cursor}" if cursor else ""), token=tl)
        if r.codigo != 200 or not isinstance(r.json, dict):
            break
        filas += r.json.get("datos", [])
        cursor = r.json.get("siguiente")
        if not cursor:
            break
    res.comprobar("Un técnico solo ve sus incidencias en la lista (BOLA)", sorted(f["id"] for f in filas) == suyas, f"{len(filas)} filas, esperaba {len(suyas)}")
    r = api.pedir("GET", f"/api/v1/incidencias/{ajena}", token=tl)
    res.comprobar("Una incidencia de otro le da 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("PATCH", f"/api/v1/incidencias/{ajena}", {"prioridad": "baja"}, token=tl)
    res.comprobar("Cambiar una de otro: 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("GET", f"/api/v1/incidencias/{ajena}/comentarios", token=tl)
    res.comprobar("Los comentarios de una de otro: 404", r.codigo == 404, str(r.codigo))
    r = api.pedir("POST", "/api/v1/incidencias", {"titulo": "Prueba: mía", "prioridad": "baja"}, token=tl)
    mia = r.json if isinstance(r.json, dict) else {}
    res.comprobar("Lo que crea un técnico queda a su nombre", r.codigo == 201 and mia.get("tecnico") == "lucia", f"{r.codigo} {mia.get('tecnico')}")
    r = api.pedir("POST", "/api/v1/incidencias", {"titulo": "Prueba: para otro", "prioridad": "baja", "tecnico": "marcos"}, token=tl)
    res.comprobar("Un técnico no crea incidencias para otro: 403", r.codigo == 403, str(r.codigo))
    r = api.pedir("PATCH", f"/api/v1/incidencias/{mia.get('id')}", {"tecnico": "marcos"}, token=tl)
    res.comprobar("Un técnico no reasigna incidencias: 403", r.codigo == 403, str(r.codigo))
    r = api.pedir("DELETE", f"/api/v1/incidencias/{mia.get('id')}", token=tl)
    res.comprobar("Un técnico no borra, ni lo suyo: 403 (BFLA)", r.codigo == 403, str(r.codigo))
    r = api.pedir("DELETE", f"/api/v1/incidencias/{mia.get('id')}", token=admin["token"])
    res.comprobar("Un administrador sí borra: 204", r.codigo == 204, str(r.codigo))
    r = api.pedir("PATCH", "/api/v1/usuarios/yo", {"rol": "admin"}, token=tl)
    res.comprobar("PATCH /api/v1/usuarios/yo con rol: 422 (asignación masiva)", r.codigo == 422, str(r.codigo))
    r = api.pedir("PATCH", "/api/v1/usuarios/yo", {"nombre": "Lucía G.", "rol": "admin"}, token=tl)
    res.comprobar("Ni mezclado con nombre: 422", r.codigo == 422, str(r.codigo))
    r = api.pedir("GET", "/api/v1/usuarios/yo", token=tl)
    res.comprobar("Y el rol sigue siendo tecnico", isinstance(r.json, dict) and r.json.get("rol") == "tecnico", r.texto[:80])
    r = api.pedir("PATCH", "/api/v1/usuarios/yo", {"nombre": "Lucía G."}, token=tl)
    res.comprobar("Cambiar solo el nombre sí: 200", r.codigo == 200 and isinstance(r.json, dict) and r.json.get("nombre") == "Lucía G.", str(r.codigo))
    vistas = [api.pedir(m, ruta, token=t) for m, ruta, t in (("GET", "/api/v1/salud", None), ("GET", "/api/v1/incidencias", None),
                                                             ("GET", "/api/v1/incidencias/1", admin["token"]), ("GET", "/api/v1/no-existe", admin["token"]))]
    delatoras = sorted({f"{k}: {v}" for r in vistas for k, v in r.cabeceras.items()
                        if k == "x-powered-by" or (k == "server" and TECNOLOGIA.search(v))})
    res.comprobar("Ninguna respuesta dice el lenguaje o el framework", not delatoras, "; ".join(delatoras))


# Qué pasa cada API en cada ejercicio. El corrector usa este mismo plan y en el mismo orden: primero cada API por
# separado, recién arrancada, y al final, en E5, E6 y E7, la comparación de las tres.
POR_API = {"e3": (suite_e3,), "e4": (suite_e3, suite_e4), "e5": (suite_e3, suite_e4), "e6": (suite_e3, suite_e4, suite_e6),
           "e7": (suite_e3, suite_e4, suite_e6, suite_e7), "e8": (suite_e3, suite_e4, suite_e6, suite_e7)}
COMPARAR = ("e5", "e6", "e7")


def ejecutar(ej: str, apis: dict[str, Api], base: str | None = None) -> dict[str, Resultado]:
    """Pasa las pruebas de un ejercicio a una API ({"": api}) o a las tres ({"go": …, "python": …, "node": …}).

    Devuelve un Resultado por API y, si se comparan, otro con la clave "" para la comparación. base es la dirección
    que sale en las órdenes para repetir un fallo (por defecto, la de cada API)."""
    resultados: dict[str, Resultado] = {}
    for nombre, api in apis.items():
        if nombre:
            print(f"--- {nombre}")
        res = resultados[nombre] = Resultado(base or api.base)
        try:
            if ej == "e8":
                suite_e8(api, res)
                print("--- Lo anterior, ahora con el token de administrador")
                admin = {u["usuario"]: u for u in _datos("usuarios.json")["usuarios"]}["admin"]["token"]
                api = Api(api.base, admin)
            for s in POR_API[ej]:
                s(api, res)
        except OSError as e:
            res.comprobar("la API dejó de responder durante las pruebas", False, str(e))
    if ej in COMPARAR and len(apis) == 3:
        res = resultados[""] = Resultado(base or "http://localhost:8000")
        try:
            suite_e5(list(apis.values()), res)
        except OSError as e:
            res.comprobar("la API dejó de responder durante las pruebas", False, str(e))
    return resultados


def fallo_suelto(texto: str) -> dict:
    """Un fallo que no sale de una prueba HTTP (no construye, falta un fichero…), con la pista que le toque."""
    return {"pista": pista(texto).id, "prueba": texto, "obtenido": "", "orden": None}


def suite_e2(fichero: str, res: Resultado) -> None:
    print("E2 · Diseño del contrato")
    try:
        import yaml
    except ImportError:
        raise SystemExit("Falta PyYAML: py -m pip install pyyaml")
    try:
        c = yaml.safe_load(Path(fichero).read_text(encoding="utf-8"))
    except Exception as e:
        res.comprobar("contrato.yaml es YAML válido", False, str(e)[:120])
        return
    res.comprobar("Es un OpenAPI 3", isinstance(c, dict) and str(c.get("openapi", "")).startswith("3"), str(c.get("openapi") if isinstance(c, dict) else c)[:40])
    rutas = (c or {}).get("paths") or {}
    # Un verbo como palabra de la ruta: separado por - o _, o en camelCase (listarComentarios, getIncidencias).
    verbos = re.compile(r"(?:^|[-_/]|(?<=[a-z])(?=[A-Z]))(?i:get|obtener|listar|list|crear|create|nuevo|new|add|anadir|borrar|eliminar|"
                        r"delete|remove|actualizar|update|modificar|cambiar|cerrar|close|editar|edit)(?:[-_]|$|(?=[A-Z]))")
    res.comprobar("Todas las rutas empiezan por /api/v1/", bool(rutas) and all(r.startswith("/api/v1/") for r in rutas), ", ".join(r for r in rutas if not r.startswith("/api/v1/")))
    res.comprobar("Ninguna ruta lleva un verbo: la acción la dice el método", not [r for r in rutas if any(verbos.search(s) for s in r.split("/"))],
                  ", ".join(r for r in rutas if any(verbos.search(s) for s in r.split("/"))))
    colecciones = {s for r in rutas for s in r.split("/")[3:4] if s and not s.startswith("{")} - {"salud"}
    res.comprobar("Las colecciones van en plural", bool(colecciones) and all(s.endswith("s") for s in colecciones), ", ".join(sorted(colecciones)))
    ops = [(r, m, op) for r, d in rutas.items() if isinstance(d, dict) for m, op in d.items()
           if m in ("get", "post", "put", "patch", "delete") and isinstance(op, dict)]
    metodos = {m for _, m, _ in ops}
    res.comprobar("Usa los cinco métodos", metodos == {"get", "post", "put", "patch", "delete"}, ", ".join(sorted(metodos)))
    codigos = lambda op: {str(k) for k in (op.get("responses") or {})}
    res.comprobar("Cada POST que crea responde 201", all("201" in codigos(op) for r, m, op in ops if m == "post"),
                  ", ".join(r for r, m, op in ops if m == "post" and "201" not in codigos(op)))
    res.comprobar("Cada DELETE responde 204", all("204" in codigos(op) for r, m, op in ops if m == "delete"),
                  ", ".join(r for r, m, op in ops if m == "delete" and "204" not in codigos(op)))
    res.comprobar("Ningún GET lleva cuerpo", not [r for r, m, op in ops if m == "get" and "requestBody" in op])
    sin_error = [f"{m.upper()} {r}" for r, m, op in ops if not r.endswith("/salud") and not any(k.startswith("4") for k in codigos(op))]
    res.comprobar("Cada operación declara sus errores 4xx", not sin_error, ", ".join(sin_error[:5]))
    con_id = [f"{m.upper()} {r}" for r, m, op in ops if "{" in r and "404" not in codigos(op)]
    res.comprobar("Toda ruta con {id} declara el 404", not con_id, ", ".join(con_id[:5]))
    lista = [op for r, m, op in ops if m == "get" and not r.endswith("}") and "comentarios" not in r and r.endswith("s")]
    res.comprobar("Hay una ruta para leer la colección y otra para un elemento", bool(lista) and any(r.endswith("}") for r, m, _ in ops if m == "get"))


# --- Los ficheros que acompañan a la API -----------------------------------------------------

LENGUAJES = ("go", "python", "node")


def lenguaje_de(carpeta: Path) -> str | None:
    for leng, fichero in (("go", "go.mod"), ("python", "requirements.txt"), ("node", "package.json")):
        if (carpeta / fichero).is_file():
            return leng
    return None


def _leer(f: Path) -> str:
    if not f.is_file():
        return ""
    datos = f.read_bytes()
    for codif in ("utf-8-sig", "utf-16"):
        try:
            return datos.decode(codif)
        except UnicodeDecodeError:
            pass
    return datos.decode("latin-1")


def revisar_ficheros(ej: str, carpeta: Path, res: Resultado) -> None:
    """Lo que se entrega además de la API: lo mismo aquí que en el corrector."""
    if ej in ("e3", "e4"):
        dicho, real = _leer(carpeta / "lenguaje.txt").strip().lower(), lenguaje_de(carpeta)
        res.comprobar("lenguaje.txt dice el lenguaje de la API", bool(dicho) and dicho == real,
                      f"lenguaje.txt dice «{dicho}» y la API está hecha en {real}")
    if ej == "e5":
        apartados = sum(1 for l in _leer(carpeta / "diferencias.md").splitlines() if re.match(r"(#{1,6}\s+|[-*]\s+|\d+[.)]\s+)\S", l))
        res.comprobar("diferencias.md explica al menos tres diferencias y su arreglo", apartados >= 3, f"{apartados} apartados")
    if ej == "e7":
        e = _leer(carpeta / "escenario.md")
        res.comprobar("escenario.md tiene las dos peticiones con If-Match, el 412 y la explicación",
                      bool(re.search(r"If-Match", e, re.I)) and "412" in e and len(e.split()) > 40, f"{len(e.split())} palabras")
    if ej == "e8":
        c = _leer(carpeta / "controles.md").upper()
        faltan = [x for x in ("CWE-639", "CWE-915", "CWE-285", "CWE-307") if x not in c]
        res.comprobar("controles.md documenta cada control con su CWE", not faltan, "faltan " + ", ".join(faltan))


# --- ¿Es la última versión? ------------------------------------------------------------------

ORIGEN = ("https://raw.githubusercontent.com/Oceano-Atlantico-Ciber/documentacion-hacking-etico/main/"
          "00-fundamentos/03-api-rest/ejercicios/plantillas/pruebas.py")


def avisar_si_hay_otra_version() -> None:
    """preparar.py copió pruebas.py a tu repositorio; si cambia en la web, tu copia se queda vieja y podría no
    coincidir con el corrector. Esto solo avisa: no descarga nada."""
    import hashlib
    import urllib.request
    try:
        with urllib.request.urlopen(ORIGEN, timeout=4) as r:
            web = r.read()
    except Exception:
        return
    norma = lambda b: b.replace(b"\r\n", b"\n")
    if hashlib.sha256(norma(web)).digest() != hashlib.sha256(norma(Path(__file__).read_bytes())).digest():
        print("! Hay una versión nueva de pruebas.py y el corrector usa esa. Descárgala encima de la tuya:\n"
              f'    PowerShell:    curl.exe -o "{Path(__file__).name}" {ORIGEN}\n'
              f"    macOS/Linux:   curl -o {Path(__file__).name} {ORIGEN}\n")


def _carpeta_del_ejercicio() -> Path:
    return AQUI.parent if AQUI.name in LENGUAJES else AQUI


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if len(argv) < 2 or argv[0] not in ("e2", "e3", "e4", "e5", "e6", "e7", "e8"):
        print("\n\n".join(__doc__.split("\n\n")[1:3]), file=sys.stderr)
        return 2
    avisar_si_hay_otra_version()
    ej = argv[0]
    if ej == "e2":
        res = Resultado()
        suite_e2(argv[1], res)
        resultados = {"": res}
    else:
        urls = argv[1:]
        if ej == "e5" and len(urls) != 3:
            print("E5 necesita las tres direcciones: Go, Python y Node", file=sys.stderr)
            return 2
        if len(urls) not in (1, 3):
            print("Pasa una dirección, o las tres (Go, Python y Node) para comprobar como el corrector", file=sys.stderr)
            return 2
        apis = {"": Api(urls[0])} if len(urls) == 1 else dict(zip(LENGUAJES, map(Api, urls)))
        try:
            apis[next(iter(apis))].pedir("GET", "/api/v1/salud")
        except OSError as e:
            print(f"No puedo hablar con la API: {e}. ¿Está arrancada en esa dirección?", file=sys.stderr)
            return 1
        resultados = ejecutar(ej, apis)
        if ej in ("e3", "e4", "e5", "e7", "e8"):
            print("--- Ficheros")
            revisar_ficheros(ej, _carpeta_del_ejercicio(), resultados.setdefault("", Resultado(urls[0])))
        if ej in ("e6", "e7", "e8") and len(urls) == 1:
            print("\n! Solo has pasado una API. El corrector prueba las tres y las compara: pásale las tres direcciones.")
    bien = sum(r.bien for r in resultados.values())
    mal = sum(r.mal for r in resultados.values())
    print(f"\n{bien} bien, {mal} mal")
    grupos = agrupar({k: r.fallos for k, r in resultados.items()})
    if grupos:
        print("\nQué arreglar (lo mismo que dirá el corrector):\n")
        print(informe(grupos, len([k for k in resultados if k])))
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
