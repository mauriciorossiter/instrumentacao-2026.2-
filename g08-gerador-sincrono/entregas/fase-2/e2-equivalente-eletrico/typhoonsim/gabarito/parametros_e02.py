# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: equivalente eletrico da swing equation.

Fonte unica das escalas e dos valores do circuito. Os parametros fisicos NAO sao redefinidos:
vem de ../../e1-caracterizacao/simulacao/parametros.py (os mesmos da Atividade 01 e da E01).

Analogia forca-tensao (a convencao do curso: J->L, B->R, K->1/C):
    esforco  potencia P [pu]          <->  tensao v [V]         v = KV * P
    fluxo    Delta_omega [rad/s]      <->  corrente i [A]       i = KI * Delta_omega
    posicao  delta - delta0 [rad]     <->  carga q [C]          q = KI * (delta - delta0)
    inercia  M = 2H/ws                <->  indutor L = KV*M/KI
    amortec. D                        <->  resistor R = KV*D/KI
    mola sincronizante linear Ks      <->  capacitor C = KI/(KV*Ks)
    resto nao linear Pmax*sen(d) - Ks*(d-d0)  <->  fonte de tensao controlada por sinal
    entrada  Pm                       <->  fonte de tensao V_m = KV*Pm

Malha unica (KVL):  V_m = R i + L di/dt + v_C + v_nl,   C dv_C/dt = i,
                    v_nl = KV*Pmax(t)*sen(delta0 + v_C/(KV*Ks)) - v_C .
Dividindo por KV e trocando i = KI*Delta_omega: (2H/ws) d2delta/dt2 = Pm - Pmax sen(delta) - D d(delta)/dt.
Escala de tempo 1:1 (1 s simulado = 1 s da planta).
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E01 = os.path.normpath(os.path.join(AQUI, '..', '..', '..', 'e1-caracterizacao', 'simulacao'))
if E01 not in sys.path:
    sys.path.append(E01)          # no fim: o estilo.py daqui tem prioridade sobre o da E01
sys.dont_write_bytecode = True

from parametros import (F_REDE, W_S, H, E_LINHA, V_BAR, X_TOT, D, PM0, P_MAX, PASSO,  # noqa: E402
                        DPM_DEGRAU, DELTA_CI_GR, T_INICIO_FALTA, DURACOES_FALTA)

# ------------------------------------------------------------------ escalas (R1c)
KV = 2.5     # V/pu  : todas as tensoes do circuito ficam em +-10 V (faixa dos canais analogicos do HIL
             #         e da entrada da cadeia de instrumentacao) nos tres ensaios: o pior caso e' v_C na
             #         falta de 270 ms (8,0 V). So' na sela (156,4 graus, fronteira de estabilidade) v_C
             #         chega a 10,6 V. Pm0 = 2,0 V, degrau = 0,25 V, Pmax = 5,0 V
KI = 0.10    # A/(rad/s): o maior |Delta_omega| do dominio estavel (11,69 rad/s, na separatriz)
             #         vira 1,17 A; nos ensaios fica abaixo de 1,04 A
KT = 1.0     # escala de tempo 1:1: a oscilacao de 1,32 Hz e' visivel ao vivo no SCADA e o VHIL roda
             #         em tempo real; a cadeia da Fase 1 foi projetada para essa dinamica

# ------------------------------------------------------------------ ponto de operacao
DELTA0 = math.asin(PM0/P_MAX)           # rad, 23,578 graus
KS = P_MAX*math.cos(DELTA0)             # pu/rad, coeficiente de potencia sincronizante (1,8330)
M = 2.0*H/W_S                           # pu.s^2/rad, "massa" da swing equation (0,026526)

# ------------------------------------------------------------------ elementos do circuito (R1d)
L_EQ = KV*M/KI                          # H   : 0,66315 H
R_EQ = KV*D/KI                          # ohm : 0,25 ohm
C_EQ = KI/(KV*KS)                       # F   : 21,822 mF
V_M0 = KV*PM0                           # V   : 2,0 V (Pm0)
V_DEGRAU = KV*DPM_DEGRAU                # V   : 0,25 V (degrau de 0,1 pu)
KV_DELTA = KV*KS                        # V/rad: v_C = KV*Ks*(delta - delta0) = 4,583 V/rad = 0,080 V/grau

# ------------------------------------------------------------------ TyphoonSim (R2)
TS_SP = 20e-6    # s, taxa de execucao dos blocos de sinal que calculam v_nl (medicao de v_C ->
                 #    seno -> fonte controlada). O erro cai linearmente com TS_SP; na falta de 270 ms
                 #    (o ensaio mais sensivel, perto da separatriz) a maior diferenca de delta contra a
                 #    E01 e' 1,4 graus com 100 us e ~0,3 grau com 20 us (equivalente.py, 'passo_sinal')
TS_POT = 'auto'  # passo do estagio de potencia (definido pelo compilador)
PASSO_CIRC = PASSO   # s, passo do RK4 do circuito continuo (o mesmo da E01)


def elementos(H_=H, D_=D, Pm0_=PM0, Pmax_=P_MAX):
    """R, L, C e Ks para outro conjunto de parametros fisicos (usado na sensibilidade, R4).
    O capacitor carrega o Ks do ponto de operacao; se Pmax mudar com o circuito ja montado,
    a fonte controlada absorve a diferenca (a equacao continua exata)."""
    d0 = math.asin(Pm0_/Pmax_)
    ks = Pmax_*math.cos(d0)
    return dict(L=KV*(2*H_/W_S)/KI, R=KV*D_/KI, C=KI/(KV*ks), Ks=ks, delta0=d0)
