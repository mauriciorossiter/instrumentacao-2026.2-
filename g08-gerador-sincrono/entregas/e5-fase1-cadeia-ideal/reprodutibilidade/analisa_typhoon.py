# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 01
Analisa os dados exportados do TyphoonSim (R4/R5): verificacao da especificacao 4-20 mA,
erro de linearidade < 1 % FE, comparacao com o gabarito Python e teste de cabo.

Uso:  python analisa_typhoon.py
Entradas:  ../typhoonsim/dados/varredura_cabo_nominal.csv  (obrigatorio)
           ../typhoonsim/dados/varredura_cabo_maximo.csv   (opcional)
           gabarito_python.csv                              (gerado por projeto.py)
Saidas:    resultados_typhoon.json e figuras fig-05, fig-06, fig-07.

Aceita tanto o CSV exportado pela API (roda_typhoon.py) quanto um CSV exportado do
Scope na interface grafica, desde que as colunas tenham os nomes das sondas.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import parametros as P
from estilo import aplica_estilo, salva, AZUL, LARANJA, AQUA, TINTA2, CINZA

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.environ.get('G08_TESTE') or os.path.join(AQUI, '..', 'typhoonsim', 'dados')
aplica_estilo()

SONDAS = ['theta_ref', 'theta_med', 'I_LOOP_mA', 'V_RL_V', 'V_TX_V', 'I_IN_uA',
          'v_cursor', 'erro_FE_pc', 'I_receptor_mA']


def carrega(nome):
    f = os.path.join(DADOS, nome + '.csv')
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
    faltam = [s for s in ['Time', 'theta_ref', 'I_LOOP_mA', 'V_RL_V', 'V_TX_V'] if s not in df.columns]
    if faltam:
        sys.exit('CSV %s sem as colunas %s (colunas lidas: %s)' % (f, faltam, list(df.columns)))
    return df


nom = carrega('varredura_cabo_nominal')
if nom is None:
    sys.exit('Falta ../typhoonsim/dados/varredura_cabo_nominal.csv - rode roda_typhoon.py '
             '(ou exporte o Scope da GUI) antes desta analise.')
mx = carrega('varredura_cabo_maximo')
gab = pd.read_csv(os.path.join(AQUI, 'gabarito_python.csv'))


def io_projeto(theta):
    """Eq. (2) do relatorio, com os resistores comerciais [mA]."""
    return 1e3 * P.GANHO_XTR * (theta / P.THETA_FS * P.VREF / P.RIN + P.VREF / P.R0)


def alinha(df, lag_max=10):
    """O TyphoonSim executa os blocos de sinal a cada DT_SINAL; cada passagem
    sinal -> circuito -> sinal acrescenta uma amostra de atraso puro (atraso numerico,
    nao dinamica do sensor, que e de ordem zero). Estima esse atraso comparando I_LOOP
    com a Eq. (2) aplicada a theta_ref, desloca as colunas medidas para alinha-las a
    theta_ref e descarta as primeiras amostras de inicializacao (antes de o sinal chegar
    ao laco, I_LOOP = 0)."""
    th_, I_ = df['theta_ref'].to_numpy(), df['I_LOOP_mA'].to_numpy()
    ref = io_projeto(th_)
    n0 = lag_max + 5
    erros = [np.max(np.abs(I_[n0 + k:] - ref[n0:len(I_) - k])) for k in range(lag_max + 1)]
    lag = int(np.argmin(erros))
    out = df.iloc[:len(df) - lag][['Time', 'theta_ref']].reset_index(drop=True)
    for c in df.columns:
        if c not in ('Time', 'theta_ref'):
            out[c] = df[c].to_numpy()[lag:]
    # erro total SEM compensar o atraso (so descartando a inicializacao), para transparencia
    sem = 100 * np.max(np.abs(I_[lag:] - (4 + 16 * th_[lag:] / P.THETA_FS))) / 16.0
    return out, lag, float(erros[lag]), float(sem)


nom, LAG, RES_LAG, ERRO_SEM_COMP = alinha(nom)
if mx is not None:
    mx, LAG_MX, _, _ = alinha(mx)

t = nom['Time'].to_numpy()
th = nom['theta_ref'].to_numpy()
I = nom['I_LOOP_mA'].to_numpy()
x = th / P.THETA_FS
I_ideal = 4.0 + 16.0 * x                      # reta ideal da especificacao

