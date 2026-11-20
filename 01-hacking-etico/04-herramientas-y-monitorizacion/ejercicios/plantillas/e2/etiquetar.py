"""Resume las alertas de Suricata (salidas/suricata/eve.json) por fase del ataque y por origen.

Uso, desde ra1/u4-e2/:

    py etiquetar.py                  muestra el resumen en pantalla   (en Linux o macOS, python3)
    py etiquetar.py alertas.txt      lo guarda en alertas.txt, en UTF-8
    py etiquetar.py alertas.txt --eve otra/ruta/eve.json

Las fases salen de la primera palabra del mensaje de cada regla (RECONOCIMIENTO, ENUMERACION...).
Completa FASES_POR_SID para las reglas que escribas tú si su mensaje no empieza por la fase.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

FASES_POR_SID: dict[int, str] = {
    # 1000100: "EXPLOTACION",
}


def fase(alerta: dict) -> str:
    sid = alerta["signature_id"]
    return FASES_POR_SID.get(sid) or alerta["signature"].split(" ", 1)[0]


def alertas(ruta: Path):
    with ruta.open(encoding="utf-8", errors="replace") as f:
        for linea in f:
            try:
                evento = json.loads(linea)
            except json.JSONDecodeError:
                continue  # la última línea puede estar a medio escribir
            if evento.get("event_type") == "alert":
                yield evento


def resumen(ruta: Path) -> str:
    por_fase: Counter[str] = Counter()
    por_origen: Counter[tuple[str, str]] = Counter()
    for evento in alertas(ruta):
        f = fase(evento["alert"])
        por_fase[f] += 1
        por_origen[(evento["src_ip"], f)] += 1

    lineas = [f"{'FASE':<16}{'ALERTAS':>8}"]
    lineas += [f"{f:<16}{n:>8}" for f, n in por_fase.most_common()]
    lineas += ["", f"{'ORIGEN':<16}{'FASE':<16}{'ALERTAS':>8}"]
    lineas += [f"{origen:<16}{f:<16}{n:>8}" for (origen, f), n in sorted(por_origen.items())]
    return "\n".join(lineas) + "\n"


def main() -> None:
    args = argparse.ArgumentParser(description="Resume las alertas de Suricata por fase y por origen.")
    args.add_argument("salida", nargs="?", help="fichero donde guardar el resumen (si no, se muestra en pantalla)")
    args.add_argument("--eve", default="salidas/suricata/eve.json", help="registro de Suricata que se resume")
    a = args.parse_args()
    texto = resumen(Path(a.eve))
    if a.salida:
        Path(a.salida).write_text(texto, encoding="utf-8", newline="\n")
        print(f"Resumen guardado en {a.salida}")
    else:
        print(texto, end="")


if __name__ == "__main__":
    main()
