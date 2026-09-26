# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 01 (cadeia ideal)
Potenciometro (Cap. 7.1.1/7.1.2) + laco de corrente 4-20 mA (Cap. 6.4)

Parametros unicos da cadeia, importados por todos os scripts
(projeto.py, monta_modelo.py, roda_typhoon.py, analisa_typhoon.py).
Toda grandeza com fonte externa traz a referencia ao lado.
"""

# ------------------------------------------------------------ sensor (R1)
# Bourns 3590S-2-103L - potenciometro de precisao, 10 voltas, fio enrolado
# Datasheet "3590 - Precision Potentiometer", REV. 12/20 (bourns.com)
R_POT      = 10e3      # ohm, resistencia total nominal
TOL_POT    = 0.05      # +-5 % (total resistance tolerance)
LIN_POT    = 0.0025    # +-0,25 % (independent linearity)  -> usado so no orcamento de erro
THETA_FS   = 3600.0    # graus, angulo eletrico efetivo (3600 +10/-0)
RES_POT    = 0.00020   # 0,020 % (resolucao tabelada p/ 10 kohm) -> Entrega 02
BACKLASH   = 1.0       # graus, backlash maximo                  -> Entrega 02
ENR_POT    = 100.0     # ohm, ruido ENR maximo                    -> Entrega 02
P_POT_40C  = 2.0       # W a +40 C

# ------------------------------------------------------------ transmissor
# TI XTR115 (SBOS124C, rev. jan/2026): Io = 100 * Iin ; VREF = 2,5 V ; VREG = 5 V
GANHO_XTR  = 100.0     # A/A
VREF       = 2.5       # V
VREG       = 5.0       # V
V_MIN_XTR  = 7.5       # V, tensao minima de operacao (V+ ate IO)
IQ_XTR     = 200e-6    # A, corrente quiescente tipica
NL_XTR     = 0.00003   # 0,003 % tipica (0,01 % max, variante U)
SPAN_XTR   = 0.0005    # 0,05 % tipico de erro de span
I_EXT_MAX  = 3.7e-3    # A, corrente disponivel p/ circuitos externos (sec. 8.1.2)

# buffer do cursor - TI OPA333 (SBOS351E, dez/2015)
IQ_BUF     = 17e-6     # A
VOS_BUF    = 10e-6     # V, maximo
IB_BUF     = 200e-12   # A, maximo a 25 C

# ------------------------------------------------------------ especificacao (R2)
I_ZERO     = 4e-3      # A
I_SPAN     = 16e-3     # A  (4-20 mA)
ERRO_LIN_MAX = 0.01    # 1 % do fundo de escala (familia C, G08)

# ------------------------------------------------------------ projeto (R3)
# valores ideais (dedução em projeto.py) e comerciais (serie E192, 0,1 %)
R0_IDEAL   = VREF / (I_ZERO / GANHO_XTR)          # 62,5 kohm
RIN_IDEAL  = VREF / (I_SPAN / GANHO_XTR)          # 15,625 kohm
R0         = 62.6e3    # ohm, E192 0,1 %
RIN        = 15.6e3    # ohm, E192 0,1 %

# ------------------------------------------------------------ laco / receptor
V_LOOP     = 24.0      # V, fonte do laco (valor nominal do datasheet XTR115)
R_L        = 250.0     # ohm, resistor de carga do receptor (-> 1-5 V)
R_CABO     = 50.0      # ohm, hipotese de projeto (ida+volta), declarada no relatorio
R_CABO_MAX = (V_LOOP - V_MIN_XTR) / (I_ZERO + I_SPAN) - R_L   # 575 ohm (limite teorico a 20 mA)
R_CABO_TESTE = 550.0   # ohm, cabo longo usado no ensaio de imunidade (margem sobre o limite)

# ------------------------------------------------------------ sinal de referencia
# varredura triangular 0 -> 3600 -> 0 graus (subida e descida)
T_VARREDURA = 20.0     # s, periodo completo (10 s subindo, 10 s descendo)
T_SIM       = 20.0     # s
DT_SINAL    = 1e-3     # s, taxa de execucao dos blocos de sinal no TyphoonSim


def theta_ref(t):
    """Angulo de referencia [graus] - varredura triangular de um periodo."""
    import numpy as np
    t = np.asarray(t, dtype=float)
    meio = T_VARREDURA / 2.0
    return np.where(t <= meio, THETA_FS * t / meio,
                    np.clip(THETA_FS * (T_VARREDURA - t) / meio, 0.0, THETA_FS))
