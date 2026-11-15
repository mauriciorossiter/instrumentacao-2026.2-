# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entregas 03 e 04: instrumentacao (malha aberta) e controle (malha fechada)
sobre o equivalente eletrico da E02.

Fonte unica dos valores novos. A planta NAO e' redefinida: as escalas e os elementos do circuito vem de
../../e2-equivalente-eletrico/simulacao/parametros_e02.py, que por sua vez importa os parametros fisicos
da E01 (../../e1-caracterizacao/simulacao/parametros.py).

Grandeza a medir (Anexo da E03, G08): tensao eficaz e frequencia nos terminais do gerador.
Tecnologia: transformador de potencial (TP) com conversao de valor eficaz.

O que entra de novo, e por que:
  * Divisao de X = X'd + Xe (0,30 + 0,30 pu): a E01 so' usava a soma. A tensao terminal depende de onde
    os terminais estao na reatancia: Vt = (X'd*V + Xe*E'∠δ)/X.
  * Local da falta: barra de AT do transformador elevador (inicio da linha). E' a mesma falta franca da
    E01 (Pe = 0); o que muda e' que agora se sabe a tensao terminal durante a falta: Vt = XT/(X'd+XT)*E'.
  * E04: o campo vira atuador. T'd0*dE'/dt = Efd - E' (reacao de armadura desprezada, K4 = 0), de modo
    que, com Efd constante (malha aberta, E03), a planta e' exatamente a da E02 (E' = 1,2 pu).
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E02 = os.path.normpath(os.path.join(AQUI, '..', '..', '..', 'e2-equivalente-eletrico', 'typhoonsim', 'gabarito'))
if E02 not in sys.path:
    sys.path.append(E02)          # no fim: estilo.py daqui tem prioridade
sys.dont_write_bytecode = True

import parametros_e02 as P2                                                     # noqa: E402
from parametros_e02 import (KV, KI, KV_DELTA, L_EQ, C_EQ, TS_SP, DELTA0, KS, M,   # noqa: E402,F401
                            F_REDE, W_S, H, E_LINHA, V_BAR, X_TOT, D, PM0, P_MAX, DPM_DEGRAU,
                            DELTA_CI_GR, T_INICIO_FALTA, E01)

# ======================================================================== rede (divisao de X)
XDP = 0.30        # pu, reatancia transitoria de eixo direto X'd. Faixa de turbogeradores 0,15-0,40 pu
                  #     [Kundur 1994, Tab. 4.2]; adotado o meio da faixa
XT = 0.10         # pu, transformador elevador (Xcc tipica 8-12 % na base da maquina)
XL = 0.20         # pu, linha de transmissao
XE = XT + XL      # pu, 0,30 pu: X'd + Xe = 0,60 pu = X da E01 (conferido abaixo)
assert abs(XDP + XE - X_TOT) < 1e-12

# ======================================================================== bases e TP
S_BASE = 100e6               # VA (a mesma base ilustrativa da E01)
V_BASE = 13.8e3              # V eficaz de linha nos terminais (tensao nominal de gerador de 100 MVA)
RTP = 13800.0/115.0          # relacao do TP: 13,8 kV : 115 V (secundario padrao 115 V), RTP = 120
K_DIV = 2.0/115.0            # condicionamento: 115 V -> 2,0 V eficazes (1 pu = 2,0 V na entrada do AD637)
V_PU_VD = V_BASE/RTP*K_DIV   # V eficazes na entrada do conversor por pu de tensao terminal (2,0 V/pu)


def terminal(delta, Ep, falta=0.0):
    """Fasor da tensao terminal (pu, referencia = barramento infinito).
    Normal:  Vt = (X'd*V + Xe*E'∠δ)/(X'd + Xe).  Falta na barra de AT: Vth = 0, Xth = XT."""
    vth = V_BAR*(1.0 - falta)
    xth = XE*(1.0 - falta) + XT*falta
    den = XDP + xth
    re = (XDP*vth + xth*Ep*math.cos(delta))/den
    im = xth*Ep*math.sin(delta)/den
    return re, im


VT0_RE, VT0_IM = terminal(DELTA0, E_LINHA)
VT0 = math.hypot(VT0_RE, VT0_IM)          # 1,0770 pu (14,86 kV)
TH0 = math.atan2(VT0_IM, VT0_RE)          # 12,88 graus

