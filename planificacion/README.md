# Planificación del primer día

Clase práctica. La idea: ver que con curiosidad y práctica se pueden hacer cosas reales sin saberlo todo, y salir con el equipo listo para trabajar el resto del curso.

## 1. Presentación (≈ 30 min)

- A qué se dedica el docente: trabajo como SRE (fiabilidad de sistemas en producción) y cómo se relaciona con la seguridad.
- Experiencia práctica en hacking con proyectos propios, con **demostración en vivo**.
- Mensaje: nadie sabe de todo; lo que cuenta es saber buscar, probar, romper en un entorno controlado y aprender de ello.
- Normas del curso: solo se ataca lo que está dentro del alcance autorizado (`alcance.md`).

## 2. Setup de trabajo (resto de la sesión)

Cada alumno sigue la guía de [clases/s01](../clases/s01/) y comprueba cada paso antes de pasar al siguiente.

| Bloque | Objetivo | Comprobación |
|---|---|---|
| Git y GitHub | Git instalado y configurado, cuenta de GitHub, usuario enviado al docente | `git --version`, `git config --global user.name` |
| Docker | Docker funcionando (Docker Desktop con WSL 2 en Windows, Docker Engine en Linux) | `docker run --rm hello-world` |
| IA | Un asistente de IA listo: **local** con Ollama o **en la nube**, a elegir | Respuesta a una pregunta de prueba |
| Primer escaneo (si da tiempo) | Primer `nmap` desde Docker contra el objetivo autorizado | Salida con puertos abiertos |

## 3. Cierre (≈ 10 min)

- Quién tiene todo funcionando y quién necesita ayuda antes de la próxima sesión.
- Recordatorio: la primera entrega es la etiqueta `entrega-s01`.
