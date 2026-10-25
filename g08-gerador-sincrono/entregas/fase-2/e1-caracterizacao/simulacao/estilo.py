# -*- coding: utf-8 -*-
"""Estilo comum das figuras (paleta, fontes, grade, virgula decimal) e rotina de salvamento PNG."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_PNG = os.path.join(AQUI, '..', 'relatorio', 'figuras')
# modo de teste: desvia as figuras para outra pasta (caracterizacao.py desvia tambem json e csv)
if os.environ.get('G08_TESTE'):
    DIR_PNG = os.environ['G08_TESTE']

# paleta categorica (ordem fixa, a mesma das entregas anteriores) + tintas de texto
AZUL, LARANJA, AQUA, AMARELO = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
MAGENTA, VERDE, VIOLETA = '#e87ba4', '#008300', '#6250d6'
TINTA, TINTA2, CINZA, GRADE = '#0b0b0b', '#52514e', '#898781', '#e1e0d9'
CRITICO = '#d03b3b'            # status: perda de sincronismo (sempre com rotulo)
FAIXA = '#ecebe6'              # preenchimento neutro (faixa de 2 %, intervalo de falta)
# rampa ordinal (um so matiz, claro -> escuro) para niveis de um parametro
RAMPA = ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281', '#0d366b']

SOLVER = 'RK4 de passo fixo, h = 1 ms'


def rampa(n):
    """n tons da rampa ordinal, igualmente espacados."""
    if n == 1:
        return [RAMPA[2]]
    idx = [round(i*(len(RAMPA) - 1)/(n - 1)) for i in range(n)]
    return [RAMPA[i] for i in idx]


def aplica_estilo():
    plt.rcParams.update({
        'font.size': 8.5, 'font.family': 'DejaVu Sans', 'mathtext.fontset': 'dejavusans',
        'axes.edgecolor': '#c3c2b7', 'axes.labelcolor': TINTA, 'axes.linewidth': 0.6,
        'axes.titlesize': 8.5, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
        'axes.titlecolor': TINTA,
        'xtick.color': TINTA2, 'ytick.color': TINTA2,
        'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
        'xtick.major.size': 3, 'ytick.major.size': 3,
        'axes.grid': True, 'grid.color': GRADE, 'grid.linewidth': 0.5,
        'axes.spines.top': False, 'axes.spines.right': False,
        'legend.edgecolor': GRADE, 'legend.fontsize': 7.5, 'legend.framealpha': 0.95,
        'lines.linewidth': 1.4,
        'figure.dpi': 110, 'savefig.dpi': 220, 'savefig.bbox': 'tight',
        'savefig.facecolor': 'white',
        'axes.formatter.use_locale': False,
    })


def num(x, nd=2):
    """Numero com virgula decimal (pt-BR) e sinal de menos tipografico."""
    return f'{x:.{nd}f}'.replace('.', ',').replace('-', '−')


def cient(x, nd=1):
    """Notacao cientifica com virgula: 2,2x10^-10 (para texto de figura)."""
    m, e = f'{x:.{nd}e}'.split('e')
    sup = str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')
    return m.replace('.', ',') + '×10' + str(int(e)).translate(sup)


def _fmt_virgula(x, pos=None):
    s = f'{x:.6g}'
    if 'e' in s:
        return s
    return s.replace('.', ',').replace('-', '−')


def virgula(*eixos):
    """Rotulos dos eixos lineares com virgula decimal."""
    for ax in eixos:
        ax.xaxis.set_major_formatter(FuncFormatter(_fmt_virgula))
        ax.yaxis.set_major_formatter(FuncFormatter(_fmt_virgula))


def rotulo_solver(ax, x=0.995, y=0.02, ha='right', va='bottom', texto=SOLVER):
    """Declara solver e passo no proprio grafico (exigencia do R3)."""
    ax.text(x, y, texto, transform=ax.transAxes, ha=ha, va=va, fontsize=6.5, color=TINTA2,
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=GRADE, lw=0.5))


def salva(fig, nome):
    os.makedirs(DIR_PNG, exist_ok=True)
    fig.savefig(os.path.join(DIR_PNG, nome + '.png'))
    plt.close(fig)
