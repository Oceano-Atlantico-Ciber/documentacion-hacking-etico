"""API de incidencias del laboratorio del E1. Solo lectura, alta y los errores básicos.

No es la que vas a programar: es la que interrogas a mano para ver que una API REST no es más
que HTTP. Biblioteca estándar de Python, sin frameworks.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

with open("incidencias.json", encoding="utf-8") as f:
    INCIDENCIAS = {i["id"]: i for i in json.load(f)["incidencias"]}
SIGUIENTE = max(INCIDENCIAS) + 1


class Api(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def responder(self, codigo, cuerpo=None, cabeceras=()):
        datos = b"" if cuerpo is None else json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        for nombre, valor in cabeceras:
            self.send_header(nombre, valor)
        if cuerpo is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def ruta(self):
        partes = [p for p in self.path.split("?")[0].split("/") if p]
        if partes[:3] != ["api", "v1", "incidencias"] or len(partes) > 4:
            return None, None
        if len(partes) == 3:
            return "coleccion", None
        return ("elemento", int(partes[3])) if partes[3].isdigit() else (None, None)

    def no_admitido(self, que):
        permitidos = "GET, POST" if que == "coleccion" else "GET"
        self.responder(405, {"error": f"{self.command} no se admite aquí"}, [("Allow", permitidos)])

    def do_GET(self):
        que, n = self.ruta()
        if que == "coleccion":
            self.responder(200, {"datos": list(INCIDENCIAS.values()), "siguiente": None})
        elif que == "elemento" and n in INCIDENCIAS:
            self.responder(200, INCIDENCIAS[n])
        else:
            self.responder(404, {"error": f"No existe {self.path}"})

    def do_POST(self):
        global SIGUIENTE
        que, _ = self.ruta()
        if que != "coleccion":
            return self.no_admitido(que) if que else self.responder(404, {"error": f"No existe {self.path}"})
        largo = int(self.headers.get("Content-Length") or 0)
        try:
            datos = json.loads(self.rfile.read(largo))
            titulo, prioridad = datos["titulo"], datos["prioridad"]
        except (ValueError, KeyError, TypeError):
            return self.responder(400, {"error": "Hace falta un JSON con titulo y prioridad"})
        nueva = {"id": SIGUIENTE, "titulo": titulo, "prioridad": prioridad, "estado": "abierta", "tecnico": None}
        INCIDENCIAS[SIGUIENTE] = nueva
        SIGUIENTE += 1
        self.responder(201, nueva, [("Location", f"/api/v1/incidencias/{nueva['id']}")])

    def otro(self):
        que, _ = self.ruta()
        self.no_admitido(que) if que else self.responder(404, {"error": f"No existe {self.path}"})

    do_PUT = do_PATCH = do_DELETE = otro


ThreadingHTTPServer(("", 8080), Api).serve_forever()
