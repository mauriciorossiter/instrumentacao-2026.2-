# -*- coding: utf-8 -*-
"""
Fase 2 / Entregas 02 e 03 - G02.
E02: circuito RLC (gemeo do modelo.tse, passo 1e-4 s) x solucao analitica do dominio mecanico; sensibilidade a R, L, C.
E03: exacerbacao das caracteristicas do instrumento em malha aberta.
Uso: python analise_e2_e3.py <figuras_e2> <dados_e2> <figuras_e3> <dados_e3>
"""
import sys, os, json, math
from dataclasses import replace
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeo import Param, simular
from estilo import plt, COR, SERIE, salvar

F2, D2, F3, D3 = sys.argv[1:5]
for d in (F2, D2, F3, D3):
    os.makedirs(d, exist_ok=True)


def analitica(t, F, x0, m=1.0, c=6.0, k=100.0):
    wn = math.sqrt(k / m); z = c / (2 * math.sqrt(k * m)); wd = wn * math.sqrt(1 - z * z)
    xinf = F / k; a = x0 - xinf
    return xinf + np.exp(-z * wn * t) * (a * np.cos(wd * t) + z * wn * a / wd * np.sin(wd * t))


def deg(t, A):
    y = np.zeros_like(t); m = t >= 0; y[m] = analitica(t[m], A, 0.0); return y


# ---------------- E02 / R3: tres ensaios no circuito (malha aberta, caminho ideal), evento em t_ev = 2 s
base = Param(malha=0, seletor=0, A=10.0, t_ev=2.0, T=6.0)
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0))
res = {}
for a, (e, tit) in zip(ax, [(1, "(a) Degrau de 10 V (10 N) em t = 2 s"), (2, "(b) Solta de x = 10 cm em t = 2 s"),
                            (3, "(c) Pulso de 15 V entre 2,0 e 2,5 s")]):
    r = simular(replace(base, ensaio=e), dec=10)
    t = r["t"]; tt = t - 2.0
    if e == 1:
        xa = deg(tt, 10.0) * 100
    elif e == 2:
        xa = np.where(tt < 0, 10.0 * (1 - np.nan), 0) if False else None
        xa = np.where(tt < 0, np.nan, analitica(np.clip(tt, 0, None), 0.0, 0.10) * 100)
    else:
        xa = np.where(tt < 0, np.nan, 10 + (deg(tt, 5.0) - deg(tt - 0.5, 5.0)) * 100)
    a.plot(t, xa, color=COR["ref"], lw=2.6, alpha=0.45, label="analítica (domínio mecânico)")
    a.plot(t, r["y_real"], color=COR["real"], lw=1.1, label="circuito (v_C em V)")
    a.set(xlabel="t [s]", ylabel="x [cm] = v_C [V]", title=tit)
    m = ~np.isnan(xa) & (t >= 2.0)
    err = float(np.max(np.abs(r["y_real"][m] - xa[m])))
    i = np.argmax(r["y_real"] * (t >= 2.0)) if e != 2 else None
    res["abc"[e - 1]] = dict(erro_max_cm=err, pico_cm=float(np.max(r["y_real"][t >= 2.0])),
                             t_pico=float(t[np.argmax(np.where(t >= 2.0, r["y_real"], -1e9))] - 2.0))
    np.savetxt(os.path.join(D2, f"fig-02-validacao-{'abc'[e-1]}.csv"), np.column_stack([t, r["y_real"], np.nan_to_num(xa, nan=-999)]),
               delimiter=",", header="t_s,vC_circuito_V,x_analitica_cm(-999=sem referencia)", comments="", fmt="%.6g")
ax[0].legend(loc="lower right", fontsize=7)
salvar(fig, os.path.join(F2, "fig-02-validacao.png"))

# ---------------- E02 / R4: sensibilidade aos elementos do circuito (degrau de 10 V)
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0))
sens = {}
for a, (par, nome, unid, lv, conv) in zip(ax, [
        ("c", "R", "Ω", [2.0, 6.0, 12.0, 30.0], lambda v: v),
        ("m", "L", "H", [0.25, 1.0, 2.0, 8.0], lambda v: v),
        ("k", "C", "mF", [40.0, 20.0, 10.0, 5.0], lambda v: 1000.0 / v)]):
    sens[nome] = []
    for i, v in enumerate(lv):
        pv = conv(v)
        p = replace(base, ensaio=1, T=6.0, **{par: pv})
        r = simular(p, dec=10)
        xcm = r["y_real"] * 100.0 / p.k          # x = q = v_C / k  [cm]
        nominal = (nome, v) in (("R", 6.0), ("L", 1.0), ("C", 10.0))
        a.plot(r["t"] - 2.0, xcm, color=COR["ref"] if nominal else SERIE[[0, 1, 3, 4][i]],
               ls="--" if nominal else "-", lw=1.8 if nominal else 1.1, label=f"{nome} = {v:g} {unid}" + (" (nominal)" if nominal else ""))
        y = xcm[r["t"] >= 2.0]
        yinf = 10.0 * 100.0 / pv if par == "k" else 10.0
        sens[nome].append(dict(valor=v, final_cm=float(np.mean(y[-500:])), pico_cm=float(y.max()),
                               OS_pct=float((y.max() - yinf) / yinf * 100)))
    a.set(xlim=(-0.2, 4.0), xlabel="t − t_ev [s]", ylabel="x = q [cm]", title=f"Variação de {nome}")
    a.legend(loc="upper right", fontsize=7)
salvar(fig, os.path.join(F2, "fig-03-sensibilidade-circuito.png"))
res["R4"] = sens
json.dump(res, open(os.path.join(D2, "resultados-e2.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False)[:1500])

# ---------------- E03 / R5: exacerbacao (malha aberta, degrau de 10 N)
lim = dict(en_sens=0, en_lim=0, en_res=0, en_ruido=0, en_interf=0)
b3 = Param(malha=0, seletor=1, ensaio=1, A=10.0, t_ev=0.5, T=3.5, **lim)
casos = [("fc = 0,3 Hz\n(filtro 3× mais lento)", dict(fc=0.3)),
         ("S = 68,6 mV/N\n(extremo superior)", dict(en_sens=1, S_real=0.0686)),
         ("ruído σ = 500 mV\n(25× o nominal)", dict(en_ruido=1, sigma=0.5)),
         ("60 Hz de 500 mV\nsem chopagem", dict(en_interf=1, a_hum=0.5, chop=0))]
fig, axs = plt.subplots(1, 4, figsize=(10.5, 2.7), sharey=True)
ex = []
for a, (n, e) in zip(axs, casos):
    r = simular(replace(b3, **e), dec=10)
    a.plot(r["t"], r["y_ideal"], color=COR["ideal"], label="ideal")
    a.plot(r["t"], r["y_med"], color=COR["med"], lw=0.9, label="medido")
    a.set(title=n, xlabel="t [s]", ylim=(-6, 20))
    m = r["t"] >= 0.5
    ex.append(dict(caso=n, erro_rms_cm=float(np.sqrt(np.mean((r["y_med"][m] - r["y_ideal"][m]) ** 2)))))
axs[0].set_ylabel("x [cm]"); axs[0].legend(loc="lower right", fontsize=7)
for a in axs:
    a.title.set_fontsize(8)
salvar(fig, os.path.join(F3, "fig-05-exacerbacao.png"))
json.dump(ex, open(os.path.join(D3, "resultados-e3-exacerbacao.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(ex)