subida = t <= P.T_VARREDURA / 2 + P.DT_SINAL / 2   # tolera o arredondamento de t no pico
# ---- erro de linearidade terminal (reta pelos extremos medidos, % do span medido)
i0 = np.interp(0.0, th[subida], I[subida])
i1 = np.interp(P.THETA_FS, th[subida], I[subida])
reta_term = i0 + (i1 - i0) * x
erro_lin = 100 * (I - reta_term) / (i1 - i0)
# ---- erro total contra a reta ideal 4-20 mA
erro_tot = 100 * (I - I_ideal) / 16.0
# ---- histerese (subida x descida) - deve ser nula na cadeia ideal
grade = np.linspace(0.02, 0.98, 49) * P.THETA_FS
I_sub = np.interp(grade, th[subida], I[subida])
desc = ~subida
ordem = np.argsort(th[desc])
I_des = np.interp(grade, th[desc][ordem], I[desc][ordem])
# ---- comparacao com o gabarito Python
I_py = np.interp(t, gab['t_s'], gab['I_loop_mA'])

R = dict(
    n_pontos=int(len(t)), t_final_s=float(t[-1]),
    atraso_numerico_amostras=LAG, atraso_numerico_ms=1e3 * LAG * P.DT_SINAL,
    residuo_apos_alinhar_uA=1e3 * RES_LAG,
    erro_total_sem_compensar_atraso_pcFS=ERRO_SEM_COMP,
    I_zero_mA=float(i0), I_fs_mA=float(i1),
    V_RL_min_V=float(nom['V_RL_V'].min()), V_RL_max_V=float(nom['V_RL_V'].max()),
    V_TX_min_V=float(nom['V_TX_V'].min()),
    erro_lin_max_pcFS=float(np.max(np.abs(erro_lin))),
    erro_total_max_pcFS=float(np.max(np.abs(erro_tot))),
    histerese_max_pcFS=float(100 * np.max(np.abs(I_sub - I_des)) / 16.0),
    dif_typhoon_python_max_uA=float(1e3 * np.max(np.abs(I - I_py))),
    atende_linearidade=bool(np.max(np.abs(erro_lin)) < 100 * P.ERRO_LIN_MAX),
)
if 'theta_med' in nom:
    R['erro_angulo_max_graus'] = float(np.max(np.abs(nom['theta_med'] - th)))
if mx is not None:
    Imx = np.interp(t, mx['Time'], mx['I_LOOP_mA'])
    R['cabo_max'] = dict(R_cabo_ohm=P.R_CABO_TESTE,
                         dif_corrente_max_uA=float(1e3 * np.max(np.abs(Imx - I))),
                         V_TX_min_V=float(mx['V_TX_V'].min()))

with open(os.path.join(os.environ.get('G08_TESTE') or AQUI, 'resultados_typhoon.json'), 'w', encoding='utf-8') as fh:
    json.dump(R, fh, indent=2, ensure_ascii=False)
for k, v in R.items():
    print('%-28s %s' % (k, v))

# ======================================================================= figuras
# fig-05: resposta no tempo a varredura (referencia x medido)
fig, ax = plt.subplots(2, 1, figsize=(6.8, 4.4), sharex=True,
                       gridspec_kw=dict(height_ratios=[1.3, 1], hspace=0.12))
ax[0].plot(t, th, color=LARANJA, lw=3.2, alpha=0.55, label='referência $\\theta_{ref}$ (ideal)')
if 'theta_med' in nom:
    ax[0].plot(t, nom['theta_med'], color=AZUL, lw=1.3, label='medido $\\theta_{med}$ (TyphoonSim)')
ax[0].set_ylabel('ângulo [graus]')
ax[0].set_ylim(-150, 3800)
ax[0].legend(loc='upper right', fontsize=7.8)
ax[1].plot(t, I, color=AZUL, lw=1.4)
ax[1].axhline(4, color=CINZA, lw=0.8, ls='--'); ax[1].axhline(20, color=CINZA, lw=0.8, ls='--')
ax[1].text(19.0, 2.7, '4 mA', fontsize=7.5, color=TINTA2)
ax[1].text(0.2, 20.5, '20 mA', fontsize=7.5, color=TINTA2)
ax[1].set_ylabel('$I_{LOOP}$ [mA]')
ax[1].set_xlabel('tempo [s]')
ax[1].set_ylim(2, 22); ax[1].set_xlim(0, P.T_SIM)
salva(fig, 'fig-04-varredura-typhoon')

# fig-06: curva de transferencia + erro
fig, ax = plt.subplots(2, 1, figsize=(6.8, 4.4), sharex=True,
                       gridspec_kw=dict(height_ratios=[1.4, 1], hspace=0.12))
