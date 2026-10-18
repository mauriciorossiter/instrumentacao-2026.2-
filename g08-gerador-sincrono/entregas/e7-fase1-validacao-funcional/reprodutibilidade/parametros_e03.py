# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03 (validacao funcional, video)

Os parametros da Entrega 01 e da Entrega 02 sao importados SEM ALTERACAO de
../../e6-fase1-nao-idealidades/reprodutibilidade/parametros.py ("os projetos das Entregas
01 e 02 sao usados como estao"). Este arquivo so acrescenta o bloco da Entrega 03: os
parametros dos tres ensaios-padrao (R11), que tambem sao os valores iniciais do painel SCADA.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_E02 = os.path.abspath(os.path.join(AQUI, '..', '..', 'e6-fase1-nao-idealidades', 'reprodutibilidade'))
if DIR_E02 not in sys.path:
    sys.path.insert(0, DIR_E02)

from parametros import *          # noqa: F401,F403  (E01 + E02, sem alteracao)
import parametros as P            # noqa: E402

# ============================================================ Entrega 03 - ensaios-padrao (R11)
# Seletor de ensaio (SCADA Input 'ens_ensaio'):
ENSAIOS = {
    0: 'varredura da E01 (0 -> 3600 -> 0 graus em 20 s)',
    1: '(a) degrau a partir do repouso',
    2: '(b) condicao inicial nao nula, sem novo estimulo',
    3: '(c) pulso breve com retorno ao valor original',
}
ENSAIO_PADRAO = 1

# Base comum: o mesmo sinal de referencia da E01 (R2), angulo do eixo em graus, dentro da faixa
# 0-3600 graus e na mesma grade de 1 ms. Os ensaios mudam so a forma no tempo.
THETA_BASE   = 0.0       # graus, repouso dos ensaios (a) e (c) (inicio da faixa, como a varredura)
AMPLITUDE    = 1800.0    # graus, amplitude do degrau e do pulso: 50 % FE -> 12 mA
THETA0       = 1800.0    # graus, referencia constante do ensaio (b) (meio da faixa)
DELTA0       = 5.0       # graus, deslocamento do cursor em relacao ao eixo imposto como condicao
                         # inicial no ensaio (b). A folga so admite 0 <= desvio <= b = 1 grau, entao
                         # a resposta mostra quanto dessa condicao inicial o sensor consegue guardar.
LARGURA      = 0.5       # s, duracao do pulso do ensaio (c)

# Disparo. Ao vivo, o ensaio dispara pelo SCADA (chave 'ens_disparo'). Para o gabarito e a
# rodada offline (sem operador), o mesmo disparo vem de um degrau no instante 'ens_t_auto'.
T_DISPARO    = 1.0       # s, instante do disparo automatico (gabarito e roda_ensaios.py)
T_AUTO_NUNCA = 1.0e9     # s, valor de 'ens_t_auto' no painel: o disparo automatico nunca acontece
T_JANELA     = 3.0       # s, duracao de cada ensaio no gabarito (3001 amostras de 1 ms)

# Camadas (SCADA Inputs, 1 = liga / 0 = desliga) - valores iniciais do painel: todas ligadas
CAMADAS_PADRAO = dict(folga_liga=1, res_liga=1, ruido_liga=1)

# Tempo de simulacao com o painel SCADA (o ensaio ao vivo precisa de folga para o operador).
# A varredura da E01 (ensaio 0) usa o relogio: so acontece nos primeiros 20 s.
T_SIM_SCADA  = 600.0     # s
# Rodada offline (roda_ensaios.py): mesma janela do gabarito
T_SIM_ENSAIO = T_JANELA

# Atraso numerico ja medido na E01: theta_ref -> I_LOOP passa duas vezes pela fronteira
# sinal/circuito, cada uma soma uma amostra de 1 ms (as 2 primeiras amostras de I_LOOP sao nulas).
ATRASO_AMOSTRAS = 2
