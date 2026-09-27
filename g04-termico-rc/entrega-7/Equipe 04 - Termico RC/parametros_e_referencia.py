"""Caracterizacao reprodutivel do RC termico do IGBT Infineon IKD04N60RF.

Os quatro pares r_i/tau_i vem da Fig. 21 do datasheet oficial, v2.6.
Este programa reduz o modelo de Foster a dois estados e gera resultados
analiticos/de referencia. Ele NAO gera nem se apresenta como dado TyphoonSim.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "referencia_analitica"
DATASHEET = (
    "https://www.infineon.com/dgdl/Infineon-IKD04N60RF-DS-v02_06-EN.pdf"
    "?fileId=db3a30433c5c92fb013c5d6c806d00dc"
)
R_MANUFACTURER = (0.492466, 0.884411, 0.589157, 0.073673)  # K/W
TAU_MANUFACTURER = (0.000200, 0.000540, 0.002100, 0.031658)  # s
MODEL_R = (1.116866866999197, 0.922840133000803)  # K/W; no .tse
MODEL_TAU = (0.0002878723810835251, 0.002021156766960753)  # s; no .tse
CASE_TEMP_C = 25.0
POWER_W = 10.0
SAMPLE_TIME_S = 10e-6
END_TIME_S = 0.25
PULSE_END_S = 0.05


def impedance(t: float, r: tuple[float, ...], tau: tuple[float, ...]) -> float:
    return sum(ri * (-math.expm1(-t / ti)) for ri, ti in zip(r, tau))


def times_logarithmic(n: int = 240) -> list[float]:
    lower, upper = math.log10(1e-5), math.log10(0.25)
    return [10 ** (lower + (upper - lower) * i / (n - 1)) for i in range(n)]


def fit_two_poles() -> tuple[float, float, float, float, dict[str, float]]:
    """Minimos quadrados relativos, com ganho DC igual ao do datasheet."""
    times = times_logarithmic()
    target = [impedance(t, R_MANUFACTURER, TAU_MANUFACTURER) for t in times]
    total_r = sum(R_MANUFACTURER)
    best: tuple[float, float, float, float] | None = None
    center_a, center_b = -3.4, -2.2
    step = 0.08

    for pass_number in range(3):
        if pass_number == 0:
            a_values = [-5.0 + i * 0.08 for i in range(39)]
            b_values = [-3.2 + i * 0.08 for i in range(32)]
        else:
            step /= 5.0
            a_values = [center_a + i * step for i in range(-12, 13)]
            b_values = [center_b + i * step for i in range(-12, 13)]

        for log_tau_fast in a_values:
            tau_fast = 10 ** log_tau_fast
            g_fast = [-math.expm1(-t / tau_fast) for t in times]
            for log_tau_slow in b_values:
                tau_slow = 10 ** log_tau_slow
                if tau_slow <= 1.5 * tau_fast:
                    continue
                g_slow = [-math.expm1(-t / tau_slow) for t in times]
                numerator = denominator = 0.0
                for desired, gf, gs in zip(target, g_fast, g_slow):
                    weight = 1.0 / max(desired, 0.02)
                    q = (gf - gs) * weight
                    numerator += q * (desired - total_r * gs) * weight
                    denominator += q * q
                r_fast = min(total_r - 0.01, max(0.01, numerator / denominator))
                r_slow = total_r - r_fast
                errors = [
                    (r_fast * gf + r_slow * gs - desired) / max(desired, 0.02)
                    for desired, gf, gs in zip(target, g_fast, g_slow)
                ]
                objective = sum(error * error for error in errors) / len(errors)
                if best is None or objective < best[0]:
                    best = (objective, r_fast, tau_fast, tau_slow)
                    center_a, center_b = log_tau_fast, log_tau_slow

    assert best is not None
    _, r_fast, tau_fast, tau_slow = best
    r_slow = total_r - r_fast
    relative = [
        abs(impedance(t, (r_fast, r_slow), (tau_fast, tau_slow)) - desired)
        / desired
        for t, desired in zip(times, target)
    ]
    absolute = [
        abs(impedance(t, (r_fast, r_slow), (tau_fast, tau_slow)) - desired)
        for t, desired in zip(times, target)
    ]
    metrics = {
        "fit_t_min_s": times[0],
        "fit_t_max_s": times[-1],
        "fit_rms_rel_percent": 100 * math.sqrt(sum(x * x for x in relative) / len(relative)),
        "fit_max_rel_percent": 100 * max(relative),
        "fit_max_abs_k_per_w": max(absolute),
    }
    return r_fast, r_slow, tau_fast, tau_slow, metrics


def exact_state(t: float, power_on_s: float, power_off_s: float | None,
                r: tuple[float, float], tau: tuple[float, float]) -> tuple[float, float]:
    if t < power_on_s:
        return 0.0, 0.0
    if power_off_s is None or t <= power_off_s:
        return tuple(POWER_W * ri * (-math.expm1(-(t - power_on_s) / ti))
                     for ri, ti in zip(r, tau))  # type: ignore[return-value]
    return tuple(
        POWER_W * ri * (-math.expm1(-(power_off_s - power_on_s) / ti))
        * math.exp(-(t - power_off_s) / ti)
        for ri, ti in zip(r, tau)
    )  # type: ignore[return-value]


def step_power(t: float) -> float:
    return POWER_W


def pulse_power(t: float) -> float:
    return POWER_W if t < PULSE_END_S else 0.0


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def simulate_zoh(r: tuple[float, float], tau: tuple[float, float],
                 *, single_precision: bool = False) -> list[tuple[float, float, float]]:
    """Saidas [degrau, relaxacao, pulso] antes da atualizacao de cada amostra."""
    gains = tuple(-math.expm1(-SAMPLE_TIME_S / ti) for ti in tau)
    if single_precision:
        gains = tuple(f32(gain) for gain in gains)
    states = [[0.0, 0.0], [POWER_W * r[0], POWER_W * r[1]], [0.0, 0.0]]
    rows: list[tuple[float, float, float]] = []
    count = round(END_TIME_S / SAMPLE_TIME_S)
    for n in range(count + 1):
        t = n * SAMPLE_TIME_S
        rows.append(tuple(CASE_TEMP_C + sum(pair) for pair in states))
        for pair, power in zip(states, (POWER_W, 0.0, pulse_power(t))):
            for i in range(2):
                new_value = pair[i] + gains[i] * (power * r[i] - pair[i])
                pair[i] = f32(new_value) if single_precision else new_value
    return rows


def rk4_step_reference(r: tuple[float, float], tau: tuple[float, float],
                       dt: float = 1e-6) -> float:
    """Integracao RK4 independente para o degrau de potencia constante."""
    state = [0.0, 0.0]
    steps = round(END_TIME_S / dt)
    maximum_error = 0.0
    for n in range(steps + 1):
        if n % 100 == 0:
            expected = POWER_W * impedance(n * dt, r, tau)
            maximum_error = max(maximum_error, abs(sum(state) - expected))
        if n == steps:
            break
        for i in range(2):
            target = POWER_W * r[i]
            k1 = (target - state[i]) / tau[i]
            k2 = (target - (state[i] + 0.5 * dt * k1)) / tau[i]
            k3 = (target - (state[i] + 0.5 * dt * k2)) / tau[i]
            k4 = (target - (state[i] + dt * k3)) / tau[i]
            state[i] += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
    return maximum_error


def save_csv(path: Path, names: tuple[str, ...], rows: list[tuple[float, ...]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(names)
        writer.writerows([[f"{value:.12g}" for value in row] for row in rows])


def main() -> None:
    OUT.mkdir(exist_ok=True)
    r_fast, r_slow, tau_fast, tau_slow, fit_metrics = fit_two_poles()
    r = (r_fast, r_slow)
    tau = (tau_fast, tau_slow)
    if max(abs(a - b) for a, b in zip(r, MODEL_R)) > 1e-8 or max(
        abs(a - b) for a, b in zip(tau, MODEL_TAU)
    ) > 1e-9:
        raise RuntimeError("O ajuste mudou; atualize os coeficientes do .tse antes de prosseguir.")
    poles = (-1.0 / tau_fast, -1.0 / tau_slow)
    omega_n = 1.0 / math.sqrt(tau_fast * tau_slow)
    zeta = (tau_fast + tau_slow) / (2.0 * math.sqrt(tau_fast * tau_slow))
    coarse = simulate_zoh(r, tau)
    single = simulate_zoh(r, tau, single_precision=True)
    count = round(END_TIME_S / SAMPLE_TIME_S)
    max_zoh_error = max(
        abs(coarse[n][0] - CASE_TEMP_C - POWER_W * impedance(n * SAMPLE_TIME_S, r, tau))
        for n in range(count + 1)
    )
    max_f32_error = max(abs(a - b) for row_a, row_b in zip(coarse, single)
                        for a, b in zip(row_a, row_b))
    max_rk4_error = rk4_step_reference(r, tau)
    try:
        import numpy as np
        eigenvalues = sorted(float(value.real) for value in np.linalg.eigvals(
            np.array([[poles[0], 0.0], [0.0, poles[1]]], dtype=float)
        ))
        assert all(abs(a - b) < 1e-9 for a, b in zip(eigenvalues, sorted(poles)))
    except ImportError:
        eigenvalues = None
    metrics = {
        "fabricante": "Infineon Technologies",
        "dispositivo": "IKD04N60RF (IGBT; somente ramo termico IGBT juncao-capsula)",
        "fonte": DATASHEET,
        "fonte_figura": "Figura 21, coeficientes Foster de Zth(j-c)",
        "acesso": "2026-09-24",
        "r_fabricante_k_por_w": R_MANUFACTURER,
        "tau_fabricante_s": TAU_MANUFACTURER,
        "r_fabricante_total_k_por_w": sum(R_MANUFACTURER),
        "r_datasheet_max_jc_k_por_w": 2.0,
        "r_reduzido_k_por_w": r,
        "tau_reduzido_s": tau,
        "c_reduzido_j_por_k": (tau_fast / r_fast, tau_slow / r_slow),
        "polos_por_s": poles,
        "autovalores_numpy_por_s": eigenvalues,
        "omega_n_rad_por_s": omega_n,
        "zeta": zeta,
        "ganho_dc_k_por_w": sum(r),
        "temperatura_capsula_c": CASE_TEMP_C,
        "potencia_ensaio_w": POWER_W,
        "temperatura_final_degrau_c": CASE_TEMP_C + POWER_W * sum(r),
        "tempo_amostragem_s": SAMPLE_TIME_S,
        "max_erro_zoh_vs_analitico_k": max_zoh_error,
        "max_erro_f32_vs_f64_k": max_f32_error,
        "max_erro_rk4_vs_analitico_k": max_rk4_error,
        **fit_metrics,
    }
    (OUT / "metricas.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    fit_rows = [
        (t, impedance(t, R_MANUFACTURER, TAU_MANUFACTURER), impedance(t, r, tau))
        for t in times_logarithmic()
    ]
    save_csv(OUT / "ajuste_impedancia.csv",
             ("tempo_s", "zth_fabricante_k_w", "zth_reduzido_k_w"), fit_rows)
    stride = 50
    curve_rows = []
    for n in range(0, count + 1, stride):
        t = n * SAMPLE_TIME_S
        step_exact = CASE_TEMP_C + POWER_W * impedance(t, r, tau)
        relaxation_exact = CASE_TEMP_C + POWER_W * sum(
            ri * math.exp(-t / ti) for ri, ti in zip(r, tau)
        )
        pulse_exact = CASE_TEMP_C + sum(exact_state(t, 0.0, PULSE_END_S, r, tau))
        curve_rows.append((t, step_exact, coarse[n][0], relaxation_exact,
                           coarse[n][1], pulse_exact, coarse[n][2],
                           step_power(t), pulse_power(t)))
    save_csv(OUT / "respostas_referencia.csv",
             ("tempo_s", "degrau_analitico_c", "degrau_zoh_c",
              "relaxacao_analitica_c", "relaxacao_zoh_c", "pulso_analitico_c",
              "pulso_zoh_c", "potencia_degrau_w", "potencia_pulso_w"), curve_rows)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
