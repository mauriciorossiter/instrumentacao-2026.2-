# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 01: caracterizacao da planta no dominio de origem.
Gerador sincrono - barramento infinito (swing equation), modelo classico.

Script unico. Executa, nesta ordem:
  R2  analise algebrica (equilibrios, linearizacao rotulada, energia, criterio das areas)
  R3  ensaios simulados: (a) degrau de Pm, (b) condicao inicial, (c) falta temporaria
  R4  validacao cruzada algebra x simulacao + verificacao numerica (energia, convergencia)
  R5  sensibilidade parametrica (H, D, X) + "e se...?" de amplitude e condicao inicial
e grava:
  ../relatorio/figuras/fig-01 ... fig-07 e fig-09 ... fig-12 (PNG; a fig-08 vem de compara_typhoon.py)
  resultados.json   (todos os numeros citados no relatorio)
  dados/ensaio_a_degrau.csv, ensaio_b_condicao_inicial.csv, ensaio_c_falta.csv

Uso:  python caracterizacao.py        (~1 min; so precisa de numpy e matplotlib)
"""
import os
import sys
import csv
import json
import math
import time
import platform

sys.dont_write_bytecode = True     # nao cria __pycache__ ao importar modelo/estilo/parametros

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

import estilo as E
import modelo as M
from parametros import (W_S, F_REDE, H, D, PM0, P_MAX, E_LINHA, V_BAR, X_TOT, PASSO,
                        DPM_DEGRAU, DELTA_CI_GR, T_INICIO_FALTA, DURACOES_FALTA,
                        NIVEIS_H, NIVEIS_D, NIVEIS_X, NIVEIS_DPM, CI_DOMINIO_GR)

AQUI = os.path.dirname(os.path.abspath(__file__))
# modo de teste (G08_TESTE=<pasta>): figuras, resultados.json e dados/ vao para essa pasta
SAIDA = os.environ.get('G08_TESTE') or AQUI
DIR_DADOS = os.path.join(SAIDA, 'dados')
GR = np.degrees      # escalares e vetores
RAD = np.radians
PI = math.pi
R = {}
t_inicio = time.time()


def dif_pc(ref, val):
    """Diferenca percentual de val em relacao a ref."""
    if ref is None or val is None or ref == 0 or not np.isfinite(ref) or not np.isfinite(val):
        return None
    return 100.0*(val - ref)/abs(ref)


def tcr_simulado(H=H, D=D, Pm=PM0, Pmax=P_MAX, t_pos=5.0, tol=1e-6):
    """Tempo critico de eliminacao por bissecao em simulacao (Pe = 0 durante a falta)."""
    if D < 0:
        return 0.0      # equilibrio instavel: qualquer perturbacao cresce
    d0 = math.asin(Pm/Pmax)
    def estavel(tc):
        r = M.simula([M.seg(tc, Pm, 0.0, H, D), M.seg(t_pos, Pm, Pmax, H, D)], d0, 0.0,
                     delta_lim=PI, registrar=False)
        return not r['perdeu']
    lo, hi = 0.0, 0.05
    while estavel(hi):
        lo, hi = hi, 2*hi
        if hi > 20.0:
            return math.inf
    while hi - lo > tol:
        mid = 0.5*(lo + hi)
        if estavel(mid):
            lo = mid
        else:
            hi = mid
    return 0.5*(lo + hi)


def degrau_critico_simulado(H=H, D=D, Pm0=PM0, Pmax=P_MAX, t_sim=15.0, tol=1e-6):
    """Maior degrau de Pm que preserva o sincronismo, por bissecao em simulacao."""
    d0 = math.asin(Pm0/Pmax)
    def estavel(dp):
        r = M.simula([M.seg(t_sim, Pm0 + dp, Pmax, H, D)], d0, 0.0, delta_lim=PI, registrar=False)
        return not r['perdeu']
    lo, hi = 0.0, Pmax - Pm0
    while hi - lo > tol:
        mid = 0.5*(lo + hi)
        if estavel(mid):
            lo = mid
        else:
            hi = mid
    return 0.5*(lo + hi)


def taxa_cauda(r, d_fim, A):
    """Taxa de decaimento dominante medida na cauda monotona (respostas sem oscilacao)."""
    dev = np.abs(r['delta'] - d_fim)
    ok = (dev < 1e-3*abs(A)) & (dev > 1e-9*abs(A))
    if np.count_nonzero(ok) < 20:
        return None
    return float(-np.polyfit(r['t'][ok], np.log(dev[ok]), 1)[0])


def ensaio_degrau(H=H, D=D, X=X_TOT, Pm0=PM0, dPm=DPM_DEGRAU, T=None):
    """Degrau dPm a partir do equilibrio: previsao algebrica e medicao na simulacao."""
    Pmax = E_LINHA*V_BAR/X
    lin = M.analise_linear(Pm0, Pmax, H, D)
    d0 = lin['delta_s_rad']
    taxa = lin['taxa_dominante']
    if T is None:   # horizonte longo: o residuo e^(-taxa*T) nao contamina o valor final
        T = 60.0 if taxa <= 0 else min(600.0, max(60.0, 30.0/taxa))
    r = M.simula([M.seg(T, Pm0 + dPm, Pmax, H, D)], d0, 0.0, delta_lim=PI)
    out = dict(H=H, D=D, X=X, Pm0=Pm0, Pmax=Pmax, dPm=dPm, T_sim=T, previsao=lin, r=r,
               perdeu=r['perdeu'], delta0_rad=d0)
    pos = M.analise_linear(Pm0 + dPm, Pmax, H, D)
    out['existe_equilibrio_final'] = pos['existe']
    if r['perdeu']:
        out['t_perda'] = r['t_fim']
        return out
    d_fim = r['delta'][-1] if taxa > 0 else math.asin((Pm0 + dPm)/Pmax)
    m = M.metricas_degrau(r, d0, d_fim)
    if taxa <= 0:
        m['ts2'] = math.inf
    m['ganho_rad_pu'] = (d_fim - d0)/dPm
    if m['Mp'] is not None and m['Mp'] > 0.01:
        m['taxa_dom'] = m['sigma']
    else:
        m['taxa_dom'] = taxa_cauda(r, d_fim, d_fim - d0)
        m['wd'] = None
    out['medido'] = m
    out['K_exato_rad_pu'] = (math.asin((Pm0 + dPm)/Pmax) - d0)/dPm
    return out


# ============================================================================ R2 - algebra
op = M.ponto_de_operacao()
lin0 = M.analise_linear()
d0, du = lin0['delta_s_rad'], lin0['delta_u_rad']
Pm1 = PM0 + DPM_DEGRAU
d1 = math.asin(Pm1/P_MAX)
du1 = PI - d1
lin1 = M.analise_linear(Pm1)
falta = M.criterio_areas_falta()
dpm_cr_areas = M.degrau_critico_areas()
sep_x, sep_w, dL, _, Ecr = M.separatriz()
V0 = float(M.potencial(d0))
Vcr = Ecr - V0
S_ILUSTR = 100e6                                   # VA, base ilustrativa (nao e' dado do sistema)
J_ilustr = 2*H*S_ILUSTR/W_S**2                     # kg.m2 para maquina de 2 polos (Omega_ms = ws)
Mr = 1.0/(2*lin0['zeta']*math.sqrt(1 - lin0['zeta']**2))
wr = lin0['wn']*math.sqrt(1 - 2*lin0['zeta']**2)

R['ambiente'] = dict(python=platform.python_version(), numpy=np.__version__,
                     matplotlib=matplotlib.__version__, sistema=platform.platform(),
                     solver='RK4 classico, passo fixo', passo_s=PASSO)
R['parametros'] = dict(f=F_REDE, ws=W_S, H=H, E_linha=E_LINHA, V=V_BAR, X=X_TOT, D=D,
                       D_pu_por_pu=D*W_S, Pm0=PM0, Pmax=P_MAX)
R['R2'] = dict(ponto_operacao=op, linear_delta0=lin0, linear_delta1=lin1,
               falta_areas=falta, degrau_critico_areas_pu=dpm_cr_areas,
               delta_L_rad=dL, delta_L_graus=GR(dL), energia_critica=Vcr,
               omega_max_separatriz=float(np.max(sep_w)),
               ressonancia_Mr=Mr, ressonancia_wr=wr, ganho_ressonancia_rad_pu=Mr*lin0['K_rad_pu'],
               J_ilustrativo_kgm2=J_ilustr, S_ilustrativa_VA=S_ILUSTR,
               ft_num=lin0['num_ganho'], ft_den=lin0['den'])

# ============================================================================ R3 (a) degrau
T_A = 120.0
rA = M.simula([M.seg(T_A, Pm=Pm1)], d0)
dfA = float(rA['delta'][-1])
mA = M.metricas_degrau(rA, d0, dfA)
mA['ganho_rad_pu'] = (dfA - d0)/DPM_DEGRAU
rA0 = M.simula([M.seg(30.0, Pm=Pm1, D=0.0)], d0)                  # D = 0: confere areas/energia
tpkA0, ypkA0 = M.picos(rA0['t'], rA0['delta'])
EA = float(M.potencial(d0, Pm1))
TA_en, _, dmaxA_en = M.periodo_energia(EA, Pm1)
dmaxA_areas = M.delta_max_areas(Pm1, d0)
Mp_areas = (dmaxA_areas - d1)/(d1 - d0)
Mp_areas_amort = Mp_areas*math.exp(-lin0['sigma']*TA_en/2)       # correcao do amortecimento no 1o meio-ciclo
R['R3a'] = dict(dPm=DPM_DEGRAU, Pm1=Pm1, T_sim=T_A, delta1_exato_rad=d1, delta1_exato_graus=GR(d1),
                delta_u1_graus=GR(du1), medido=mA, valor_final_graus=GR(dfA),
                zeta_medido=mA['sigma']/math.hypot(mA['sigma'], mA['wd']),
                omega_max_rad_s=float(np.max(np.abs(rA['omega']))),
                Pe_max_pu=float(np.max(rA['Pe'])),
                D0=dict(delta_pico_sim_rad=float(ypkA0[0]), delta_pico_areas_rad=dmaxA_areas,
                        erro_pico_graus=GR(float(ypkA0[0]) - dmaxA_areas),
                        T_sim=float(np.mean(np.diff(tpkA0[:11]))), T_energia=TA_en,
                        Mp_areas=Mp_areas),
                Mp_areas_amortecido=Mp_areas_amort,
                wd_energia=2*PI/TA_en)

# ============================================================================ R3 (b) condicao inicial
dci = RAD(DELTA_CI_GR)
rB = M.simula([M.seg(60.0)], dci, 0.0)
rB0 = M.simula([M.seg(30.0, D=0.0)], dci, 0.0)
EB = float(M.potencial(dci))
TB_en, dminB_en, _ = M.periodo_energia(EB)
tpB, ypB = M.picos(rB['t'], rB['delta'])
tvB, yvB = M.picos(rB['t'], -rB['delta'])
tpB0, _ = M.picos(rB0['t'], rB0['delta'])
tvB0, yvB0 = M.picos(rB0['t'], -rB0['delta'])
okB = (ypB - d0) > 1e-6
sigB = float(-np.polyfit(tpB[okB][:40], np.log(ypB[okB][:40] - d0), 1)[0])
WB0 = M.energia(rB0['delta'], rB0['omega'])
WB = M.energia(rB['delta'], rB['omega']) + rB['Ed']
rB10 = M.simula([M.seg(60.0)], dci, 0.0, passo=1e-2)
WB10 = M.energia(rB10['delta'], rB10['omega']) + rB10['Ed']
R['R3b'] = dict(delta_ci_graus=DELTA_CI_GR, T_sim=60.0, energia_inicial=EB - V0,
                fracao_energia_critica=(EB - V0)/Vcr,
                T1_sim=float(tpB[0]), T1_sim_D0=float(tpB0[0]), T_energia=TB_en, T_linear=lin0['Td'],
                delta_min_sim_graus=GR(-float(yvB[0])), delta_min_sim_D0_graus=GR(-float(yvB0[0])),
                delta_min_energia_graus=GR(dminB_en), delta_min_linear_graus=GR(2*d0 - dci),
                # energia (D = 0) com a correcao do amortecimento no 1o meio-ciclo (como no Mp do ensaio a)
                delta_min_energia_amort_graus=GR(d0 - (d0 - dminB_en)*math.exp(-lin0['sigma']*TB_en/2)),
                t_min_sim=float(tvB[0]), sigma_sim=sigB,
                valor_final_graus=GR(float(rB['delta'][-1])),
                omega_max_rad_s=float(np.max(np.abs(rB['omega']))),
                residuo_energia_D0=float(np.max(np.abs(WB0 - WB0[0]))/Vcr),
                residuo_energia_D=float(np.max(np.abs(WB - WB[0]))/Vcr),
                residuo_energia_D_h10ms=float(np.max(np.abs(WB10 - WB10[0]))/Vcr))

# convergencia do RK4: erro de delta(10 s) contra passo de referencia 0,1 ms
ref10 = M.simula([M.seg(10.0)], dci, 0.0, passo=1e-4, registrar=False)['delta_fim']
conv = []
for h in (0.04, 0.02, 0.01, 0.005, 0.002, 0.001, 0.0005):
    dh = M.simula([M.seg(10.0)], dci, 0.0, passo=h, registrar=False)['delta_fim']
    conv.append(dict(h=h, erro_rad=abs(dh - ref10)))
ordem = np.polyfit(np.log([c['h'] for c in conv[:5]]), np.log([c['erro_rad'] for c in conv[:5]]), 1)[0]
# custo computacional (nota de viabilidade de tempo real): segundos de CPU por segundo simulado
t_cpu = time.perf_counter()
M.simula([M.seg(60.0)], dci, 0.0, registrar=False)
custo = (time.perf_counter() - t_cpu)/60.0
R['R4_numerico'] = dict(convergencia=conv, ordem_observada=float(ordem),
                        estabilidade_rk4_h_max=2.785/lin0['wn'],
                        amostras_por_periodo=lin0['Td']/PASSO,
                        cpu_por_s_simulado=custo, fator_tempo_real=1.0/custo)

# ============================================================================ R3 (c) falta temporaria
tf = T_INICIO_FALTA
casosC = []
for tc in DURACOES_FALTA:
    r = M.simula([M.seg(tf), M.seg(tc, Pmax=0.0), M.seg(2.5)], d0, 0.0, delta_lim=2*PI)
    k = np.where(np.isclose(r['t'], tf + tc, atol=1e-12))[0][0]
    dc_fech, wc_fech = M.trajetoria_falta(tc, d0)
    caso = dict(duracao=tc, perdeu=bool(r['perdeu'] or np.max(r['delta']) > PI), r=r,
                delta_elim_graus=GR(float(r['delta'][k])), omega_elim=float(r['omega'][k]),
                erro_forma_fechada_rad=abs(float(r['delta'][k]) - float(dc_fech)),
                delta_max_graus=GR(float(np.max(r['delta']))),
                omega_max=float(np.max(np.abs(r['omega']))))
    if caso['perdeu']:
        i_pi = np.where(r['delta'] > PI)[0][0]
        caso['t_180'] = float(r['t'][i_pi])
    casosC.append(caso)
tcr_s = tcr_simulado()
tcr_s0 = tcr_simulado(D=0.0)
dcr_s0 = GR(float(M.trajetoria_falta(tcr_s0, d0, D=0.0)[0]))
R['R3c'] = dict(t_inicio=tf, casos=[{k: v for k, v in c.items() if k != 'r'} for c in casosC],
                tcr_areas=falta['t_cr'], delta_cr_areas_graus=falta['delta_cr_graus'],
                tcr_sim_D0=tcr_s0, tcr_sim_D=tcr_s, delta_cr_sim_D0_graus=dcr_s0,
                A1=falta['A1'], A2=falta['A2'],
                omega_elim_tcr=float(M.trajetoria_falta(tcr_s, d0)[1]))

# ============================================================================ R5 - sensibilidade
print('R5: sensibilidade ...')
sensH = [ensaio_degrau(H=v) for v in NIVEIS_H]
sensD = [ensaio_degrau(D=v, T=(80.0 if v <= 0 else None)) for v in NIVEIS_D]
sensX = [ensaio_degrau(X=v) for v in NIVEIS_X]
for c in sensH:
    c['tcr_areas'] = M.criterio_areas_falta(PM0, P_MAX, c['H'])['t_cr']
    c['tcr_sim'] = tcr_simulado(H=c['H'])
for c in sensD:
    c['tcr_areas'] = falta['t_cr']
    c['tcr_sim'] = tcr_simulado(D=c['D'])
for c in sensX:
    c['tcr_areas'] = M.criterio_areas_falta(PM0, c['Pmax'])['t_cr']
    c['tcr_sim'] = tcr_simulado(Pmax=c['Pmax'])
# D < 0: instante da perda de sincronismo e previsao pela taxa de crescimento da energia
cDneg = sensD[0]
lin_neg1 = M.analise_linear(Pm1, P_MAX, H, NIVEIS_D[0])
E_ini_neg = float(M.potencial(d0, Pm1) - M.potencial(d1, Pm1))
E_cr_neg = float(M.potencial(du1, Pm1) - M.potencial(d1, Pm1))
t_perda_prev = math.log(E_cr_neg/E_ini_neg)/(2*abs(lin_neg1['sigma']))

# amplitude do degrau ("e se...?")
sensA = []
for dp in NIVEIS_DPM:
    c = ensaio_degrau(dPm=dp)
    Pm1a = PM0 + dp
    d1a = math.asin(Pm1a/P_MAX)
    Ta, _, _ = M.periodo_energia(float(M.potencial(d0, Pm1a)), Pm1a)
    dma = M.delta_max_areas(Pm1a, d0)
    c['previsao_nl'] = dict(K=(d1a - d0)/dp, wd=2*PI/Ta, T=Ta,
                            Mp=(dma - d1a)/(d1a - d0)*math.exp(-lin0['sigma']*Ta/2))
    sensA.append(c)
dpm_cr_sim = degrau_critico_simulado()
dpm_cr_sim0 = degrau_critico_simulado(D=0.0)
casos_cr = []
for dp in (dpm_cr_sim - 0.005, dpm_cr_sim + 0.005):
    r = M.simula([M.seg(6.0, Pm=PM0 + dp)], d0, 0.0, delta_lim=2*PI)
    casos_cr.append(dict(dPm=dp, r=r, perdeu=bool(np.max(r['delta']) > PI),
                         delta_max_graus=GR(float(np.max(r['delta'])))))
# condicao inicial dos dois lados de delta_u
casos_ci = []
for g in CI_DOMINIO_GR:
    x0 = RAD(g)
    r = M.simula([M.seg(12.0)], x0, 0.0, delta_lim=2*PI)
    Ei = float(M.potencial(x0)) - V0
    Tg, dming, _ = M.periodo_energia(float(M.potencial(x0)))
    caso = dict(delta0_graus=g, r=r, perdeu=bool(np.max(r['delta']) > PI),
                energia=Ei, fracao_critica=Ei/Vcr, T_energia=Tg,
                delta_min_energia_graus=(GR(dming) if dming is not None else None))
    if caso['perdeu']:
        caso['t_180'] = float(r['t'][np.where(r['delta'] > PI)[0][0]])
    else:
        tpk, _ = M.picos(r['t'], r['delta'])
        tvl, yvl = M.picos(r['t'], -r['delta'])
        caso['T1_sim'] = float(tpk[0])
        caso['delta_min_sim_graus'] = GR(-float(yvl[0]))
    casos_ci.append(caso)


# ---------------------------------------------------------------- sintese: elasticidades
def metricas_algebricas(H=H, D=D, X=X_TOT, Pm0=PM0):
    Pmax = E_LINHA*V_BAR/X
    lin = M.analise_linear(Pm0, Pmax, H, D)
    return dict(K=lin['K_rad_pu'], wd=lin['wd'], sigma=lin['sigma'], zeta=lin['zeta'],
                Mp=lin['Mp'], tcr=M.criterio_areas_falta(Pm0, Pmax, H)['t_cr'],
                margem=1.0 - Pm0/Pmax, dpm_cr=M.degrau_critico_areas(Pm0, Pmax))


def metricas_simuladas(H=H, D=D, X=X_TOT, Pm0=PM0):
    c = ensaio_degrau(H=H, D=D, X=X, Pm0=Pm0, dPm=0.01)
    m = c['medido']
    zeta = m['sigma']/math.hypot(m['sigma'], m['wd'])
    return dict(K=m['ganho_rad_pu'], wd=m['wd'], sigma=m['sigma'], zeta=zeta, Mp=m['Mp'],
                tcr=tcr_simulado(H=H, D=D, Pm=Pm0, Pmax=c['Pmax']),
                dpm_cr=degrau_critico_simulado(H=H, D=D, Pm0=Pm0, Pmax=c['Pmax']))


NOMINAL = dict(H=H, D=D, X=X_TOT, Pm0=PM0)
elast_alg, elast_sim = {}, {}
for p in ('H', 'D', 'X', 'Pm0'):
    q = 1e-4
    mais = metricas_algebricas(**{**NOMINAL, p: NOMINAL[p]*(1 + q)})
    menos = metricas_algebricas(**{**NOMINAL, p: NOMINAL[p]/(1 + q)})
    elast_alg[p] = {k: math.log(mais[k]/menos[k])/math.log((1 + q)**2) for k in mais}
    q = 0.10
    mais = metricas_simuladas(**{**NOMINAL, p: NOMINAL[p]*(1 + q)})
    menos = metricas_simuladas(**{**NOMINAL, p: NOMINAL[p]/(1 + q)})
    elast_sim[p] = {k: math.log(mais[k]/menos[k])/math.log((1 + q)**2) for k in mais}


def resumo_sens(c):
    lin = c['previsao']
    s = dict(nivel_H=c['H'], nivel_D=c['D'], nivel_X=c['X'], Pmax=c['Pmax'], dPm=c['dPm'],
             delta0_graus=GR(c['delta0_rad']), perdeu=c['perdeu'],
             existe_equilibrio_final=c['existe_equilibrio_final'],
             prev=dict(K=lin['K_rad_pu'], wn=lin['wn'], wd=lin['wd'], zeta=lin['zeta'],
                       sigma=lin['sigma'], taxa_dom=lin['taxa_dominante'], Mp=lin['Mp'],
                       ts2=lin.get('ts2_forma_fechada'), regime=lin['regime'], polos=lin['polos']),
             tcr_areas=c.get('tcr_areas'), tcr_sim=c.get('tcr_sim'))
    # linearizacao no equilibrio FINAL delta_1: e' ela que governa a oscilacao/cauda apos o degrau
    l1 = M.analise_linear(c['Pm0'] + c['dPm'], c['Pmax'], c['H'], c['D'])
    if l1['existe']:
        s['prev_delta1'] = dict(K_exato=c['K_exato_rad_pu'] if 'K_exato_rad_pu' in c else None,
                                wd=l1['wd'], zeta=l1['zeta'], sigma=l1['sigma'],
                                taxa_dom=l1['taxa_dominante'], regime=l1['regime'],
                                ts2=l1.get('ts2_forma_fechada'), polos=l1['polos'])
    if c['perdeu']:
        s['t_perda'] = c['t_perda']
    else:
        m = c['medido']
        s['sim'] = dict(K=m['ganho_rad_pu'], wd=m['wd'], sigma=m['sigma'], taxa_dom=m['taxa_dom'],
                        Mp=m['Mp'], ts2=m['ts2'], tp=m['tp'])
        s['K_exato'] = c['K_exato_rad_pu']
    if 'previsao_nl' in c:
        s['prev_nl'] = c['previsao_nl']
    return s


R['R5'] = dict(H=[resumo_sens(c) for c in sensH], D=[resumo_sens(c) for c in sensD],
               X=[resumo_sens(c) for c in sensX], amplitude=[resumo_sens(c) for c in sensA],
               D_negativo=dict(t_perda_sim=cDneg.get('t_perda'), t_perda_prev_energia=t_perda_prev,
                               taxa_crescimento=-lin_neg1['sigma']),
               D_critico_delta0=2*math.sqrt(2*H*lin0['Ps']/W_S),
               D_critico_delta1=2*math.sqrt(2*H*lin1['Ps']/W_S),
               degrau_critico=dict(areas_D0=dpm_cr_areas, sim_D0=dpm_cr_sim0, sim_D=dpm_cr_sim,
                                   casos=[{k: v for k, v in c.items() if k != 'r'} for c in casos_cr]),
               condicao_inicial=[{k: v for k, v in c.items() if k != 'r'} for c in casos_ci],
               elasticidade_algebrica=elast_alg, elasticidade_simulada=elast_sim)
print('calculos concluidos em %.1f s; gerando figuras ...' % (time.time() - t_inicio))

# ============================================================================ figuras
E.aplica_estilo()
G = E.num


def marca(ax, x, y, texto=None, dx=0, dy=0, ha='left', va='bottom', cor=E.TINTA, aberto=False,
          ms=4.6, fs=7.0, z=7):
    ax.plot([x], [y], 'o', ms=ms, mfc=('white' if aberto else cor), mec=cor, mew=1.0, zorder=z)
    if texto:
        ax.annotate(texto, (x, y), xytext=(dx, dy), textcoords='offset points', ha=ha, va=va,
                    fontsize=fs, color=E.TINTA, zorder=z + 1)


def caixa_texto(ax, x, y, s, ha='left', va='top', fs=7.0):
    ax.text(x, y, s, transform=ax.transAxes, ha=ha, va=va, fontsize=fs, color=E.TINTA,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=E.GRADE, lw=0.5), zorder=9)


def eixo_log(ax, ticks_x, ticks_y):
    fmt = FuncFormatter(lambda v, p: E._fmt_virgula(v))
    ax.xaxis.set_major_locator(FixedLocator(ticks_x)); ax.xaxis.set_major_formatter(fmt)
    ax.yaxis.set_major_locator(FixedLocator(ticks_y)); ax.yaxis.set_major_formatter(fmt)
    ax.xaxis.set_minor_formatter(NullFormatter()); ax.yaxis.set_minor_formatter(NullFormatter())


# ----------------------------------------------------------------------------- fig 01
def fig01():
    fig = plt.figure(figsize=(6.7, 5.05))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 100); ax.set_ylim(0, 75.4); ax.axis('off')
    oy = 3.0     # deslocamento vertical do painel (a)
    T, T2 = E.TINTA, E.TINTA2

    def caixa(x, y, w, h, txt, fs=7.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.0',
                                    fc='white', ec=T2, lw=0.9, zorder=3))
        ax.text(x + w/2, y + h/2, txt, ha='center', va='center', fontsize=fs, color=T, zorder=4,
                linespacing=1.3)

    def seta(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), zorder=2,
                    arrowprops=dict(arrowstyle='-|>', color=T, lw=0.9, shrinkA=0, shrinkB=0,
                                    mutation_scale=8))

    def linha(xs, ys):
        ax.plot(xs, ys, color=T, lw=0.9, solid_capstyle='butt', zorder=2)

    def ponto(x, y):
        ax.plot([x], [y], 'o', ms=3.0, color=T, zorder=5)

    def txt(x, y, s, ha='center', va='center', fs=7.4, cor=T, **kw):
        ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=cor, zorder=5, **kw)

    # (a) sistema fisico
    txt(1, 70.4 + oy, '(a) Sistema físico: máquina síncrona ligada a barramento infinito (SMIB), '
        'modelo clássico', ha='left', fs=8.2, weight='bold')
    caixa(2, 47 + oy, 14, 11, 'Turbina\n(vapor)')
    seta(16.6, 52.5 + oy, 24.0, 52.5 + oy)
    txt(20.3, 54.7 + oy, r'$P_m$', fs=8)
    txt(20.3, 50.2 + oy, 'entrada', fs=6.3, cor=T2)
    caixa(24.4, 45 + oy, 20, 15, 'Gerador síncrono\n' + r"$E'\angle\delta$ atrás de $X'_d$" + '\n' +
          r'$H = 5$ s,  $D$')
    seta(34.4, 60.5 + oy, 34.4, 65.4 + oy)
    txt(35.6, 63.6 + oy, r'saídas: $\delta$,  $\Delta\omega$', ha='left', fs=7.2)
    linha([44.8, 52.0], [52.5 + oy, 52.5 + oy])
    txt(48.4, 54.5 + oy, r'$P_e$', fs=8)
    caixa(52, 48 + oy, 17, 9, 'Transformador\n+ linha  ' + r'$(X_e)$')
    linha([69.4, 82.0], [52.5 + oy, 52.5 + oy])
    ax.plot([82.6, 82.6], [44 + oy, 61 + oy], color=T, lw=2.6, solid_capstyle='butt', zorder=3)
    txt(84.2, 52.5 + oy, 'Barramento\ninfinito\n' + r'$V\angle 0^\circ$,  60 Hz', ha='left', fs=7.4)
    txt(48.0, 43.4 + oy, r"$X = X'_d + X_e = 0{,}60$ pu", fs=7.2, cor=T2)
    ax.plot([75.4, 73.8, 76.4, 74.6], [52.3 + oy, 49.4 + oy, 48.6 + oy, 45.6 + oy], color=T,
            lw=1.1, zorder=4)
    seta(74.9, 46.6 + oy, 74.4, 44.8 + oy)
    txt(75.5, 41.4 + oy, 'distúrbio: falta / chaveamento\n(altera X e, portanto, ' + r'$P_{max}$)',
        fs=6.6, cor=T2)

    # (b) diagrama de blocos
    txt(1, 38.9, r'(b) Diagrama de blocos (forma A: $\Delta\omega$ em rad/s, potências em pu)',
        ha='left', fs=8.2, weight='bold')
    y = 21.0
    txt(3.0, y + 1.8, r'$P_m$', fs=8)
    seta(1.5, y, 10.5, y)
    ax.add_patch(Circle((12.5, y), 2.0, fc='white', ec=T, lw=0.9, zorder=3))
    txt(12.5, y, r'$\Sigma$', fs=7.4)
    txt(9.5, y + 2.6, '+', fs=7.5); txt(14.9, y + 3.1, '−', fs=8); txt(14.9, y - 3.2, '−', fs=8)
    seta(14.5, y, 19.0, y)
    txt(16.7, y + 1.8, r'$P_a$', fs=7.2)
    caixa(19, y - 3.6, 10, 7.2, r'$\frac{\omega_s}{2H}$', fs=10)
    seta(29.4, y, 37.0, y)
    txt(33.2, y + 1.9, r'$\Delta\dot\omega$', fs=7.4)
    caixa(37, y - 3.6, 8, 7.2, r'$\frac{1}{s}$', fs=10)
    txt(41.0, y - 5.2, r'$\Delta\omega(0)$', fs=6.6, cor=T2)
    linha([45.4, 51.0], [y, y]); ponto(51, y)
    txt(51.0, y + 1.9, r'$\Delta\omega$', fs=7.4)
    seta(51.0, y, 56.0, y)
    caixa(56, y - 3.6, 8, 7.2, r'$\frac{1}{s}$', fs=10)
    txt(60.0, y - 5.2, r'$\delta(0)$', fs=6.6, cor=T2)
    linha([64.4, 71.0], [y, y]); ponto(71, y)
    txt(73.0, y + 1.9, r'$\delta$', fs=7.4)
    seta(71.0, y, 82.0, y)
    txt(83.0, y, r'$\delta$ [rad]  (saída)', ha='left', fs=7.2)
    yb = 11.0
    linha([51, 51], [y, yb]); ponto(51, yb)
    seta(51.0, yb, 44.4, yb)
    caixa(36, yb - 3.2, 8, 6.4, r'$D$', fs=8.5)
    linha([35.6, 12.5], [yb, yb]); seta(12.5, yb, 12.5, y - 2.0)
    txt(24.0, yb + 1.7, r'$D\,\Delta\omega$', fs=7.0, cor=T2)
    seta(51.0, yb, 58.0, yb)
    txt(58.8, yb, r'$\Delta\omega$ [rad/s]  (saída)', ha='left', fs=7.2)
    yt = 29.5
    linha([71, 71], [y, yt]); seta(71.0, yt, 62.4, yt)
    caixa(46, yt - 3.2, 16, 6.4, r'$P_{max}\,\sin(\cdot)$', fs=8)
    linha([45.6, 12.5], [yt, yt]); seta(12.5, yt, 12.5, y + 2.0)
    ponto(27, yt); seta(27.0, yt, 27.0, yt + 4.3)
    txt(28.0, yt + 3.6, r'$P_e$ [pu]  (saída)', ha='left', fs=7.0)
    seta(54.0, 36.6, 54.0, yt + 3.6)
    txt(55.3, 35.6, r"distúrbio: $P_{max}(t) = E'V/X(t)$", ha='left', fs=6.6, cor=T2)
    txt(1.5, 3.2, r'$P_a = P_m - P_e - D\,\Delta\omega$  (potência acelerante);   '
        r'$\delta(0)$ e $\Delta\omega(0)$: condições iniciais dos integradores', ha='left', fs=6.8,
        cor=T2)
    E.salva(fig, 'fig-01-diagrama-blocos')


# ----------------------------------------------------------------------------- fig 02
def fig02():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.7, 2.8))
    dg = np.linspace(-60, 180, 700)
    a1.plot(dg, P_MAX*np.sin(np.radians(dg)), color=E.AZUL, label=r'$P_e = P_{max}\sin\delta$')
    a1.axhline(PM0, color=E.TINTA2, lw=0.9)
    a1.text(-57, PM0 + 0.09, r'$P_{m0} = 0{,}80$ pu', fontsize=7, color=E.TINTA2)
    xx = np.radians(np.array([2.0, 46.0]))
    a1.plot(np.degrees(xx), PM0 + lin0['Ps']*(xx - d0), color=E.LARANJA, lw=1.1, ls='--')
    a1.text(60, 1.02, 'inclinação em ' + r'$\delta_s$:' + '\n' + r'$P_s = P_{max}\cos\delta_s$' +
            ' = 1,833 pu/rad', fontsize=6.6, color=E.TINTA, ha='left', va='bottom')
    marca(a1, GR(d0), PM0, r'$\delta_s$' + ' = 23,58°\n(estável)', dx=4, dy=-24, fs=6.8)
    marca(a1, GR(du), PM0, r'$\delta_u$' + ' = 156,42°\n(instável)', dx=2, dy=-24,
          aberto=True, ha='center', fs=6.8)
    marca(a1, 90.0, P_MAX, r'$P_{max} = E^\prime V/X = 2{,}00$ pu', dx=0, dy=5, ha='center', ms=3.5,
          fs=6.8)
    a1.set_xticks(range(-60, 181, 30)); a1.set_xlim(-60, 180); a1.set_ylim(-1.9, 2.45)
    a1.set_xlabel(r'ângulo do rotor $\delta$ [graus]'); a1.set_ylabel('potência [pu]')
    a1.set_title('(a) Curva potência–ângulo e equilíbrios')
    E.virgula(a1)

    dg2 = np.linspace(-90, 200, 700)
    a2.axvspan(GR(dL), GR(du), color=E.FAIXA, lw=0, zorder=0)
    a2.plot(dg2, M.potencial(np.radians(dg2)) - V0, color=E.AZUL)
    a2.axhline(Vcr, color=E.TINTA2, lw=0.9)
    a2.text(-86, Vcr + 0.12, 'energia crítica = ' + G(Vcr, 3) + ' pu·rad', fontsize=6.8,
            color=E.TINTA2)
    marca(a2, GR(d0), 0.0, r'$\delta_s$ (mínimo)', dx=0, dy=-12, ha='center', fs=6.8)
    marca(a2, GR(du), Vcr, r'$\delta_u$ (sela)', dx=0, dy=-13, ha='center', aberto=True, fs=6.8)
    marca(a2, GR(dL), Vcr, r'$\delta_L$' + ' = ' + G(GR(dL), 2) + '°', dx=3, dy=-13, ha='left',
          aberto=True, fs=6.8)
    a2.text(0.5*(GR(dL) + GR(du)), 3.15, 'região de sincronismo\ncom ' + r'$\Delta\omega = 0$',
            ha='center', va='top', fontsize=6.8, color=E.TINTA)
    a2.set_xticks(range(-90, 201, 45)); a2.set_xlim(-90, 200); a2.set_ylim(-0.5, 3.3)
    a2.set_xlabel(r'ângulo do rotor $\delta$ [graus]')
    a2.set_ylabel(r'$V(\delta) - V(\delta_s)$ [pu·rad]')
    a2.set_title('(b) Energia potencial e energia crítica')
    E.virgula(a2)
    fig.tight_layout(w_pad=1.5)
    E.salva(fig, 'fig-02-potencia-angulo')


# ----------------------------------------------------------------------------- fig 03
def fig03():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.7, 2.95), gridspec_kw=dict(width_ratios=[1, 1.2]))
    a = W_S/(2*H); sig = lin0['sigma']
    pm = P_MAX*np.sin(np.linspace(0.0, 0.99999*PI/2, 800))
    Ps = np.sqrt(P_MAX**2 - pm**2)
    wdl = np.sqrt(np.maximum(a*Ps - sig**2, 0.0))
    a1.axhline(0, color='#c3c2b7', lw=0.7, zorder=1); a1.axvline(0, color='#c3c2b7', lw=0.7, zorder=1)
    a1.plot(-sig*np.ones_like(pm), wdl, color=E.AZUL, lw=1.6, label=r'estável $\delta_s$')
    a1.plot(-sig*np.ones_like(pm), -wdl, color=E.AZUL, lw=1.6)
    lu1 = -sig + np.sqrt(sig**2 + a*Ps); lu2 = -sig - np.sqrt(sig**2 + a*Ps)
    a1.plot(lu1, np.zeros_like(pm), color=E.LARANJA, lw=2.6, solid_capstyle='butt',
            label=r'sela $\delta_u$')
    a1.plot(lu2, np.zeros_like(pm), color=E.LARANJA, lw=2.6, solid_capstyle='butt')
    for pmv, lab in ((0.0, '0'), (PM0, '0,8'), (1.6, '1,6'), (1.9, '1,9')):
        Psv = math.sqrt(P_MAX**2 - pmv**2)
        w_ = math.sqrt(a*Psv - sig**2)
        nominal = abs(pmv - PM0) < 1e-9
        a1.plot([-sig], [w_], 'x' if nominal else 'o', ms=(7 if nominal else 3.5), mew=1.6,
                color=E.TINTA, zorder=6)
        a1.plot([-sig], [-w_], 'x' if nominal else 'o', ms=(7 if nominal else 3.5), mew=1.6,
                color=E.TINTA, zorder=6)
        dy = {0.0: 5, PM0: -6}.get(pmv, 0)
        a1.annotate(r'$P_{m0}$ = ' + lab + (' (nominal)' if nominal else ''), (-sig, w_),
                    xytext=(7, dy), textcoords='offset points', fontsize=6.3, color=E.TINTA,
                    va='center')
        for l in (-sig + math.sqrt(sig**2 + a*Psv), -sig - math.sqrt(sig**2 + a*Psv)):
            a1.plot([l], [0], 'x' if nominal else 'o', ms=(7 if nominal else 3.5), mew=1.6,
                    color=E.TINTA, zorder=6)
    a1.annotate('', xy=(-1.3, 1.4), xytext=(-1.3, 4.2),
                arrowprops=dict(arrowstyle='-|>', color=E.TINTA2, lw=0.8, mutation_scale=7))
    a1.text(-1.8, 2.8, r'$P_{m0} \rightarrow P_{max}$:' + '\npolos → origem\n(sela-nó)', fontsize=6.1,
            color=E.TINTA2, va='center', ha='right')
    a1.text(9.7, -2.6, 'nominal (×):\n' + r'$\lambda_s$ = −0,1885 ± j 8,311' + '\n' +
            r'$\lambda_u$ = +8,126 e −8,503', fontsize=6.4, color=E.TINTA, va='top', ha='right')
    a1.set_xlim(-10, 10); a1.set_ylim(-10, 10)
    a1.set_xlabel(r'Re $\lambda$ [1/s]'); a1.set_ylabel(r'Im $\lambda$ [rad/s]')
    a1.set_title(r'(a) Autovalores × ponto de operação $P_{m0}$')
    a1.legend(loc='lower right', fontsize=6.4, handlelength=1.4)
    E.virgula(a1)

    w = np.logspace(-1, 2, 3000)
    Gs = lin0['num_ganho']/(lin0['wn']**2 - w**2 + 2j*sig*w)
    a2.loglog(w, np.abs(Gs), color=E.AZUL, label='linearização em ' + r'$\delta_0$ (ref. auxiliar)')
    K = lin0['K_rad_pu']
    a2.axhline(K, color=E.TINTA2, lw=0.8)
    marca(a2, 0.1, K, r'ganho estático $K = 1/P_s$ = 0,5455 rad/pu', dx=3, dy=5, ms=3.5, fs=6.6)
    marca(a2, wr, Mr*K, r'$\omega_r$ = %s rad/s;  pico = %s rad/pu (= %s K)'
          % (G(wr, 3), G(Mr*K, 2), G(Mr, 1)), dx=-5, dy=2, ha='right', va='center', ms=3.5, fs=6.6)
    a2.set_xlim(0.1, 100); a2.set_ylim(1e-3, 30)
    eixo_log(a2, [0.1, 1, 10, 100], [1e-3, 1e-2, 1e-1, 1, 10])
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, p: E._fmt_virgula(v)))
    a2.set_xlabel(r'frequência $\omega$ [rad/s]')
    a2.set_ylabel(r'$|\Delta\delta/\Delta P_m|$ [rad/pu]')
    a2.set_title(r'(b) Resposta em frequência $\Delta\delta/\Delta P_m$')
    a2.legend(loc='lower left', fontsize=6.6)
    fig.tight_layout(w_pad=1.5)
    E.salva(fig, 'fig-03-polos-frequencia')


# ----------------------------------------------------------------------------- fig 04
def fig04():
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(6.7, 5.7),
                                     gridspec_kw=dict(height_ratios=[1.3, 1.0, 0.75]))
    t, y = rA['t'], np.degrees(rA['delta'])
    tpre = np.array([-0.25, 0.0])
    m = mA
    s1 = t <= 3.0
    a1.axhline(GR(dfA), color=E.TINTA2, lw=0.8)
    ylin = GR(d0) + np.degrees(M.degrau_linear(t[s1], DPM_DEGRAU, lin0))
    a1.plot(np.r_[tpre, t[s1]], np.r_[[GR(d0)]*2, ylin], color=E.LARANJA, lw=1.1, ls='--',
            label=r'linearização em $\delta_0$ (referência auxiliar, forma fechada)')
    a1.plot(np.r_[tpre, t[s1]], np.r_[[GR(d0)]*2, y[s1]], color=E.AZUL, lw=1.5,
            label='modelo não linear (simulação)')
    tpk, ypk = M.picos(t, rA['delta'])
    marca(a1, m['tp'], GR(m['delta_pico_rad']),
          '1º pico: $t_p$ = %s s;  $M_p$ = %s %%' % (G(m['tp'], 3), G(100*m['Mp'], 2)),
          dx=5, dy=3, fs=6.8)
    marca(a1, m['tr'], GR(dfA), '$t_r$ = %s s' % G(m['tr'], 3), dx=4, dy=-13, fs=6.8)
    yT = GR(ypk[2]) + 0.45
    a1.annotate('', xy=(tpk[3], yT), xytext=(tpk[2], yT),
                arrowprops=dict(arrowstyle='<|-|>', color=E.TINTA, lw=0.8, mutation_scale=7))
    a1.text(0.5*(tpk[2] + tpk[3]), yT + 0.12, '$T_d$ = %s s (média de 10 ciclos)' % G(m['Td'], 4),
            ha='center', va='bottom', fontsize=6.8)
    a1.text(2.98, GR(dfA) - 0.2, r'valor final $\delta_\infty$ = %s°' % G(GR(dfA), 3), ha='right',
            va='top', fontsize=6.8)
    a1.text(-0.22, GR(d0) + 0.15, r'$\delta_0$ = %s°' % G(GR(d0), 3), ha='left', va='bottom',
            fontsize=6.8)
    a1.set_xlim(-0.25, 3.0); a1.set_ylim(GR(d0) - 0.6, GR(ypk[0]) + 2.1)
    a1.set_ylabel(r'$\delta$ [graus]')
    a1.set_title(r'(a) Degrau $P_m$: 0,80 $\rightarrow$ 0,90 pu em $t = 0$ (detalhe de 0 a 3 s)')
    a1.legend(loc='upper right', fontsize=6.6, ncol=2)
    E.rotulo_solver(a1)
    E.virgula(a1)

    s2 = t <= 30.0
    faixa = 0.02*(dfA - d0)
    a2.axhspan(GR(dfA - faixa), GR(dfA + faixa), color=E.FAIXA, lw=0, zorder=0)
    env = GR(dfA - d0)*np.exp(-lin0['sigma']*t[s2])/math.sqrt(1 - lin0['zeta']**2)
    a2.plot(t[s2], y[s2], color=E.AZUL, lw=0.55, label='modelo não linear (simulação)')
    a2.plot(t[s2], GR(dfA) + env, color=E.LARANJA, lw=1.0, ls='--',
            label=r'envoltória algébrica $\delta_\infty \pm (\delta_\infty-\delta_0)\,e^{-\sigma t}/\sqrt{1-\zeta^2}$')
    a2.plot(t[s2], GR(dfA) - env, color=E.LARANJA, lw=1.0, ls='--')
    a2.axvline(m['ts2'], color=E.TINTA, lw=0.8)
    a2.text(m['ts2'] + 0.3, GR(d0) + 0.25, '$t_s$(2 %%) = %s s' % G(m['ts2'], 2), fontsize=6.8,
            va='bottom')
    a2.text(29.7, GR(dfA + faixa) + 0.05, 'faixa de ±2 %', fontsize=6.4, color=E.TINTA2,
            ha='right', va='bottom')
    a2.set_xlim(0, 30); a2.set_ylim(GR(d0) - 0.6, GR(ypk[0]) + 2.1)
    a2.set_ylabel(r'$\delta$ [graus]')
    a2.set_title('(b) Janela de 30 s: decaimento (σ medido = %s 1/s) e acomodação'
                 % G(m['sigma'], 4))
    a2.legend(loc='upper right', fontsize=6.6)
    E.rotulo_solver(a2)
    E.virgula(a2)

    a3.plot([-0.25, 0, 0, 3.0], [PM0, PM0, Pm1, Pm1], color=E.TINTA2, lw=1.0, label='$P_m(t)$ (entrada)')
    a3.plot(np.r_[tpre, t[s1]], np.r_[[PM0]*2, rA['Pe'][s1]], color=E.AZUL, lw=1.4,
            label='$P_e(t) = P_{max}\\sin\\delta$')
    ipe = np.argmax(rA['Pe'][s1])
    marca(a3, t[s1][ipe], rA['Pe'][s1][ipe], 'máx. %s pu' % G(rA['Pe'][s1][ipe], 3), dx=5, dy=-2,
          fs=6.8, va='center')
    a3.set_xlim(-0.25, 3.0); a3.set_ylim(0.76, 1.03)
    a3.set_xlabel('tempo [s]'); a3.set_ylabel('potência [pu]')
    a3.set_title('(c) Potência elétrica entregue à rede')
    a3.legend(loc='lower right', fontsize=6.6, ncol=2)
    E.virgula(a3)
    fig.tight_layout(h_pad=0.9)
    E.salva(fig, 'fig-04-degrau')


# ----------------------------------------------------------------------------- fig 05
def fig05():
    fig = plt.figure(figsize=(6.7, 3.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1])
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1])
    t, y = rB['t'], np.degrees(rB['delta'])
    s1 = t <= 6.0
    a1.axhline(GR(d0), color=E.TINTA2, lw=0.8)
    ylin = GR(d0 + M.livre_linear(t[s1], dci - d0, 0.0, lin0))
    a1.plot(t[s1], ylin, color=E.LARANJA, lw=1.1, ls='--',
            label=r'linearização em $\delta_0$ (ref. auxiliar)')
    a1.plot(t[s1], y[s1], color=E.AZUL, lw=1.4, label='não linear (simulação)')
    marca(a1, 0.0, DELTA_CI_GR, 'δ(0) = 60°, Δω(0) = 0', dx=5, dy=12, fs=6.6)
    marca(a1, tpB[0], GR(ypB[0]), '$T_1$ = %s s\n(linear: %s s)'
          % (G(tpB[0], 4), G(lin0['Td'], 4)), dx=6, dy=1, fs=6.6)
    marca(a1, tvB[0], GR(-yvB[0]), None, ms=4.6)
    marca(a1, tvB[0], GR(dminB_en), None, aberto=True, ms=6.5)
    a1.text(tvB[0] + 0.2, GR(dminB_en) - 1.0,
            '● mínimo simulado: %s°\n○ previsão por energia (D = 0): %s°'
            % (G(GR(-yvB[0]), 2), G(GR(dminB_en), 2)), fontsize=6.4, va='top')
    a1.text(6.08, GR(d0), r'$\delta_s$', ha='left', va='center', fontsize=6.8, color=E.TINTA2,
            clip_on=False)
    a1.set_xlim(0, 6); a1.set_ylim(-30, 78)
    a1.set_xlabel('tempo [s]'); a1.set_ylabel(r'$\delta$ [graus]')
    a1.set_title('(a) Resposta livre a partir de δ(0) = 60°')
    a1.legend(loc='upper right', fontsize=6.4)
    E.rotulo_solver(a1)
    E.virgula(a1)

    a2.plot(GR(sep_x), sep_w, color=E.TINTA2, lw=0.9, label='separatriz (D = 0)')
    a2.plot(GR(sep_x), -sep_w, color=E.TINTA2, lw=0.9)
    a2.plot(y, rB['omega'], color=E.AZUL, lw=0.7, label='trajetória simulada')
    marca(a2, DELTA_CI_GR, 0.0, 'início', dx=0, dy=6, ha='center', fs=6.4)
    marca(a2, GR(d0), 0.0, None, ms=4)
    marca(a2, GR(du), 0.0, r'$\delta_u$', aberto=True, dx=0, dy=6, ha='center', fs=6.6)
    marca(a2, GR(dL), 0.0, r'$\delta_L$', aberto=True, dx=0, dy=6, ha='center', fs=6.6)
    a2.set_xlim(-75, 175); a2.set_xticks(range(-60, 181, 60))
    a2.set_ylim(-12, 12)
    a2.set_xlabel(r'$\delta$ [graus]'); a2.set_ylabel(r'$\Delta\omega$ [rad/s]')
    a2.set_title('(b) Plano de fase')
    a2.legend(loc='lower center', fontsize=6.2, ncol=1)
    E.virgula(a2)
    fig.tight_layout(w_pad=1.4)
    E.salva(fig, 'fig-05-condicao-inicial')


# ----------------------------------------------------------------------------- fig 06
def fig06():
    fig = plt.figure(figsize=(6.7, 3.05))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.4, 1])
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1])
    cores = [E.RAMPA[1], E.RAMPA[4], E.CRITICO]
    a1.axvline(tf, color=E.TINTA2, lw=0.8, ls=':')
    a1.axhline(GR(du), color=E.TINTA2, lw=0.8)
    a1.text(1.98, GR(du) - 3, r'$\delta_u$ = 156,4°', ha='right', va='top', fontsize=6.6,
            color=E.TINTA2)
    a1.axhline(falta['delta_cr_graus'], color=E.TINTA2, lw=0.8, ls=':')
    a1.text(0.78, falta['delta_cr_graus'] + 2, r'$\delta_{cr}$ = %s°' % G(falta['delta_cr_graus'], 2)
            + '\n(critério das áreas)', ha='left', va='bottom', fontsize=6.6, color=E.TINTA2)
    for c, cor in zip(casosC, cores):
        r = c['r']
        s = (r['t'] <= 2.0) & (r['delta'] <= RAD(205))
        rot = 'falta de %d ms: ' % round(1000*c['duracao']) + \
              ('✕ perde sincronismo' if c['perdeu'] else 'estável')
        a1.plot(r['t'][s], GR(r['delta'][s]), color=cor, lw=1.4, label=rot)
        marca(a1, tf + c['duracao'], c['delta_elim_graus'], None, cor=cor, ms=4.2)
    a1.text(tf + 0.02, 198, 'início da\nfalta (Pe = 0)', fontsize=6.2, color=E.TINTA2,
            va='top', ha='left')
    a1.set_xlim(0, 2.0); a1.set_ylim(-95, 205); a1.set_yticks(range(-90, 181, 30))
    a1.set_xlabel('tempo [s]'); a1.set_ylabel(r'$\delta$ [graus]')
    a1.set_title('(a) Falta temporária aplicada em t = 0,10 s')
    a1.legend(loc='lower right', fontsize=6.3)
    E.rotulo_solver(a1, y=0.98, va='top', texto=E.SOLVER + '\nmarcador = eliminação da falta')
    E.virgula(a1)

    dg = np.linspace(0, 180, 500); dr = np.radians(dg)
    dcr = falta['delta_cr_rad']
    x1 = np.linspace(d0, dcr, 200)
    a2.fill_between(GR(x1), 0, PM0, color=E.LARANJA, alpha=0.28, lw=0)
    x2 = np.linspace(dcr, du, 300)
    a2.fill_between(GR(x2), PM0, P_MAX*np.sin(x2), color=E.AQUA, alpha=0.30, lw=0)
    a2.plot(dg, P_MAX*np.sin(dr), color=E.AZUL, lw=1.4, label='$P_e$ pré e pós-falta')
    a2.plot([0, 180], [0, 0], color=E.LARANJA, lw=1.6, label='$P_e$ durante a falta (= 0)')
    a2.axhline(PM0, color=E.TINTA2, lw=0.9)
    a2.text(2, PM0 + 0.05, '$P_m$', fontsize=6.8, color=E.TINTA2)
    a2.text(GR(0.5*(d0 + dcr)), 0.32, '$A_1$\n%s' % G(falta['A1'], 3), ha='center', fontsize=6.8)
    a2.text(GR(0.5*(dcr + du)) - 6, 1.25, '$A_2$\n%s' % G(falta['A2'], 3), ha='center', fontsize=6.8)
    for xv, lab in ((d0, r'$\delta_0$'), (dcr, r'$\delta_{cr}$'), (du, r'$\delta_u$')):
        a2.axvline(GR(xv), color=E.TINTA2, lw=0.6, ls=':')
        a2.text(GR(xv), 2.18, lab, ha='center', va='bottom', fontsize=6.8)
    a2.set_xlim(0, 180); a2.set_xticks(range(0, 181, 30)); a2.set_ylim(-0.12, 3.0)
    a2.set_yticks([0, 0.5, 1, 1.5, 2])
    a2.set_xlabel(r'$\delta$ [graus]'); a2.set_ylabel('potência [pu]')
    a2.set_title(r'(b) Critério das áreas: $A_1 = A_2$ [pu·rad]')
    a2.legend(loc='upper right', fontsize=6.2, ncol=1)
    E.virgula(a2)
    fig.tight_layout(w_pad=1.4)
    E.salva(fig, 'fig-06-falta')


# ----------------------------------------------------------------------------- fig 07
def fig07():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.7, 2.8))
    series = [(rB0, WB0, 'D = 0, h = 1 ms:  $|W(t)-W(0)|$', E.AZUL),
              (rB, WB, 'D = 0,01, h = 1 ms:  $|W-W(0)+E_d|$', E.LARANJA),
              (rB10, WB10, 'D = 0,01, h = 10 ms', E.AQUA)]
    for r, W, lab, cor in series:
        s = (r['t'] > 0) & (r['t'] <= 30.0)
        res = np.maximum(np.abs(W - W[0])[s]/Vcr, 1e-18)
        a1.semilogy(r['t'][s], res, color=cor, lw=0.7, label=lab)
    a1.axhline(np.finfo(float).eps, color=E.TINTA2, lw=0.8)
    a1.text(29.5, np.finfo(float).eps*1.6, 'ε da dupla precisão = 2,2×10⁻¹⁶', ha='right',
            va='bottom', fontsize=6.4, color=E.TINTA2)
    a1.set_xlim(0, 30); a1.set_ylim(1e-17, 1e-5)
    a1.set_xlabel('tempo [s]'); a1.set_ylabel('resíduo / energia crítica')
    a1.set_title('(a) Balanço de energia (ensaio b)')
    a1.legend(loc='upper left', fontsize=6.3)
    a1.xaxis.set_major_formatter(FuncFormatter(lambda v, p: E._fmt_virgula(v)))

    hs = np.array([c['h'] for c in conv]); er = np.array([c['erro_rad'] for c in conv])
    a2.loglog(hs*1e3, er, 'o-', color=E.AZUL, ms=4.5, mfc=E.AZUL, mec='white', lw=1.2,
              label=r'erro de $\delta(10\,s)$ (ref.: h = 0,1 ms)')
    href = np.array([0.8, 40.0])
    a2.loglog(href, er[2]*(href/10.0)**4, color=E.TINTA2, lw=0.8, ls='--', label='inclinação 4 (teórica)')
    i1 = int(np.where(np.isclose(hs, 1e-3))[0][0])
    marca(a2, 1.0, er[i1], 'h = 1 ms (adotado):\n%s rad' % E.cient(er[i1]),
          dx=6, dy=-4, va='top', fs=6.6)
    a2.set_xlabel('passo h [ms]'); a2.set_ylabel('erro [rad]')
    a2.set_title('(b) Convergência do RK4: ordem observada %s' % G(ordem, 2))
    a2.set_xlim(0.3, 60)
    a2.xaxis.set_major_locator(FixedLocator([0.5, 1, 2, 5, 10, 20, 40]))
    a2.xaxis.set_major_formatter(FuncFormatter(lambda v, p: E._fmt_virgula(v)))
    a2.xaxis.set_minor_formatter(NullFormatter())
    a2.legend(loc='upper left', fontsize=6.3)
    fig.tight_layout(w_pad=1.5)
    E.salva(fig, 'fig-07-validacao-numerica')


# ----------------------------------------------------------------------------- R5: figuras
def multiplos(fig, celula, casos, rotulos, janela, cores):
    n = len(casos)
    sub = celula.subgridspec(n, 1, hspace=0.18)
    axes = []
    for i, (c, rot, cor) in enumerate(zip(casos, rotulos, cores)):
        ax = fig.add_subplot(sub[i], sharex=(axes[0] if axes else None))
        r = c['r']
        s = (r['t'] <= janela) & (r['delta'] <= PI)
        yy = GR(r['delta'][s] - c['delta0_rad'])
        ax.plot(r['t'][s], yy, color=(E.CRITICO if c['perdeu'] else cor), lw=0.75)
        if c['perdeu']:
            tl = c['t_perda']
            rot = rot + ('\n✕ perde sincronismo (t = %s s)' % G(tl, 1) if tl <= janela
                         else '\n✕ perde sincronismo em t = %s s' % G(tl, 1))
        lo, hi = float(np.min(yy)), float(np.max(yy))
        folga = 1.4 if c['perdeu'] else 0.75                               # folga para o rotulo
        ax.set_ylim(min(lo, 0.0) - 0.08*(hi - lo), hi + folga*(hi - lo))
        ax.text(0.995, 0.95, rot, transform=ax.transAxes, ha='right', va='top', fontsize=6.4,
                color=E.TINTA, bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.9))
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
        ax.tick_params(labelsize=6.5)
        if i < n - 1:
            ax.tick_params(labelbottom=False)
        E.virgula(ax)
        axes.append(ax)
    axes[0].set_xlim(0, janela)
    axes[-1].set_xlabel('tempo [s]')
    axes[n//2].set_ylabel(r'$\delta - \delta_0$ [graus]')
    return axes


def painel_elasticidade(ax, xp, pred, xs, sim, xlabel, ticks_x, ticks_y, ylim, loc='best'):
    nomes = [('K', 'ganho estático K', E.AZUL, 'o'), ('wd', r'frequência $\omega_d$', E.LARANJA, 's'),
             ('taxa', r'taxa de decaimento $\sigma$', E.AQUA, '^'),
             ('tcr', r'tempo crítico $t_{cr}$', E.AMARELO, 'D')]
    ax.axhline(1, color='#c3c2b7', lw=0.7); ax.axvline(1, color='#c3c2b7', lw=0.7)
    for k, lab, cor, mk in nomes:
        ax.plot(xp, pred[k], color=cor, lw=1.4)
        ax.plot(xs, sim[k], mk, ms=5, mfc=cor, mec='white', mew=0.9, zorder=5)
        ax.plot([], [], color=cor, lw=1.4, marker=mk, ms=5, mfc=cor, mec='white', label=lab)
    ax.set_xscale('log'); ax.set_yscale('log')
    eixo_log(ax, ticks_x, ticks_y)
    ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel('valor / valor nominal')
    lg = ax.legend(loc=loc, fontsize=6.2, title='linhas: álgebra · pontos: simulação',
                   title_fontsize=6.0)
    lg.get_title().set_color(E.TINTA2)


def sim_de(casos, chave):
    out = []
    for c in casos:
        if c['perdeu']:
            out.append(np.nan)
        elif chave == 'tcr':
            out.append(c['tcr_sim'])
        else:
            v = c['medido'].get(chave)
            out.append(np.nan if (v is None or not np.isfinite(v)) else v)
    return np.array(out, dtype=float)


def fig09():
    fig = plt.figure(figsize=(6.7, 4.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.32)
    rot = ['H = %s s (×%s)' % (G(v, 1), G(v/H, 1)) + ('  nominal' if v == H else '') for v in NIVEIS_H]
    multiplos(fig, gs[0], sensH, rot, 20.0, E.rampa(len(sensH)))
    ax = fig.add_subplot(gs[1])
    hp = np.logspace(np.log10(0.15), np.log10(6.0), 300)*H
    pr = [M.analise_linear(PM0, P_MAX, h, D) for h in hp]
    pred = dict(K=np.array([p['K_rad_pu'] for p in pr])/lin0['K_rad_pu'],
                wd=np.array([p['wd'] for p in pr])/lin0['wd'],
                taxa=np.array([p['sigma'] for p in pr])/lin0['sigma'],
                tcr=np.array([M.criterio_areas_falta(PM0, P_MAX, h)['t_cr'] for h in hp])/falta['t_cr'])
    i0 = NIVEIS_H.index(H)
    sim = {k: sim_de(sensH, c)/sim_de(sensH, c)[i0] for k, c in
           (('K', 'ganho_rad_pu'), ('wd', 'wd'), ('taxa', 'taxa_dom'), ('tcr', 'tcr'))}
    painel_elasticidade(ax, hp/H, pred, np.array(NIVEIS_H)/H, sim, r'$H / H_{nom}$',
                        [0.2, 0.5, 1, 2, 5], [0.2, 0.5, 1, 2, 5], (0.15, 7))
    ax.set_title('(b) Métricas normalizadas', fontsize=8)
    fig.axes[0].set_title('(a) Degrau de 0,10 pu por nível de H (RK4, h = 1 ms)', fontsize=8)
    E.salva(fig, 'fig-09-sens-inercia')


def fig10():
    fig = plt.figure(figsize=(6.7, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.32)
    rot = []
    for v in NIVEIS_D:
        z = M.analise_linear(PM0, P_MAX, H, v)['zeta']
        rot.append('D = %s  (ζ = %s)' % (G(v, 3), G(z, 3)) + ('  nominal' if v == D else ''))
    cores = E.rampa(len(sensD))
    multiplos(fig, gs[0], sensD, rot, 20.0, cores)
    ax = fig.add_subplot(gs[1])
    dp = np.logspace(np.log10(0.0015), np.log10(1.5), 400)
    pr = [M.analise_linear(PM0, P_MAX, H, v) for v in dp]
    wdp = np.array([p['wd'] if p['wd'] is not None else np.nan for p in pr])
    pred = dict(K=np.array([p['K_rad_pu'] for p in pr])/lin0['K_rad_pu'],
                wd=wdp/lin0['wd'],
                taxa=np.array([p['taxa_dominante'] for p in pr])/lin0['sigma'],
                tcr=np.ones_like(dp))
    pos = [i for i, v in enumerate(NIVEIS_D) if v > 0]
    casos = [sensD[i] for i in pos]
    i0 = [NIVEIS_D[i] for i in pos].index(D)
    sim = {k: sim_de(casos, c)/sim_de(casos, c)[i0] for k, c in
           (('K', 'ganho_rad_pu'), ('wd', 'wd'), ('taxa', 'taxa_dom'), ('tcr', 'tcr'))}
    painel_elasticidade(ax, dp/D, pred, np.array([NIVEIS_D[i] for i in pos])/D, sim,
                        r'$D / D_{nom}$  (D > 0)', [0.2, 1, 10, 100], [0.1, 1, 10, 100], (0.08, 400),
                        loc='upper left')
    ax.text(0.98, 0.03, r'$t_{cr}$ algébrico: forma fechada com' + '\nD = 0 (não depende de D)',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=6.0, color=E.TINTA2)
    ax.set_title('(b) Métricas normalizadas', fontsize=8)
    fig.axes[0].set_title('(a) Degrau de 0,10 pu por nível de D (RK4, h = 1 ms)', fontsize=8)
    E.salva(fig, 'fig-10-sens-amortecimento')


def fig11():
    fig = plt.figure(figsize=(6.7, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.32)
    rot = []
    for c in sensX:
        rot.append('X = %s pu  (Pmax = %s pu; δ₀ = %s°)' % (G(c['X'], 2), G(c['Pmax'], 2),
                                                            G(GR(c['delta0_rad']), 1))
                   + ('  nominal' if c['X'] == X_TOT else ''))
    multiplos(fig, gs[0], sensX, rot, 20.0, E.rampa(len(sensX)))
    ax = fig.add_subplot(gs[1])
    xp = np.linspace(0.25, 1.47, 400)
    pr = [M.analise_linear(PM0, E_LINHA*V_BAR/x, H, D) for x in xp]
    pred = dict(K=np.array([p['K_rad_pu'] for p in pr])/lin0['K_rad_pu'],
                wd=np.array([p['wd'] for p in pr])/lin0['wd'],
                taxa=np.array([p['sigma'] for p in pr])/lin0['sigma'],
                tcr=np.array([M.criterio_areas_falta(PM0, E_LINHA*V_BAR/x)['t_cr'] for x in xp])/falta['t_cr'])
    i0 = NIVEIS_X.index(X_TOT)
    sim = {k: sim_de(sensX, c)/sim_de(sensX, c)[i0] for k, c in
           (('K', 'ganho_rad_pu'), ('wd', 'wd'), ('taxa', 'taxa_dom'), ('tcr', 'tcr'))}
    painel_elasticidade(ax, xp/X_TOT, pred, np.array(NIVEIS_X)/X_TOT, sim, r'$X / X_{nom}$',
                        [0.5, 1, 1.5, 2, 2.5], [0.1, 0.2, 0.5, 1, 2, 5, 10], (0.06, 14))
    ax.set_title('(b) Métricas normalizadas', fontsize=8)
    fig.axes[0].set_title('(a) Degrau de 0,10 pu por nível de X (RK4, h = 1 ms)', fontsize=8)
    E.salva(fig, 'fig-11-sens-reatancia')


def fig12():
    fig = plt.figure(figsize=(6.7, 5.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.42, wspace=0.28)
    a1 = fig.add_subplot(gs[0, :]); a2 = fig.add_subplot(gs[1, 0]); a3 = fig.add_subplot(gs[1, 1])
    tt = np.linspace(0, 2.5, 2000)
    a1.plot(tt, np.degrees(M.degrau_linear(tt, 1.0, lin0)), color=E.LARANJA, lw=1.1, ls='--',
            label=r'linearização em $\delta_0$ (igual para qualquer $\Delta P_m$)')
    for c, cor in zip(sensA, E.rampa(len(sensA))):
        r = c['r']; s = r['t'] <= 2.5
        a1.plot(r['t'][s], GR(r['delta'][s] - d0)/c['dPm'], color=cor, lw=1.2,
                label=r'$\Delta P_m$ = %s pu' % G(c['dPm'], 2))
    a1.set_xlim(0, 2.5); a1.set_ylim(0, 98); a1.set_yticks(range(0, 71, 10))
    a1.set_xlabel('tempo [s]'); a1.set_ylabel(r'$(\delta - \delta_0)/\Delta P_m$ [graus/pu]')
    a1.set_title('(a) E se o degrau for maior? Resposta normalizada (RK4, h = 1 ms)')
    a1.legend(loc='upper right', fontsize=6.3, ncol=3)
    E.virgula(a1)

    for c, cor in zip(casos_cr, [E.AZUL, E.CRITICO]):
        r = c['r']; s = (r['t'] <= 4.0) & (r['delta'] <= RAD(200))
        rot = r'$\Delta P_m$ = %s pu: ' % G(c['dPm'], 3) + ('✕ perde sincronismo' if c['perdeu'] else 'estável')
        a2.plot(r['t'][s], GR(r['delta'][s]), color=cor, lw=1.3, label=rot)
    du_c = GR(PI - math.asin((PM0 + dpm_cr_sim)/P_MAX))
    a2.axhline(du_c, color=E.TINTA2, lw=0.8)
    a2.text(3.95, du_c + 3, r'$\delta_{u1} \approx$ %s°' % G(du_c, 1), ha='right', va='bottom',
            fontsize=6.4, color=E.TINTA2)
    a2.set_xlim(0, 4); a2.set_ylim(0, 200); a2.set_yticks(range(0, 181, 45))
    a2.set_xlabel('tempo [s]'); a2.set_ylabel(r'$\delta$ [graus]')
    a2.set_title('(b) Degrau crítico (simulado: %s pu)' % G(dpm_cr_sim, 3))
    a2.legend(loc='upper right', fontsize=6.0)
    E.rotulo_solver(a2)
    E.virgula(a2)

    for c, cor in zip(casos_ci, [E.AZUL, E.CRITICO]):
        r = c['r']; s = (r['t'] <= 12.0) & (r['delta'] <= RAD(200))
        rot = r'$\delta(0)$ = %d°: ' % c['delta0_graus'] + ('✕ perde sincronismo' if c['perdeu'] else 'estável')
        a3.plot(r['t'][s], GR(r['delta'][s]), color=cor, lw=1.1, label=rot)
    a3.axhline(GR(du), color=E.TINTA2, lw=0.8)
    a3.text(11.9, GR(du) + 3, r'$\delta_u$ = 156,4°', ha='right', va='bottom', fontsize=6.4,
            color=E.TINTA2)
    a3.set_xlim(0, 12); a3.set_ylim(-105, 200); a3.set_yticks(range(-90, 181, 45))
    a3.set_xlabel('tempo [s]'); a3.set_ylabel(r'$\delta$ [graus]')
    a3.set_title(r'(c) Condição inicial perto de $\delta_u$')
    a3.legend(loc='lower right', fontsize=6.0)
    E.rotulo_solver(a3, y=0.22)
    E.virgula(a3)
    E.salva(fig, 'fig-12-sens-amplitude-ci')


for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig09, fig10, fig11, fig12):
    f()


# ============================================================================ dados e resultados
def grava_csv(nome, cab, colunas):
    os.makedirs(DIR_DADOS, exist_ok=True)
    with open(os.path.join(DIR_DADOS, nome), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(cab)
        for linha in zip(*colunas):
            w.writerow(['%.6f' % linha[0]] + ['%.10e' % v for v in linha[1:]])


def amostra(r, t_grade):
    t = r['t']
    _, idx = np.unique(t[::-1], return_index=True)      # remove instantes duplicados (troca de trecho)
    idx = len(t) - 1 - idx
    return [np.interp(t_grade, t[idx], r[k][idx]) for k in ('delta', 'omega', 'Pe')]


tg = np.round(np.arange(0.0, 30.0 + 1e-9, 0.01), 6)
grava_csv('ensaio_a_degrau.csv', ['t_s', 'delta_rad', 'delta_omega_rad_s', 'Pe_pu'],
          [tg] + amostra(rA, tg))
grava_csv('ensaio_b_condicao_inicial.csv', ['t_s', 'delta_rad', 'delta_omega_rad_s', 'Pe_pu'],
          [tg] + amostra(rB, tg))
tgc = np.round(np.arange(0.0, 2.0 + 1e-9, 0.001), 6)
colc, cabc = [tgc], ['t_s']
for c in casosC:
    ms = '%03d' % round(1000*c['duracao'])
    dl, wl, pl = amostra(c['r'], tgc)
    colc += [dl, wl, pl]
    cabc += ['delta_rad_falta%sms' % ms, 'delta_omega_rad_s_falta%sms' % ms, 'Pe_pu_falta%sms' % ms]
grava_csv('ensaio_c_falta.csv', cabc, colc)


def limpa(o):
    if isinstance(o, dict):
        return {str(k): limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpa(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        v = float(o)
        if math.isnan(v):
            return None
        if math.isinf(v):
            return 'inf' if v > 0 else '-inf'
        return v
    if isinstance(o, np.ndarray):
        return limpa(o.tolist())
    return o


R['tempo_execucao_s'] = time.time() - t_inicio
with open(os.path.join(SAIDA, 'resultados.json'), 'w', encoding='utf-8') as fh:
    json.dump(limpa(R), fh, indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ resumo em tela
print('\n=== R2  delta_s = %.4f graus | Ps = %.5f | K = %.5f rad/pu | wn = %.5f | zeta = %.5f'
      % (lin0['delta_s_graus'], lin0['Ps'], lin0['K_rad_pu'], lin0['wn'], lin0['zeta']))
print('        wd = %.5f rad/s | Td = %.5f s | Mp = %.4f | tp = %.5f | ts2 = %.3f s | tcr = %.5f s'
      % (lin0['wd'], lin0['Td'], lin0['Mp'], lin0['tp'], lin0['ts2_forma_fechada'], falta['t_cr']))
print('=== R3a ganho = %.5f | wd = %.5f | Mp = %.4f | tp = %.5f | ts2 = %.3f | sigma = %.5f'
      % (mA['ganho_rad_pu'], mA['wd'], mA['Mp'], mA['tp'], mA['ts2'], mA['sigma']))
print('=== R3b T1 = %.5f s (energia %.5f; D=0 %.5f) | min = %.3f graus (energia %.3f)'
      % (tpB[0], TB_en, tpB0[0], GR(-yvB[0]), GR(dminB_en)))
print('=== R3c tcr: areas %.6f | sim D=0 %.6f | sim D %.6f' % (falta['t_cr'], tcr_s0, tcr_s))
print('=== R5  degrau critico: areas %.5f | sim D=0 %.5f | sim D %.5f' % (dpm_cr_areas, dpm_cr_sim0, dpm_cr_sim))
print('        D<0: perda em %s s (previsao %.1f s)' % (cDneg.get('t_perda'), t_perda_prev))
print('        RK4: ordem observada %.3f | residuo energia D=0: %.2e' % (ordem, R['R3b']['residuo_energia_D0']))
print('OK: figuras em %s, resultados.json e dados/*.csv  (%.1f s)'
      % (os.path.normpath(E.DIR_PNG), time.time() - t_inicio))
