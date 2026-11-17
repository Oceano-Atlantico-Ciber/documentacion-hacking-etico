FROM node:22-alpine
WORKDIR /app
# Las dependencias primero, para que su capa salga de la caché mientras no cambien.
COPY package.json ./
RUN npm install --omit=dev
# Completa: copia main.js e incidencias.json, usa el usuario sin privilegios «node»,
# declara el puerto 8000 y arranca con:
#   ENTRYPOINT ["node", "main.js"]
