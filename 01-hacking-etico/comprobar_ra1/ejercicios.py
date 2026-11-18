"""Comprobaciones públicas de cada ejercicio del RA1, en el orden de «El corrector marca fallo si» de cada enunciado.

Cada una recibe el caso (una copia del repositorio del alumno) y produce sus fallos uno a uno; lanza Fallo
cuando lo entregado no permite seguir. Las respuestas con clave no se comprueban aquí: lo hace el corrector.
"""

from __future__ import annotations

import re
from typing import Callable, Iterator

from . import red
from .base import Caso, Fallo, campos, fecha, normal, palabras, tabla, vacio

Comprobacion = Callable[[Caso], Iterator[str]]

FIGURAS = {"hacking etico", "hacktivismo", "ciberdelito"}
ARTICULOS = {"ninguno", "197 bis", "197 ter", "264", "264 bis"}
SI_NO = {"si", "no"}
PROPIEDADES = {"confidencialidad", "integridad", "disponibilidad", "autenticidad"}
TIPOS = {"diseno", "configuracion", "software", "humana"}
FASES = {"reconocimiento", "escaneo", "obtener acceso", "mantener acceso", "borrar huellas"}
CAJAS = {"caja negra", "caja gris", "caja blanca"}

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
    "soc gestionado": (),  # cualquier proveedor: se valora el porqué
}

DARKNETS = {
    "programa": {"tor browser", "router i2p", "cliente de zeronet", "nodo de hyphanet"},
    "direcciones": {".onion", ".i2p", "direccion bitcoin o .bit", "claves usk@, ssk@ o chk@"},
    "como funciona": {"enrutamiento cebolla", "enrutamiento ajo", "p2p con bittorrent", "almacen distribuido"},
}
REDES = ("tor", "i2p", "zeronet", "freenet")


def _filas(filas: list[dict[str, str]], columna: str, ids: list[str], fichero: str) -> dict[str, dict[str, str]]:
    """Las filas por su identificador (primera columna), exigiendo que estén todas y una sola vez."""
    por_id: dict[str, dict[str, str]] = {}
    for f in filas:
        clave = normal(f[columna])
        if clave in por_id:
            raise Fallo(f"{fichero}: la fila {f[columna]} está repetida")
        por_id[clave] = f
    if faltan := [i for i in ids if normal(i) not in por_id]:
        raise Fallo(f"{fichero}: faltan las filas {', '.join(faltan)}; no borres filas de la plantilla")
    return {normal(i): por_id[normal(i)] for i in ids}


def _de(valor: str, permitidos: set[str]) -> bool:
    return normal(valor) in permitidos


# --- U1 · Qué es el hacking ético -------------------------------------------------------------

def u1_e1(c: Caso) -> Iterator[str]:
    fichero = "casos.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Caso", "Figura", "Delito", "Artículo", "Por qué"),
                   "caso", [str(n) for n in range(1, 11)], fichero)
    for n, f in filas.items():
        figura, delito, articulo = normal(f["figura"]), normal(f["delito"]), normal(f["articulo"])
        if not (figura or delito or articulo):
            yield f"caso {n}: sin rellenar"
            continue
        if figura not in FIGURAS:
            yield f"caso {n}: «{f['figura']}» no es una de las figuras de la lista"
        if delito not in SI_NO:
            yield f"caso {n}: en Delito va sí o no"
        if articulo not in ARTICULOS:
            yield f"caso {n}: «{f['articulo']}» no es uno de los artículos de la lista"
        if figura == "hacking etico" and (delito == "si" or articulo != "ninguno"):
            yield f"caso {n}: si es hacking ético no es delito ni tiene artículo"
        if delito == "si" and articulo == "ninguno" or delito == "no" and articulo not in ("ninguno", ""):
            yield f"caso {n}: el artículo no cuadra con la columna Delito"
        if palabras(f["por que"]) < 4:
            yield f"caso {n}: falta el porqué (una frase tuya)"


