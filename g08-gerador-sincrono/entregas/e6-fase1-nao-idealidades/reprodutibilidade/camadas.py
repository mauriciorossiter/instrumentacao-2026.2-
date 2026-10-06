# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Camadas nao ideais sobre a cadeia da Entrega 01 (R6-R10) - gabarito Python.

Cadeia (ordem fisica):
  theta_ref (eixo) -> [folga/backlash] -> theta_c (cursor) -> [resolucao] -> x_q
  -> sensor de ordem zero (x_q . VREF) -> [ruido de contato: dR_c . I_cursor]
  -> v_cursor -> MESMO circuito da Entrega 01 (OPA333 -> R0/RIN -> XTR115 -> laco) -> I_LOOP

As funcoes folga(), resolucao() e GeradorRosa reproduzem, operacao por operacao, o codigo C
da C function 'potenciometro' do TyphoonSim (monta_modelo.py), para que o gabarito e a
simulacao sejam comparaveis amostra a amostra.

As camadas estao definidas em modelo_camadas.py (fonte unica, compartilhada com o
codigo C do TyphoonSim gerado por monta_modelo.py).

Uso:  python camadas.py
Saidas:
    resultados_camadas.json                 <- todos os numeros citados no relatorio
    gabarito_<caso>.csv                     <- curvas esperadas para comparar com o TyphoonSim
    ../Fase1_Latex/valores_python.tex       <- macros LaTeX com os numeros
    figuras fig-07 ... fig-11 (PNG + PDF)
