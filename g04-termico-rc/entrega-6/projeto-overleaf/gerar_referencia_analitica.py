"""Gera apenas curvas TEORICAS ilustrativas, nunca captura TyphoonSim.

Os arquivos ficam em referencia_analitica/ e o relatorio os identifica como
previsoes. Eles nao substituem resultados_vhil/ nem os dados brutos medidos.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "referencia_analitica"
CASES = ((0.5, "05"), (1.0, "10"), (1.5, "15"))
FS = 10000.0
FC = 500.0
FM = 25.0


def main() -> None:
    DESTINATION.mkdir(exist_ok=True)
    for mu, tag in CASES:
        with (DESTINATION / f"tempo_teorico_mu{tag}.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow(("tempo_ms", "sinal_am", "env_pos", "env_neg", "env_abs"))
            for i in range(801):
                t = i / FS
                m = math.cos(2 * math.pi * FM * t)
                c = math.cos(2 * math.pi * FC * t)
                u = 1 + mu * m
                writer.writerow((f"{1000*t:.6f}", f"{u*c:.9f}", f"{u:.9f}", f"{-u:.9f}", f"{abs(u):.9f}"))

        with (DESTINATION / f"espectro_teorico_mu{tag}.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow(("frequencia_hz", "amplitude_v"))
            for f, amplitude in ((FC - FM, mu / 2), (FC, 1.0), (FC + FM, mu / 2)):
                writer.writerow((f"{f:.1f}", f"{amplitude:.6f}"))
    print(f"Referencias analiticas em {DESTINATION}")


if __name__ == "__main__":
    main()
