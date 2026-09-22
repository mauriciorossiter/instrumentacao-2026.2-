# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Sistema 7: Gerador Sincrono (Swing Equation)
Topico atribuido: LIMIAR
Geracao de dados brutos (Secao 3.3) -- protocolo de sinal da Orientacao
"Geracao de dados - Caracteristicas estaticas", linha "Limiar":

  Sinal de excitacao:      pequenos incrementos crescentes de x, a partir
                           de um ponto de repouso constante
  O que precisa aparecer:  sequencia de incrementos pequenos e conhecidos,
                           com leitura registrada apos cada incremento

Reusa a MESMA funcao matematica da caracteristica estatica ja construida e
validada em ../Latex/caracterizacao_limiar.py e no circuito equivalente do
TyphoonSim (../Latex/typhoonsim/), com erro cruzado TyphoonSim x Python
< 0,31% (relatorio, Secao 6): o limiar deste sistema instrumentado nasce da
quantizacao do conversor A/D do canal de delta somada ao piso de ruido do
canal (relatorio, Secoes 5.2 e 5.6).

  x_referencia  = delta - delta0                          [graus]  (sem distorcao)
  y_instrumento = q * floor( (x_referencia + ruido) / q )  [graus]  (com ruido)

ATENCAO -- ESTE SCRIPT E' GABARITO, NAO PARTE DA ENTREGA:
Contém os parametros numericos internos da funcao geradora (quantum,
sigma do ruido). A orientacao pede explicitamente que esses parametros
NAO precisam ser revelados no material que acompanha os dados (para que
o exercicio de analise das Secoes 3.1/3.2 seja resolvido a partir dos
dados, e nao da resposta). Mantenha este arquivo apenas no repositorio de
trabalho da equipe; a pasta dados/ (CSV + metadados) e' o que deve
efetivamente ser entregue.

Gera:
  dados/Equipe_08_Limiar.csv
  figs/dados_limiar_visualizacao.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_DADOS = os.path.join(AQUI, 'dados')
DIR_FIGS = os.path.join(AQUI, 'figs')
os.makedirs(DIR_DADOS, exist_ok=True)
os.makedirs(DIR_FIGS, exist_ok=True)

SEED = 20260903                                  # semente fixa: dataset reprodutivel
RNG = np.random.default_rng(SEED)

# --------------------------------------------------------------------------
# Canal instrumentado -- identico ao caracterizado em ../Latex/caracterizacao_limiar.py
# (Ensaios L2/L3/L6 do relatorio principal), reduzido aqui ao mecanismo que
# a Orientacao pede para exercitar: quantizacao (12 bits, FS = 360 graus,
# pior caso -- delta0 sobre uma transicao de codigo) + ruido do canal.
# --------------------------------------------------------------------------
FS_DEG = 360.0
NBITS = 12
Q_DEG = FS_DEG / 2**NBITS                        # quantum do conversor
SIGMA_DEG = 0.02                                 # piso de ruido representativo (relatorio, Sec. 7)
FS_AMOSTRAGEM = 60.0                              # amostras/s (taxa de reporte tipica de PMU)

# --------------------------------------------------------------------------
# Protocolo de excitacao da equipe (Limiar): pequenos incrementos crescentes
# de x a partir de um ponto de repouso constante (x = 0, i.e. delta = delta0).
# Repete-se a mesma varredura em multiplas rodadas independentes -- cada uma
# volta ao repouso antes de recomecar -- para que o exercicio de analise
# disponha de varias realizacoes de ruido em cada x, sem que a equipe
# aplique qualquer promediacao antes de entregar (isso e' pre-processamento,
# proibido pela Orientacao).
# --------------------------------------------------------------------------
DELTA_X = Q_DEG / 10.0                           # incremento pequeno e conhecido
N_STEPS = 100                                     # passos por varredura (0 a 10 quanta)
M_SWEEPS = 30                                     # varreduras independentes


def quantiza(x_deg):
    """Quantizador uniforme, pior caso (x=0 exatamente sobre uma transicao)."""
    return Q_DEG * np.floor(x_deg / Q_DEG)


linhas = []
idx_global = 0
for sweep in range(M_SWEEPS):
    for k in range(N_STEPS + 1):
        x_ref = k * DELTA_X                       # sinal de referencia, SEM distorcao
        ruido_amostra = RNG.normal(0.0, SIGMA_DEG)
        y_inst = float(quantiza(x_ref + ruido_amostra))   # leitura do instrumento, COM ruido
        linhas.append((idx_global / FS_AMOSTRAGEM, float(x_ref), y_inst))
        idx_global += 1

df = pd.DataFrame(linhas, columns=['tempo', 'x_referencia', 'y_instrumento'])
caminho_csv = os.path.join(DIR_DADOS, 'Equipe_08_Limiar.csv')
df.to_csv(caminho_csv, index=False)

# --------------------------------------------------------------------------
# Figura de apoio ao relatorio: primeira varredura (sweep 0), mostrando a
# grandeza de referencia (sinal em escada fina, sem distorcao) sobreposta
# a' leitura do instrumento (que so muda ao cruzar um quantum, com o ruido
# produzindo dispersao perto de cada transicao).
# --------------------------------------------------------------------------
primeira = df.iloc[:N_STEPS + 1]
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.plot(primeira['x_referencia'], primeira['x_referencia'], lw=1.2, color='#888888',
        ls='--', label='x_referencia (grandeza real, sem distorcao)')
ax.plot(primeira['x_referencia'], primeira['y_instrumento'], 'o', ms=3.2, color='#1f4e79',
        label='y_instrumento (leitura, com ruido)')
ax.set_xlabel('x_referencia  [graus]  (incremento acumulado a partir do repouso)')
ax.set_ylabel('[graus]')
ax.set_title('Protocolo Limiar -- primeira varredura de %d incrementos' % N_STEPS)
ax.legend(loc='upper left', fontsize=8.5)
ax.grid(alpha=.3)
fig.tight_layout()
fig.savefig(os.path.join(DIR_FIGS, 'dados_limiar_visualizacao.png'), dpi=160)
plt.close(fig)

# --------------------------------------------------------------------------
# Resumo de verificacao (nao entra no CSV; apenas para conferencia da equipe)
# --------------------------------------------------------------------------
n_total = len(df)
n_distintos = df['y_instrumento'].nunique()
troca = df.groupby([np.arange(n_total) // (N_STEPS + 1)])['y_instrumento'].apply(
    lambda s: (s.diff().fillna(0) != 0).sum())
print('OK - dataset gerado: %s' % caminho_csv)
print('  amostras totais.......... %d  (%d varreduras x %d passos)' % (n_total, M_SWEEPS, N_STEPS + 1))
print('  codigos distintos em y... %d' % n_distintos)
print('  transicoes de codigo por varredura (media)... %.2f' % troca.mean())
print('  figura de apoio.......... %s' % os.path.join(DIR_FIGS, 'dados_limiar_visualizacao.png'))
