FROM python:3.12-alpine
WORKDIR /app
COPY api.py incidencias.json ./
USER nobody
EXPOSE 8080
ENTRYPOINT ["python", "-u", "api.py"]
