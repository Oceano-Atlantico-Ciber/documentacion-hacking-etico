"""Comprobaciones de cada ejercicio de Docker, en el orden de «El corrector marca fallo si» de su página.

Cada una recibe el árbol del repositorio del alumno en el commit evaluado y produce sus fallos uno a uno;
lanza Fallo cuando lo entregado no permite seguir. Lo esperado sale de preparar.py, el mismo módulo que da
los ficheros de partida. Lo que el alumno construye o levanta pasa antes por levantar.py o compose.py.
"""

from __future__ import annotations

import io
import json
import os
import re
import secrets
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

import preparar as p

from . import compose, levantar
from .docker import Fallo, contenedor, docker, http, obligatorio, reintentar

Comprobacion = Callable[["Caso"], Iterator[str]]


@dataclass(frozen=True)
class Caso:
    usuario: str
    raiz: Path  # el repositorio del alumno, extraído del commit evaluado
    ej: str

    @property
    def carpeta(self) -> Path:
        return self.raiz / p.RAIZ / self.ej

    def leer(self, nombre: str) -> str | None:
        f = self.carpeta / nombre
        return _texto(f.read_bytes()) if f.is_file() else None

    def exigir(self, *nombres: str) -> None:
        if faltan := [n for n in nombres if not (self.carpeta / n).is_file()]:
            raise Fallo(f"falta {', '.join(f'{p.RAIZ}/{self.ej}/{n}' for n in faltan)}")


