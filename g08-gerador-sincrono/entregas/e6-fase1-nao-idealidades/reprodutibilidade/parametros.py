# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02 (nao idealidades)
Potenciometro (Cap. 7.1.1/7.1.2) + laco de corrente 4-20 mA (Cap. 6.4)

Parametros unicos da cadeia, importados por todos os scripts
(camadas.py, monta_modelo.py, roda_typhoon.py, analisa_typhoon.py).
Os blocos ate "sinal de referencia" sao os da Entrega 01, sem alteracao (o circuito
nao muda - requisito R10); o bloco "Entrega 02" no fim acrescenta as camadas.
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


# ============================================================ Entrega 02 - camadas nao ideais
# R6 - camada estatica: resolucao (fio enrolado) + histerese por folga mecanica (backlash)
#   resolucao 0,020 % e backlash 1,0 graus: datasheet Bourns 3590 (REV. 12/20)
N_PASSOS     = int(round(1.0 / RES_POT))      # 5000 posicoes discretas do cursor ao longo da trilha
PASSO_GRAUS  = RES_POT * THETA_FS             # 0,72 grau por passo de resolucao
FOLGA_GRAUS  = BACKLASH                       # 1,0 grau de folga entre eixo e cursor
FASE_ESPIRA  = 0.25    # posicao da 1a espira em relacao ao zero eletrico, em passos (hipotese).
                       # Com 0,25 nenhuma amostra da varredura (0,36 grau/ms) cai exatamente numa
                       # fronteira entre espiras, o que evita empate numerico entre Python e C.

# R7 - camada dinamica: ordem zero (sensor) + polos da eletronica, so para quantificar
GBW_BUF      = 350e3   # Hz, OPA333 GBW (SBOS351E); como seguidor, f_c ~ GBW
CIN_BUF      = 4e-12   # F, OPA333 capacitancia de entrada de modo comum (SBOS351E)
BW_XTR       = 380e3   # Hz, XTR115 small-signal bandwidth (SBOS124C)
RPM_MAX_POT  = 200.0   # rpm, Bourns 3590 (RPM operating max.)

# R8 - camada espectral: ruido de contato do cursor (ENR), espectro 1/f
#   ENR = resistencia parasita transitoria entre cursor e trilha com o eixo girando;
#   ensaiada com 1 mA no cursor para 3 k < Rt <= 200 k (Bourns Trimpot Catalog,
#   Applications/Processing Guide, p. 150).
I_TESTE_ENR  = 1e-3    # A, corrente de ensaio do ENR para Rt = 10 k
I_CURSOR     = IB_BUF  # A, corrente que de fato passa pelo contato (entrada do OPA333, max. 25 C)
SEMENTE      = 20261005  # semente do gerador pseudoaleatorio (LCG), igual no Python e no C do TyphoonSim

# R8 - demonstracao no TyphoonSim com o potenciometro "eletrico" (resistores variaveis) e
# SEM buffer: o efeito de carga e o ruido de contato aparecem no proprio circuito
R_MIN_POT    = 10.0    # ohm, resistencia minima absoluta: 1 ohm ou 0,1 % de Rt (a maior) - Bourns 3590
R_C0         = ENR_POT + R_MIN_POT  # ohm, resistencia de contato de base (HIPOTESE: so para que
                       # R_c = R_C0 + dR_c nunca chegue a zero no resistor variavel do Typhoon)
