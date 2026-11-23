# -*- coding: utf-8 -*-
"""Estilo comum das figuras (G02, ECOM060 2026.2)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COR = dict(
    real="#2a78d6",      # grandeza real da planta
    med="#eb6834",       # grandeza medida (caminho real)
    ideal="#1baf7a",     # caminho ideal
    ref="#52514e",       # referencia
    u="#6250d6",         # esforco
    c4="#eda100",
    c5="#e87ba4",
    c6="#008300",
    crit="#898781",      # limites de criterio
    grid="#e1e0d9",
)
SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 200, "font.size": 9, "axes.titlesize": 9.5,
    "axes.labelsize": 9, "legend.fontsize": 8, "axes.grid": True, "grid.color": COR["grid"],
    "grid.linewidth": 0.6, "axes.edgecolor": "#c3c2b7", "axes.spines.top": False,
    "axes.spines.right": False, "lines.linewidth": 1.6, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "#fcfcfb", "font.family": "DejaVu Sans",
    "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def salvar(fig, caminho):
    fig.tight_layout()
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