def _texto(datos: bytes) -> str:
    """Texto de un fichero hecho en Windows: UTF-8 con o sin BOM, o UTF-16 si salió de PowerShell; sin CR."""
    codificacion = "utf-16" if datos[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return datos.decode(codificacion, "replace").replace("\r\n", "\n")


def _lineas(texto: str | None) -> list[str]:
    """Las líneas con contenido, con los espacios normalizados: lo que el editor cambia sin que se vea no cuenta."""
    return [" ".join(linea.split()) for linea in (texto or "").splitlines() if linea.strip()]


def _igual(real: str | None, esperado: str) -> bool:
    return real is not None and _lineas(real) == _lineas(esperado)


def _diferencia(real: str, esperado: str) -> str:
    """La primera diferencia entre dos textos, explicada para el alumno."""
    r, e = _lineas(real), _lineas(esperado)
    for n, (a, b) in enumerate(zip(r, e), 1):
        if a != b:
            return f"la línea {n} es «{a}» y debería ser «{b}»"
    return f"falta la línea «{e[len(r)]}»" if len(r) < len(e) else f"sobra la línea «{r[len(e)]}»"


def _salida(texto: str) -> str:
    """Una salida de varias líneas en una sola, para citarla en un fallo."""
    return " / ".join(_lineas(texto)) or "nada"


def _from(dockerfile: str) -> str | None:
    """Imagen del primer FROM, sin AS."""
    m = re.search(r"^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)", dockerfile, re.IGNORECASE | re.MULTILINE)
    return m.group(1) if m else None


def _construir(caso: Caso, etiqueta: str, *opciones: str, carpeta: Path | None = None) -> str:
    """Construye y devuelve la salida de BuildKit (va a stderr), o Fallo si no construye."""
    r = docker("build", "--progress=plain", *opciones, "-t", etiqueta, str(carpeta or caso.carpeta), espera=600)
    if r.codigo:
        raise Fallo(f"el Dockerfile no construye: {r.motivo}")
    return r.error


def _config(imagen: str) -> dict:
    return json.loads(obligatorio(docker("image", "inspect", imagen)).salida)[0]["Config"]


def _puertos(c: dict) -> dict[str, list[tuple[str, str]]]:
    """Puertos publicados de un contenedor: {"80/tcp": [("127.0.0.1", "8080")]}."""
    return {k: sorted((b.get("HostIp", ""), b.get("HostPort", "")) for b in v)
            for k, v in (c["HostConfig"].get("PortBindings") or {}).items() if v}


def _publica(c: dict) -> str:
    """Los puertos publicados, como los escribe docker ps: 127.0.0.1:8080->80/tcp."""
    return ", ".join(f"{ip or '0.0.0.0'}:{puerto}->{interno}" for interno, enlaces in _puertos(c).items()
                     for ip, puerto in enlaces) or "ningún puerto"


def _montado(c: dict, destino: str) -> str:
    """Qué hay montado en destino, para explicar un montaje que no es el pedido."""
    return ", ".join(f"{m['Type']} {m.get('Name') or m.get('Source')}" + ("" if m["RW"] else " en solo lectura")
                     for m in c["Mounts"] if m["Destination"] == destino) or "nada"


def _carpeta(ruta: str | Path) -> str:
    """Una carpeta del equipo, comparable: Docker Desktop en Windows puede dar C:\… o /run/desktop/mnt/host/c/…"""
    if m := re.fullmatch(r"(?:/run/desktop/mnt/host|/host_mnt|/mnt)/([a-zA-Z])(/.*)?", str(ruta)):
        if os.name == "nt":
            ruta = f"{m[1]}:{m[2] or '/'}"
    return os.path.normcase(str(Path(ruta).resolve()))


def _monta(c: dict, tipo: str, origen: str | Path, destino: str, solo_lectura: bool = False) -> bool:
    clave = "Name" if tipo == "volume" else "Source"
    return any(m["Type"] == tipo and m["Destination"] == destino and (not solo_lectura or not m["RW"])
               and (m.get(clave) == origen if tipo == "volume" else _carpeta(m[clave]) == _carpeta(origen))
               for m in c["Mounts"])


def _en_marcha(*nombres: str) -> list[dict]:
    """Los contenedores que deja levantar.sh, que tienen que seguir en marcha unos segundos después."""
    time.sleep(3)
    datos = []
    for nombre in nombres:
        if (c := contenedor(nombre)) is None:
            raise Fallo(f"levantar.sh no crea {nombre}")
        if not c["State"]["Running"]:
            raise Fallo(f"{nombre} no sigue en marcha: {docker('logs', '--tail', '1', nombre).error.strip() or 'mira docker logs'}")
        datos.append(c)
    return datos


def _sondeo(texto: str, esperado: list[tuple[str | None, str, str]]) -> str | None:
    """Por qué las líneas de un sondeo no son (equipo, puerto, estado) en ese orden; equipo None vale cualquiera."""
    lineas = _lineas(texto)
    if len(lineas) != len(esperado):
        return f"tiene {len(lineas)} líneas y debe tener {len(esperado)}, una por puerto sondeado"
    for n, (linea, (equipo, puerto, estado)) in enumerate(zip(lineas, esperado), 1):
        m = re.fullmatch(r"(\S+):(\d+) (abierto|cerrado)", linea)
        if not m:
            return f"la línea {n}, «{linea}», no tiene la forma equipo:puerto abierto|cerrado"
        if (equipo or m[1], puerto, estado) != (m[1], m[2], m[3]):
            return f"la línea {n} es «{linea}» y debería ser «{equipo or m[1]}:{puerto} {estado}»"
    return None


# --- E1 · Ciclo de vida ------------------------------------------------------------------

def e1(caso: Caso) -> Iterator[str]:
    caso.exigir("index.html", "inspect.json", "logs.txt")
    pagina = p.e1_pagina(caso.usuario)
    if not _igual(real := caso.leer("index.html"), pagina):
        yield f"index.html ha cambiado: {_diferencia(real, pagina)}. Tiene que quedar como lo dejó preparar.py"
    try:
        datos = json.loads(caso.leer("inspect.json"))
        c = datos[0]
        nombre, imagen, estado = c["Name"], c["Config"]["Image"], c["State"]
    except (ValueError, LookupError, TypeError):
        raise Fallo("inspect.json no es la salida de docker container inspect e1-web") from None
    if nombre != "/e1-web":
        yield f"el contenedor de inspect.json se llamaba {nombre.lstrip('/')} y debía llamarse e1-web"
    if imagen != "nginx:1.27-alpine":
        yield f"el contenedor salía de {imagen} y debía salir de nginx:1.27-alpine"
    if _puertos(c) != {"80/tcp": [("127.0.0.1", "8080")]}:
        yield f"el contenedor no publicaba 127.0.0.1:8080->80/tcp: publicaba {_publica(c)}"
    if estado["FinishedAt"].startswith("0001"):
        yield "el contenedor no llegó a pararse y volver a arrancar: según inspect.json no se paró nunca"
    elif estado["StartedAt"] <= estado["FinishedAt"]:
        yield ("el contenedor no llegó a pararse y volver a arrancar: según inspect.json sigue parado; "
               "saca inspect.json después de docker start")
    # nginx anota el tamaño de cada respuesta: el de tu página, tal como la copiaste (LF o CRLF).
    tamanos = {str(len(pagina.encode())), str(len(pagina.replace("\n", "\r\n").encode())),
               str((caso.carpeta / "index.html").stat().st_size)}
    servidas = re.findall(r'"GET /(?:index\.html)? HTTP/1\.[01]" 200 (\d+)', caso.leer("logs.txt"))
    if not servidas:
        yield "en logs.txt no hay ninguna petición servida con tu página: no hay ningún GET / con código 200"
    elif not tamanos & set(servidas):
        yield (f"en logs.txt no hay ninguna petición servida con tu página: las respuestas miden {', '.join(sorted(set(servidas)))} "
               f"bytes y tu página mide {', '.join(sorted(tamanos))}; ¿copiaste index.html al contenedor?")


# --- E2 · Tu primera imagen --------------------------------------------------------------

def e2(caso: Caso) -> Iterator[str]:
    caso.exigir("Dockerfile", "sondeo.txt")
    if motivo := _sondeo(caso.leer("sondeo.txt"), [(None, "22", "cerrado"), (None, "80", "abierto"), (None, "443", "cerrado")]):
        yield f"sondeo.txt no es el sondeo de 22, 80 y 443, con el 80 abierto: {motivo}"
    if (imagen := _from(caso.leer("Dockerfile"))) != "python:3.12-alpine":
        yield f"el Dockerfile parte de {imagen or 'ninguna imagen (no hay FROM)'} y debe partir de python:3.12-alpine"
    _construir(caso, "corrector-e2")
    uso = docker("run", "--rm", "--network", "none", "corrector-e2")
    if uso.codigo != 2 or "Uso: python sondeo.py" not in uso.error:
        raise Fallo("sin argumentos, la imagen no muestra el uso del sondeo: ¿arranca con ENTRYPOINT python sondeo.py?")
    obligatorio(docker("network", "create", "corrector-e2"))
    obligatorio(docker("run", "-d", "--name", "e2-diana", "--network", "corrector-e2", "nginx:1.27-alpine"))
    esperado = "e2-diana:80 abierto\ne2-diana:22 cerrado\n"
    r = reintentar(lambda: docker("run", "--rm", "--network", "corrector-e2", "corrector-e2", "e2-diana", "80", "22"),
                   lambda r: _igual(r.salida, esperado), 15)
    if not _igual(r.salida, esperado):
        yield (f"con los argumentos e2-diana 80 22, la imagen no imprime lo mismo que python sondeo.py: "
               f"imprime «{_salida(r.salida)}» y debería imprimir «{_salida(esperado)}»")


# --- E3 · Capas, caché y .dockerignore ---------------------------------------------------

E3_SALIDA = "cliente de la API listo (requests 2.32.3)"


def e3(caso: Caso) -> Iterator[str]:
    caso.exigir("Dockerfile", ".dockerignore", "app.py", "requirements.txt")
    partida = p.e3(caso.usuario)
    if not _igual(real := caso.leer("requirements.txt"), partida["requirements.txt"]):
        yield f"has cambiado requirements.txt: {_diferencia(real, partida['requirements.txt'])}"
    if (imagen := _from(caso.leer("Dockerfile"))) != "python:3.12-alpine":
        yield f"has cambiado el FROM: el Dockerfile parte de {imagen or 'ninguna imagen'} y debe seguir en python:3.12-alpine"
    for nombre in (".env", "notas/pendiente.md"):  # .env no se sube: se repone como lo tenía el alumno
        if not (f := caso.carpeta / nombre).exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(partida[nombre], encoding="utf-8")
    _construir(caso, "corrector-e3")
    if (c := _config("corrector-e3")).get("Cmd") != ["python", "app.py"] or c.get("Entrypoint"):
        yield (f"has cambiado el CMD: la imagen arranca con ENTRYPOINT {c.get('Entrypoint')} y CMD {c.get('Cmd')}, "
               "y tiene que seguir siendo CMD [\"python\", \"app.py\"] sin ENTRYPOINT")
    if (salida := docker("run", "--rm", "--network", "none", "corrector-e3").salida).strip() != E3_SALIDA:
        yield f"python app.py no imprime lo mismo que antes: imprime «{_salida(salida)}» y debería imprimir «{E3_SALIDA}»"
    busca = docker("run", "--rm", "--network", "none", "--entrypoint", "find", "corrector-e3",
                   "/", "-xdev", "(", "-name", ".env", "-o", "-name", "pendiente.md", ")")
    if busca.salida.strip():
        yield f".env o notas/ están dentro de la imagen: {', '.join(busca.salida.split())}. Exclúyelos en .dockerignore"
    app = caso.carpeta / "app.py"
    # Un comentario que nunca se ha construido: si fuera siempre el mismo, la caché de BuildKit de una
    # comprobación anterior (otro alumno, o pruebas.py en tu equipo) haría pasar por CACHED un Dockerfile mal ordenado.
    app.write_text(app.read_text(encoding="utf-8") + f"\n# cambio de un comentario, del corrector {secrets.token_hex(8)}\n",
                   encoding="utf-8")
    progreso = _construir(caso, "corrector-e3")
    pasos = re.findall(r"^#(\d+) \[[^\]]*\] RUN .*pip install", progreso, re.MULTILINE)
    if not pasos or not all(re.search(rf"^#{n} CACHED$", progreso, re.MULTILINE) for n in pasos):
        yield ("al cambiar app.py, pip install no sale de la caché: copia requirements.txt e instala antes de "
               "COPY app.py, para que un cambio en app.py no invalide esa capa")


# --- E4 · El secreto de la capa ----------------------------------------------------------

def e4(caso: Caso) -> Iterator[str]:
    caso.exigir("Dockerfile", "hallazgo.txt", ".dockerignore")
    clave = p.e4_clave(caso.usuario)
    hallazgo = caso.leer("hallazgo.txt")
    if clave in hallazgo:
        yield "hallazgo.txt tiene tu clave completa: deja solo oa- y sus 8 primeros caracteres"
    elif clave[:11] not in hallazgo:
        yield "hallazgo.txt no tiene tu clave ocultada: no aparece oa- seguido de sus 8 primeros caracteres"
    if filtrada := sorted(str(f.relative_to(caso.raiz)) for f in caso.raiz.rglob("*")
                          if f.is_file() and clave.encode() in f.read_bytes()):
        yield f"la clave completa está en tu repositorio: {', '.join(filtrada)}. Guárdala fuera de git (api.key está en .gitignore)"
    (caso.carpeta / "api.key").write_text(clave + "\n", encoding="utf-8")  # donde la guardó el alumno
    progreso = _construir(caso, "corrector-e4", "--no-cache", "--secret", f"id=api,src={caso.carpeta / 'api.key'}")
    if "clave de la API válida" not in progreso:
        yield ("la construcción no ejecuta informe.py --comprobar con el secreto: no aparece «clave de la API válida». "
               "Usa RUN --mount=type=secret,id=api")
    if _en_capas(clave.encode(), "corrector-e4"):
        yield ("alguna capa de la imagen resultante contiene la clave: entró con COPY, ARG o ENV. "
               "Solo debe llegar con RUN --mount=type=secret")


def _en_capas(dato: bytes, imagen: str) -> bool:
    """Si dato está en algún fichero de alguna capa, o en la configuración, de la imagen guardada."""
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / "imagen.tar"
        obligatorio(docker("save", "-o", str(destino), imagen))
        with tarfile.open(destino) as guardada:
            for blob in guardada:
                contenido = guardada.extractfile(blob).read() if blob.isfile() else b""
                if dato in contenido:
                    return True
                try:
                    with tarfile.open(fileobj=io.BytesIO(contenido), mode="r:*") as capa:
                        if any(f.isfile() and dato in capa.extractfile(f).read() for f in capa):
                            return True
                except tarfile.TarError:
                    pass  # no es una capa: la configuración o un índice, ya mirados arriba
    return False


# --- E5 · Datos que sobreviven -----------------------------------------------------------

def e5(caso: Caso) -> Iterator[str]:
    caso.exigir("levantar.sh", "consulta.txt", "web/index.html")
    consulta = caso.leer("consulta.txt")
    if f"primer hallazgo de {caso.usuario}" not in consulta.lower():
        yield f"consulta.txt no muestra tu fila: falta «primer hallazgo de {caso.usuario}»"
    elif "(1 row)" not in consulta:
        yield "consulta.txt no muestra tu fila: falta «(1 row)», el pie que pone psql a la consulta"
    levantar.ejecutar(caso.carpeta, {"postgres:16-alpine", "nginx:1.27-alpine"})
    db, web = _en_marcha("e5-db", "e5-web")
    yield from _imagenes({"e5-db": (db, "postgres:16-alpine"), "e5-web": (web, "nginx:1.27-alpine")})
    if not _monta(db, "volume", "e5-datos", "/var/lib/postgresql/data"):
        yield f"los datos de Postgres no están en el volumen e5-datos: en /var/lib/postgresql/data hay {_montado(db, '/var/lib/postgresql/data')}"
    if not _monta(web, "bind", caso.carpeta / "web", "/usr/share/nginx/html", solo_lectura=True):
        yield f"la web no monta ./web en solo lectura en /usr/share/nginx/html: hay {_montado(web, '/usr/share/nginx/html')}"
    pagina = p.e5_pagina(caso.usuario)
    if _puertos(web) != {"80/tcp": [("127.0.0.1", "8085")]}:
        yield f"la web no responde en 127.0.0.1:8085 con tu página: e5-web publica {_publica(web)}"
    elif (codigo := http("http://127.0.0.1:8085/"))[0] != 200:
        yield f"la web no responde en 127.0.0.1:8085 con tu página: responde con el código {codigo[0]}"
    elif not _igual(codigo[1], pagina):
        yield f"la web no responde en 127.0.0.1:8085 con tu página: {_diferencia(codigo[1], pagina)}"


def _imagenes(contenedores: dict[str, tuple[dict, str]]) -> Iterator[str]:
    for nombre, (c, esperada) in contenedores.items():
        if (imagen := c["Config"]["Image"]) != esperada:
            yield f"{nombre} sale de {imagen} y debe salir de {esperada}"


# --- E6 · Red y puertos ------------------------------------------------------------------

def e6(caso: Caso) -> Iterator[str]:
    caso.exigir("levantar.sh", "sondeo.txt")
    if motivo := _sondeo(caso.leer("sondeo.txt"), [("e6-web", "80", "abierto"), ("e6-web", "443", "cerrado"),
                                                   ("e6-datos", "5432", "abierto"), ("e6-datos", "80", "cerrado")]):
        yield f"sondeo.txt no tiene las cuatro líneas, con 80 y 5432 abiertos: {motivo}"
    levantar.ejecutar(caso.carpeta, {"postgres:16-alpine", "nginx:1.27-alpine"})
    web, datos = _en_marcha("e6-web", "e6-datos")
    yield from _imagenes({"e6-web": (web, "nginx:1.27-alpine"), "e6-datos": (datos, "postgres:16-alpine")})
    for nombre, c in (("e6-web", web), ("e6-datos", datos)):
        if "e6-red" not in (redes := c["NetworkSettings"]["Networks"]):
            yield f"{nombre} no está en e6-red: está en {', '.join(redes) or 'ninguna red'}"
    if _puertos(web) != {"80/tcp": [("127.0.0.1", "8086")]}:
        yield f"la web no publica en 127.0.0.1:8086->80/tcp: publica {_publica(web)}"
    if _puertos(datos):
        yield f"la base de datos publica algún puerto ({_publica(datos)}): solo la web tiene que verse desde el equipo"


# --- E7 · Tu primer compose --------------------------------------------------------------

def e7(caso: Caso) -> Iterator[str]:
    caso.exigir("docker-compose.yml", ".env.ejemplo", "web/index.html")
    if (env := caso.carpeta / ".env").exists():
        yield ".env está en el repositorio: solo se sube .env.ejemplo"
        env.unlink()
    proyecto = compose.Proyecto(caso.carpeta)
    if proyecto("config", "-q").codigo == 0:
        yield "docker compose config no falla sin .env: POSTGRES_PASSWORD tiene que ser obligatoria, ${POSTGRES_PASSWORD:?…}"
    clave = secrets.token_hex(12)
    env.write_text(f"POSTGRES_PASSWORD={clave}\n", encoding="utf-8")
    config = proyecto.config()
    if abiertas := compose.puertas(config, caso.raiz):
        raise Fallo(f"el compose abre puertas sobre el equipo: {'; '.join(abiertas)}")
    yield from _e7_tabla(config, caso, clave)
    if (r := proyecto("up", "-d", espera=600)).codigo:
        raise Fallo(f"docker compose up falla: {r.motivo}")
    pagina = reintentar(lambda: proyecto("run", "--rm", "curl", "-s", "http://web/"), lambda r: r.codigo == 0, 20)
    if not _igual(caso.leer("web/index.html"), pagina.salida):
        yield f"con up, curl no recibe tu página: {_diferencia(pagina.salida, caso.leer('web/index.html'))}"
    if (r := proyecto("--profile", "*", "build", "sondeo", espera=600)).codigo:
        raise Fallo(f"sondeo no se construye desde ../e2: {r.motivo}")
    sondeo = reintentar(lambda: proyecto("run", "--rm", "sondeo", "datos", "5432"), lambda r: "abierto" in r.salida, 30)
    if sondeo.salida.strip() != "datos:5432 abierto":
        yield f"con up, el sondeo no ve el 5432 de datos: imprime «{_salida(sondeo.salida)}» en lugar de «datos:5432 abierto»"


def _e7_tabla(config: dict, caso: Caso, clave: str) -> Iterator[str]:
    servicios = config.get("services", {})
    if (nombre := config.get("name")) != "e7-lab":
        raise Fallo(f"el proyecto se llama {nombre} y debe llamarse e7-lab")
    if set(servicios) != {"web", "datos", "sondeo", "curl"}:
        raise Fallo(f"el proyecto tiene los servicios {', '.join(sorted(servicios))} y deben ser exactamente web, datos, sondeo y curl")
    esperado = {
        "web": {"imagen": "nginx:1.27-alpine", "puertos": [("127.0.0.1", "8087", 80)], "perfiles": [],
                "montajes": [("bind", str((caso.carpeta / "web").resolve()), "/usr/share/nginx/html", True)]},
        "datos": {"imagen": "postgres:16-alpine", "puertos": [], "perfiles": [],
                  "montajes": [("volume", "datos", "/var/lib/postgresql/data", False)]},
        "sondeo": {"imagen": "sondeo:1.0", "perfiles": ["herramientas"]},
        "curl": {"imagen": "curlimages/curl:8.11.1", "perfiles": ["herramientas"]},
    }
    for nombre, pide in esperado.items():
        real = compose.resumen(servicios[nombre])
        if mal := [f"{aspecto} es {real[aspecto]} y debe ser {valor}"
                   for aspecto, valor in (pide | {"redes": ["lab"]}).items() if real[aspecto] != valor]:
            yield f"{nombre} no cumple la tabla en: {'; '.join(mal)}"
    if servicios["datos"].get("environment", {}).get("POSTGRES_PASSWORD") != clave:
        yield "POSTGRES_PASSWORD de datos no sale de .env: escríbela como ${POSTGRES_PASSWORD}, sin valor en el compose"
    contexto = (servicios["sondeo"].get("build") or {}).get("context")
    if not contexto or Path(contexto).resolve() != (caso.raiz / p.RAIZ / "e2").resolve():
        yield f"sondeo no se construye desde ../e2: su build apunta a {contexto or 'ninguna carpeta'}"


# --- E8 · Auditar un compose -------------------------------------------------------------

E8_FALLOS = 10  # el compose y el Dockerfile de partida tienen al menos diez; el informe, una fila por fallo
SECRETO = re.compile(r"PASSWORD|SECRET|TOKEN|CLAVE|KEY", re.IGNORECASE)


def e8(caso: Caso) -> Iterator[str]:
    caso.exigir("docker-compose.yml", "panel/Dockerfile", ".env.ejemplo", "informe.md")
    if (env := caso.carpeta / ".env").exists():
        yield ".env está en el repositorio: solo se sube .env.ejemplo"
    if (filas := _filas(caso.leer("informe.md"))) < E8_FALLOS:
        yield f"informe.md tiene {filas} filas y hay al menos {E8_FALLOS} fallos: una fila por fallo"
    yield from _trivy(caso)
    valores = {k: secrets.token_hex(12) for k in re.findall(r"^\s*([A-Za-z_]\w*)\s*=", caso.leer(".env.ejemplo"), re.MULTILINE)}
    env.write_text("".join(f"{k}={v}\n" for k, v in valores.items()), encoding="utf-8")
    proyecto = compose.Proyecto(caso.carpeta)
    config = proyecto.config()
    if abiertas := compose.puertas(config, caso.raiz):
        raise Fallo(f"queda alguna puerta abierta: {'; '.join(abiertas)}")
    servicios = config.get("services", {})
    for nombre, s in servicios.items():
        imagenes = [s["image"]] if "image" in s and "build" not in s else []
        if build := s.get("build"):
            dockerfile = Path(build["context"], build.get("dockerfile", "Dockerfile"))
            imagenes.append(_from(_texto(dockerfile.read_bytes())) if dockerfile.is_file() else None)
        if sueltas := [i or "un Dockerfile sin FROM" for i in imagenes if not (i and _fija(i))]:
            yield f"{nombre}: la imagen no tiene versión fija ({', '.join(sueltas)}): usa una etiqueta concreta, no latest"
        if fuera := [f"{pu.get('host_ip') or '0.0.0.0'}:{pu.get('published')}" for pu in s.get("ports", [])
                     if pu.get("host_ip") != "127.0.0.1"]:
            yield f"{nombre}: publica un puerto fuera de 127.0.0.1 ({', '.join(fuera)})"
        if escritura := [v["source"] for v in s.get("volumes", []) if v["type"] == "bind" and not v.get("read_only")]:
            yield f"{nombre}: monta una carpeta con escritura ({', '.join(escritura)}): añade :ro"
        if escritas := [k for k, v in (s.get("environment") or {}).items() if SECRETO.search(k) and v not in valores.values()]:
            yield f"{nombre}: {', '.join(escritas)} sigue escrita en el compose, no sale de .env"
        if str(s.get("image", "")).startswith("postgres") and s.get("ports"):
            yield f"{nombre}: la base de datos publica un puerto"
    if faltan := {"web", "panel"} - set(servicios):
        raise Fallo(f"faltan los servicios {', '.join(sorted(faltan))}")
    if (r := proyecto("up", "-d", "--build", espera=900)).codigo:
        raise Fallo(f"docker compose up falla: {r.motivo}")
    codigo, cuerpo = http("http://127.0.0.1:8000/")
    if codigo != 200:
        yield f"el panel no arranca en 127.0.0.1:8000: responde con el código {codigo}"
    elif "panel de administración" not in cuerpo:
        yield "el panel no arranca en 127.0.0.1:8000: responde otra página, no la del panel de administración"
    elif proyecto("exec", "-T", "panel", "id", "-u").salida.strip() in ("0", ""):
        yield "el panel corre como root: añade un USER sin privilegios en panel/Dockerfile"
    if (codigo := http("http://127.0.0.1:8088/")[0]) != 200:
        yield f"la web no responde en 127.0.0.1:8088: responde con el código {codigo}"
    elif http("http://127.0.0.1:8088/docker-compose.yml")[0] == 200:
        yield "la web sigue sirviendo docker-compose.yml: monta solo la carpeta de la web, no la del proyecto"


def _fija(imagen: str) -> bool:
    nombre = imagen.rsplit("/", 1)[-1]
    return "@sha256:" in imagen or (":" in nombre and not nombre.endswith(":latest"))


def _filas(markdown: str) -> int:
    """Filas de datos de las tablas de un markdown: sin cabeceras ni separadores."""
    filas = [l.strip() for l in markdown.split("\n") if l.strip().startswith("|")]
    separadores = [i for i, l in enumerate(filas) if re.fullmatch(r"\|[\s:|-]+\|?", l)]
    return len(filas) - 2 * len(separadores)  # cada tabla: una cabecera y su separador


def _trivy(caso: Caso) -> Iterator[str]:
    r = docker("run", "--rm", "-v", f"{caso.carpeta}:/work:ro", "aquasec/trivy:0.58.0", "config", "--quiet",
               "--severity", "HIGH,CRITICAL", "--format", "json", "/work", espera=600)
    resultado = json.loads(obligatorio(r).salida)
    if avisos := sorted({m["ID"] for res in resultado.get("Results") or [] for m in res.get("Misconfigurations") or []
                         if m.get("Status") == "FAIL"}):
        yield f"Trivy da avisos altos o críticos: {', '.join(avisos)}. Míralos con trivy config ."


COMPROBACIONES: dict[str, Comprobacion] = {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e6": e6, "e7": e7, "e8": e8}
