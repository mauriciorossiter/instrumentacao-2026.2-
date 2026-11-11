# -*- coding: utf-8 -*-
"""
ECOM060 - Fase 2, Entrega 02 (G05): validacao do equivalente eletrico contra a Entrega 01.

Le os dados capturados no HIL virtual (rodar_vhil_e2.py -> .npz), recalcula as curvas da Entrega 01
(mesmo modelo e mesmo solver: solve_ivp RK45) e gera as figuras do relatorio e resultados_e2.json.
Uso:  python analisar_e2.py <pasta_npz_vhil> <pasta_figuras> <saida_json>
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.integrate import solve_ivp

SRC, FIG, OUT = sys.argv[1:4]
os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------- Entrega 01 (dossie)
A, K, H0, H_MAX, H_MIN = 0.50, 0.010, 0.50, 1.20, 0.10
QI0 = K * np.sqrt(H0)
R_HID = 2 * np.sqrt(H0) / K
TAU = A * R_HID
T_EV = 50.0                                     # evento do ensaio (s, escala do tanque)
# ---------------------------------------------------------------- escalas e circuito (R1)
KV, KI, KT = 10.0, 1000.0, 100.0
C_POR_M2 = KI / (KV * KT)
C_NOM = A * C_POR_M2
K_E = K * KI / np.sqrt(KV)
I0 = KI * QI0
V0 = KV * H0
R_LIN = 2 * np.sqrt(V0) / K_E
TAU_C = R_LIN * C_NOM

AZUL, AZUL2, LARANJA, CINZA, VERDE, VERM = "#185079", "#3A86B0", "#D9822B", "#7F7F7F", "#2E8B57", "#A01E1E"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "mathtext.fontset": "stix",
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 200, "legend.fontsize": 8.5})
virgula = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def br(v, d=2):
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def eixos(*axs):
    for ax in axs:
        ax.xaxis.set_major_formatter(virgula); ax.yaxis.set_major_formatter(virgula)


def salvar(fig, nome):
    fig.savefig(os.path.join(FIG, nome), bbox_inches="tight"); plt.close(fig); print("figura:", nome)


def rodape(fig, txt="VHIL: HIL virtual do Typhoon HIL Control Center 2026.2, passo 20 µs (= 2 ms no tanque). "
                    "Entrega 01: Python/SciPy, RK45, rtol 10⁻¹⁰."):
    fig.text(0.99, -0.06, txt, ha="right", va="top", fontsize=6.5, color=CINZA)


def simular(h_ini, t_fim, qi=lambda t: QI0, a=A, k=K, dt=0.05):
    f = lambda t, h: [(qi(t) - k * np.sqrt(max(h[0], 0.0))) / a]
    ev = lambda t, h: h[0] - 1e-12
    ev.terminal, ev.direction = True, -1
    s = solve_ivp(f, (0, t_fim), [h_ini], method="RK45", t_eval=np.arange(0, t_fim, dt), rtol=1e-10,
                  atol=1e-12, max_step=0.1, events=ev)
    t, h = s.t, s.y[0]
    if s.t_events[0].size:
        t, h = np.append(t, s.t_events[0][0]), np.append(h, 0.0)
    return t, h


def cruza(t, y, nivel):
    s = np.sign(y - nivel)
    i = np.where(np.diff(s) != 0)[0]
    if not i.size:
        return float("nan")
    i = i[0]
    return float(t[i] + (nivel - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))


def tempos(t, h, h_i, h_f, t0=0.0):
    r = {n: cruza(t, h, h_i + fr * (h_f - h_i)) - t0 for n, fr in
         (("t10", .10), ("t63", .632), ("t90", .90), ("ts5", .95), ("ts2", .98))}
    r["tr"] = r["t90"] - r["t10"]
    return r


def vhil(n):
    d = np.load(os.path.join(SRC, n + ".npz"))
    t = d["t_fisico_s"]
    ok = np.concatenate([[True], np.diff(t) > 0])       # relogio do ensaio monotonico
    return {k: d[k][ok] for k in d.files} | {"t": t[ok]}


def regime(d, t0):
    m = d["t"] >= t0
    return float(np.mean(d["h_m"][m]))


R = {"escala": dict(kv=KV, ki=KI, kt=KT, C=C_NOM, K_e=K_E, I0=I0, V0=V0, R_lin=R_LIN, tau_c=TAU_C,
                    c_por_m2=C_POR_M2)}

# ================================================================ fig 01: analogia (esquema lado a lado)
import schemdraw
import schemdraw.elements as elm
from matplotlib.patches import Rectangle, FancyArrowPatch

fig = plt.figure(figsize=(9.6, 3.9))
axT = fig.add_axes([0.0, 0.0, 0.36, 1.0]); axT.set_axis_off(); axT.set_xlim(0, 10); axT.set_ylim(-1.0, 10)
axT.add_patch(Rectangle((2.0, 1.2), 5.2, 6.6, fill=False, lw=2, ec=AZUL))
axT.add_patch(Rectangle((2.0, 1.2), 5.2, 3.6, color=AZUL2, alpha=0.35, lw=0))
axT.annotate("", xy=(3.3, 6.3), xytext=(3.3, 9.0), arrowprops=dict(arrowstyle="-|>", lw=2, color=LARANJA))
axT.text(3.6, 8.5, r"$q_i$ (bomba)", color=LARANJA, fontsize=11)
axT.annotate("", xy=(8.9, 1.55), xytext=(7.2, 1.55), arrowprops=dict(arrowstyle="-|>", lw=2, color=AZUL))
axT.text(7.25, 0.45, r"$q_o=k\sqrt{h}$", color=AZUL, fontsize=11)
axT.annotate("", xy=(4.0, -0.6), xytext=(4.0, 1.2), arrowprops=dict(arrowstyle="-|>", lw=1.6, color=CINZA))
axT.text(3.0, -0.5, r"$q_d$", color=CINZA, fontsize=11)
axT.annotate("", xy=(1.5, 4.8), xytext=(1.5, 1.2), arrowprops=dict(arrowstyle="<->", lw=1.2))
axT.text(0.55, 2.9, r"$h$", fontsize=13)
axT.text(4.6, 3.0, r"área $A$", ha="center", fontsize=11, color=AZUL)
axT.text(4.6, 9.6, "Domínio hidráulico (Entrega 01)", ha="center", fontsize=11, weight="bold", color=AZUL)

axC = fig.add_axes([0.40, 0.0, 0.60, 0.92]); axC.set_axis_off()
tmp_png = os.path.join(FIG, "_circ_tmp.png")
with schemdraw.Drawing(show=False) as d:
    d.config(unit=2.4, fontsize=13, lw=1.5, font="Times New Roman")
    d += elm.SourceI().up().at((0, 0)).color(LARANJA).label("$i_i$\nbomba", loc="bottom", ofst=0.25)
    d += elm.Line().right(2.6).at((0, 2.4))
    d += elm.Dot().at((2.6, 2.4))
    d += elm.Capacitor().down().at((2.6, 2.4)).color(AZUL).label("$C$\nárea", loc="bottom", ofst=0.2)
    d += elm.Line().right(2.6).at((2.6, 2.4))
    d += elm.Dot().at((5.2, 2.4))
    d += elm.SourceControlledI().down().at((5.2, 2.4)).color(AZUL).label("$K_e\\sqrt{v}$\norifício", loc="bottom",
                                                                          ofst=0.2)
    d += elm.Line().right(2.6).at((5.2, 2.4))
    d += elm.SourceI().down().at((7.8, 2.4)).color(CINZA).label("$i_d$\nretirada", loc="bottom", ofst=0.2)
    d += elm.Line().left(7.8).at((7.8, 0))
    d += elm.Ground().at((2.6, 0))
    d += elm.Label().at((3.9, 3.0)).label(r"nó 'nível':  $v = k_v\,h$", fontsize=14)
    d.save(tmp_png, dpi=220)
axC.imshow(plt.imread(tmp_png)); os.remove(tmp_png)
axC.set_title("Domínio elétrico (TyphoonSim)", fontsize=11, weight="bold", color=AZUL)
salvar(fig, "fig-01-analogia-tanque-circuito.png")

# ================================================================ fig 02: caracteristica do orificio
vv = np.linspace(0, 13, 400)
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.plot(vv, K_E * np.sqrt(vv), color=AZUL, lw=2, label=r"orifício: $i_o = K_e\sqrt{v}$  (bloco sqrt + fonte controlada)")
ax.plot(vv, I0 + (vv - V0) / R_LIN, "--", color=CINZA, lw=1.3,
        label=rf"tangente em $V_0$ = 5 V: resistor $R_{{lin}}$ = {br(R_LIN, 3)} Ω")
ax.axhline(I0, color=LARANJA, lw=1, ls=":"); ax.text(0.3, I0 + 0.3, rf"$I_0$ = {br(I0, 3)} A (bomba)", color=LARANJA, fontsize=8.5)
ax.plot(V0, I0, "o", color=AZUL, ms=6)
ax.annotate("equilíbrio: 5 V ↔ 0,50 m\n7,071 A ↔ 7,071 L/s", (V0, I0), xytext=(6.8, 4.2), fontsize=8.5,
            arrowprops=dict(arrowstyle="->", lw=0.8))
ax.axvspan(12, 13, color=VERM, alpha=0.08, lw=0); ax.text(12.05, 1.0, "transborda\n(h > 1,2 m)", fontsize=7.5, color=VERM)
ax.set_xlim(0, 13); ax.set_ylim(0, 12.5)
ax.set_xlabel("tensão no nó $v$ [V]   (10 V = 1 m)"); ax.set_ylabel("corrente $i_o$ [A]   (1 A = 1 L/s)")
ax.legend(loc="lower right", frameon=False)
eixos(ax)
salvar(fig, "fig-02-caracteristica-orificio.png")

# ================================================================ R3 (a) degrau
dA = vhil("a")
qa = QI0 * 1.2; hfa = (qa / K) ** 2
te, he = simular(H0, 720, qi=lambda t: QI0 if t < T_EV else qa)
mv = dA["t"] >= T_EV
tm_v = tempos(dA["t"][mv], dA["h_m"][mv], H0, hfa, T_EV)
tm_e = tempos(te[te >= T_EV], he[te >= T_EV], H0, hfa, T_EV)
dif_a = np.interp(dA["t"], te, he) - dA["h_m"]
R["a"] = dict(vhil=tm_v, e01=tm_e, hf_vhil=regime(dA, 700), hf_e01=float(he[-1]), hf_teo=hfa,
              h_antes_vhil=float(np.mean(dA["h_m"][(dA["t"] > 5) & (dA["t"] < 49)])),
              dif_max_mm=float(np.max(np.abs(dif_a[dA["t"] >= T_EV])) * 1e3))
d1 = vhil("a1pct")
q1 = QI0 * 1.01; hf1 = (q1 / K) ** 2
t1, h1 = simular(H0, 760, qi=lambda t: QI0 if t < T_EV else q1)
R["pequeno"] = dict(t63_vhil=tempos(d1["t"][d1["t"] >= T_EV], d1["h_m"][d1["t"] >= T_EV], H0, hf1, T_EV)["t63"],
                    t63_e01=tempos(t1[t1 >= T_EV], h1[t1 >= T_EV], H0, hf1, T_EV)["t63"],
                    hf_vhil=regime(d1, 740), hf_e01=float(h1[-1]))
R["pequeno"]["ganho_vhil"] = (R["pequeno"]["hf_vhil"] - H0) / (0.01 * QI0)
R["pequeno"]["ganho_e01"] = (R["pequeno"]["hf_e01"] - H0) / (0.01 * QI0)

fig, (ax, axd) = plt.subplots(2, 1, figsize=(6.6, 4.3), sharex=True, gridspec_kw=dict(height_ratios=[2.3, 1]))
ax.plot(te, he, color=AZUL, lw=2.4, label="Entrega 01 (modelo hidráulico, Python)")
ax.plot(dA["t"], dA["h_m"], "--", color=LARANJA, lw=1.4, label="equivalente elétrico em VHIL (v/kᵥ)")
for nome, txt in (("t63", "63,2 %"), ("ts2", "±2 %")):
    tt = tm_v[nome] + T_EV; yy = np.interp(tt, dA["t"], dA["h_m"])
    ax.plot(tt, yy, "o", color=LARANJA, ms=5, zorder=6)
    ax.annotate(f"{txt}: {br(tm_v[nome], 1)} s (E01 {br(tm_e[nome], 1)} s)", (tt, yy), xytext=(tt + 25, yy - 0.035),
                fontsize=8)
ax.annotate("degrau +20 % em $q_i$\n(t = 50 s = 0,5 s no circuito)", (T_EV, H0), xytext=(80, 0.52), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.8))
ax.set_ylim(0.48, 0.75); ax.set_ylabel("nível $h$ [m]")
ax.legend(loc="lower right", frameon=False)
axd.plot(dA["t"][mv], dif_a[mv] * 1e3, color=VERDE, lw=1)
axd.set_ylabel("E01 − VHIL [mm]"); axd.set_xlabel("tempo no tanque $t$ [s]   (= 100 × tempo no circuito)")
axd.set_xlim(0, 720)
eixos(ax, axd); rodape(fig)
salvar(fig, "fig-05-validacao-degrau.png")

# ================================================================ R3 (b) condicao inicial e drenagem
dB, dB2 = vhil("b"), vhil("b2")
tb, hb = simular(1.0, 470)
tv, hv = simular(1.0, 130, qi=lambda t: 0.0)
mb = dB["t"] >= T_EV
tbv, hbv = dB["t"][mb] - T_EV, dB["h_m"][mb]
tb2, hb2 = dB2["t"] - T_EV, dB2["h_m"]
mvz = tb2 >= 0
R["b"] = dict(vhil=tempos(tbv, hbv, 1.0, H0), e01=tempos(tb, hb, 1.0, H0),
              hf_vhil=regime(dB, 500), hf_e01=float(hb[-1]),
              t_vazio_vhil=cruza(tb2[mvz], hb2[mvz], 1e-3), t_vazio_e01=cruza(tv, hv, 1e-3),
              t_hmin_vhil=cruza(tb2[mvz], hb2[mvz], H_MIN), t_hmin_e01=cruza(tv, hv, H_MIN),
              h_pre_vhil=float(np.mean(dB["h_m"][(dB["t"] > 5) & (dB["t"] < 49)])),
              h_min_vhil=float(np.min(hb2[mvz])))
dif_b = np.interp(tbv, tb, hb) - hbv
dif_v = np.interp(tb2[mvz], tv, hv) - hb2[mvz]
R["b"]["dif_max_mm"] = float(np.max(np.abs(dif_b)) * 1e3)
R["b"]["dif_max_vazio_mm"] = float(np.max(np.abs(dif_v[tb2[mvz] < 95])) * 1e3)

fig, (ax, axd) = plt.subplots(2, 1, figsize=(6.6, 4.3), sharex=True, gridspec_kw=dict(height_ratios=[2.3, 1]))
ax.axhspan(0, H_MIN, color=CINZA, alpha=0.12, lw=0)
ax.plot(tb, hb, color=AZUL, lw=2.4, label="E01: h(0) = 1,0 m, bomba ligada")
ax.plot(tbv, hbv, "--", color=LARANJA, lw=1.4, label="VHIL: h(0) = 1,0 m, bomba ligada")
ax.plot(tv, hv, color=AZUL2, lw=2.4, label="E01: h(0) = 1,0 m, bomba desligada")
ax.plot(tb2[mvz], hb2[mvz], "--", color=VERM, lw=1.4, label="VHIL: h(0) = 1,0 m, bomba desligada")
tvz = R["b"]["t_vazio_vhil"]
ax.plot(tvz, 0, "o", color=VERM, ms=5)
ax.annotate(f"chega a 1 mm: {br(tvz, 1)} s (E01 {br(R['b']['t_vazio_e01'], 1)} s)", (tvz, 0), xytext=(tvz + 20, 0.12), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.7))
ax.set_ylim(0, 1.1); ax.set_ylabel("nível $h$ [m]")
ax.legend(loc="upper right", frameon=False, fontsize=8)
axd.plot(tbv, dif_b * 1e3, color=VERDE, lw=1, label="bomba ligada")
axd.plot(tb2[mvz & (tb2 < 99)], dif_v[tb2[mvz] < 99] * 1e3, color=VERM, lw=1, label="drenagem (até 99 s)")
axd.legend(loc="upper right", frameon=False, fontsize=7.5, ncol=2)
axd.set_ylabel("E01 − VHIL [mm]"); axd.set_xlabel("tempo após liberar a condição inicial [s]")
axd.set_xlim(0, 450)
eixos(ax, axd); rodape(fig)
salvar(fig, "fig-06-validacao-condicao-inicial.png")

# ================================================================ R3 (c) senoide na frequencia de canto
dC = vhil("c")
W = 1 / TAU; per = 2 * np.pi / W; T_SEN = 8 * per
tcv, hcv = dC["t"] - T_EV, dC["h_m"]
tc, hc = simular(H0, T_SEN, qi=lambda t: QI0 * (1 + 0.1 * np.sin(W * t)), dt=0.2)


def amp_fase(t, y):
    m = (t >= T_SEN - 2 * per) & (t <= T_SEN)
    tt, yy = t[m], y[m]
    I = 2 * np.trapezoid((yy - yy.mean()) * np.sin(W * tt), tt) / (tt[-1] - tt[0])
    Q = 2 * np.trapezoid((yy - yy.mean()) * np.cos(W * tt), tt) / (tt[-1] - tt[0])
    return float(np.hypot(I, Q)), float(np.degrees(np.arctan2(Q, I))), float(yy.mean())


av, fv, mv_ = amp_fase(tcv, hcv); ae, fe, me = amp_fase(tc, hc)
R["c"] = dict(amp_vhil=av, fase_vhil=fv, media_vhil=mv_, amp_e01=ae, fase_e01=fe, media_e01=me,
              amp_lin=R_HID * 0.1 * QI0 / np.sqrt(2), periodo=per)
m0 = (tcv >= 0) & (tcv <= T_SEN - 1)
dif_c = np.interp(tcv[m0], tc, hc) - hcv[m0]
R["c"]["dif_max_mm"] = float(np.max(np.abs(dif_c)) * 1e3)
fig, (ax, axd) = plt.subplots(2, 1, figsize=(6.6, 4.3), sharex=True, gridspec_kw=dict(height_ratios=[2.3, 1]))
ax.plot(tc, hc, color=AZUL, lw=2.4, label="Entrega 01")
ax.plot(tcv[m0], hcv[m0], "--", color=LARANJA, lw=1.2, label="equivalente elétrico em VHIL")
ax.set_ylim(0.40, 0.62); ax.set_ylabel("nível $h$ [m]")
ax.set_title(f"$q_i = q_{{i0}}(1+0{{,}}1\\sin\\omega t)$, ω = 1/τ (período {br(per, 1)} s = {br(per / KT, 3)} s no circuito)",
             fontsize=9)
ax.text(60, 0.41, f"regime: amplitude {br(av, 4)} m (E01 {br(ae, 4)}), fase {br(fv, 2)}° (E01 {br(fe, 2)}°)", fontsize=8)
ax.legend(loc="upper right", frameon=False, ncol=2)
axd.plot(tcv[m0], dif_c * 1e3, color=VERDE, lw=1)
axd.set_ylabel("E01 − VHIL [mm]"); axd.set_xlabel("tempo após o início da senoide [s]")
axd.set_xlim(0, T_SEN)
eixos(ax, axd); rodape(fig)
salvar(fig, "fig-07-validacao-senoide.png")

# ================================================================ R4 sensibilidade: area A
NIV_A = [("A0125", 0.125), ("A025", 0.25), ("A05", 0.5), ("A1", 1.0), ("A2", 2.0)]
cores = ["#9ECAE1", "#6BAED6", AZUL, "#E6A35C", "#B85C00"]
fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.6, 3.3), gridspec_kw=dict(width_ratios=[1.7, 1]))
lst = []
for (n, a), c in zip(NIV_A, cores):
    d = vhil(n)
    te_, he_ = simular(H0, 1500, qi=lambda t: qa, a=a)
    tvv, hvv = d["t"] - T_EV, d["h_m"]
    m = tvv >= 0
    t63v = tempos(tvv[m], hvv[m], H0, hfa)["t63"]; t63e = tempos(te_, he_, H0, hfa)["t63"]
    lst.append(dict(A=a, t63_vhil=t63v, t63_e01=t63e, hf_vhil=float(np.mean(hvv[tvv > 1480])), hf_e01=float(he_[-1]),
                    C=a * C_POR_M2))
    ax.plot(te_, he_, color=c, lw=2.2, alpha=0.9)
    ax.plot(tvv[m], hvv[m], "--", color="k", lw=0.8)
ax.plot([], [], color=AZUL, lw=2.2, label="Entrega 01"); ax.plot([], [], "--", color="k", lw=0.8, label="VHIL")
for (n, a), c in zip(NIV_A, cores):
    ax.plot([], [], color=c, lw=4, label=f"A = {br(a, 3).rstrip('0').rstrip(',')} m² → C = {br(a * C_POR_M2, 3).rstrip('0').rstrip(',')} F")
ax.set_xlim(0, 1500); ax.set_ylim(0.49, 0.75)
ax.set_xlabel("tempo após o degrau [s]"); ax.set_ylabel("nível $h$ [m]")
ax.set_title("Área: banco de capacitores chaveado no SCADA", fontsize=9.5)
ax.legend(loc="lower right", frameon=False, fontsize=7.2)
aa = np.array([r["A"] for r in lst])
axb.loglog(aa, [r["t63_e01"] for r in lst], "-", color=AZUL, lw=2, label="E01")
axb.loglog(aa, [r["t63_vhil"] for r in lst], "o", color=LARANJA, ms=6, label="VHIL")
axb.set_xlabel("área A [m²]"); axb.set_ylabel("t₆₃ [s]"); axb.legend(frameon=False)
axb.set_title("t₆₃ proporcional a A", fontsize=9.5)
from matplotlib.ticker import NullFormatter, FixedLocator
axb.xaxis.set_major_locator(FixedLocator(aa)); axb.xaxis.set_minor_formatter(NullFormatter())
axb.yaxis.set_major_locator(FixedLocator([20, 40, 80, 160, 320])); axb.yaxis.set_minor_formatter(NullFormatter())
axb.xaxis.set_major_formatter(virgula); axb.yaxis.set_major_formatter(virgula)
eixos(ax); rodape(fig)
salvar(fig, "fig-08-sensibilidade-area.png")
R["sens_A"] = lst

# ================================================================ R4 sensibilidade: coeficiente k
NIV_K = [("k0005", 0.005), ("k00075", 0.0075), ("k001", 0.010), ("k0015", 0.015), ("k002", 0.020)]
cores = ["#B85C00", "#E6A35C", AZUL, "#6BAED6", "#9ECAE1"]
fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.6, 3.3), gridspec_kw=dict(width_ratios=[1.7, 1]))
ax.axhspan(H_MAX, 2.2, color=VERM, alpha=0.08, lw=0); ax.axhspan(0, H_MIN, color=CINZA, alpha=0.12, lw=0)
lst = []
for (n, k), c in zip(NIV_K, cores):
    d = vhil(n)
    te_, he_ = simular(H0, 3000, k=k)
    tvv, hvv = d["t"] - T_EV, d["h_m"]
    m = tvv >= 0
    heq = (QI0 / k) ** 2
    rec = dict(k=k, h_eq=heq, hf_vhil=float(np.mean(hvv[tvv > 2980])), hf_e01=float(he_[-1]),
               t_transb_vhil=cruza(tvv[m], hvv[m], H_MAX), t_transb_e01=cruza(te_, he_, H_MAX),
               K_e=k * KI / np.sqrt(KV))
    if k != K:
        rec["t63_vhil"] = tempos(tvv[m], hvv[m], H0, heq)["t63"]; rec["t63_e01"] = tempos(te_, he_, H0, heq)["t63"]
    lst.append(rec)
    ax.plot(te_, he_, color=c, lw=2.2)
    ax.plot(tvv[m], hvv[m], "--", color="k", lw=0.8)
ax.plot([], [], color=AZUL, lw=2.2, label="Entrega 01"); ax.plot([], [], "--", color="k", lw=0.8, label="VHIL")
for (n, k), c in zip(NIV_K, cores):
    ax.plot([], [], color=c, lw=4, label=f"k = {br(k, 4).rstrip('0')} → Kₑ = {br(k * KI / np.sqrt(KV), 2)} A/√V")
ax.text(1450, 1.62, "acima de 1,2 m: transborda", fontsize=7.5, color=VERM)
ax.set_xlim(0, 3000); ax.set_ylim(0, 2.1)
ax.set_xlabel("tempo após a mudança de k [s]"); ax.set_ylabel("nível $h$ [m]")
ax.set_title("Válvula: ganho do orifício alterado no SCADA", fontsize=9.5)
ax.legend(loc="center right", frameon=False, fontsize=7)
kk = np.linspace(0.0045, 0.021, 100)
axb.loglog(kk, (QI0 / kk) ** 2, "-", color=AZUL, lw=2, label="E01: (qᵢ₀/k)²")
axb.loglog([r["k"] for r in lst], [r["hf_vhil"] for r in lst], "o", color=LARANJA, ms=6, label="VHIL (regime)")
axb.set_xlabel("k [m²·⁵/s]"); axb.set_ylabel("nível de equilíbrio [m]"); axb.legend(frameon=False)
axb.set_title("h* proporcional a 1/k²", fontsize=9.5)
axb.xaxis.set_major_locator(FixedLocator([0.005, 0.0075, 0.01, 0.015, 0.02])); axb.xaxis.set_minor_formatter(NullFormatter())
axb.yaxis.set_major_locator(FixedLocator([0.125, 0.25, 0.5, 1, 2])); axb.yaxis.set_minor_formatter(NullFormatter())
axb.xaxis.set_major_formatter(virgula); axb.yaxis.set_major_formatter(virgula)
axb.tick_params(axis="x", labelrotation=35, labelsize=8)
eixos(ax); rodape(fig)
salvar(fig, "fig-09-sensibilidade-k.png")
R["sens_k"] = lst


# ================================================================ saida
def limpo(o):
    if isinstance(o, dict):
        return {k: limpo(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpo(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else float(o)
    return o


json.dump(limpo(R), open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(limpo({k: R[k] for k in ("a", "pequeno", "b", "c")}), indent=1))
for r in R["sens_A"]:
    print("A", r)
for r in R["sens_k"]:
    print("k", r)
