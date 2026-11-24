# -*- coding: utf-8 -*-
"""
Entrega Final (Fase 2) - G02: gera figuras (PNG) e dados (CSV/JSON) dos itens 3 a 8.

Uso:  python analise_final.py <pasta_figuras> <pasta_dados>
Todas as curvas vem do gemeo numerico (gemeo.py), que reproduz bloco a bloco o modelo.tse.
As previsoes do item 7 sao calculadas pelo modelo LINEAR (sem portadora, sem ruido) e gravadas
em previsoes-item7.json ANTES de qualquer varredura simulada.
"""
import sys, os, json, math, time
from dataclasses import replace, asdict
import numpy as np
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeo import Param, simular, metricas, atende, CRIT, coef_butter
from estilo import plt, COR, SERIE, salvar

FIG, DAD = sys.argv[1], sys.argv[2]
os.makedirs(FIG, exist_ok=True); os.makedirs(DAD, exist_ok=True)
P0 = Param()
LIMPO = dict(en_sens=0, en_lim=0, en_res=0, en_ruido=0, en_interf=0)


def csv(nome, cols):
    keys = list(cols)
    n = max(len(np.atleast_1d(cols[k])) for k in keys)
    arr = np.column_stack([np.resize(np.atleast_1d(np.asarray(cols[k], dtype=float)), n) for k in keys])
    np.savetxt(os.path.join(DAD, nome + ".csv"), arr, delimiter=",", header=",".join(keys), comments="", fmt="%.6g")


def r2(d):
    return {k: (round(float(v), 4) if isinstance(v, (int, float, np.floating)) else v) for k, v in d.items()}


# ======================================================================================
# Modelo linear para previsao (item 7)
# ======================================================================================
def resp_linear(fc=None, g=1.0, p=P0, T=4.0, A=10.0, fcorr=None):
    """Degrau r->x da malha linear: PID (D na medicao) + P(s) + g*H_bw(s)*[corretor]."""
    s = np.poly1d([1, 0])
    Pn, Pd = np.poly1d([p.k]), np.poly1d([p.m, p.c, p.k])
    if fc:
        wb = 2 * np.pi * fc
        Hn, Hd = np.poly1d([1.0]), np.poly1d([1 / wb**2, math.sqrt(2) / wb, 1])
    else:
        Hn, Hd = np.poly1d([1.0]), np.poly1d([1.0])
    if fcorr:
        wb, wf = 2 * np.pi * fcorr, 2 * np.pi * p.f_f
        Hn = Hn * np.poly1d([1 / wb**2, math.sqrt(2) / wb, 1]); Hd = Hd * np.poly1d([1 / wf**2, 2 / wf, 1])
    # C_r = (Kp s + Ki)/s ; C_y = (Kp s + Ki)/s + Kd s/(Tf s+1)
    Tf = np.poly1d([p.Tf, 1])
    Cyn = (np.poly1d([p.Kp, p.Ki]) * Tf + np.poly1d([p.Kd, 0, 0]))
    Cyd = s * Tf
    Crn, Crd = np.poly1d([p.Kp, p.Ki]), s
    # x/r = Cr P / (1 + Cy g H P)
    # Cyd = s*Tf e Crd = s: o fator s cancela
    num = Crn * Pn * Tf * Hd
    den = Pd * Cyd * Hd + g * Cyn * Pn * Hn
    t = np.linspace(0, T, 4001)
    _, y = signal.step(signal.TransferFunction(num.coeffs, den.coeffs), T=t)
    y = A * y
    estavel = np.all(np.real(np.roots(den.coeffs)) < 0)
    os_ = max(0.0, (y.max() - A) / A * 100) if estavel else float("inf")
    fora = np.where(np.abs(y - A) > 0.02 * A)[0]
    ts = t[fora[-1]] if len(fora) else 0.0
    return t, y, os_, ts, estavel


