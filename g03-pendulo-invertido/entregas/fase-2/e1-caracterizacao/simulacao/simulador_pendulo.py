# -*- coding: utf-8 -*-
"""
ECOM060 — Instrumentação Eletrônica (2026.2) — Equipe G03
Fase 2, Entrega 01: Caracterização do Pêndulo Invertido no domínio de origem.

Gera todas as figuras (./figuras/) e os resultados (./resultados/resultados.json
e ./resultados.txt) usados no relatório.

Execução: python caracterizacao_pendulo.py
"""

import os
import math
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch

# ---------------------------------------------------------------------------
# Configuração geral
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figuras")
RES = os.path.join(HERE, "resultados")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "dejavuserif",
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})

RTOL, ATOL = 1e-10, 1e-12
METODO = "DOP853"
LIMITE_DOMINIO = 0.60  # rad
GRAVIDADE = 9.81

linhas_resultado = []

def registrar(texto=""):
    print(texto)
    linhas_resultado.append(texto)

def salvar_figura(nome):
    caminho = os.path.join(FIG, nome)
    plt.savefig(caminho, dpi=200, bbox_inches="tight")
    plt.close()
    return caminho

def virgula(texto):
    return texto.replace(".", ",")

# ---------------------------------------------------------------------------
# Parâmetros nominais
# ---------------------------------------------------------------------------
P = dict(m=0.50, l=1.00, b=0.05, g=GRAVIDADE)

def J(p):   return p["m"] * p["l"] ** 2
def mgl(p): return p["m"] * p["g"] * p["l"]

def criar_parametros(massa=P["m"], comprimento=P["l"], atrito=P["b"]):
    return {"m": massa, "l": comprimento, "b": atrito, "g": GRAVIDADE}

# ---------------------------------------------------------------------------
# Dinâmica não linear
# ---------------------------------------------------------------------------
def rhs(t, x, p, u):
    return [x[1],
            p["g"] / p["l"] * np.sin(x[0])
            - p["b"] / J(p) * x[1]
            + u(t) / J(p)]

def simular(x0, u, p=P, T=5.0, n=2001, metodo=METODO, rtol=RTOL, atol=ATOL):
    t = np.linspace(0, T, n)
    s = solve_ivp(rhs, (0, T), x0, method=metodo, t_eval=t,
                  args=(p, u), rtol=rtol, atol=atol)
    return s.t, s.y

# ---------------------------------------------------------------------------
# Análise algébrica
# ---------------------------------------------------------------------------
def autovalores_topo(p):
    a = p["g"] / p["l"]
    c = p["b"] / J(p)
    d = math.sqrt(c * c + 4 * a)
    return (-c + d) / 2, (-c - d) / 2

def parametros_base(p):
    wn = math.sqrt(mgl(p) / J(p))
    sigma = p["b"] / (2 * J(p))
    zeta = sigma / wn
    if zeta < 1:
        wd = wn * math.sqrt(1 - zeta ** 2)
        Mp = math.exp(-math.pi * zeta / math.sqrt(1 - zeta ** 2))
        ts2 = 4 / (zeta * wn)
    else:
        wd = float("nan")
        Mp = 0.0
        ts2 = 4 / (sigma - math.sqrt(sigma ** 2 - wn ** 2))
    return {"wn": wn, "sigma": sigma, "zeta": zeta, "wd": wd,
            "Mp": Mp, "ts2": ts2, "K": 1 / mgl(p)}

def resposta_linear_topo(p, th0, w0, u0, t):
    """Solução fechada de Jθ'' + bθ' - mgL θ = u0 (constante)."""
    pp, pm = autovalores_topo(p)
    th_p = -u0 / mgl(p)
    d0 = th0 - th_p
    A = (w0 - pm * d0) / (pp - pm)
    B = d0 - A
    return th_p + A * np.exp(pp * t) + B * np.exp(pm * t)

