// API de incidencias en Go, solo con la biblioteca estándar (net/http).
//
// Arrancar en tu equipo:   go run .
// Probar:                  curl.exe -i http://localhost:8000/api/v1/salud
//
// El contrato está en contrato.yaml. Desde Go 1.22 el enrutador entiende el método y los
// parámetros de la ruta: "GET /api/v1/incidencias/{id}" y r.PathValue("id").
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

type Incidencia struct {
	ID        int     `json:"id"`
	Titulo    string  `json:"titulo"`
	Prioridad string  `json:"prioridad"`
	Estado    string  `json:"estado"`
	Tecnico   *string `json:"tecnico"` // puntero: puede ser null
}

type Comentario struct {
	ID         int    `json:"id"`
	Incidencia int    `json:"incidencia"`
	Texto      string `json:"texto"`
}

// Los datos viven en memoria: se cargan de incidencias.json al arrancar.
var datos struct {
	Incidencias []Incidencia `json:"incidencias"`
	Comentarios []Comentario `json:"comentarios"`
}

// responder escribe una respuesta JSON con su código. Úsala en todas las rutas.
func responder(w http.ResponseWriter, codigo int, cuerpo any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(codigo)
	json.NewEncoder(w).Encode(cuerpo)
}

func main() {
	crudo, err := os.ReadFile("incidencias.json")
	if err != nil {
		log.Fatal(err)
	}
	if err := json.Unmarshal(crudo, &datos); err != nil {
		log.Fatal(err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/salud", func(w http.ResponseWriter, r *http.Request) {
		responder(w, http.StatusOK, map[string]string{"estado": "ok"})
	})

	// E3: GET /api/v1/incidencias                     -> {"datos": [...], "siguiente": null}
	// E3: GET /api/v1/incidencias/{id}                -> la incidencia, o 404
	// E3: GET /api/v1/incidencias/{id}/comentarios    -> {"datos": [...], "siguiente": null}, o 404

	log.Println("Escuchando en http://localhost:8000")
	log.Fatal(http.ListenAndServe(":8000", mux))
}
