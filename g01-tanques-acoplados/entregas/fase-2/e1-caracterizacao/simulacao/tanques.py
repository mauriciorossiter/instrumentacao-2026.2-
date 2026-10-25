# -*- coding: utf-8 -*-
"""
Fase 2 - Entrega 01 (G01, Tanques Acoplados em Serie)
Caracterizacao da planta no dominio hidraulico: R2 (algebrico), R3 (simulacao),
R4 (validacao cruzada), R5 (sensibilidade) e teste de convergencia numerica.

Modelo (dossie, eqs. 5-6), nao linear, 2a ordem:
    A1 dh1/dt = q_in - k1*sqrt(h1)
    A2 dh2/dt = k1*sqrt(h1) - k2*sqrt(h2)
k1, k2 sao coeficientes AGREGADOS (k = c*a*sqrt(2g)); o material da disciplina
fornece apenas k1 e k2, por isso c e a nao aparecem separadamente.

Como rodar:  python tanques.py      (Python >= 3.10, numpy, scipy, matplotlib)
Saidas: figuras PNG em ../relatorio/figuras, curvas em ./dados e tabelas
em ./resultados.md. O modulo complementos.py gera as verificacoes adicionais.

Parametros: Tabela 1 do relatorio da Atividade 01 do G01 (15/08/2026),
"parametros de referencia fornecidos no dossie do sistema" (valores de
referencia para simulacao, nao identificados experimentalmente).

Historico de revisao (21/10/2026):
  - tempos (t63, tr, ts) agora medidos na saida densa do integrador, com o
    instante exato do cruzamento (brentq), e normalizados pelo equilibrio
    NAO LINEAR analitico. Antes: normalizacao por h2(T_final), que ainda
    nao tinha convergido (erro de 1,3e-5 m), o que estreitava a banda de 2 %
    e dava ts = 608,1 s em vez de 608,9 s para o degrau de 5 %;
  - horizonte de simulacao 20*tau (antes 12*tau);
  - R4 separa: modelo linearizado x equilibrio nao linear analitico x
    simulacao nao linear;
  - teste de convergencia (passo maximo e tolerancias);
  - R5 classifica cada caso pelo dominio [hmin, hmax] e desenha os casos
    fora do dominio tracejados, como extrapolacao matematica;
  - pico do pulso (R3c) do modelo linearizado calculado em forma fechada.
"""
import os
import sys
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 12, "axes.titlesize": 12, "legend.fontsize": 10})

# ----------------------------- parametros ---------------------------------
P = dict(
    A1=0.50,       # m^2      secao transversal do tanque 1
    A2=0.50,       # m^2      secao transversal do tanque 2
    k1=0.010,      # m^2,5/s  coef. agregado do orificio T1 -> T2
    k2=0.010,      # m^2,5/s  coef. agregado do orificio T2 -> dreno
    q0=0.010,      # m^3/s    vazao nominal (h10 = h20 = 1,00 m)
    hmin=0.10,     # m        limite inferior operacional adotado
    hmax=1.20,     # m        transbordamento
)
DSTEP = 0.05       # degrau de +5 % em q_in (R3a); +10 % levaria h2 a 1,21 m
SOLVER = "RK45"
MAX_STEP = 0.1     # s
RTOL, ATOL = 1e-8, 1e-10
H_IC = [1.15, 0.60]          # R3b, dentro de [hmin, hmax]
TP, AMP = 30.0, 0.20         # R3c: pulso de +20 % por 30 s

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.abspath(os.path.join(HERE, "..", "relatorio", "figuras"))
DATA = os.path.join(HERE, "dados")
os.makedirs(FIG, exist_ok=True)
os.makedirs(DATA, exist_ok=True)
FIG_NAMES = {
    "r3a_degrau.png": "fig-02-resposta-degrau.png",
    "r3b_condicao_inicial.png": "fig-03-condicao-inicial.png",
    "r3c_pulso.png": "fig-04-resposta-pulso.png",
    "r5_k2.png": "fig-06a-sensibilidade-k2.png",
    "r5_A2.png": "fig-06b-sensibilidade-a2.png",
    "r5_q0.png": "fig-06c-sensibilidade-vazao.png",
    "r5_k1.png": "fig-06d-sensibilidade-k1.png",
}
SOLVER_TXT = f"solve_ivp {SOLVER}, passo máx. {MAX_STEP} s, rtol {RTOL:g}, atol {ATOL:g}"


def fig_path(name):
    return os.path.join(FIG, FIG_NAMES.get(name, name))


