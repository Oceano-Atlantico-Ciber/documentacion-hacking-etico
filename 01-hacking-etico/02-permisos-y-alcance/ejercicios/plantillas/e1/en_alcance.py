#!/usr/bin/env python3
"""Dice si una prueba contra una dirección, en un momento dado, está dentro de tu alcance.json.

Uso, desde ra1/u2-e1/:

    py en_alcance.py 192.168.1.20 "2027-02-03 22:15"

Es la misma regla que aplica el corrector, con otras direcciones y otros momentos que no ves.
"""

from __future__ import annotations

import ipaddress
import json
import sys
from datetime import datetime, time, timedelta
from pathlib import Path


def _red(texto: str) -> ipaddress.IPv4Network:
    return ipaddress.ip_network(texto.strip(), strict=False)


def _hora(texto: str) -> time:
    return datetime.strptime(texto.strip(), "%H:%M").time()


def permitido(alcance: dict, ip: str, momento: datetime) -> bool:
    """Dentro del alcance, fuera de las exclusiones, entre las fechas y en el horario, que puede cruzar la medianoche."""
    direccion = ipaddress.ip_address(ip)
    if not any(direccion in _red(x) for x in alcance["dentro"]):
        return False
    if any(direccion in _red(x) for x in alcance["fuera"]):
        return False
    inicio = datetime.fromisoformat(alcance["inicio"]).date()
    fin = datetime.fromisoformat(alcance["fin"]).date()
    desde, hasta = _hora(alcance["horario"]["desde"]), _hora(alcance["horario"]["hasta"])
    ahora = momento.time()
    if desde <= hasta:
        en_horario, noche = desde <= ahora < hasta, momento.date()
    else:  # lo de madrugada pertenece a la noche que empezó el día anterior
        en_horario = ahora >= desde or ahora < hasta
        noche = momento.date() if ahora >= desde else (momento - timedelta(days=1)).date()
    return en_horario and inicio <= noche <= fin


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    alcance = json.loads(Path("alcance.json").read_text(encoding="utf-8-sig"))
    print("DENTRO del alcance" if permitido(alcance, argv[0], datetime.fromisoformat(argv[1])) else "FUERA del alcance")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
