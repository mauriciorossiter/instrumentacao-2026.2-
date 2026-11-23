# -*- coding: utf-8 -*-
"""
Fase 1 / Entrega 03 - G02: validacao funcional da cadeia piezo + lock-in (sem planta).
Tres ensaios-padrao (R11) com a cadeia completa e comparacao camada a camada (R13).
Uso: python analise_f1e3.py <pasta_figuras> <pasta_dados>
"""
import sys, os, json
from dataclasses import replace
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeo import Param, simular
from estilo import plt, COR, SERIE, salvar

FIG, DAD = sys.argv[1], sys.argv[2]
os.makedirs(FIG, exist_ok=True); os.makedirs(DAD, exist_ok=True)
BASE = Param(planta=0, malha=0, seletor=1, G=25.0, A=0.6, t_ev=1.0, T=4.0)
ens = [(1, "(a) Degrau 0 → 0,6 N"), (2, "(b) Condição inicial: solta em t = 1 s"), (3, "(c) Pulso 0,9 N por 0,5 s")]
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0))
out = {}
for a, (e, tit) in zip(ax, ens):
    p = replace(BASE, ensaio=e)
    r = simular(p, dec=10)
    rc = simular(replace(p, comp_cal=1), dec=10)
    a.plot(r["t"], r["r"], color=COR["ideal"], lw=1.8, label="referência ideal (Videal)")
    a.plot(r["t"], r["y_med"], color=COR["med"], lw=1.1, label="medido, sem calibração")
    a.plot(rc["t"], rc["y_med"], color=COR["real"], lw=1.1, label="medido, calibração ×1,625")
    a.set(xlabel="t [s]", ylabel="F [N rms]", title=tit, ylim=(-0.15, 1.05))
    np.savetxt(os.path.join(DAD, f"fig-01-ensaio-{'abc'[e-1]}.csv"),
               np.column_stack([r["t"], r["r"], r["y_med"], rc["y_med"]]), delimiter=",",
               header="t_s,F_ideal_N,F_medido_N,F_medido_calibrado_N", comments="", fmt="%.6g")
    m = r["t"] >= r["t"][-1] - 0.8
    out["abc"[e - 1]] = dict(final_ideal=float(np.mean(r["r"][m])), final_med=float(np.mean(r["y_med"][m])),
                             final_cal=float(np.mean(rc["y_med"][m])))
ax[0].legend(loc="center right", fontsize=7)
salvar(fig, os.path.join(FIG, "fig-01-tres-ensaios.png"))

# camada a camada (degrau)
lim = dict(en_sens=0, en_lim=0, en_res=0, en_ruido=0, en_interf=0)
cam = [("cadeia ideal da E01", dict(**lim)), ("estática (S, limiar, resolução)", dict(lim, en_sens=1, en_lim=1, en_res=1)),
       ("dinâmica sem chopagem (passa-alta)", dict(lim, chop=0)), ("espectral (ruído + 60 Hz + offset + deriva)",
                                                                 dict(lim, en_ruido=1, en_interf=1)),
       ("todas (com chopagem)", dict())]
fig, a = plt.subplots(figsize=(6.6, 3.1))
p = replace(BASE, ensaio=1)
rr = simular(p, dec=10)
a.plot(rr["t"], rr["r"], color=COR["ref"], ls="--", lw=1.2, label="referência ideal")
desvios = []
for i, (n, ex) in enumerate(cam):
    r = simular(replace(p, **ex), dec=10)
    a.plot(r["t"], r["y_med"], color=SERIE[i], lw=1.2, label=n)
    m = r["t"] >= 2.0
    desvios.append(dict(camada=n, desvio_rms_N=float(np.sqrt(np.mean((r["y_med"][m] - r["r"][m]) ** 2))),
                        final_N=float(np.mean(r["y_med"][r["t"] >= 3.2]))))
a.set(xlabel="t [s]", ylabel="F [N rms]", title="R13: cada camada isolada × referência ideal (degrau de 0,6 N)",
      ylim=(-0.25, 0.8))
a.legend(loc="lower right", fontsize=7, ncol=2)
salvar(fig, os.path.join(FIG, "fig-02-camadas.png"))
out["camadas"] = desvios
# previsao e teste: amplitude 1,0 N (previsao: 1,0 x 0,615 = 0,615 N sem calibracao)
r = simular(replace(BASE, ensaio=1, A=1.0), dec=10)
out["previsao_teste_A1N"] = dict(previsto=0.615, obtido=float(np.mean(r["y_med"][r["t"] >= 3.2])))
json.dump(out, open(os.path.join(DAD, "resultados-f1e3.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
