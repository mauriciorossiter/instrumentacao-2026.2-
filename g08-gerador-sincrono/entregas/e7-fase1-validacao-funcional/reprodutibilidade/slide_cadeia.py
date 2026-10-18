# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03
Slide de abertura do video (1920 x 1080): a cadeia completa, com o que veio de cada entrega.
Saida: ../figuras/slide-00-cadeia.png

Uso:  python slide_cadeia.py
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import parametros_e03 as E   # noqa: E402,F401  (poe a E02 no sys.path)
import estilo as S           # noqa: E402

COR = {'E01': S.AZUL, 'E02': S.LARANJA, 'E03': S.AQUA}
FUNDO = '#fcfcfb'


def caixa(ax, x, y, w, h, titulo, linhas, ent, fs=17):
    cor = COR[ent]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.12',
                                fc='white', ec=cor, lw=3))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.09), w, 0.09, boxstyle='square,pad=0', fc=cor, ec=cor, lw=0))
    ax.text(x + w / 2, y + h - 0.32, titulo, ha='center', va='center', fontsize=fs, weight='bold', color=S.TINTA)
    for i, l in enumerate(linhas):
        ax.text(x + w / 2, y + h - 0.7 - 0.36 * i, l, ha='center', va='center', fontsize=13.5 if not l.startswith('saída') else 12.5, color=(S.CINZA if l.startswith('saída') else S.TINTA2), style=('italic' if l.startswith('saída') else 'normal'))


def seta(ax, x0, y0, x1, y1, rot='', cor=S.TINTA2, dy=0.2):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='-|>', color=cor, lw=2.4, mutation_scale=22))
    if rot:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, rot, ha='center', va='bottom', fontsize=12.5, color=S.TINTA2)


def main():
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=FUNDO)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 19.2); ax.set_ylim(0, 10.8); ax.axis('off')

    ax.text(0.7, 10.05, 'Grupo 08 — cadeia de medição completa', fontsize=34, weight='bold', color=S.TINTA)
    ax.text(0.7, 9.45, 'Ângulo do eixo do gerador síncrono (0–3600°) medido por potenciômetro e laço de corrente 4–20 mA',
            fontsize=17, color=S.TINTA2)

    # linha principal: largura total de 0,6 a 18,6 com 5 vaos de 0,55
    y, h = 4.2, 2.55
    gap = 0.55
    blocos = [
        (2.5, 'Referência θ_ref', ['gerador de ensaios', '(a) degrau', '(b) cond. inicial', '(c) pulso · varredura E01', 'saída: θ do eixo'], 'E03'),
        (3.3, 'Camadas do sensor', ['R6 folga 1,0°', 'R6 resolução 0,72°', 'R7 ordem zero (y = K·x)', 'R8 ruído de contato 1/f', 'saída: θ do cursor'], 'E02'),
        (2.4, 'Potenciômetro', ['Bourns 3590S, 10 kΩ', '10 voltas = 3600°', 'K = 0,694 mV/°', '', 'saída: v_cursor'], 'E01'),
        (2.0, 'Buffer', ['OPA333', 'seguidor', 'I_B ≤ 200 pA', '', 'saída: I_IN'], 'E01'),
        (2.5, 'Transmissor', ['XTR115', 'I_O = 100 · I_IN', 'R0 = 62,6 kΩ', 'R_IN = 15,6 kΩ', 'saída: 4–20 mA'], 'E01'),
        (2.55, 'Receptor', ['R_L = 250 Ω', 'laço de 24 V', 'θ_med =', '3600·(I − 4)/16', 'saída: θ_med'], 'E01'),
    ]
    x = 0.6
    xs = []
    for w, tit, lin, ent in blocos:
        caixa(ax, x, y, w, h, tit, lin, ent)
        xs.append((x, w))
        x += w + gap
    ym = y + h / 2 - 0.15
    for (x0, w0), (x1, _) in zip(xs[:-1], xs[1:]):
        seta(ax, x0 + w0 + 0.04, ym, x1 - 0.04, ym)
    x_ref = xs[0][0] + xs[0][1] / 2
    x_cam = xs[1][0] + xs[1][1] / 2
    x_rx = xs[-1][0] + xs[-1][1] / 2

    # painel SCADA (topo) e comparacao R12 (baixo)
    caixa(ax, 2.2, 7.6, 9.0, 1.25, 'Painel SCADA (operado ao vivo)', ['ensaio · disparo · amplitude · θ₀ · δ₀ · largura · liga/desliga de cada camada'], 'E03', fs=16)
    seta(ax, 3.2, 7.6, x_ref, y + h + 0.03)
    seta(ax, x_cam, 7.6, x_cam, y + h + 0.03)
    caixa(ax, 5.6, 1.35, 8.6, 1.25, 'R12 — medido × referência ideal', ['Trace Graph do SCADA: θ_med sobreposto a θ_ref nos três ensaios'], 'E03', fs=16)
    seta(ax, x_ref, y, 5.6, 2.0, cor=S.CINZA)
    seta(ax, x_rx, y, 14.2, 2.0, cor=S.CINZA)

    # legenda das entregas
    for i, (ent, txt) in enumerate((('E01', 'Entrega 01 — cadeia ideal (circuito sem alteração)'),
                                    ('E02', 'Entrega 02 — três camadas de não idealidade'),
                                    ('E03', 'Entrega 03 — ensaios-padrão e painel SCADA'))):
        yy = 0.55 - 0.0 * i
        xx = 0.7 + 6.2 * i
        ax.add_patch(FancyBboxPatch((xx, yy - 0.12), 0.45, 0.24, boxstyle='round,pad=0,rounding_size=0.05',
                                    fc=COR[ent], ec=COR[ent]))
        ax.text(xx + 0.6, yy, txt, va='center', fontsize=14, color=S.TINTA)

    out = os.path.abspath(os.path.join(AQUI, '..', 'figuras', 'slide-00-cadeia.png'))
    if os.environ.get('G08_TESTE'):
        out = os.path.join(os.environ['G08_TESTE'], 'slide-00-cadeia.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=100, facecolor=FUNDO)
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    main()
