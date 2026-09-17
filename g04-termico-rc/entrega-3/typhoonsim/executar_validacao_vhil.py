"""Executa e documenta a validação experimental do instrumento estático.

Uso recomendado, no Prompt de Comando configurado pelo Typhoon HIL 2026.2:

    typhoon-python executar_validacao_vhil.py

O script compila o .tse, carrega o .cpd no Virtual HIL, adquire os seis probes,
estima intercepto e inclinação por mínimos quadrados e grava arquivos prontos
para inclusão no relatório. Nenhum resultado é criado se a aquisição real não
for concluída com sucesso.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time
from typing import Iterable, Sequence


SIGNALS = (
    "Entrada_x",
    "Saida_ideal",
    "Saida_desvio_zero",
    "Saida_sensibilidade",
    "Saida_real",
    "Erro_total",
)

EXPECTED = {
    "Saida_ideal": (0.0, 1.0),
    "Saida_desvio_zero": (0.5, 1.0),
    "Saida_sensibilidade": (0.0, 1.2),
    "Saida_real": (0.5, 1.2),
    "Erro_total": (0.5, 0.2),
}

P0 = 0.0
K0 = 1.0
P_EXPECTED = 0.5
K_EXPECTED = 1.2
TOL_P = 0.01
TOL_K = 0.01


@dataclass(frozen=True)
class FitResult:
    signal: str
    intercept: float
    slope: float
    rmse: float
    max_abs_residual: float
    expected_intercept: float
    expected_slope: float


def fail(message: str) -> RuntimeError:
    return RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fit_line(x_values: Sequence[float], y_values: Sequence[float], signal: str) -> FitResult:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        raise fail(f"Dados insuficientes para ajustar {signal}.")
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    if denominator <= 0.0:
        raise fail("A entrada não variou; não é possível estimar a sensibilidade.")
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / denominator
    intercept = y_mean - slope * x_mean
    residuals = [y - (intercept + slope * x) for x, y in zip(x_values, y_values)]
    rmse = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    expected_intercept, expected_slope = EXPECTED[signal]
    return FitResult(
        signal=signal,
        intercept=intercept,
        slope=slope,
        rmse=rmse,
        max_abs_residual=max(abs(value) for value in residuals),
        expected_intercept=expected_intercept,
        expected_slope=expected_slope,
    )


def validate_rows(rows: Sequence[dict[str, float]]) -> None:
    for index, row in enumerate(rows):
        missing = [name for name in ("tempo_s", *SIGNALS) if name not in row]
        if missing:
            raise fail(f"Amostra {index} sem as colunas: {', '.join(missing)}")
        if not all(math.isfinite(float(row[name])) for name in ("tempo_s", *SIGNALS)):
            raise fail(f"Amostra {index} contém valor não finito.")
    x_values = [row["Entrada_x"] for row in rows]


def analyse(rows: Sequence[dict[str, float]]) -> tuple[list[FitResult], dict[str, object]]:
    validate_rows(rows)
    # Retiram-se apenas os pontos muito próximos da descontinuidade da rampa.
    selected = [row for row in rows if 0.02 <= row["Entrada_x"] <= 9.98]
    x_values = [row["Entrada_x"] for row in selected]
    fits = [
        fit_line(x_values, [row[signal] for row in selected], signal)
        for signal in EXPECTED
    ]
    real_fit = next(item for item in fits if item.signal == "Saida_real")
    delta_p = real_fit.intercept - P0
    delta_k = real_fit.slope - K0
    passed = (
        abs(real_fit.intercept - P_EXPECTED) <= TOL_P
        and abs(real_fit.slope - K_EXPECTED) <= TOL_K
    )
    reset_count = sum(
        1
        for previous, current in zip(rows, rows[1:])
        if current["Entrada_x"] < previous["Entrada_x"] - 5.0
    )
    summary = {
        "sample_count": len(rows),
        "fit_sample_count": len(selected),
        "x_min": min(row["Entrada_x"] for row in rows),
        "x_max": max(row["Entrada_x"] for row in rows),
        "reset_count": reset_count,
        "p0": P0,
        "k0": K0,
        "p_hat": real_fit.intercept,
        "k_hat": real_fit.slope,
        "delta_p": delta_p,
        "delta_k": delta_k,
        "expected_p": P_EXPECTED,
        "expected_k": K_EXPECTED,
        "tolerance_p": TOL_P,
        "tolerance_k": TOL_K,
        "passed": passed,
    }
    return fits, summary


def compile_model(tse_path: Path) -> Path:
    try:
        from typhoon.api.schematic_editor import model
    except ImportError as exc:
        raise fail(
            "A API do Typhoon não foi encontrada. Execute com typhoon-python, "
            "não com o Python comum do Windows."
        ) from exc

    print(f"[1/5] Abrindo e compilando: {tse_path}")
    model.load(str(tse_path))
    try:
        if not model.compile():
            raise fail("A compilação do modelo retornou falha.")
        cpd_path = Path(model.get_compiled_model_file(str(tse_path))).resolve()
    finally:
        close_model = getattr(model, "close_model", None)
        if callable(close_model):
            close_model()
    if not cpd_path.exists():
        raise fail(f"O compilador não produziu o arquivo esperado: {cpd_path}")
    return cpd_path


def acquire(cpd_path: Path, duration: float, interval_ms: int, physical_hil: bool) -> list[dict[str, float]]:
    try:
        import typhoon.api.hil as hil
    except ImportError as exc:
        raise fail(
            "A API do Typhoon não foi encontrada. Execute com typhoon-python."
        ) from exc

    mode = "HIL físico" if physical_hil else "Virtual HIL"
    print(f"[2/5] Carregando {cpd_path.name} em {mode}.")
    loaded = hil.load_model(file=str(cpd_path), vhil_device=not physical_hil)
    if not loaded:
        raise fail("O .cpd não pôde ser carregado no dispositivo selecionado.")
    if not hil.start_simulation():
        raise fail("A simulação não pôde ser iniciada.")

    rows: list[dict[str, float]] = []
    start = time.perf_counter()
    try:
        hil.wait_msec(100)
        print(f"[3/5] Adquirindo {duration:.1f} s dos probes: {', '.join(SIGNALS)}")
        while True:
            now = time.perf_counter()
            elapsed = now - start
            if elapsed >= duration:
                break
            values = hil.read_analog_signals(signals=list(SIGNALS))
            if values is None or len(values) != len(SIGNALS):
                raise fail(
                    "Não foi possível ler todos os probes. Confirme os nomes "
                    "dos sinais e se o modelo correto está carregado."
                )
            row = {"tempo_s": elapsed}
            row.update({name: float(value) for name, value in zip(SIGNALS, values)})
            rows.append(row)
            hil.wait_msec(interval_ms)
    finally:
        hil.stop_simulation()
    return rows


def read_standard_csv(path: Path) -> list[dict[str, float]]:
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise fail("O CSV não possui cabeçalho.")
        missing = [name for name in ("tempo_s", *SIGNALS) if name not in reader.fieldnames]
        if missing:
            raise fail(
                "O CSV deve usar o formato padronizado deste pacote. "
                f"Colunas ausentes: {', '.join(missing)}"
            )
        rows = []
        for csv_row in reader:
            rows.append({name: float(csv_row[name]) for name in ("tempo_s", *SIGNALS)})
    return rows


def write_csv(path: Path, rows: Iterable[dict[str, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("tempo_s", *SIGNALS))
        writer.writeheader()
        for row in rows:
            writer.writerow({name: f"{float(row[name]):.9f}" for name in writer.fieldnames})


def decimal_comma(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def write_tex(
    path: Path,
    summary: dict[str, object],
    metadata: dict[str, object],
    fits: Sequence[FitResult],
) -> None:
    status = "APROVADA" if summary["passed"] else "REPROVADA"
    acquired_tex = r"\allowbreak\ ".join(
        rf"\mbox{{{part}}}" for part in str(metadata["acquired_at"]).split()
    )
    lines = [
        "% Gerado automaticamente por executar_validacao_vhil.py.",
        "% A presença deste arquivo indica que houve aquisição pela API do Typhoon.",
        rf"\newcommand{{\DataAquisicaoVHIL}}{{{acquired_tex}}}",
        rf"\newcommand{{\NumeroAmostrasVHIL}}{{{summary['sample_count']}}}",
        rf"\newcommand{{\PexpVHIL}}{{{decimal_comma(float(summary['p_hat']))}}}",
        rf"\newcommand{{\KexpVHIL}}{{{decimal_comma(float(summary['k_hat']))}}}",
        rf"\newcommand{{\DeltaPexpVHIL}}{{{decimal_comma(float(summary['delta_p']))}}}",
        rf"\newcommand{{\DeltaKexpVHIL}}{{{decimal_comma(float(summary['delta_k']))}}}",
        rf"\newcommand{{\PexpVHILnum}}{{{float(summary['p_hat']):.6f}}}",
        rf"\newcommand{{\KexpVHILnum}}{{{float(summary['k_hat']):.6f}}}",
        rf"\newcommand{{\XminVHIL}}{{{decimal_comma(float(summary['x_min']))}}}",
        rf"\newcommand{{\XmaxVHIL}}{{{decimal_comma(float(summary['x_max']))}}}",
        rf"\newcommand{{\StatusValidacaoVHIL}}{{{status}}}",
        rf"\newcommand{{\HashModeloVHIL}}{{{metadata['model_sha256'][:12]}}}",
    ]
    prefixes = {
        "Saida_ideal": "ideal",
        "Saida_desvio_zero": "zero",
        "Saida_sensibilidade": "sens",
        "Saida_real": "real",
        "Erro_total": "erro",
    }
    for item in fits:
        prefix = prefixes[item.signal]
        lines.append(
            rf"\newcommand{{\P{prefix}VHIL}}{{{decimal_comma(item.intercept)}}}"
        )
        lines.append(
            rf"\newcommand{{\K{prefix}VHIL}}{{{decimal_comma(item.slope)}}}"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(path: Path, fits: Sequence[FitResult], summary: dict[str, object], metadata: dict[str, object]) -> None:
    status = "APROVADA" if summary["passed"] else "REPROVADA"
    lines = [
        "VALIDAÇÃO EXPERIMENTAL - INSTRUMENTO ESTÁTICO",
        "=" * 49,
        f"Aquisição: {metadata['acquired_at']}",
        f"Origem: {metadata['source']}",
        f"Modelo: {metadata['model_name']}",
        f"SHA-256 do modelo: {metadata['model_sha256']}",
        f"Amostras: {summary['sample_count']}",
        f"Faixa de x: {summary['x_min']:.6f} a {summary['x_max']:.6f}",
        "",
        f"p_hat = {summary['p_hat']:.6f} (esperado: {P_EXPECTED:.6f})",
        f"K_hat = {summary['k_hat']:.6f} (esperado: {K_EXPECTED:.6f})",
        f"Delta p = p_hat - p0 = {summary['delta_p']:.6f}",
        f"Delta K = K_hat - K0 = {summary['delta_k']:.6f}",
        f"Resultado: {status}",
        "",
        "AJUSTES POR CANAL",
    ]
    for item in fits:
        lines.append(
            f"{item.signal}: intercepto={item.intercept:.6f}; "
            f"inclinação={item.slope:.6f}; RMSE={item.rmse:.3e}; "
            f"resíduo_máx={item.max_abs_residual:.3e}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def persist_results(
    output_dir: Path,
    rows: Sequence[dict[str, float]],
    fits: Sequence[FitResult],
    summary: dict[str, object],
    metadata: dict[str, object],
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "dados_vhil.csv"
    json_path = output_dir / "resultados_vhil.json"
    tex_path = output_dir / "resultados_experimentais.tex"
    txt_path = output_dir / "resumo_validacao.txt"
    write_csv(csv_path, rows)
    payload = {
        "metadata": metadata,
        "summary": summary,
        "fits": [asdict(item) for item in fits],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_tex(tex_path, summary, metadata, fits)
    write_summary(txt_path, fits, summary, metadata)
    return [csv_path, json_path, tex_path, txt_path]


def mirror_to_report(files: Sequence[Path], report_dir: Path | None) -> None:
    if report_dir is None:
        return
    report_dir.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, report_dir / path.name)
    print(f"[5/5] Dados copiados para o relatório: {report_dir}")


def self_test_rows() -> list[dict[str, float]]:
    rows = []
    for index in range(601):
        elapsed = index * 0.02
        x_value = elapsed % 10.0
        rows.append(
            {
                "tempo_s": elapsed,
                "Entrada_x": x_value,
                "Saida_ideal": x_value,
                "Saida_desvio_zero": x_value + 0.5,
                "Saida_sensibilidade": 1.2 * x_value,
                "Saida_real": 0.5 + 1.2 * x_value,
                "Erro_total": 0.5 + 0.2 * x_value,
            }
        )
    return rows


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Compila, executa e valida o instrumento estático no VHIL."
    )
    parser.add_argument("--tse", type=Path, default=root / "instrumento_estatico_generico.tse")
    parser.add_argument("--cpd", type=Path, help="Usa um .cpd existente e ignora a compilação.")
    parser.add_argument("--csv", type=Path, help="Analisa um dados_vhil.csv já adquirido.")
    parser.add_argument("--output-dir", type=Path, default=root / "resultados_vhil")
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=root / "Relatorio_Instrumento_Estatico_Revisado" / "resultados_vhil",
        help="Pasta do relatório para a qual os resultados serão copiados.",
    )
    parser.add_argument("--duration", type=float, default=11.5)
    parser.add_argument("--interval-ms", type=int, default=20)
    parser.add_argument("--physical-hil", action="store_true")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Testa somente a análise com dados sintéticos; não vale como evidência experimental.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parent
    source = "Typhoon HIL API - Virtual HIL"

    if args.self_test:
        rows = self_test_rows()
        source = "AUTOTESTE SINTÉTICO - NÃO É EVIDÊNCIA EXPERIMENTAL"
        model_path = args.tse.resolve()
        output_dir = args.output_dir.resolve()
        report_dir = None
    elif args.csv:
        rows = read_standard_csv(args.csv.resolve())
        source = f"CSV adquirido previamente: {args.csv.resolve()}"
        model_path = args.tse.resolve()
        output_dir = args.output_dir.resolve()
        report_dir = args.report_dir.resolve() if args.report_dir else None
    else:
        model_path = args.tse.resolve()
        if not model_path.exists():
            raise fail(f"Modelo não encontrado: {model_path}")
        cpd_path = args.cpd.resolve() if args.cpd else compile_model(model_path)
        if args.cpd and not cpd_path.exists():
            raise fail(f"Arquivo compilado não encontrado: {cpd_path}")
        rows = acquire(cpd_path, args.duration, args.interval_ms, args.physical_hil)
        source = "Typhoon HIL API - HIL físico" if args.physical_hil else source
        output_dir = args.output_dir.resolve()
        report_dir = args.report_dir.resolve() if args.report_dir else None

    print("[4/5] Estimando interceptos, inclinacoes, Delta p e Delta K.")
    fits, summary = analyse(rows)
    acquired_at = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S %z")
    metadata = {
        "acquired_at": acquired_at,
        "source": source,
        "model_name": model_path.name,
        "model_sha256": sha256(model_path) if model_path.exists() else "indisponível",
        "script_name": Path(__file__).name,
    }
    files = persist_results(output_dir, rows, fits, summary, metadata)
    mirror_to_report(files, report_dir)

    status = "APROVADA" if summary["passed"] else "REPROVADA"
    print(f"p_hat={summary['p_hat']:.6f}; K_hat={summary['k_hat']:.6f}")
    print(f"Delta p={summary['delta_p']:.6f}; Delta K={summary['delta_k']:.6f}")
    print(f"Resultado={status}; arquivos={output_dir}")
    if args.self_test:
        print("ATENCAO: o autoteste nao substitui a execucao no TyphoonSim/VHIL.")
    return 0 if summary["passed"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
