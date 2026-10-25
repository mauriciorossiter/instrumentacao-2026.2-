# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 01: caracterizacao da planta no dominio de origem
Gerador sincrono ligado a barramento infinito (SMIB), modelo classico (swing equation):

    (2H/ws) d2(delta)/dt2 = Pm - Pmax*sin(delta) - D*d(delta)/dt ,   Pmax = E'V/X

Parametros unicos, importados por modelo.py e caracterizacao.py. Sao os da Tabela 1
da Atividade 01, mantidos sem alteracao em todas as entregas do G08; a fonte de cada
valor esta ao lado. Convencao "Forma A": velocidades em rad/s eletricos, potencias em pu.
"""
import math

# ------------------------------------------------------------------ rede
F_REDE  = 60.0                 # Hz, frequencia nominal do sistema interligado brasileiro
W_S     = 2*math.pi*F_REDE     # rad/s eletricos, velocidade sincrona (376,99 rad/s)
V_BAR   = 1.00                 # pu, tensao do barramento infinito (referencia angular, 0 grau)

# ------------------------------------------------------------------ maquina e ligacao
H       = 5.0    # s, constante de inercia. Faixa tipica de turbogeradores: 2,5-6 s (2 polos)
                 #    e 4-10 s (4 polos) [Kundur 1994, Tab. 3.2]
E_LINHA = 1.20   # pu, tensao interna transitoria E' do modelo classico (maquina sobre-excitada;
                 #    a coerencia com o ponto de operacao e conferida em modelo.ponto_de_operacao)
X_TOT   = 0.60   # pu, reatancia total X = X'd + Xe. X'd de turbogeradores: 0,15-0,40 pu
                 #    [Kundur 1994, Tab. 4.2]; o restante e' transformador elevador + linha
D       = 0.01   # pu/(rad/s), amortecimento equivalente (Forma A) = D*ws = 3,77 pu/(pu de vel.).
                 #    Escolha da equipe: resulta zeta = 2,3 %, modo local pouco amortecido,
                 #    tipico de maquina sem estabilizador (PSS) [Kundur 1994, Cap. 12]
PM0     = 0.80   # pu, potencia mecanica no ponto de operacao (80 % da base)

P_MAX   = E_LINHA*V_BAR/X_TOT  # pu, potencia maxima transferivel = 2,00 pu

# ------------------------------------------------------------------ solucionador (R3)
PASSO   = 1e-3   # s, passo fixo do Runge-Kutta classico de 4a ordem (RK4)

# ------------------------------------------------------------------ ensaios (R3)
DPM_DEGRAU   = 0.10    # pu, ensaio (a): degrau de Pm a partir do equilibrio (0,80 -> 0,90 pu)
DELTA_CI_GR  = 60.0    # graus, ensaio (b): condicao inicial delta(0), com Delta_omega(0) = 0
T_INICIO_FALTA = 0.10  # s, ensaio (c): instante de aplicacao da falta (Pe = 0 durante a falta)
DURACOES_FALTA = (0.20, 0.27, 0.29)   # s, duracoes da falta no ensaio (c)

# ------------------------------------------------------------------ sensibilidade (R5)
NIVEIS_H = (1.0, 2.5, 5.0, 10.0, 25.0)            # s       (x0,2  x0,5  nominal  x2  x5)
NIVEIS_D = (-0.005, 0.0, 0.01, 0.1, 0.441, 1.0)   # pu/(rad/s); 0,441 ~ amortecimento critico
NIVEIS_X = (0.30, 0.45, 0.60, 0.90, 1.20, 1.40)   # pu      (x0,5 ... x2,33)
NIVEIS_DPM = (0.01, 0.10, 0.30, 0.60)             # pu, amplitudes do degrau ("e se...?")
CI_DOMINIO_GR = (150.0, 160.0)                    # graus, condicoes iniciais dos dois lados de delta_u

# ------------------------------------------------------------------ TyphoonSim (segunda ferramenta)
TY_PASSO        = PASSO   # s, taxa de execucao dos blocos de sinal nativos (1 ms)
TY_T_DEGRAU     = 1.0     # s, instante do degrau de Pm no TyphoonSim (antes dele, equilibrio)
TY_T_POS_DEGRAU = 60.0    # s simulados depois do degrau, ensaio (a)
TY_T_CI         = 30.0    # s, ensaio (b)
TY_T_FALTA      = 2.6     # s, ensaio (c)
# duracoes de falta: as do ensaio (c) e um par que cerca o t_cr do esquema discreto (h = 1 ms)
TY_DURACOES_FALTA = (0.20, 0.27, 0.29, 0.287, 0.288)
