# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 01
Memoria de calculo numerica (R3), analise de alternativas (R3b) e figuras de projeto.

Uso:  python projeto.py
Saidas:
    resultados_projeto.json                     <- todos os numeros citados no relatorio
    ../relatorio/figuras/fig-0X-*.png           <- figuras (PNG, para o repositorio/slides)
    ../Fase1_Latex/figs/fig-0X-*.pdf            <- mesmas figuras (vetor, para o LaTeX)
Requer: numpy, matplotlib (schemdraw so para o esquematico).
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import parametros as P
from estilo import aplica_estilo, salva, AZUL, LARANJA, AQUA, TINTA, TINTA2, CINZA

AQUI = os.path.dirname(os.path.abspath(__file__))
aplica_estilo()
R = {}   # resultados

# =====================================================================
# 1. Deducao dos componentes (R3)
# =====================================================================
Iin_zero = P.I_ZERO / P.GANHO_XTR              # 40 uA
Iin_span = P.I_SPAN / P.GANHO_XTR              # 160 uA
R0_id  = P.VREF / Iin_zero                      # 62,5 k
Rin_id = P.VREF / Iin_span                      # 15,625 k

def io_transmissor(x, R0=P.R0, Rin=P.RIN, vref=P.VREF):
    """Corrente de laco [A] da cadeia ideal com buffer: Io = 100 (x Vref/Rin + Vref/R0)."""
    return P.GANHO_XTR * (x * vref / Rin + vref / R0)

I0_com = io_transmissor(0.0)
IFS_com = io_transmissor(1.0)
R['componentes'] = dict(
    Iin_zero_uA=Iin_zero * 1e6, Iin_span_uA=Iin_span * 1e6,
    R0_ideal_kohm=R0_id / 1e3, Rin_ideal_kohm=Rin_id / 1e3,
    R0_com_kohm=P.R0 / 1e3, Rin_com_kohm=P.RIN / 1e3,
    I_zero_com_mA=I0_com * 1e3, I_fs_com_mA=IFS_com * 1e3,
    erro_zero_pcFS=100 * (I0_com - P.I_ZERO) / P.I_SPAN,
    erro_fs_pcFS=100 * (IFS_com - (P.I_ZERO + P.I_SPAN)) / P.I_SPAN,
    sens_mA_por_grau=(IFS_com - I0_com) * 1e3 / P.THETA_FS,
    sens_ideal_uA_por_grau=P.I_SPAN / P.THETA_FS * 1e6,
    sens_pot_mV_por_grau=P.VREF / P.THETA_FS * 1e3,
)

# =====================================================================
# 2. Orcamento de corrente do transmissor a 2 fios
# =====================================================================
I_pot_nom = P.VREF / P.R_POT
I_pot_max = P.VREF / (P.R_POT * (1 - P.TOL_POT))
I_ext = I_pot_max + P.IQ_BUF
R['orcamento_corrente'] = dict(
    I_pot_nom_mA=I_pot_nom * 1e3, I_pot_max_mA=I_pot_max * 1e3,
    I_buffer_uA=P.IQ_BUF * 1e6, I_externa_total_mA=I_ext * 1e3,
    I_disponivel_mA=P.I_EXT_MAX * 1e3,
    I_minima_saida_mA=(P.IQ_XTR + I_ext) * 1e3,
    I_carga_VREF_mA=(I_pot_max + Iin_zero + Iin_span) * 1e3,
    P_pot_mW=P.VREF ** 2 / P.R_POT * 1e3,
)

# =====================================================================
# 3. Efeito de carga do cursor - justificativa do buffer (R3 / R3b)
# =====================================================================
x = np.linspace(0, 1, 1001)

def erro_carga(x, Rp, Rin):
    """Erro [fracao do span] quando o cursor alimenta Rin (terra virtual) sem buffer.
    Thevenin do cursor: Vth = x Vs, Rth = x(1-x) Rp."""
    k = x * (1 - x) * Rp
    return -x * k / (Rin + k)

opcoes = {
    'A': dict(rot=r'A: 10 k$\Omega$, $V_{REF}$=2,5 V, sem buffer', Rp=10e3, Vs=P.VREF),
    'B': dict(rot=r'B: 1 k$\Omega$, $V_{REG}$=5 V, sem buffer', Rp=1e3, Vs=P.VREG),
    'C': dict(rot=r'C: 10 k$\Omega$, $V_{REF}$=2,5 V, com buffer (adotada)', Rp=10e3, Vs=P.VREF),
}
R['alternativas'] = {}
for k, o in opcoes.items():
    Rin_o = o['Vs'] / Iin_span
    if k == 'C':
        # buffer: carga do cursor = impedancia de entrada do OPA333 (corrente de polarizacao)
        e = -P.IB_BUF * x * (1 - x) * o['Rp'] / o['Vs'] * np.ones_like(x)
    else:
        e = erro_carga(x, o['Rp'], Rin_o)
    o['e'] = e
    Ipot = o['Vs'] / o['Rp'] + (P.IQ_BUF if k == 'C' else 0.0)
    R['alternativas'][k] = dict(
        Rp_ohm=o['Rp'], Vexc_V=o['Vs'], Rin_kohm=Rin_o / 1e3,
        Rp_sobre_Rin=o['Rp'] / Rin_o,
        erro_lin_max_pcFS=100 * float(np.max(np.abs(e))),
        x_do_max=float(x[np.argmax(np.abs(e))]),
        I_externa_mA=Ipot * 1e3,
        cabe_no_orcamento=bool(Ipot < P.I_EXT_MAX),
    )

