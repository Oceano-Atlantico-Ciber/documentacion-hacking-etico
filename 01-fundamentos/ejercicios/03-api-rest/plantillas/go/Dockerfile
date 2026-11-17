# Construcción en dos etapas: se compila con la imagen de Go y el binario se copia a una imagen
# mínima, sin compilador ni código fuente.
FROM golang:1.24-alpine AS compilar
WORKDIR /src
COPY go.mod ./
COPY *.go ./
RUN CGO_ENABLED=0 go build -o /api .

FROM alpine:3.21
WORKDIR /app
# Completa: copia el binario /api de la etapa «compilar» (COPY --from=compilar ...)
# y incidencias.json, usa un usuario sin privilegios, declara el puerto 8000
# y arranca el binario con ENTRYPOINT.