ax[0].plot(th, I_ideal, color=LARANJA, lw=3.2, alpha=0.55, label='reta ideal 4–20 mA')
ax[0].plot(th[subida], I[subida], color=AZUL, lw=1.3, label='TyphoonSim (subida)')
ax[0].plot(th[desc], I[desc], color=AQUA, lw=1.0, ls='--', label='TyphoonSim (descida)')
ax[0].set_ylabel('$I_{LOOP}$ [mA]')
ax[0].legend(loc='upper left', fontsize=7.8)
ax[1].axhspan(-1, 1, color=CINZA, alpha=0.18, lw=0, label='especificação $\\pm$1 % FE')
ax[1].plot(th[subida], erro_tot[subida], color=AZUL, lw=1.3, label='erro total (contra 4–20 mA ideal)')
ax[1].plot(th[subida], erro_lin[subida], color=AQUA, lw=1.3, label='erro de linearidade (terminal)')
ax[1].set_ylabel('erro [% FE]')
ax[1].set_xlabel('$\\theta_{ref}$ [graus]')
ax[1].set_ylim(-1.3, 1.3); ax[1].set_xlim(0, P.THETA_FS)
ax[1].legend(loc='lower left', fontsize=7.4, ncol=1)
salva(fig, 'fig-05-transferencia-typhoon')

# fig-07: imunidade a resistencia de cabo
if mx is not None:
    fig, ax = plt.subplots(2, 1, figsize=(6.8, 4.0), sharex=True,
                           gridspec_kw=dict(height_ratios=[1, 1], hspace=0.14))
    ax[0].plot(t, 1e3 * (Imx - I), color=AZUL, lw=1.3)
    ax[0].set_ylabel('$\\Delta I_{LOOP}$ [$\\mu$A]\n(550 $\\Omega$ − 50 $\\Omega$)')
    lim = max(1.0, 1.2 * np.max(np.abs(1e3 * (Imx - I))))
    ax[0].set_ylim(-lim, lim)
    ax[1].plot(t, nom['V_TX_V'], color=AZUL, lw=1.4, label='cabo 50 $\\Omega$')
    ax[1].plot(mx['Time'], mx['V_TX_V'], color=LARANJA, lw=1.4, label='cabo 550 $\\Omega$')
    ax[1].axhline(P.V_MIN_XTR, color='#0b0b0b', lw=0.9, ls='--')
    ax[1].text(0.2, P.V_MIN_XTR + 0.6, 'mínimo XTR115 (7,5 V)', fontsize=7.5, color=TINTA2)
    ax[1].set_ylabel('tensão no\ntransmissor [V]')
    ax[1].set_xlabel('tempo [s]')
    ax[1].set_ylim(0, 25); ax[1].set_xlim(0, P.T_SIM)
    ax[1].legend(loc='lower right', fontsize=7.8)
    salva(fig, 'fig-06-cabo-typhoon')
print('figuras geradas.')


# ======================================================================= macros LaTeX
def br(v, nd):
    """numero no formato brasileiro (virgula decimal)"""
    return ('%.*f' % (nd, v)).replace('-', r'\textminus{}').replace('.', ',')


def cient(v):
    """numero pequeno em notacao cientifica LaTeX (virgula decimal); zero exato vira '0'"""
    if v == 0:
        return '0'
    m, e = ('%.1e' % v).split('e')
    return r'\ensuremath{%s\times10^{%d}}' % (m.replace('.', '{,}'), int(e))


mac = {
    'tyNpontos': '%d' % R['n_pontos'],
    'tyIzero': br(R['I_zero_mA'], 4), 'tyIfs': br(R['I_fs_mA'], 4),
    'tyVRLmin': br(R['V_RL_min_V'], 3), 'tyVRLmax': br(R['V_RL_max_V'], 3),
    'tyVTXmin': br(R['V_TX_min_V'], 2),
    'tyErroLin': cient(R['erro_lin_max_pcFS']),
    'tyErroTot': br(R['erro_total_max_pcFS'], 3),
    'tyHist': cient(R['histerese_max_pcFS']),
    'tyDifPy': br(R['dif_typhoon_python_max_uA'], 3),
    'tyErroAng': br(R.get('erro_angulo_max_graus', float('nan')), 1),
    'tyAtende': 'atende' if R['atende_linearidade'] else 'não atende',
    'tyAtraso': '%d' % R['atraso_numerico_amostras'],
    'tyAtrasoMs': br(R['atraso_numerico_ms'], 0),
    'tyResiduo': br(R['residuo_apos_alinhar_uA'], 4),
    'tyErroSemComp': br(R['erro_total_sem_compensar_atraso_pcFS'], 3),
}
if 'cabo_max' in R:
    mac['tyCaboDif'] = br(R['cabo_max']['dif_corrente_max_uA'], 3)
    mac['tyCaboVTX'] = br(R['cabo_max']['V_TX_min_V'], 2)
destino = os.environ.get('G08_TESTE') or os.path.join(AQUI, '..', 'Fase1_Latex')
with open(os.path.join(destino, 'valores_typhoon.tex'), 'w', encoding='utf-8') as fh:
    fh.write('%% gerado por reprodutibilidade/analisa_typhoon.py a partir dos CSV do TyphoonSim\n')
    for k, v in mac.items():
        fh.write(r'\newcommand{\%s}{%s}' % (k, v) + '\n')
print('macros LaTeX em', os.path.join(destino, 'valores_typhoon.tex'))
