"""Comprobaciones públicas de cada ejercicio del RA1, en el orden de «El corrector marca fallo si» de cada enunciado.

Cada una recibe el caso (una copia del repositorio del alumno) y produce sus fallos uno a uno; lanza Fallo
cuando lo entregado no permite seguir. Lo esperado sale del escenario de cada alumno en preparar.py. Nada
depende de webs externas. Las respuestas con clave (figuras, tipos de fallo, CWE, CVE, técnicas…) las
compara el corrector, que guarda la clave en el repositorio privado del docente.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator

import preparar as p

from .base import Caso, Fallo, normal, palabras, tabla, vacio

Comprobacion = Callable[[Caso], Iterator[str]]

FIGURAS = {"hacking etico", "hacktivismo", "ciberdelito"}
ARTICULOS = {"ninguno", "197 bis", "197 ter", "264", "264 bis"}
TIPOS_FALLO = {"no", "autorizacion", "objetivos", "fechas", "tecnicas", "datos", "terceros"}
PROPIEDADES = {"confidencialidad", "integridad", "disponibilidad", "autenticidad"}
CAJAS = {"caja negra", "caja gris", "caja blanca"}
PROHIBIDO = {"denegacion de servicio", "ingenieria social", "modificar datos", "borrar datos", "escaneo", "explotacion"}

# Herramientas que se aceptan en cada familia (en minúsculas y sin tildes; basta con que aparezcan en el nombre).
# Es la misma tabla que «Herramientas por familia» en el tema 4.1.
CATALOGO: dict[str, tuple[str, ...]] = {
    "antivirus/edr": ("defender", "crowdstrike", "falcon", "sentinelone", "wazuh", "eset", "sophos", "bitdefender",
                      "trend micro"),
    "cortafuegos": ("pfsense", "opnsense", "fortigate", "fortinet", "firewall de windows", "windows defender firewall",
                    "grupos de seguridad", "security group", "aws waf", "palo alto", "ufw"),
    "escaner de red": ("nmap", "masscan", "angry ip"),
    "escaner de vulnerabilidades": ("openvas", "greenbone", "nessus", "qualys", "nuclei", "inspector"),
    "ids/ips": ("suricata", "snort", "zeek"),
    "siem": ("wazuh", "elastic", "splunk", "sentinel", "graylog", "qradar", "security onion"),
    "registro de la nube": ("cloudtrail", "guardduty", "security hub", "auditoria de microsoft 365", "purview",
                            "azure monitor", "defender for cloud"),
    "analizador de codigo": ("trivy", "semgrep", "sonarqube", "checkov", "dependabot", "codeql", "snyk"),
    "soc gestionado": (),  # cualquier proveedor
}

DARKNETS = {
    "programa": {"tor browser", "router i2p", "cliente de zeronet", "nodo de hyphanet"},
    "direcciones": {".onion", ".i2p", "direccion bitcoin o .bit", "claves usk@, ssk@ o chk@"},
    "como funciona": {"enrutamiento cebolla", "enrutamiento ajo", "p2p con bittorrent", "almacen distribuido"},
}


def _filas(filas: list[dict[str, str]], columna: str, ids: list[str], fichero: str) -> dict[str, dict[str, str]]:
    """Las filas por su identificador (primera columna), exigiendo que estén todas y una sola vez."""
    por_id: dict[str, dict[str, str]] = {}
    for f in filas:
        clave = normal(f[columna])
        if clave in por_id:
            raise Fallo(f"{fichero}: la fila {f[columna]} está repetida")
        por_id[clave] = f
    if faltan := [i for i in ids if normal(i) not in por_id]:
        raise Fallo(f"{fichero}: faltan las filas {', '.join(faltan)}; no borres ni cambies filas de la plantilla")
    if sobran := [f[columna] for k, f in por_id.items() if k not in {normal(i) for i in ids}]:
        raise Fallo(f"{fichero}: sobran las filas {', '.join(sobran)}")
    return {normal(i): por_id[normal(i)] for i in ids}


def _json(c: Caso, nombre: str) -> dict:
    try:
        datos = json.loads(c.leer(nombre))
    except json.JSONDecodeError as e:
        raise Fallo(f"{nombre} no es JSON válido (línea {e.lineno}): {e.msg}")
    if not isinstance(datos, dict):
        raise Fallo(f"{nombre} tiene que ser un objeto JSON, como la plantilla")
    return datos


def _texto(valor: object) -> str:
    return valor.strip() if isinstance(valor, str) else ""


# --- U1 · Qué es el hacking ético -------------------------------------------------------------

def u1_e1(c: Caso) -> Iterator[str]:
    fichero = "casos.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Caso", "Figura", "Artículo"), "caso",
                   p.u1_e1_casos(c.usuario), fichero)
    for n, f in filas.items():
        figura, articulo = normal(f["figura"]), normal(f["articulo"])
        if not (figura or articulo):
            yield f"{n.upper()}: sin rellenar"
            continue
        if figura not in FIGURAS:
            yield f"{n.upper()}: «{f['figura']}» no es una de las figuras de la lista"
        if articulo not in ARTICULOS:
            yield f"{n.upper()}: «{f['articulo']}» no es uno de los artículos de la lista"
        elif figura == "hacking etico" and articulo != "ninguno":
            yield f"{n.upper()}: si es hacking ético no hay artículo que aplicar"


def security_txt(texto: str) -> dict[str, list[str]]:
    campos: dict[str, list[str]] = {}
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if ":" not in linea:
            raise Fallo(f"security.txt: «{linea[:40]}» no es una línea Campo: valor")
        nombre, valor = linea.split(":", 1)
        campos.setdefault(nombre.strip().lower(), []).append(valor.strip())
    return campos


def u1_e2(c: Caso) -> Iterator[str]:
    d = p.u1_e2_datos(c.usuario)
    campos = security_txt(c.leer("web/.well-known/security.txt"))
    for campo, esperado in (("contact", d["contacto"]), ("policy", d["politica"]), ("canonical", d["canonica"])):
        valores = campos.get(campo, [])
        if esperado not in valores:
            yield f"security.txt: falta {campo.capitalize()}: {esperado}"
    if "es" not in [x.strip().lower() for v in campos.get("preferred-languages", []) for x in v.split(",")]:
        yield "security.txt: falta Preferred-Languages con es"
    expira = campos.get("expires", [])
    if len(expira) != 1:
        yield "security.txt: tiene que haber un solo Expires (RFC 9116)"
    else:
        try:
            fecha = datetime.fromisoformat(expira[0].replace("Z", "+00:00").replace("z", "+00:00"))
        except ValueError:
            fecha = None
        ahora = datetime.now(timezone.utc)
        if fecha is None or fecha.tzinfo is None:
            yield "security.txt: Expires va en formato RFC 3339 con zona, como 2027-10-31T23:59:59Z"
        elif not ahora < fecha <= ahora + timedelta(days=366):
            yield "security.txt: Expires tiene que ser una fecha futura de dentro de menos de un año"
    if conocidos := set(campos) - {"contact", "expires", "encryption", "acknowledgments", "preferred-languages",
                                   "canonical", "policy", "hiring", "csaf"}:
        yield f"security.txt: campos que no son de RFC 9116: {', '.join(sorted(conocidos))}"


# --- U2 · Permisos y alcance ------------------------------------------------------------------

def _en_alcance():
    ruta = p.plantilla("u2-e1") / "en_alcance.py"
    spec = importlib.util.spec_from_file_location("en_alcance", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.permitido


def u2_e1_pruebas(usuario: str) -> list[tuple[str, str, bool, str]]:
    """Las preguntas del corrector: dirección, momento, respuesta esperada y qué se pregunta."""
    e = p.u2_e1_encargo(usuario)
    red = ipaddress.ip_network(e["red"])
    inicio, fin = datetime.fromisoformat(e["inicio"]), datetime.fromisoformat(e["fin"])
    h_desde = e["desde"]
    noche = lambda dia, hora: (dia.replace(hour=int(hora[:2]), minute=int(hora[3:]))).strftime("%Y-%m-%d %H:%M")  # noqa: E731
    madrugada = lambda dia: (dia + timedelta(days=1)).replace(hour=3).strftime("%Y-%m-%d %H:%M")  # noqa: E731
    otro_equipo = str(red.network_address + 37)
    return [
        (e["web"], noche(inicio, h_desde), True, "la web la primera noche"),
        (e["citas"], madrugada(inicio + timedelta(days=2)), True, "el portal de citas de madrugada"),
        (otro_equipo, noche(inicio + timedelta(days=5), "23:30"), True, "un equipo de la red de la consulta"),
        (e["datafono"], noche(inicio + timedelta(days=5), "23:30"), False, "el datáfono"),
        (e["otra"], noche(inicio + timedelta(days=5), "23:30"), False, "una dirección que no es de la clínica"),
        (e["web"], (inicio + timedelta(days=3)).replace(hour=12).strftime("%Y-%m-%d %H:%M"), False, "la web a mediodía"),
        (e["web"], noche(inicio - timedelta(days=1), "23:30"), False, "la noche antes de empezar"),
        (e["web"], madrugada(fin), True, "la madrugada de la última noche"),
        (e["web"], noche(fin + timedelta(days=1), "23:30"), False, "la noche después de terminar"),
    ]


def u2_e1(c: Caso) -> Iterator[str]:
    a = _json(c, "alcance.json")
    for campo in ("cliente", "autoriza", "tipo", "inicio", "fin"):
        if not _texto(a.get(campo)):
            yield f"alcance.json: falta {campo}"
    if normal(_texto(a.get("tipo"))) not in CAJAS:
        yield "alcance.json: tipo es caja negra, caja gris o caja blanca"
    for campo in ("dentro", "fuera", "prohibido"):
        if not isinstance(a.get(campo), list) or not a[campo] or not all(isinstance(x, str) for x in a[campo]):
            raise Fallo(f"alcance.json: {campo} tiene que ser una lista de textos, no vacía")
    for x in a["dentro"] + a["fuera"]:
        try:
            ipaddress.ip_network(x.strip(), strict=False)
        except ValueError:
            raise Fallo(f"alcance.json: «{x}» no es una dirección IP ni una red (como 10.0.0.0/24)")
    if malos := [x for x in a["prohibido"] if normal(x) not in PROHIBIDO]:
        yield f"alcance.json: en prohibido van valores de la lista del enunciado; sobran {', '.join(malos)}"
    for campo, formato in (("inicio", "%Y-%m-%d"), ("fin", "%Y-%m-%d")):
        try:
            datetime.strptime(_texto(a.get(campo)), formato)
        except ValueError:
            raise Fallo(f"alcance.json: {campo} va como aaaa-mm-dd")
    horario = a.get("horario") or {}
    try:
        for k in ("desde", "hasta"):
            datetime.strptime(_texto(horario.get(k)), "%H:%M")
    except ValueError:
        raise Fallo("alcance.json: horario.desde y horario.hasta van como hh:mm")
    emergencia = a.get("emergencia") or {}
    if not (_texto(emergencia.get("nombre")) and _texto(emergencia.get("telefono"))):
        yield "alcance.json: falta el nombre o el teléfono de emergencia"
    permitido = _en_alcance()
    mal = [que for ip, momento, esperado, que in u2_e1_pruebas(c.usuario)
           if permitido(a, ip, datetime.fromisoformat(momento)) != esperado]
    if mal:
        yield f"con tu alcance.json, {len(mal)} de {len(u2_e1_pruebas(c.usuario))} preguntas del corrector salen mal; por ejemplo, {mal[0]}"


def u2_e2(c: Caso) -> Iterator[str]:
    fichero = "fallos.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Cláusula", "Fallo"), "clausula",
                   [f"C{n}" for n in range(1, 13)], fichero)
    tipos = []
    for n, f in filas.items():
        valor = normal(f["fallo"])
        if valor not in TIPOS_FALLO:
            yield f"{n.upper()}: en Fallo va «no» o un tipo de la lista"
        elif valor != "no":
            tipos.append(valor)
    if len(tipos) != 6:
        yield f"hay seis cláusulas con fallo y has marcado {len(tipos)}"
    elif len(set(tipos)) != 6:
        yield "cada uno de los seis fallos es de un tipo distinto"


# --- U3 · Vulnerabilidades y ataques ----------------------------------------------------------

def u3_e1(c: Caso) -> Iterator[str]:
    fichero = "ranking.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Reto", "CWE", "Propiedad"), "reto",
                   [str(n) for n in range(1, 7)], fichero)
    for n, f in filas.items():
        if not re.fullmatch(r"cwe-\d+", normal(f["cwe"])):
            yield f"reto {n}: el CWE va como CWE-123"
        if normal(f["propiedad"]) not in PROPIEDADES:
            yield f"reto {n}: la propiedad es confidencialidad, integridad, disponibilidad o autenticidad"


def u3_e2(c: Caso) -> Iterator[str]:
    f = _json(c, "ficha.json")
    if _texto(f.get("cve")) != p.u3_e2_cve(c.usuario):
        raise Fallo(f"ficha.json: tu CVE es {p.u3_e2_cve(c.usuario)}; no lo cambies")
    for campo in ("producto", "versiones_afectadas", "version_corregida", "defensa"):
        if not _texto(f.get(campo)):
            yield f"ficha.json: falta {campo}"
    if not re.fullmatch(r"CWE-\d+", _texto(f.get("cwe"))):
        yield "ficha.json: cwe va como CWE-123"
    cvss = f.get("cvss") or {}
    if _texto(cvss.get("version")) != "3.1":
        yield "ficha.json: cvss.version es 3.1: usa la nota de CVSS 3.1 de NVD"
    if not isinstance(cvss.get("nota"), (int, float)) or not 0 < cvss["nota"] <= 10:
        yield "ficha.json: cvss.nota es un número entre 0 y 10, sin comillas"
    if not _texto(cvss.get("vector")).startswith("CVSS:3.1/"):
        yield "ficha.json: cvss.vector es la cadena completa, empezando por CVSS:3.1/"
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", _texto(f.get("fecha_kev"))):
        yield "ficha.json: fecha_kev va como aaaa-mm-dd"
    props = f.get("propiedades")
    if not isinstance(props, list) or not props or not all(normal(str(x)) in PROPIEDADES for x in props):
        yield "ficha.json: propiedades es una lista con una o varias de las cuatro propiedades"
    fuentes = f.get("fuentes")
    if not isinstance(fuentes, list) or not any("nvd.nist.gov" in str(x) or "cve.org" in str(x) for x in fuentes):
        yield "ficha.json: en fuentes falta la ficha oficial (nvd.nist.gov o cve.org)"
    if palabras(_texto(f.get("defensa"))) < 6:
        yield "ficha.json: en defensa separa lo que corrige el fallo de lo que solo reduce el riesgo"


def u3_e3(c: Caso) -> Iterator[str]:
    r = _json(c, "respuestas.json")
    inc = p.u3_e3_incidente(c.usuario)
    esperado = {"ip_atacante": inc["atacante"], "intentos_fallidos": inc["fallidos"], "primer_acceso": inc["acceso"],
                "cuenta_usada": inc["victima"], "cuenta_creada": inc["creado"], "servicio_instalado": inc["servicio"],
                "registro_borrado": inc["borrado"]}
    for campo, valor in esperado.items():
        dado = r.get(campo)
        if isinstance(valor, int):
            if dado != valor:
                yield f"respuestas.json: {campo} no coincide con el registro (es un número, sin comillas)"
        elif normal(str(dado or "")) != normal(valor):
            yield f"respuestas.json: {campo} no coincide con el registro"
    tecnicas = r.get("tecnicas") or {}
    for evento in ("5152", "4625", "4720", "7045", "1102"):
        if not re.fullmatch(r"T\d{4}(\.\d{3})?", _texto(tecnicas.get(evento)).upper()):
            yield f"respuestas.json: la técnica del evento {evento} va como T1234 o T1234.001"


# --- U4 · Herramientas y monitorización -------------------------------------------------------

def u4_e1(c: Caso) -> Iterator[str]:
    fichero = "herramientas.md"
    filas = [f for f in tabla(c.leer(fichero), fichero, "Organización", "Familia", "Herramienta", "Por qué")
             if not vacio(f["organizacion"])]
    por_org: dict[str, int] = {}
    for f in filas:
        org, familia, herramienta = normal(f["organizacion"]), normal(f["familia"]), normal(f["herramienta"])
        if not (familia or herramienta):
            continue
        if org not in ("a", "b", "c"):
            yield f"«{f['organizacion']}» no es A, B o C"
            continue
        por_org[org] = por_org.get(org, 0) + 1
        if familia not in CATALOGO:
            yield f"{org.upper()}: «{f['familia']}» no es una familia de la tabla del tema"
        elif CATALOGO[familia] and not any(x in herramienta for x in CATALOGO[familia]):
            yield f"{org.upper()}: «{f['herramienta']}» no es una herramienta de la familia {familia}"
        if palabras(f["por que"]) < 5:
            yield f"{org.upper()}: justifica «{f['herramienta']}» pensando en esa organización"
    for org in ("a", "b", "c"):
        if por_org.get(org, 0) < 3:
            yield f"la organización {org.upper()} necesita al menos tres herramientas"


def u4_e2(c: Caso) -> Iterator[str]:
    from . import suricata

    reglas = c.leer("suricata/local.rules")
    sids = [int(x) for x in re.findall(r"\bsid\s*:\s*(\d+)", reglas)]
    if any(s not in sids for s in range(1000001, 1000007)):
        yield "suricata/local.rules: no borres las reglas de la plantilla (sid 1000001 a 1000006)"
    if not any(s >= 1000100 for s in sids):
        raise Fallo("suricata/local.rules: falta tu regla, con sid desde 1000100")
    alertas = c.leer("alertas.txt")
    if "FASE" not in alertas or "ORIGEN" not in alertas:
        yield "alertas.txt no es la salida de etiquetar.py"
    yield from suricata.comprobar(reglas, c.usuario)


def u4_e3(c: Caso) -> Iterator[str]:
    fichero = "darknets.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Red", "Programa", "Direcciones", "Cómo funciona"), "red",
                   ["Tor", "I2P", "ZeroNet", "Freenet"], fichero)
    for red_, f in filas.items():
        for columna, permitidos in DARKNETS.items():
            if normal(f[columna]) not in permitidos:
                yield f"{red_}: «{f[columna]}» no es uno de los valores de la lista de {columna}"


COMPROBACIONES: dict[str, Comprobacion] = {
    "u1-e1": u1_e1, "u1-e2": u1_e2, "u2-e1": u2_e1, "u2-e2": u2_e2, "u3-e1": u3_e1,
    "u3-e2": u3_e2, "u3-e3": u3_e3, "u4-e1": u4_e1, "u4-e2": u4_e2, "u4-e3": u4_e3,
}
CON_DOCKER = {"u4-e2"}
