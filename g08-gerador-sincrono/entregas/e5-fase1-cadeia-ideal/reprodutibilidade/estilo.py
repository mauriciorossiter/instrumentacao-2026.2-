# -*- coding: utf-8 -*-
"""Estilo comum das figuras (paleta, fontes, grade) e rotina de salvamento PNG + PDF."""
import os
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_PNG = os.path.join(AQUI, '..', 'relatorio', 'figuras')
DIR_PDF = os.path.join(AQUI, '..', 'Fase1_Latex', 'figs')
# modo de teste: desvia as figuras para outra pasta (nunca sobrescreve as da entrega)
if os.environ.get('G08_TESTE'):
    DIR_PNG = DIR_PDF = os.environ['G08_TESTE']

# paleta categorica (ordem fixa) + tintas de texto
AZUL, LARANJA, AQUA, AMARELO = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
TINTA, TINTA2, CINZA = '#0b0b0b', '#52514e', '#8a8983'


def aplica_estilo():
    plt.rcParams.update({
        'font.size': 9, 'font.family': 'DejaVu Sans',
        'axes.edgecolor': CINZA, 'axes.labelcolor': TINTA, 'axes.linewidth': 0.6,
        'xtick.color': TINTA2, 'ytick.color': TINTA2,
        'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
        'axes.grid': True, 'grid.color': '#d9d8d3', 'grid.linewidth': 0.5,
        'axes.spines.top': False, 'axes.spines.right': False,
        'legend.edgecolor': '#d9d8d3', 'legend.fontsize': 8,
        'figure.dpi': 110, 'savefig.dpi': 200, 'savefig.bbox': 'tight',
        'axes.formatter.use_locale': False,
    })


def salva(fig, nome):
    os.makedirs(DIR_PNG, exist_ok=True)
    os.makedirs(DIR_PDF, exist_ok=True)
    fig.savefig(os.path.join(DIR_PNG, nome + '.png'))
    fig.savefig(os.path.join(DIR_PDF, nome + '.pdf'))
    plt.close(fig)
