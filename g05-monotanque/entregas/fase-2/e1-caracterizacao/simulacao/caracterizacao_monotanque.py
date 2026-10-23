# -*- coding: utf-8 -*-
"""
ECOM060 - Fase 2, Entrega 01: caracterizacao do Monotanque no dominio hidraulico (G05).

Modelo nao linear (balanco de massa + Torricelli):
    A dh/dt = qi(t) - k*sqrt(h) - qd(t)

Gera todas as figuras do relatorio em ../relatorio/figuras/ e os numeros em resultados.json.
Uso:  python caracterizacao_monotanque.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

AQUI = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(AQUI, "..", "relatorio", "figuras")
os.makedirs(FIG, exist_ok=True)

# ----------------------------------------------------------------------------- parametros (dossie oficial)
A = 0.50            # area da secao transversal [m^2]
K = 0.010           # coeficiente de descarga agregado [m^2,5/s]
H_MAX = 1.20        # altura maxima do tanque [m]
H_MIN = 0.10        # altura minima operacional [m]
H0 = 0.50           # ponto de operacao nominal [m]
QI0 = K * np.sqrt(H0)   # vazao nominal de equilibrio = 0,0070711 m^3/s (dossie: 0,00707)

# ----------------------------------------------------------------------------- solver (declarado nas figuras)
RTOL, ATOL, MAX_STEP, DT_OUT = 1e-10, 1e-12, 0.1, 0.05
SOLVER_TXT = "solve_ivp RK45 (Dormand–Prince), passo variável ≤ 0,1 s, rtol = 10⁻¹⁰, saída a cada 0,05 s"

AZUL, AZUL2, LARANJA, CINZA, VERDE = "#185079", "#3A86B0", "#D9822B", "#7F7F7F", "#2E8B57"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "mathtext.fontset": "stix",
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 200, "legend.fontsize": 8.5})
virgula = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def br(v, d=2):
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def eixos(*axs):
    for ax in axs:
        ax.xaxis.set_major_formatter(virgula)
        ax.yaxis.set_major_formatter(virgula)


def rodape(fig, extra=""):
    fig.text(0.99, -0.075, "Solver: " + SOLVER_TXT + extra, ha="right", va="top", fontsize=6.5, color=CINZA)


def salvar(fig, nome):
    fig.savefig(os.path.join(FIG, nome), bbox_inches="tight")
    plt.close(fig)
    print("figura:", nome)


# ----------------------------------------------------------------------------- modelo e simulacao
def simular(h_ini, t_fim, qi=lambda t: QI0, qd=lambda t: 0.0, a=A, k=K, parar_vazio=False):
    """integra A dh/dt = qi - k sqrt(h) - qd; devolve t, h."""
    def f(t, h):
        return [(qi(t) - k * np.sqrt(max(h[0], 0.0)) - qd(t)) / a]

    ev = None
    if parar_vazio:
        def ev(t, h):
            return h[0] - 1e-12
        ev.terminal, ev.direction = True, -1
    t_eval = np.arange(0, t_fim + DT_OUT / 2, DT_OUT)
    s = solve_ivp(f, (0, t_fim), [h_ini], method="RK45", t_eval=t_eval, rtol=RTOL, atol=ATOL,
                  max_step=MAX_STEP, events=ev)
    t, h = s.t, s.y[0]
    if parar_vazio and s.t_events[0].size:
        t, h = np.append(t, s.t_events[0][0]), np.append(h, 0.0)
    return t, h


def t_fechado(h, h_ini, qi, a=A, k=K):
    """tempo para ir de h_ini a h com qi constante (solucao fechada, variavel u = sqrt(h))."""
    u0, u = np.sqrt(h_ini), np.sqrt(h)
    if qi == 0:
        return 2 * a / k * (u0 - u)
    ui = qi / k
    return 2 * a / k * ((u0 - u) + ui * np.log((ui - u0) / (ui - u)))


def h_fechado(t, h_ini, qi, a=A, k=K):
    """inverte t_fechado numericamente (brentq) para obter h(t) exato."""
    out = []
    hf = (qi / k) ** 2
    for ti in np.atleast_1d(t):
        if ti <= 0:
            out.append(h_ini)
            continue
        if qi == 0:
            out.append(max(np.sqrt(h_ini) - k / (2 * a) * ti, 0) ** 2)
            continue
        lo, hi = sorted((h_ini, hf))
        eps = 1e-15 * max(hf, 1)
        g = lambda h: t_fechado(h, h_ini, qi, a, k) - ti
        a_, b_ = (lo + eps, hi - eps) if h_ini < hf else (lo + eps, hi - eps)
        if g(hf + (eps if h_ini > hf else -eps)) < 0:      # ja praticamente no equilibrio
            out.append(hf)
            continue
        out.append(brentq(g, a_, b_, xtol=1e-15, rtol=1e-14, maxiter=500))
    return np.array(out)


def cruza(t, y, nivel):
    """primeiro instante em que y cruza 'nivel' (interpolacao linear)."""
    s = np.sign(y - nivel)
    i = np.where(np.diff(s) != 0)[0]
    if not i.size:
        return np.nan
    i = i[0]
    return t[i] + (nivel - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i])


def tempos(t, h, h_i, h_f, t0=0.0):
    """t10, t63, t90, ts2 contados a partir de t0 (resposta monotonica)."""
    d = h_f - h_i
    r = {}
    for nome, frac in (("t10", 0.10), ("t63", 0.632), ("t90", 0.90), ("ts2", 0.98), ("ts5", 0.95)):
        r[nome] = cruza(t, h, h_i + frac * d) - t0
    r["tr"] = r["t90"] - r["t10"]
    return r


def tempos_fechado(h_i, h_f, qi, a=A, k=K):
    d = h_f - h_i
    r = {n: t_fechado(h_i + fr * d, h_i, qi, a, k) for n, fr in
         (("t10", 0.10), ("t63", 0.632), ("t90", 0.90), ("ts2", 0.98), ("ts5", 0.95))}
    r["tr"] = r["t90"] - r["t10"]
    return r


R = {}

# ----------------------------------------------------------------------------- R2: analise algebrica
R_HID = 2 * np.sqrt(H0) / K          # resistencia hidraulica linearizada [s/m^2] = ganho estatico local [m/(m^3/s)]
TAU = A * R_HID                      # constante de tempo [s]
POLO = -1 / TAU
R["algebra"] = dict(h_eq=(QI0 / K) ** 2, qi0=QI0, R=R_HID, ganho_local=R_HID, tau=TAU, polo=POLO,
                    tr=np.log(9) * TAU, ts2=np.log(50) * TAU, ts5=np.log(20) * TAU,
                    t63=TAU, banda=1 / (2 * np.pi * TAU))
print("tau = %.4f s, R = %.4f s/m2, polo = %.6f 1/s" % (TAU, R_HID, POLO))

# ----------------------------------------------------------------------------- fig 01: esquema fisico
fig, ax = plt.subplots(figsize=(6.2, 3.6))
ax.set_xlim(0, 10); ax.set_ylim(-0.6, 6.4); ax.axis("off"); ax.grid(False)
ax.add_patch(Rectangle((2.5, 0.6), 4, 4.8, fill=False, lw=1.8, ec="k"))
ax.add_patch(Rectangle((2.5, 0.6), 4, 2.4, fc="#BBD7EA", ec="none"))
ax.plot([2.5, 6.5], [3.0, 3.0], color=AZUL, lw=1.2)
ax.plot([2.3, 2.7], [5.4 - 0.0, 5.4], color="k", lw=0)  # alinhamento
ax.annotate("", xy=(1.6, 3.0), xytext=(1.6, 0.6), arrowprops=dict(arrowstyle="<->", color=AZUL, lw=1.2))
ax.plot([1.5, 2.5], [3.0, 3.0], color=AZUL, lw=0.6, ls=":")
ax.text(1.4, 1.8, "$h(t)$", ha="right", va="center", fontsize=12, color=AZUL)
ax.plot([6.5, 6.75], [5.4, 5.4], "k--", lw=0.8); ax.text(6.8, 5.4, "$h_{máx}$ = 1,20 m", va="center", fontsize=9)
ax.plot([2.25, 2.5], [0.85, 0.85], "k--", lw=0.8); ax.text(1.0, 0.85, "$h_{mín}$ = 0,10 m", va="center", fontsize=9, ha="right")
ax.text(4.5, 1.6, "área $A$ = 0,50 m²", ha="center", fontsize=10)
ax.add_patch(Rectangle((3.2, 6.0), 0.5, 0.25, fc="#BBD7EA", ec="k", lw=1))
ax.annotate("", xy=(3.45, 3.3), xytext=(3.45, 6.0), arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=2))
ax.text(3.05, 6.12, "$q_i(t)$ — vazão de entrada\n(bomba/válvula, manipulada)", fontsize=9, va="center", ha="right")
ax.add_patch(Rectangle((6.5, 0.6), 1.2, 0.3, fc="#BBD7EA", ec="k", lw=1))
ax.annotate("", xy=(8.9, 0.75), xytext=(7.7, 0.75), arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=2))
ax.text(7.4, 0.0, r"$q_o = k\sqrt{h}$ — orifício (Torricelli)", fontsize=9, ha="center")
ax.add_patch(Rectangle((6.5, 1.75), 0.6, 0.22, fc="#BBD7EA", ec="k", lw=1))
ax.annotate("", xy=(8.3, 1.86), xytext=(7.1, 1.86), arrowprops=dict(arrowstyle="-|>", color=LARANJA, lw=1.8))
ax.text(7.2, 2.35, "$q_d(t)$ — retirada/consumo\n(distúrbio, não manipulada)", fontsize=9, color=LARANJA, va="center")
salvar(fig, "fig-01-esquema-tanque.png")

# ----------------------------------------------------------------------------- fig 02: diagrama de blocos
fig, ax = plt.subplots(figsize=(7.2, 2.5))
ax.set_xlim(0, 12); ax.set_ylim(0, 4); ax.axis("off"); ax.grid(False)


def bloco(x, y, w, h, txt, fc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=fc, ec="k", lw=1.2))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=10)


def seta(x0, y0, x1, y1, txt=None, c="k", pos="top"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color=c, lw=1.2))
    if txt:
        ax.text((x0 + x1) / 2, y0 + (0.18 if pos == "top" else -0.35), txt, ha="center", fontsize=9.5, color=c)


ax.add_patch(plt.Circle((3.0, 2.0), 0.28, fc="white", ec="k", lw=1.2))
ax.text(2.45, 2.05, "+", fontsize=10); ax.text(3.12, 1.45, "−", fontsize=11); ax.text(3.12, 2.35, "−", fontsize=11)
seta(0.6, 2.0, 2.72, 2.0, "$q_i(t)$ [m³/s]")
ax.text(0.6, 1.45, "entrada manipulada", fontsize=8, color=CINZA)
seta(3.0, 3.5, 3.0, 2.28, None, c=LARANJA)
ax.text(3.1, 3.55, "$q_d(t)$ distúrbio", fontsize=9, color=LARANJA)
bloco(4.3, 1.45, 1.6, 1.1, r"$\frac{1}{A}$")
seta(3.28, 2.0, 4.3, 2.0, r"$\frac{dV}{dt}$")
bloco(6.6, 1.45, 1.4, 1.1, r"$\int dt$")
seta(5.9, 2.0, 6.6, 2.0, r"$\dot h$")
seta(8.0, 2.0, 11.5, 2.0, "$h(t)$ [m]")
ax.text(10.2, 1.45, "saída medida (estado)", fontsize=8, color=CINZA)
bloco(5.3, 0.1, 2.1, 0.9, r"$k\sqrt{h}$")
ax.plot([9.0, 9.0, 7.4], [2.0, 0.55, 0.55], color="k", lw=1.2)
ax.plot([5.3, 3.0], [0.55, 0.55], color="k", lw=1.2)
seta(3.0, 0.55, 3.0, 1.72, None)
ax.text(3.15, 0.75, "$q_o$", fontsize=9.5)
salvar(fig, "fig-02-diagrama-blocos.png")

# ----------------------------------------------------------------------------- fig 03: equilibrio e linearizacao
hh = np.linspace(0, 1.3, 400)
fig, ax = plt.subplots(figsize=(6.2, 3.4))
ax.fill_between([0, H_MIN], 0, 0.013, color=CINZA, alpha=0.12, lw=0)
ax.fill_between([H_MAX, 1.3], 0, 0.013, color=CINZA, alpha=0.12, lw=0)
ax.plot(hh, K * np.sqrt(hh) * 1e3, color=AZUL, lw=2, label=r"saída $q_o(h)=k\sqrt{h}$")
ax.axhline(QI0 * 1e3, color=LARANJA, lw=1.6, label=r"entrada $q_{i0}$ = 7,071 L/s")
ax.plot(hh, (QI0 + (hh - H0) / R_HID) * 1e3, "--", color=CINZA, lw=1.2, label=r"tangente em $h_0$: inclinação $1/R$")
ax.plot([H0], [QI0 * 1e3], "o", color="k", ms=6, zorder=5)
ax.annotate("equilíbrio $h_0$ = 0,50 m\nentrada = saída", (H0, QI0 * 1e3), xytext=(0.52, 3.6), fontsize=9,
            arrowprops=dict(arrowstyle="->", lw=0.8))
ax.text(0.03, 9.6, "$h < h_0$: sai menos do que entra\n→ o nível sobe", fontsize=8.5, color=AZUL)
ax.text(0.93, 5.3, "$h > h_0$: sai mais do que entra\n→ o nível desce", fontsize=8.5, color=AZUL)
ax.text(0.01, 0.4, "fora do\ndomínio", fontsize=7.5, color=CINZA); ax.text(1.215, 0.4, "transborda", fontsize=7.5, color=CINZA)
ax.set_xlim(0, 1.3); ax.set_ylim(0, 13)
ax.set_xlabel("nível $h$ [m]"); ax.set_ylabel("vazão [L/s]  (1 L/s = 10⁻³ m³/s)")
ax.legend(loc="lower right", frameon=False)
eixos(ax)
salvar(fig, "fig-03-equilibrio-linearizacao.png")

# ----------------------------------------------------------------------------- R3(a) degrau a partir do equilibrio
T_DEG, DEG = 50.0, 0.20
qi_a = QI0 * (1 + DEG)
hf_a = (qi_a / K) ** 2
ta, ha = simular(H0, 650, qi=lambda t: QI0 if t < T_DEG else qi_a)
m = ta >= T_DEG
ta_r, ha_r = ta[m] - T_DEG, ha[m]
tm_a = tempos(ta_r, ha_r, H0, hf_a)
tf_a = tempos_fechado(H0, hf_a, qi_a)
hf_lin = H0 + R_HID * DEG * QI0
lin_a = H0 + R_HID * DEG * QI0 * (1 - np.exp(-np.clip(ta - T_DEG, 0, None) / TAU))
ex_a = h_fechado(ta_r, H0, qi_a)
# mesmo degrau integrado com a descontinuidade no inicio (t = 0): separa o erro causado pelo passo que a atravessa
ta2, ha2 = simular(H0, 600, qi=lambda t: qi_a)
erro_sem_desc = float(np.max(np.abs(ha2 - h_fechado(ta2, H0, qi_a))))
R["a"] = dict(erro_sem_descontinuidade=erro_sem_desc,deg=DEG, qi=qi_a, h_ini=H0, hf=hf_a, hf_sim=float(ha[-1]), hf_lin=hf_lin, sim=tm_a, fechado=tf_a,
              tau_local_final=A * 2 * np.sqrt(hf_a) / K, erro_max_fechado=float(np.max(np.abs(ha_r - ex_a))),
              h_antes=float(ha[ta < T_DEG][-1]))

fig, ax = plt.subplots(figsize=(6.6, 3.5))
ax.plot(ta, ha, color=AZUL, lw=2, label="simulação (modelo não linear)")
ax.plot(ta, lin_a, "--", color=CINZA, lw=1.3, label="linearização em $h_0$ (referência auxiliar)")
ax.axhline(hf_a, color=AZUL, lw=0.7, ls=":")
ax.axhspan(hf_a - 0.02 * (hf_a - H0), hf_a + 0.02 * (hf_a - H0), color=AZUL2, alpha=0.12, lw=0)
for nome, cor, txt in (("t10", "k", "10 %"), ("t63", LARANJA, "63,2 %"), ("t90", "k", "90 %"), ("ts2", VERDE, "±2 %")):
    tt = tm_a[nome] + T_DEG
    yy = np.interp(tt, ta, ha)
    ax.plot(tt, yy, "o", color=cor, ms=5, zorder=6)
    ax.annotate(f"{txt}: {br(tm_a[nome], 1)} s", (tt, yy), xytext=(tt + 18, yy - 0.025), fontsize=8, color=cor)
ax.annotate("degrau +20 % em $q_i$\n(t = 50 s)", (T_DEG, H0), xytext=(70, 0.53), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.8))
ax.text(560, hf_a + 0.006, f"{br(hf_a, 3)} m", fontsize=8, color=AZUL)
ax.text(560, hf_lin - 0.017, f"{br(hf_lin, 3)} m", fontsize=8, color=CINZA)
ax.set_xlim(0, 650); ax.set_ylim(0.48, 0.75)
ax.set_xlabel("tempo $t$ [s]"); ax.set_ylabel("nível $h$ [m]")
ax.legend(loc="lower right", frameon=False)
eixos(ax); rodape(fig)
salvar(fig, "fig-04-ensaio-a-degrau.png")

# degrau pequeno (+1 %) para medir a constante de tempo local (confirma o polo)
tp, hp = simular(H0, 700, qi=lambda t: QI0 * 1.01)
hfp = (QI0 * 1.01 / K) ** 2
R["degrau_pequeno"] = dict(t63=tempos(tp, hp, H0, hfp)["t63"], hf=hfp)

# ----------------------------------------------------------------------------- R3(b) condicao inicial nao nula
H_B = 1.00
tb, hb = simular(H_B, 600)                                  # volta ao equilibrio com qi = qi0
tv, hv = simular(H_B, 120, qi=lambda t: 0.0, parar_vazio=True)   # drenagem livre (qi = 0)
tm_b = tempos(tb, hb, H_B, H0)
tf_b = tempos_fechado(H_B, H0, QI0)
lin_b = H0 + (H_B - H0) * np.exp(-tb / TAU)
t_vazio = 2 * A * np.sqrt(H_B) / K
t_vazio_sim = float(tv[-1])
t_hmin = t_fechado(H_MIN, H_B, 0.0)
ex_b = h_fechado(tb, H_B, QI0)
ex_v = h_fechado(tv, H_B, 0.0)
R["b"] = dict(h_ini=H_B, hf_sim=float(hb[-1]), sim=tm_b, fechado=tf_b, t_vazio=t_vazio, t_vazio_sim=t_vazio_sim,
              t_hmin=t_hmin, t_hmin_sim=cruza(tv, hv, H_MIN), h50_fechado=(1 - K / (2 * A) * 50) ** 2,
              h50_sim=float(np.interp(50, tv, hv)), erro_max_fechado=float(np.max(np.abs(hb - ex_b))),
              erro_max_vazio=float(np.max(np.abs(hv - ex_v))),
              t63_lin=TAU, erro_lin_max=float(np.max(np.abs(hb - lin_b))))

fig, ax = plt.subplots(figsize=(6.6, 3.5))
ax.axhspan(H_MAX, 1.3, color=CINZA, alpha=0.12, lw=0); ax.axhspan(0, H_MIN, color=CINZA, alpha=0.12, lw=0)
ax.plot(tb, hb, color=AZUL, lw=2, label=r"$h(0)$ = 1,0 m, $q_i = q_{i0}$ (volta ao equilíbrio)")
ax.plot(tb, lin_b, "--", color=CINZA, lw=1.2, label="linearização em $h_0$ (referência auxiliar)")
ax.plot(tv, hv, color=LARANJA, lw=2, label=r"$h(0)$ = 1,0 m, $q_i$ = 0 (drenagem livre)")
tt = np.linspace(0, t_vazio, 30)
ax.plot(tt, (1 - K / (2 * A) * tt) ** 2, "x", color="k", ms=4, label=r"solução fechada $\sqrt{h}=\sqrt{h(0)}-\frac{k}{2A}t$")
y63 = np.interp(tm_b["t63"], tb, hb)
ax.plot(tm_b["t63"], y63, "o", color=AZUL, ms=5); ax.annotate(f"63,2 %: {br(tm_b['t63'], 1)} s", (tm_b["t63"], y63),
                                                             xytext=(tm_b["t63"] + 20, y63 + 0.05), fontsize=8, color=AZUL)
yts = np.interp(tm_b["ts2"], tb, hb)
ax.plot(tm_b["ts2"], yts, "o", color=VERDE, ms=5); ax.annotate(f"±2 %: {br(tm_b['ts2'], 1)} s", (tm_b["ts2"], yts),
                                                              xytext=(tm_b["ts2"] + 10, yts + 0.06), fontsize=8, color=VERDE)
ax.plot(t_vazio_sim, 0, "o", color=LARANJA, ms=5)
ax.annotate(f"vazio: {br(t_vazio_sim, 2)} s", (t_vazio_sim, 0), xytext=(t_vazio_sim + 15, 0.05), fontsize=8, color=LARANJA)
ax.plot(t_hmin, H_MIN, "s", color=LARANJA, ms=4)
ax.annotate(f"sai do domínio ($h_{{mín}}$): {br(t_hmin, 1)} s", (t_hmin, H_MIN), xytext=(t_hmin + 25, 0.2), fontsize=8,
            color=LARANJA, arrowprops=dict(arrowstyle="->", lw=0.6, color=LARANJA))
ax.set_xlim(0, 450); ax.set_ylim(0, 1.3)
ax.set_xlabel("tempo $t$ [s]"); ax.set_ylabel("nível $h$ [m]")
ax.legend(loc="upper right", frameon=False, fontsize=8)
eixos(ax); rodape(fig)
salvar(fig, "fig-05-ensaio-b-condicao-inicial.png")

# ----------------------------------------------------------------------------- R3(c) senoide na frequencia de canto
W = 1 / TAU
AMP = 0.10
T_SEN = 8 * 2 * np.pi / W
tc, hc = simular(H0, T_SEN, qi=lambda t: QI0 * (1 + AMP * np.sin(W * t)))
per = 2 * np.pi / W
m = tc >= T_SEN - 2 * per                       # ultimos 2 periodos (regime)
tt_, yy_ = tc[m], hc[m]
I = 2 * np.trapezoid((yy_ - yy_.mean()) * np.sin(W * tt_), tt_) / (tt_[-1] - tt_[0])
Q = 2 * np.trapezoid((yy_ - yy_.mean()) * np.cos(W * tt_), tt_) / (tt_[-1] - tt_[0])
amp_sim, fase_sim = np.hypot(I, Q), np.degrees(np.arctan2(Q, I))
amp_lin = R_HID * AMP * QI0 / np.sqrt(2)
R["c"] = dict(amp_rel=AMP, w=W, periodo=per, amp_lin=amp_lin, fase_lin=-45.0, amp_sim=amp_sim, fase_sim=fase_sim,
              media_sim=float(yy_.mean()), max_sim=float(yy_.max()), min_sim=float(yy_.min()),
              atraso_lin=per / 8, atraso_sim=-fase_sim / 360 * per)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 4.4), sharex=True, gridspec_kw=dict(height_ratios=[1, 2]))
ax1.plot(tc, QI0 * (1 + AMP * np.sin(W * tc)) * 1e3, color=LARANJA, lw=1.4)
ax1.set_ylabel("$q_i$ [L/s]")
ax1.set_title(f"entrada: $q_i = q_{{i0}}(1 + 0{{,}}1\\,\\sin\\omega t)$, ω = 1/τ = {br(W, 5)} rad/s (período {br(per, 1)} s)",
              fontsize=9)
ax2.plot(tc, hc, color=AZUL, lw=1.8, label="simulação (não linear)")
ax2.plot(tc, H0 + amp_lin * np.sin(W * tc - np.pi / 4) - amp_lin * np.sin(-np.pi / 4) * np.exp(-tc / TAU), "--",
         color=CINZA, lw=1.1, label="linearização: amplitude 0,0707 m, fase −45°")
k0 = int(np.ceil((T_SEN - 2 * per) / per))
pico_in = (np.pi / 2) / W + k0 * per
pico_out = tt_[np.argmax(yy_)]
ax2.axvline(pico_in, color=LARANJA, lw=0.8, ls=":")
ax2.axvline(pico_out, color=AZUL, lw=0.8, ls=":")
ax2.annotate("", xy=(pico_out, H0 + 0.095), xytext=(pico_in, H0 + 0.095),
             arrowprops=dict(arrowstyle="<->", lw=0.9))
ax2.text(pico_in - 30, H0 + 0.103, f"atraso {br(pico_out - pico_in, 1)} s (⅛ de período = 45°)", ha="right", fontsize=8)
ax2.plot(pico_out, yy_.max(), "o", color=AZUL, ms=4)
ax2.text(pico_out + 20, yy_.max() - 0.004, f"máx {br(yy_.max(), 3)} m", fontsize=8, color=AZUL)
imin = np.argmin(yy_); ax2.plot(tt_[imin], yy_[imin], "o", color=AZUL, ms=4)
ax2.text(tt_[imin], yy_[imin] - 0.016, ha="center", s=f"mín {br(yy_[imin], 3)} m", fontsize=8, color=AZUL)
ax2.set_ylim(0.40, 0.63)
ax2.set_xlabel("tempo $t$ [s]"); ax2.set_ylabel("nível $h$ [m]")
ax2.legend(loc="lower left", frameon=False, ncol=2, fontsize=8)
eixos(ax1, ax2); rodape(fig)
salvar(fig, "fig-06-ensaio-c-senoide.png")

# ----------------------------------------------------------------------------- R4: erro simulacao x solucao fechada
fig, ax = plt.subplots(figsize=(6.6, 2.6))
ax.semilogy(ta_r, np.abs(ha_r - ex_a) + 1e-17, color=AZUL, lw=1, label="(a) degrau")
ax.semilogy(tb, np.abs(hb - ex_b) + 1e-17, color=VERDE, lw=1, label="(b) volta de 1,0 m")
ax.semilogy(tv, np.abs(hv - ex_v) + 1e-17, color=LARANJA, lw=1, label="(b) drenagem livre")
ax.set_ylim(1e-16, 1e-6)
ax.set_xlabel("tempo após o início do transitório [s]"); ax.set_ylabel("|simulado − fechado| [m]")
ax.legend(loc="upper right", frameon=False, ncol=3)
ax.xaxis.set_major_formatter(virgula); rodape(fig)
salvar(fig, "fig-07-erro-simulacao-fechada.png")

# ----------------------------------------------------------------------------- R5: sensibilidade parametrica
R["sens"] = {}

# P1: area A (degrau +20 % a partir do equilibrio)
NIV_A = [0.125, 0.25, 0.50, 1.0, 2.0]
cores = ["#9ECAE1", "#6BAED6", AZUL, "#E6A35C", "#B85C00"]
fig, ax = plt.subplots(figsize=(6.6, 3.3))
lst = []
for a, c in zip(NIV_A, cores):
    t_, h_ = simular(H0, 1500, qi=lambda t: qi_a, a=a)
    tm = tempos(t_, h_, H0, hf_a)
    lst.append(dict(A=a, t63=tm["t63"], ts2=tm["ts2"], hf=float(h_[-1]), tau_lin=a * R_HID))
    ax.plot(t_, h_, color=c, lw=2 if a == A else 1.4, label=f"A = {br(a, 3).rstrip('0').rstrip(',')} m²" +
            (" (nominal)" if a == A else "") + f" → 63 % em {br(tm['t63'], 0)} s")
    ax.plot(tm["t63"], H0 + 0.632 * (hf_a - H0), "o", color=c, ms=4)
ax.axhline(hf_a, color="k", lw=0.6, ls=":"); ax.text(1300, hf_a + 0.005, f"{br(hf_a, 2)} m para todos", fontsize=8)
ax.set_xlim(0, 1500); ax.set_ylim(0.49, 0.76)
ax.set_xlabel("tempo $t$ [s]"); ax.set_ylabel("nível $h$ [m]")
ax.set_title("E se a área do tanque mudar? (degrau +20 % em $q_i$ a partir de $h_0$)", fontsize=9.5)
ax.legend(loc="lower right", frameon=False, fontsize=8)
eixos(ax); rodape(fig)
salvar(fig, "fig-08-sensibilidade-area.png")
R["sens"]["A"] = lst

# P2: coeficiente k (valvula de saida muda em t = 0, qi = qi0 mantida)
NIV_K = [0.005, 0.0075, 0.010, 0.015, 0.020]
cores = ["#B85C00", "#E6A35C", AZUL, "#6BAED6", "#9ECAE1"]
fig, ax = plt.subplots(figsize=(6.6, 3.3))
ax.axhspan(H_MAX, 2.2, color="#D62728", alpha=0.08, lw=0)
ax.text(1100, 1.4, "acima de $h_{máx}$: o tanque transborda (modelo deixa de valer)", fontsize=8, color="#A01E1E")
ax.axhspan(0, H_MIN, color=CINZA, alpha=0.12, lw=0)
lst = []
for k, c in zip(NIV_K, cores):
    t_, h_ = simular(H0, 3000, k=k)
    heq = (QI0 / k) ** 2
    rec = dict(k=k, h_eq=heq, tau_eq=2 * A * np.sqrt(heq) / k, hf_sim=float(h_[-1]),
               t_transborda=cruza(t_, h_, H_MAX))
    if heq != H0:
        rec["t63"] = tempos(t_, h_, H0, heq)["t63"]
    lst.append(rec)
    ax.plot(t_, h_, color=c, lw=2 if k == K else 1.4,
            label=f"k = {br(k, 4).rstrip('0')}" + (" (nominal)" if k == K else "") + f" → $h_{{eq}}$ = {br(heq, 3)} m")
    if not np.isnan(rec["t_transborda"]):
        ax.plot(rec["t_transborda"], H_MAX, "X", color="#A01E1E", ms=7, zorder=6)
        ax.annotate(f"transborda em {br(rec['t_transborda'], 0)} s", (rec["t_transborda"], H_MAX),
                    xytext=(rec["t_transborda"] + 80, 1.05), fontsize=8, color="#A01E1E",
                    arrowprops=dict(arrowstyle="->", lw=0.6, color="#A01E1E"))
ax.set_xlim(0, 3000); ax.set_ylim(0, 2.1)
ax.set_xlabel("tempo $t$ [s]"); ax.set_ylabel("nível $h$ [m]")
ax.set_title("E se a válvula de saída abrir ou fechar? ($k$ muda em t = 0, $q_i = q_{i0}$ mantida)", fontsize=9.5)
ax.legend(loc="center right", frameon=False, fontsize=8)
eixos(ax); rodape(fig)
salvar(fig, "fig-09-sensibilidade-k.png")
R["sens"]["k"] = lst

# P3: amplitude do degrau de vazao (a partir do equilibrio)
NIV_D = [-0.50, -0.20, 0.20, 0.50, 1.00]
cores = ["#9ECAE1", "#6BAED6", AZUL, "#E6A35C", "#B85C00"]
fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw=dict(width_ratios=[1.6, 1]))
ax.axhspan(H_MAX, 2.2, color="#D62728", alpha=0.08, lw=0); ax.axhspan(0, H_MIN, color=CINZA, alpha=0.12, lw=0)
lst = []
for d, c in zip(NIV_D, cores):
    q = QI0 * (1 + d)
    t_, h_ = simular(H0, 1500, qi=lambda t: q)
    heq = (q / K) ** 2
    rec = dict(deg=d, h_eq=heq, h_lin=H0 + R_HID * d * QI0, t63=tempos(t_, h_, H0, heq)["t63"],
               tau_eq=2 * A * np.sqrt(heq) / K, t_transborda=cruza(t_, h_, H_MAX))
    lst.append(rec)
    ax.plot(t_, h_, color=c, lw=2 if d == DEG else 1.4, label=f"{'+' if d > 0 else '−'}{abs(d) * 100:.0f} %")
    if not np.isnan(rec["t_transborda"]):
        ax.plot(rec["t_transborda"], H_MAX, "X", color="#A01E1E", ms=7, zorder=6)
ax.set_xlim(0, 1500); ax.set_ylim(0, 2.1)
ax.set_xlabel("tempo $t$ [s]"); ax.set_ylabel("nível $h$ [m]")
ax.legend(title="degrau em $q_i$", loc="lower right", bbox_to_anchor=(1, 0.17), frameon=False, fontsize=8, title_fontsize=8, ncol=2)
ax.set_title("E se o degrau for maior?", fontsize=9.5)
dd = np.linspace(-0.6, 1.05, 100)
axb.plot(dd * 100, H0 * (1 + dd) ** 2, color=AZUL, lw=2, label=r"real: $h_{eq}=(q_i/k)^2$")
axb.plot(dd * 100, H0 + R_HID * dd * QI0, "--", color=CINZA, lw=1.3, label="linearizado (reta)")
for r_, c in zip(lst, cores):
    axb.plot(r_["deg"] * 100, r_["h_eq"], "o", color=c, ms=5)
axb.axhline(H_MAX, color="#A01E1E", lw=0.8, ls=":")
axb.set_xlabel("degrau em $q_i$ [%]"); axb.set_ylabel("nível final [m]")
axb.legend(loc="upper left", frameon=False, fontsize=8)
eixos(ax, axb); rodape(fig)
salvar(fig, "fig-10-sensibilidade-amplitude.png")
R["sens"]["deg"] = lst


# ----------------------------------------------------------------------------- saida
def limpo(o):
    if isinstance(o, dict):
        return {k: limpo(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpo(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else float(o)
    return o


R["solver"] = dict(metodo="RK45", rtol=RTOL, atol=ATOL, max_step=MAX_STEP, dt_saida=DT_OUT)
R["parametros"] = dict(A=A, k=K, h_max=H_MAX, h_min=H_MIN, h0=H0, qi0=QI0)
with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as fp:
    json.dump(limpo(R), fp, indent=1, ensure_ascii=False)
print(json.dumps(limpo({k: R[k] for k in ("algebra", "a", "degrau_pequeno", "b", "c")}), indent=1))