def u1_e2(c: Caso) -> Iterator[str]:
    fichero = "seguridad.md"
    texto = c.leer(fichero)
    filas = [f for f in tabla(texto, fichero, "Dominio", "Contact", "Expires", "Policy") if not vacio(f["dominio"])]
    dominios = [normal(f["dominio"]).removeprefix("https://").removeprefix("www.").strip("/") for f in filas]
    if len(set(dominios)) < 3:
        yield "hacen falta tres dominios distintos en la tabla de security.txt"
    for f, dominio in zip(filas, dominios):
        if not re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", dominio):
            yield f"«{f['dominio']}» no es un dominio: escribe solo el nombre, como github.com"
            continue
        datos = red.security_txt(dominio) or red.security_txt("www." + dominio)
        if datos is None:
            yield f"{dominio} no tiene security.txt (o no se ha podido descargar): elige otro dominio"
            continue
        contactos = {normal(x).removeprefix("mailto:").rstrip("/") for x in datos["contact"]}
        if normal(f["contact"]).removeprefix("mailto:").rstrip("/") not in contactos:
            yield f"{dominio}: el Contact no coincide con ninguno de su security.txt; si el fichero ha cambiado, actualízalo"
        if not re.match(r"\d{4}-\d{2}-\d{2}", f["expires"].strip()) and not (normal(f["expires"]) == "no tiene" and "expires" not in datos):
            yield f"{dominio}: en Expires va la fecha tal como aparece (empieza por aaaa-mm-dd)"
        politicas = {normal(x).rstrip("/") for x in datos.get("policy", [])}
        politica = normal(f["policy"]).rstrip("/")
        if (politicas and politica not in politicas) or (not politicas and politica != "no tiene"):
            yield f"{dominio}: Policy no coincide con su security.txt (si no tiene, escribe «no tiene»)"
    programas = [f for f in tabla(texto, fichero, "Programa", "Enlace", "Permite", "Prohíbe") if not vacio(f["programa"])]
    if not programas:
        yield "falta el programa de recompensas en la segunda tabla"
    for f in programas:
        if not f["enlace"].strip().startswith("https://"):
            yield f"{f['programa']}: el enlace tiene que empezar por https://"
        if palabras(f["permite"]) < 4 or palabras(f["prohibe"]) < 4:
            yield f"{f['programa']}: resume con tus palabras qué permite y qué prohíbe"


# --- U2 · Permisos y alcance ------------------------------------------------------------------

ALCANCE = ("Cliente", "Autoriza", "Dentro del alcance", "Fuera del alcance", "Tipo de prueba", "Permitido",
           "Prohibido", "Inicio", "Fin", "Horario", "Contacto de emergencia", "Entregable", "Datos personales")


def u2_e1(c: Caso) -> Iterator[str]:
    fichero = "alcance.md"
    valores = campos(c.leer(fichero), fichero)
    if faltan := [x for x in ALCANCE if normal(x) not in valores]:
        raise Fallo(f"{fichero}: faltan los campos {', '.join(faltan)}; no cambies la primera columna")
    for x in ALCANCE:
        if vacio(valores[normal(x)]):
            yield f"{fichero}: el campo {x} está vacío"
    inicio, fin = fecha(valores[normal("Inicio")]), fecha(valores[normal("Fin")])
    if not inicio or not fin:
        yield f"{fichero}: Inicio y Fin van como dd/mm/aaaa"
    elif fin < inicio:
        yield f"{fichero}: la fecha de fin es anterior a la de inicio"
    if not _de(valores[normal("Tipo de prueba")], CAJAS):
        yield f"{fichero}: en Tipo de prueba va caja negra, caja gris o caja blanca"


def u2_e2(c: Caso) -> Iterator[str]:
    fichero = "fallos.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Cláusula", "Fallo", "Por qué"), "clausula",
                   [f"C{n}" for n in range(1, 13)], fichero)
    marcadas = 0
    for n, f in filas.items():
        if not _de(f["fallo"], SI_NO):
            yield f"{n.upper()}: en Fallo va sí o no"
        elif normal(f["fallo"]) == "si":
            marcadas += 1
            if palabras(f["por que"]) < 4:
                yield f"{n.upper()}: explica el riesgo de esa cláusula"
    if marcadas != 6:
        yield f"hay seis cláusulas con fallo y has marcado {marcadas}"


# --- U3 · Vulnerabilidades y ataques ----------------------------------------------------------

def u3_e1(c: Caso) -> Iterator[str]:
    fichero = "ranking.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Reto", "CWE", "Propiedad", "Tipo", "Corrección"), "reto",
                   [str(n) for n in range(1, 7)], fichero)
    for n, f in filas.items():
        if not (f["cwe"] or f["propiedad"] or f["tipo"]):
            yield f"reto {n}: sin rellenar"
            continue
        if not re.fullmatch(r"cwe-\d+", normal(f["cwe"])):
            yield f"reto {n}: el CWE va como CWE-123"
        if not _de(f["propiedad"], PROPIEDADES):
            yield f"reto {n}: la propiedad es confidencialidad, integridad, disponibilidad o autenticidad"
        if not _de(f["tipo"], TIPOS):
            yield f"reto {n}: el tipo es diseño, configuración, software o humana"
        if palabras(f["correccion"]) < 4:
            yield f"reto {n}: falta cómo se corrige"


FICHA = ("CVE", "Producto", "Tipo", "CWE", "Nota CVSS", "Versión CVSS", "Vector CVSS", "Fecha en KEV",
         "Versiones afectadas", "Versión corregida", "Propiedades", "Explotación", "Defensa", "Fuentes")
EJEMPLOS = {"CVE-2026-109618", "CVE-2026-109619"}