def resposta_linear_base(p, d0, u0, t):
    """Solução fechada de δ = θ-π em torno de θ=π, para u0 constante."""
    q = parametros_base(p)
    if q["zeta"] < 1:
        return (u0 * q["K"] * (1 - np.exp(-q["sigma"] * t)
                * (np.cos(q["wd"] * t) + q["sigma"] / q["wd"] * np.sin(q["wd"] * t)))
                + d0 * np.exp(-q["sigma"] * t)
                * (np.cos(q["wd"] * t) + q["sigma"] / q["wd"] * np.sin(q["wd"] * t)))
    else:
        s1 = -q["sigma"] + math.sqrt(q["sigma"] ** 2 - q["wn"] ** 2)
        s2 = -q["sigma"] - math.sqrt(q["sigma"] ** 2 - q["wn"] ** 2)
        return u0 * q["K"] * (1 + (s2 * np.exp(s1 * t) - s1 * np.exp(s2 * t)) / (s1 - s2)) \
             + d0 * (s1 * np.exp(s2 * t) - s2 * np.exp(s1 * t)) / (s1 - s2)

# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------
def instante_saida_dominio(t, th, lim=LIMITE_DOMINIO, ref=0.0):
    for k in range(1, len(t)):
        if abs(th[k] - ref) >= lim:
            a, b = abs(th[k - 1] - ref), abs(th[k] - ref)
            return t[k - 1] + (lim - a) / (b - a) * (t[k] - t[k - 1])
    return float("nan")

def picos_locais(t, y):
    return [(t[k], y[k]) for k in range(1, len(y) - 1)
            if y[k] > y[k - 1] and y[k] >= y[k + 1]]

# ---------------------------------------------------------------------------
# FIGURA 1 — Diagrama de blocos (estilo diagrama.py, completo)
# ---------------------------------------------------------------------------
def figura_diagrama_blocos():
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 44)
    ax.axis("off")

    def box(x, y, w, h, txt, fs=12):
        ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=1.5))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs)

    def arr(p, q, **k):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13,
                                     lw=1.4, color="k", **k))

    def line(xs, ys):
        ax.plot(xs, ys, "k", lw=1.4)

    def somador(x, y):
        ax.add_patch(Circle((x, y), 2.4, fill=False, lw=1.5))
        ax.text(x, y, r"$\Sigma$", ha="center", va="center", fontsize=12)

    yc = 32
    somador(30, yc)
    arr((4, yc), (27.6, yc));   ax.text(4, yc + 2.5, r"$u(t)\ [\mathrm{N\cdot m}]$", fontsize=11)
    arr((30, 43), (30, yc + 2.6)); ax.text(31, 41, r"$d(t)\ [\mathrm{N\cdot m}]$", fontsize=11)
    box(40, yc - 5, 10, 10, r"$1/J$")
    arr((32.4, yc), (40, yc))
    arr((50, yc), (60, yc));    ax.text(51, yc + 6, r"$\ddot{\theta}\ [\mathrm{rad/s^2}]$", fontsize=10)
    box(60, yc - 5, 10, 10, r"$\int$")
    arr((70, yc), (82, yc));    ax.text(71.5, yc + 6, r"$\dot{\theta}\ [\mathrm{rad/s}]$", fontsize=10)
    box(82, yc - 5, 10, 10, r"$\int$")
    arr((92, yc), (99, yc));    ax.text(91, yc + 6, r"$\theta\ [\mathrm{rad}]$", fontsize=10)

    # realimentação do atrito
    line([76, 76], [yc, 19])
    ax.plot(76, yc, "ko", ms=4)
    arr((76, 19), (66, 19))
    box(52, 14, 14, 10, r"$b$"); ax.text(59, 11.5, "atrito viscoso", ha="center", fontsize=10, style="italic")
    line([52, 30], [19, 19])
    arr((30, 19), (30, 29.5)); ax.text(31.2, 24.5, "$-$", fontsize=18)

    # realimentação da gravidade
    line([96, 96], [yc, 5])
    ax.plot(96, yc, "ko", ms=4)
    arr((96, 5), (80, 5))
    box(60, 0.5, 20, 9.5, r"$m g l\,\sin(\cdot)$")
    ax.text(70, -2.5, "torque gravitacional (desestabilizante)", ha="center", fontsize=10, style="italic")
    line([60, 22], [5, 5])
    line([22, 22], [5, 26])
    arr((22, 26), (28.3, 30.3)); ax.text(18, 18, "$+$", fontsize=18)

    ax.set_title("Diagrama de blocos da dinâmica não linear do pêndulo invertido",
                 fontsize=12, pad=8)
    salvar_figura("fig-01-diagrama-blocos.png")


