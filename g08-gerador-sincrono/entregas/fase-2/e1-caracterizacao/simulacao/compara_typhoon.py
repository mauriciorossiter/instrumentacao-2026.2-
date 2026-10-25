# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 01: confronta a simulacao do TyphoonSim (segunda ferramenta)
com o Python (RK4) e com a analise algebrica.

Le typhoonsim/dados/*.csv (gerados por typhoonsim/roda_typhoon.py) e:
  1. reproduz, em Python, o esquema discreto exato dos blocos nativos (Euler simpletico, h = 1 ms)
     e mede a diferenca amostra a amostra: confere que o .tse e' o modelo pretendido;
  2. mede nos dados do Typhoon os mesmos pontos caracteristicos do R3 (mesmas funcoes de modelo.py)
     e compara com o RK4 e com a algebra;
  3. grava resultados_typhoon.json e a figura ../relatorio/figuras/fig-08-typhoon.png.

Uso:  python compara_typhoon.py        (Python comum: numpy e matplotlib; ~10 s)
"""
import os
import sys
import json
import math

sys.dont_write_bytecode = True     # nao cria __pycache__ ao importar modelo/estilo/parametros

import numpy as np
import matplotlib.pyplot as plt

import estilo as E
import modelo as M
from parametros import (W_S, H, D, PM0, P_MAX, DPM_DEGRAU, DELTA_CI_GR, T_INICIO_FALTA,
                        TY_PASSO, TY_T_DEGRAU, TY_DURACOES_FALTA)

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, 'typhoonsim', 'dados')
SAIDA = os.environ.get('G08_TESTE') or AQUI
GR = np.degrees
D0 = math.asin(PM0/P_MAX)
D1 = math.asin((PM0 + DPM_DEGRAU)/P_MAX)
ROTULO = 'TyphoonSim 2026.2: blocos nativos, Euler simplético, h = 1 ms'


def le(nome):
    caminho = os.path.join(DADOS, nome + '.csv')
    if not os.path.exists(caminho):
        sys.exit('falta %s: rode typhoonsim/roda_typhoon.py com a API do Typhoon' % caminho)
    a = np.genfromtxt(caminho, delimiter=',', names=True)
    return {k: a[k].astype(float) for k in a.dtype.names}


def esquema_typhoon(tempo, d_ini, t_deg=None, dpm=0.0, t_f=None, t_c=0.0):
    """Esquema discreto dos blocos nativos do swing_equation.tse (Integrator = Euler progressivo):
         dw[k+1] = dw[k] + h ws/2H (Pm(t_k) - Pmax(t_k) sen(delta[k]) - D dw[k])
         delta[k+1] = delta[k] + h dw[k+1]
    Os degraus valem 1 a partir do instante (t >= t0), como no bloco Step."""
    h, a = TY_PASSO, W_S/(2*H)
    d, w = d_ini, 0.0
    out_d, out_w = np.empty(len(tempo)), np.empty(len(tempo))
    for k, t in enumerate(tempo):
        pm = PM0 + (dpm if (t_deg is not None and t >= t_deg - 1e-9) else 0.0)
        falta = t_f is not None and (t_f - 1e-9) <= t < (t_f + t_c - 1e-9)
        pa = pm - (0.0 if falta else P_MAX)*math.sin(d) - D*w
        out_d[k], out_w[k] = d, w
        w = w + h*a*pa
        d = d + h*w
    return out_d, out_w


def esquema_variante(tempo, d_ini, t_deg, dpm, variante):
    """Ligacoes alternativas dos mesmos integradores nativos (Euler progressivo), para mostrar o efeito
    da discretizacao sobre o amortecimento:
      'explicito': integrador de delta recebe dw[k] direto     -> delta[k+1] = delta[k] + h dw[k]
      'atraso'   : com um Unit Delay nesse caminho (1a montagem) -> delta[k+1] = delta[k] + h dw[k-1]"""
    h, a = TY_PASSO, W_S/(2*H)
    d, w, w_ant = d_ini, 0.0, 0.0
    out = np.empty(len(tempo))
    for k, t in enumerate(tempo):
        pm = PM0 + (dpm if t >= t_deg - 1e-9 else 0.0)
        amort = w_ant if variante == 'atraso' else w
        pa = pm - P_MAX*math.sin(d) - D*amort
        out[k] = d
        d = d + h*(w_ant if variante == 'atraso' else w)
        w_ant, w = w, w + h*a*pa
    return out


def picos_vales(t, y):
    tp, yp = M.picos(t, y)
    tv, yv = M.picos(t, -y)
    return tp, yp, tv, -yv


R = json.load(open(os.path.join(AQUI, 'resultados.json'), encoding='utf-8'))
L0, L1 = R['R2']['linear_delta0'], R['R2']['linear_delta1']
T = {}

# ======================================================================== ensaio (a) degrau
A = le('ensaio_a_degrau')
gd, gw = esquema_typhoon(A['Time'], D0, t_deg=TY_T_DEGRAU, dpm=DPM_DEGRAU)
s = A['Time'] >= TY_T_DEGRAU - 1e-9
ta, da = A['Time'][s] - TY_T_DEGRAU, A['delta_rad'][s]
mA = M.metricas_degrau(dict(t=ta, delta=da), D0, da[-1])
rA = M.simula([M.seg(ta[-1], Pm=PM0 + DPM_DEGRAU)], D0)
dif_a = da - np.interp(ta, rA['t'], rA['delta'])
T['a'] = dict(final_graus=GR(da[-1]), K=(da[-1] - D0)/DPM_DEGRAU, wd=mA['wd'], sigma=mA['sigma'],
              zeta=mA['sigma']/math.hypot(mA['sigma'], mA['wd']), Mp=mA['Mp'], tp=mA['tp'], tr=mA['tr'],
              ts2=mA['ts2'], Pe_max=float(np.max(A['Pe_pu'][s])),
              dif_esquema_rad=float(np.max(np.abs(A['delta_rad'] - gd))),
              dif_esquema_dw=float(np.max(np.abs(A['delta_omega'] - gw))),
              dif_rk4_graus=float(GR(np.max(np.abs(dif_a)))))
# efeito da discretizacao: as duas ligacoes alternativas, no mesmo ensaio (a)
T['variantes'] = {}
for var in ('explicito', 'atraso'):
    dv = esquema_variante(A['Time'], D0, TY_T_DEGRAU, DPM_DEGRAU, var)[s]
    mv = M.metricas_degrau(dict(t=ta, delta=dv), D0, dv[-1])
    T['variantes'][var] = dict(sigma=mv['sigma'], ts2=mv['ts2'], Mp=mv['Mp'],
                               sigma_previsto=L0['sigma'] - (0.5 if var == 'explicito' else 1.0)*L1['wn']**2*TY_PASSO)
T['variantes']['simpletico'] = dict(sigma=mA['sigma'], ts2=mA['ts2'], Mp=mA['Mp'], sigma_previsto=L0['sigma'])

# ======================================================================== ensaio (b) condicao inicial
B = le('ensaio_b_condicao_inicial')
dci = math.radians(DELTA_CI_GR)
gdb, _ = esquema_typhoon(B['Time'], dci)
tb, db = B['Time'], B['delta_rad']
tpb, ypb, tvb, yvb = picos_vales(tb, db)
okb = (ypb - D0) > 1e-6
sig_b = float(-np.polyfit(tpb[okb][:40], np.log(ypb[okb][:40] - D0), 1)[0])
rB = M.simula([M.seg(tb[-1])], dci)
dif_b = db - np.interp(tb, rB['t'], rB['delta'])
T['b'] = dict(T1=float(tpb[0]), delta_min_graus=float(GR(yvb[0])), sigma=sig_b,
              dif_esquema_rad=float(np.max(np.abs(db - gdb))), dif_rk4_graus=float(GR(np.max(np.abs(dif_b)))))

# ======================================================================== ensaio (c) falta
casos_c = []
for tc in TY_DURACOES_FALTA:
    nome = 'ensaio_c_falta_%03dms' % round(1000*tc)
    C = le(nome)
    gdc, _ = esquema_typhoon(C['Time'], D0, t_f=T_INICIO_FALTA, t_c=tc)
    k_el = int(np.argmin(np.abs(C['Time'] - (T_INICIO_FALTA + tc))))
    perdeu = bool(np.max(C['delta_rad']) > math.pi)
    rc = M.simula([M.seg(T_INICIO_FALTA), M.seg(tc, Pmax=0.0), M.seg(C['Time'][-1] - T_INICIO_FALTA - tc)],
                  D0, 0.0, delta_lim=2*math.pi)
    sel = C['delta_rad'] < math.pi                     # compara so enquanto ha sincronismo
    dif = C['delta_rad'][sel] - np.interp(C['Time'][sel], rc['t'], rc['delta'])
    casos_c.append(dict(duracao=tc, nome=nome, C=C, perdeu=perdeu,
                        perdeu_rk4=bool(np.max(rc['delta']) > math.pi),
                        delta_elim_graus=float(GR(C['delta_rad'][k_el])),
                        delta_max_graus=float(GR(np.max(C['delta_rad']))),
                        dif_esquema_rad=float(np.max(np.abs(C['delta_rad'] - gdc)[sel])),
                        dif_rk4_graus=float(GR(np.max(np.abs(dif))))))
estaveis = [c['duracao'] for c in casos_c if not c['perdeu']]
perdidos = [c['duracao'] for c in casos_c if c['perdeu']]
T['c'] = dict(casos=[{k: v for k, v in c.items() if k != 'C'} for c in casos_c],
              tcr_intervalo=[max(estaveis), min(perdidos)],
              tcr_rk4=R['R3c']['tcr_sim_D'], tcr_areas=R['R3c']['tcr_areas'])
T['dif_esquema_max_rad'] = max(T['a']['dif_esquema_rad'], T['b']['dif_esquema_rad'],
                               max(c['dif_esquema_rad'] for c in casos_c))

# referencias para a tabela do relatorio
MA = R['R3a']['medido']
T['referencias'] = dict(
    rk4=dict(final_graus=R['R3a']['valor_final_graus'], K=MA['ganho_rad_pu'], wd=MA['wd'], sigma=MA['sigma'],
             zeta=R['R3a']['zeta_medido'], Mp=MA['Mp'], tp=MA['tp'], tr=MA['tr'], ts2=MA['ts2'],
             T1_b=R['R3b']['T1_sim'], delta_min_b=R['R3b']['delta_min_sim_graus'], sigma_b=R['R3b']['sigma_sim']),
    algebra=dict(final_graus=R['R3a']['delta1_exato_graus'], K=(D1 - D0)/DPM_DEGRAU, wd=L1['wd'], sigma=L1['sigma'],
                 zeta=L1['zeta'], Mp=R['R3a']['Mp_areas_amortecido'], tp=L1['tp'], ts2=L1['ts2_forma_fechada']))
T['solver'] = ROTULO


# ======================================================================== figura
def limpa(o):
    if isinstance(o, dict):
        return {k: limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpa(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.bool_):
        return bool(o)
    return o


E.aplica_estilo()
G = E.num
fig = plt.figure(figsize=(6.7, 5.4))
gs = fig.add_gridspec(2, 2, hspace=0.48, wspace=0.27)
a1, a2, a3, a4 = (fig.add_subplot(gs[i, j]) for i in range(2) for j in range(2))

s3 = ta <= 3.0
a1.plot(rA['t'][rA['t'] <= 3.0], GR(rA['delta'][rA['t'] <= 3.0]), color=E.LARANJA, lw=2.6, alpha=0.45,
        label='Python, RK4')
a1.plot(ta[s3], GR(da[s3]), color=E.AZUL, lw=1.1, label='TyphoonSim')
a1.axhline(GR(da[-1]), color=E.TINTA2, lw=0.8)
a1.plot([mA['tp']], [GR(mA['delta_pico_rad'])], 'o', ms=4.2, color=E.TINTA, zorder=6)
a1.annotate('$t_p$ = %s s; $M_p$ = %s %%' % (G(mA['tp'], 3), G(100*mA['Mp'], 2)),
            (mA['tp'], GR(mA['delta_pico_rad'])), xytext=(5, 2), textcoords='offset points', fontsize=6.6)
a1.set_xlim(0, 3); a1.set_ylim(GR(D0) - 0.5, GR(mA['delta_pico_rad']) + 1.6)
a1.set_xlabel('tempo após o degrau [s]'); a1.set_ylabel(r'$\delta$ [graus]')
a1.set_title('(a) Degrau de 0,10 pu')
a1.legend(loc='upper right', fontsize=6.3, ncol=2)
E.virgula(a1)

s6 = tb <= 6.0
a2.plot(rB['t'][rB['t'] <= 6.0], GR(rB['delta'][rB['t'] <= 6.0]), color=E.LARANJA, lw=2.6, alpha=0.45,
        label='Python, RK4')
a2.plot(tb[s6], GR(db[s6]), color=E.AZUL, lw=1.0, label='TyphoonSim')
a2.plot([tpb[0]], [GR(ypb[0])], 'o', ms=4.2, color=E.TINTA, zorder=6)
a2.annotate('$T_1$ = %s s' % G(tpb[0], 4), (tpb[0], GR(ypb[0])), xytext=(5, 2), textcoords='offset points',
            fontsize=6.6)
a2.plot([tvb[0]], [GR(yvb[0])], 'o', ms=4.2, color=E.TINTA, zorder=6)
a2.annotate('mín. %s°' % G(GR(yvb[0]), 2), (tvb[0], GR(yvb[0])), xytext=(6, -2), textcoords='offset points',
            fontsize=6.6, va='top')
a2.set_xlim(0, 6); a2.set_ylim(-25, 78)
a2.set_xlabel('tempo [s]'); a2.set_ylabel(r'$\delta$ [graus]')
a2.set_title(r'(b) Condição inicial $\delta(0)$ = 60°')
a2.legend(loc='upper right', fontsize=6.3, ncol=2)
E.virgula(a2)

cores = {200: E.RAMPA[1], 270: E.RAMPA[3], 287: E.RAMPA[5], 288: E.CRITICO, 290: '#e88c8c'}
for c in casos_c:
    C = c['C']; ms_ = round(1000*c['duracao'])
    sel = (C['Time'] <= 2.0) & (C['delta_rad'] <= math.radians(205))
    a3.plot(C['Time'][sel], GR(C['delta_rad'][sel]), color=cores.get(ms_, E.AZUL), lw=1.2,
            label='%d ms: %s' % (ms_, '✕ perde' if c['perdeu'] else 'estável'))
    a3.plot([T_INICIO_FALTA + c['duracao']], [c['delta_elim_graus']], 'o', ms=3.4, color=cores.get(ms_, E.AZUL), zorder=6)
a3.axhline(R['R2']['linear_delta0']['delta_u_graus'], color=E.TINTA2, lw=0.8)
a3.text(1.98, R['R2']['linear_delta0']['delta_u_graus'] - 3, r'$\delta_u$', ha='right', va='top', fontsize=6.6,
        color=E.TINTA2)
a3.set_xlim(0, 2.0); a3.set_ylim(-95, 205); a3.set_yticks(range(-90, 181, 45))
a3.set_xlabel('tempo [s]'); a3.set_ylabel(r'$\delta$ [graus]')
a3.set_title(r'(c) Falta: $t_{cr}$ entre %d e %d ms' % (round(1000*max(estaveis)), round(1000*min(perdidos))))
a3.legend(loc='lower right', fontsize=5.9, ncol=2, title='TyphoonSim; ● = eliminação', title_fontsize=5.9)
E.virgula(a3)

a4.semilogy(ta, np.maximum(GR(np.abs(dif_a)), 1e-12), color=E.AZUL, lw=0.5, label='ensaio (a): TyphoonSim − RK4')
a4.semilogy(tb, np.maximum(GR(np.abs(dif_b)), 1e-12), color=E.AQUA, lw=0.5, label='ensaio (b): TyphoonSim − RK4')
erro_esq = GR(np.abs(A['delta_rad'] - gd))[s]
a4.semilogy(ta, np.maximum(erro_esq, 1e-12), color=E.TINTA2, lw=0.5,
            label='ensaio (a): TyphoonSim − esquema discreto')
a4.set_xlim(0, 30); a4.set_ylim(1e-9, 1e3)
a4.set_xlabel('tempo [s]'); a4.set_ylabel(r'$|\Delta\delta|$ [graus]')
a4.set_title('(d) Diferenças absolutas')
a4.legend(loc='upper right', fontsize=5.9)
a4.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: E._fmt_virgula(v)))
for ax in (a1, a2):
    E.rotulo_solver(ax, x=0.01, y=0.02, ha='left', texto='TyphoonSim, h = 1 ms')
E.rotulo_solver(a3, x=0.01, y=0.98, ha='left', va='top', texto='TyphoonSim, h = 1 ms')
fig.suptitle(ROTULO, fontsize=7.5, color=E.TINTA2, y=0.995)
E.salva(fig, 'fig-08-typhoon')

with open(os.path.join(SAIDA, 'resultados_typhoon.json'), 'w', encoding='utf-8') as fh:
    json.dump(limpa(T), fh, indent=1, ensure_ascii=False)

print('Typhoon x esquema discreto: max %.2e rad (todas as sondas de delta)' % T['dif_esquema_max_rad'])
print('(a) wd=%.5f sigma=%.5f Mp=%.4f tp=%.5f ts=%.3f K=%.5f | max|Ty-RK4| = %.4f graus'
      % (T['a']['wd'], T['a']['sigma'], T['a']['Mp'], T['a']['tp'], T['a']['ts2'], T['a']['K'], T['a']['dif_rk4_graus']))
print('(b) T1=%.5f dmin=%.3f sigma=%.5f | max|Ty-RK4| = %.4f graus'
      % (T['b']['T1'], T['b']['delta_min_graus'], T['b']['sigma'], T['b']['dif_rk4_graus']))
for c in T['c']['casos']:
    print('(c) %3d ms: %-7s (RK4: %-7s) elim %.2f graus, max %.1f graus, max|Ty-RK4| %.4f graus'
          % (round(1000*c['duracao']), 'perde' if c['perdeu'] else 'estavel', 'perde' if c['perdeu_rk4'] else 'estavel',
             c['delta_elim_graus'], c['delta_max_graus'], c['dif_rk4_graus']))
print('t_cr Typhoon entre %s e %s s (RK4 %.5f; areas D=0 %.5f)' % (T['c']['tcr_intervalo'][0], T['c']['tcr_intervalo'][1],
                                                                  T['c']['tcr_rk4'], T['c']['tcr_areas']))
for var, v in T['variantes'].items():
    print('variante %-10s sigma=%.5f (previsto %.5f) ts=%.2f s Mp=%.4f' % (var, v['sigma'], v['sigma_previsto'], v['ts2'], v['Mp']))
