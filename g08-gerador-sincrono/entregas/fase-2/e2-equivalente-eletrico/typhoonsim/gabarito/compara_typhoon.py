# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: compara o equivalente eletrico rodado no Virtual HIL
(typhoonsim/dados/*.csv, gerados por typhoonsim/roda_vhil.py) com a Entrega 01 (RK4, modelo.py).

As mesmas metricas da E01 (modelo.metricas_degrau) sao aplicadas as duas respostas, e o tempo do
VHIL e' realinhado no evento (borda de Pm no degrau, queda de Pe na falta), porque o instante de
inicio da captura e' so aproximado.

Uso (Python comum):  python compara_typhoon.py
Saidas: resultados_typhoon.json; ../../relatorio/figuras/fig-02-vhil-ensaios.png,
        fig-03-vhil-sensibilidade.png
"""
import json
import math
import os

import numpy as np
import pandas as pd

import parametros_e02 as P
import modelo as M1
import estilo as E
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
VHIL = os.path.join(AQUI, '..', 'dados')
G = np.degrees
LIM = math.pi


def pdif(sim, ref):
    if sim is None or ref is None or ref == 0 or not np.isfinite(ref):
        return None
    return 100.0*(sim - ref)/abs(ref)


def le(nome):
    f = os.path.join(VHIL, nome + '.csv')
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f)
    return dict(t=d['Time'].to_numpy(float), t_sim=d['t_sim'].to_numpy(float),
                delta=np.radians(d['delta_graus'].to_numpy(float)), omega=d['delta_omega'].to_numpy(float),
                Pe=d['Pe_pu'].to_numpy(float), Pm=d['Pm_pu'].to_numpy(float), vC=d['vC_V'].to_numpy(float),
                i=d['i_A'].to_numpy(float), vnl=d['vnl_V'].to_numpy(float), vm=d['Vm_V'].to_numpy(float))


def corta(r, t0):
    """Realinha o tempo em t0 e guarda so' t >= 0."""
    k = r['t'] >= t0 - 1e-12
    return {c: (v[k] - t0 if c == 't' else v[k]) for c, v in r.items()}


def evento_degrau(r):
    pm = r['Pm']
    k = np.argmax(pm > 0.5*(pm[0] + pm[-1]))
    return r['t'][k]


def evento_falta(r):
    k = np.argmax((r['t'] > -0.5) & (np.abs(r['Pe']) < 0.02))
    return r['t'][k]


# ------------------------------------------------------------------ E01 (referencia)
def e01(segs, d0=P.DELTA0, lim=None):
    return M1.simula([M1.seg(du, Pm=pm, Pmax=px, D=dd) for (du, pm, px, dd) in segs], d0, delta_lim=lim)


def degrau(Pmax, D, dur):
    Pm1 = P.PM0 + P.DPM_DEGRAU
    return e01([(dur, Pm1, Pmax, D)], d0=math.asin(P.PM0/Pmax))


def metr(r, Pmax, final_medido=True):
    d_ini, d_fim = math.asin(P.PM0/Pmax), math.asin((P.PM0 + P.DPM_DEGRAU)/Pmax)
    if final_medido:
        # valor final medido (media do ultimo 0,5 s): as regressoes de sigma e omega_d usam o desvio
        # em torno do regime de cada resposta, sem herdar o pequeno erro estatico do VHIL
        d_fim = float(np.mean(r['delta'][r['t'] > r['t'][-1] - 0.5]))
    m = M1.metricas_degrau(r, d_ini, d_fim)
    if m['Mp'] is not None and m['Mp'] < 1e-3:          # superamortecido: sem pico nem oscilacao
        m['tp'], m['Mp'] = None, 0.0
    m['delta_final_medido_graus'] = float(G(np.mean(r['delta'][r['t'] > r['t'][-1] - 0.5])))
    m['ganho_rad_pu'] = (np.mean(r['delta'][r['t'] > r['t'][-1] - 0.5]) - d_ini)/P.DPM_DEGRAU
    if m.get('sigma') and m.get('wd'):
        m['zeta'] = m['sigma']/math.hypot(m['sigma'], m['wd'])
    return m


CHAVES = [('ganho_rad_pu', 'ganho estatico [rad/pu]'), ('tp', 't do 1o pico [s]'), ('Mp', 'sobressinal [-]'),
          ('wd', 'omega_d [rad/s]'), ('sigma', 'sigma [1/s]'), ('zeta', 'zeta [-]'), ('ts2', 't_s 2 % [s]')]


def tabela(mv, me):
    out = {}
    for k, _ in CHAVES:
        a, b = mv.get(k), me.get(k)
        if a is None or b is None or (isinstance(b, float) and not np.isfinite(b)):
            out[k] = dict(vhil=a, e01=b, dif_pct=None)
        else:
            out[k] = dict(vhil=a, e01=b, dif_pct=pdif(a, b))
    return out


def main():
    E.aplica_estilo()
    res = dict(criterio='ganho, tp, Mp, omega_d: |dif| <= 1 %; sigma e ts2 (medidas de cauda: regressao '
                        'de picos pequenos e cruzamento da faixa de 2 %): |dif| <= 10 %', ensaios={}, sens_D=[], sens_X=[])
    curvas = {}

    # ---------------- ensaio (a)
    r = le('ensaio_a_degrau')
    if r is not None:
        rv = corta(r, evento_degrau(r))
        dur = rv['t'][-1]
        re = degrau(P.P_MAX, P.D, dur)
        res['ensaios']['a_degrau'] = tabela(metr(rv, P.P_MAX), metr(re, P.P_MAX))
        res['ensaios']['a_degrau']['delta_final_graus'] = dict(
            vhil=metr(rv, P.P_MAX)['delta_final_medido_graus'], e01=metr(re, P.P_MAX)['delta_final_medido_graus'])
        curvas['a'] = (rv, re)

    # ---------------- ensaio (b): captura a partir do Start (Time = tempo de simulacao)
    r = le('ensaio_b_condicao_inicial')
    if r is not None:
        rv = corta(r, 0.0)
        re = e01([(rv['t'][-1] + 1.0, P.PM0, P.P_MAX, P.D)], d0=math.radians(P.DELTA_CI_GR))
        # o relogio de simulacao lido no inicio da captura e' grosseiro: o instante real do 1o ponto
        # sai da propria trajetoria (delta decrescente a partir de 60 graus, sistema autonomo)
        k1 = np.argmax(re['delta'] < rv['delta'][0])
        t_off = float(np.interp(rv['delta'][0], re['delta'][k1:k1 - 2:-1] if k1 > 1 else re['delta'][:2][::-1],
                                re['t'][k1:k1 - 2:-1] if k1 > 1 else re['t'][:2][::-1]))
        rv['t'] = rv['t'] + t_off
        k = np.searchsorted(re['t'], rv['t'][0])
        tpv, ypv = M1.picos(rv['t'], rv['delta'])
        tpe, ype = M1.picos(re['t'], re['delta'])
        tpv, ypv = tpv[tpv > 0.3], ypv[tpv > 0.3]
        tpe, ype = tpe[tpe > 0.3], ype[tpe > 0.3]
        janela = rv['t'] < 1.0
        sv = -np.polyfit(tpv[:20], np.log(ypv[:20] - P.DELTA0), 1)[0]
        se = -np.polyfit(tpe[:20], np.log(ype[:20] - P.DELTA0), 1)[0]
        b = dict(
            inicio_captura_s=t_off,
            T1=dict(vhil=float(tpv[0]), e01=float(tpe[0])),
            periodo=dict(vhil=float(np.mean(np.diff(tpv[:10]))), e01=float(np.mean(np.diff(tpe[:10])))),
            delta_min_graus=dict(vhil=float(G(np.min(rv['delta'][janela]))),
                                 e01=float(G(np.min(re['delta'][re['t'] < 1.0])))),
            pico1_graus=dict(vhil=float(G(ypv[0])), e01=float(G(ype[0]))),
            sigma=dict(vhil=float(sv), e01=float(se)))
        for v in b.values():
            if isinstance(v, dict):
                v['dif_pct'] = pdif(v['vhil'], v['e01'])
        res['ensaios']['b_condicao_inicial'] = b
        curvas['b'] = (rv, re)

    # ---------------- ensaio (c): faltas
    fal = []
    for tc in (0.20, 0.27, 0.287, 0.288, 0.29):
        r = le('ensaio_c_falta_%03dms' % round(1000*tc))
        if r is None:
            continue
        rv = corta(r, evento_falta(r) - P.T_INICIO_FALTA)
        re = e01([(P.T_INICIO_FALTA, P.PM0, P.P_MAX, P.D), (tc, P.PM0, 0.0, P.D),
                  (rv['t'][-1] - P.T_INICIO_FALTA - tc, P.PM0, P.P_MAX, P.D)], lim=4*LIM)
        out = {}
        for nome, rr in (('vhil', rv), ('e01', re)):
            kel = np.searchsorted(rr['t'], P.T_INICIO_FALTA + tc - 1e-9)
            out[nome] = dict(perdeu=bool(np.max(rr['delta']) > LIM), delta_elim_graus=float(G(rr['delta'][kel])),
                             delta_max_graus=float(G(np.max(rr['delta']))) if np.max(rr['delta']) <= LIM else None,
                             omega_max=float(np.max(rr['omega'][rr['t'] < P.T_INICIO_FALTA + tc + 0.6])))
        out['duracao_s'] = tc
        out['dif_delta_max_pct'] = pdif(out['vhil']['delta_max_graus'], out['e01']['delta_max_graus'])
        out['dif_delta_elim_pct'] = pdif(out['vhil']['delta_elim_graus'], out['e01']['delta_elim_graus'])
        fal.append(out)
        curvas['c%03d' % round(1000*tc)] = (rv, re)
    res['ensaios']['c_falta'] = fal
    est = [f['duracao_s'] for f in fal if not f['vhil']['perdeu']]
    ins = [f['duracao_s'] for f in fal if f['vhil']['perdeu']]
    if est and ins:
        res['ensaios']['tcr_vhil_s'] = [max(est), min(ins)]
    res['ensaios']['tcr_e01_s'] = [0.2879138, 0.2879224]

    # ---------------- R4: sensibilidade
    sens = {}
    for nd in (0.0, 0.1, 0.441, 1.0):
        r = le('sens_D_%s' % repr(nd))
        if r is None:
            continue
        rv = corta(r, evento_degrau(r))
        re = degrau(P.P_MAX, nd, rv['t'][-1])
        mv, me = metr(rv, P.P_MAX), metr(re, P.P_MAX)
        if nd == 0.0:
            mv, me = metr(rv, P.P_MAX, False), metr(re, P.P_MAX, False)
            mv['ganho_rad_pu'] = me['ganho_rad_pu'] = None   # sem regime permanente
            mv['ts2'] = me['ts2'] = None
        res['sens_D'].append(dict(D=nd, R_ohm=P.KV*nd/P.KI, **tabela(mv, me)))
        sens[('D', nd)] = (rv, re)
    for nx in (0.30, 0.45, 0.90, 1.20):
        r = le('sens_X_%s' % repr(nx))
        if r is None:
            continue
        pmax = P.E_LINHA*P.V_BAR/nx
        rv = corta(r, evento_degrau(r))
        re = degrau(pmax, P.D, rv['t'][-1])
        mv, me = metr(rv, pmax), metr(re, pmax)
        # janela de 25 s: o 2 % da E01 (~21 s) cai no fim dela; nao entra no criterio
        res['sens_X'].append(dict(X=nx, Pmax=pmax, delta_ini_graus=float(G(math.asin(P.PM0/pmax))),
                                  delta_fim_graus=float(G(math.asin((P.PM0 + P.DPM_DEGRAU)/pmax))),
                                  delta_ini_vhil_graus=float(G(rv['delta'][0])), **tabela(mv, me)))
        sens[('X', nx)] = (rv, re)

    # pior diferenca nas grandezas do criterio
    piores = []
    for blocos in ([res['ensaios'].get('a_degrau', {})] + res['sens_D'] + res['sens_X']):
        for k in ('ganho_rad_pu', 'tp', 'Mp', 'wd'):
            v = blocos.get(k)
            if isinstance(v, dict) and v.get('dif_pct') is not None:
                piores.append(abs(v['dif_pct']))
    res['pior_dif_pct_principais'] = max(piores) if piores else None

    with open(os.path.join(AQUI, 'resultados_typhoon.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=lambda o: None)

    fig_ensaios(curvas)
    fig_sens(sens)
    print(json.dumps(res, indent=1, ensure_ascii=False, default=lambda o: None)[:6000])


# ------------------------------------------------------------------ figuras
def sobrepoe(ax, rv, re, tmax, titulo, rot=True):
    k = re['t'] <= tmax
    ax.plot(re['t'][k], G(re['delta'][k]), color=E.CINZA, lw=2.6, alpha=0.55, label='E01 (RK4)')
    k = rv['t'] <= tmax
    ax.plot(rv['t'][k], G(rv['delta'][k]), color=E.AZUL, lw=1.0, label='equivalente no VHIL')
    ax.set_title(titulo)
    ax.set_xlabel('t [s]')
    ax.set_ylabel('δ [graus]')
    if rot:
        ax.legend(loc='best')
    E.virgula(ax)


def fig_ensaios(c):
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.2))
    if 'a' in c:
        sobrepoe(axs[0, 0], *c['a'], 6.0, '(a) degrau de 0,1 pu em Pm')
    if 'b' in c:
        sobrepoe(axs[0, 1], *c['b'], 6.0, '(b) condição inicial δ(0) = 60°', rot=False)
    ax = axs[1, 0]
    cores = {'c200': E.AQUA, 'c270': E.AMARELO, 'c287': E.VIOLETA, 'c288': E.CRITICO}
    for kk, cor in cores.items():
        if kk not in c:
            continue
        rv, re = c[kk]
        k = re['t'] <= 2.5
        ax.plot(re['t'][k], np.minimum(G(re['delta'][k]), 260), color=E.CINZA, lw=2.6, alpha=0.5)
        k = rv['t'] <= 2.5
        ax.plot(rv['t'][k], np.minimum(G(rv['delta'][k]), 260), color=cor, lw=1.0,
                label='%s ms' % kk[1:] + (' (perde)' if np.max(rv['delta']) > LIM else ''))
    ax.axhline(180, color=E.CRITICO, lw=0.6, ls='--')
    ax.axvspan(P.T_INICIO_FALTA, P.T_INICIO_FALTA + 0.2, color=E.FAIXA, zorder=0)
    ax.set_ylim(0, 260)
    ax.set_title('(c) falta trifásica: Pmax = 0 durante t_f')
    ax.set_xlabel('t [s]'); ax.set_ylabel('δ [graus]'); ax.legend(loc='upper left', title='t_f', fontsize=7)
    E.virgula(ax)
    ax = axs[1, 1]
    if 'a' in c:
        rv, re = c['a']
        ti = np.interp(rv['t'], re['t'], G(re['delta']))
        k = rv['t'] <= 30
        ax.plot(rv['t'][k], G(rv['delta'][k]) - ti[k], color=E.AZUL, lw=0.8)
        ax.set_title('(a) diferença VHIL − E01')
        ax.set_xlabel('t [s]'); ax.set_ylabel('Δδ [graus]')
        E.virgula(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(E.DIR_PNG, 'fig-02-vhil-ensaios.png'))
    plt.close(fig)


def fig_sens(s):
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.9))
    cores = E.rampa(4)
    for ax, par, niveis, rot in ((axs[0], 'D', (0.0, 0.1, 0.441, 1.0), 'D [pu]'),
                                 (axs[1], 'X', (0.30, 0.45, 0.90, 1.20), 'X [pu]')):
        for cor, n in zip(cores, niveis):
            if (par, n) not in s:
                continue
            rv, re = s[(par, n)]
            k = re['t'] <= 5
            ax.plot(re['t'][k], G(re['delta'][k]), color=E.CINZA, lw=2.4, alpha=0.5)
            k = rv['t'] <= 5
            ax.plot(rv['t'][k], G(rv['delta'][k]), color=cor, lw=1.0, label=E.num(n, 3 if n == 0.441 else 2))
        ax.set_title('R4: degrau de 0,1 pu variando %s (cinza: E01)' % par)
        ax.set_xlabel('t após o degrau [s]'); ax.set_ylabel('δ [graus]')
        ax.legend(title=rot, fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.24), ncol=4, frameon=False)
        E.virgula(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(E.DIR_PNG, 'fig-03-vhil-sensibilidade.png'))
    plt.close(fig)


if __name__ == '__main__':
    main()