def margem_ganho(fc, p=P0):
    """Maior g (fator de sensibilidade S/S_nom) com malha linear estavel."""
    lo, hi = 1.0, 20.0
    if not resp_linear(fc, hi, p)[4]:
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if resp_linear(fc, mid, p)[4]:
                lo = mid
            else:
                hi = mid
        return lo
    return float("inf")


t0 = time.time()
print("== previsoes (modelo linear)")
fcs_fino = np.round(np.concatenate([np.arange(1, 10, 0.1), np.arange(10, 31, 1)]), 2)
os_pred = []
for fc in fcs_fino:
    os_pred.append(resp_linear(fc)[2])
os_pred = np.array(os_pred)
idx = np.where(np.array(os_pred) <= CRIT["os"])[0][0]
fc_crit_pred = float(fcs_fino[idx])
g_lim = margem_ganho(10.0)
prev = {
    "gerado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
    "metodo": "malha linear (PID com D na medicao + planta + Butterworth 2a ordem), sem portadora e sem ruido",
    "item7a_fc_minimo_para_sobressinal_10pct_Hz": fc_crit_pred,
    "item7a_ripple_portadora": "atenuacao do Butterworth em 200 Hz = (fc/200)^2; com Kd=0,2 e Tf=0,01 s o ganho do "
                                "PID em 200 Hz e ~|Kd/Tf|=20 -> esforco de ripple ~ 20*A*(fc/200)^2/sqrt(2)",
    "item7a_fc_maximo_ripple_1N_Hz": float(200 * math.sqrt(1.0 * math.sqrt(2) / (20 * 10))),
    "item7b_erro_regime_pct": "e_ss = S_nom/S - 1 (acao integral zera o erro da MEDICAO, nao o da planta)",
    "item7b_faixa_S_sobre_Snom_para_2pct": [1 / 1.02, 1 / 0.98],
    "item7b_margem_ganho_fc10Hz_S_sobre_Snom": round(g_lim, 3),
}
json.dump(prev, open(os.path.join(DAD, "previsoes-item7.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(prev, indent=1, ensure_ascii=False))

resultados = {"previsoes": prev}

# ======================================================================================
# Item 3 - caracteristicas
# ======================================================================================
print("== item 3")
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0))
F = np.linspace(0, 20, 50)
ax[0].fill_between(F, 0.0246 * F, 0.0686 * F, color=COR["real"], alpha=0.12, lw=0, label="faixa de tolerância")
ax[0].plot(F, 0.04 * F, color=COR["ref"], ls="--", label="S nominal 40 mV/N")
ax[0].plot(F, 0.0246 * F, color=COR["real"], label="S mín. 24,6 mV/N (−38 %)")
ax[0].plot(F, 0.0686 * F, color=COR["med"], label="S máx. 68,6 mV/N (+71 %)")
ax[0].set(xlabel="força na mola Fk [N] (= x [cm])", ylabel="Vs = S·Fk [V]", title="(a) Estática: sensibilidade")
ax[0].legend(loc="upper left")
f = np.logspace(-2, 3, 600); w = 2 * np.pi * f
tau = 10e6 * 10e-9
Hhp = (1j * w * tau) / (1 + 1j * w * tau)
wb = 2 * np.pi * 1.0
Hbw = 1 / (1 - (w / wb) ** 2 + 1j * math.sqrt(2) * w / wb)
ax[1].semilogx(f, 20 * np.log10(np.abs(Hhp)), color=COR["c5"], label="piezo Ct–Rin (passa-alta, 1,59 Hz)")
ax[1].semilogx(f, 20 * np.log10(np.abs(Hbw)), color=COR["med"], label="Butterworth do lock-in (1 Hz)")
ax[1].axvline(100, color=COR["crit"], ls=":", lw=1); ax[1].text(105, -55, "portadora\n100 Hz", fontsize=7, color=COR["ref"])
ax[1].axvspan(0.01, 10 / (2 * np.pi) * 1.0, color=COR["ideal"], alpha=0.10, lw=0)
ax[1].text(0.012, -25, "banda da planta\n(ωn = 10 rad/s)", fontsize=7, color=COR["ref"])
ax[1].set(xlabel="frequência [Hz]", ylabel="|H| [dB]", ylim=(-90, 5), title="(b) Dinâmica: sensor e condicionamento")
ax[1].legend(loc="lower left", bbox_to_anchor=(0.0, 0.0))
# espectro no pre-amp e apos demodulacao (malha aberta, F = 10 N em regime)
p = replace(P0, malha=0, seletor=1, ensaio=1, A=10.0, t_ev=0.0, T=3.0, en_sens=0)
res = simular(p, dec=1)
msk = res["t"] >= 1.0
for key, cor, lab in (("pre_amp", COR["real"], "saída do pré-amp"), ("demod", COR["med"], "após demodulação")):
    xx = res[key][msk]; N = len(xx)
    X = np.abs(np.fft.rfft(xx * np.hanning(N))) / (N / 4)
    ff = np.fft.rfftfreq(N, 1e-4)
    ax[2].semilogy(ff, X + 1e-6, color=cor, lw=0.9, label=lab)
ax[2].set(xlim=(0, 260), ylim=(1e-4, 20), xlabel="frequência [Hz]", ylabel="amplitude [V]",
          title="(c) Espúrias: 60 Hz, offset, deriva, ruído")
for fx, tx in ((60, "60"), (40, "40"), (160, "160"), (200, "2f")):
    ax[2].axvline(fx, color=COR["crit"], ls=":", lw=0.8)
ax[2].legend(loc="upper right")
salvar(fig, os.path.join(FIG, "fig-03-caracteristicas.png"))
csv("fig-03-caracteristicas", {"f_Hz": f, "Hhp_dB": 20 * np.log10(np.abs(Hhp)), "Hbw_dB": 20 * np.log10(np.abs(Hbw))})

# ======================================================================================
# Item 4 - malha aberta, cada caracteristica isolada
# ======================================================================================
print("== item 4")
base_ma = replace(P0, malha=0, seletor=1, ensaio=1, A=10.0, t_ev=0.5, T=3.5, **LIMPO)
casos = [
    ("só lock-in (S nominal)", {}),
    ("+ desvio de sensibilidade", dict(en_sens=1)),
    ("+ ruído e interferências", dict(en_ruido=1, en_interf=1)),
    ("+ limiar e resolução", dict(en_lim=1, en_res=1)),
    ("sem chopagem (passa-alta)", dict(chop=0, fc=1.0)),
    ("cadeia real completa", dict(en_sens=1, en_lim=1, en_res=1, en_ruido=1, en_interf=1)),
]
fig, axs = plt.subplots(2, 3, figsize=(10.5, 5.2), sharex=True)
tab4 = []
cols = {}
for i, (nome, ex) in enumerate(casos):
    pp = replace(base_ma, **ex)
    rr = simular(pp, dec=10)
    a = axs.flat[i]
    a.plot(rr["t"], rr["y_ideal"], color=COR["ideal"], label="ideal (x real)")
    a.plot(rr["t"], rr["y_med"], color=COR["med"], lw=1.2, label="medido")
    a.set_title(f"({'abcdef'[i]}) {nome}")
    a.set_ylim(-2, 17)
    if i % 3 == 0: a.set_ylabel("x [cm]")
    if i >= 3: a.set_xlabel("t [s]")
    m = rr["t"] >= pp.t_ev
    err = rr["y_med"][m] - rr["y_ideal"][m]
    fim = rr["t"][m] >= rr["t"][-1] - 0.8
    tab4.append(dict(caso=nome, erro_rms_cm=float(np.sqrt(np.mean(err**2))),
                     erro_final_pct=float(np.mean(err[fim]) / 10 * 100),
                     ruido_final_cm=float(np.std(err[fim]))))
    cols.setdefault("t", rr["t"]); cols["ideal"] = rr["y_ideal"]; cols[f"med_{i}"] = rr["y_med"]
axs.flat[0].legend(loc="lower right")
salvar(fig, os.path.join(FIG, "fig-04-malha-aberta-isoladas.png"))
csv("fig-04-malha-aberta-isoladas", cols)
resultados["item4"] = [r2(d) for d in tab4]
for d in tab4: print(r2(d))

# ======================================================================================
# Item 5 e 6 - controle ideal e controle real
# ======================================================================================
print("== itens 5 e 6")
pi = replace(P0, seletor=0, T=4.0, t_ev=1.0)
ri = simular(pi, dec=10); mi = metricas(ri, pi)
pr = replace(P0, seletor=1, T=4.0, t_ev=1.0)
rr = simular(pr, dec=10)
mr_real = metricas(rr, pr, "y_real"); mr_med = metricas(rr, pr, "y_med")
fig, ax = plt.subplots(2, 1, figsize=(6.4, 4.4), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
ax[0].axhspan(9.8, 10.2, color=COR["ideal"], alpha=0.12, lw=0, label="faixa de ±2 %")
ax[0].axhline(11.0, color=COR["crit"], ls=":", lw=1, label="sobressinal máx. 10 %")
ax[0].plot(ri["t"], ri["r"], color=COR["ref"], ls="--", lw=1.2, label="referência r")
ax[0].plot(ri["t"], ri["y_real"], color=COR["real"], label="x (planta)")
ax[0].axvline(1.0 + CRIT["ts"], color=COR["crit"], lw=0.8, ls="-.")
ax[0].text(1.0 + CRIT["ts"] + 0.03, 2, "ts máx.\n1,0 s", fontsize=7, color=COR["ref"])
ax[0].set(ylabel="x [cm]", ylim=(-0.5, 12.5), title="Controle com instrumento ideal (PID Kp=2, Ki=10, Kd=0,2)")
ax[0].legend(loc="lower right", ncol=2)
ax[1].plot(ri["t"], ri["u"], color=COR["u"], label="esforço u (força)")
ax[1].axhline(30, color=COR["crit"], ls=":", lw=1)
ax[1].set(xlabel="t [s]", ylabel="u [N]", ylim=(-2, 34))
ax[1].legend(loc="upper right")
salvar(fig, os.path.join(FIG, "fig-05-controle-ideal.png"))
csv("fig-05-controle-ideal", {k: ri[k] for k in ("t", "r", "y_real", "u")})

fig, ax = plt.subplots(2, 1, figsize=(6.4, 4.4), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
ax[0].axhspan(9.8, 10.2, color=COR["ideal"], alpha=0.12, lw=0)
ax[0].plot(rr["t"], rr["r"], color=COR["ref"], ls="--", lw=1.2, label="referência r")
ax[0].plot(rr["t"], rr["y_med"], color=COR["med"], lw=1.2, label="medido (entra no PID)")
ax[0].plot(rr["t"], rr["y_real"], color=COR["real"], label="x real da planta")
ax[0].set(ylabel="x [cm]", title="Mesmo controlador com o instrumento real (cadeia da E02, fc = 1 Hz)")
ax[0].legend(loc="upper left", ncol=3)
ax[1].plot(rr["t"], rr["u"], color=COR["u"], lw=1.0, label="esforço u")
ax[1].axhline(30, color=COR["crit"], ls=":", lw=1); ax[1].axhline(-30, color=COR["crit"], ls=":", lw=1)
ax[1].set(xlabel="t [s]", ylabel="u [N]")
ax[1].legend(loc="upper left")
salvar(fig, os.path.join(FIG, "fig-06-controle-real.png"))
csv("fig-06-controle-real", {k: rr[k] for k in ("t", "r", "y_med", "y_real", "u")})
# decomposicao: o que causa cada diferenca
dec6 = []
for nome, ex in [("cadeia real completa", {}),
                 ("sem desvio de S", dict(en_sens=0)),
                 ("sem ruído/interferências", dict(en_ruido=0, en_interf=0)),
                 ("sem limiar/resolução", dict(en_lim=0, en_res=0)),
                 ("só o lock-in (fc = 1 Hz)", dict(**LIMPO)),
                 ("lock-in com fc = 10 Hz, demais ligadas", dict(fc=10.0))]:
    pp = replace(pr, **ex); r_ = simular(pp, dec=20)
    a_, b_ = metricas(r_, pp, "y_real"), metricas(r_, pp, "y_med")
    dec6.append(dict(caso=nome, real=r2(a_), medido=r2(b_), atende=atende(a_)))
resultados["item5"] = r2(mi)
resultados["item6"] = dict(real=r2(mr_real), medido=r2(mr_med), decomposicao=dec6)
print("ideal", r2(mi)); print("real", r2(mr_real)); print("medido", r2(mr_med))
for d in dec6: print(d)

# ======================================================================================
# Item 7 - ponto de ruptura (simulado, depois da previsao)
# ======================================================================================
print("== item 7")
fcs = [2, 3, 4, 5, 6, 6.5, 7, 8, 10, 12, 15, 17, 20, 25]
sw_fc = []
for fc in fcs:
    pp = replace(P0, seletor=1, T=4.0, fc=fc, **LIMPO); r_ = simular(pp, dec=20); m_ = metricas(r_, pp)
    sw_fc.append(dict(fc=fc, **r2(m_), atende=atende(m_)))
Ss = [0.5, 0.615, 0.8, 0.9, 0.95, 0.97, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03, 1.05, 1.1, 1.25, 1.5, 1.715, 2.0, 2.2, 2.5]
sw_S = []
for g in Ss:
    pp = replace(P0, seletor=1, T=4.0, fc=10.0, **dict(LIMPO, en_sens=1), S_real=0.04 * g)
    r_ = simular(pp, dec=20); m_ = metricas(r_, pp)
    sw_S.append(dict(S_rel=g, **r2(m_), atende=atende(m_)))
resultados["item7"] = dict(fc=sw_fc, S=sw_S)
ok_fc = [d["fc"] for d in sw_fc if d["atende"]]
ok_S = [d["S_rel"] for d in sw_S if d["atende"]]
resultados["item7"]["janela_fc_Hz"] = [min(ok_fc), max(ok_fc)] if ok_fc else None
resultados["item7"]["janela_S_rel"] = [min(ok_S), max(ok_S)] if ok_S else None
print("janela fc", resultados["item7"]["janela_fc_Hz"], "janela S", resultados["item7"]["janela_S_rel"])

fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.1))
ax[0].plot(fcs_fino, np.clip(os_pred, 0, 200), color=COR["ref"], ls="--", lw=1.2, label="previsão (modelo linear)")
ax[0].plot([d["fc"] for d in sw_fc], [min(d["os"], 200) for d in sw_fc], "o", color=COR["med"], ms=5, label="simulado")
ax[0].axhline(10, color=COR["crit"], ls=":", lw=1)
ax[0].axvline(fc_crit_pred, color=COR["ref"], lw=0.8)
ax[0].set(xscale="log", xlabel="fc do lock-in [Hz]", ylabel="sobressinal [%]", ylim=(0, 60),
          title="(a) Sobressinal × fc")
ax[0].set_xticks([2, 3, 5, 7, 10, 15, 20, 25]); ax[0].set_xticklabels(["2", "3", "5", "7", "10", "15", "20", "25"])
ax[0].legend(loc="upper right")
ax[1].plot([d["fc"] for d in sw_fc], [min(d["u_rip"], 60) for d in sw_fc], "o-", color=COR["u"], ms=5, label="simulado")
ffp = np.linspace(2, 25, 100)
ax[1].plot(ffp, 20 * 10 * (ffp / 200) ** 2 / math.sqrt(2), color=COR["ref"], ls="--", lw=1.2, label="previsão (ripple 2f)")
ax[1].axhline(1.0, color=COR["crit"], ls=":", lw=1)
ax[1].set(xlabel="fc do lock-in [Hz]", ylabel="ripple do esforço [N rms]", ylim=(0, 5),
          title="(b) Ripple do esforço × fc")
ax[1].legend(loc="upper left")
gg = np.array([d["S_rel"] for d in sw_S])
ax[2].plot(np.linspace(0.45, 2.6, 200), (1 / np.linspace(0.45, 2.6, 200) - 1) * 100, color=COR["ref"], ls="--",
           lw=1.2, label="previsão S_nom/S − 1")
ax[2].plot(gg, [max(-100, min(d["ess"], 120)) for d in sw_S], "o", color=COR["real"], ms=5, label="simulado")
ax[2].axhspan(-2, 2, color=COR["ideal"], alpha=0.15, lw=0)
ax[2].axvline(g_lim, color=COR["crit"], ls=":", lw=1); ax[2].text(g_lim + 0.03, 60, "instável\n(margem\nde ganho)", fontsize=7)
ax[2].axvline(0.615, color=COR["med"], lw=0.8, ls="-."); ax[2].axvline(1.715, color=COR["med"], lw=0.8, ls="-.")
ax[2].text(0.63, -80, "S mín", fontsize=7); ax[2].text(1.73, -80, "S máx", fontsize=7)
ax[2].set(xlabel="S / S_nom", ylabel="erro de regime da planta [%]", ylim=(-100, 110),
          title="(c) Erro de regime × sensibilidade (fc = 10 Hz)")
ax[2].legend(loc="upper right")
salvar(fig, os.path.join(FIG, "fig-07-ponto-de-ruptura.png"))
csv("fig-07-ponto-de-ruptura", {"fc_Hz": [d["fc"] for d in sw_fc], "os_pct": [d["os"] for d in sw_fc],
                                "u_rip_N": [d["u_rip"] for d in sw_fc]})
csv("fig-07-ponto-de-ruptura-S", {"S_rel": gg, "ess_pct": [d["ess"] for d in sw_S], "os_pct": [d["os"] for d in sw_S]})
csv("fig-07-previsao-linear", {"fc_Hz": fcs_fino, "os_pred_pct": np.clip(os_pred, 0, 1e3)})

# ======================================================================================
# Item 8 - compensacao (correcoes calculadas)
# ======================================================================================
print("== item 8")
cenarios = [("real, sem compensação", {}), ("só calibração (×1,625)", dict(comp_cal=1)),
            ("só correção dinâmica", dict(comp_din=1)), ("calibração + correção dinâmica", dict(comp_cal=1, comp_din=1))]
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.3))
tab8 = []
cols8 = {}
for i, (nome, ex) in enumerate(cenarios):
    pp = replace(pr, **ex); r_ = simular(pp, dec=10)
    a_, b_ = metricas(r_, pp, "y_real"), metricas(r_, pp, "y_med")
    tab8.append(dict(caso=nome, real=r2(a_), medido=r2(b_), atende=atende(a_)))
    cols8.setdefault("t", r_["t"]); cols8[f"x_real_{i}"] = r_["y_real"]; cols8[f"u_{i}"] = r_["u"]
    if i in (0, 3):
        a = ax[0]
        a.plot(r_["t"], r_["y_real"], color=[COR["real"], None, None, COR["ideal"]][i], lw=1.4 if i == 3 else 1.0,
               label=f"x real – {nome}")
