"""Compose del alumno: se lee con docker compose config y solo se levanta si no abre ninguna puerta
sobre el equipo que corrige (Docker 4 · Puertas que abre un compose)."""

from __future__ import annotations

import json
from pathlib import Path

from .docker import Fallo, Salida, docker

SOCKET = Path("/var/run/docker.sock").resolve()
DEL_EQUIPO = ("network_mode", "pid", "ipc", "uts", "userns_mode", "cgroup")


class Proyecto:
    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        self._base = ("compose", "--project-directory", str(carpeta), "-f", str(carpeta / "docker-compose.yml"))

    def __call__(self, *args: str, espera: int = 300) -> Salida:
        return docker(*self._base, *args, cwd=self.carpeta, espera=espera)

    def config(self) -> dict:
        """El compose tal como lo entiende Docker, con todos los perfiles: también lo que solo se lanza con run."""
        r = self("--profile", "*", "config", "--format", "json")
        if r.codigo:
            raise Fallo(f"docker compose config falla con un .env completo: {r.motivo}")
        return json.loads(r.salida)


def puertas(config: dict, raiz: Path) -> list[str]:
    """Lo que daría al compose poder sobre el equipo. raiz es el repositorio del alumno: nada fuera de él."""
    abiertas = []
    dentro = lambda ruta: Path(ruta).resolve().is_relative_to(raiz.resolve())
    for nombre, s in config.get("services", {}).items():
        if s.get("privileged"):
            abiertas.append(f"{nombre}: privileged")
        abiertas += [f"{nombre}: {clave}" for clave in ("cap_add", "devices", "volumes_from") if s.get(clave)]
        abiertas += [f"{nombre}: {clave}: {s[clave]}" for clave in DEL_EQUIPO
                     if s.get(clave) == "host" or str(s.get(clave, "")).startswith("container:")]
        if any("unconfined" in o for o in s.get("security_opt", [])):
            abiertas.append(f"{nombre}: security_opt sin confinamiento")
        for v in s.get("volumes", []):
            if v["type"] == "bind" and Path(v["source"]).resolve() == SOCKET:
                abiertas.append(f"{nombre}: monta el socket de Docker")
            elif v["type"] == "bind" and not dentro(v["source"]):
                abiertas.append(f"{nombre}: monta {v['source']}, fuera de tu repositorio")
            elif v["type"] not in ("bind", "volume", "tmpfs"):
                abiertas.append(f"{nombre}: montaje de tipo {v['type']}")
        if build := s.get("build"):
            if not dentro(build["context"]):
                abiertas.append(f"{nombre}: construye desde {build['context']}, fuera de tu repositorio")
            if build.get("ssh") or build.get("additional_contexts"):
                abiertas.append(f"{nombre}: build con ssh o contextos adicionales")
    for tipo in ("secrets", "configs"):
        for nombre, d in (config.get(tipo) or {}).items():
            if (f := d.get("file")) and not dentro(f):
                abiertas.append(f"{tipo} {nombre}: lee {f}, fuera de tu repositorio")
            if d.get("environment") or d.get("external"):
                abiertas.append(f"{tipo} {nombre}: sale del entorno o del motor, no de tu repositorio")
    return abiertas


def resumen(s: dict) -> dict[str, object]:
    """Lo que la tabla de un ejercicio dice de un servicio, en una forma que se compara con ==."""
    return {
        "imagen": s.get("image"),
        "puertos": sorted((p.get("host_ip", ""), str(p.get("published", "")), int(p["target"])) for p in s.get("ports", [])),
        "montajes": sorted((v["type"], v.get("source", "") if v["type"] != "bind" else str(Path(v["source"]).resolve()),
                            v["target"], bool(v.get("read_only"))) for v in s.get("volumes", [])),
        "redes": sorted(s.get("networks") or {}),
        "perfiles": sorted(s.get("profiles", [])),
    }