# ---------------------------------------------------------------------------
# FIGURA 2 — Retrato de fase
# ---------------------------------------------------------------------------
def figura_retrato_fase(p=P, lim=LIMITE_DOMINIO):
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    th = np.linspace(-1.2 * np.pi, 1.2 * np.pi, 41)
    w = np.linspace(-8, 8, 41)
    TH, W = np.meshgrid(th, w)
    dTH = W
    dW = (p["g"] / p["l"]) * np.sin(TH) - (p["b"] / J(p)) * W
    ax.streamplot(th, w, dTH, dW, density=1.15, color="0.55",
                  linewidth=0.7, arrowsize=0.85)
    ax.plot([0], [0], "o", color="tab:red", ms=8, label=r"$\theta=0$ (sela, instável)")
    ax.plot([-np.pi, np.pi], [0, 0], "s", color="tab:blue", ms=7,
            label=r"$\theta=\pm\pi$ (foco estável)")
    ax.axvspan(-lim, lim, color="tab:orange", alpha=0.12,
               label=virgula(r"domínio |θ| ≤ %g rad" % lim))
    ax.set_xlabel(r"$\theta$ (rad)")
    ax.set_ylabel(r"$\omega$ (rad/s)")
    ax.set_title(r"Retrato de fase em malha aberta ($\tau=0$)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_xlim(-1.2 * np.pi, 1.2 * np.pi)
    salvar_figura("fig-02-retrato-fase.png")


# ---------------------------------------------------------------------------
# FIGURA 3 — Degrau a partir do equilíbrio
# ---------------------------------------------------------------------------
def figura_degrau(p=P, u0=0.05, T=3.0):
    t, y = simular([0.0, 0.0], lambda t: u0, p=p, T=T, n=6001)
    t_lin = resposta_linear_topo(p, 0.0, 0.0, u0, t)
    t_saida = instante_saida_dominio(t, y[0])
    # Fallback: se não saiu do domínio, usa o tempo final
    if math.isnan(t_saida):
        t_saida = T

    fig, ax = plt.subplots(figsize=(7.5, 3.9))
    ax.plot(t, y[0], label="modelo não linear")
    ax.plot(t, t_lin, "--", label="linearização local (referência)")
    ax.axhline(LIMITE_DOMINIO, color="0.4", ls=":", lw=1)
    ax.text(0.05, LIMITE_DOMINIO + 0.02, virgula("limite 0,60 rad"), fontsize=8, color="0.3")
    ax.plot([t_saida], [LIMITE_DOMINIO], "o", color="tab:red")
    ax.annotate(virgula("saída do domínio\nt = %.3f s" % t_saida),
                xy=(t_saida, LIMITE_DOMINIO),
                xytext=(t_saida - 0.55, 0.85), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xlim(0, max(t_saida + 0.15, 0.5))
    ax.set_ylim(-0.02, max(1.1, y[0].max() + 0.1))
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel(r"$\theta$ (rad)")
    ax.set_title(virgula("Degrau τ = %g N·m, θ(0)=0, ω(0)=0" % u0))
    ax.legend(loc="upper left", fontsize=8)
    ax.text(0.99, 0.02, "DOP853 | rtol=1e-10, atol=1e-12",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color="0.35")
    salvar_figura("fig-03-degrau.png")
    return t_saida


# ---------------------------------------------------------------------------
# FIGURA 4 — Condição inicial não nula
# ---------------------------------------------------------------------------
def figura_condicao_inicial(p=P, th0=0.30, T=2.0):
    t, y = simular([th0, 0.0], lambda t: 0.0, p=p, T=T, n=4001)
    t_lin = resposta_linear_topo(p, th0, 0.0, 0.0, t)
    t_saida = instante_saida_dominio(t, y[0])
    if math.isnan(t_saida):
        t_saida = T

    erro = np.abs(y[0] - t_lin)
    erro_max = float(erro.max())

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(7.5, 5.8), sharex=True,
                                     gridspec_kw={"height_ratios": [2, 1]})
    ax_a.plot(t, y[0], label="modelo não linear")
    ax_a.plot(t, t_lin, "--", label="linearização local (referência)")
    ax_a.axhline(LIMITE_DOMINIO, color="0.4", ls=":", lw=1)
    ax_a.plot([t_saida], [LIMITE_DOMINIO], "o", color="tab:red")
    ax_a.annotate(virgula("saída do domínio\nt = %.3f s" % t_saida),
                  xy=(t_saida, LIMITE_DOMINIO),
                  xytext=(t_saida - 0.25, 0.75), fontsize=8,
                  arrowprops=dict(arrowstyle="->", lw=0.8))
    ax_a.set_ylabel(r"$\theta$ (rad)")
    ax_a.set_title(virgula("Condição inicial θ(0) = %g rad, ω(0)=0, τ=0" % th0))
    ax_a.legend(loc="upper left", fontsize=8)
    ax_a.set_xlim(0, max(t_saida + 0.05, 0.5))
    ax_a.set_ylim(min(y[0].min(), t_lin.min()) - 0.02,
                  max(y[0].max(), t_lin.max()) + 0.05)

    ax_b.plot(t, erro, color="tab:green")
    ax_b.set_xlabel("Tempo (s)")
    ax_b.set_ylabel(r"$|\theta_{nl} - \theta_{lin}|$ (rad)")
    ax_b.set_xlim(0, max(t_saida + 0.05, 0.5))
    ax_b.text(0.99, 0.02, "DOP853 | rtol=1e-10, atol=1e-12",
              transform=ax_b.transAxes, ha="right", va="bottom",
              fontsize=7, color="0.35")
    salvar_figura("fig-04-condicao-inicial.png")
    return t_saida, erro_max


# ---------------------------------------------------------------------------
# FIGURA 5 — Pulso de torque
# ---------------------------------------------------------------------------
def figura_pulso(p=P, u0=0.15, t_on=0.5, t_off=0.8, T=3.0):
    seg = [(0.0, 0.0), (t_on, u0), (t_off, 0.0)]
    t_final = T

    # --- simulação não linear em segmentos ---
    t_all, th_all = [], []
    estado = [0.0, 0.0]
    for i, (t0, u) in enumerate(seg):
        t1 = seg[i + 1][0] if i + 1 < len(seg) else t_final
        n = max(2, int((t1 - t0) * 2000))
        tt = np.linspace(t0, t1, n)
        ss = solve_ivp(rhs, (t0, t1), estado, method=METODO, t_eval=tt,
                       args=(p, lambda _: u), rtol=RTOL, atol=ATOL)
        t_all.extend(ss.t.tolist())
        th_all.extend(ss.y[0].tolist())
        estado = [ss.y[0][-1], ss.y[1][-1]]
    t = np.array(t_all)
    th = np.array(th_all)

    # --- referência linear trecho a trecho ---
    th_lin = np.zeros_like(t)
    estado_lin = [0.0, 0.0]
    for i, (t0, u) in enumerate(seg):
        t1 = seg[i + 1][0] if i + 1 < len(seg) else t_final
        mask = (t >= t0) & (t <= t1)
        tt = t[mask]
        th_seg = resposta_linear_topo(p, estado_lin[0], estado_lin[1], u, tt - t0)
        th_lin[mask] = th_seg
        if len(tt) > 0:
            th_fim = resposta_linear_topo(p, estado_lin[0], estado_lin[1], u, t1 - t0)
            dt = 1e-6
            th_fim2 = resposta_linear_topo(p, estado_lin[0], estado_lin[1], u, t1 - t0 + dt)
            estado_lin = [th_fim, (th_fim2 - th_fim) / dt]

    t_saida = instante_saida_dominio(t, th)
    if math.isnan(t_saida):
        t_saida = T

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(7.5, 5.4), sharex=True,
                                     gridspec_kw={"height_ratios": [1, 2.2]})
    tau = np.array([u0 if t_on <= tk < t_off else 0.0 for tk in t])
    ax_a.plot(t, tau, color="tab:purple")
    ax_a.set_ylabel(r"$\tau$ (N·m)")
    ax_a.set_title(virgula("Pulso τ = %g N·m entre %.1f s e %.1f s" % (u0, t_on, t_off)))
    ax_a.set_xlim(0, max(t_saida + 0.15, 1.0))

    ax_b.plot(t, th, label="modelo não linear")
    ax_b.plot(t, th_lin, "--", label="linearização local (referência)")
    ax_b.axhline(LIMITE_DOMINIO, color="0.4", ls=":", lw=1)
    ax_b.axvspan(t_on, t_off, color="tab:purple", alpha=0.08)
    ax_b.plot([t_saida], [LIMITE_DOMINIO], "o", color="tab:red")
    ax_b.annotate(virgula("saída do domínio\nt = %.3f s" % t_saida),
                  xy=(t_saida, LIMITE_DOMINIO),
                  xytext=(t_saida - 0.65, 0.75), fontsize=8,
                  arrowprops=dict(arrowstyle="->", lw=0.8))
    ax_b.set_xlim(0, max(t_saida + 0.15, 1.0))
    ax_b.set_ylim(-0.02, max(1.0, th.max() + 0.1))
    ax_b.set_xlabel("Tempo (s)")
    ax_b.set_ylabel(r"$\theta$ (rad)")
    ax_b.legend(loc="upper left", fontsize=8)
    ax_b.text(0.99, 0.02, "DOP853 | rtol=1e-10, atol=1e-12",
              transform=ax_b.transAxes, ha="right", va="bottom",
              fontsize=7, color="0.35")
    salvar_figura("fig-05-pulso.png")
    return t_saida


