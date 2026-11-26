# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E03, E04 e Entrega Final: compara os ensaios rodados no Virtual HIL (typhoonsim/dados/*.csv,
gerados por typhoonsim/roda_vhil.py) com o gabarito Python (sistema.py), ensaio por ensaio.

1. Cada captura e' reamostrada na grade de 1 ms do gabarito e realinhada no tempo: a captura comeca algumas
   dezenas de ms depois do Start, entao o deslocamento e' o que minimiza o erro RMS do canal V_ideal (sem ruido).
2. As MESMAS metricas do gabarito sao aplicadas aos dois lados: e03.metricas/caracteristicos (E03) e
   e04.metricas (E04: Mp, ts, erro estacionario, afundamento, Efd pico, sigma(Efd), zeta).
3. O ruido do VHIL (Random Source sem semente) nao e' a mesma realizacao do gabarito: nos canais com ruido a
   comparacao e' estatistica.

Saidas: typhoonsim/comparacao_typhoon.json; ../relatorio/figuras/fig-06-vhil-malha-aberta.png, fig-10-vhil-malha-fechada.png
Uso:    python compara_typhoon.py
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, AQUI)
import parametros_e34 as P          # noqa: E402
import sistema as S                 # noqa: E402
import estilo as E                  # noqa: E402
import e03 as E3                    # noqa: E402
import e04 as E4                    # noqa: E402
from ensaios_e34 import ENSAIOS     # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402

DADOS = os.path.join(AQUI, '..', 'dados')
DT = 1e-3
MAPA = (('V_ideal', 'V_id'), ('V_real', 'V_re'), ('f_ideal', 'f_id'), ('f_real', 'f_re'), ('Efd', 'Efd'),
        ('upss', 'upss'), ('Vref_ef', 'Vref'), ('Pe_pu', 'Pe'))


def le_vhil(nome, gab):
    d = pd.read_csv(os.path.join(DADOS, nome + '.csv'))
    t = d['Time'].to_numpy(float)
    # deslocamento: minimiza o RMS de V_ideal (canal sem ruido) contra o gabarito
    best = (0.0, np.inf)
    vi = d['V_ideal'].to_numpy(float)
    for off in np.arange(-0.10, 0.10001, 0.0005):
        tt = t + off
        k = (tt >= gab['t'][0]) & (tt <= gab['t'][-1])
        e = vi[k] - np.interp(tt[k], gab['t'], gab['V_id'])
        r = np.sqrt(np.mean(e**2))
        if r < best[1]:
            best = (off, r)
    off = best[0] if np.ptp(gab['V_id']) > 1e-4 else 0.0
    tt = t + off
    tg = np.arange(max(round(tt[0]/DT)*DT, 0.0) + DT, min(tt[-1], gab['t'][-1]) - DT/2, DT)
    r = dict(t=tg, deslocamento_ms=1e3*off)
    for col, k in MAPA:
        if col in d:
            r[k] = np.interp(tg, tt, d[col].to_numpy(float))
    r['delta'] = np.radians(np.interp(tg, tt, d['delta_graus'].to_numpy(float)))
    return r


def corta(g, t0, t1):
    k = (g['t'] >= t0 - 1e-9) & (g['t'] <= t1 + 1e-9)
    return {c: (v[k] if isinstance(v, np.ndarray) and v.shape == g['t'].shape else v) for c, v in g.items()}


def gab(nome):
    ens, cfg = ENSAIOS[nome]
    return S.simula(ens, cfg)


def par(nome):
    g = gab(nome)
    v = le_vhil(nome, g)
    g = corta(g, v['t'][0], v['t'][-1])
    return g, v


