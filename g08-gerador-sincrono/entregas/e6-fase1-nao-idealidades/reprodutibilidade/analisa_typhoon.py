# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Analisa os CSV do TyphoonSim (R9/R10): aplica as MESMAS metricas do gabarito Python
(modelo_camadas.metricas) a cada caso, compara amostra a amostra com o gabarito e gera a
figura e as macros LaTeX dos resultados da simulacao.

Uso:  python analisa_typhoon.py          (Python comum: numpy, pandas, matplotlib)
Entradas:  ../typhoonsim/dados/varredura_<caso>.csv   (caso = ideal, estatica, espectral, completa,
                                                        r8_sem_buffer, r8_sem_buffer_sem_ruido;
                                                        'completa' e obrigatorio)
           gabarito_<caso>.csv                         (gerados por camadas.py)
Saidas:    resultados_typhoon.json, fig-12-r10-typhoon, ../Fase1_Latex/valores_typhoon.tex

Aceita o CSV exportado pela API (roda_typhoon.py) ou exportado do Scope na interface, desde
que as colunas tenham os nomes das sondas.
"""
import json
import re
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import parametros as P
from scipy.signal import welch

from modelo_camadas import metricas, io_transmissor, filtro_kellet, K_ENR
from estilo import aplica_estilo, salva, AZUL, LARANJA, AQUA, TINTA, TINTA2, CINZA

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.environ.get('G08_TESTE') or os.path.join(AQUI, '..', 'typhoonsim', 'dados')
SAIDA = os.environ.get('G08_TESTE') or AQUI
aplica_estilo()

SONDAS = ['theta_ref', 'theta_med', 'I_LOOP_mA', 'V_RL_V', 'V_TX_V', 'I_IN_uA',
          'v_cursor', 'erro_FE_pc', 'I_receptor_mA', 'theta_cursor', 'dRc_ohm']
CASOS = ['ideal', 'estatica', 'espectral', 'completa', 'r8_sem_buffer', 'r8_sem_buffer_sem_ruido']
# sondas lidas direto dos blocos de sinal (sem passar pelo circuito eletrico): sem atraso numerico
SEM_ATRASO = ('theta_cursor', 'theta_resolucao', 'v_cursor', 'dRc_ohm', 'ruido_branco_N01')
# O Random Source nativo nao tem semente: nos casos com ruido, a comparacao ponto a ponto com o
# gabarito e feita so na parte deterministica (contra o caso equivalente sem ruido); o ruido e
# comparado pela estatistica, e o filtro 1/f nativo e conferido a partir do branco sorteado.
REF_DETERMINISTICA = {'espectral': 'ideal', 'completa': 'estatica', 'r8_sem_buffer': 'r8_sem_buffer_sem_ruido'}


def carrega(caso):
    f = os.path.join(DADOS, 'varredura_%s.csv' % caso)
    if not os.path.exists(f):
        return None
    df = pd.read_csv(f)
    mapa = {}
    for c in df.columns:
        base = c.split('.')[-1].strip()           # aceita 'Root.theta_ref' etc.
        if base.lower() in ('time', 't', 'tempo', 'time [s]'):
            mapa[c] = 'Time'
        for s in SONDAS:
            if base.lower() == s.lower():
                mapa[c] = s
    df = df.rename(columns=mapa)
    faltam = [s for s in ['Time', 'theta_ref', 'I_LOOP_mA', 'V_TX_V'] if s not in df.columns]
    if faltam:
        sys.exit('CSV %s sem as colunas %s (colunas lidas: %s)' % (f, faltam, list(df.columns)))
    return df


def alinha(df, gab, lag_max=10):
    """Atraso numerico do TyphoonSim (uma amostra por passagem sinal -> circuito -> sinal;
    2 ms na Entrega 01). Estimado contra o gabarito DO MESMO CASO, entao as camadas nao
    enviesam a estimativa. Desloca as colunas medidas e descarta a inicializacao."""
    I_ = df['I_LOOP_mA'].to_numpy()
    ref = np.interp(df['Time'], gab['t_s'], gab['I_loop_mA'])
    n0 = lag_max + 5
    erros = [np.max(np.abs(I_[n0 + k:] - ref[n0:len(I_) - k])) for k in range(lag_max + 1)]
    lag = int(np.argmin(erros))
    out = df.iloc[:len(df) - lag][['Time', 'theta_ref']].reset_index(drop=True)
    for c in df.columns:
        if c in SEM_ATRASO:                       # sondas do dominio de sinal: mesmo passo de theta_ref
            out[c] = df[c].to_numpy()[:len(df) - lag]
        elif c not in ('Time', 'theta_ref'):      # sondas que passam pelo circuito: deslocadas
            out[c] = df[c].to_numpy()[lag:]
    return out, lag


R = {}
DF = {}
for caso in CASOS:
    df = carrega(caso)
    if df is None:
        continue
    gab = pd.read_csv(os.path.join(AQUI, 'gabarito_%s.csv' % caso))
    gab_det = pd.read_csv(os.path.join(AQUI, 'gabarito_%s.csv' % REF_DETERMINISTICA.get(caso, caso)))
    df, lag = alinha(df, gab_det)
    t = df['Time'].to_numpy(); th = df['theta_ref'].to_numpy(); I = df['I_LOOP_mA'].to_numpy()
    m = metricas(t, th, I)[0]
    m['atraso_numerico_amostras'] = lag
    m['atraso_numerico_ms'] = 1e3 * lag * P.DT_SINAL
    m['V_TX_min_V'] = float(df['V_TX_V'].min())
    # parte deterministica: contra o gabarito sem ruido (o ruido do Typhoon e outra realizacao)
    m['dif_typhoon_python_max_uA'] = float(1e3 * np.max(np.abs(I - np.interp(t, gab_det['t_s'], gab_det['I_loop_mA']))))
    if 'theta_cursor' in df:
        m['dif_theta_cursor_max_graus'] = float(np.max(np.abs(
            df['theta_cursor'].to_numpy() - np.interp(t, gab['t_s'], gab['theta_cursor_graus']))))
    if 'dRc_ohm' in df and 'ruido_branco_N01' in df and caso in REF_DETERMINISTICA:
        dr = df['dRc_ohm'].to_numpy()
        # filtro 1/f nativo x Python, a partir do MESMO branco que o Random Source sorteou
        m['dif_filtro_1f_ohm'] = float(np.max(np.abs(dr - K_ENR * filtro_kellet(df['ruido_branco_N01'].to_numpy()))))
        f_, psd = welch(dr, fs=1 / P.DT_SINAL, nperseg=4096)
        bd = (f_ >= 0.5) & (f_ <= 200)
        m['ruido_rms_ohm'] = float(np.std(dr))
        m['ruido_pico_ohm'] = float(np.max(np.abs(dr)))
        m['ruido_inclinacao_dec'] = float(np.polyfit(np.log10(f_[bd]), np.log10(psd[bd]), 1)[0])
    R[caso] = m
    DF[caso] = (df, gab)

if 'completa' not in R:
    sys.exit('Falta ../typhoonsim/dados/varredura_completa.csv - rode roda_typhoon.py antes.')

with open(os.path.join(SAIDA, 'resultados_typhoon.json'), 'w', encoding='utf-8') as fh:
    json.dump(R, fh, indent=2, ensure_ascii=False)
for caso, m in R.items():
    print('\n[%s]' % caso)
    for k, v in m.items():
        print('   %-30s %s' % (k, v))

# ======================================================================= figura
df, gab = DF['completa']
t = df['Time'].to_numpy(); th = df['theta_ref'].to_numpy(); I = df['I_LOOP_mA'].to_numpy()
_, _, e_tot = metricas(t, th, I)
sub = t <= P.T_VARREDURA / 2 + P.DT_SINAL / 2
x = th / P.THETA_FS
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1.2, 1], wspace=0.36))
ax[0].plot(th[sub], e_tot[sub], color=AZUL, lw=0.7, label='TyphoonSim, subida')
ax[0].plot(th[~sub], e_tot[~sub], color=LARANJA, lw=0.7, label='TyphoonSim, descida')
ax[0].text(3550, -0.065, 'máx. |TyphoonSim − Python| = %s µA' % ('%.1e' % R['completa']['dif_typhoon_python_max_uA']).replace('.', ','),
           fontsize=7.0, color=TINTA2, ha='right')
ax[0].set_xlabel('$\\theta_{ref}$ [graus]'); ax[0].set_ylabel('erro total [% FE]')
ax[0].set_xlim(0, P.THETA_FS); ax[0].set_ylim(-0.08, 0.2)
ax[0].legend(loc='upper left', fontsize=7.0)
ax[0].set_title('(a) cadeia completa no circuito da E01', fontsize=8.5)
# zoom na reversao: degraus de resolucao e zona morta da folga. Angulo indicado descontando
# o ganho e o zero dos resistores comerciais da E01, para isolar o efeito das camadas.
i0, i1 = 1e3 * io_transmissor(0.0), 1e3 * io_transmissor(1.0)
ang = lambda Iv: P.THETA_FS * (np.asarray(Iv) - i0) / (i1 - i0)
j = (t > P.T_VARREDURA / 2 - 0.012) & (t < P.T_VARREDURA / 2 + 0.012)
jg = (gab['t_s'] > P.T_VARREDURA / 2 - 0.013) & (gab['t_s'] < P.T_VARREDURA / 2 + 0.013)
ax[1].plot(1e3 * (t[j] - P.T_VARREDURA / 2), th[j] - P.THETA_FS, color=CINZA, lw=1.0, ls='--', label='$\\theta_{ref}$')
ax[1].step(1e3 * (gab['t_s'][jg] - P.T_VARREDURA / 2), ang(gab['I_loop_mA'][jg]) - P.THETA_FS,
           where='mid', color=TINTA, lw=0.8, label='gabarito Python')
ax[1].plot(1e3 * (t[j] - P.T_VARREDURA / 2), ang(I[j]) - P.THETA_FS, 'o', ms=3.2, color=AZUL, label='TyphoonSim (1 ms)')
ax[1].set_xlim(-12, 12); ax[1].set_ylim(-5, 1.5)
ax[1].set_xlabel('tempo em relação à reversão [ms]'); ax[1].set_ylabel('ângulo indicado − 3600 [graus]')
ax[1].legend(loc='lower center', fontsize=7.0)
ax[1].annotate('zona morta', xy=(1.5, 0.2), xytext=(3.5, 0.9), fontsize=7.4, color=TINTA2,
               arrowprops=dict(arrowstyle='-', color=TINTA2, lw=0.6))
ax[1].set_title('(b) zoom na reversão', fontsize=8.5)
salva(fig, 'fig-12-r10-typhoon')


# fig-14: contrafactual R8 no TyphoonSim (potenciometro eletrico, sem buffer)
if 'r8_sem_buffer' in DF and 'r8_sem_buffer_sem_ruido' in DF:
    d1, g1 = DF['r8_sem_buffer']; d0, _ = DF['r8_sem_buffer_sem_ruido']
    n = min(len(d1), len(d0))
    t1 = d1['Time'].to_numpy()[:n]; th1 = d1['theta_ref'].to_numpy()[:n]
    I1 = d1['I_LOOP_mA'].to_numpy()[:n]; I0 = d0['I_LOOP_mA'].to_numpy()[:n]
    _, _, e1 = metricas(t1, th1, I1)
    s1 = t1 <= P.T_VARREDURA / 2 + P.DT_SINAL / 2
    dr = 100 * (I1 - I0) / 16.0
    R['r8_sem_buffer']['ruido_pico_pcFS'] = float(np.max(np.abs(dr)))
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw=dict(width_ratios=[1.15, 1], wspace=0.38))
    ax[0].axhspan(-1, 1, color=CINZA, alpha=0.18, lw=0, label='especificação ±1 % FE')
    ax[0].plot(th1[s1], e1[s1], color=LARANJA, lw=0.8, label='TyphoonSim, sem buffer')
    ax[0].plot(th[sub], e_tot[sub], color=AZUL, lw=1.2, label='TyphoonSim, com buffer (E01)')
    ax[0].set_xlabel('$\\theta_{ref}$ [graus]'); ax[0].set_ylabel('erro total [% FE]')
    ax[0].set_xlim(0, P.THETA_FS); ax[0].set_ylim(-14.5, 2); ax[0].legend(loc='lower left', fontsize=7.0)
    ax[0].set_title('(a) efeito de carga + ruído, subida', fontsize=8.5)
    ax[1].plot(t1, dr, color=LARANJA, lw=0.5)
    ax[1].axhline(0, color=CINZA, lw=0.8)
    ax[1].set_xlabel('tempo [s]'); ax[1].set_ylabel('parcela do ruído [% FE]'); ax[1].set_xlim(0, P.T_SIM)
    ax[1].set_title('(b) só o ruído (com − sem ruído)', fontsize=8.5)
    salva(fig, 'fig-14-r8-typhoon')
    with open(os.path.join(SAIDA, 'resultados_typhoon.json'), 'w', encoding='utf-8') as fh:
        json.dump(R, fh, indent=2, ensure_ascii=False)

# ======================================================================= macros LaTeX
def br(v, nd):
    return ('%.*f' % (nd, v)).replace('-', r'\textminus{}').replace('.', ',')


def cient(v):
    if v == 0:
        return '0'
    m_, e_ = ('%.1e' % v).split('e')
    return r'\ensuremath{%s\times10^{%d}}' % (m_.replace('.', '{,}'), int(e_))


c = R['completa']
mac = {
    'tyCompLin': br(c['erro_lin_subida_pcFS'], 4), 'tyCompBanda': br(c['erro_lin_banda_pcFS'], 4),
    'tyCompTot': br(c['erro_total_pcFS'], 3), 'tyCompHist': br(c['histerese_graus'], 2),
    'tyCompZM': br(c['zona_morta_reversao_graus'], 2), 'tyCompAng': br(c['erro_angulo_graus'], 2),
    'tyCompVTX': br(c['V_TX_min_V'], 2), 'tyCompDif': cient(c['dif_typhoon_python_max_uA']),
    'tyAtraso': '%d' % c['atraso_numerico_amostras'], 'tyAtrasoMs': br(c['atraso_numerico_ms'], 0),
    'tyCompAtende': 'atende' if c['atende'] else 'não atende',
}
if 'ruido_rms_ohm' in c:
    mac['tyRuidoRms'] = br(c['ruido_rms_ohm'], 1)
    mac['tyRuidoPico'] = br(c['ruido_pico_ohm'], 0)
    mac['tyRuidoInclin'] = br(c['ruido_inclinacao_dec'], 2)
    mac['tyFiltroDif'] = cient(c['dif_filtro_1f_ohm'])
for caso, nome in [('ideal', 'Ideal'), ('estatica', 'Est'), ('espectral', 'Esp')]:
    if caso in R:
        mac['ty%sTot' % nome] = br(R[caso]['erro_total_pcFS'], 3)
        mac['ty%sDif' % nome] = cient(R[caso]['dif_typhoon_python_max_uA'])
if 'r8_sem_buffer' in R:
    r8 = R['r8_sem_buffer']
    mac['tySbLin'] = br(r8['erro_lin_subida_pcFS'], 2)
    mac['tySbTot'] = br(r8['erro_total_pcFS'], 2)
    # diferenca deterministica: so faz sentido na rodada sem ruido (o ruido do Typhoon e outra realizacao)
    r8s = R.get('r8_sem_buffer_sem_ruido', r8)
    mac['tySbDif'] = cient(r8s['dif_typhoon_python_max_uA'])
    if 'ruido_pico_pcFS' in r8:
        mac['tySbRuido'] = br(r8['ruido_pico_pcFS'], 2)
destino = os.environ.get('G08_TESTE') or os.path.join(AQUI, '..', 'Fase1_Latex')
with open(os.path.join(destino, 'valores_typhoon.tex'), 'w', encoding='utf-8') as fh:
    fh.write('%% gerado por reprodutibilidade/analisa_typhoon.py a partir dos CSV do TyphoonSim\n')
    for k, v in mac.items():
        # virgula decimal como {,}: sem espaco extra tambem dentro de $...$
        fh.write(r'\newcommand{\%s}{%s}' % (k, re.sub(r'(?<!\{),(?!\})', '{,}', v)) + '\n')
print('\nfigura e macros LaTeX geradas em', destino)
