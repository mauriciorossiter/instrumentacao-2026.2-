"""Definição dos ensaios e parâmetros em unidades físicas."""
from dataclasses import dataclass, replace

RHO_G = 9810.0  # Pa/m
P_FS = 16000.0  # Pa
VS = 5.0
SLOPE = 0.8 * VS * RHO_G / P_FS  # 2.4525 V/m
H_FS = P_FS / RHO_G
N = 100.0
CHANS = ("h1", "h2")
PLANTA = {
    "degrau": (5., 0., 10., 10.),
    "inicial": (0., 0., 11.5, 6.),
    "pulso": (0., 20., 10., 10.),
}

@dataclass(frozen=True)
class Instrumento:
    zero_mm: float = 6.0
    ganho_pct: float = 0.3
    tau_s: float = 0.2
    ruido_mm: float = 2.0
    fc_hz: float = 0.2
    adc_bits: int = 12
    correcao_mm: float = 0.0
    curvatura_mm: float = 3.0

    def validar(self):
        import math
        campos = {
            "zero_mm": (-100, 100), "ganho_pct": (-5, 5),
            "tau_s": (0, 100), "ruido_mm": (0, 100),
            "fc_hz": (0, 0.5), "adc_bits": (0, 16),
            "correcao_mm": (-100, 100), "curvatura_mm": (-10, 10),
        }
        for k, (a, b) in campos.items():
            v = getattr(self, k)
            if not math.isfinite(v) or not a <= v <= b:
                raise ValueError(f"{k}: valor válido de {a} a {b}")
        if int(self.adc_bits) != self.adc_bits or self.adc_bits in (1, 2, 3):
            raise ValueError("adc_bits: usar 0 (bypass) ou inteiro de 4 a 16")
        if 0 < self.tau_s < 0.05:
            raise ValueError("tau_s: usar 0 (bypass) ou pelo menos 0,05 s")
        if 0 < self.fc_hz < 0.01:
            raise ValueError("fc_hz: usar 0 (bypass) ou pelo menos 0,01 Hz")

NOMINAL = Instrumento()
IDEAL = Instrumento(0, 0, 0, 0, 0, 0, 0, 0)
CASOS = {k: (k, NOMINAL) for k in PLANTA}
CASOS.update({
    "referencia": ("degrau", IDEAL),
    "so-ganho": ("degrau", replace(IDEAL, ganho_pct=0.3)),
    "so-adc": ("degrau", replace(IDEAL, adc_bits=12)),
    "so-curvatura": ("degrau", replace(IDEAL, curvatura_mm=3.0)),
    "so-interferencia": ("degrau", replace(IDEAL, ruido_mm=2.0)),
    "so-filtro": ("degrau", replace(IDEAL, fc_hz=0.2)),
    "zero-corrigido": ("degrau", replace(NOMINAL, correcao_mm=6.0)),
})
for valor in (6, 20, 60):
    CASOS[f"zero-{valor}mm"] = "degrau", replace(IDEAL, zero_mm=valor)
for nome, valor in (("0p2", .2), ("10", 10), ("60", 60)):
    CASOS[f"tau-{nome}s"] = "degrau", replace(IDEAL, tau_s=valor)
for valor in (2, 10, 40):
    CASOS[f"ruido-{valor}mm"] = "degrau", replace(IDEAL, fc_hz=.2, ruido_mm=valor)
