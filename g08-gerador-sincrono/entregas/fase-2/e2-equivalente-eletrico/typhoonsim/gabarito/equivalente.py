# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: equivalente eletrico da swing equation.

Executa R1 (escalas, elementos, verificacao de ganho/polos/tau), R3 (os tres ensaios da E01 no
circuito, reconvertidos e sobrepostos ao RK4 da E01) e R4 (sensibilidade a D e X, variados como no
SCADA, e a H, que exige trocar L e recompilar). Gera as figuras de ../relatorio/figuras,
resultados_e02.json e dados/*.csv (gabarito para o TyphoonSim).

A referencia e' a E01: o RK4 de ../../e1-caracterizacao/simulacao/modelo.py, com os mesmos parametros.
O "circuito" aqui e' o gabarito do que o TyphoonSim deve dar: a malha R-L-C exata entre amostras e a
fonte controlada amostrada a cada 100 us (circuito.simula_amostrado).

Uso:  python equivalente.py        (numpy, matplotlib e schemdraw)
"""
import json
import math
import os
import time

import numpy as np

import parametros_e02 as P
import circuito as C
import modelo as M1                       # E01
import estilo as E

AQUI = os.path.dirname(os.path.abspath(__file__))
R01 = json.load(open(os.path.join(P.E01, 'resultados.json'), encoding='utf-8'))
DADOS = os.path.join(AQUI, 'dados')
LIM = math.pi                             # perda de sincronismo: delta > 180 graus
G = np.degrees


def pdif(sim, ref):
    return 100.0*(sim - ref)/abs(ref)


# ============================================================== R1
def r1():
    lin0 = M1.analise_linear()
    # circuito linear (fonte controlada trocada por V = KV*Pm0): RLC serie
    L, R, Cc = P.L_EQ, P.R_EQ, P.C_EQ
    wn = 1/math.sqrt(L*Cc)
    sig = R/(2*L)
    wd = math.sqrt(wn**2 - sig**2)
    ganho_V = 1.0                                  # dv_C/dv_m em regime (o C fica com toda a tensao)
    K_reconv = ganho_V*P.KV/P.KV_DELTA             # rad/pu
    circ = dict(wn=wn, sigma=sig, wd=wd, zeta=sig/wn, tau_env=1/sig, K_V_V=ganho_V, K_rad_pu=K_reconv,
                polos=[-sig, wd])
    e01 = dict(wn=lin0['wn'], sigma=lin0['sigma'], wd=lin0['wd'], zeta=lin0['zeta'],
               tau_env=1/lin0['sigma'], K_rad_pu=lin0['K_rad_pu'])
    dif = {k: pdif(circ[k], e01[k]) for k in e01}
    # faixas de cada variavel nos ensaios (preenchidas em r3) e energia
    return dict(
        escalas=dict(KV_V_pu=P.KV, KI_A_rad_s=P.KI, KT=P.KT, KQ_C_rad=P.KI, KV_delta_V_rad=P.KV_DELTA,
                     KP_W=P.KV*P.KI, KE_J=P.KV*P.KI),
        elementos=dict(L_H=L, R_ohm=R, C_F=Cc, V_m0_V=P.V_M0, V_degrau_V=P.V_DEGRAU,
                       M=P.M, Ks=P.KS, delta0_graus=G(P.DELTA0)),
        circuito_linear=circ, e01_linear=e01, diferenca_pct=dif)


# ============================================================== ensaios
def ensaio_a(sim):
    d1 = math.asin((P.PM0 + P.DPM_DEGRAU)/P.P_MAX)
    r = sim([(120.0, P.PM0 + P.DPM_DEGRAU, P.P_MAX, P.D)])
    m = M1.metricas_degrau(r, P.DELTA0, d1)
    m['ganho_rad_pu'] = (r['delta'][-1] - P.DELTA0)/P.DPM_DEGRAU
    m['valor_final_graus'] = G(r['delta'][-1])
    m['zeta'] = m['sigma']/math.hypot(m['sigma'], m['wd'])
    return r, m


def ensaio_b(sim):
    r = sim([(60.0, P.PM0, P.P_MAX, P.D)], d0=math.radians(P.DELTA_CI_GR))
    tp, yp = M1.picos(r['t'], r['delta'])
    k = r['t'] < tp[0]
    sig = -np.polyfit(tp[:40], np.log(yp[:40] - P.DELTA0), 1)[0]
    return r, dict(T1=float(tp[0]), delta_min_graus=float(G(np.min(r['delta'][k]))), sigma=float(sig),
                   omega_max=float(np.max(np.abs(r['omega']))))


def ensaio_c(sim, tc):
    seg = [(P.T_INICIO_FALTA, P.PM0, P.P_MAX, P.D), (tc, P.PM0, 0.0, P.D), (2.5, P.PM0, P.P_MAX, P.D)]
    r = sim(seg, lim=LIM)
    k = np.searchsorted(r['t'], P.T_INICIO_FALTA + tc - 1e-9)
    return r, dict(duracao=tc, perdeu=bool(r['perdeu'] or np.max(r['delta']) > LIM),
                   delta_elim_graus=float(G(r['delta'][k])), delta_max_graus=float(G(np.max(r['delta']))),
                   omega_max=float(np.max(r['omega'])))


def tcr(sim, a=0.25, b=0.32, tol=1e-4):
    while b - a > tol:
        c = 0.5*(a + b)
        if ensaio_c(sim, c)[1]['perdeu']:
            b = c
        else:
            a = c
    return a, b


# adaptadores: a mesma assinatura para a E01 (RK4) e para o circuito
def sim_e01(seg, d0=P.DELTA0, lim=None):
    return M1.simula([M1.seg(du, Pm=pm, Pmax=px, D=dd) for (du, pm, px, dd) in seg], d0, delta_lim=lim)


def sim_circ(seg, d0=P.DELTA0, lim=None, **kw):
    return C.simula_amostrado(seg, vC0=(d0 - P.DELTA0)*P.KV_DELTA, delta_lim=lim, **kw)


def sim_circ_cont(seg, d0=P.DELTA0, lim=None):
    return C.simula_continuo(seg, vC0=(d0 - P.DELTA0)*P.KV_DELTA, delta_lim=lim)


def r3():
    out = {}
    ref, cir, con = {}, {}, {}
    ref['a'], ma1 = ensaio_a(sim_e01)
    cir['a'], ma2 = ensaio_a(sim_circ)
    con['a'], ma3 = ensaio_a(sim_circ_cont)
    out['a'] = dict(e01=ma1, circuito=ma2, continuo=ma3)
    ref['b'], mb1 = ensaio_b(sim_e01)
    cir['b'], mb2 = ensaio_b(sim_circ)
    con['b'], mb3 = ensaio_b(sim_circ_cont)
    out['b'] = dict(e01=mb1, circuito=mb2, continuo=mb3)
    out['c'] = dict(casos=[])
    ref['c'], cir['c'] = {}, {}
    for tc in P.DURACOES_FALTA:
        ref['c'][tc], c1 = ensaio_c(sim_e01, tc)
        cir['c'][tc], c2 = ensaio_c(sim_circ, tc)
        out['c']['casos'].append(dict(e01=c1, circuito=c2))
    out['c']['tcr_e01'] = R01['R3c'].get('tcr_simulado', None)
    out['c']['tcr_circuito'] = tcr(sim_circ)
    out['c']['tcr_e01_bissecao'] = tcr(sim_e01, tol=1e-5)
    # equivalencia continua (R1b numerica): maior diferenca de delta entre o circuito RK4 e a E01
    out['equivalencia_continua_rad'] = max(float(np.max(np.abs(con[k]['delta'] - ref[k]['delta'])))
                                           for k in ('a', 'b'))
    # diferenca amostra a amostra do circuito amostrado contra a E01 (interpolado na grade da E01)
    out['dif_max_graus'] = {k: float(G(np.max(np.abs(np.interp(ref[k]['t'], cir[k]['t'], cir[k]['delta'])
                                                     - ref[k]['delta'])))) for k in ('a', 'b')}
    # faixas eletricas
    fx = {}
    for k in ('a', 'b'):
        r = cir[k]
        fx[k] = dict(vm=[float(r['vm'].min()), float(r['vm'].max())], vC=[float(r['vC'].min()), float(r['vC'].max())],
                     vnl=[float(r['vnl'].min()), float(r['vnl'].max())], i=[float(r['i'].min()), float(r['i'].max())],
                     vPe=[float(P.KV*r['Pe'].min()), float(P.KV*r['Pe'].max())])
    r = cir['c'][0.27]
    fx['c270'] = dict(vm=[float(r['vm'].min()), float(r['vm'].max())], vC=[float(r['vC'].min()), float(r['vC'].max())],
                      vnl=[float(r['vnl'].min()), float(r['vnl'].max())], i=[float(r['i'].min()), float(r['i'].max())],
                      vPe=[float(P.KV*r['Pe'].min()), float(P.KV*r['Pe'].max())])
    out['faixas'] = fx
    # sensibilidade da implementacao ao passo dos blocos de sinal (escolha de TS_SP)
    var = []
    r1c, c1 = ensaio_c(sim_e01, 0.27)
    for Ts, at in ((1e-3, 0), (1e-4, 0), (1e-4, 1), (2e-5, 0), (2e-5, 1), (5e-6, 0)):
        sim = lambda s, d0=P.DELTA0, lim=None: sim_circ(s, d0, lim, Ts=Ts, atraso=at)
        _, m = ensaio_a(sim)
        r2c, c2 = ensaio_c(sim, 0.27)
        n = min(len(r1c['t']), 2000)
        dif_c = float(G(np.max(np.abs(np.interp(r1c['t'][:n], r2c['t'], r2c['delta']) - r1c['delta'][:n]))))
        var.append(dict(Ts=Ts, atraso=at, sigma=m['sigma'], wd=m['wd'], Mp=m['Mp'],
                        dif_sigma_pct=pdif(m['sigma'], ma1['sigma']), dif_falta270_graus=dif_c,
                        delta_max_falta270=c2['delta_max_graus']))
    out['passo_sinal_e01_delta_max_falta270'] = c1['delta_max_graus']
    out['passo_sinal'] = var
    return out, ref, cir


# ============================================================== R4
def mede_degrau(sim, seg_pre, Pm1, Pmax, dd, janela=60.0):
    """Acomoda (seg_pre) e aplica o degrau de 0,1 pu; mede a partir do degrau."""
    d_ini = math.asin(P.PM0/Pmax)
    d_fim = math.asin(Pm1/Pmax) if Pm1 < Pmax else None
    seg = seg_pre + [(janela if dd > 0.005 else 30.0, Pm1, Pmax, dd)]
    r = sim(seg, lim=LIM)
    t0 = sum(s[0] for s in seg_pre)
    k = r['t'] >= t0 - 1e-12
    rr = dict(t=r['t'][k] - t0, delta=r['delta'][k])
    if d_fim is None or r['perdeu']:
        return dict(perdeu=True)
    m = M1.metricas_degrau(rr, d_ini, d_fim)
    # ganho pelo valor final; com D = 0 nao ha regime permanente e o ganho nao e' definido
    m['ganho_rad_pu'] = (rr['delta'][-1] - d_ini)/P.DPM_DEGRAU if dd > 0 else None
    return m


def r4():
    out = dict(D=[], X=[], H=[])
    Pm1 = P.PM0 + P.DPM_DEGRAU
    for nd in (0.0, 0.01, 0.1, 0.441, 1.0):           # resistor variavel (SCADA): R = KV*D/KI
        mc = mede_degrau(sim_circ, [], Pm1, P.P_MAX, nd)
        e1 = next(x for x in R01['R5']['D'] if abs(x['nivel_D'] - nd) < 1e-12)
        out['D'].append(dict(nivel=nd, R_ohm=P.KV*nd/P.KI, circuito=mc, e01=dict(e1['sim'], ganho_rad_pu=e1['sim'].get('K'))))
    for nx in (0.30, 0.45, 0.60, 0.90, 1.20):          # Pmax = E'V/X no bloco de sinal (SCADA)
        pmax = P.E_LINHA*P.V_BAR/nx
        pre = [] if abs(nx - P.X_TOT) < 1e-12 else [(80.0, P.PM0, pmax, P.D)]   # acomoda no novo equilibrio
        mc = mede_degrau(sim_circ, pre, Pm1, pmax, P.D)
        e1 = next(x for x in R01['R5']['X'] if abs(x['nivel_X'] - nx) < 1e-12)
        out['X'].append(dict(nivel=nx, Pmax=pmax, circuito=mc, e01=dict(e1['sim'], ganho_rad_pu=e1['sim'].get('K'))))
    for nh in (1.0, 2.5, 5.0, 10.0, 25.0):             # L = KV*(2H/ws)/KI: troca do indutor e recompilacao
        el = P.elementos(H_=nh)
        sim = lambda s, d0=P.DELTA0, lim=None, L=el['L']: C.simula_amostrado(s, vC0=(d0 - P.DELTA0)*P.KV_DELTA,
                                                                                L=L, delta_lim=lim)
        mc = mede_degrau(sim, [], Pm1, P.P_MAX, P.D, janela=max(60.0, 12.0*nh))
        e1 = next(x for x in R01['R5']['H'] if abs(x['nivel_H'] - nh) < 1e-12)
        out['H'].append(dict(nivel=nh, L_H=el['L'], circuito=mc, e01=dict(e1['sim'], ganho_rad_pu=e1['sim'].get('K'))))
    # elasticidades (inclinacao log-log entre os niveis vizinhos ao nominal)
    def elast(lista, chave, ia, ib, fonte):
        a, b = lista[ia], lista[ib]
        return math.log(b[fonte][chave]/a[fonte][chave])/math.log(b['nivel']/a['nivel'])
    # inclinacao log-log entre os dois niveis vizinhos ao nominal, a MESMA conta nas duas fontes
    for fonte in ('circuito', 'e01'):
        out['elasticidade_' + fonte] = dict(
            H=dict(wd=elast(out['H'], 'wd', 1, 3, fonte), sigma=elast(out['H'], 'sigma', 1, 3, fonte)),
            D=dict(sigma=elast(out['D'], 'sigma', 1, 2, fonte), Mp=elast(out['D'], 'Mp', 1, 2, fonte)),
            X=dict(ganho=elast(out['X'], 'ganho_rad_pu', 1, 3, fonte), wd=elast(out['X'], 'wd', 1, 3, fonte)))
    return out


# ============================================================== figuras
def fig_circuito():
    import schemdraw
    import schemdraw.elements as elm
    schemdraw.config(fontsize=11, lw=1.2)
    with schemdraw.Drawing(show=False) as d:
        d.config(unit=3.6)
        vm = d.add(elm.SourceV().up().label('$V_m = K_V P_m$\n%s V (+%s V)' % (E.num(P.V_M0, 1), E.num(P.V_DEGRAU, 2)),
                                            loc='bottom', color=E.LARANJA, ofst=0.25))
        d.add(elm.Line().up(1.2))
        d.add(elm.Line().right(0.6))
        d.add(elm.MeterA().right().label('$i \\to \\Delta\\omega$', loc='top', color=E.AZUL))
        d.add(elm.Inductor2().right().label('$L$ = %s H\n(inércia 2H/ω$_s$)' % E.num(P.L_EQ, 4), loc='top'))
        d.add(elm.Line().right(1.0))
        d.add(elm.ResistorVar().right().label('$R$ = %s Ω\n(amortecimento D)' % E.num(P.R_EQ, 2), loc='top'))
        d.add(elm.Line().right(0.6))
        no = d.here
        cap = d.add(elm.Capacitor().down().label('$C$ = %s mF\n(mola linear $K_s$)' % E.num(1e3*P.C_EQ, 3),
                                                 loc='top', ofst=0.25))
        fc = d.add(elm.SourceControlledV().down().reverse().label('$v_{nl}$ = $K_V P_{max}$ sen δ − $v_C$\n(blocos de sinal)',
                                                                  loc='top', color=E.AQUA, ofst=0.25))
        d.add(elm.Line().left().tox(vm.start))
        canto = d.here
        d.add(elm.Line().up().toy(vm.start))
        d.add(elm.Ground().at(canto))
        d.add(elm.Line().at(no).right(3.2))
        d.add(elm.MeterV().down().toy(cap.end).label('$v_C \\to \\delta-\\delta_0$', loc='bottom',
                                                     color=E.AZUL, ofst=0.25))
        d.add(elm.Line().left(3.2))
        fig = d.draw(show=False)
    fig.fig.savefig(os.path.join(E.DIR_PNG, 'fig-01-circuito.png'), dpi=220, bbox_inches='tight',
                    facecolor='white')


def fig_verificacao(R1):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 2.7))
    lin = M1.analise_linear()
    c = R1['circuito_linear']
    for s in (1, -1):
        ax[0].plot(-lin['sigma'], s*lin['wd'], 'o', ms=9, mfc='none', mec=E.LARANJA, mew=1.5,
                   label='E01: linearização em δ$_0$' if s > 0 else None)
        ax[0].plot(-c['sigma'], s*c['wd'], 'x', ms=7, color=E.AZUL, mew=1.5,
                   label='circuito RLC: $-R/2L \\pm j\\sqrt{1/LC-(R/2L)^2}$' if s > 0 else None)
    ax[0].axvline(0, color=E.CINZA, lw=0.6)
    ax[0].set_xlim(-0.6, 0.15); ax[0].set_ylim(-10, 10)
    ax[0].set_xlabel('Re [1/s]'); ax[0].set_ylabel('Im [rad/s]')
    ax[0].set_title('(a) polos: −0,1885 ± j8,3107 1/s nos dois')
    ax[0].legend(loc='center left', fontsize=6.5)
    # resposta linear ao degrau: RLC sem a fonte nao linear x forma fechada da E01
    t = np.linspace(0, 6, 3001)
    dd = M1.degrau_linear(t, P.DPM_DEGRAU, lin)
    # circuito linear: simula com fonte trocada por constante (Pmax*sen -> linearizado): v_nl = KV*Pm0
    L, R, Cc = P.L_EQ, P.R_EQ, P.C_EQ
    Phi, Gam = C.discretiza(R, L, Cc, t[1] - t[0])
    x = np.zeros(2); vc = [0.0]
    for _ in t[1:]:
        x = Phi @ x + Gam*P.V_DEGRAU
        vc.append(x[1])
    ax[1].plot(t, G(np.array(vc)/P.KV_DELTA), color=E.AZUL, lw=2.4, alpha=0.55, label='circuito RLC (v$_C$ reconvertido)')
    ax[1].plot(t, G(dd), '--', color=E.LARANJA, lw=1.1, label='E01: forma fechada linear (7)')
    ax[1].set_xlabel('t [s]'); ax[1].set_ylabel('Δδ [°]')
    ax[1].set_title('(b) degrau de 0,1 pu (%s V): ganho 1 V/V = 0,5455 rad/pu' % E.num(P.V_DEGRAU, 2))
    ax[1].legend(loc='lower right', fontsize=6.5)
    E.virgula(*ax)
    fig.tight_layout()
    E.salva(fig, 'apoio-verificacao-linear')


def fig_validacao(ref, cir, R3):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(10.5, 4.6), gridspec_kw=dict(height_ratios=[2.2, 1]))
    rot = 'circuito: R-L-C exato + fonte controlada a cada %d µs' % round(1e6*P.TS_SP)
    # (a)
    for j, k, T in ((0, 'a', 6), (1, 'b', 6)):
        r1, r2 = ref[k], cir[k]
        ax[0, j].plot(r2['t'], G(r2['delta']), color=E.AZUL, lw=2.6, alpha=0.5, label='equivalente elétrico (reconvertido)')
        ax[0, j].plot(r1['t'], G(r1['delta']), '--', color=E.LARANJA, lw=1.0, label='E01: RK4, h = 1 ms')
        ax[0, j].set_xlim(0, T)
        di = np.interp(r1['t'], r2['t'], r2['delta']) - r1['delta']
        ax[1, j].plot(r1['t'], G(di)*1e3, color=E.TINTA2, lw=0.8)
        ax[1, j].set_xlim(0, 30 if k == 'a' else 30)
        ax[1, j].set_xlabel('t [s]'); ax[1, j].set_ylabel('Δ [m°]')
    ax[0, 0].set_title('(a) degrau 0,80 → 0,90 pu  (V$_m$: %s → %s V)' % (E.num(P.V_M0, 2), E.num(P.V_M0 + P.V_DEGRAU, 2)))
    ax[0, 1].set_title('(b) δ(0) = 60°  (v$_C$(0) = %s V)' % E.num((math.radians(P.DELTA_CI_GR) - P.DELTA0)*P.KV_DELTA, 3))
    ax[0, 0].set_ylabel('δ [°]')
    ax[0, 0].legend(loc='lower right', fontsize=6.5)
    cores = {0.20: E.AZUL, 0.27: E.AQUA, 0.29: E.CRITICO}
    for tc in P.DURACOES_FALTA:
        r1, r2 = ref['c'][tc], cir['c'][tc]
        ax[0, 2].plot(r2['t'], G(r2['delta']), color=cores[tc], lw=2.6, alpha=0.45)
        ax[0, 2].plot(r1['t'], G(r1['delta']), '--', color=E.TINTA, lw=0.8)
        ax[0, 2].text(r2['t'][-1] if tc < 0.29 else 0.9, min(G(r2['delta'][-1]), 175) if tc < 0.29 else 178,
                      '%d ms' % round(1000*tc) + (' (perde)' if tc == 0.29 else ''), fontsize=6.5, color=cores[tc],
                      ha='right', va='bottom')
        n = min(len(r1['t']), 2000)
        di = np.interp(r1['t'][:n], r2['t'], r2['delta']) - r1['delta'][:n]
        if tc < 0.29:
            ax[1, 2].plot(r1['t'][:n], G(di)*1e3, color=cores[tc], lw=0.8, label='%d ms' % round(1000*tc))
    ax[0, 2].set_ylim(0, 185); ax[0, 2].set_xlim(0, 2.6)
    a, b = R3['c']['tcr_circuito']
    ax[0, 2].set_title('(c) falta franca a partir de 0,10 s; t$_{cr}$ = %s–%s ms' % (E.num(1000*a, 1), E.num(1000*b, 1)))
    ax[1, 2].set_xlabel('t [s]'); ax[1, 2].set_ylabel('Δ [m°]'); ax[1, 2].legend(fontsize=6, loc='upper left')
    ax[1, 2].set_xlim(0, 2.6)
    for a_ in ax.flat:
        E.virgula(a_)
    E.rotulo_solver(ax[0, 1], texto=rot)
    fig.tight_layout()
    E.salva(fig, 'apoio-validacao-python')


def fig_faixas(cir):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 2.6), sharey=False)
    for j, (r, tit, T) in enumerate(((cir['a'], '(a) degrau', 6), (cir['b'], '(b) δ(0) = 60°', 6),
                                     (cir['c'][0.27], '(c) falta de 270 ms', 2.6))):
        ax[j].plot(r['t'], r['vm'], color=E.LARANJA, label='V$_m$ (P$_m$)')
        ax[j].plot(r['t'], r['vC'], color=E.AZUL, label='v$_C$ (δ − δ$_0$)')
        ax[j].plot(r['t'], P.KV*r['Pe'], color=E.AQUA, label='v$_C$ + v$_{nl}$ (P$_e$)')
        a2 = ax[j].twinx()
        a2.plot(r['t'], 1000*r['i'], color=E.VIOLETA, lw=0.9, label='i (Δω)')
        a2.set_ylabel('i [mA]', color=E.VIOLETA); a2.tick_params(axis='y', colors=E.VIOLETA)
        a2.grid(False); a2.spines['right'].set_visible(True)
        ax[j].set_xlim(0, T); ax[j].set_title(tit); ax[j].set_xlabel('t [s]')
        ax[j].axhspan(-10, 10, color=E.FAIXA, zorder=-5, lw=0)
        E.virgula(ax[j], a2)
    ax[0].set_ylabel('tensão [V]')
    ax[0].legend(loc='center right', fontsize=6)
    fig.tight_layout()
    E.salva(fig, 'apoio-faixas-eletricas')


def fig_sensibilidade(R4):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 2.9))
    cfg = (('D', 'D [pu/(rad/s)]  →  R = %s·D Ω' % E.num(P.KV/P.KI, 0), [('sigma', 'σ'), ('Mp', 'M$_p$')], ax[0]),
           ('X', 'X [pu]  →  P$_{max}$ = 1,2/X no bloco de sinal', [('ganho_rad_pu', 'K'), ('wd', 'ω$_d$')], ax[1]),
           ('H', 'H [s]  →  L = %s·H H (recompila)' % E.num(P.L_EQ/P.H, 4), [('wd', 'ω$_d$'), ('sigma', 'σ')], ax[2]))
    for chave, xl, metr, a in cfg:
        if chave == 'D':     # sigma e Mp chegam a zero: eixos lineares, valores absolutos
            lst = R4['D']
            niv = np.array([x['nivel'] for x in lst])
            a.plot(niv, [x['e01']['sigma'] for x in lst], 'o', ms=7, mfc='none', mec=E.AZUL, mew=1.3, label='σ [1/s]: E01')
            a.plot(niv, [x['circuito']['sigma'] for x in lst], '-x', color=E.AZUL, lw=1.0, ms=5, label='σ [1/s]: circuito')
            a2 = a.twinx()
            a2.plot(niv, [100*x['e01']['Mp'] for x in lst], 'o', ms=7, mfc='none', mec=E.LARANJA, mew=1.3, label='M$_p$ [%]: E01')
            a2.plot(niv, [100*x['circuito']['Mp'] for x in lst], '-x', color=E.LARANJA, lw=1.0, ms=5, label='M$_p$ [%]: circuito')
            a2.set_ylabel('M$_p$ [%]', color=E.LARANJA); a2.grid(False); a2.spines['right'].set_visible(True)
            a.set_xlabel(xl); a.set_ylabel('σ [1/s]', color=E.AZUL)
            h1, l1 = a.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
            a.legend(h1 + h2, l1 + l2, fontsize=5.8, loc='center right')
            E.virgula(a, a2)
            continue
        lst = [x for x in R4[chave] if not x['circuito'].get('perdeu')]
        niv = np.array([x['nivel'] for x in lst])
        nom = next(x for x in lst if abs(x['nivel'] - {'D': P.D, 'X': P.X_TOT, 'H': P.H}[chave]) < 1e-12)
        for (m, nome), cor in zip(metr, (E.AZUL, E.LARANJA)):
            yc = np.array([x['circuito'][m] or np.nan for x in lst])/nom['circuito'][m]
            ye = np.array([x['e01'][m] if x['e01'].get(m) is not None else np.nan for x in lst])/nom['e01'][m]
            a.plot(niv, ye, 'o', ms=7, mfc='none', mec=cor, mew=1.3, label='%s: E01 (RK4)' % nome)
            a.plot(niv, yc, '-x', color=cor, lw=1.0, ms=5, label='%s: circuito' % nome)
        a.set_xscale('log' if chave != 'D' else 'symlog', **({'linthresh': 0.01} if chave == 'D' else {}))
        a.set_yscale('log')
        from matplotlib.ticker import FuncFormatter, NullFormatter
        for eixo in (a.xaxis, a.yaxis):
            eixo.set_major_formatter(FuncFormatter(lambda v, p: ('%g' % v).replace('.', ',')))
            eixo.set_minor_formatter(NullFormatter())
        a.set_xticks(niv)
        a.set_yticks([0.2, 0.5, 1, 2, 5])
        a.set_xlabel(xl); a.set_ylabel('métrica / nominal')
        a.legend(fontsize=5.8)
    ax[0].set_title('(a) amortecimento — SCADA (σ só com oscilação)')
    ax[1].set_title('(b) reatância — SCADA')
    ax[2].set_title('(c) inércia — troca de L')
    fig.tight_layout()
    E.salva(fig, 'apoio-sensibilidade-python')


def grava_csv(cir):
    os.makedirs(DADOS, exist_ok=True)
    for k, nome in (('a', 'ensaio_a_degrau'), ('b', 'ensaio_b_condicao_inicial')):
        r = cir[k]
        s = slice(None, None, max(1, round(1e-3/P.TS_SP)))          # 1 ms
        np.savetxt(os.path.join(DADOS, nome + '.csv'),
                   np.column_stack([r['t'][s], r['vm'][s], r['i'][s], r['vC'][s], r['vnl'][s],
                                    r['delta'][s], r['omega'][s], r['Pe'][s]]),
                   delimiter=',', fmt='%.9e', comments='',
                   header='t_s,Vm_V,i_A,vC_V,vnl_V,delta_rad,delta_omega_rad_s,Pe_pu')
    for tc, r in cir['c'].items():
        s = slice(None, None, max(1, round(1e-3/P.TS_SP)))
        np.savetxt(os.path.join(DADOS, 'ensaio_c_falta_%03dms.csv' % round(1000*tc)),
                   np.column_stack([r['t'][s], r['vm'][s], r['i'][s], r['vC'][s], r['vnl'][s],
                                    r['delta'][s], r['omega'][s], r['Pe'][s]]),
                   delimiter=',', fmt='%.9e', comments='',
                   header='t_s,Vm_V,i_A,vC_V,vnl_V,delta_rad,delta_omega_rad_s,Pe_pu')


def limpa(o):
    if isinstance(o, dict):
        return {str(k): limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpa(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if (math.isnan(o) or math.isinf(o)) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


if __name__ == '__main__':
    t0 = time.time()
    E.aplica_estilo()
    R1 = r1()
    R3, ref, cir = r3()
    R4 = r4()
    fig_circuito()
    fig_verificacao(R1)
    fig_validacao(ref, cir, R3)
    fig_faixas(cir)
    fig_sensibilidade(R4)
    grava_csv(cir)
    res = limpa(dict(R1=R1, R3=R3, R4=R4, tempo_s=time.time() - t0))
    json.dump(res, open(os.path.join(AQUI, 'resultados_e02.json'), 'w', encoding='utf-8'), indent=1,
              ensure_ascii=False)
    a = R3['a']
    print('R1  L=%.4f H  R=%.3f ohm  C=%.4f mF  | dif. polos/ganho/tau max = %.1e %%' % (
        P.L_EQ, P.R_EQ, 1e3*P.C_EQ, max(abs(v) for v in R1['diferenca_pct'].values())))
    print('R3a ganho %.5f/%.5f  wd %.4f/%.4f  sigma %.4f/%.4f  Mp %.4f/%.4f  ts %.2f/%.2f' % (
        a['circuito']['ganho_rad_pu'], a['e01']['ganho_rad_pu'], a['circuito']['wd'], a['e01']['wd'],
        a['circuito']['sigma'], a['e01']['sigma'], a['circuito']['Mp'], a['e01']['Mp'],
        a['circuito']['ts2'], a['e01']['ts2']))
    print('R3b', R3['b'])
    print('R3c tcr circuito', R3['c']['tcr_circuito'], ' e01', R3['c']['tcr_e01_bissecao'])
    print('equivalencia continua %.2e rad; dif max (graus)' % R3['equivalencia_continua_rad'], R3['dif_max_graus'])
    print('faixas', json.dumps(res['R3']['faixas']))
    print('tempo %.0f s' % (time.time() - t0))
