// API de incidencias en Node con Express 5.
//
// Arrancar en tu equipo, desde esta carpeta:
//   npm install
//   node --watch main.js
// Probar:  curl.exe -i http://localhost:8000/api/v1/salud   (en macOS o Linux, curl)
//
// El contrato está en contrato.yaml. Express tiene costumbres propias (por ejemplo, añade la
// cabecera X-Powered-By y responde 404 en HTML): manda el contrato, no el framework.
import express from "express";
import { readFileSync } from "node:fs";

const datos = JSON.parse(readFileSync("incidencias.json", "utf-8"));

// Los datos viven en memoria: un Map por id.
const incidencias = new Map(datos.incidencias.map((i) => [i.id, i]));
const comentarios = new Map(datos.comentarios.map((c) => [c.id, c]));

const app = express();
app.use(express.json());

// Una respuesta JSON con su código. Úsala en todas las rutas.
const responder = (res, codigo, cuerpo) => res.status(codigo).json(cuerpo);

app.get("/api/v1/salud", (req, res) => responder(res, 200, { estado: "ok" }));

// E3: GET /api/v1/incidencias                     -> {"datos": [...], "siguiente": null}
// E3: GET /api/v1/incidencias/:id                 -> la incidencia, o 404
// E3: GET /api/v1/incidencias/:id/comentarios     -> {"datos": [...], "siguiente": null}, o 404

app.listen(8000, () => console.log("Escuchando en http://localhost:8000"));
