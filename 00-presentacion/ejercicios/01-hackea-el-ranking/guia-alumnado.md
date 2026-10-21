# Guía de exploración: «Hackea el ranking»

## Alcance y preparación

Trabaja únicamente contra la web del juego que ha indicado el docente y durante la práctica autorizada. Si la dirección no es `http://localhost:8080`, sustituye esa base por la URL exacta que te hayan dado. No escanees la red del aula ni pruebes estas técnicas contra otras webs.

**La aplicación está en inglés y esta guía en español.** En la pantalla, **Start game** inicia una partida, **Click** suma pulsaciones, **Leaderboard** es el ranking y **Flags** son las banderas. `trusted` significa que el servidor se fía de los datos enviados por el navegador; `validated` significa que el servidor calcula la puntuación. La dirección con `?scoreboard` muestra el marcador para el proyector y oculta los controles para jugar.

`localhost` siempre apunta a **tu propio equipo**. En clase el juego se publica con un túnel de Pinggy: usa el enlace que proyecta el docente, por ejemplo `https://abcd.a.free.pinggy.link` (sin `:8080`), tanto en el navegador como en todos los comandos. Si el túnel se reabre, el enlace cambia y hay que usar el nuevo. `http://localhost:8080` solo sirve si levantas el juego en tu equipo.

La guía está escrita para el modo `trusted`. Abre la página en el navegador y comprueba el modo y el marcador antes de empezar:

```bash
curl -i http://localhost:8080/api/leaderboard
```

Busca `"mode": "trusted"` y `"leaderboard"` en la respuesta. `-i` muestra también el código HTTP: `200` significa que la petición ha funcionado. En Windows PowerShell, usa `curl.exe` en lugar de `curl` si este nombre ejecuta el alias de PowerShell y pega cada ejemplo de varias líneas como una sola línea. La barra invertida al final de línea sirve para continuar comandos en Bash, zsh y Git Bash.

## 1. Observa qué hace el navegador

Abre las herramientas de desarrollo con F12 y entra en **Network/Red**. Si hay mucho tráfico, filtra por **Fetch/XHR**. Escribe tu nombre, pulsa **Start game**, pulsa **Click** varias veces y espera los diez segundos. Selecciona las peticiones a `/api/game` y `/api/score`: mira **Headers/Cabeceras**, **Payload/Carga útil** y **Response/Respuesta**. Identifica qué petición guarda la puntuación, su método HTTP, la ruta, las cabeceras y los campos enviados. Si no ves las peticiones, abre Network antes de iniciar otra partida.

También puedes leer el código del cliente con **Ver código fuente**. Apunta qué datos calcula el navegador y qué pistas deja el propio código sobre otras rutas. No des por hecho que una cabecera o un botón del navegador impiden enviar peticiones directamente.

## 2. Envía una puntuación inventada con curl

El cliente normal envía la puntuación al terminar. Prueba a enviar una puntuación directamente al mismo endpoint, sin jugar:

```bash
curl -i -X POST http://localhost:8080/api/score \
  -H 'Content-Type: application/json' \
  --data '{"name":"ana","score":9999}'
```

Después consulta el ranking:

```bash
curl -sS http://localhost:8080/api/leaderboard
```

Deberías recibir `200` y ver a `ana` con una puntuación de `9999`, superior al máximo estimado de `150`. Las banderas de este ejemplo son `impossible` y `no_browser` (en pantalla, **Impossible score** y **No browser**). Anota qué demuestra cada una. ¿Qué dato está aceptando el servidor sin verificar que la partida haya ocurrido? Usa otro nombre si `ana` ya aparece en el marcador.

## 3. Falsifica una cabecera del navegador

El cliente envía `X-Game: browser`. Repite la petición anterior con esa cabecera:

```bash
curl -i -X POST http://localhost:8080/api/score \
  -H 'Content-Type: application/json' \
  -H 'X-Game: browser' \
  --data '{"name":"bea","score":9999}'
```

Vuelve a mirar el ranking. `bea` debería obtener `impossible`, pero no `no_browser`, aunque la petición también se haya enviado con `curl`. ¿Puede el servidor saber por esa cabecera si la petición viene realmente de la web? ¿Qué tendría que validar en su lugar?

## 4. Cambia la petición desde la consola del navegador

Con la página del juego abierta, entra en **Console/Consola** y ejecuta una petición desde el mismo origen:

