FROM python:3.12-alpine
WORKDIR /app
# Las dependencias primero, para que su capa salga de la caché mientras no cambien.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Completa: copia main.py e incidencias.json, usa un usuario sin privilegios,
# declara el puerto 8000 y arranca con:
#   ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
