"""Pruebas de caja negra del contrato de incidencias: hablan con tu API solo por HTTP.

Uso, con tu API recién arrancada (las pruebas crean y borran datos):

    py pruebas.py e3 http://localhost:8000
    py pruebas.py e4 http://localhost:8000
    py pruebas.py e5 http://localhost:8001 http://localhost:8002 http://localhost:8003
    py pruebas.py e6 http://localhost:8000
    py pruebas.py e7 http://localhost:8000
    py pruebas.py e8 http://localhost:8000
    py pruebas.py e2 contrato.yaml            (necesita: py -m pip install pyyaml)

Da igual en qué lenguaje esté la API: estas pruebas no ven el código, solo lo que responde.
Lee incidencias.json (y en el E8 usuarios.json) de su misma carpeta para saber qué esperar.
El corrector pasa estas mismas pruebas y alguna más.
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

    def pedir(self, metodo: str, ruta: str, cuerpo=None, cabeceras: dict | None = None, crudo: str | None = None,
              token: str | None = "") -> Respuesta:
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
        c = http.client.HTTPConnection(self.equipo, self.puerto, timeout=10)
        try:
            c.request(metodo, ruta, body=datos, headers=cab)
            r = c.getresponse()
            return Respuesta(r.status, {k.lower(): v for k, v in r.getheaders()}, r.read().decode("utf-8", "replace"))
        finally:
            c.close()


# --- Registro de resultados ----------------------------------------------------------------

class Resultado:
    def __init__(self):
        self.bien = self.mal = 0

    def comprobar(self, nombre: str, condicion: bool, detalle: str = "") -> bool:
        if condicion:
            self.bien += 1
            print(f"  ✓ {nombre}")
        else:
            self.mal += 1
            print(f"  ✗ {nombre}" + (f"  ({detalle})" if detalle else ""))
        return condicion


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


SUITES = {"e3": [suite_e3], "e4": [suite_e3, suite_e4], "e6": [suite_e3, suite_e4, suite_e6],
          "e7": [suite_e3, suite_e4, suite_e6, suite_e7], "e8": [suite_e8]}


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


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if len(argv) < 2 or argv[0] not in ("e2", "e3", "e4", "e5", "e6", "e7", "e8"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    res = Resultado()
    try:
        if argv[0] == "e2":
            suite_e2(argv[1], res)
        elif argv[0] == "e5":
            if len(argv) != 4:
                print("E5 necesita las tres direcciones: Go, Python y Node", file=sys.stderr)
                return 2
            apis = [Api(u) for u in argv[1:]]
            suite_e5(apis, res)
            for a in apis:
                print(f"--- {a.equipo}:{a.puerto}")
                suite_e4(a, res)
        elif argv[0] == "e8":
            api = Api(argv[1])
            suite_e8(api, res)
            print("--- Lo anterior, ahora con el token de administrador")
            admin = Api(argv[1], {u["usuario"]: u for u in _datos("usuarios.json")["usuarios"]}["admin"]["token"])
            for s in (suite_e3, suite_e4, suite_e6, suite_e7):
                s(admin, res)
        else:
            api = Api(argv[1])
            for s in SUITES[argv[0]]:
                s(api, res)
    except (ConnectionError, OSError) as e:
        print(f"No puedo hablar con la API: {e}. ¿Está arrancada en esa dirección?", file=sys.stderr)
        return 1
    print(f"\n{res.bien} bien, {res.mal} mal")
    return 1 if res.mal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