# ----------------------------- R2: algebrico -------------------------------
def step_lin(t, tau1, tau2):
    """Resposta normalizada do linearizado ao degrau (0 -> 1)."""
    if abs(tau1 - tau2) > 1e-9:
        return 1 - (tau1 * np.exp(-t / tau1) - tau2 * np.exp(-t / tau2)) / (tau1 - tau2)
    return 1 - (1 + t / tau1) * np.exp(-t / tau1)


def cross(f, level, t_hi):
    """Primeiro instante em que a funcao monotona f(t) atinge 'level'."""
    return brentq(lambda t: f(t) - level, 0.0, t_hi, xtol=1e-6)


def last_cross(f, band, t_hi, dt=0.5):
    """Ultimo instante em que |f - 1| = band (entrada definitiva na banda)."""
    t = np.arange(0, t_hi, dt)
    out = np.abs(f(t) - 1) > band
    i = np.where(out)[0][-1]
    return brentq(lambda x: abs(f(x) - 1) - band, t[i], t[i] + dt, xtol=1e-6)


def algebra(p, dq_rel=DSTEP):
    k1, k2, q = p["k1"], p["k2"], p["q0"]
    h1, h2 = (q / k1) ** 2, (q / k2) ** 2
    t1 = 2 * p["A1"] * np.sqrt(h1) / k1
    t2 = 2 * p["A2"] * np.sqrt(h2) / k2
    A = np.array([[-1 / t1, 0], [k1 / (2 * p["A2"] * np.sqrt(h1)), -1 / t2]])
    lam = np.linalg.eigvals(A).real
    K2 = 2 * q / k2 ** 2          # m/(m^3/s) = s/m^2   dh2/dq
    K1 = 2 * q / k1 ** 2
    tt = 20 * max(t1, t2)
    y = lambda t: step_lin(t, t1, t2)
    t63 = cross(y, 0.632, tt)
    tr = cross(y, 0.9, tt) - cross(y, 0.1, tt)
    ts = last_cross(y, 0.02, tt)
    zeta = (t1 + t2) / (2 * np.sqrt(t1 * t2))
    return dict(k1=k1, k2=k2, h1=h1, h2=h2, t1=t1, t2=t2, lam=lam, K1=K1, K2=K2,
                tr=tr, t63=t63, ts=ts, zeta=zeta, wn=1 / np.sqrt(t1 * t2),
                h2_nl=lambda dq: ((q * (1 + dq)) / k2) ** 2,
                h1_nl=lambda dq: ((q * (1 + dq)) / k1) ** 2)


def pulse_peak_lin(r, dq_abs, Tp):
    """Pico de dh2 do linearizado (tau1 = tau2) para um pulso retangular."""
    tau = r["t1"]
    assert abs(r["t1"] - r["t2"]) < 1e-9
    E = np.exp(Tp / tau)
    tp = Tp * E / (E - 1)                       # d/dt [y(t) - y(t-Tp)] = 0
    val = r["K2"] * dq_abs * (step_lin(tp, tau, tau) - step_lin(tp - Tp, tau, tau))
    return tp, val


# ----------------------------- simulacao -----------------------------------
def f_nl(t, h, p, qin):
    k1, k2 = p["k1"], p["k2"]
    h1, h2 = max(h[0], 0.0), max(h[1], 0.0)
    return [(qin(t) - k1 * np.sqrt(h1)) / p["A1"],
            (k1 * np.sqrt(h1) - k2 * np.sqrt(h2)) / p["A2"]]


def f_lin(t, d, p, qin, r):
    dq = qin(t) - p["q0"]
    return [-d[0] / r["t1"] + dq / p["A1"],
            r["k1"] / (2 * p["A2"] * np.sqrt(r["h1"])) * d[0] - d[1] / r["t2"]]


def simulate(p, qin, h0, T, r=None, max_step=MAX_STEP, rtol=RTOL, atol=ATOL):
    nl = solve_ivp(f_nl, (0, T), h0, args=(p, qin), method=SOLVER, max_step=max_step,
                   rtol=rtol, atol=atol, dense_output=True)
    if not nl.success:
        raise RuntimeError(nl.message)
    te = np.arange(0, T, 0.5)
    out = dict(sol=nl.sol, t=te, h1=nl.sol(te)[0], h2=nl.sol(te)[1])
    if r is not None:
        d0 = [h0[0] - r["h1"], h0[1] - r["h2"]]
        li = solve_ivp(f_lin, (0, T), d0, args=(p, qin, r), method=SOLVER, max_step=max_step,
                       rtol=rtol, atol=atol, dense_output=True)
        if not li.success:
            raise RuntimeError(li.message)
        out.update(l1=li.sol(te)[0] + r["h1"], l2=li.sol(te)[1] + r["h2"])
    return out


