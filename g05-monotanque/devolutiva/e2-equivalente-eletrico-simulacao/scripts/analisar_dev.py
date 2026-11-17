# -*- coding: utf-8 -*-
"""
Devolutiva da Fase 2 / Entrega 02 (G05): caracterizacao do equivalente eletrico v2.

Le os ensaios do VHIL (4_dados/vhil/*.npz), calcula as referencias
  - Entrega 01:  A dh/dt = qi - k*sqrt(h)                          (1 estado)
  - modelo v2:   A dh/dt = qi - q ;  I_h dq/dt = h - q|q|/k^2        (2 estados: nivel e vazao no tubo)
e gera as figuras do relatorio e 4_dados/resultados_dev.json.
Uso:  python analisar_dev.py
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from scipy.integrate import solve_ivp

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SRC = os.path.join(BASE, "4_dados", "vhil")
FIG = os.path.join(BASE, "2_entrega", "relatorio", "figuras")
OUT = os.path.join(BASE, "4_dados", "resultados_dev.json")
os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------- parametros (Entrega 01 + tubo)
A, K, H0, H_MAX, H_MIN = 0.50, 0.010, 0.50, 1.20, 0.10
G, CD, L_TUBO = 9.81, 0.60, 1.0
QI0 = K * np.sqrt(H0)
A_OR = K / (CD * np.sqrt(2 * G))                 # m2
D_OR = np.sqrt(4 * A_OR / np.pi)                 # m
I_POR_M = 1 / (G * A_OR)                         # s2/m2 por metro de tubo
I_H = L_TUBO * I_POR_M
R_HID = 2 * np.sqrt(H0) / K                      # s/m2
TAU = A * R_HID
T_EV = 100.0                                     # s (tanque): fim da preparacao
KV, KI, KT = 10.0, 1000.0, 100.0
C_F = A * KI / (KV * KT)
L_H = KV * I_H / (KI * KT)
K_E = K * KI / np.sqrt(KV)
R_OHM = R_HID * KV / KI
NU = 1.0e-6

AZUL, AZUL2, LARANJA, CINZA, VERDE, VERM, ROXO = ("#185079", "#3A86B0", "#D9822B", "#7F7F7F", "#2E8B57",
                                                  "#A01E1E", "#6A3D9A")
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "mathtext.fontset": "stix",
                     "font.size": 10, "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 200, "legend.fontsize": 8.5})
virgula = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def eixos(*axs, x=True):
    for ax in axs:
        if x:
            ax.xaxis.set_major_formatter(virgula)
        ax.yaxis.set_major_formatter(virgula)


def salvar(fig, nome):
    fig.savefig(os.path.join(FIG, nome), bbox_inches="tight"); plt.close(fig); print("figura:", nome)


def rodape(fig, txt="VHIL: Typhoon HIL Control Center 2026.2, passo 20 µs (= 2 ms no tanque). "
                    "Referências: Python/SciPy (Radau, rtol 10⁻⁹)."):
    fig.text(0.99, -0.03, txt, ha="right", va="top", fontsize=6.5, color=CINZA)


# ---------------------------------------------------------------- modelos de referencia (escala do tanque)
def ref_e01(h_ini, t_fim, qi=lambda t: QI0, a=A, k=K, dt=0.1):
    f = lambda t, h: [(qi(t) - k * np.sqrt(max(h[0], 0.0))) / a]
    ev = lambda t, h: h[0] - 1e-12
    ev.terminal, ev.direction = True, -1
    s = solve_ivp(f, (0, t_fim), [h_ini], method="RK45", t_eval=np.arange(0, t_fim, dt), rtol=1e-10, atol=1e-12,
                  max_step=0.5, events=ev)
    t, h = s.t, s.y[0]
    if s.t_events[0].size:
        t, h = np.append(t, s.t_events[0][0]), np.append(h, 0.0)
    return t, h


def ref_v2(h_ini, t_fim, qi=lambda t: QI0, a=A, k=K, ih=I_H, linear_em=None, dt=0.1, q_ini=None):
    """2 estados. linear_em = h_op -> orificio trocado pela tangente em h_op (so o resistor)."""
    if linear_em is None:
        perda = lambda q: q * abs(q) / k ** 2
    else:
        r = 2 * np.sqrt(linear_em) / k
        perda = lambda q: r * q - linear_em
    q0 = k * np.sqrt(h_ini) if q_ini is None else q_ini
    f = lambda t, x: [(qi(t) - x[1]) / a, (x[0] - perda(x[1])) / ih]
    s = solve_ivp(f, (0, t_fim), [h_ini, q0], method="Radau", t_eval=np.arange(0, t_fim, dt), rtol=1e-9,
                  atol=1e-12, max_step=1.0)
    return s.t, s.y[0], s.y[1]


def cruza(t, y, nivel):
    s = np.sign(y - nivel)
    i = np.where(np.diff(s) != 0)[0]
    if not i.size:
        return float("nan")
    i = i[0]
    return float(t[i] + (nivel - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))


def tempos(t, h, h_i, h_f):
    r = {n: cruza(t, h, h_i + fr * (h_f - h_i)) for n, fr in
         (("t10", .10), ("t63", .632), ("t90", .90), ("ts2", .98))}
    # ts2 = ultima entrada na faixa de 2 %
    fora = np.where(np.abs(h - h_f) > 0.02 * abs(h_f - h_i))[0]
    r["ts2"] = float(t[fora[-1] + 1]) if fora.size and fora[-1] + 1 < len(t) else float("nan")
    return r


def vhil(n):
    d = np.load(os.path.join(SRC, n + ".npz"))
    t = d["t_fisico_s"]
    ok = np.concatenate([[True], np.diff(t) > 0])
    out = {k: d[k][ok] for k in d.files if k != "dec"}
    out["t"] = t[ok] - T_EV                                  # t = 0 no inicio do ensaio
    return out


def interp(tr, yr, t):
    return np.interp(t, tr, yr)


R = {"param": dict(A=A, k=K, h0=H0, qi0=QI0, a_or=A_OR, d_or=D_OR, I_por_m=I_POR_M, I_h=I_H, R_hid=R_HID,
                   tau=TAU, C=C_F, L=L_H, K_e=K_E, R_ohm=R_OHM, kv=KV, ki=KI, kt=KT, l_tubo=L_TUBO,
                   Re=4 * QI0 / (np.pi * D_OR * NU), v_jato=QI0 / (CD * A_OR),
                   wn=1 / np.sqrt(A * I_H), zeta=A * R_HID / (2 * np.sqrt(A * I_H)),
                   tau_L=I_H / R_HID)}
lam = np.roots([A * I_H, A * R_HID, 1])
R["param"]["polos"] = sorted([float(x.real) for x in lam])
R["param"]["zero"] = -R_HID / I_H

# ================================================================ fig 01: o tanque com tubo e o circuito v2
import schemdraw
import schemdraw.elements as elm
from matplotlib.patches import Rectangle

fig = plt.figure(figsize=(10.2, 4.0))
axT = fig.add_axes([0.0, 0.0, 0.36, 1.0]); axT.set_axis_off(); axT.set_xlim(0, 10.5); axT.set_ylim(-1.2, 10)
axT.add_patch(Rectangle((1.6, 1.8), 4.8, 6.2, fill=False, lw=2, ec=AZUL))
axT.add_patch(Rectangle((1.6, 1.8), 4.8, 3.4, color=AZUL2, alpha=0.35, lw=0))
axT.add_patch(Rectangle((6.4, 1.8), 3.4, 0.55, color=AZUL2, alpha=0.35, lw=1.2, ec=AZUL))
axT.annotate("", xy=(3.0, 6.0), xytext=(3.0, 9.2), arrowprops=dict(arrowstyle="-|>", lw=2, color=LARANJA))
axT.text(3.3, 8.7, r"$q_i$ bomba", color=LARANJA, fontsize=11)
axT.annotate("", xy=(10.4, 2.07), xytext=(9.8, 2.07), arrowprops=dict(arrowstyle="-|>", lw=2, color=AZUL))
axT.text(6.5, 0.9, r"tubo: massa $\rho l a$ (inércia)", color=AZUL, fontsize=9.5)
axT.text(6.5, 0.1, r"orifício: perda $q|q|/k^2$", color=AZUL, fontsize=9.5)
axT.text(8.0, 2.65, r"$q$", color=AZUL, fontsize=12)
axT.annotate("", xy=(1.1, 5.2), xytext=(1.1, 1.8), arrowprops=dict(arrowstyle="<->", lw=1.2))
axT.text(0.2, 3.3, r"$h$", fontsize=13)
axT.text(4.0, 3.2, r"área $A$", ha="center", fontsize=11, color=AZUL)
axT.text(5.0, 9.7, "Tanque com tubo de saída", ha="center", fontsize=11, weight="bold", color=AZUL)

axC = fig.add_axes([0.39, 0.0, 0.61, 0.95]); axC.set_axis_off()
tmp_png = os.path.join(FIG, "_circ_tmp.png")
with schemdraw.Drawing(show=False) as d:
    d.config(unit=2.0, fontsize=12.5, lw=1.5, font="Times New Roman")
    d += elm.SourceI().up().at((0, 0)).to((0, 4.2)).color(LARANJA).label("$i_i$\nbomba", loc="bottom", ofst=0.25)
    d += elm.Line().right(2.6).at((0, 4.2))
    d += elm.Dot().at((2.6, 4.2))
    d += elm.Capacitor().down().at((2.6, 4.2)).to((2.6, 0)).color(AZUL).label("$C$\ntanque", loc="bottom", ofst=0.2)
    d += elm.Line().right(2.6).at((2.6, 4.2))
    d += elm.Dot().at((5.2, 4.2))
    d += elm.Inductor2().down().at((5.2, 4.2)).to((5.2, 2.8)).color(ROXO).label("$L$ inércia", loc="bottom",
                                                                                  ofst=0.15)
    d += elm.Resistor().down().at((5.2, 2.8)).to((5.2, 1.4)).color(VERDE).label("$R$ escoamento", loc="bottom",
                                                                                 ofst=0.15)
    d += elm.SourceControlledV().down().at((5.2, 1.4)).to((5.2, 0)).reverse().color(CINZA).label("$e(i_o)$\nparte não linear",
                                                                                       loc="bottom", ofst=0.15)
    d += elm.Line().right(3.0).at((5.2, 4.2))
    d += elm.SourceI().down().at((8.2, 4.2)).to((8.2, 0)).color(CINZA).label("$i_d$\nconsumo", loc="bottom",
                                                                            ofst=0.2)
    d += elm.Line().left(8.2).at((8.2, 0))
    d += elm.Ground().at((2.6, 0))
    d += elm.Label().at((2.6, 4.75)).label("$v = k_v h$", color=AZUL)
    d += elm.Label().at((6.35, 3.85)).label("$i_o$", color=AZUL)
    d.save(tmp_png, dpi=220)
axC.imshow(plt.imread(tmp_png)); os.remove(tmp_png)
salvar(fig, "fig-01-tanque-e-circuito-v2.png")

# ================================================================ fig 02: caracteristica estatica da resistencia de saida
dren = vhil("b2")
ops = {n: vhil(n) for n in ("op020", "op035", "op050", "op080", "op110")}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.7))
hh = np.linspace(0, 1.25, 400)
m = (dren["t"] > 0.5) & (dren["h_m"] > 0.002)
ax1.plot(dren["h_m"][m], dren["qo_Ls"][m], color=AZUL2, lw=4, alpha=0.45, label="VHIL: drenagem livre (curva medida)")
ax1.plot(hh, 1000 * K * np.sqrt(hh), color=AZUL, lw=1.2, label=r"$q = k\sqrt{h}$ (Entrega 01)")
ax1.plot(hh, 1000 * (QI0 + (hh - H0) / R_HID), "--", color=VERDE, lw=1.3, label=f"tangente em 0,5 m (resistor R)")
pts = []
for n, d in ops.items():
    sel = (d["t"] > -40) & (d["t"] < -1)
    pts.append((float(np.mean(d["h_m"][sel])), float(np.mean(d["qo_Ls"][sel]))))
pts = np.array(pts)
ax1.plot(pts[:, 0], pts[:, 1], "o", color=LARANJA, ms=6, label="VHIL: pontos de equilíbrio")
ax1.set_xlabel("nível h [m]   (tensão v = 10·h [V])"); ax1.set_ylabel("vazão de saída [L/s] = corrente [A]")
ax1.set_title("Característica tensão × corrente da saída", fontsize=10.5)
ax1.legend(loc="lower right"); ax1.set_xlim(0, 1.25); ax1.set_ylim(0, 12)
# resistencias secante e incremental
ax2.plot(hh[1:], np.sqrt(hh[1:]) / K, color=AZUL, lw=1.4, label=r"secante  $R_s = h/q = \sqrt{h}/k$")
ax2.plot(hh[1:], 2 * np.sqrt(hh[1:]) / K, color=VERM, lw=1.4, label=r"incremental  $R = dh/dq = 2\sqrt{h}/k$")
rinc = []
for (n, d), (hop, _) in zip(ops.items(), pts):
    hf = float(np.mean(d["h_m"][d["t"] > d["t"][-1] - 40]))
    dq = 0.02 * K * np.sqrt(hop)
    rinc.append((hop, (hf - hop) / dq))
rinc = np.array(rinc)
ax2.plot(rinc[:, 0], rinc[:, 1], "s", color=LARANJA, ms=6, label="VHIL: Δh/Δq (degrau de 2 %)")
ax2.axhline(R_HID, color=VERDE, ls="--", lw=1); ax2.text(1.22, R_HID + 5, "resistor R (fixo)", ha="right",
                                                         color=VERDE, fontsize=8.5)
ax2.set_xlabel("nível de operação h [m]"); ax2.set_ylabel("resistência [s/m²]   (×0,01 = Ω)")
ax2.set_title("Resistência de escoamento depende do nível", fontsize=10.5)
ax2.legend(loc="upper left"); ax2.set_xlim(0, 1.25); ax2.set_ylim(0, 240)
eixos(ax1, ax2); fig.tight_layout(); rodape(fig)
salvar(fig, "fig-02-caracteristica-resistencia.png")

# ================================================================ fig 03: pontos de operacao (degrau de 2 %)
fig, ax = plt.subplots(figsize=(10.0, 3.6))
cores = [AZUL2, AZUL, VERDE, LARANJA, VERM]
R["op"] = []
for (n, d), cor, (hop, rm) in zip(ops.items(), cores, rinc):
    hf = float(np.mean(d["h_m"][d["t"] > d["t"][-1] - 40]))
    dq = 0.02 * K * np.sqrt(hop)
    tr, hr, _ = ref_v2(hop, d["t"][-1], qi=lambda t, hop=hop: K * np.sqrt(hop) * 1.02)
    tr1, hr1 = ref_e01(hop, d["t"][-1], qi=lambda t, hop=hop: K * np.sqrt(hop) * 1.02)
    m = d["t"] >= 0
    tv = tempos(d["t"][m], d["h_m"][m], hop, hf)
    hf_r = hr[-1]; tvr = tempos(tr, hr, hop, hf_r)
    hf_1 = hr1[-1]; tv1 = tempos(tr1, hr1, hop, hf_1)
    tau_lin = A * 2 * np.sqrt(hop) / K
    R["op"].append(dict(h=hop, q=K * np.sqrt(hop) * 1000, R_sec=np.sqrt(hop) / K, R_inc=2 * np.sqrt(hop) / K,
                        R_vhil=float(rm), tau_lin=tau_lin, t63_vhil=tv["t63"], t63_v2=tvr["t63"], t63_e01=tv1["t63"],
                        wn=1 / np.sqrt(A * I_H), zeta=A * 2 * np.sqrt(hop) / K / (2 * np.sqrt(A * I_H)),
                        R_ohm=2 * np.sqrt(hop) / K * KV / KI, tau_c=tau_lin / KT))
    ax.plot(d["t"][m], (d["h_m"][m] - hop) / (hf - hop), color=cor, lw=2.2, alpha=0.8,
            label=f"h₀ = {hop:.2f} m: τ = {tv['t63']:.1f} s".replace(".", ","))
    ax.plot(tr, (hr - hop) / (hf_r - hop), ":", color="k", lw=0.8)
ax.axhline(0.632, color=CINZA, lw=0.8, ls="--"); ax.text(8, 0.66, "63,2 %", color=CINZA, fontsize=8)
ax.plot([], [], ":", color="k", lw=0.8, label="modelo de referência")
ax.set_xlim(0, 600); ax.set_xlabel("tempo após o degrau [s]"); ax.set_ylabel("resposta normalizada")
ax.set_title("Degrau de +2 % na bomba em cinco pontos de operação: quanto mais alto o nível, mais lento",
             fontsize=10.5)
ax.legend(loc="lower right", ncol=2); eixos(ax); fig.tight_layout(); rodape(fig)
salvar(fig, "fig-03-pontos-de-operacao.png")

# ================================================================ fig 04: linear (so R) x nao linear
fig, ax = plt.subplots(figsize=(10.0, 4.0))
R["lin"] = []
for pct, cor in ((50, VERM), (20, LARANJA), (-20, AZUL2), (-50, AZUL)):
    s = f"{'p' if pct > 0 else 'm'}{abs(pct)}"
    dn, dl = vhil("nl_" + s), vhil("li_" + s)
    q = QI0 * (1 + pct / 100)
    tr, hr = ref_e01(H0, dn["t"][-1], qi=lambda t, q=q: q)
    mn, ml = dn["t"] >= -20, dl["t"] >= -20
    ax.plot(dn["t"][mn], dn["h_m"][mn], color=cor, lw=2.2, label=f"{pct:+d} %: não linear")
    ax.plot(dl["t"][ml], dl["h_m"][ml], "--", color=cor, lw=1.4, label=f"{pct:+d} %: linearizado (só R)")
    ax.plot(tr, hr, ":", color="k", lw=0.8)
    hf_n = float(np.mean(dn["h_m"][dn["t"] > dn["t"][-1] - 30]))
    hf_l = float(np.mean(dl["h_m"][dl["t"] > dl["t"][-1] - 30]))
    t_n = tempos(dn["t"][dn["t"] >= 0], dn["h_m"][dn["t"] >= 0], H0, hf_n)
    t_l = tempos(dl["t"][dl["t"] >= 0], dl["h_m"][dl["t"] >= 0], H0, hf_l)
    R["lin"].append(dict(pct=pct, hf_teo=(q / K) ** 2, hf_nl=hf_n, hf_lin=hf_l, hf_lin_teo=H0 + R_HID * (q - QI0),
                         t63_nl=t_n["t63"], t63_lin=t_l["t63"], t63_e01=tempos(tr, hr, H0, hr[-1])["t63"],
                         erro_hf_pct=100 * (hf_l - hf_n) / (hf_n - H0)))
ax.plot([], [], ":", color="k", lw=0.8, label="Entrega 01")
ax.set_xlim(-20, 800); ax.set_xlabel("tempo após o degrau [s]"); ax.set_ylabel("nível h [m]")
ax.set_title("Mesmo circuito, orifício não linear × só o resistor R (tangente em 0,5 m)", fontsize=10.5)
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5)); eixos(ax); fig.tight_layout(); rodape(fig)
salvar(fig, "fig-05-linear-x-nao-linear.png")


# ================================================================ fig 05: resposta em frequencia
def ajuste(t, y, w):
    M = np.column_stack([np.ones_like(t), t - t.mean(), np.cos(w * t), np.sin(w * t)])
    c = np.linalg.lstsq(M, y, rcond=None)[0]
    return np.hypot(c[2], c[3]), np.arctan2(-c[3], c[2])         # y ~ amp*cos(w t + fase)


R["bode"] = []
for f_ in sorted(glob.glob(os.path.join(SRC, "bode_w*.npz")), key=lambda p: float(p.split("_w")[1][:-4])):
    wr = float(f_.split("_w")[1][:-4])
    d = vhil(os.path.basename(f_)[:-4])
    w = wr * (1 / (A * R_HID))                               # rad/s no tanque
    per = 2 * np.pi / w
    m = d["t"] >= d["t"][-1] - 3 * per
    ai, fi = ajuste(d["t"][m], d["qi_Ls"][m], w)
    ah, fh = ajuste(d["t"][m], d["h_m"][m], w)
    ao, fo = ajuste(d["t"][m], d["qo_Ls"][m], w)
    dfh = (np.degrees(fh - fi) + 180) % 360 - 180
    dfo = (np.degrees(fo - fi) + 180) % 360 - 180
    R["bode"].append(dict(w_rel=wr, w=w, H=ah / (ai / 1000), fase_H=dfh, Qo=ao / ai, fase_Qo=dfo))
ww = np.logspace(-4, 2.2, 600)
s = 1j * ww
Hh = (R_HID + s * I_H) / (A * I_H * s ** 2 + A * R_HID * s + 1)
Hq = 1 / (A * I_H * s ** 2 + A * R_HID * s + 1)
H1 = R_HID / (A * R_HID * s + 1)
B = R["bode"]
bw = np.array([b["w"] for b in B])
fig, axs = plt.subplots(2, 2, figsize=(10.5, 5.6), sharex=True)
axs[0, 0].loglog(ww, abs(H1), ":", color="k", lw=1, label="Entrega 01 (1ª ordem)")
axs[0, 0].loglog(ww, abs(Hh), color=AZUL, lw=1.3, label="teoria (linearizada, com inércia)")
axs[0, 0].loglog(bw, [b["H"] for b in B], "o", color=LARANJA, ms=5, label="VHIL")
axs[0, 0].set_ylabel("|H(jω)/Q_i(jω)| [s/m²]"); axs[0, 0].set_title("Nível ← bomba (tensão ← corrente)", fontsize=10.5)
axs[1, 0].semilogx(ww, np.degrees(np.angle(H1)), ":", color="k", lw=1)
axs[1, 0].semilogx(ww, np.degrees(np.angle(Hh)), color=AZUL, lw=1.3)
axs[1, 0].semilogx(bw, [b["fase_H"] for b in B], "o", color=LARANJA, ms=5)
axs[1, 0].set_ylabel("fase [°]"); axs[1, 0].set_ylim(-100, 5)
axs[0, 1].loglog(ww, abs(H1 / R_HID), ":", color="k", lw=1, label="Entrega 01 (sem inércia)")
axs[0, 1].loglog(ww, abs(Hq), color=AZUL, lw=1.3, label="teoria (2ª ordem)")
axs[0, 1].loglog(bw, [b["Qo"] for b in B], "o", color=LARANJA, ms=5, label="VHIL")
axs[0, 1].set_ylabel("|Q_o(jω)/Q_i(jω)|"); axs[0, 1].set_title("Vazão de saída ← bomba (corrente no L ← fonte)",
                                                               fontsize=10.5)
axs[1, 1].semilogx(ww, np.degrees(np.angle(H1 / R_HID)), ":", color="k", lw=1)
axs[1, 1].semilogx(ww, np.degrees(np.angle(Hq)), color=AZUL, lw=1.3)
axs[1, 1].semilogx(bw, [b["fase_Qo"] for b in B], "o", color=LARANJA, ms=5)
axs[1, 1].set_ylabel("fase [°]"); axs[1, 1].set_ylim(-185, 5)
for ax in axs[1]:
    ax.set_xlabel("frequência ω no tanque [rad/s]   (×100 no circuito)")
for ax in axs.flat:
    for p_ in R["param"]["polos"]:
        ax.axvline(-p_, color=CINZA, lw=0.7, ls="--")
axs[0, 0].legend(loc="lower left"); axs[0, 1].legend(loc="lower left")
axs[0, 1].text(-R["param"]["polos"][0] * 1.1, 0.5, "polo da\ninércia", fontsize=8, color=CINZA)
axs[0, 0].text(-R["param"]["polos"][1] * 1.1, 1.5, "polo do\ntanque", fontsize=8, color=CINZA)
fig.tight_layout(); rodape(fig)
salvar(fig, "fig-06-resposta-em-frequencia.png")

# ================================================================ fig 06: inercia do liquido (comprimento do tubo)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.8))
R["inercia"] = []
for nome, l, cor in (("l0p1_a", 0.1, AZUL2), ("a", 1.0, AZUL), ("l10_a", 10, VERDE), ("l100_a", 100, LARANJA),
                     ("l1000_a", 1000, VERM)):
    d = vhil(nome)
    ih = l * I_POR_M
    tr, hr, qr = ref_v2(H0, d["t"][-1], qi=lambda t: QI0 * 1.2, ih=ih)
    m = d["t"] >= -20
    ax1.plot(d["t"][m], d["qo_Ls"][m], color=cor, lw=2, label=f"l = {l:g} m".replace(".", ","))
    ax1.plot(tr, 1000 * qr, ":", color="k", lw=0.7)
    ax2.plot(d["t"][m], d["h_m"][m], color=cor, lw=2)
    ax2.plot(tr, hr, ":", color="k", lw=0.7)
    qf = 1000 * QI0 * 1.2
    mm = d["t"] >= 0
    hf = float(np.mean(d["h_m"][d["t"] > d["t"][-1] - 30]))
    wn = 1 / np.sqrt(A * ih); z = A * R_HID / (2 * np.sqrt(A * ih))
    ov_teo = 100 * np.exp(-np.pi * z / np.sqrt(1 - z ** 2)) if z < 1 else 0.0
    R["inercia"].append(dict(l=l, I=ih, L=KV * ih / (KI * KT), wn=wn, zeta=z,
                             polos=sorted(float(x.real) for x in np.roots([A * ih, A * R_HID, 1])),
                             ov_qo_teo_lin=ov_teo,
                             ov_qo_vhil=100 * max(0.0, (float(np.max(d["qo_Ls"][mm])) - qf) / (qf - 1000 * QI0)),
                             ov_qo_ref=100 * max(0.0, (float(np.max(1000 * qr)) - qf) / (qf - 1000 * QI0)),
                             ov_h_vhil=100 * max(0.0, (float(np.max(d["h_m"][mm])) - hf) / (hf - H0)),
                             ov_h_ref=100 * max(0.0, (float(np.max(hr)) - hr[-1]) / (hr[-1] - H0)),
                             t63_vhil=tempos(d["t"][mm], d["h_m"][mm], H0, hf)["t63"],
                             t63_ref=tempos(tr, hr, H0, hr[-1])["t63"]))
ax1.plot([], [], ":", color="k", lw=0.7, label="modelo de referência")
ax1.set_xlim(-20, 900); ax1.set_xlabel("tempo após o degrau [s]"); ax1.set_ylabel("vazão de saída q [L/s]")
ax1.set_title("Vazão no tubo (corrente no indutor)", fontsize=10.5); ax1.legend(loc="lower right", ncol=2)
ax2.set_xlim(-20, 900); ax2.set_xlabel("tempo após o degrau [s]"); ax2.set_ylabel("nível h [m]")
ax2.set_title("Nível (tensão no capacitor)", fontsize=10.5)
eixos(ax1, ax2); fig.tight_layout(); rodape(fig)
salvar(fig, "fig-08-inercia-do-liquido.png")

# ================================================================ fig 07: validacao contra a Entrega 01 (a, b, c)
fig, axs = plt.subplots(1, 3, figsize=(11.0, 3.6))
R["val"] = {}
cfg = {"a": (H0, lambda t: QI0 * 1.2), "b": (1.0, lambda t: QI0), "b2": (1.0, lambda t: 0.0),
       "c": (H0, lambda t: QI0 * (1 + 0.1 * np.sin(t / TAU)))}
for pre, rot, ls_ in (("", "VHIL, tubo de 1 m", "-"), ("l0p1_", "VHIL, tubo de 0,1 m", "--")):
    for n, (hi, qi) in cfg.items():
        d = vhil(pre + n)
        m = d["t"] >= 0
        t, h = d["t"][m], d["h_m"][m]
        tr, hr = ref_e01(hi, t[-1], qi=qi)
        dif = np.abs(np.interp(tr, t, h) - hr)
        dif = dif[tr < t[-1] - 1]
        reg = {"dif_max_mm": 1000 * float(np.max(dif))}
        if n in ("a", "b"):
            hf_r = hr[-1]; hf = float(np.mean(h[t > t[-1] - 30]))
            for k_, v_ in tempos(t, h, hi, hf).items():
                reg[k_] = v_
            for k_, v_ in tempos(tr, hr, hi, hf_r).items():
                reg[k_ + "_e01"] = v_
            reg["hf"], reg["hf_e01"] = hf, float(hf_r)
        if n == "b2":
            reg["t_1mm"], reg["t_1mm_e01"] = cruza(t, h, 0.001), cruza(tr, hr, 0.001)
            reg["t_hmin"], reg["t_hmin_e01"] = cruza(t, h, H_MIN), cruza(tr, hr, H_MIN)
        if n == "c":
            w = 1 / TAU; mm = t >= t[-1] - 2 * np.pi / w * 2
            a1, f1 = ajuste(t[mm], h[mm], w)
            mr = tr >= tr[-1] - 2 * np.pi / w * 2
            a2, f2 = ajuste(tr[mr], hr[mr], w)
            fq = ajuste(t[mm], d["qi_Ls"][m][mm], w)[1]
            reg.update(amp=a1, amp_e01=a2, fase=(np.degrees(f1 - fq) + 180) % 360 - 180,
                       fase_e01=(np.degrees(f2) + 90 + 180) % 360 - 180)
        R["val"][pre + n] = reg
        if pre == "":
            ax = axs[{"a": 0, "b": 1, "b2": 1, "c": 2}[n]]
            ax.plot(tr, hr, color="k", lw=1, label="Entrega 01" if n != "b2" else None, zorder=3)
        ax = axs[{"a": 0, "b": 1, "b2": 1, "c": 2}[n]]
        ax.plot(t, h, ls_, color=AZUL2 if pre == "" else LARANJA, lw=3 if pre == "" else 1.4,
                alpha=0.6 if pre == "" else 1, label=rot if n != "b2" else None)
axs[0].set_title("(a) degrau de +20 %", fontsize=10.5); axs[0].set_xlim(0, 700)
axs[1].set_title("(b) h(0) = 1,0 m: bomba ligada e drenagem", fontsize=10.5); axs[1].set_xlim(0, 600)
axs[2].set_title("(c) senoide ±10 % em ω = 1/τ", fontsize=10.5); axs[2].set_xlim(0, 1600)
for ax in axs:
    ax.set_xlabel("tempo [s]")
axs[0].set_ylabel("nível h [m]"); axs[0].legend(loc="lower right")
eixos(*axs); fig.tight_layout(); rodape(fig)
salvar(fig, "fig-04-validacao-entrega01.png")

# ================================================================ fig 08: sensibilidade (area recompilada, k no SCADA)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.7))
R["area"] = []
for nome, a_, cor in (("A025_a", 0.25, AZUL2), ("a", 0.5, AZUL), ("A1_a", 1.0, VERDE), ("A2_a", 2.0, LARANJA)):
    d = vhil(nome)
    tr, hr = ref_e01(H0, d["t"][-1], qi=lambda t: QI0 * 1.2, a=a_)
    m = d["t"] >= -20
    ax1.plot(d["t"][m], d["h_m"][m], color=cor, lw=2.2, label=f"A = {a_:g} m² (C = {a_:g} F)".replace(".", ","))
    ax1.plot(tr, hr, ":", color="k", lw=0.8)
    mm = d["t"] >= 0
    hf = float(np.mean(d["h_m"][d["t"] > d["t"][-1] - 20]))
    R["area"].append(dict(A=a_, C=a_, t63=tempos(d["t"][mm], d["h_m"][mm], H0, hf)["t63"],
                          t63_e01=tempos(tr, hr, H0, hr[-1])["t63"], hf=hf))
ax1.plot([], [], ":", color="k", lw=0.8, label="Entrega 01")
ax1.set_xlim(-20, 1900); ax1.set_xlabel("tempo após o degrau [s]"); ax1.set_ylabel("nível h [m]")
ax1.set_title("Área (valor do único capacitor, recompilado)", fontsize=10.5); ax1.legend(loc="lower right")
R["k"] = []
for nome, k_, cor in (("k0050", 0.005, VERM), ("k0075", 0.0075, LARANJA), ("a", 0.01, AZUL),
                      ("k0150", 0.015, VERDE), ("k0200", 0.02, AZUL2)):
    d = vhil(nome)
    if nome == "a":
        continue
    tr, hr = ref_e01(H0, d["t"][-1], qi=lambda t: QI0, k=k_)
    m = d["t"] >= -20
    ax2.plot(d["t"][m], d["h_m"][m], color=cor, lw=2.2, label=f"k = {k_:g}".replace(".", ","))
    ax2.plot(tr, hr, ":", color="k", lw=0.8)
    mm = d["t"] >= 0
    hf = float(np.mean(d["h_m"][d["t"] > d["t"][-1] - 20]))
    R["k"].append(dict(k=k_, h_teo=(QI0 / k_) ** 2, hf=hf, t63=tempos(d["t"][mm], d["h_m"][mm], H0, hf)["t63"],
                       t63_e01=tempos(tr, hr, H0, hr[-1])["t63"], t_transb=cruza(d["t"][mm], d["h_m"][mm], H_MAX),
                       t_transb_e01=cruza(tr, hr, H_MAX)))
ax2.axhline(H_MAX, color=CINZA, ls="--", lw=0.8); ax2.text(1750, H_MAX + 0.03, "h máx = 1,2 m", ha="right",
                                                          fontsize=8, color=CINZA)
ax2.set_xlim(-20, 1800); ax2.set_xlabel("tempo [s]"); ax2.set_ylabel("nível h [m]")
ax2.set_title("Válvula k (no SCADA), bomba em q_i0", fontsize=10.5); ax2.legend(loc="center right")
eixos(ax1, ax2); fig.tight_layout(); rodape(fig)
salvar(fig, "fig-07-sensibilidade.png")

# ================================================================ drenagem com tubo longo (nota)
R["dren_tubo"] = {}
for nome, l in (("b2", 1), ("l10_dren", 10), ("l100_dren", 100), ("l1000_dren", 1000)):
    d = vhil(nome)
    m = d["t"] >= 0
    R["dren_tubo"][str(l)] = dict(h_min=float(np.min(d["h_m"][m])), q_min=float(np.min(d["qo_Ls"][m])),
                                  t_vazio=cruza(d["t"][m], d["h_m"][m], 0.001))


def limpo(o):
    if isinstance(o, dict):
        return {k: limpo(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpo(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    return o


json.dump(limpo(R), open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(limpo({k: R[k] for k in ("param", "op", "lin", "inercia", "val")}), indent=1))
