"""Gera a entrega bruta da Equipe 04 no TyphoonSim/VHIL.

Execute com o interpretador do Typhoon HIL Control Center 2026.2:

    typhoon-python executar_geracao_dados_equipe_04.py

O script compila o .tse, executa duas varreduras completas e exporta apenas
os valores lidos dos probes. Nenhuma media, filtragem, suavizacao ou ajuste de
curva e aplicado aos dados.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import math
from pathlib import Path
import sys
import time
from typing import Sequence


SIGNALS = (
    "x_referencia",
    "y_instrumento",
    "condicao_id",
    "experimento_concluido",
)

DATA_FILENAME = "Equipe_04_DesvioZeroSensibilidade.csv"
METADATA_FILENAME = "Equipe_04_DesvioZeroSensibilidade_metadados.csv"


def fail(message: str) -> RuntimeError:
    return RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compile_model(tse_path: Path) -> Path:
    try:
        from typhoon.api.schematic_editor import model
    except ImportError as exc:
        raise fail(
            "A API do Typhoon nao foi encontrada. Execute com typhoon-python."
        ) from exc

    print(f"[1/4] Abrindo e compilando {tse_path.name}.")
    model.load(str(tse_path))
    try:
        if not model.compile():
            raise fail("A compilacao do esquematico retornou falha.")
        cpd_path = Path(model.get_compiled_model_file(str(tse_path))).resolve()
    finally:
        close_model = getattr(model, "close_model", None)
        if callable(close_model):
            close_model()

    if not cpd_path.exists():
        raise fail(f"O arquivo compilado nao foi localizado: {cpd_path}")
    return cpd_path


def acquire_raw_data(
    cpd_path: Path,
    interval_ms: int,
    timeout_s: float,
    physical_hil: bool,
) -> list[dict[str, float]]:
    try:
        import typhoon.api.hil as hil
    except ImportError as exc:
        raise fail(
            "A API do Typhoon nao foi encontrada. Execute com typhoon-python."
        ) from exc

    mode = "HIL fisico" if physical_hil else "TyphoonSim/Virtual HIL"
    print(f"[2/4] Carregando o modelo em {mode}.")
    if not hil.load_model(file=str(cpd_path), vhil_device=not physical_hil):
        raise fail("O modelo compilado nao pode ser carregado.")
    if not hil.start_simulation():
        raise fail("A simulacao nao pode ser iniciada.")

    rows: list[dict[str, float]] = []
    start = time.perf_counter()
    next_progress_report = 5.0
    last_sample: dict[str, float] | None = None
    try:
        hil.wait_msec(100)
        print("[3/4] Adquirindo os probes sem qualquer pre-processamento.")
        while True:
            now = time.perf_counter()
            elapsed = now - start
            if elapsed > timeout_s:
                if last_sample is None:
                    detail = "nenhuma amostra recebida"
                else:
                    detail = (
                        f"ultima leitura: condicao={last_sample['condicao_id']:.0f}, "
                        f"x={last_sample['x_referencia']:.4f} V, "
                        f"concluido={last_sample['experimento_concluido']:.0f}"
                    )
                raise fail(
                    "Tempo limite excedido antes de a segunda varredura atingir "
                    f"9,90 V ({detail})."
                )

            values = hil.read_analog_signals(signals=list(SIGNALS))
            if values is None or len(values) != len(SIGNALS):
                raise fail(
                    "Nem todos os probes foram lidos. Confirme o modelo e os nomes dos sinais."
                )

            sample = {name: float(value) for name, value in zip(SIGNALS, values)}
            sample["tempo"] = elapsed
            rows.append(sample)
            last_sample = sample

            condition = int(round(sample["condicao_id"]))
            if elapsed >= next_progress_report:
                print(
                    "  progresso: "
                    f"{elapsed:.1f} s; condicao={condition}; "
                    f"x={sample['x_referencia']:.3f} V"
                )
                next_progress_report += 5.0

            # O criterio principal usa diretamente o requisito experimental:
            # a segunda condicao precisa cobrir a faixa nominal. O probe de
            # termino permanece apenas como informacao diagnostica.
            if condition == 2 and sample["x_referencia"] >= 9.90:
                break

            hil.wait_msec(interval_ms)
    finally:
        hil.stop_simulation()
    return rows


def validate_raw_data(rows: Sequence[dict[str, float]]) -> dict[int, int]:
    if not rows:
        raise fail("Nenhuma amostra foi adquirida.")

    grouped: dict[int, list[dict[str, float]]] = {1: [], 2: []}
    for index, row in enumerate(rows):
        if not all(math.isfinite(float(row[name])) for name in ("tempo", *SIGNALS)):
            raise fail(f"A amostra {index} contem valor nao finito.")
        condition = int(round(row["condicao_id"]))
        if condition not in grouped:
            raise fail(f"Condicao invalida na amostra {index}: {row['condicao_id']}")
        grouped[condition].append(row)

    counts: dict[int, int] = {}
    for condition, samples in grouped.items():
        if len(samples) < 300:
            raise fail(
                f"A condicao {condition} possui apenas {len(samples)} amostras; "
                "a varredura nao esta suficientemente densa."
            )
        x_values = [sample["x_referencia"] for sample in samples]
        if min(x_values) > 0.10 or max(x_values) < 9.90:
            raise fail(
                f"A condicao {condition} nao cobriu a faixa de 0 a 10 V: "
                f"{min(x_values):.4f} a {max(x_values):.4f} V."
            )
        for previous, current in zip(x_values, x_values[1:]):
            if current < previous - 0.05:
                raise fail(
                    f"A entrada da condicao {condition} nao e uma rampa crescente."
                )
        counts[condition] = len(samples)
    return counts


def write_delivery(
    output_dir: Path,
    rows: Sequence[dict[str, float]],
    counts: dict[int, int],
    model_path: Path,
    interval_ms: int,
    source: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / DATA_FILENAME
    metadata_path = output_dir / METADATA_FILENAME

    with data_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("tempo", "x_referencia", "y_instrumento", "condicao"),
        )
        writer.writeheader()
        for row in rows:
            condition = int(round(row["condicao_id"]))
            writer.writerow(
                {
                    "tempo": f"{row['tempo']:.9f}",
                    "x_referencia": f"{row['x_referencia']:.9f}",
                    "y_instrumento": f"{row['y_instrumento']:.9f}",
                    "condicao": f"condicao_{condition}",
                }
            )

    acquired_at = datetime.now().astimezone().isoformat(timespec="seconds")
    metadata = (
        ("campo", "valor"),
        ("nome_da_equipe", "Equipe 04 - Gabriela Pontes; Julia Goncalves; Placido Cordeiro"),
        ("caracteristica_modelada", "Desvio de zero e de sensibilidade"),
        ("unidade_de_x", "V"),
        ("unidade_de_y", "V"),
        ("faixa_nominal", "0 a 10 V"),
        ("condicoes", "condicao_1; condicao_2"),
        ("origem_dos_dados", source),
        ("pre_processamento", "nenhum"),
        ("intervalo_nominal_de_amostragem_ms", str(interval_ms)),
        ("amostras_condicao_1", str(counts[1])),
        ("amostras_condicao_2", str(counts[2])),
        ("data_hora_da_aquisicao", acquired_at),
        ("modelo_tse", model_path.name),
        ("sha256_do_modelo", sha256(model_path)),
    )
    with metadata_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerows(metadata)

    return data_path, metadata_path


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Gera o CSV bruto exigido para a Equipe 04."
    )
    parser.add_argument(
        "--tse",
        type=Path,
        default=root / "Equipe_04_Geracao_Dados_DesvioZeroSensibilidade.tse",
    )
    parser.add_argument("--cpd", type=Path, help="Usa um .cpd ja compilado.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "ENTREGA_AO_PROFESSOR",
    )
    parser.add_argument("--interval-ms", type=int, default=20)
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Limite de tempo de parede; o padrao tolera Virtual HIL lento.",
    )
    parser.add_argument("--physical-hil", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    model_path = args.tse.resolve()
    if not model_path.exists():
        raise fail(f"Modelo nao encontrado: {model_path}")

    cpd_path = args.cpd.resolve() if args.cpd else compile_model(model_path)
    if not cpd_path.exists():
        raise fail(f"Arquivo compilado nao encontrado: {cpd_path}")

    source = "HIL fisico" if args.physical_hil else "TyphoonSim/Virtual HIL"
    rows = acquire_raw_data(
        cpd_path,
        interval_ms=args.interval_ms,
        timeout_s=args.timeout,
        physical_hil=args.physical_hil,
    )
    counts = validate_raw_data(rows)
    print("[4/4] Gravando somente os dados brutos e os metadados exigidos.")
    data_path, metadata_path = write_delivery(
        args.output_dir.resolve(),
        rows,
        counts,
        model_path,
        args.interval_ms,
        source,
    )
    print(f"Dados: {data_path}")
    print(f"Metadados: {metadata_path}")
    print("Nenhuma media, filtragem, suavizacao ou regressao foi aplicada.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