def measure_step(sol, y0, yf, T, idx=1):
    """t63, tr (10-90 %) e ts (banda de +-2 % da variacao total, entrada
    definitiva), normalizados pelo valor final analitico yf."""
    n = lambda t: (sol(t)[idx] - y0) / (yf - y0)
    t63 = cross(n, 0.632, T)
    tr = cross(n, 0.9, T) - cross(n, 0.1, T)
    ts = last_cross(n, 0.02, T)
    return t63, tr, ts


def pct(a, b):
    return 100 * (b - a) / a


def fmt(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def domain_class(p, h1a, h2a, h1b, h2b):
    """Classifica pelo equilibrio inicial (a) e final (b) de h1 e h2."""
    lo, hi = p["hmin"], p["hmax"]
    ok = lambda h: lo <= h <= hi
    if not (ok(h1a) and ok(h2a)):
        return "extrapolação: equilíbrio fora do domínio"
    if not (ok(h1b) and ok(h2b)):
        return "extrapolação: degrau sai do domínio"
    return "válido"


# ----------------------------- R3 + R4 -------------------------------------
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("R2-R4: ensaios principais e convergência...", flush=True)
    p = P
    r = algebra(p)
    q0 = p["q0"]
    T = 20 * max(r["t1"], r["t2"])
    lines = []
    w = lines.append
    w("# Resultados — Fase 2, Entrega 01 (G01)\n")
    w("> Parâmetros: Tabela 1 do relatório da Atividade 01 (valores de referência do dossiê do sistema, adotados para simulação; não identificados experimentalmente).\n")
    w(f"Simulação: {SOLVER_TXT}. Tempos medidos na saída densa do integrador (instante exato do cruzamento), normalizados pelo equilíbrio não linear analítico.\n")

    w("## Parâmetros\n\n| Símbolo | Valor | Unidade |\n|---|---|---|")
    units = dict(A1="m²", A2="m²", k1="m^2,5/s", k2="m^2,5/s", q0="m³/s", hmin="m", hmax="m")
    for k, v in p.items():
        w(f"| {k} | {v:g} | {units[k]} |")
    w("")

    w("## R2 — Análise algébrica (ponto nominal)\n\n| Grandeza | Valor | Observação |\n|---|---|---|")
    w(f"| h̄1 = (q̄/k1)² | {r['h1']:.4f} m | equilíbrio exato (não linear) |")
    w(f"| h̄2 = (q̄/k2)² | {r['h2']:.4f} m | equilíbrio exato (não linear) |")
    w(f"| τ1 = 2A1√h̄1/k1 | {r['t1']:.2f} s | linearização local |")
    w(f"| τ2 = 2A2√h̄2/k2 | {r['t2']:.2f} s | linearização local |")
    w(f"| polos λ1, λ2 | {r['lam'][0]:.5f}, {r['lam'][1]:.5f} s⁻¹ | reais negativos |")
    w(f"| Kdc (δh2/δq) = 2q̄/k2² | {r['K2']:.2f} s/m² (= m por m³/s) | linearização local |")
    w(f"| Kdc (δh1/δq) = 2q̄/k1² | {r['K1']:.2f} s/m² | linearização local |")
    w(f"| ζ = (τ1+τ2)/(2√(τ1τ2)) | {r['zeta']:.3f} | {'= 1: criticamente amortecido (polo duplo)' if abs(r['zeta']-1) < 1e-6 else '> 1: sobreamortecido'} |")
    w(f"| ωn = 1/√(τ1τ2) | {r['wn']:.4f} rad/s | parâmetro do polinômio; não há oscilação |")
    w("| sobressinal | não se aplica | polos reais |")
    w(f"| t63 (h2) | {r['t63']:.2f} s | linearizado |")
    w(f"| tr 10–90 % (h2) | {r['tr']:.2f} s | linearizado |")
    w(f"| ts 2 % (h2) | {r['ts']:.2f} s | linearizado, banda ±2 % da variação |\n")

    # --- R3a degrau a partir do equilibrio (duas amplitudes para R4)
    res = {}
    for dq in (0.01, DSTEP):
        qin = lambda t, dq=dq: q0 * (1 + dq)
        s = simulate(p, qin, [r["h1"], r["h2"]], T, r)
        hf = r["h2_nl"](dq)
        res[dq] = (s, hf) + measure_step(s["sol"], r["h2"], hf, T)
    s, hf5, t63, tr, ts = res[DSTEP]
    hlin5 = r["h2"] + r["K2"] * DSTEP * q0
    Tplot = 12 * r["t1"]
    m = s["t"] <= Tplot
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot(s["t"][m], s["h1"][m], label="h1 não linear")
    ax.plot(s["t"][m], s["h2"][m], label="h2 não linear")
    ax.plot(s["t"][m], s["l2"][m], "--", label="h2 linearizado")
    y63 = r["h2"] + 0.632 * (hf5 - r["h2"])
    ax.plot(t63, y63, "ko"); ax.annotate(f"63 %: {fmt(t63)} s", (t63, y63), xytext=(8, -16), textcoords="offset points")
    ax.axvline(ts, color="gray", ls=":"); ax.annotate(f"tₛ(2 %) = {fmt(ts)} s", (ts, r["h2"]), xytext=(-4, 6), textcoords="offset points", ha="right")
    ax.axhline(hf5, color="C1", ls=":", lw=0.8); ax.axhline(hlin5, color="C2", ls=":", lw=0.8)
    ax.text(Tplot * 0.98, hlin5 - 0.017, f"h2(∞): não linear {fmt(hf5, 4)} m · linearizado {fmt(hlin5, 4)} m",
            ha="right", va="top", fontsize=10)
    ax.set(xlabel="tempo [s]", ylabel="nível [m]", title=f"R3(a) degrau de +{DSTEP*100:.0f} % em qᵢ a partir do equilíbrio")
    ax.legend(loc="lower right"); ax.grid(alpha=.3)
    fig.text(0.01, 0.005, SOLVER_TXT, fontsize=7, color="gray")
    fig.tight_layout(); fig.savefig(fig_path("r3a_degrau.png"), dpi=170); plt.close(fig)

    # --- R3b condicao inicial nao nula (q_in nominal)
    sb = simulate(p, lambda t: q0, H_IC, T, r)
    m = sb["t"] <= Tplot
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot(sb["t"][m], sb["h1"][m], label="h1 não linear"); ax.plot(sb["t"][m], sb["l1"][m], "--", label="h1 linearizado")
    ax.plot(sb["t"][m], sb["h2"][m], label="h2 não linear"); ax.plot(sb["t"][m], sb["l2"][m], "--", label="h2 linearizado")
    ax.axhline(r["h1"], color="gray", ls=":", lw=.8)
    ipk = np.argmax(sb["h2"]); ax.plot(sb["t"][ipk], sb["h2"][ipk], "ko")
    ax.annotate(f"máx. h2 = {fmt(sb['h2'][ipk], 3)} m em {sb['t'][ipk]:.0f} s", (sb["t"][ipk], sb["h2"][ipk]), xytext=(8, 8), textcoords="offset points")
    ax.plot(0, H_IC[0], "ks"); ax.plot(0, H_IC[1], "ks")
    ax.set(xlabel="tempo [s]", ylabel="nível [m]", title=f"R3(b) condição inicial h1(0) = {fmt(H_IC[0], 2)} m, h2(0) = {fmt(H_IC[1], 2)} m")
    ax.legend(loc="lower right"); ax.grid(alpha=.3); fig.text(0.01, 0.005, SOLVER_TXT, fontsize=7, color="gray")
    fig.tight_layout(); fig.savefig(fig_path("r3b_condicao_inicial.png"), dpi=170); plt.close(fig)
    # tau1 medido: ajuste log do decaimento de h1 (subsistema de 1a ordem) perto do equilibrio
    tt = np.linspace(3 * r["t1"], 8 * r["t1"], 2001)
    e1 = np.abs(sb["sol"](tt)[0] - r["h1"])
    tau1_med = -1 / np.polyfit(tt, np.log(e1), 1)[0]

    # --- R3c pulso de vazao
    qin = lambda t: q0 * (1 + AMP) if 0 <= t < TP else q0
    sc = simulate(p, qin, [r["h1"], r["h2"]], T, r)
    m = sc["t"] <= Tplot
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot(sc["t"][m], sc["h1"][m], label="h1 não linear"); ax.plot(sc["t"][m], sc["h2"][m], label="h2 não linear")
    ax.plot(sc["t"][m], sc["l2"][m], "--", label="h2 linearizado")
    ax.axvspan(0, TP, color="orange", alpha=.15, label=f"pulso +{AMP*100:.0f} % em qᵢ ({TP:.0f} s)")
    for key in ("h1", "h2"):
        i = np.argmax(sc[key]); ax.plot(sc["t"][i], sc[key][i], "ko")
        ax.annotate(f"pico {fmt(sc[key][i], 3)} m em {sc['t'][i]:.0f} s", (sc["t"][i], sc[key][i]), xytext=(8, 2), textcoords="offset points")
    ax.set(xlabel="tempo [s]", ylabel="nível [m]", title="R3(c) pulso de vazão a partir do equilíbrio")
    ax.legend(); ax.grid(alpha=.3); fig.text(0.01, 0.005, SOLVER_TXT, fontsize=7, color="gray")
    fig.tight_layout(); fig.savefig(fig_path("r3c_pulso.png"), dpi=170); plt.close(fig)
    tpk_lin, dpk_lin = pulse_peak_lin(r, AMP * q0, TP)
    ipn = np.argmax(sc["h2"]); dpk_sim = sc["h2"][ipn] - r["h2"]
    ipn1 = np.argmax(sc["h1"])

    # --- R4 validacao cruzada
    w("## R4 — Validação cruzada\n")
    w("Colunas: (L) modelo linearizado, analítico; (NL) modelo não linear, analítico (só existe para equilíbrios); (S) simulação numérica do modelo não linear.\n")
    w("| Grandeza | L | NL | S | S×L | S×NL |\n|---|---|---|---|---|---|")
    w(f"| h̄2 inicial (m) | — | {r['h2']:.4f} | {res[0.01][0].get('h2')[0]:.4f} | — | {pct(r['h2'], res[0.01][0]['h2'][0]):.3f} % |")
    for dq in (0.01, DSTEP):
        s_, hf, *_ = res[dq]
        hl = r["h2"] + r["K2"] * dq * q0
        hs = s_["sol"](T)[1]
        w(f"| h2(∞), degrau {dq*100:.0f} % (m) | {hl:.4f} | {hf:.4f} | {hs:.4f} | {pct(hl, hs):.3f} % | {pct(hf, hs):.4f} % |")
    for dq in (0.01, DSTEP):
        s_, hf, *_ = res[dq]
        hs = s_["sol"](T)[1]
        Ks, Knl = (hs - r["h2"]) / (dq * q0), (hf - r["h2"]) / (dq * q0)
        w(f"| K efetivo = Δh2/Δq, degrau {dq*100:.0f} % (s/m²) | {r['K2']:.2f} | {Knl:.2f} | {Ks:.2f} | {pct(r['K2'], Ks):.2f} % | {pct(Knl, Ks):.4f} % |")
    w(f"| τ1 (s), decaimento de h1 em R3(b) | {r['t1']:.2f} | — | {tau1_med:.2f} | {pct(r['t1'], tau1_med):.2f} % | — |")
    for lab, key, i in (("t63", "t63", 2), ("tr 10–90 %", "tr", 3), ("ts 2 %", "ts", 4)):
        for dq in (0.01, DSTEP):
            v = res[dq][i]
            w(f"| {lab} (s), degrau {dq*100:.0f} % | {r[key]:.2f} | — | {v:.2f} | {pct(r[key], v):.2f} % | — |")
    w(f"| pico de δh2 no pulso (m) | {dpk_lin:.4f} em {tpk_lin:.1f} s | — | {dpk_sim:.4f} em {sc['t'][ipn]:.1f} s | {pct(dpk_lin, dpk_sim):.2f} % | — |")
    w(f"| pico de h1 no pulso (m) | — | — | {sc['h1'][ipn1]:.4f} em {sc['t'][ipn1]:.1f} s | — | — |")
    ovs = max(0.0, (s["sol"](np.linspace(0, T, 40001))[1].max() - hf5) / (hf5 - r["h2"]) * 100)
    w(f"| sobressinal, degrau 5 % | 0 | — | {ovs:.4f} % | — | — |\n")

    # --- convergencia numerica
    w("## Convergência numérica (degrau de +5 %, modelo não linear)\n")
    w("| passo máx. (s) | rtol | atol | h2(∞) (m) | erro vs NL analítico (m) | t63 (s) | tr (s) | ts 2 % (s) |\n|---|---|---|---|---|---|---|---|")
    qin5 = lambda t: q0 * (1 + DSTEP)
    for ms, rt, at in ((0.1, 1e-6, 1e-8), (0.1, 1e-8, 1e-10), (0.05, 1e-8, 1e-10), (0.01, 1e-10, 1e-12)):
        sv = simulate(p, qin5, [r["h1"], r["h2"]], T, None, ms, rt, at)
        a, b, c = measure_step(sv["sol"], r["h2"], hf5, T)
        hs = sv["sol"](T)[1]
        w(f"| {ms:g} | {rt:g} | {at:g} | {hs:.6f} | {hs-hf5:.1e} | {a:.2f} | {b:.2f} | {c:.2f} |")
    w("")

    # --- R5 sensibilidade
    w(f"## R5 — Sensibilidade paramétrica (degrau de +{DSTEP*100:.0f} % a partir do equilíbrio de cada caso)\n")
    w(f"Domínio adotado: {p['hmin']:g} m ≤ h1, h2 ≤ {p['hmax']:g} m. Casos fora dele são extrapolações matemáticas do modelo, não operações da planta; seus tempos não são medições de operação válida.\n")
    studies = [("k2", "k2 (coef. do orifício de saída do T2)", [0.25, 0.5, 1, 2, 3, 4]),
               ("A2", "A2 (área transversal do T2)", [0.25, 0.5, 1, 2, 4]),
               ("q0", "q̄in (vazão de operação)", [0.25, 0.5, 0.75, 1, 2, 4]),
               ("k1", "k1 (coef. do orifício T1→T2)", [0.25, 0.5, 1, 2, 3, 4])]
    for key, name, levels in studies:
        print(f"R5: {key}...", flush=True)
        fig, (ax, axn) = plt.subplots(1, 2, figsize=(7.0, 3.9))
        w(f"### {name}\n\n| nível | h̄1 [m] | h̄2 [m] | τ1 [s] | τ2 [s] | Kdc [s/m²] | ts 2 % lin. [s] | ts 2 % sim. [s] | domínio |\n|---|---|---|---|---|---|---|---|---|")
        for j, lv in enumerate(levels):
            pp = dict(p); pp[key] = p[key] * lv
            rr = algebra(pp)
            Tl = 20 * max(rr["t1"], rr["t2"])
            qq = pp["q0"]
            ss = simulate(pp, lambda t, qq=qq: qq * (1 + DSTEP), [rr["h1"], rr["h2"]], Tl)
            hf = rr["h2_nl"](DSTEP)
            _, _, tsl = measure_step(ss["sol"], rr["h2"], hf, Tl)
            cls = domain_class(pp, rr["h1"], rr["h2"], rr["h1_nl"](DSTEP), hf)
            valid = cls == "válido"
            tstxt = f"{tsl:.0f}" if valid else f"({tsl:.0f})"
            w(f"| ×{lv:g} | {rr['h1']:.4g} | {rr['h2']:.4g} | {rr['t1']:.1f} | {rr['t2']:.1f} | {rr['K2']:.4g} | {rr['ts']:.0f} | {tstxt} | {cls} |")
            lab = f"{key} ×{fmt(lv, 2).rstrip('0').rstrip(',')}" + ("" if valid else " (extrapolação)")
            sty = dict(ls="-" if valid else "--", lw=2.0 if valid else 1.3, alpha=1 if valid else 0.75, color=f"C{j}")
            ax.plot(ss["t"], ss["h2"] - rr["h2"], label=lab, **sty)
            axn.plot(ss["t"], (ss["h2"] - rr["h2"]) / (hf - rr["h2"]), **sty)
        w("")
        ax.set(xlabel="tempo [s] (log)", ylabel="δh2 = h2 − h̄2 [m]", title="amplitude (ganho)")
        axn.set(xlabel="tempo [s] (log)", ylabel="δh2 / δh2(∞)", title="normalizado (velocidade)")
        for a in (ax, axn):
            a.set_xscale("log"); a.set_xlim(1, None); a.grid(alpha=.3)
        fig.suptitle(f"R5: {name} · tracejado = fora do domínio", fontsize=12)
        fig.legend(loc="lower center", ncol=3, fontsize=9, frameon=False)
        fig.text(0.01, 0.005, SOLVER_TXT, fontsize=7, color="gray")
        fig.tight_layout(rect=(0, 0.15, 1, 1)); fig.savefig(fig_path(f"r5_{key}.png"), dpi=170); plt.close(fig)

    from complementos import completar
    completar(p, r, res, sb, sc, T, lines)

    with open(os.path.join(HERE, "resultados.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