ax[0].plot(ri["t"], ri["r"], color=COR["ref"], ls="--", lw=1.2, label="referência")
ax[0].axhspan(9.8, 10.2, color=COR["ideal"], alpha=0.12, lw=0)
ax[0].set(xlabel="t [s]", ylabel="x [cm]", ylim=(-5, 30), title="(a) Instrumento real: antes × depois")
ax[0].legend(loc="upper left")
# janela de fc real tolerada com o corretor ajustado em 1 Hz
fca = [0.8, 0.9, 0.95, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0]
sw8 = []
for fc in fca:
    pp = replace(P0, seletor=1, T=4.0, fc=fc, fc_corr=1.0, comp_din=1, **LIMPO); r_ = simular(pp, dec=20)
    m_ = metricas(r_, pp); sw8.append(dict(fc=fc, **r2(m_), atende=atende(m_)))
sw8b = []
for fc in fca:
    pp = replace(P0, seletor=1, T=4.0, fc=fc, fc_corr=0.85, comp_din=1, **LIMPO); r_ = simular(pp, dec=20)
    m_ = metricas(r_, pp); sw8b.append(dict(fc=fc, **r2(m_), atende=atende(m_)))
ax[1].plot(fca, [min(d["os"], 60) for d in sw8], "o-", color=COR["med"], ms=5, label="corretor ajustado em 1,00 Hz")
ax[1].plot(fca, [min(d["os"], 60) for d in sw8b], "s-", color=COR["real"], ms=5, label="corretor ajustado em 0,85 Hz")
ax[1].axhline(10, color=COR["crit"], ls=":", lw=1)
ax[1].axvspan(0.9, 1.1, color=COR["ideal"], alpha=0.12, lw=0)
ax[1].text(0.905, 50, "tolerância\n±10 % do\nfiltro", fontsize=7, color=COR["ref"])
ax[1].set(xlabel="fc real do filtro do lock-in [Hz]", ylabel="sobressinal [%]", ylim=(0, 60),
          title="(b) Robustez da correção ao fc real")