# sensibilidades da tensao terminal no ponto de operacao (constantes de Heffron-Phillips)
_a, _b = XDP/X_TOT*V_BAR, XE/X_TOT*E_LINHA
K5 = -_a*_b*math.sin(DELTA0)/VT0                          # dVt/dδ  = -0,1114 pu/rad (negativo!)
K6 = (XE/X_TOT)*(_b + _a*math.cos(DELTA0))/VT0            # dVt/dE' =  0,4913 pu/pu
K2 = V_BAR*math.sin(DELTA0)/X_TOT                         # dPe/dE' =  0,6667 pu/pu
DTH_DDELTA = (_b*_b + _a*_b*math.cos(DELTA0))/VT0**2      # dθt/dδ  =  0,5474: f terminal = 60 + 0,547*Δω/2π

# ======================================================================== campo (E04)
TDO = 6.0         # s, constante de tempo transitoria de circuito aberto T'd0 [Kundur 1994, Tab. 4.2: 3-10 s]
EFD0 = E_LINHA    # pu, tensao de campo de regime (sem reacao de armadura, Efd = E' em regime)
EFD_MAX = 6.0     # pu, teto da excitatriz estatica (5 x Efd0) [IEEE 421.5-2016, ST1A, dados de exemplo: VRmax 6,43 pu]
EFD_MIN = -4.8    # pu, teto negativo (-4 x Efd0)

# ======================================================================== taxas
TS_M = 100e-6     # s, taxa da cadeia de medicao (ADC a 10 kS/s, 166,7 amostras por ciclo) e do controle
N_SUB = int(round(TS_M/TS_SP))   # 5 subpassos da planta (20 us, o mesmo da E02) por amostra de medicao
assert abs(N_SUB*TS_SP - TS_M) < 1e-15

# ======================================================================== cadeia REAL (valores padrao)
# Cada caracteristica e' um bloco identificavel, ajustavel pelo SCADA. 'neutro' e' o valor que a desliga.
CAV_UF = 2.2                     # uF, capacitor de media do AD637 (valor comercial)
TAU_POR_UF = 25e-3               # s/uF, constante de tempo de media do AD637 [AD637 Rev. L, Tab. 1, p. 4]
# O AD637 calcula o valor eficaz de forma IMPLICITA: Vo = media(Vin²/Vo). Para pequenas variacoes a constante
# de tempo efetiva e' tau/2 e a ondulacao de pico e' 50/(6,3*tau*f) % da leitura [AD637 Rev. L, Eq. 1, p. 14].
REAL = dict(
    eps_tp=0.30,                 # %, erro de relacao do TP (limite da classe 0,3: TCF 0,997-1,003, IEEE C57.13)
    tau_rms=TAU_POR_UF*CAV_UF,   # s, constante de media do AD637 (55 ms com CAV = 2,2 uF)
    nbits=12,                    # bits do ADC (0 a 4,096 V -> LSB de 1 mV = 0,05 % de 2 V)
    sigma=5e-3,                  # V eficazes de ruido branco (banda de 5 kHz) somado ao sinal de 2 V
    n_cic=4.0,                   # ciclos da media exponencial do frequencimetro
    fclk=1e6,                    # Hz, relogio do contador de periodo (captura do temporizador)
)
NEUTRO = dict(eps_tp=0.0, tau_rms=0.0, nbits=0, sigma=0.0, n_cic=0.0, fclk=0.0)   # 0 = desligada
ROTULO = dict(eps_tp='erro de relação do TP', tau_rms='média do conversor (AD637)', nbits='resolução do ADC',
              sigma='ruído no secundário', n_cic='média do frequencímetro', fclk='relógio do contador')
UNID = dict(eps_tp='%', tau_rms='s', nbits='bits', sigma='V', n_cic='ciclos', fclk='Hz')

# projeto fixo dos circuitos auxiliares (R3 da E03)
FC_SK = 10.0                     # Hz, filtro de saida Sallen-Key 2a ordem (Butterworth) do AD637
Q_SK = 1.0/math.sqrt(2.0)
VREF_ADC = 4.096                 # V, fundo de escala do ADC (0 a 4,096 V; 1 pu = 2,0 V -> 2,05 pu de faixa)
FC_PF = 150.0                    # Hz, pre-filtro passa-baixas 2a ordem do frequencimetro
Q_PF = 1.0/math.sqrt(2.0)
HIST = 0.020                     # V, histerese do comparador (+-20 mV em 2,83 V de pico)

# ======================================================================== ensaios
T_EV = 1.0                       # s, instante do evento (degrau de Pm, degrau de Vref, inicio da falta)
DUR_FALTA = 0.20                 # s, falta do ensaio (c): a de 200 ms da E01
DVREF = 0.02                     # pu, degrau de referencia de tensao (E04): +2 % de 1 pu
SEMENTE = 8                      # semente do ruido (gabarito Python; o Random Source do TyphoonSim nao tem)
