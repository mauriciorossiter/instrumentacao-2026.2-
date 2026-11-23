# -*- coding: utf-8 -*-
"""
Fase 2 / Entrega 01 - G02: caracterizacao do massa-mola-amortecedor no dominio de origem (R2-R5).

    m x'' + c x' + k x = F(t),   m = 1 kg, c = 6 N.s/m, k = 100 N/m

Uso:  python caracterizacao.py <pasta_figuras> <pasta_dados>
Ferramenta: Python 3.12, numpy, scipy (solve_ivp RK45, rtol 1e-10, atol 1e-12, passo maximo 1 ms), matplotlib.
"""
import sys, os, json, math
import numpy as np
from scipy.integrate import solve_ivp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estilo import plt, COR, SERIE, salvar

FIG, DAD = sys.argv[1], sys.argv[2]
os.makedirs(FIG, exist_ok=True); os.makedirs(DAD, exist_ok=True)
M, C, K, F0 = 1.0, 6.0, 100.0, 10.0
SOLVER = dict(method="RK45", rtol=1e-10, atol=1e-12, max_step=1e-3)


def carac(m=M, c=C, k=K):
    wn = math.sqrt(k / m); z = c / (2 * math.sqrt(k * m))
    d = dict(wn=wn, zeta=z, K=1 / k, polos=np.roots([m, c, k]))
    if z < 1:
        wd = wn * math.sqrt(1 - z**2)
        d.update(wd=wd, Tp=math.pi / wd, OS=100 * math.exp(-z * math.pi / math.sqrt(1 - z**2)),
                 ts2=(4 / (z * wn) if z > 0 else float("inf")), Td=2 * math.pi / wd)
    return d


def sim(F, x0=0.0, v0=0.0, T=2.5, m=M, c=C, k=K, n=5001):
    t = np.linspace(0, T, n)
    s = solve_ivp(lambda t, y: [y[1], (F(t) - c * y[1] - k * y[0]) / m], (0, T), [x0, v0], t_eval=t, **SOLVER)
    return t, s.y[0], s.y[1]


def analitica_degrau(t, F=F0, m=M, c=C, k=K, x0=0.0, v0=0.0):
    ca = carac(m, c, k); wn, z, wd = ca["wn"], ca["zeta"], ca["wd"]
    xinf = F / k
    a, b = x0 - xinf, v0
    return xinf + np.exp(-z * wn * t) * (a * np.cos(wd * t) + (b + z * wn * a) / wd * np.sin(wd * t))


def medir(t, x, xinf):
    i = np.argmax(x)
    os_ = (x[i] - xinf) / xinf * 100
    fora = np.where(np.abs(x - xinf) > 0.02 * abs(xinf))[0]
    ts = t[fora[-1]] if len(fora) else 0.0
    i10 = np.where(x >= 0.1 * xinf)[0][0]; i90 = np.where(x >= 0.9 * xinf)[0][0]
    return dict(Tp=float(t[i]), OS=float(os_), ts2=float(ts), tr=float(t[i90] - t[i10]), xinf=float(x[-1]))


res = {}
ca = carac()
res["R2"] = {k_: (complex(v).__repr__() if k_ == "polos" else float(v)) for k_, v in ca.items() if k_ != "polos"}
res["R2"]["polos"] = [f"{p.real:.4f} {'+' if p.imag >= 0 else '-'} j{abs(p.imag):.5f}" for p in ca["polos"]]

# ---------------- R3 (a) degrau, (b) condicao inicial, (c) pulso
tA, xA, vA = sim(lambda t: F0, T=2.5)
xA_an = analitica_degrau(tA)
tB, xB, vB = sim(lambda t: 0.0, x0=0.10, T=2.5)
xB_an = analitica_degrau(tB, F=0.0, x0=0.10)
pulso = lambda t: 1.5 * F0 if 2.0 <= t < 2.5 else F0
tC, xC, vC = sim(pulso, x0=0.10, T=6.0, n=12001)
# analitica do pulso por superposicao: regime + degrau +0,5F0 em 2,0 s - degrau em 2,5 s
def deg(t, A):
    y = np.zeros_like(t); m_ = t >= 0
    y[m_] = analitica_degrau(t[m_], F=A); return y
