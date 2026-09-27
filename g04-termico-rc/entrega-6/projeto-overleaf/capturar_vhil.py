"""Compila e captura AM no TyphoonSim/Virtual HIL sem polling subamostrado.

Executar no computador que possui o Typhoon HIL Control Center:
    typhoon-python capturar_vhil.py

A captura usa a API de Capture a 10 kS/s. O CSV resultante contem somente
amostras efetivamente retornadas pelo TyphoonSim, nunca dados sinteticos.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "Equipe_04_ModulacaoAM.tse"
SIGNALS = (
    "mensagem_norm",
    "portadora",
    "indice_modulacao",
    "envoltoria_assinada",
    "sinal_am",
)
SAMPLE_COUNT = 36000
EXPECTED_DT = 0.0001


def choose_decimation(sim_step: float, target_dt: float = EXPECTED_DT) -> tuple[int, float]:
    """Escolhe a decimacao do Capture a partir do passo-base do modelo carregado."""
    if not math.isfinite(sim_step) or sim_step <= 0:
        raise RuntimeError(f"Passo-base de simulacao invalido: {sim_step!r}.")
    decimation = max(1, round(target_dt / sim_step))
    actual_dt = decimation * sim_step
    if abs(actual_dt - target_dt) > 0.02 * target_dt:
        raise RuntimeError(
            f"O passo-base {sim_step:.9g} s nao permite Capture a 100 us "
            f"(decimacao inteira mais proxima: {decimation}; passo: {actual_dt:.9g} s)."
        )
    return decimation, actual_dt


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compile_model(model_path: Path) -> Path:
    try:
        from typhoon.api.schematic_editor import model
    except ImportError as exc:
        raise RuntimeError(
            "API Typhoon ausente. Execute com typhoon-python no PC do Typhoon HIL."
        ) from exc

    print(f"[1/4] Abrindo e compilando {model_path.name} ...", flush=True)
    model.load(str(model_path))
    try:
        if not model.compile():
            raise RuntimeError("Compilacao falhou. Abra o .tse no Schematic Editor e leia o log.")
        cpd = Path(model.get_compiled_model_file(str(model_path))).resolve()
    finally:
        close = getattr(model, "close_model", None)
        if callable(close):
            close()
    if not cpd.is_file():
        raise RuntimeError(f".cpd compilado nao encontrado: {cpd}")
    return cpd


def flatten_signal_list(value: object) -> list[str]:
    result: list[str] = []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        for item in value:
            result.extend(flatten_signal_list(item))
    return result


def capture(cpd: Path, timeout_s: float) -> tuple[list[dict[str, float]], dict[str, object]]:
    try:
        import typhoon.api.hil as hil
    except ImportError as exc:
        raise RuntimeError("API HIL ausente. Execute com typhoon-python.") from exc

    print("[2/4] Carregando modelo em TyphoonSim/Virtual HIL ...", flush=True)
    if not hil.load_model(file=str(cpd), vhil_device=True):
        raise RuntimeError("Nao foi possivel carregar o .cpd em Virtual HIL.")

    available = set(flatten_signal_list(hil.get_analog_signals()))
    missing = set(SIGNALS) - available
    if missing:
        raise RuntimeError(
            f"Probes indisponiveis: {sorted(missing)}. Disponiveis: {sorted(available)}"
        )

    version = hil.get_sw_product_and_ver() if hasattr(hil, "get_sw_product_and_ver") else "nao informado"
    buffer: list[object] = []
    started = False
    try:
        if not hil.start_simulation():
            raise RuntimeError("A simulacao nao iniciou.")
        started = True
        raw_sim_step = hil.get_sim_step()
        if raw_sim_step is None:
            raise RuntimeError("A API nao informou o passo-base do modelo ativo.")
        sim_step = float(raw_sim_step)
        decimation, requested_dt = choose_decimation(sim_step)
        print(
            f"[3/4] Passo-base = {sim_step:.9g} s; decimacao Capture = {decimation}; "
            f"passo previsto = {requested_dt:.9g} s. "
            f"Capturando {SAMPLE_COUNT} amostras de cinco probes ...",
            flush=True,
        )
        ok = hil.start_capture(
            [decimation, len(SIGNALS), SAMPLE_COUNT],
            ["Forced"],
            list(SIGNALS),
            dataBuffer=buffer,
        )
        if not ok:
            raise RuntimeError("start_capture retornou falha; veja o log do Typhoon.")

        started_wall = time.monotonic()
        while hil.capture_in_progress():
            elapsed = time.monotonic() - started_wall
            if elapsed > timeout_s:
                hil.stop_capture()
                raise RuntimeError(
                    f"A captura nao terminou apos {timeout_s:.0f} s de relogio. "
                    "Confirme que a simulacao esta rodando, confira os probes e "
                    "aumente --timeout se o VHIL estiver lento."
                )
            time.sleep(0.05)

        if not buffer:
            raise RuntimeError("Capture terminou, mas nao retornou buffer de amostras.")
        signal_names, y_matrix, x_data = buffer[0]
        signal_names = [str(name) for name in signal_names]
        index = {name: i for i, name in enumerate(signal_names)}
        if set(SIGNALS) - set(index):
            raise RuntimeError(f"Buffer veio com sinais inesperados: {signal_names}")

        times = [float(value) for value in x_data]
        if len(times) < SAMPLE_COUNT - 10:
            raise RuntimeError(
                f"Captura incompleta: {len(times)} amostras; esperado {SAMPLE_COUNT}."
            )
        rows: list[dict[str, float]] = []
        for i, timestamp in enumerate(times):
            row = {"tempo_s": timestamp}
            for name in SIGNALS:
                row[name] = float(y_matrix[index[name]][i])
            rows.append(row)

        dts = [b - a for a, b in zip(times, times[1:])]
        dt = statistics.median(dts)
        if not (0.98 * EXPECTED_DT <= dt <= 1.02 * EXPECTED_DT):
            raise RuntimeError(
                f"Passo da captura = {dt:.9g} s, mas o projeto requer 100 us. "
                "Nao substitua Capture por leitura por polling."
            )
        if max(abs(x - dt) for x in dts) > 0.02 * EXPECTED_DT:
            raise RuntimeError("Tempos de captura nao uniformes; FFT nao confiavel.")

        max_model_error = max(
            max(
                abs(row["envoltoria_assinada"] - (1 + row["indice_modulacao"] * row["mensagem_norm"])),
                abs(row["sinal_am"] - row["envoltoria_assinada"] * row["portadora"]),
            )
            for row in rows
        )
        if max_model_error > 1e-4:
            raise RuntimeError(
                f"As saidas nao obedecem a identidade AM (erro {max_model_error:.6g}). "
                "Confira alinhamento dos sinais no Capture."
            )
        regimes = {round(row["indice_modulacao"], 1) for row in rows}
        if regimes != {0.5, 1.0, 1.5}:
            raise RuntimeError(f"Indices capturados incompletos: {sorted(regimes)}")
        if not all(math.isfinite(value) for row in rows for value in row.values()):
            raise RuntimeError("A captura contem valor nao finito.")

        info = {
            "origem": "TyphoonSim/Virtual HIL; API hil.start_capture",
            "data_hora_captura": datetime.now().astimezone().isoformat(timespec="seconds"),
            "software_typhoon": str(version),
            "passo_simulacao_s": sim_step,
            "decimacao_capture": decimation,
            "passo_solicitado_captura_s": requested_dt,
            "passo_captura_s": dt,
            "taxa_captura_hz": 1.0 / dt,
            "amostras": len(rows),
            "sinais": list(SIGNALS),
            "indices_presentes": sorted(regimes),
            "erro_max_identidade_am": max_model_error,
        }
        return rows, info
    finally:
        if started:
            hil.stop_simulation()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=300.0, help="Limite de espera da captura, em segundos reais.")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout deve ser positivo")

    cpd = compile_model(MODEL)
    rows, info = capture(cpd, args.timeout)
    target = ROOT / "capturas" / datetime.now().strftime("captura_%Y%m%d_%H%M%S")
    target.mkdir(parents=True, exist_ok=False)
    data = target / "Equipe_04_ModulacaoAM_captura.csv"
    metadata = target / "Equipe_04_ModulacaoAM_metadados.json"
    with data.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("tempo_s", *SIGNALS))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: f"{value:.12g}" for key, value in row.items()})
    info.update({
        "arquivo_dados": data.name,
        "sha256_dados": sha256(data),
        "arquivo_modelo": MODEL.name,
        "sha256_modelo": sha256(MODEL),
        "arquivo_compilado": cpd.name,
        "sha256_compilado": sha256(cpd),
    })
    metadata.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[4/4] Captura salva: {data}", flush=True)
    print(f"Metadados: {metadata}", flush=True)
    print("Proximo passo: typhoon-python analisar_captura.py <pasta-da-captura>", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