# ---------------------------------------------------------------------------
# FIGURA 6 — Ajuste de λ₁ (taxa exponencial medida)
# ---------------------------------------------------------------------------
def figura_ajuste_lambda(p=P):
    th0 = 1e-4
    t, y = simular([th0, 0.0], lambda t: 0.0, p=p, T=2.2, n=4001)
    mask = (t >= 1.0) & (t <= 2.0)
    coef = np.polyfit(t[mask], np.log(y[0][mask]), 1)
    lam_med = coef[0]
    inter = coef[1]

    fig, ax = plt.subplots(figsize=(7.5, 3.7))
    ax.semilogy(t, y[0], label=r"não linear, $\theta(0)=10^{-4}$ rad")
    ax.semilogy(t, np.exp(inter + lam_med * t), "--",
                label=virgula(r"ajuste em [1,2] s: $\lambda_1^{med} = %.4f$ s$^{-1}$" % lam_med))
    ax.axvspan(1.0, 2.0, color="tab:orange", alpha=0.10)
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel(r"$\theta$ (rad), escala log")
    ax.set_title("Medição do autovalor instável pela taxa de crescimento")
    ax.legend(loc="upper left", fontsize=8)
    salvar_figura("fig-06-ajuste-lambda.png")
    return lam_med


# ---------------------------------------------------------------------------
# FIGURA 7 — Degrau em torno do equilíbrio inferior (θ = π)
# ---------------------------------------------------------------------------
def figura_equilibrio_inferior(p=P, u0=0.05, T=300.0):
    q = parametros_base(p)
    t, y = simular([math.pi, 0.0], lambda t: u0, p=p, T=T, n=30001)
    d = y[0] - math.pi
    d_ss = u0 * q["K"]

    picos = picos_locais(t, d)
    if len(picos) >= 2:
        tp = picos[0][0]
        Mp = (picos[0][1] - d_ss) / d_ss
        Td = picos[1][0] - picos[0][0]
    else:
        tp, Mp, Td = float("nan"), 0.0, float("nan")

    ts2 = float("nan")
    for k in range(len(t)):
        if abs(d[k] - d_ss) > 0.02 * abs(d_ss):
            ts2 = t[k]

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(7.5, 5.8))

    # ---- painel superior: visão geral ----
    ax_a.plot(t, d, lw=0.7)
    ax_a.axhline(d_ss, color="tab:red", ls="--", lw=1,
                 label=virgula(r"teórico $\tau/(mgL) = %.5f$ rad" % d_ss))
    ax_a.axhline(d_ss * 1.02, color="0.5", ls=":", lw=0.8)
    ax_a.axhline(d_ss * 0.98, color="0.5", ls=":", lw=0.8)
    if not math.isnan(ts2):
        ax_a.axvline(ts2, color="tab:green", ls="--", lw=1,
                     label=virgula(r"$t_s(2\%%) \approx %.1f$ s" % ts2))
    ax_a.set_xlim(0, min(150, T))
    ax_a.set_xlabel("Tempo (s)")
    ax_a.set_ylabel(r"$\theta - \pi$ (rad)")
    ax_a.set_title(virgula("Degrau τ = %g N·m em torno de θ = π" % u0))
    ax_a.legend(loc="upper right", fontsize=8)

    # ---- painel inferior: detalhe dos picos ----
    ax_b.plot(t, d)
    ax_b.axhline(d_ss, color="tab:red", ls="--", lw=1)
    if not math.isnan(tp):
        ax_b.plot([tp], [picos[0][1]], "o", color="tab:red")
        ax_b.annotate(virgula(r"$t_p = %.3f$ s ; $M_p = %.1f\%%$" % (tp, 100 * Mp)),
                      xy=(tp, picos[0][1]), xytext=(3.4, 0.0235),
                      fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8))
    if not math.isnan(Td):
        ax_b.annotate("", xy=(picos[1][0], picos[1][1]),
                      xytext=(picos[0][0], picos[1][1]),
                      arrowprops=dict(arrowstyle="<->", lw=0.8))
        ax_b.text((picos[0][0] + picos[1][0]) / 2, picos[1][1] + 0.0012,
                  virgula(r"$T_d = %.3f$ s" % Td), ha="center", fontsize=8)
    ax_b.set_xlim(0, 8)
    ax_b.set_ylim(-0.001, max(0.03, d_ss * 3))
    ax_b.set_xlabel("Tempo (s)")
    ax_b.set_ylabel(r"$\theta - \pi$ (rad)")

    fig.tight_layout()
    salvar_figura("fig-07-equilibrio-inferior.png")
    return {"tp": tp, "Mp": Mp, "Td": Td, "ts2": ts2,
            "d_ss": d_ss, "d_ss_teorico": d_ss}


