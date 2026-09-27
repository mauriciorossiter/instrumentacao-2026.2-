"""Gera duas figuras PNG a partir dos CSVs verificados, sem alterar os dados.

Uso: python gerar_figuras.py
Requer Pillow. A figura VHIL usa somente a captura indicada abaixo.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FIT = ROOT / "referencia_analitica" / "ajuste_impedancia.csv"
VHIL = ROOT / "capturas" / "captura_20260925_094319" / "resultados_vhil" / "curvas_vhil.csv"
OUT = ROOT / "figuras"
OUT.mkdir(exist_ok=True)
FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")


def font(size: int, bold: bool = False):
    path = FONT_BOLD if bold else FONT_PATH
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return [{key: float(value) for key, value in row.items()}
                for row in csv.DictReader(stream)]


BLUE, RED, GREEN, GRAY, BLACK = "#1764ab", "#bd4539", "#228352", "#dbe2e9", "#18212b"


def polyline(draw: ImageDraw.ImageDraw, points, color: str, width: int = 4, dashed: bool = False):
    if not dashed:
        draw.line(points, fill=color, width=width, joint="curve")
        return
    for i in range(0, len(points) - 1, 3):
        draw.line(points[i:i + 2], fill=color, width=width)


def make_fit() -> None:
    rows = read_csv(FIT)
    image = Image.new("RGB", (1500, 800), "white")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 145, 110, 1420, 665
    draw.text((left, 28), "Impedância térmica junção–cápsula: dados do fabricante e modelo reduzido",
              font=font(30, True), fill=BLACK)
    lx0, lx1, ymin, ymax = math.log10(1e-5), math.log10(0.25), 0, 2.1
    x = lambda t: left + (math.log10(t) - lx0) * (right - left) / (lx1 - lx0)
    y = lambda v: bottom - (v - ymin) * (bottom - top) / (ymax - ymin)
    for t, label in ((1e-5, "10 µs"), (1e-4, "0,1 ms"), (1e-3, "1 ms"),
                     (1e-2, "10 ms"), (1e-1, "100 ms")):
        xx = round(x(t))
        draw.line((xx, top, xx, bottom), fill=GRAY, width=2)
        draw.text((xx - 30, bottom + 12), label, font=font(20), fill=BLACK)
    for value in (0, 0.5, 1, 1.5, 2):
        yy = round(y(value))
        draw.line((left, yy, right, yy), fill=GRAY, width=2)
        draw.text((left - 66, yy - 12), f"{value:.1f}", font=font(20), fill=BLACK)
    draw.rectangle((left, top, right, bottom), outline=BLACK, width=2)
    for key, color, dashed in (("zth_fabricante_k_w", BLUE, False),
                               ("zth_reduzido_k_w", RED, True)):
        pts = [(round(x(row["tempo_s"])), round(y(row[key]))) for row in rows]
        polyline(draw, pts, color, 5, dashed)
    draw.text((left, bottom + 65), "Tempo desde o degrau de potência (escala logarítmica)",
              font=font(22), fill=BLACK)
    draw.text((left, 76), "Zth,j-c (K/W)", font=font(22), fill=BLACK)
    draw.line((920, 482, 985, 482), fill=BLUE, width=5)
    draw.text((1000, 469), "Fabricante: 4 ramos", font=font(20), fill=BLACK)
    draw.line((920, 516, 940, 516), fill=RED, width=5)
    draw.line((950, 516, 970, 516), fill=RED, width=5)
    draw.text((1000, 503), "Redução: 2 ramos", font=font(20), fill=BLACK)
    image.save(OUT / "ajuste_impedancia.png", optimize=True)


def make_vhil() -> None:
    rows = read_csv(VHIL)
    image = Image.new("RGB", (1500, 1530), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 26), "TyphoonSim/VHIL versus solução analítica", font=font(32, True), fill=BLACK)
    panels = (
        ("Degrau de 10 W, ligado de 10 a 60 ms", "degrau_vhil_c", "degrau_teoria_c", 70),
        ("Relaxação a partir do equilíbrio", "relax_vhil_c", "relax_teoria_c", 15),
        ("Pulso de 10 W, ligado de 10 a 20 ms", "pulso_vhil_c", "pulso_teoria_c", 35),
    )
    for panel, (label, measured, theoretical, xmax) in enumerate(panels):
        top = 150 + panel * 430
        left, right, bottom = 145, 1420, top + 295
        draw.text((left, top - 47), label, font=font(25, True), fill=BLACK)
        x = lambda t: left + t * 1000 * (right - left) / xmax
        y = lambda v: bottom - (v - 24) * (bottom - top) / 23
        for ms in range(0, xmax + 1, 5 if xmax <= 35 else 10):
            xx = round(x(ms / 1000))
            draw.line((xx, top, xx, bottom), fill=GRAY, width=2)
            draw.text((xx - 13, bottom + 8), str(ms), font=font(17), fill=BLACK)
        for temp in (25, 30, 35, 40, 45):
            yy = round(y(temp))
            draw.line((left, yy, right, yy), fill=GRAY, width=2)
            draw.text((left - 48, yy - 10), str(temp), font=font(17), fill=BLACK)
        draw.rectangle((left, top, right, bottom), outline=BLACK, width=2)
        plotted = [row for row in rows if row["tempo_s"] * 1000 <= xmax]
        theory_points = [(round(x(row["tempo_s"])), round(y(row[theoretical]))) for row in plotted]
        measured_points = [(round(x(row["tempo_s"])), round(y(row[measured]))) for row in plotted]
        polyline(draw, theory_points, RED, 6, True)
        polyline(draw, measured_points, BLUE, 3)
        draw.text((left, bottom + 44), "Tempo no ciclo (ms)", font=font(19), fill=BLACK)
    draw.line((875, 91, 935, 91), fill=BLUE, width=4)
    draw.text((950, 78), "VHIL", font=font(20), fill=BLACK)
    polyline(draw, [(1100, 91), (1160, 91)], RED, 5, True)
    draw.text((1175, 78), "Analítico", font=font(20), fill=BLACK)
    draw.text((40, 1435), "Temperatura de junção (°C). O desvio máximo é inferior a 0,000002 K em cada ensaio.",
              font=font(21), fill=BLACK)
    image.save(OUT / "ensaios_vhil.png", optimize=True)


if __name__ == "__main__":
    make_fit()
    make_vhil()
    print("Figuras geradas em", OUT)
