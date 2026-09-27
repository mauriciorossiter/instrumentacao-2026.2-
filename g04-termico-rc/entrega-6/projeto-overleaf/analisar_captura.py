"""Analisa a captura VHIL de AM e gera figuras/tabela para o Overleaf.

Uso no computador com o Typhoon, apos capturar_vhil.py:
    typhoon-python analisar_captura.py capturas/captura_AAAAMMDD_HHMMSS

Usa apenas a biblioteca padrao do Python. Exige CSV e metadados que
capturar_vhil.py salvou; recusa arquivo sem procedencia VHIL verificavel.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parent
EXPECTED_SIGNALS = (
    "tempo_s",
    "mensagem_norm",
    "portadora",
    "indice_modulacao",
    "envoltoria_assinada",
    "sinal_am",
)
REGIMES = ((0.5, "05"), (1.0, "10"), (1.5, "15"))
FREQUENCIES = (475.0, 500.0, 525.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_capture(directory: Path) -> tuple[list[dict[str, float]], dict[str, object]]:
    metadata_path = directory / "Equipe_04_ModulacaoAM_metadados.json"
    if not metadata_path.is_file():
        raise ValueError(f"Metadados nao encontrados: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("origem") != "TyphoonSim/Virtual HIL; API hil.start_capture":
        raise ValueError("Origem VHIL nao confirmada no arquivo de metadados.")
    data_path = directory / str(metadata.get("arquivo_dados", ""))
    if not data_path.is_file():
        raise ValueError(f"CSV nao encontrado: {data_path}")
    if sha256(data_path).lower() != str(metadata.get("sha256_dados", "")).lower():
        raise ValueError("O hash do CSV diverge dos metadados da captura.")
    model = ROOT / "Equipe_04_ModulacaoAM.tse"
    if sha256(model).lower() != str(metadata.get("sha256_modelo", "")).lower():
        raise ValueError("O .tse foi alterado depois da captura; mantenha a versao capturada.")

    with data_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != EXPECTED_SIGNALS:
            raise ValueError(f"Colunas do CSV inesperadas: {reader.fieldnames}")
        rows = [{key: float(value[key]) for key in EXPECTED_SIGNALS} for value in reader]
    if len(rows) != int(metadata.get("amostras", -1)):
        raise ValueError("Contagem de amostras diverge dos metadados.")
    if len(rows) < 12000:
        raise ValueError("Captura curta para comparar os tres regimes.")
    if not all(math.isfinite(value) for row in rows for value in row.values()):
        raise ValueError("Ha valores nao finitos no CSV.")
    dts = [b["tempo_s"] - a["tempo_s"] for a, b in zip(rows, rows[1:])]
    dt = statistics.median(dts)
    if not (0.000098 <= dt <= 0.000102):
        raise ValueError(f"Taxa de amostragem incorreta: dt={dt:.9g} s")
    if max(abs(value - dt) for value in dts) > 2e-6:
        raise ValueError("Eixo temporal irregular; nao calcular espectro.")
    return rows, metadata


def runs_by_regime(rows: list[dict[str, float]]) -> dict[float, list[dict[str, float]]]:
    runs: dict[float, list[list[dict[str, float]]]] = {mu: [] for mu, _ in REGIMES}
    current: list[dict[str, float]] = []
    last_mu: float | None = None
    for row in rows:
        mu = round(row["indice_modulacao"], 1)
        if mu not in runs or abs(row["indice_modulacao"] - mu) > 1e-4:
            raise ValueError(f"Indice de modulacao nao esperado: {row['indice_modulacao']}")
        if last_mu is not None and mu != last_mu:
            runs[last_mu].append(current)
            current = []
        current.append(row)
        last_mu = mu
    if current and last_mu is not None:
        runs[last_mu].append(current)

    result = {}
    for mu, segments in runs.items():
        if not segments:
            raise ValueError(f"Regime mu={mu} ausente.")
        segment = max(segments, key=len)
        if len(segment) < 3800:
            raise ValueError(
                f"Regime mu={mu} tem apenas {len(segment)} amostras contiguas. "
                "Capture mais de um ciclo completo."
            )
        result[mu] = segment[:4000]
    return result


def solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [matrix[i][:] + [vector[i]] for i in range(size)]
    for k in range(size):
        pivot = max(range(k, size), key=lambda row: abs(augmented[row][k]))
        if abs(augmented[pivot][k]) < 1e-12:
            raise ValueError("Ajuste harmonico singular; verifique a captura.")
        augmented[k], augmented[pivot] = augmented[pivot], augmented[k]
        scale = augmented[k][k]
        augmented[k] = [value / scale for value in augmented[k]]
        for i in range(size):
            if i == k:
                continue
            factor = augmented[i][k]
            augmented[i] = [a - factor * b for a, b in zip(augmented[i], augmented[k])]
    return [augmented[i][-1] for i in range(size)]


def harmonic_fit(segment: list[dict[str, float]]) -> tuple[list[float], float]:
    count = 1 + 2 * len(FREQUENCIES)
    gram = [[0.0] * count for _ in range(count)]
    rhs = [0.0] * count
    t0 = segment[0]["tempo_s"]
    for row in segment:
        t = row["tempo_s"] - t0
        basis = [1.0]
        for frequency in FREQUENCIES:
            angle = 2.0 * math.pi * frequency * t
            basis.extend((math.cos(angle), math.sin(angle)))
        y = row["sinal_am"]
        for i in range(count):
            rhs[i] += basis[i] * y
            for j in range(count):
                gram[i][j] += basis[i] * basis[j]
    coefficients = solve_linear(gram, rhs)
    amplitudes = [math.hypot(coefficients[1 + 2 * i], coefficients[2 + 2 * i]) for i in range(3)]
    errors = []
    for row in segment:
        t = row["tempo_s"] - t0
        prediction = coefficients[0]
        for i, frequency in enumerate(FREQUENCIES):
            angle = 2.0 * math.pi * frequency * t
            prediction += coefficients[1 + 2 * i] * math.cos(angle)
            prediction += coefficients[2 + 2 * i] * math.sin(angle)
        errors.append((row["sinal_am"] - prediction) ** 2)
    return amplitudes, math.sqrt(sum(errors) / len(errors))


def spectrum(segment: list[dict[str, float]], limit_hz: float = 1000.0) -> list[tuple[float, float]]:
    n = len(segment)
    dt = statistics.median(
        b["tempo_s"] - a["tempo_s"] for a, b in zip(segment, segment[1:])
    )
    fs = 1.0 / dt
    window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    weighted = [row["sinal_am"] * w for row, w in zip(segment, window)]
    norm = 2.0 / sum(window)
    points = []
    for k in range(int(limit_hz * n / fs) + 1):
        multiplier = complex(
            math.cos(-2 * math.pi * k / n),
            math.sin(-2 * math.pi * k / n),
        )
        phase = complex(1.0, 0.0)
        total = complex(0.0, 0.0)
        for value in weighted:
            total += value * phase
            phase *= multiplier
        points.append((k * fs / n, abs(total) * norm))
    return points


def write_csv(path: Path, fields: tuple[str, ...], data: list[dict[str, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in data:
            writer.writerow({name: f"{row[name]:.10g}" for name in fields})


def analyze(directory: Path) -> Path:
    rows, metadata = load_capture(directory)
    segments = runs_by_regime(rows)
    output = ROOT / "resultados_vhil"
    output.mkdir(exist_ok=True)
    summary = []
    for mu, tag in REGIMES:
        segment = segments[mu]
        amplitudes, residual = harmonic_fit(segment)
        inferred_mu = (amplitudes[0] + amplitudes[2]) / amplitudes[1]
        minimum_envelope = min(row["envoltoria_assinada"] for row in segment)
        if residual > 0.002 or abs(amplitudes[1] - 1.0) > 0.03 or abs(inferred_mu - mu) > 0.03:
            raise ValueError(
                f"Resultados incoerentes para mu={mu}: A_c={amplitudes[1]:.4f}, "
                f"mu estimado={inferred_mu:.4f}, residuo={residual:.4f}."
            )
        summary.append({
            "mu_programado": mu,
            "amostras_janela": len(segment),
            "amplitude_475_v": amplitudes[0],
            "amplitude_500_v": amplitudes[1],
            "amplitude_525_v": amplitudes[2],
            "mu_estimado": inferred_mu,
            "envoltoria_minima_v": minimum_envelope,
            "residuo_rms_v": residual,
        })

        t0 = segment[0]["tempo_s"]
        time_rows = []
        for row in segment:
            relative = (row["tempo_s"] - t0) * 1000.0
            if relative > 80.0:
                break
            u = row["envoltoria_assinada"]
            time_rows.append({
                "tempo_ms": relative,
                "sinal_am": row["sinal_am"],
                "env_pos": u,
                "env_neg": -u,
                "env_abs": abs(u),
            })
        write_csv(
            output / f"tempo_mu{tag}.csv",
            ("tempo_ms", "sinal_am", "env_pos", "env_neg", "env_abs"),
            time_rows,
        )
        spectral_rows = [
            {"frequencia_hz": f, "amplitude_v": a}
            for f, a in spectrum(segment)
        ]
        write_csv(
            output / f"espectro_mu{tag}.csv",
            ("frequencia_hz", "amplitude_v"),
            spectral_rows,
        )

    result = {
        "origem": metadata["origem"],
        "data_hora_captura": metadata["data_hora_captura"],
        "sha256_modelo": metadata["sha256_modelo"],
        "sha256_dados": metadata["sha256_dados"],
        "total_amostras_captura": len(rows),
        "taxa_amostragem_hz": metadata["taxa_captura_hz"],
        "casos": summary,
    }
    (output / "resumo.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "% GERADO EXCLUSIVAMENTE DE CAPTURA TyphoonSim/Virtual HIL.",
        "% Nao editar numeros manualmente; reexecute analisar_captura.py.",
        f"\\def\\CapturaData{{{metadata['data_hora_captura']}}}",
        f"\\def\\CapturaN{{{len(rows)}}}",
        f"\\def\\CapturaTaxa{{{float(metadata['taxa_captura_hz']):.2f}}}",
        f"\\def\\CapturaHashModelo{{{metadata['sha256_modelo']}}}",
        f"\\def\\CapturaHashDados{{{metadata['sha256_dados']}}}",
        "\\begin{center}",
        "\\begin{tabular}{@{}rrrrrrr@{}}",
        "\\toprule",
        "$\\mu$ & $A_{475}$ [V] & $A_{500}$ [V] & $A_{525}$ [V] & $\\hat\\mu$ & $u_{\\min}$ [V] & RMS res. [V] \\\\",
        "\\midrule",
    ]
    for case in summary:
        lines.append(
            f"{case['mu_programado']:.1f} & "
            f"{case['amplitude_475_v']:.4f} & "
            f"{case['amplitude_500_v']:.4f} & "
            f"{case['amplitude_525_v']:.4f} & "
            f"{case['mu_estimado']:.4f} & "
            f"{case['envoltoria_minima_v']:.4f} & "
            f"{case['residuo_rms_v']:.5f} \\\\")
    lines.extend(("\\bottomrule", "\\end{tabular}", "\\end{center}"))
    (output / "medidas.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captura", type=Path, help="Pasta criada por capturar_vhil.py")
    args = parser.parse_args()
    output = analyze(args.captura.resolve())
    print(f"Resultados para o Overleaf: {output}")
    print("Copie a pasta resultados_vhil ao projeto Overleaf e compile novamente.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