```js
fetch("/api/score", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Game": "browser"
  },
  body: JSON.stringify({ name: "cris", score: 9999 })
}).then(r => r.json()).then(console.log)
```

Consulta el ranking y compara el resultado con los retos hechos con `curl`. Esta técnica y la anterior llegan al mismo fallo de diseño por caminos distintos: el cliente puede fabricar la petición y sus valores. Este ejemplo usa una ruta relativa (`/api/score`), por eso debe ejecutarse en la consola de la página del juego.

## 5. Modifica la puntuación de otra persona

Prueba el método `PUT` contra una cuenta de ejemplo. Pide a otra persona que juegue primero; cambia `dani` por el nombre exacto que aparece en el ranking y `ana` por el tuyo:

```bash
curl -i -X PUT http://localhost:8080/api/score/dani \
  -H 'Content-Type: application/json' \
  --data '{"author":"ana","score":9999}'
```

Consulta el ranking. La puntuación de `dani` debería subir a `9999` y `ana` debería recibir `other_player` (**Changed another player's score**). El servidor conserva la puntuación más alta de cada nombre, así que usa un valor superior al que ya tenga el jugador elegido. Explica qué control de autorización falta: conocer o escribir el nombre de una persona no debería bastar para cambiar sus datos.

## 6. Encuentra y prueba la ruta de reinicio

Busca pistas en el código que se entrega al navegador y localiza la ruta de administración. **Este reto borra todo el ranking y las partidas en curso de toda la clase.** Está permitido: avisa en voz alta antes de lanzarlo para que nadie pierda una partida a medias.

```bash
curl -i 'http://localhost:8080/api/admin/reset?name=ana'
```

Consulta el ranking de nuevo: los resultados anteriores desaparecen y `ana` recibe `hidden_route` (**Hidden admin route**). ¿Se pidió autenticación? ¿Qué efecto tiene que una operación que modifica el estado se pueda llamar con `GET`? Describe cómo se podría limitar esta acción a una persona autorizada.

## Comparación con el modo `validated`

Al final, el docente puede reiniciar el juego en modo `validated`. Compruébalo primero en `/api/leaderboard`; al cambiar de modo se reinicia el marcador. Juega una partida normal y observa que el navegador envía cada pulsación a `/api/click` y termina con `/api/finish`. Repite las comprobaciones de los retos 2, 5 y 6 contra esa instancia: `/api/score` y el `PUT` deben responder `404`, y el reinicio debe responder `403`. Comprueba también que esas peticiones no cambian el marcador. En este modo el servidor lleva la cuenta de la partida.

## Si algo no coincide

- **No conecta o no abre la web:** comprueba que estás usando el enlace de Pinggy que se proyecta ahora mismo; si responde `502` o no existe, el túnel se ha reabierto con otra URL. `localhost` solo sirve si el juego está en tu equipo.
- **Recibes `404` en `/api/score`:** consulta `/api/leaderboard`; probablemente el servidor ya está en modo `validated`, o has escrito otra ruta.
- **Recibes `400 Invalid name`:** usa un nombre de entre 1 y 24 caracteres. Se admiten letras, números, espacios, guiones, puntos y guiones bajos.
- **El ranking parece tardar en actualizarse:** vuelve a consultar `/api/leaderboard` o espera unos segundos; la página lo refresca cada cinco segundos.
- **Recibes un resultado inesperado:** guarda el método, la URL, el cuerpo, el código HTTP y la respuesta antes de repetir la prueba. Así podrás distinguir un error de escritura de un comportamiento del servidor.

## Qué debes entregar en tus notas

Para cada reto, registra:

- Qué querías comprobar y qué petición enviaste (método, ruta, cabeceras y cuerpo).
- La respuesta del servidor y el cambio observado en el ranking.
- La causa del fallo y una medida concreta para corregirlo.
- Si la prueba modificó datos compartidos; en especial, el reto de reinicio.

Puedes usar este formato breve: **hipótesis → petición enviada → respuesta y cambio en el ranking → explicación → corrección propuesta**. Copia solo los fragmentos relevantes de la respuesta; no hace falta pegar toda la salida de la terminal.

No es necesario buscar inyección SQL: esta práctica no usa una base de datos. El código también escapa el nombre antes de insertarlo en la tabla, así que no afirmes que has encontrado XSS sin una prueba que lo demuestre.
