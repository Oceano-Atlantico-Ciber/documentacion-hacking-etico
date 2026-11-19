"""API de incidencias en Python con FastAPI.

Arrancar en tu equipo, desde esta carpeta:
    py -m venv .venv
    source .venv/Scripts/activate        (Git Bash)
    pip install -r requirements.txt
    uvicorn main:app --port 8000 --reload

Probar:  curl.exe -i http://localhost:8000/api/v1/salud
Documentación que genera FastAPI: http://localhost:8000/docs

El contrato está en contrato.yaml. FastAPI tiene costumbres propias (por ejemplo, responde 422
si un parámetro de la ruta no es del tipo declarado): manda el contrato, no el framework.
"""

import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse

with open("incidencias.json", encoding="utf-8") as f:
    datos = json.load(f)

# Los datos viven en memoria: un diccionario por id.
incidencias = {i["id"]: i for i in datos["incidencias"]}
comentarios = {c["id"]: c for c in datos["comentarios"]}

app = FastAPI(title="API de incidencias")


def responder(codigo: int, cuerpo) -> JSONResponse:
    """Una respuesta JSON con su código. Úsala en todas las rutas."""
    return JSONResponse(status_code=codigo, content=cuerpo)


@app.get("/api/v1/salud")
def salud():
    return responder(200, {"estado": "ok"})


# E3: GET /api/v1/incidencias                     -> {"datos": [...], "siguiente": None}
# E3: GET /api/v1/incidencias/{id}                -> la incidencia, o 404
# E3: GET /api/v1/incidencias/{id}/comentarios    -> {"datos": [...], "siguiente": None}, o 404