xC_an = 0.10 + deg(tC - 2.0, 0.5 * F0) - deg(tC - 2.5, 0.5 * F0)

fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0))
for a, (t, x, xa, tit) in zip(ax, [(tA, xA, xA_an, "(a) Degrau de 10 N a partir do repouso"),
                                     (tB, xB, xB_an, "(b) Condição inicial x(0) = 0,10 m, F = 0"),
                                     (tC, xC, xC_an, "(c) Pulso de 1,5F0 entre 2,0 e 2,5 s")]):
    a.plot(t, xa * 100, color=COR["ref"], lw=2.6, alpha=0.45, label="analítica")
    a.plot(t, x * 100, color=COR["real"], lw=1.2, label="numérica (RK45)")
    a.set(xlabel="t [s]", ylabel="x [cm]", title=tit)
mA = medir(tA, xA, F0 / K)
ax[0].plot(mA["Tp"], xA.max() * 100, "o", color=COR["med"], ms=5)
ax[0].annotate(f"pico {xA.max()*100:.2f} cm\nTp = {mA['Tp']:.3f} s", (mA["Tp"], xA.max() * 100), (0.9, 12.5), fontsize=7,
               arrowprops=dict(arrowstyle="-", color=COR["crit"]))
ax[0].axhspan(9.8, 10.2, color=COR["ideal"], alpha=0.15, lw=0)
ax[0].axvline(mA["ts2"], color=COR["crit"], ls=":", lw=1); ax[0].text(mA["ts2"] + 0.04, 3, f"ts(2%)\n{mA['ts2']:.3f} s", fontsize=7)
ax[0].legend(loc="lower right")
salvar(fig, os.path.join(FIG, "fig-02-ensaios-r3.png"))
np.savetxt(os.path.join(DAD, "fig-02-ensaios-r3-a.csv"), np.column_stack([tA, xA, xA_an, vA]), delimiter=",",
           header="t_s,x_num_m,x_analitica_m,v_num_ms", comments="", fmt="%.8g")
np.savetxt(os.path.join(DAD, "fig-02-ensaios-r3-b.csv"), np.column_stack([tB, xB, xB_an, vB]), delimiter=",",
           header="t_s,x_num_m,x_analitica_m,v_num_ms", comments="", fmt="%.8g")
np.savetxt(os.path.join(DAD, "fig-02-ensaios-r3-c.csv"), np.column_stack([tC, xC, xC_an, vC]), delimiter=",",
           header="t_s,x_num_m,x_analitica_m,v_num_ms", comments="", fmt="%.8g")

# ---------------- R4 validacao cruzada
# picos da resposta livre -> decremento logaritmico
pk = [i for i in range(1, len(xB) - 1) if xB[i] > xB[i - 1] and xB[i] > xB[i + 1] and xB[i] > 0]
delta = math.log(xB[pk[0]] / xB[pk[1]]); z_dec = delta / math.sqrt(4 * math.pi**2 + delta**2)
Td_med = tB[pk[1]] - tB[pk[0]]
r4 = [
    ("Valor final [m]", F0 / K, mA["xinf"]),
    ("Sobressinal [%]", ca["OS"], mA["OS"]),
    ("Tempo de pico [s]", ca["Tp"], mA["Tp"]),
    ("Acomodação 2 % [s] (4/ζωn)", ca["ts2"], mA["ts2"]),
    ("Período amortecido [s]", ca["Td"], Td_med),
    ("ζ (decremento logarítmico)", ca["zeta"], z_dec),
    ("Pico do pulso [m]", float(np.max(xC_an)), float(np.max(xC))),
]
res["R4"] = [dict(grandeza=g, algebrica=a, simulada=s, dif_pct=(s - a) / a * 100) for g, a, s in r4]
res["R3_erro_max_m"] = dict(a=float(np.max(np.abs(xA - xA_an))), b=float(np.max(np.abs(xB - xB_an))),
                            c=float(np.max(np.abs(xC - xC_an))))

