"""Consultas a fuentes públicas: security.txt de una web, el catálogo CISA KEV y la ficha de NVD de un CVE."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from functools import lru_cache

from .base import Fallo

AGENTE = "comprobaciones-hacking-etico/1.0"
KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={}"


def descargar(url: str, intentos: int = 3) -> bytes:
    """El cuerpo de la respuesta; reintenta si el servidor limita (403, 429, 503) o no responde."""
    ultimo: Exception | None = None
    for intento in range(intentos):
        try:
            peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(peticion, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 500, 502, 503, 504):
                raise
            ultimo = e
        except (urllib.error.URLError, TimeoutError) as e:
            ultimo = e
        time.sleep(6 * (intento + 1))  # NVD sin clave admite 5 peticiones cada 30 s
    raise Fallo(f"no se ha podido consultar {url} ({ultimo}); vuelve a probar en un rato")


def security_txt(dominio: str) -> dict[str, list[str]] | None:
    """Los campos del security.txt del dominio (en minúsculas), o None si no tiene."""
    for ruta in ("/.well-known/security.txt", "/security.txt"):
        try:
            texto = descargar(f"https://{dominio}{ruta}", intentos=2).decode("utf-8", "replace")
        except urllib.error.HTTPError:
            continue
        except Fallo:
            return None
        campos: dict[str, list[str]] = {}
        for linea in texto.splitlines():
            linea = linea.strip()
            if linea.startswith("#") or ":" not in linea or linea.startswith("-----"):
                continue
            nombre, valor = linea.split(":", 1)
            if nombre.strip() and " " not in nombre.strip():
                campos.setdefault(nombre.strip().lower(), []).append(valor.strip())
        if "contact" in campos:
            return campos
    return None


@lru_cache(maxsize=1)
def kev() -> dict[str, dict]:
    """El catálogo de vulnerabilidades explotadas de CISA, por CVE."""
    datos = json.loads(descargar(KEV))
    return {v["cveID"].upper(): v for v in datos["vulnerabilities"]}


@lru_cache(maxsize=32)
def nvd(cve: str) -> dict | None:
    """La ficha del CVE en NVD (el objeto «cve» de la API 2.0), o None si NVD no lo tiene."""
    datos = json.loads(descargar(NVD.format(cve)))
    vulns = datos.get("vulnerabilities") or []
    return vulns[0]["cve"] if vulns else None


def notas(ficha: dict) -> list[dict]:
    """Cada nota CVSS de la ficha de NVD: versión, nota y vector."""
    resultado = []
    for clave, lista in (ficha.get("metrics") or {}).items():
        for m in lista:
            d = m.get("cvssData") or {}
            if "baseScore" in d:
                resultado.append({"version": str(d.get("version", "")), "nota": float(d["baseScore"]),
                                  "vector": d.get("vectorString", "")})
    return resultado


def cwes(ficha: dict) -> set[str]:
    return {d["value"].upper() for w in ficha.get("weaknesses") or [] for d in w.get("description") or []
            if d.get("value", "").upper().startswith("CWE-")}
