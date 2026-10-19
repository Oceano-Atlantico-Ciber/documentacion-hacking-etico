# S01 · Git y primer escaneo (14-15 oct)

Primera clase, práctica: presentación y montaje del equipo de trabajo. Planificación completa en [planificacion](../../planificacion/).

Enunciado del ejercicio: [ejercicios-hacking-etico/semanas/s01](https://github.com/Oceano-Atlantico-Ciber/ejercicios-hacking-etico/tree/main/semanas/s01).

## 1. Git y GitHub

1. Instala Git: <https://git-scm.com/downloads> (en Linux, `sudo apt install git`).
2. Configura tu identidad:

   ```bash
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu@correo"
   git config --global init.defaultBranch main
   ```

3. Crea una cuenta en <https://github.com> si no la tienes y pásale tu usuario al docente.
4. Comprueba:

   ```bash
   git --version
   ```

## 2. Docker

- **Windows:** instala Docker Desktop con el motor WSL 2 (<https://docs.docker.com/desktop/>).
- **macOS:** Docker Desktop.
- **Linux:** Docker Engine (<https://docs.docker.com/engine/install/>) y añade tu usuario al grupo `docker`.

Comprueba:

```bash
docker run --rm hello-world
docker compose version
```

## 3. IA: local o en la nube

Elige una opción. Las dos sirven para el curso.

### Opción A: local con Ollama

Los datos no salen de tu equipo. Necesita unos 8 GB de RAM libres para modelos pequeños.

1. Instala Ollama: <https://ollama.com/download>.
2. Descarga un modelo pequeño y pruébalo:

   ```bash
   ollama pull llama3.2
   ollama run llama3.2 "Explica en una frase qué es un escaneo de puertos"
   ```

### Opción B: en la nube

Usa el asistente que prefieras (por ejemplo Claude o ChatGPT) desde el navegador o su aplicación.

**Regla para las dos opciones:** nunca pegues en una IA en la nube contraseñas, claves ni datos reales de terceros.

## 4. Primer escaneo (si da tiempo)

Solo contra objetivos autorizados. `scanme.nmap.org` lo publica el proyecto Nmap precisamente para practicar:

```bash
docker run --rm instrumentisto/nmap -sV scanme.nmap.org
```

Apunta qué puertos aparecen abiertos y pregúntale a tu IA qué es cada servicio.

## Checklist

- [ ] `git --version` responde y tu identidad está configurada
- [ ] Usuario de GitHub enviado al docente
- [ ] `docker run --rm hello-world` funciona
- [ ] IA local o en la nube respondiendo
- [ ] (Extra) Primer `nmap` ejecutado