# ---------------------------------------------------------------------------
# FIGURA 8 — Validação cruzada para grandes amplitudes
# ---------------------------------------------------------------------------
def figura_validacao_grande(p=P):
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10, 3.8))
    Us = np.linspace(0.01, 0.95 * mgl(p), 300)
    r = Us / mgl(p)
    erro_ss = np.abs(r - np.arcsin(r)) / np.arcsin(r) * 100
    ax_a.plot(r, erro_ss)
    ax_a.set_xlabel(r"$u_0/(mgL)$")
    ax_a.set_ylabel("erro relativo no regime permanente (%)")
    ax_a.set_title("Erro do regime permanente: linear × não linear", fontsize=10)

    u0 = 2.5
    t, y = simular([math.pi, 0.0], lambda t: u0, p=p, T=120, n=12001)
    d = y[0] - math.pi
    d_nl = math.asin(u0 / mgl(p))
    d_lin = u0 / mgl(p)
    ax_b.plot(t, d, label="não linear")
    ax_b.plot(t, resposta_linear_base(p, 0.0, u0, t), "--", label="linearizado")
    ax_b.axhline(d_nl, color="C0", lw=0.6, ls=":")
    ax_b.axhline(d_lin, color="C1", lw=0.6, ls=":")
    ax_b.set_xlabel("Tempo (s)")
    ax_b.set_ylabel(r"$\delta = \theta - \pi$ (rad)")
    ax_b.set_title(virgula(r"Grande amplitude ($u_0 = %g$ N·m)" % u0), fontsize=10)
    ax_b.legend(fontsize=8)
    fig.tight_layout()
    salvar_figura("fig-08-validacao-grande-amplitude.png")
    return {"d_nl": d_nl, "d_lin": d_lin,
            "erro_rel_pct": (d_lin - d_nl) / d_nl * 100}