fig, ax = plt.subplots(figsize=(6.6, 3.1))
cores = {'A': LARANJA, 'B': AQUA, 'C': AZUL}
for k, o in opcoes.items():
    ax.plot(100 * x, 100 * o['e'], color=cores[k], lw=1.8, label=o['rot'])
ax.axhspan(-100 * P.ERRO_LIN_MAX, 100 * P.ERRO_LIN_MAX, color=CINZA, alpha=0.18, lw=0,
           label='faixa da especificação ($\\pm$1 % FE)')
ax.set_xlabel('posição do cursor  $x=\\theta/\\theta_{FE}$  [%]')
ax.set_ylabel('erro de linearidade [% FE]')
ax.set_xlim(0, 100)
ax.legend(loc='lower left', fontsize=7.6, frameon=True, framealpha=0.95)
kA = R['alternativas']['A']
ax.annotate(('−%.1f %% FE' % kA['erro_lin_max_pcFS']).replace('.', ','), xy=(100 * kA['x_do_max'], -kA['erro_lin_max_pcFS']),
            xytext=(78, -5.2), fontsize=8, color=TINTA2,
            arrowprops=dict(arrowstyle='-', color=TINTA2, lw=0.6))
salva(fig, 'fig-02-efeito-carga')

# =====================================================================
# 4. Compliancia do laco (R3)
# =====================================================================
I = np.linspace(P.I_ZERO, P.I_ZERO + P.I_SPAN, 50)
casos = [(0.0, 'sem cabo'), (P.R_CABO, 'cabo nominal (%.0f $\\Omega$)' % P.R_CABO),
         (P.R_CABO_MAX, 'cabo máximo (%.0f $\\Omega$)' % P.R_CABO_MAX)]
fig, ax = plt.subplots(figsize=(6.6, 2.9))
for (rc, rot), cor in zip(casos, [AQUA, AZUL, LARANJA]):
    ax.plot(I * 1e3, P.V_LOOP - I * (P.R_L + rc), color=cor, lw=1.8, label=rot)
ax.axhline(P.V_MIN_XTR, color=TINTA, lw=1.0, ls='--')
ax.text(4.2, P.V_MIN_XTR + 0.5, 'mínimo do XTR115: 7,5 V', fontsize=8, color=TINTA2)
ax.set_xlabel('corrente de laço  $I_O$  [mA]')
ax.set_ylabel('tensão no transmissor [V]')
ax.set_xlim(4, 20); ax.set_ylim(0, 25)
ax.legend(loc='lower left', fontsize=8)
salva(fig, 'fig-03-compliancia')

R['laco'] = dict(
    V_loop=P.V_LOOP, R_L=P.R_L, R_cabo=P.R_CABO,
    R_total_max_ohm=(P.V_LOOP - P.V_MIN_XTR) / (P.I_ZERO + P.I_SPAN),
    R_cabo_max_ohm=P.R_CABO_MAX,
    V_tx_min_nominal=P.V_LOOP - (P.I_ZERO + P.I_SPAN) * (P.R_L + P.R_CABO),
    V_RL_min=P.I_ZERO * P.R_L, V_RL_max=(P.I_ZERO + P.I_SPAN) * P.R_L,
    P_Q1_max_W=(P.V_LOOP - (P.I_ZERO + P.I_SPAN) * P.R_L) * (P.I_ZERO + P.I_SPAN),
)

# =====================================================================
# 5. Orcamento de erro de linearidade (componentes reais, para R3/R5)
# =====================================================================
lin = {
    'potenciometro (linearidade independente)': P.LIN_POT,
    'XTR115 (não linearidade, típ.)': P.NL_XTR,
    'efeito de carga (com buffer)': float(np.max(np.abs(opcoes['C']['e']))),
}
R['orcamento_linearidade_pcFS'] = {k: 100 * v for k, v in lin.items()}
R['orcamento_linearidade_pcFS']['soma (pior caso)'] = 100 * sum(lin.values())
R['orcamento_linearidade_pcFS']['XTR115 (não linearidade, máx. variante U)'] = 0.01

# =====================================================================
# 6. R3b - transmissao em tensao x corrente (numeros para o texto)
# =====================================================================
R_adc = 10e3        # impedancia de entrada tipica de um receptor em tensao (hipotese)
dV_terra = 0.1      # V, diferenca de potencial de terra entre campo e painel (hipotese)
R['r3b'] = dict(
    tensao_queda_cabo_pcFS=100 * P.R_CABO / (P.R_CABO + R_adc),
    tensao_terra_pcFS=100 * dV_terra / 5.0,
    corrente_queda_cabo_pcFS=0.0,
    R_adc_ohm=R_adc, dV_terra_V=dV_terra,
)

# =====================================================================
# 7. Resposta ideal esperada (gabarito Python para comparar com o TyphoonSim)
# =====================================================================
t = np.arange(0, P.T_SIM + P.DT_SINAL / 2, P.DT_SINAL)
th = P.theta_ref(t)
io = io_transmissor(th / P.THETA_FS)
np.savetxt(os.path.join(AQUI, 'gabarito_python.csv'),
           np.column_stack([t, th, io * 1e3, io * P.R_L]),
           delimiter=',', header='t_s,theta_ref_graus,I_loop_mA,V_RL_V', comments='', fmt='%.9g')

with open(os.path.join(AQUI, 'resultados_projeto.json'), 'w', encoding='utf-8') as fh:
    json.dump(R, fh, indent=2, ensure_ascii=False)

for bloco, d in R.items():
    print('\n[%s]' % bloco)
    for k, v in d.items():
        print('   %-45s %s' % (k, ('%.6g' % v) if isinstance(v, float) else v))
