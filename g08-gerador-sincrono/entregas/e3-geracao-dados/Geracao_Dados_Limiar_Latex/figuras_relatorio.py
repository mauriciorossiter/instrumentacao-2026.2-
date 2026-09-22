# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Topico: LIMIAR
Figuras do relatorio LaTeX de geracao de dados (Secao 3.3).

Le o dataset ja entregue (../dados/Equipe_08_Limiar.csv) -- nao gera dados
novos, apenas as duas figuras que ilustram o relatorio:

  figs/dados_limiar_visualizacao.pdf     primeira varredura: x_referencia
                                          sobreposto a y_instrumento
  figs/primeira_transicao_histograma.pdf variabilidade do 1o incremento em
                                          que a leitura muda, entre as
                                          varreduras
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(AQUI, 'figs')
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': .3,
                     'figure.dpi': 160, 'savefig.bbox': 'tight',
                     'axes.spines.top': False, 'axes.spines.right': False})

df = pd.read_csv(os.path.join(AQUI, '..', 'dados', 'Equipe_08_Limiar.csv'))

N_STEPS = 100                                    # passos por varredura (0..100), ver relatorio
passos_por_varredura = N_STEPS + 1
n_varreduras = len(df) // passos_por_varredura
df['varredura'] = np.arange(len(df)) // passos_por_varredura
df['k'] = np.arange(len(df)) % passos_por_varredura

# ===========================================================================
# FIGURA 1 - primeira varredura: referencia x leitura do instrumento
# ===========================================================================
primeira = df[df['varredura'] == 0]
fig1, ax1 = plt.subplots(figsize=(6.6, 4.0))
ax1.plot(primeira['x_referencia'], primeira['x_referencia'], lw=1.1, color='#888888',
         ls='--', label=r'$x_{\mathrm{referencia}}$ (grandeza real, sem distorção)')
ax1.plot(primeira['x_referencia'], primeira['y_instrumento'], 'o', ms=3.0, color='#1f4e79',
         label=r'$y_{\mathrm{instrumento}}$ (leitura, com ruído)')
ax1.set_xlabel(r'$x_{\mathrm{referencia}}$  [graus]  (incremento acumulado a partir do repouso)')
ax1.set_ylabel('[graus]')
ax1.set_title('Protocolo Limiar --- primeira varredura de incrementos crescentes')
ax1.legend(loc='upper left', fontsize=8)
fig1.tight_layout()
fig1.savefig(os.path.join(FIG, 'dados_limiar_visualizacao.pdf'))
plt.close(fig1)

# ===========================================================================
# FIGURA 2 - variabilidade do 1o incremento detectado, entre varreduras
# ===========================================================================
primeiras_k = []
for v, g in df.groupby('varredura'):
    g = g.sort_values('k')
    y0 = g.iloc[0]['y_instrumento']
    diff = g[g['y_instrumento'] != y0]
    primeiras_k.append(int(diff.iloc[0]['k']) if len(diff) else np.nan)
primeiras_k = np.array(primeiras_k, dtype=float)

fig2, ax2 = plt.subplots(figsize=(6.2, 4.0))
bins = np.arange(0.5, np.nanmax(primeiras_k) + 1.5, 1.0)
ax2.hist(primeiras_k, bins=bins, color='#1f4e79', edgecolor='white', alpha=.9)
ax2.axvline(np.nanmean(primeiras_k), color='#c00000', lw=1.3, ls='--',
            label=r'média = %.2f' % np.nanmean(primeiras_k))
ax2.set_xlabel(u'índice k do 1º incremento em que a leitura muda (por varredura)')
ax2.set_ylabel(u'número de varreduras')
ax2.set_title(u'Variabilidade do limiar observado nos dados brutos\n'
              u'(%d varreduras independentes, mesmo protocolo)' % n_varreduras)
ax2.legend(loc='upper right', fontsize=8.5)
fig2.tight_layout()
fig2.savefig(os.path.join(FIG, 'primeira_transicao_histograma.pdf'))
plt.close(fig2)

print('OK - figuras em', FIG)
print('  primeira transicao k: media=%.2f  min=%d  max=%d' %
      (np.nanmean(primeiras_k), np.nanmin(primeiras_k), np.nanmax(primeiras_k)))