def limpo(o):
    if isinstance(o, dict):
        return {str(k): limpo(x) for k, x in o.items() if k not in ('t',) and not isinstance(x, np.ndarray)}
    if isinstance(o, (list, tuple)):
        return [limpo(x) for x in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def main():
    E.aplica_estilo()
    out = dict(e03={}, e04={})
    curvas = {}
    # ------------------------------------------------------------------ E03 (malha aberta)
    for nome, letra in (('e03_a', 'a'), ('e03_b', 'b'), ('e03_c', 'c'), ('e03_c_tau1', 'c'), ('e03_b_N16', 'b')):
        if not os.path.exists(os.path.join(DADOS, nome + '.csv')):
            continue
        g, v = par(nome)
        out['e03'][nome] = dict(deslocamento_ms=v['deslocamento_ms'],
                                gabarito=dict(metricas=E3.metricas(g), caracteristicos=E3.caracteristicos(letra, g)),
                                vhil=dict(metricas=E3.metricas(v), caracteristicos=E3.caracteristicos(letra, v)),
                                dif_max_V_ideal=float(np.max(np.abs(v['V_id'] - g['V_id']))),
                                dif_max_delta_graus=float(np.degrees(np.max(np.abs(v['delta'] - g['delta'])))))
        curvas[nome] = (g, v)
        print(nome, 'desloc %.1f ms' % v['deslocamento_ms'], 'dV_ideal %.2e' % out['e03'][nome]['dif_max_V_ideal'],
              'ddelta %.3f graus' % out['e03'][nome]['dif_max_delta_graus'], flush=True)
    # ------------------------------------------------------------------ E04 (malha fechada)
    for caso in ('ideal', 'real', 'R5'):
        nomes = ['e04_%s_%s' % (caso, e) for e in ('r', 'p', 'regime')]
        if not all(os.path.exists(os.path.join(DADOS, n + '.csv')) for n in nomes):
            continue
        cfg = ENSAIOS[nomes[0]][1]
        gs, vs = [], []
        for n in nomes:
            g, v = par(n)
            gs.append(g); vs.append(v)
            curvas[n] = (g, v)
        mg, _ = E4.metricas(cfg, runs=tuple(gs))
        mv, _ = E4.metricas(cfg, runs=tuple(vs))
        out['e04'][caso] = dict(gabarito=mg, vhil=mv, deslocamento_ms=[v['deslocamento_ms'] for v in vs])
        fn = 'e04_%s_f' % caso
        if os.path.exists(os.path.join(DADOS, fn + '.csv')):
            g, v = par(fn)
            curvas[fn] = (g, v)
            for lado, r in (('gabarito', g), ('vhil', v)):
                out['e04'][caso][lado]['falta'] = dict(
                    delta_max_graus=float(np.degrees(r['delta'].max())),
                    Efd_max=float(r['Efd'].max()), Efd_min=float(r['Efd'].min()),
                    V_final=float(np.mean(r['V_id'][r['t'] > r['t'][-1] - 0.5])))
        print(caso, {k: (round(mg[k], 4) if isinstance(mg[k], float) else None, round(mv[k], 4)
                         if isinstance(mv[k], float) else None) for k in ('efd_pico', 'dp_efd', 'zeta')},
              'Mp', round(mg['planta']['Mp_pct'], 2), round(mv['planta']['Mp_pct'], 2),
              'ess', round(mg['planta']['ess_pct'], 3), round(mv['planta']['ess_pct'], 3), flush=True)

    # ------------------------------------------------------------------ Entrega Final (opcional): uma de cada vez
    out['final'] = {}
    for nome in [n for n in ENSAIOS if n.startswith('fin_a_so_')]:
        if not os.path.exists(os.path.join(DADOS, nome + '.csv')):
            continue
        g, v = par(nome)
        mg, mv = E3.metricas(g), E3.metricas(v)
        out['final'][nome] = dict(gabarito=dict(V=mg['V'], f=mg['f']), vhil=dict(V=mv['V'], f=mv['f']),
                                  deslocamento_ms=v['deslocamento_ms'])
        print(nome, 'erro RMS V [mpu] %.3f / %.3f' % (1e3*mg['V']['err_rms'], 1e3*mv['V']['err_rms']),
              'f [mHz] %.2f / %.2f' % (1e3*mg['f']['err_rms'], 1e3*mv['f']['err_rms']), flush=True)

    with open(os.path.join(AQUI, 'comparacao_typhoon.json'), 'w', encoding='utf-8') as fh:
        json.dump(limpo(out), fh, indent=1, ensure_ascii=False)
    figuras(curvas)


def lado(ax, g, v, chave, esc=1.0, rot='', tmax=None, cor=None):
    k = g['t'] <= (tmax or 99)
    ax.plot(g['t'][k], esc*g[chave][k], color=E.CINZA, lw=2.4, alpha=0.55, label='gabarito Python')
    k = v['t'] <= (tmax or 99)
    ax.plot(v['t'][k], esc*v[chave][k], color=cor or E.AZUL, lw=0.9, label='VHIL')
    ax.set_title(rot)
    ax.set_xlabel('t [s]')
    E.virgula(ax)


def figuras(c):
    out_dir = os.path.join(AQUI, '..', '..', 'relatorio', 'figuras')
    os.makedirs(out_dir, exist_ok=True)
    if all(k in c for k in ('e03_a', 'e03_c', 'e03_c_tau1', 'e03_b_N16')):
        fig, axs = plt.subplots(2, 2, figsize=(7.6, 5.2))
        g, v = c['e03_a']
        lado(axs[0, 0], g, v, 'V_re', rot='(a) degrau de Pm: V medida [pu]', tmax=5)
        axs[0, 0].plot(v['t'][v['t'] <= 5], v['V_id'][v['t'] <= 5], color=E.LARANJA, lw=0.8, label='V real (VHIL)')
        axs[0, 0].legend(fontsize=7)
        lado(axs[0, 1], g, v, 'f_re', rot='(a) degrau de Pm: f medida [Hz]', tmax=5)
        g, v = c['e03_c']
        lado(axs[1, 0], g, v, 'V_re', rot='(c) falta 200 ms: V medida [pu]', tmax=2.5)
        g2, v2 = c['e03_c_tau1']
        k = v2['t'] <= 2.5
        axs[1, 0].plot(v2['t'][k], v2['V_re'][k], color=E.VIOLETA, lw=0.9, label='VHIL, τ_RMS = 1 s (R5)')
        axs[1, 0].legend(fontsize=7)
        g, v = c['e03_b_N16']
        lado(axs[1, 1], g, v, 'f_re', rot='(b) com N = 16 ciclos (R5): f medida [Hz]', tmax=4, cor=E.VIOLETA)
        k = v['t'] <= 4
        axs[1, 1].plot(v['t'][k], v['f_id'][k], color=E.LARANJA, lw=0.8, label='f real (VHIL)')
        axs[1, 1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, 'fig-06-vhil-malha-aberta.png'))
        plt.close(fig)
    if all(k in c for k in ('e04_ideal_r', 'e04_real_r', 'e04_real_p', 'e04_R5_regime', 'e04_real_regime')):
        fig, axs = plt.subplots(2, 2, figsize=(7.6, 5.2))
        for nome, cor, rot in (('e04_ideal_r', E.AZUL, 'medição ideal'), ('e04_real_r', E.LARANJA, 'medição real')):
            g, v = c[nome]
            k = g['t'] <= 4
            axs[0, 0].plot(g['t'][k], g['V_id'][k], color=E.CINZA, lw=2.4, alpha=0.5)
            k = v['t'] <= 4
            axs[0, 0].plot(v['t'][k], v['V_id'][k], color=cor, lw=0.9, label=rot)
        axs[0, 0].set_title('degrau de Vref (+0,02 pu): V real da planta [pu]')
        axs[0, 0].legend(fontsize=7); axs[0, 0].set_xlabel('t [s]'); E.virgula(axs[0, 0])
        for nome, cor, rot in (('e04_ideal_p', E.AZUL, 'medição ideal'), ('e04_real_p', E.LARANJA, 'medição real')):
            if nome not in c:
                continue
            g, v = c[nome]
            k = g['t'] <= 8
            axs[0, 1].plot(g['t'][k], np.degrees(g['delta'][k]), color=E.CINZA, lw=2.4, alpha=0.5)
            k = v['t'] <= 8
            axs[0, 1].plot(v['t'][k], np.degrees(v['delta'][k]), color=cor, lw=0.9, label=rot)
        axs[0, 1].set_title('degrau de Pm (+0,1 pu): δ [graus]')
        axs[0, 1].legend(fontsize=7); axs[0, 1].set_xlabel('t [s]'); E.virgula(axs[0, 1])
        for nome, cor, rot in (('e04_real_regime', E.LARANJA, 'passa-baixas 150 Hz'),
                               ('e04_R5_regime', E.AQUA, 'passa-faixa 60 ± 5 Hz (R5)')):
            g, v = c[nome]
            axs[1, 0].plot(v['t'], v['Efd'], color=cor, lw=0.7, label=rot + ': σ = %s pu' % ('%.3f' % np.std(v['Efd'][v['t'] > 0.2])).replace('.', ','))
        axs[1, 0].set_title('regime, medição real: Efd [pu] no VHIL')
        axs[1, 0].legend(fontsize=7); axs[1, 0].set_xlabel('t [s]'); E.virgula(axs[1, 0])
        if 'e04_R5_p' in c:
            for nome, cor, rot in (('e04_real_p', E.LARANJA, 'passa-baixas'), ('e04_R5_p', E.AQUA, 'passa-faixa (R5)')):
                g, v = c[nome]
                k = v['t'] <= 8
                axs[1, 1].plot(v['t'][k], np.degrees(v['delta'][k]), color=cor, lw=0.9, label=rot)
            axs[1, 1].set_title('degrau de Pm, medição real: δ [graus] no VHIL')
            axs[1, 1].legend(fontsize=7); axs[1, 1].set_xlabel('t [s]'); E.virgula(axs[1, 1])
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, 'fig-10-vhil-malha-fechada.png'))
        plt.close(fig)


if __name__ == '__main__':
    main()
