"""Confere uma captura VHIL REAL contra as solucoes analiticas do RC termico.

Uso: typhoon-python analisar_captura.py capturas/captura_AAAAMMDD_HHMMSS
Nao cria resultados experimentais na ausencia de um CSV autenticado.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

from parametros_e_referencia import CASE_TEMP_C, MODEL_R, MODEL_TAU, POWER_W

ROOT = Path(__file__).resolve().parent
SIGNALS = ("reset_ciclo", "potencia_degrau_W", "potencia_pulso_W",
           "Tj_degrau_C", "Tj_relaxacao_C", "Tj_pulso_C")
DT = 1e-5
CYCLE = 10000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rise_response(t: float, on: float, off: float | None = None) -> float:
    if t < on:
        return CASE_TEMP_C
    def step(age: float) -> float:
        return POWER_W * sum(r * (-math.expm1(-age / tau))
                             for r, tau in zip(MODEL_R, MODEL_TAU))
    value = step(t - on)
    if off is not None and t >= off:
        value -= step(t - off)
    return CASE_TEMP_C + value


def linear_crossing(xs: list[float], ys: list[float], target: float) -> float:
    for i in range(1, len(xs)):
        if ys[i - 1] <= target <= ys[i]:
            fraction = (target - ys[i - 1]) / (ys[i] - ys[i - 1]) if ys[i] != ys[i - 1] else 0.0
            return xs[i - 1] + fraction * (xs[i] - xs[i - 1])
    raise ValueError(f"Nao houve cruzamento de {target:.5g} C no trecho de degrau.")


def analyze(directory: Path) -> dict[str, object]:
    data = directory / "Equipe04_TermicoRC_captura.csv"
    meta = directory / "Equipe04_TermicoRC_metadados.json"
    if not data.is_file() or not meta.is_file():
        raise FileNotFoundError("Informe a pasta com CSV e metadados da captura real.")
    info = json.loads(meta.read_text(encoding="utf-8"))
    if info.get("sha256_dados") != sha256(data):
        raise ValueError("Hash do CSV difere dos metadados; captura alterada.")
    model = ROOT / "Equipe04_TermicoRC_IGBT.tse"
    if info.get("sha256_modelo") != sha256(model):
        raise ValueError("O .tse nao corresponde ao compilado para esta captura.")
    with data.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if set(("tempo_s", *SIGNALS)) - set(reader.fieldnames or []):
            raise ValueError("Colunas esperadas ausentes do CSV.")
        rows = [{key: float(value) for key, value in row.items()} for row in reader]
    if len(rows) < 2 * CYCLE:
        raise ValueError("Captura curta: sao necessarios pelo menos 2 ciclos completos.")
    if not all(math.isfinite(v) for row in rows for v in row.values()):
        raise ValueError("Valor nao finito no CSV.")
    dts = [b["tempo_s"] - a["tempo_s"] for a, b in zip(rows, rows[1:])]
    dt = statistics.median(dts)
    if abs(dt - DT) > 0.02 * DT or max(abs(v - dt) for v in dts) > 0.02 * DT:
        raise ValueError(f"Passo irregular ou divergente de 10 us: {dt:.9g} s.")
    resets = [i for i, row in enumerate(rows) if row["reset_ciclo"] >= 0.5
              and (i == 0 or rows[i - 1]["reset_ciclo"] < 0.5)]
    starts = [i + 1 for i in resets if i + CYCLE < len(rows)]
    if not starts:
        raise ValueError("Nenhum ciclo de 10000 amostras apos reset foi capturado inteiro.")
    start = starts[0]
    cycle = rows[start:start + CYCLE]
    if len(cycle) != CYCLE:
        raise ValueError("Ciclo incompleto.")
    if any(abs(cycle[i]["potencia_degrau_W"] - (POWER_W if 999 <= i < 5999 else 0.0)) > 0.1
           or abs(cycle[i]["potencia_pulso_W"] - (POWER_W if 999 <= i < 1999 else 0.0)) > 0.1
           for i in range(CYCLE)):
        raise ValueError("A sequencia de potencia nao corresponde ao ensaio especificado.")
    on, step_off, pulse_off = 999 * dt, 5999 * dt, 1999 * dt
    errors = {key: 0.0 for key in ("Tj_degrau_C", "Tj_relaxacao_C", "Tj_pulso_C")}
    points: list[tuple[float, ...]] = []
    xs: list[float] = []
    ys: list[float] = []
    for i, row in enumerate(cycle):
        t = i * dt
        expected = {
            "Tj_degrau_C": rise_response(t, on, step_off),
            "Tj_relaxacao_C": CASE_TEMP_C + POWER_W * sum(
                r * math.exp(-t / tau) for r, tau in zip(MODEL_R, MODEL_TAU)),
            "Tj_pulso_C": rise_response(t, on, pulse_off),
        }
        for key in errors:
            errors[key] = max(errors[key], abs(row[key] - expected[key]))
        if 999 <= i <= 5998:
            xs.append(t - on)
            ys.append(row["Tj_degrau_C"])
        if i % 20 == 0:
            points.append((t, row["Tj_degrau_C"], expected["Tj_degrau_C"],
                           row["Tj_relaxacao_C"], expected["Tj_relaxacao_C"],
                           row["Tj_pulso_C"], expected["Tj_pulso_C"]))
    final = CASE_TEMP_C + POWER_W * sum(MODEL_R)
    t10 = linear_crossing(xs, ys, CASE_TEMP_C + 0.1 * (final - CASE_TEMP_C))
    t90 = linear_crossing(xs, ys, CASE_TEMP_C + 0.9 * (final - CASE_TEMP_C))
    t98 = linear_crossing(xs, ys, CASE_TEMP_C + 0.98 * (final - CASE_TEMP_C))
    try:
        capture_label = str(data.relative_to(ROOT))
    except ValueError:
        capture_label = str(data)
    result: dict[str, object] = {
        "origem": "CSV da captura TyphoonSim; sem amostras sinteticas",
        "captura": capture_label, "sha256_captura": sha256(data),
        "indice_inicio_ciclo": start, "passo_s": dt,
        "erros_maximos_k": errors,
        "tempo_subida_10_90_s": t90 - t10,
        "tempo_atingir_98_porcento_s": t98,
        "pico_degrau_c": max(ys),
        "temperatura_final_teorica_c": final,
        "criterio_erro_0_15_k": max(errors.values()) <= 0.15,
    }
    out = directory / "resultados_vhil"
    out.mkdir(exist_ok=True)
    with (out / "curvas_vhil.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("tempo_s", "degrau_vhil_c", "degrau_teoria_c", "relax_vhil_c",
                         "relax_teoria_c", "pulso_vhil_c", "pulso_teoria_c"))
        writer.writerows(points)
    (out / "resumo.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    def error_tex(value: float) -> str:
        mantissa, exponent = f"{value:.3e}".split("e")
        return f"${mantissa.replace('.', '{,}')}\\times10^{{{int(exponent)}}}\\,\\mathrm{{K}}$"

    rise_tex = f"{1000 * (t90-t10):.4f}".replace(".", "{,}")
    settle_tex = f"{1000*t98:.4f}".replace(".", "{,}")
    tex = ("\\begin{tabular}{lr}\\toprule\n"
           "Medida VHIL & Valor \\\\ \\midrule\n"
           f"Maior erro, degrau & {error_tex(errors['Tj_degrau_C'])} \\\\ \n"
           f"Maior erro, relaxa\\c{{c}}\\~ao & {error_tex(errors['Tj_relaxacao_C'])} \\\\ \n"
           f"Maior erro, pulso & {error_tex(errors['Tj_pulso_C'])} \\\\ \n"
           f"Subida 10--90\\% & ${rise_tex}$~ms \\\\ \n"
           f"Atingimento de 98\\% & ${settle_tex}$~ms \\\\ \n"
           "\\bottomrule\\end{tabular}\n")
    (out / "medidas.tex").write_text(tex, encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", type=Path, help="Pasta produzida por capturar_vhil.py")
    args = parser.parse_args()
    print(json.dumps(analyze(args.pasta.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