def u3_e2(c: Caso) -> Iterator[str]:
    fichero = "ficha.md"
    valores = campos(c.leer(fichero), fichero)
    if faltan := [x for x in FICHA if normal(x) not in valores]:
        raise Fallo(f"{fichero}: faltan los campos {', '.join(faltan)}; no cambies la primera columna")
    v = {x: valores[normal(x)].strip() for x in FICHA}
    for x in FICHA:
        if vacio(v[x]):
            yield f"{fichero}: el campo {x} está vacío"
    cve = v["CVE"].upper()
    if not re.fullmatch(r"CVE-\d{4}-\d{4,}", cve):
        raise Fallo(f"{fichero}: el CVE va como CVE-2024-1234")
    if cve in EJEMPLOS:
        raise Fallo("PHP2Shell es el ejemplo resuelto: elige otro CVE del catálogo KEV")
    entrada = red.kev().get(cve)
    if entrada is None:
        raise Fallo(f"{cve} no está en el catálogo CISA KEV: elige uno que sí esté")
    if v["Fecha en KEV"] != entrada["dateAdded"]:
        yield f"Fecha en KEV: no coincide con la del catálogo (formato aaaa-mm-dd)"
    producto = normal(v["Producto"])
    if normal(entrada["product"]) not in producto and normal(entrada["vendorProject"]) not in producto:
        yield "Producto: no coincide con el fabricante ni con el producto del catálogo"
    ficha = red.nvd(cve)
    if ficha is None:
        raise Fallo(f"NVD no tiene {cve} todavía: elige otro CVE")
    conocidos = red.cwes(ficha) | {x.upper() for x in entrada.get("cwes") or []}
    if v["CWE"].upper() not in conocidos:
        yield f"CWE: {v['CWE']} no es el que dan NVD o CISA para {cve}" if conocidos else "CWE: no coincide"
    notas = red.notas(ficha)
    if not notas:
        raise Fallo(f"NVD aún no ha puesto nota CVSS a {cve}: elige otro CVE")
    try:
        nota = float(v["Nota CVSS"].replace(",", "."))
    except ValueError:
        nota = -1.0
    version = v["Versión CVSS"].removeprefix("CVSS").removeprefix("cvss").strip()
    iguales = [n for n in notas if n["nota"] == nota and n["version"] == version]
    if not iguales:
        yield "Nota CVSS y Versión CVSS: no coinciden con ninguna de las notas que da NVD"
    elif not any(normal(n["vector"]) == normal(v["Vector CVSS"]) for n in iguales):
        yield "Vector CVSS: no coincide con el de esa nota en NVD"
    if not _de(v["Tipo"], TIPOS):
        yield "Tipo: es diseño, configuración, software o humana"
    propiedades = {x for x in re.split(r"\s*(?:,|;|\by\b)\s*", normal(v["Propiedades"])) if x}
    if not propiedades or not propiedades <= PROPIEDADES:
        yield "Propiedades: una o varias de confidencialidad, integridad, disponibilidad y autenticidad, separadas por comas"
    if "nvd.nist.gov" not in v["Fuentes"] and "cve.org" not in v["Fuentes"]:
        yield "Fuentes: falta la ficha oficial (nvd.nist.gov o cve.org)"
    if palabras(v["Defensa"]) < 6:
        yield "Defensa: separa lo que corrige el fallo de lo que solo reduce el riesgo"


def u3_e3(c: Caso) -> Iterator[str]:
    fichero = "incidente.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Paso", "Fase", "Técnica", "Por qué"), "paso",
                   [f"P{n}" for n in range(1, 8)], fichero)
    for n, f in filas.items():
        if not (f["fase"] or f["tecnica"]):
            yield f"{n.upper()}: sin rellenar"
            continue
        if not _de(f["fase"], FASES):
            yield f"{n.upper()}: la fase es una de las cinco del tema"
        if not re.fullmatch(r"T\d{4}(\.\d{3})?", f["tecnica"].strip().upper()):
            yield f"{n.upper()}: la técnica va como T1234 o T1234.001"
        if palabras(f["por que"]) < 4:
            yield f"{n.upper()}: falta el porqué"


# --- U4 · Herramientas y monitorización -------------------------------------------------------

def u4_e1(c: Caso) -> Iterator[str]:
    fichero = "herramientas.md"
    filas = [f for f in tabla(c.leer(fichero), fichero, "Organización", "Familia", "Herramienta", "Por qué")
             if not vacio(f["organizacion"])]
    por_org: dict[str, int] = {}
    for f in filas:
        org, familia, herramienta = normal(f["organizacion"]), normal(f["familia"]), normal(f["herramienta"])
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
    yield from suricata.comprobar(reglas)


def u4_e3(c: Caso) -> Iterator[str]:
    fichero = "darknets.md"
    filas = _filas(tabla(c.leer(fichero), fichero, "Red", "Programa", "Direcciones", "Cómo funciona"), "red",
                   ["Tor", "I2P", "ZeroNet", "Freenet"], fichero)
    for red_, f in filas.items():
        for columna, permitidos in DARKNETS.items():
            if not _de(f[columna], permitidos):
                yield f"{red_}: «{f[columna]}» no es uno de los valores de la lista de {columna}"


COMPROBACIONES: dict[str, Comprobacion] = {
    "u1-e1": u1_e1, "u1-e2": u1_e2, "u2-e1": u2_e1, "u2-e2": u2_e2, "u3-e1": u3_e1,
    "u3-e2": u3_e2, "u3-e3": u3_e3, "u4-e1": u4_e1, "u4-e2": u4_e2, "u4-e3": u4_e3,
}
CON_DOCKER = {"u4-e2"}