# ---------------- R5 sensibilidade parametrica
niveis = {"m": [0.25, 0.5, 1.0, 2.0, 8.0], "c": [0.0, 2.0, 6.0, 12.0, 30.0], "k": [25.0, 50.0, 100.0, 200.0, 800.0]}
perguntas = {
    "m": "E se a massa for multiplicada por 8? Previsão: ωn cai para 10/√8 = 3,5 rad/s, ζ cai para 0,106, "
         "sobressinal sobe para 72 %, ganho estático não muda.",
    "c": "E se o amortecedor for retirado (c = 0)? Previsão: oscilação permanente em ωn = 10 rad/s, "
         "amplitude de 10 cm em torno de 10 cm (de 0 a 20 cm), no limite do curso.",
    "k": "E se a mola for 8× mais rígida? Previsão: ganho estático cai para 1/8 (1,25 cm), ωn sobe para "
         "28,3 rad/s, ζ cai para 0,106.",
}
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0), sharey=False)
r5 = {}
cols = {}
for a, (p, lv) in zip(ax, niveis.items()):
    r5[p] = []
    for i, v in enumerate(lv):
        kw = dict(m=M, c=C, k=K); kw[p] = v
        t, x, _ = sim(lambda t: F0, T=4.0, n=4001, **kw)
        cc = carac(**kw)
        xinf = F0 / kw["k"]
        mm = medir(t, x, xinf) if cc["zeta"] > 0 else dict(Tp=float(t[np.argmax(x)]), OS=float((x.max() - xinf) / xinf * 100),
                                                         ts2=float("inf"), tr=float("nan"), xinf=float(x[-1]))
        r5[p].append(dict(valor=v, wn=cc["wn"], zeta=cc["zeta"], xinf_cm=xinf * 100, OS_pct=mm["OS"],
                          ts2_s=mm["ts2"], Tp_s=mm["Tp"]))
        nominal = (v == {"m": M, "c": C, "k": K}[p])
        a.plot(t, x * 100, color=COR["ref"] if nominal else SERIE[[0, 1, 3, 4][min(i, 3) if i < 2 else i - 1]],
               ls="--" if nominal else "-", lw=1.8 if nominal else 1.1,
               label=f"{p} = {v:g}" + (" (nominal)" if nominal else ""))
        cols[f"{p}_{v:g}"] = x
    cols["t"] = t
    a.set(xlabel="t [s]", ylabel="x [cm]", title=f"Variação de {p}  ({'kg' if p=='m' else 'N·s/m' if p=='c' else 'N/m'})")
    a.legend(loc="upper right", fontsize=7)
salvar(fig, os.path.join(FIG, "fig-03-sensibilidade-r5.png"))
np.savetxt(os.path.join(DAD, "fig-03-sensibilidade-r5.csv"), np.column_stack([cols["t"]] + [cols[k_] for k_ in cols if k_ != "t"]),
           delimiter=",", header="t_s," + ",".join(k_ for k_ in cols if k_ != "t"), comments="", fmt="%.6g")
res["R5"] = r5
res["R5_perguntas"] = perguntas
json.dump(res, open(os.path.join(DAD, "resultados-caracterizacao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(res["R2"], indent=1, ensure_ascii=False))
for d in res["R4"]: print(d)
print(res["R3_erro_max_m"])
for p in r5:
    for d in r5[p]: print(p, {k_: round(v, 3) for k_, v in d.items()})