"""
import json
import re
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import welch

import parametros as P
from estilo import aplica_estilo, salva, AZUL, LARANJA, AQUA, AMARELO, TINTA, TINTA2, CINZA

AQUI = os.path.dirname(os.path.abspath(__file__))
aplica_estilo()
R = {}

# =====================================================================
# 1. Camadas: definicao unica em modelo_camadas.py (a mesma do codigo C do TyphoonSim)
# =====================================================================
from modelo_camadas import (cadeia, cadeia_sem_buffer, metricas, CASOS, CASOS_R8, K_ENR,
                            DRC as dRc, N_AMOSTRAS)

t = np.arange(N_AMOSTRAS) * P.DT_SINAL
th = P.theta_ref(t)
SAIDAS = {k: cadeia(th, c, dRc) for k, c in CASOS.items()}
SAIDAS['so_folga'] = cadeia(th, {'folga'})
SAIDAS['so_resolucao'] = cadeia(th, {'resolucao'})

# contrafactual R8 (potenciometro eletrico, sem buffer) - gabarito do modelo_r8_sem_buffer.tse
for k, c in CASOS_R8.items():
    SAIDAS[k] = cadeia_sem_buffer(th, c, dRc)

for k in list(CASOS) + list(CASOS_R8):
    s = SAIDAS[k]
    np.savetxt(os.path.join(AQUI, 'gabarito_%s.csv' % k),
               np.column_stack([t, th, s['theta_c'], s['v_cursor'], s['I_mA'], s['I_mA'] * P.R_L / 1e3]),
               delimiter=',', header='t_s,theta_ref_graus,theta_cursor_graus,v_cursor_V,I_loop_mA,V_RL_V',
               comments='', fmt='%.12g')


# =====================================================================
# 2. Metricas (modelo_camadas.metricas - as mesmas aplicadas ao TyphoonSim)
# =====================================================================
# (a) na grade de 1 ms do TyphoonSim - e o que se compara com a simulacao
R['casos'] = {}
for k in list(CASOS) + ['so_folga', 'so_resolucao']:
    R['casos'][k] = metricas(t, th, SAIDAS[k]['I_mA'])[0]

# (b) na grade fina (~0,06 ms = ~0,022 grau por amostra, passo incomensuravel com a espira) -
#     valores "verdadeiros" das camadas deterministicas; a 1 ms (0,36 grau por amostra)
#     histerese e zona morta saem quantizadas
tf = np.linspace(0, P.T_VARREDURA, 333331)
thf = P.theta_ref(tf)
R['casos_grade_fina'] = {}
for k, cam in [('ideal', set()), ('estatica', {'folga', 'resolucao'}),
               ('so_folga', {'folga'}), ('so_resolucao', {'resolucao'})]:
    R['casos_grade_fina'][k] = metricas(tf, thf, cadeia(thf, cam)['I_mA'])[0]

# desvio de cada camada contra a saida ideal da Entrega 01 (R9), em graus do eixo, medido
# no cursor (v_cursor/VREF . 3600) para nao misturar o ganho dos resistores comerciais.
# Camadas deterministicas: grade fina; ruido (definido a 1 ms, como no TyphoonSim): grade de 1 ms.
SF = {k: cadeia(thf, cam) for k, cam in [('ideal', set()), ('estatica', {'folga', 'resolucao'}),
                                         ('so_folga', {'folga'}), ('so_resolucao', {'resolucao'})]}
ideal = SAIDAS['ideal']['I_mA']
def desvio_graus(k):
    if k in SF:
        return P.THETA_FS * (SF[k]['v_cursor'] - SF['ideal']['v_cursor']) / P.VREF
    return P.THETA_FS * (SAIDAS[k]['v_cursor'] - SAIDAS['ideal']['v_cursor']) / P.VREF

R['desvio_contra_E01'] = {}
for k in ['so_resolucao', 'so_folga', 'estatica', 'espectral']:
    d = desvio_graus(k)
    R['desvio_contra_E01'][k] = dict(max_graus=float(np.max(np.abs(d))),
                                     max_pcFS=float(100 * np.max(np.abs(d)) / P.THETA_FS))

# =====================================================================
# 3. R6 - numeros da camada estatica
# =====================================================================
R['r6'] = dict(
    resolucao_pc=100 * P.RES_POT, N_passos=P.N_PASSOS, passo_graus=P.PASSO_GRAUS,
    passo_mV=1e3 * P.VREF / P.N_PASSOS, passo_uA=1e6 * P.I_SPAN / P.N_PASSOS,
    erro_quantizacao_max_graus=P.PASSO_GRAUS / 2,
    erro_quantizacao_max_pcFS=100 * P.RES_POT / 2,
    folga_graus=P.FOLGA_GRAUS, folga_pcFS=100 * P.FOLGA_GRAUS / P.THETA_FS,
    zona_morta_min_graus=P.FOLGA_GRAUS, zona_morta_max_graus=P.FOLGA_GRAUS + P.PASSO_GRAUS,
    taxa_varredura_graus_s=P.THETA_FS / (P.T_VARREDURA / 2),
    amostras_por_passo=P.PASSO_GRAUS / (P.THETA_FS / (P.T_VARREDURA / 2) * P.DT_SINAL),
)

# =====================================================================
# 4. R7 - dinamica: ordem zero do sensor e polos da eletronica
# =====================================================================
tau_buf = 1 / (2 * np.pi * P.GBW_BUF)
tau_xtr = 1 / (2 * np.pi * P.BW_XTR)
R_th_max = P.R_POT / 4 + P.ENR_POT                 # Thevenin do cursor no meio da trilha + contato
tau_in = R_th_max * P.CIN_BUF
tau_tot = tau_buf + tau_xtr + tau_in              # atraso de rampa de polos em cascata
vel = P.THETA_FS / (P.T_VARREDURA / 2)            # 360 graus/s
vel_max = P.RPM_MAX_POT * 360 / 60                # 1200 graus/s
R['r7'] = dict(
    tau_buffer_us=1e6 * tau_buf, tau_xtr_us=1e6 * tau_xtr, tau_entrada_ns=1e9 * tau_in,
    tau_total_us=1e6 * tau_tot,
    velocidade_varredura_graus_s=vel, rpm_varredura=vel * 60 / 360,
    rpm_max_datasheet=P.RPM_MAX_POT,
    atraso_rampa_graus=tau_tot * vel, atraso_rampa_pcFS=100 * tau_tot * vel / P.THETA_FS,
    atraso_rampa_rpm_max_graus=tau_tot * vel_max,
    razao_passo_typhoon_sobre_tau=P.DT_SINAL / tau_tot,
    atraso_numerico_typhoon_graus=2 * P.DT_SINAL * vel,
    f_fundamental_varredura_Hz=1 / P.T_VARREDURA,
)
# resposta ao degrau da eletronica (dois polos reais) - escala de microssegundos
ts = np.linspace(0, 5e-6, 2001)
a, b_ = tau_buf, tau_xtr
deg2 = 1 - (a * np.exp(-ts / a) - b_ * np.exp(-ts / b_)) / (a - b_)
R['r7']['t_99_us'] = float(1e6 * ts[np.argmax(deg2 >= 0.99)])

# =====================================================================
# 5. R8 - ruido de contato 1/f
# =====================================================================
f, psd = welch(dRc, fs=1 / P.DT_SINAL, nperseg=4096)
banda = (f >= 0.5) & (f <= 200)
incl = np.polyfit(np.log10(f[banda]), np.log10(psd[banda]), 1)[0]
x = np.linspace(0, 1, 1001)
Rth = x * (1 - x) * P.R_POT
# sem buffer: o cursor alimenta RIN direto; o contato fica em serie (I = x.VREF/(Rth+Rc+RIN))
I_sem = lambda rc: x * P.VREF / (Rth + rc + P.RIN)
e_sem_buffer = 100 * np.max(np.abs(I_sem(0.0) - I_sem(P.ENR_POT))) / (P.VREF / P.RIN)
R['r8'] = dict(
    ENR_ohm=P.ENR_POT, K_escala=float(K_ENR),
    dRc_rms_ohm=float(np.std(dRc)), dRc_pico_ohm=float(np.max(np.abs(dRc))),
    inclinacao_psd_dec=float(incl),
    I_cursor_pA=1e12 * P.I_CURSOR,
    v_ruido_buffer_nV=1e9 * P.ENR_POT * P.I_CURSOR,
    erro_buffer_pcFS=100 * P.ENR_POT * P.I_CURSOR / P.VREF,
    v_ruido_ensaio_mV=1e3 * P.ENR_POT * P.I_TESTE_ENR,
    erro_ensaio_pcFS=100 * P.ENR_POT * P.I_TESTE_ENR / P.VREF,
    erro_sem_buffer_pcFS=float(e_sem_buffer),
    fator_buffer=float(e_sem_buffer / (100 * P.ENR_POT * P.I_CURSOR / P.VREF)),
)

# contrafactual R8 no circuito: o que o TyphoonSim deve mostrar sem o buffer
m_sb = metricas(t, th, SAIDAS['r8_sem_buffer']['I_mA'])[0]
m_sbs = metricas(t, th, SAIDAS['r8_sem_buffer_sem_ruido']['I_mA'])[0]
d_ruido = SAIDAS['r8_sem_buffer']['I_mA'] - SAIDAS['r8_sem_buffer_sem_ruido']['I_mA']
R['r8_circuito_sem_buffer'] = dict(
    R_min_ohm=P.R_MIN_POT, R_c0_ohm=P.R_C0,
    erro_lin_subida_pcFS=m_sb['erro_lin_subida_pcFS'], erro_total_pcFS=m_sb['erro_total_pcFS'],
    erro_lin_sem_ruido_pcFS=m_sbs['erro_lin_subida_pcFS'],
    ruido_pico_pcFS=float(100 * np.max(np.abs(d_ruido)) / 16.0),
    ruido_rms_pcFS=float(100 * np.std(d_ruido) / 16.0),
    atende=m_sb['atende'],
)

# =====================================================================
# 6. Figuras
# =====================================================================
FE = P.THETA_FS


def envoltoria(x, y, nb=300):
    """min/max de y em nb faixas de x - para desenhar um dente de serra denso como faixa."""
    o = np.argsort(x); x, y = x[o], y[o]
    ed = np.linspace(x[0], x[-1], nb + 1)
    i = np.clip(np.searchsorted(ed, x, side='right') - 1, 0, nb - 1)
    lo = np.full(nb, np.nan); hi = np.full(nb, np.nan)
    np.fmin.at(lo, i, y); np.fmax.at(hi, i, y)
    return 0.5 * (ed[1:] + ed[:-1]), lo, hi


def br(v, nd):
    return ('%.*f' % (nd, v)).replace('.', ',')


def brt(v, nd):
    """como br, com o sinal de menos tipografico (so para as macros LaTeX)"""
    return br(v, nd).replace('-', r'\textminus{}')

# ---- fig-07: R6, camada estatica (curva fina, para ver os degraus)
est = cadeia(thf, {'folga', 'resolucao'})
ind = est['x_q'] * FE                                # angulo indicado pelo cursor
subf = tf <= P.T_VARREDURA / 2
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw=dict(width_ratios=[1, 1.25], wspace=0.32))
j = (thf > 1795.5) & (thf < 1801.5)
ax[0].plot(thf[j & subf], thf[j & subf], color=CINZA, lw=1.0, ls='--', label='ideal (E01)')
ax[0].plot(thf[j & subf], ind[j & subf], color=AZUL, lw=1.4, label='subida')
ax[0].plot(thf[j & ~subf], ind[j & ~subf], color=LARANJA, lw=1.4, label='descida')
ax[0].set_xlabel('$\\theta_{ref}$ [graus]'); ax[0].set_ylabel('ângulo indicado [graus]')
ax[0].set_title('zoom: degraus de %s° e folga de %s°' % (br(P.PASSO_GRAUS, 2), br(P.FOLGA_GRAUS, 1)), fontsize=8.5)
ax[0].legend(loc='upper left', fontsize=7.4)
for m, cor, rot_ in [(subf, AZUL, 'subida'), (~subf, LARANJA, 'descida')]:
    xc, lo, hi = envoltoria(thf[m], (ind - thf)[m])
    ax[1].fill_between(xc, lo, hi, color=cor, alpha=0.55, lw=0, label=rot_)
ax[1].axhline(0, color=CINZA, lw=0.8)
ax[1].set_xlabel('$\\theta_{ref}$ [graus]'); ax[1].set_ylabel('indicado − referência [graus]')
ax[1].set_xlim(0, FE); ax[1].set_ylim(-0.7, 1.7)
ax2 = ax[1].secondary_yaxis('right', functions=(lambda g: 100 * g / FE, lambda p: p * FE / 100))
ax2.set_ylabel('[% FE]')
ax[1].legend(loc='upper left', fontsize=7.4, ncol=2)
ax[1].set_title('desvio ao longo da faixa', fontsize=8.5)
salva(fig, 'fig-07-r6-estatica')

# ---- fig-08: R7, dinamica
fig, ax = plt.subplots(figsize=(6.6, 2.6))
ax.plot(1e6 * ts, np.where(ts > 0, 1.0, 0.0), color=CINZA, lw=1.2, ls='--', label='sensor de ordem zero (ideal)')
ax.plot(1e6 * ts, deg2, color=AZUL, lw=1.6, label='+ polos do OPA333 e do XTR115')
ax.axvline(R['r7']['t_99_us'], color=TINTA2, lw=0.7, ls=':')
ax.text(R['r7']['t_99_us'] + 0.08, 0.80, '99 %% em %s µs' % br(R['r7']['t_99_us'], 2), fontsize=7.8, color=TINTA2)
ax.text(3.05, 0.45, 'um passo do TyphoonSim = 1000 µs\n(≈ %d× a constante de tempo total)'
        % round(R['r7']['razao_passo_typhoon_sobre_tau'], -1), fontsize=7.8, color=TINTA2)
ax.set_xlabel('tempo após um degrau [µs]'); ax.set_ylabel('saída normalizada')
ax.set_xlim(0, 5); ax.set_ylim(-0.05, 1.12)
ax.legend(loc='lower right', fontsize=7.6)
salva(fig, 'fig-08-r7-dinamica')

# ---- fig-09: R8, ruido de contato
fig = plt.figure(figsize=(7.0, 4.6))
g = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], hspace=0.55, wspace=0.34)
a0 = fig.add_subplot(g[0, :]); a1 = fig.add_subplot(g[1, 0]); a2 = fig.add_subplot(g[1, 1])
a0.plot(t, dRc, color=AZUL, lw=0.6)
a0.axhline(P.ENR_POT, color=TINTA2, lw=0.7, ls='--'); a0.axhline(-P.ENR_POT, color=TINTA2, lw=0.7, ls='--')
a0.text(0.15, P.ENR_POT * 0.72, 'ENR máx. = 100 Ω (pico)', fontsize=7.5, color=TINTA2,
        bbox=dict(fc='white', ec='none', alpha=0.85, pad=1.0))
a0.set_xlabel('tempo [s]'); a0.set_ylabel('$\\Delta R_c$ [Ω]'); a0.set_xlim(0, P.T_SIM)
a0.set_title('(a) resistência de contato do cursor: realização 1/f do gabarito (semente fixa)', fontsize=8.5)
a1.loglog(f[1:], psd[1:], color=AZUL, lw=1.0)
ref = psd[banda][0] * f[banda][0] / f[1:]
a1.loglog(f[1:], ref, color=LARANJA, lw=1.0, ls='--', label='inclinação 1/f')
a1.set_xlabel('frequência [Hz]'); a1.set_ylabel('DEP de $\\Delta R_c$ [Ω²/Hz]')
a1.set_title('(b) espectro: inclinação %s déc./déc.' % br(incl, 2), fontsize=8.5)
a1.legend(loc='lower left', fontsize=7.4)
cen = ['cadeia E01\n(buffer, 200 pA)', 'sem buffer\n(cursor → $R_{IN}$)', 'ensaio do\ndatasheet (1 mA)']
val = [R['r8']['erro_buffer_pcFS'], R['r8']['erro_sem_buffer_pcFS'], R['r8']['erro_ensaio_pcFS']]
a2.bar(range(3), val, color=[AZUL, CINZA, CINZA], width=0.6)
a2.set_yscale('log'); a2.set_ylim(1e-7, 30)
a2.axhline(1.0, color=LARANJA, lw=1.0, ls='--'); a2.text(-0.42, 0.25, 'especificação:\n1 % FE', fontsize=7.2, color=LARANJA, va='top')
for i, v in enumerate(val):
    a2.text(i, v * 2.0, ('%.1e' % v).replace('.', ','), ha='center', fontsize=7.4, color=TINTA)
a2.set_xticks(range(3)); a2.set_xticklabels(cen, fontsize=7.2)
a2.set_ylabel('pico do ruído na saída [% FE]')
a2.set_title('(c) $v_n=\\Delta R_c\\cdot I_{cursor}$', fontsize=8.5)
salva(fig, 'fig-09-r8-espectral')

# ---- fig-10: R9, cada camada contra o sinal ideal da E01 (mesma varredura, mesma base de tempo)
fig, ax = plt.subplots(3, 1, figsize=(7.0, 5.0), sharex=True, gridspec_kw=dict(hspace=0.42))
d_est = desvio_graus('estatica')
xc, lo, hi = envoltoria(tf, d_est, 400)
ax[0].fill_between(xc, lo, hi, color=AZUL, alpha=0.6, lw=0)
ax[0].set_ylabel('[graus]'); ax[0].set_ylim(-0.6, 1.6)
ax[0].set_title('R6 estática (resolução + folga): saída − ideal E01', fontsize=8.5, loc='left')
ax[0].text(0.3, 0.55, 'subida: ±%s° (meio passo)' % br(P.PASSO_GRAUS / 2, 2), fontsize=7.4, color=TINTA2)
ax[0].text(10.3, 0.15, 'descida: folga de +1° somada ao meio passo', fontsize=7.4, color=TINTA2)
d_din = np.where(np.diff(th, prepend=th[0]) >= 0, -1, 1) * R['r7']['atraso_rampa_graus']
ax[1].plot(t, d_din, color=AQUA, lw=1.2)
ax[1].set_ylabel('[graus]'); ax[1].set_ylim(-5e-4, 5e-4)
ax[1].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
ax[1].set_title('R7 dinâmica (ordem zero + polos da eletrônica): atraso de rampa τ·dθ/dt', fontsize=8.5, loc='left')
d_esp = desvio_graus('espectral')
ax[2].plot(t, 1e6 * d_esp, color=LARANJA, lw=0.5)
ax[2].set_ylabel('[µgraus]')
ax[2].set_title('R8 espectral (ruído de contato 1/f, com o buffer da E01)', fontsize=8.5, loc='left')
ax[2].set_xlabel('tempo [s]'); ax[2].set_xlim(0, P.T_SIM)
salva(fig, 'fig-10-r9-camadas')

# ---- fig-11: R10, cadeia completa no circuito da E01 + resumo por camada
mc, e_lin_c, e_tot_c = metricas(t, th, SAIDAS['completa']['I_mA'])
_, _, e_tot_i = metricas(t, th, ideal)
sub = t <= P.T_VARREDURA / 2 + P.DT_SINAL / 2
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1.35, 1], wspace=0.42))
ax[0].plot(th[sub], e_tot_c[sub], color=AZUL, lw=0.7, label='completa, subida')
ax[0].plot(th[~sub], e_tot_c[~sub], color=LARANJA, lw=0.7, label='completa, descida')
ax[0].plot(th, e_tot_i, color=TINTA, lw=0.9, ls='--', label='ideal E01 (resistores E192)')
ax[0].set_xlabel('$\\theta_{ref}$ [graus]'); ax[0].set_ylabel('erro total [% FE]')
ax[0].set_xlim(0, FE); ax[0].set_ylim(-0.08, 0.2)
ax[0].text(3500, -0.07, 'especificação: ±1 % FE (fora da escala)', fontsize=7.0, color=TINTA2, ha='right')
ax[0].legend(loc='upper left', fontsize=7.0)
ax[0].set_title('(a) erro total da cadeia completa', fontsize=8.5)
rot = ['espectral\n(ruído)', 'dinâmica\n(polos)', 'resolução', 'folga', 'resistores\nE192 (E01)', 'linearidade\npot. (não atrib.)']
vals = [R['desvio_contra_E01']['espectral']['max_pcFS'], R['r7']['atraso_rampa_pcFS'],
        R['desvio_contra_E01']['so_resolucao']['max_pcFS'], R['desvio_contra_E01']['so_folga']['max_pcFS'],
        R['casos']['ideal']['erro_total_pcFS'], 100 * P.LIN_POT]
cores = [LARANJA, AQUA, AZUL, AZUL, CINZA, CINZA]
ax[1].barh(range(6), vals, color=cores, height=0.6)
ax[1].set_xscale('log'); ax[1].set_xlim(1e-7, 3)
ax[1].axvline(1.0, color=LARANJA, lw=1.0, ls='--')
ax[1].set_yticks(range(6)); ax[1].set_yticklabels(rot, fontsize=7.0)
ax[1].set_xlabel('desvio máximo [% FE]')
ax[1].set_title('(b) contribuição por camada', fontsize=8.5)
salva(fig, 'fig-11-r10-completa')

# ---- fig-13: contrafactual R8 no circuito (sem buffer), gabarito do modelo_r8_sem_buffer.tse
sbI = SAIDAS['r8_sem_buffer']['I_mA']
_, _, e_sb = metricas(t, th, sbI)
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw=dict(width_ratios=[1.15, 1], wspace=0.38))
ax[0].axhspan(-1, 1, color=CINZA, alpha=0.18, lw=0, label='especificação ±1 % FE')
ax[0].plot(th[sub], e_sb[sub], color=LARANJA, lw=0.8, label='sem buffer (cursor → $R_{IN}$)')
ax[0].plot(th[sub], e_tot_c[sub], color=AZUL, lw=1.2, label='com buffer (cadeia da E01)')
ax[0].set_xlabel('$\\theta_{ref}$ [graus]'); ax[0].set_ylabel('erro total [% FE]')
ax[0].set_xlim(0, FE); ax[0].set_ylim(-14.5, 2); ax[0].legend(loc='lower left', fontsize=7.0, ncol=1)
ax[0].set_title('(a) efeito de carga + ruído, subida', fontsize=8.5)
ax[1].plot(t, 100 * d_ruido / 16.0, color=LARANJA, lw=0.5)
ax[1].axhline(0, color=CINZA, lw=0.8)
ax[1].set_xlabel('tempo [s]'); ax[1].set_ylabel('parcela do ruído [% FE]')
ax[1].set_xlim(0, P.T_SIM)
ax[1].set_title('(b) só o ruído de contato (com − sem ruído)', fontsize=8.5)
ax[1].text(0.3, -0.5, 'cresce com x: a corrente no cursor é ∝ x', fontsize=7.2, color=TINTA2)
salva(fig, 'fig-13-r8-sem-buffer')

# =====================================================================
# 7. Saidas
# =====================================================================
with open(os.path.join(AQUI, 'resultados_camadas.json'), 'w', encoding='utf-8') as fh:
    json.dump(R, fh, indent=2, ensure_ascii=False)


def cient(v, nd=1):
    m, e = ('%.*e' % (nd, v)).split('e')
    return r'\ensuremath{%s\times10^{%d}}' % (m.replace('.', '{,}'), int(e))


C = R['casos']; F = R['casos_grade_fina']; D = R['desvio_contra_E01']
mac = {
    'pyPasso': br(P.PASSO_GRAUS, 2), 'pyPassoMv': br(R['r6']['passo_mV'], 1),
    'pyPassoUa': br(R['r6']['passo_uA'], 1), 'pyNpassos': '%d' % P.N_PASSOS,
    'pyQmaxG': br(R['r6']['erro_quantizacao_max_graus'], 2), 'pyQmaxFE': br(R['r6']['erro_quantizacao_max_pcFS'], 3),
    'pyFolgaFE': br(R['r6']['folga_pcFS'], 4), 'pyAmPasso': br(R['r6']['amostras_por_passo'], 0),
    'pyZMmax': br(R['r6']['zona_morta_max_graus'], 2),
    'pyEstHist': br(F['estatica']['histerese_graus'], 2), 'pyEstHistFE': br(F['estatica']['histerese_pcFS'], 3),
    'pyEstZM': br(F['estatica']['zona_morta_reversao_graus'], 2),
    'pyEstLin': br(F['estatica']['erro_lin_subida_pcFS'], 3), 'pyEstBanda': br(F['estatica']['erro_lin_banda_pcFS'], 3),
    'pyFolgaHist': br(F['so_folga']['histerese_graus'], 2), 'pyFolgaZM': br(F['so_folga']['zona_morta_reversao_graus'], 2),
    'pyEstTot': br(F['estatica']['erro_total_pcFS'], 3), 'pyEstAng': br(F['estatica']['erro_angulo_graus'], 2),
    'pyTyEstHist': br(C['estatica']['histerese_graus'], 2), 'pyTyEstZM': br(C['estatica']['zona_morta_reversao_graus'], 2),
    'pyResMax': br(D['so_resolucao']['max_graus'], 2), 'pyFolgaMax': br(D['so_folga']['max_graus'], 2),
    'pyEstMax': br(D['estatica']['max_graus'], 2), 'pyEstMaxFE': br(D['estatica']['max_pcFS'], 3),
    'pyDescMin': br(P.FOLGA_GRAUS - P.PASSO_GRAUS / 2, 2),
    'pyOrdensFund': br(np.log10(min(P.GBW_BUF, P.BW_XTR) * P.T_VARREDURA), 1).replace(',', '{,}'),
    'pyMargem': br(100 * P.ERRO_LIN_MAX / C['completa']['erro_total_pcFS'], 1),
    'pyTauBuf': br(R['r7']['tau_buffer_us'], 3), 'pyTauXtr': br(R['r7']['tau_xtr_us'], 3),
    'pyTauIn': br(R['r7']['tau_entrada_ns'], 1), 'pyTauTot': br(R['r7']['tau_total_us'], 2),
    'pyTnn': br(R['r7']['t_99_us'], 2), 'pyRpm': br(R['r7']['rpm_varredura'], 0),
    'pyAtrasoRampa': cient(R['r7']['atraso_rampa_graus']), 'pyAtrasoRampaFE': cient(R['r7']['atraso_rampa_pcFS']),
    'pyAtrasoRpmMax': cient(R['r7']['atraso_rampa_rpm_max_graus']),
    'pyRazaoTy': '%d' % round(R['r7']['razao_passo_typhoon_sobre_tau'], -1),
    'pyAtrasoTy': br(R['r7']['atraso_numerico_typhoon_graus'], 2),
    'pyInclin': brt(R['r8']['inclinacao_psd_dec'], 2), 'pyRuidoRms': br(R['r8']['dRc_rms_ohm'], 1),
    'pyRuidoBufNv': br(R['r8']['v_ruido_buffer_nV'], 0), 'pyRuidoBufFE': cient(R['r8']['erro_buffer_pcFS']),
    'pyRuidoSemFE': br(R['r8']['erro_sem_buffer_pcFS'], 2), 'pyRuidoEnsMv': br(R['r8']['v_ruido_ensaio_mV'], 0),
    'pyRuidoEnsFE': br(R['r8']['erro_ensaio_pcFS'], 1), 'pyFatorBuf': cient(R['r8']['fator_buffer'], 1),
    'pyEspMax': cient(D['espectral']['max_graus']),
    'pyCompLin': br(C['completa']['erro_lin_subida_pcFS'], 4), 'pyCompBanda': br(C['completa']['erro_lin_banda_pcFS'], 4),
    'pyCompTot': br(C['completa']['erro_total_pcFS'], 3), 'pyIdealTot': br(C['ideal']['erro_total_pcFS'], 3),
    'pyCompHist': br(C['completa']['histerese_graus'], 2), 'pyCompHistFE': br(C['completa']['histerese_pcFS'], 4),
    'pyCompAng': br(C['completa']['erro_angulo_graus'], 2), 'pyIdealAng': br(C['ideal']['erro_angulo_graus'], 2),
    'pyCompZM': br(C['completa']['zona_morta_reversao_graus'], 2),
    'pyCompAtende': 'atende' if C['completa']['atende'] else 'não atende',
    'pyVTX': br(P.V_LOOP - np.max(SAIDAS['completa']['I_mA']) * 1e-3 * (P.R_L + P.R_CABO), 2),
    'pyKenr': br(K_ENR, 3),
    'pySbLin': br(R['r8_circuito_sem_buffer']['erro_lin_subida_pcFS'], 2),
    'pySbTot': br(R['r8_circuito_sem_buffer']['erro_total_pcFS'], 2),
    'pySbRuido': br(R['r8_circuito_sem_buffer']['ruido_pico_pcFS'], 2),
    'pySbRuidoRms': br(R['r8_circuito_sem_buffer']['ruido_rms_pcFS'], 3),
    'pyRcZero': br(P.R_C0, 0), 'pyRmin': br(P.R_MIN_POT, 0),
}
with open(os.path.join(AQUI, '..', 'Fase1_Latex', 'valores_python.tex'), 'w', encoding='utf-8') as fh:
    fh.write('%% gerado por reprodutibilidade/camadas.py\n')
    for k, v in mac.items():
        # virgula decimal como {,}: sem espaco extra tambem dentro de $...$
        fh.write(r'\newcommand{\%s}{%s}' % (k, re.sub(r'(?<!\{),(?!\})', '{,}', v)) + '\n')

for bloco, d in R.items():
    print('\n[%s]' % bloco)
    for k, v in d.items():
        print('   %-34s %s' % (k, v))