ax[1].legend(loc="upper right")
salvar(fig, os.path.join(FIG, "fig-08-compensacao.png"))
csv("fig-08-compensacao", cols8)
csv("fig-08-compensacao-robustez", {"fc_real_Hz": fca, "os_corr_1Hz": [d["os"] for d in sw8],
                                    "os_corr_085Hz": [d["os"] for d in sw8b],
                                    "urip_corr_1Hz": [d["u_rip"] for d in sw8], "urip_corr_085Hz": [d["u_rip"] for d in sw8b]})
ok8 = [d["fc"] for d in sw8 if d["atende"]]; ok8b = [d["fc"] for d in sw8b if d["atende"]]
resultados["item8"] = dict(cenarios=tab8, robustez_1Hz=sw8, robustez_085Hz=sw8b,
                           janela_1Hz=[min(ok8), max(ok8)] if ok8 else None,
                           janela_085Hz=[min(ok8b), max(ok8b)] if ok8b else None)
for d in tab8: print(d)
print("janelas", resultados["item8"]["janela_1Hz"], resultados["item8"]["janela_085Hz"])

# ruido residual da medicao em regime (malha aberta, F = 10 N)
ruido = []
for nome, ex in [("fc = 1 Hz", {}), ("fc = 10 Hz", dict(fc=10.0)), ("fc = 1 Hz + correção", dict(comp_din=1))]:
    pp = replace(P0, malha=0, seletor=1, A=10.0, t_ev=0.0, T=4.0, en_sens=0, en_lim=0, en_res=0, **ex)
    r_ = simular(pp, dec=1); m = r_["t"] >= 2.0
    ruido.append(dict(caso=nome, desvio_mm=float(np.std(r_["y_med"][m]) * 10), media_cm=float(np.mean(r_["y_med"][m]))))
resultados["ruido_residual"] = [r2(d) for d in ruido]
print(ruido)

json.dump(resultados, open(os.path.join(DAD, "resultados-final.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print(f"ok em {time.time()-t0:.0f} s")
