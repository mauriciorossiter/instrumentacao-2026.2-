# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03
Compara os CSV do TyphoonSim (roda_ensaios.py) com o gabarito Python (ensaios.py).

  - theta_ref e theta_cursor (sinais, sem atraso): ponto a ponto. Diferenca de 0,72 grau ou
    mais indica problema no gerador, na folga ou na injecao da condicao inicial.
  - theta_med (passa pelo circuito): contra a coluna *_typhoon do gabarito, que ja tem o atraso
    numerico de 2 amostras. O ruido de contato mexe em theta_med so na 9a casa (1e-10 A no laco),
    entao a outra realizacao do Random Source nao atrapalha a comparacao.
Saidas: ../gabarito/comparacao_typhoon.json e ../figuras/fig-17-e03-typhoon-x-python.png

Uso:  python compara_ensaios.py
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ensaios as G      # noqa: E402
import parametros as P   # noqa: E402

DADOS = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'dados'))
LETRA = {'a': 1, 'b': 2, 'c': 3}
CAMADAS = {'completa': G.TODAS, 'ideal': ()}


def le(arq):
    d = np.genfromtxt(arq, delimiter=',', names=True)
    return {n: d[n] for n in d.dtype.names}


def main():
    import estilo as S
    S.aplica_estilo()
    res = {}
    fig, ax = plt.subplots(3, 1, figsize=(8, 6.6), sharex=True)
    for i, (letra, ens) in enumerate(LETRA.items()):
        for caso, cam in CAMADAS.items():
            arq = os.path.join(DADOS, 'ensaio_%s_%s.csv' % (letra, caso))
            if not os.path.exists(arq):
                print('falta %s' % arq)
                continue
            ty = le(arq)
            g = G.simula(ens, cam)
            t = g['t']
            _, th_g = G.com_atraso(g)
            interp = lambda nome: np.interp(t, ty['Time'], ty[nome])   # noqa: E731
            ok = G.janela_estavel(g)
            r = dict(
                theta_ref_max_graus=float(np.max(np.abs(interp('theta_ref') - g['theta_ref']))),
                theta_cursor_max_graus=float(np.max(np.abs(interp('theta_cursor') - g['theta_cursor']))),
                theta_med_max_graus=float(np.max(np.abs(interp('theta_med') - th_g)[ok])),
            )
            r['confere'] = bool(r['theta_ref_max_graus'] < 1e-6 and r['theta_cursor_max_graus'] < 0.1
                                and r['theta_med_max_graus'] < 0.05)
            res['%s_%s' % (letra, caso)] = r
            print('ensaio (%s) %-8s %s' % (letra, caso, r))
            if caso == 'completa':
                a = ax[i]
                d_ty = np.where(ok, interp('theta_med') - g['theta_ref'], np.nan)
                d_g = np.where(ok, th_g - g['theta_ref'], np.nan)
                a.plot(t, d_g, color=S.CINZA, lw=3, alpha=0.5, label='gabarito Python')
                a.plot(t, d_ty, color=S.AZUL, lw=1.2, label='TyphoonSim')
                a.set_ylabel('medido − ref. [graus]')
                a.set_title('ensaio (%s)' % letra, loc='left', fontsize=9)
                a.set_ylim(-3, 3)
    ax[0].legend(loc='lower right')
    ax[-1].set_xlabel('tempo [s]')
    fig.tight_layout()
    os.makedirs(G.DIR_FIG, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(G.DIR_FIG, 'fig-17-e03-typhoon-x-python.%s' % ext))
    plt.close(fig)
    os.makedirs(G.DIR_GAB, exist_ok=True)
    with open(os.path.join(G.DIR_GAB, 'comparacao_typhoon.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
