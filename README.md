# Documentación · Hacking ético

Repositorio público con todo el material de la asignatura de Hacking ético: las clases, los ficheros y todo lo que vayamos generando durante el curso.

## Repositorios de la organización

- [documentacion-hacking-etico](https://github.com/Oceano-Atlantico-Ciber/documentacion-hacking-etico) (este): clases, laboratorio, planificación y glosario.
- [ejercicios-hacking-etico](https://github.com/Oceano-Atlantico-Ciber/ejercicios-hacking-etico): enunciados, ficheros de partida y plantilla de vuestro repositorio de entregas.
- [soluciones-hacking-etico](https://github.com/Oceano-Atlantico-Ciber/soluciones-hacking-etico): privado, solo para el docente.

## Estructura

- `clases/sNN/`: la clase de cada semana.
- `laboratorio/`: el Docker Compose del laboratorio.
- `planificacion/`: la planificación del primer día.
- [`glosario.md`](glosario.md): las herramientas del curso en una línea cada una.

## Normas de entrega

1. Cada semana se entrega con **una etiqueta `entrega-sNN`** en vuestro repositorio (por ejemplo `entrega-s01`), creada **antes del jueves** de esa semana.
2. **Se corrige lo que hay en la etiqueta.** Lo que subáis después a `main` no cuenta para esa entrega.
3. Al subir la etiqueta, GitHub Actions pasa Trivy sobre el repositorio; si encuentra fallos HIGH o CRITICAL, la ejecución falla.
4. Nada de secretos en el repositorio (claves, contraseñas, ficheros `.env`).

```bash
git tag entrega-s01
git push origin entrega-s01
```
