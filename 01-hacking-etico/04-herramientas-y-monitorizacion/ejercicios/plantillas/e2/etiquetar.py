"""Resume las alertas de Suricata (salidas/suricata/eve.json) por fase del ataque y por origen.

Uso: py etiquetar.py [ruta/a/eve.json]   (en Linux o macOS, python3)
Las fases salen de la primera palabra del mensaje de cada regla (RECONOCIMIENTO, ENUMERACION...).
Completa FASES_POR_SID para las reglas que escribas tú si su mensaje no empieza por la fase.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

FASES_POR_SID: dict[int, str] = {
    # 1000100: "EXPLOTACION",
}


def fase(alerta: dict) -> str:
    sid = alerta["signature_id"]
    return FASES_POR_SID.get(sid) or alerta["signature"].split(" ", 1)[0]


def alertas(ruta: Path):
    with ruta.open() as f:
        for linea in f:
            evento = json.loads(linea)
            if evento.get("event_type") == "alert":
                yield evento


def main(ruta: Path) -> None:
    por_fase: Counter[str] = Counter()
    por_origen: Counter[tuple[str, str]] = Counter()
    for evento in alertas(ruta):
        f = fase(evento["alert"])
        por_fase[f] += 1
        por_origen[(evento["src_ip"], f)] += 1

    print(f"{'FASE':<16}{'ALERTAS':>8}")
    for f, n in por_fase.most_common():
        print(f"{f:<16}{n:>8}")
    print()
    print(f"{'ORIGEN':<16}{'FASE':<16}{'ALERTAS':>8}")
    for (origen, f), n in sorted(por_origen.items()):
        print(f"{origen:<16}{f:<16}{n:>8}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "salidas/suricata/eve.json"))