# ---------------------------------------------------------------------------
# FIGURA 9 — Sensibilidade paramétrica (3 parâmetros × 2 ensaios)
# ---------------------------------------------------------------------------
def figura_sensibilidade(p=P):
    fatores = [0.25, 0.5, 1.0, 2.0, 10.0]
    estudos = [("m", "massa", "kg", P["m"]),
               ("l", "comprimento", "m", P["l"]),
               ("b", "atrito", "N·m·s/rad", P["b"])]
    resultados = {}
    for simbolo, nome, unidade, valor_nominal in estudos:
        fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10, 3.9))
        linhas = []
        for f in fatores:
            valor = valor_nominal * f
            if simbolo == "m":
                p_t = criar_parametros(massa=valor)
            elif simbolo == "l":
                p_t = criar_parametros(comprimento=valor)
            else:
                p_t = criar_parametros(atrito=valor)
            pp, pm = autovalores_topo(p_t)
            t, y = simular([0.0, 0.0], lambda t: 0.05, p=p_t, T=12.0, n=8001)
            sd = instante_saida_dominio(t, y[0])
            t2, y2 = simular([0.02, 0.0], lambda t: 0.0, p=p_t, T=12.0, n=8001)
            sl = instante_saida_dominio(t2, y2[0])
            rotulo = virgula(r"%s = %g %s" % (simbolo, valor, unidade))
            est = "-" if f == 1.0 else "--"
            lw = 2.0 if f == 1.0 else 1.1
            ax_a.plot(t, y[0], est, lw=lw, label=rotulo)
            ax_b.plot(t2, y2[0], est, lw=lw, label=rotulo)
            linhas.append({"fator": f, "valor": valor, "lambda1": pp,
                           "t_saida_degrau": sd, "t_saida_livre": sl})
        for ax, ttl in [(ax_a, virgula("Degrau 0,05 N·m, θ(0)=0")),
                        (ax_b, virgula("Resposta livre, θ(0)=0,02 rad"))]:
            ax.axhline(LIMITE_DOMINIO, color="0.4", ls=":", lw=1)
            ax.set_xlim(0, 6)
            ax.set_ylim(-0.02, 0.8)
            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel(r"$\theta$ (rad)")
            ax.set_title(ttl, fontsize=10)
        ax_a.legend(fontsize=7, loc="upper right")
        fig.suptitle(virgula("Sensibilidade ao parâmetro %s (%s)" % (simbolo, nome)),
                     fontsize=11)
        fig.tight_layout()
        salvar_figura("fig-09-sensibilidade-%s.png" % nome)
        resultados[simbolo] = linhas
    return resultados


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    registrar("=== PARÂMETROS NOMINAIS ===")
    registrar("m = %.3f kg | l = %.3f m | J = %.4f kg·m² | b = %.4f N·m·s/rad | g = %.2f m/s²"
              % (P["m"], P["l"], J(P), P["b"], P["g"]))
    registrar("mgL = %.4f N·m | mgL/J = %.4f s⁻² | b/J = %.4f s⁻¹"
              % (mgl(P), mgl(P) / J(P), P["b"] / J(P)))

    # R2 — grandezas algébricas
    pp, pm = autovalores_topo(P)
    q = parametros_base(P)
    registrar("\n=== R2 — ANÁLISE ALGÉBRICA ===")
    registrar("λ₁ (instável) = %+.4f s⁻¹ ; τ₁ = 1/λ₁ = %.4f s" % (pp, 1 / pp))
    registrar("λ₂ (estável)   = %+.4f s⁻¹ ; τ₂ = 1/|λ₂| = %.4f s" % (pm, 1 / abs(pm)))
    registrar("tempo de duplicação do modo instável: ln2/λ₁ = %.4f s" % (math.log(2) / pp))
    registrar("ganho DC formal (topo): G(0) = -1/(mgL) = %.4f rad/(N·m)" % (-1 / mgl(P)))
    registrar("Equilíbrio inferior (θ=π): ωn = %.4f rad/s | ζ = %.5f | ωd = %.4f rad/s"
              % (q["wn"], q["zeta"], q["wd"]))
    registrar("  polos = %.4f ± j%.4f s⁻¹ | Td = %.4f s | tp = %.4f s"
              % (-q["sigma"], q["wd"], 2 * math.pi / q["wd"], math.pi / q["wd"]))
    registrar("  Mp = %.2f %% | ts(2%%) = %.2f s | K = 1/mgL = %.4f rad/(N·m)"
              % (100 * q["Mp"], q["ts2"], q["K"]))

    # Figuras
    figura_diagrama_blocos()
    figura_retrato_fase()
    t_saida_degrau = figura_degrau()
    t_saida_ci, erro_ci = figura_condicao_inicial()
    t_saida_pulso = figura_pulso()
    lam_med = figura_ajuste_lambda()
    base = figura_equilibrio_inferior()
    val_grande = figura_validacao_grande()
    sens = figura_sensibilidade()

    # R4 — tabela de validação cruzada
    registrar("\n=== R4 — VALIDAÇÃO CRUZADA (algébrico × simulado) ===")
    def dpct(ref, med):
        return 100 * (med - ref) / ref

    # Simulação do degrau para extrair a saída do domínio
    t_deg, y_deg = simular([0.0, 0.0], lambda t: 0.05, p=P, T=3.0, n=6001)
    saida_degrau_nl = instante_saida_dominio(t_deg, y_deg[0])
    if math.isnan(saida_degrau_nl):
        saida_degrau_nl = float(t_deg[-1])

    # Referência linear para a saída do domínio do degrau
    t_deg_lin = resposta_linear_topo(P, 0.0, 0.0, 0.05, t_deg)
    saida_degrau_lin = instante_saida_dominio(t_deg, t_deg_lin)
    if math.isnan(saida_degrau_lin):
        saida_degrau_lin = float(t_deg[-1])

    tab = [
        ("λ₁ (s⁻¹)", pp, lam_med),
        ("saída do domínio — degrau (s)", saida_degrau_lin, saida_degrau_nl),
        ("saída do domínio — CI 0,30 rad (s)", None, t_saida_ci),
        ("saída do domínio — pulso (s)", None, t_saida_pulso),
        ("θ=π: valor final (rad)", base["d_ss_teorico"], base["d_ss"]),
        ("θ=π: Td (s)", 2 * math.pi / q["wd"], base["Td"]),
        ("θ=π: tp (s)", math.pi / q["wd"], base["tp"]),
        ("θ=π: Mp (%)", 100 * q["Mp"], 100 * base["Mp"]),
        ("θ=π: ts 2% (s)", q["ts2"], base["ts2"]),
    ]
    for nome, ref, med in tab:
        if ref is None or med is None \
           or (isinstance(ref, float) and math.isnan(ref)) \
           or (isinstance(med, float) and math.isnan(med)):
            registrar("%-32s (não comparável)" % nome)
        else:
            registrar("%-32s alg = %10.5f | sim = %10.5f | dif = %+7.3f %%"
                      % (nome, ref, med, dpct(ref, med)))

    # R5 — síntese de sensibilidade
    registrar("\n=== R5 — SENSIBILIDADE PARAMÉTRICA (resumo) ===")
    for simbolo, linhas in sens.items():
        registrar("\n-- %s --" % simbolo)
        for L in linhas:
            registrar("fator %5.2f | valor %7.4f | λ₁ = %8.4f | t_saída degrau = %6.3f s | t_saída livre = %6.3f s"
                      % (L["fator"], L["valor"], L["lambda1"],
                         L["t_saida_degrau"], L["t_saida_livre"]))

    # Salvamento dos resultados
    with open(os.path.join(RES, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump({
            "parametros": {k: float(v) for k, v in P.items()},
            "J": J(P), "mgL": mgl(P),
            "autovalores_topo": [float(pp), float(pm)],
            "parametros_base": {k: (None if isinstance(v, float) and math.isnan(v) else float(v))
                                for k, v in q.items()},
            "t_saida_degrau": float(t_saida_degrau),
            "t_saida_ci": float(t_saida_ci),
            "t_saida_pulso": float(t_saida_pulso),
            "lambda_medido": float(lam_med),
            "erro_ci_max": float(erro_ci),
            "base": {k: (None if isinstance(v, float) and math.isnan(v) else float(v))
                     for k, v in base.items()},
            "validacao_grande": val_grande,
            "sensibilidade": sens,
        }, f, indent=2, ensure_ascii=False)

    with open(os.path.join(HERE, "resultados.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_resultado) + "\n")

    print("\nFiguras em:", FIG)
    print("Resultados em:", RES)