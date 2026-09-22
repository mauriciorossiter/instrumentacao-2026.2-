# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Sistema 7: Gerador Sincrono (Swing Equation)
Caracterizacao do LIMIAR (threshold) do sistema instrumentado.

Limiar = menor variacao da entrada, PARTINDO DO REPOUSO/ponto de operacao
estabelecido, que produz uma variacao DETECTAVEL na saida.

O modelo continuo nao tem limiar (a sensibilidade estatica 1/Ps e' finita e
nao nula). O limiar e', portanto, uma propriedade da CADEIA DE MEDICAO. Este
script quantifica as tres origens praticas:
  (A) verificacao de que o limiar intrinseco do modelo e' nulo
  (B) limiar imposto pela quantizacao do canal de medicao de delta
  (C) limiar imposto pelo ruido do canal de medicao de delta
  (D) limiar no pico do transitorio x limiar em regime permanente
  (E) dependencia do limiar com o ponto de operacao (delta_0)

Reusa o mesmo modelo nao linear, parametros e tolerancias do relatorio v2
(caracterizacao_swing_v2.py) e do relatorio de entradas espurias v1.

Gera:
  figs/limiar_quantizacao.pdf
  figs/limiar_ruido.pdf
  figs/limiar_ponto_operacao.pdf
  resultados_limiar.json
"""
import os, json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': .3,
                     'figure.dpi': 160, 'savefig.bbox': 'tight',
                     'axes.spines.top': False, 'axes.spines.right': False})

AQUI = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(AQUI, 'figs'); os.makedirs(FIG, exist_ok=True)

RTOL, ATOL = 1e-10, 1e-12
RNG = np.random.default_rng(20260830)      # semente fixa: Monte Carlo reprodutivel

# ------------------------------------------------------------- parametros (== v2)
ws, H, D, Pmax, Pm0 = 2*np.pi*60.0, 5.0, 0.01, 2.0, 0.80
d0 = float(np.arcsin(Pm0/Pmax))
Ps = Pmax*np.cos(d0)                       # coef. de potencia sincronizante [pu/rad]
wn = np.sqrt(ws*Ps/(2*H))
zeta = (D/2.0)*np.sqrt(ws/(2*H*Ps))
wd = wn*np.sqrt(1-zeta**2)
S_est = 1.0/Ps                             # sensibilidade estatica [rad/pu]

R = {}   # dicionario de resultados

R['parametros'] = dict(ws=ws, H=H, D=D, Pmax=Pmax, Pm0=Pm0,
                       delta0_rad=d0, delta0_deg=float(np.degrees(d0)),
                       Ps_pu_por_rad=float(Ps), wn_rad_s=float(wn), zeta=float(zeta),
                       wd_rad_s=float(wd), fd_Hz=float(wd/(2*np.pi)),
                       sensibilidade_estatica_rad_por_pu=float(S_est),
                       sensibilidade_estatica_graus_por_pu=float(np.degrees(S_est)))

def f_nl(t, x, Pm):
    return [x[1], (ws/(2*H))*(Pm - Pmax*np.sin(x[0]) - D*x[1])]

def integra(Pm, t_final, x0=(d0, 0.0), n=20001):
    t_eval = np.linspace(0.0, t_final, n)
    s = solve_ivp(f_nl, (0.0, t_final), list(x0), args=(Pm,),
                  method='DOP853', t_eval=t_eval, rtol=RTOL, atol=ATOL)
    return s.t, s.y[0], s.y[1]

def dinf(dPm):
    """Equilibrio exato: Pmax*sin(delta_inf) = Pm0 + dPm."""
    return float(np.arcsin((Pm0 + dPm)/Pmax))

# ===========================================================================
# (A) O limiar intrinseco do modelo e' NULO
# ===========================================================================
# Se o modelo tivesse limiar, existiria dPm > 0 abaixo do qual delta nao muda.
# Varre-se dPm por 9 ordens de grandeza e verifica-se que a razao
# (delta_inf - delta_0)/dPm permanece igual a 1/Ps ate onde a aritmetica permite.
T_LONGO = 200.0                            # >> 4/(zeta*wn) = 21,2 s
sweep_A = []
for dPm in [1e-2, 1e-3, 1e-4, 1e-6, 1e-8, 1e-10, 1e-11]:
    dd_exato = dinf(dPm) - d0
    linha = dict(dPm_pu=float(dPm),
                 ddelta_exato_rad=float(dd_exato),
                 ddelta_exato_deg=float(np.degrees(dd_exato)),
                 razao_exata_rad_por_pu=float(dd_exato/dPm),
                 desvio_rel_vs_1surPs_pc=float(100*abs(dd_exato/dPm - S_est)/S_est))
    if dPm in (1e-2, 1e-4, 1e-6, 1e-8, 1e-10):
        _, dsim, _ = integra(Pm0 + dPm, T_LONGO, n=401)
        dd_sim = float(dsim[-1] - d0)
        linha.update(ddelta_simulado_rad=dd_sim,
                     razao_simulada_rad_por_pu=float(dd_sim/dPm),
                     erro_sim_vs_exato_rad=float(abs(dd_sim - dd_exato)),
                     erro_sim_vs_exato_pc=float(100*abs(dd_sim-dd_exato)/abs(dd_exato)))
    sweep_A.append(linha)
R['A_limiar_intrinseco'] = dict(
    descricao='razao ddelta/dPm deve permanecer 1/Ps para qualquer dPm>0 se o limiar for nulo',
    S_est_rad_por_pu=float(S_est), varredura=sweep_A)

# ===========================================================================
# (B) Limiar imposto pela QUANTIZACAO do canal de medicao de delta
# ===========================================================================
# Canal de medicao de angulo com fundo de escala FS = 360 graus (angulo de
# sincrofasor, que envolve em +-180 graus) e conversor A/D de n bits.
# Criterio de deteccao garantida: a variacao precisa valer um quantum inteiro q
# (pior caso: ponto de operacao logo acima de uma transicao de codigo).
# Caso medio (ponto de operacao uniformemente distribuido no codigo): q/2.
FS_DEG = 360.0
FS_Pm = Pmax                               # fundo de escala da entrada: 0..Pmax pu
quant = []
for nbits in [8, 10, 12, 14, 16, 18]:
    q_deg = FS_DEG/2**nbits
    lim_Pm = float(np.radians(q_deg)*Ps)   # dPm = ddelta/S = ddelta*Ps
    quant.append(dict(bits=nbits,
                      q_deg=float(q_deg),
                      limiar_delta_garantido_deg=float(q_deg),
                      limiar_delta_medio_deg=float(q_deg/2),
                      limiar_Pm_garantido_pu=lim_Pm,
                      limiar_Pm_medio_pu=float(lim_Pm/2),
                      limiar_pc_FS_entrada=float(100*lim_Pm/FS_Pm),
                      limiar_pc_de_Pm0=float(100*lim_Pm/Pm0)))
R['B_limiar_quantizacao'] = dict(FS_delta_deg=FS_DEG, FS_Pm_pu=FS_Pm, varredura=quant)
Q12 = next(v for v in quant if v['bits'] == 12)

# ===========================================================================
# (C) Limiar imposto pelo RUIDO do canal de medicao de delta
# ===========================================================================
# Ruido gaussiano branco de desvio-padrao sigma_delta no angulo medido.
# Detector: diferenca entre a media de N amostras DEPOIS e a media de N
# amostras ANTES do degrau. sigma_diff = sigma*sqrt(2/N).
# Limite de decisao fixado por uma taxa de falso alarme alpha (unilateral);
# o limiar e' o ddelta que da probabilidade de deteccao Pd.
SIGMA_DEG = 0.02          # representativo (ver secao de limitacoes do relatorio)
ALPHA, PD = 1e-3, 0.95
FS_AMOSTRAGEM = 60.0      # quadros/s (taxa de reporte tipica de PMU)
z_a, z_b = float(norm.ppf(1-ALPHA)), float(norm.ppf(PD))
k_det = z_a + z_b

ruido = []
for N in [1, 6, 60, 600, 1200]:
    sig_diff = SIGMA_DEG*np.sqrt(2.0/N)
    lim_deg = float(k_det*sig_diff)
    ruido.append(dict(N_amostras=N, janela_s=float(N/FS_AMOSTRAGEM),
                      sigma_diff_deg=float(sig_diff),
                      limiar_delta_deg=lim_deg,
                      limiar_Pm_pu=float(np.radians(lim_deg)*Ps),
                      limiar_pc_FS_entrada=float(100*np.radians(lim_deg)*Ps/FS_Pm)))

# --- verificacao Monte Carlo do detector (N = 60, janela de 1 s)
N_MC, NTRIAL = 60, 200000
sig_diff_MC = SIGMA_DEG*np.sqrt(2.0/N_MC)
limite_decisao = z_a*sig_diff_MC
lim_MC_teorico = k_det*sig_diff_MC
def taxa_deteccao(ddelta_deg, ntrial=NTRIAL):
    est = RNG.normal(ddelta_deg, sig_diff_MC, ntrial)
    return float(np.mean(est > limite_decisao))
R['C_limiar_ruido'] = dict(
    sigma_delta_deg=SIGMA_DEG, alpha_falso_alarme=ALPHA, Pd_alvo=PD,
    z_alpha=z_a, z_Pd=z_b, k_deteccao=float(k_det),
    fs_amostragem_Hz=FS_AMOSTRAGEM, varredura=ruido,
    monte_carlo=dict(N=N_MC, n_ensaios=NTRIAL,
                     limite_decisao_deg=float(limite_decisao),
                     limiar_teorico_deg=float(lim_MC_teorico),
                     Pd_no_limiar_medida=taxa_deteccao(lim_MC_teorico),
                     taxa_falso_alarme_medida=taxa_deteccao(0.0),
                     Pd_em_metade_do_limiar=taxa_deteccao(lim_MC_teorico/2)))

# ===========================================================================
# (D) Limiar no PICO do transitorio x limiar em REGIME PERMANENTE
# ===========================================================================
# O sistema e' pouco amortecido (zeta = 0,0227): o primeiro pico da resposta ao
# degrau vale (1 + Mp) vezes o valor de regime. Detectar no pico amplifica o
# sinal por esse fator G -- mas encurta drasticamente a janela de media.
dPm_lin = 1e-3                              # degrau pequeno: regime linear
t_tr, d_tr, _ = integra(Pm0 + dPm_lin, 30.0, n=300001)
dd_tr = d_tr - d0
i_p = int(np.argmax(dd_tr))
dd_pico, t_pico = float(dd_tr[i_p]), float(t_tr[i_p])
dd_ss = dinf(dPm_lin) - d0
G = dd_pico/dd_ss
Mp_teorico = float(np.exp(-zeta*np.pi/np.sqrt(1-zeta**2)))

# Janela util em torno do pico: intervalo contiguo em que a resposta se mantem
# a menos de 1% abaixo do valor de pico. E' o que se pode promediar la'.
tol_pico = 0.01
piso_pico = dd_pico*(1-tol_pico)
j = i_p
while j > 0 and dd_tr[j] >= piso_pico: j -= 1
k = i_p
while k < len(dd_tr)-1 and dd_tr[k] >= piso_pico: k += 1
janela_pico = float(t_tr[k] - t_tr[j])
N_pico = max(1, int(np.floor(FS_AMOSTRAGEM*janela_pico)))

T_OBS_SS = 20.0                             # janela de observacao em regime [s]
N_ss = int(FS_AMOSTRAGEM*T_OBS_SS)
lim_ss_ruido = k_det*SIGMA_DEG*np.sqrt(2.0/N_ss)
lim_pico_ruido = k_det*SIGMA_DEG*np.sqrt(2.0/N_pico)/G
t_acomodacao = 4.0/(zeta*wn)

R['D_pico_vs_regime'] = dict(
    dPm_teste_pu=dPm_lin,
    Mp_simulado=float(G-1), Mp_teorico=Mp_teorico,
    ganho_transitorio_G=float(G),
    erro_G_vs_teoria_pc=float(100*abs(G-(1+Mp_teorico))/(1+Mp_teorico)),
    t_pico_s=t_pico, t_pico_teorico_s=float(np.pi/wd),
    t_acomodacao_2pc_s=float(t_acomodacao),
    janela_pico_1pc_s=janela_pico, N_amostras_no_pico=N_pico,
    T_observacao_regime_s=T_OBS_SS, N_amostras_regime=N_ss,
    # limitado por ruido
    limiar_delta_regime_deg=float(lim_ss_ruido),
    limiar_delta_pico_deg=float(lim_pico_ruido),
    razao_pico_sobre_regime_ruido=float(lim_pico_ruido/lim_ss_ruido),
    # limitado por quantizacao (12 bits): a media nao ajuda sem dither
    limiar_delta_regime_quant_deg=float(Q12['q_deg']),
    limiar_delta_pico_quant_deg=float(Q12['q_deg']/G),
    razao_pico_sobre_regime_quant=float(1.0/G),
    limiar_Pm_pico_quant_pu=float(np.radians(Q12['q_deg']/G)*Ps))

# ===========================================================================
# (E) Dependencia do limiar com o ponto de operacao
# ===========================================================================
# Ps = Pmax*cos(delta_0) -> a sensibilidade estatica 1/Ps cresce sem limite
# quando delta_0 -> 90 graus. O limiar referido a' ENTRADA cai na mesma medida.
op = []
for d0g in [10.0, 23.578178, 45.0, 60.0, 75.0, 85.0]:
    dr = np.radians(d0g)
    Ps_i = Pmax*np.cos(dr)
    z_i = (D/2.0)*np.sqrt(ws/(2*H*Ps_i))
    wn_i = np.sqrt(ws*Ps_i/(2*H))
    op.append(dict(delta0_deg=d0g, Pm0_pu=float(Pmax*np.sin(dr)),
                   Ps_pu_por_rad=float(Ps_i),
                   sensibilidade_graus_por_pu=float(np.degrees(1.0/Ps_i)),
                   limiar_Pm_12bits_pu=float(np.radians(Q12['q_deg'])*Ps_i),
                   limiar_pc_FS_entrada=float(100*np.radians(Q12['q_deg'])*Ps_i/FS_Pm),
                   zeta=float(z_i), wn_rad_s=float(wn_i)))
R['E_ponto_de_operacao'] = dict(bits=12, q_deg=Q12['q_deg'], varredura=op)

# ===========================================================================
# (F) Limiar da CADEIA COMPLETA: quantizacao + ruido, e o papel do dither
# ===========================================================================
# Quantizacao e ruido nao se somam trivialmente. Se o ruido for pequeno frente
# ao quantum (sigma < q/2), a media de varias amostras NAO desce abaixo de q:
# o conversor devolve sempre o mesmo codigo e a media nao tem o que promediar.
# Se o ruido for da ordem do quantum (sigma >= q/2), ele atua como DITHER
# natural: a quantizacao passa a se comportar como um ruido adicional de
# variancia q^2/12, que se soma em quadratura a sigma, e a media volta a
# funcionar -- recuperando resolucao abaixo de 1 LSB.
N_MEDIA = 1200                      # 20 s a 60 quadros/s
LIMIAR_DITHER = 0.5                 # sigma/q a partir do qual o dither e' efetivo
cadeia = []
for v in quant:
    q_i = v['q_deg']
    razao = SIGMA_DEG/q_i
    dither_ok = bool(razao >= LIMIAR_DITHER)
    sigma_eff = float(np.sqrt(SIGMA_DEG**2 + q_i**2/12.0))
    lim_ruido_i = float(k_det*sigma_eff*np.sqrt(2.0/N_MEDIA))
    lim_cadeia = lim_ruido_i if dither_ok else q_i        # sem dither, o piso e' o quantum
    cadeia.append(dict(bits=v['bits'], q_deg=q_i,
                       sigma_sobre_q=float(razao), dither_efetivo=dither_ok,
                       sigma_efetivo_deg=sigma_eff,
                       limiar_so_quantizacao_deg=q_i,
                       limiar_so_ruido_deg=float(k_det*SIGMA_DEG*np.sqrt(2.0/N_MEDIA)),
                       limiar_cadeia_deg=float(lim_cadeia),
                       limiar_cadeia_Pm_pu=float(np.radians(lim_cadeia)*Ps),
                       limiar_cadeia_pc_FS=float(100*np.radians(lim_cadeia)*Ps/FS_Pm),
                       mecanismo_dominante='quantizacao' if not dither_ok else 'ruido'))
g12 = next(c for c in cadeia if c['bits'] == 12)
g14 = next(c for c in cadeia if c['bits'] == 14)
g16 = next(c for c in cadeia if c['bits'] == 16)
R['F_limiar_da_cadeia'] = dict(
    N_media=N_MEDIA, T_media_s=float(N_MEDIA/FS_AMOSTRAGEM),
    criterio_dither_sigma_sobre_q=LIMIAR_DITHER, varredura=cadeia,
    ganho_12_para_14_bits=float(g12['limiar_cadeia_Pm_pu']/g14['limiar_cadeia_Pm_pu']),
    ganho_14_para_16_bits=float(g14['limiar_cadeia_Pm_pu']/g16['limiar_cadeia_Pm_pu']),
    # conversao ILUSTRATIVA para unidade de engenharia (base nao declarada no v2)
    ilustracao_base_100MVA_kW=float(1e5*g14['limiar_cadeia_Pm_pu']))

with open(os.path.join(AQUI, 'resultados_limiar.json'), 'w') as fh:
    json.dump(R, fh, indent=2)

# ===========================================================================
# FIGURA 1 - limiar por quantizacao (o grafico que mostra o limiar)
# ===========================================================================
q12 = Q12['q_deg']
lim12_Pm = Q12['limiar_Pm_garantido_pu']

def quantiza(delta_deg):
    """Quantizador uniforme com delta_0 exatamente sobre uma transicao de codigo
       (pior caso do limiar: e' preciso um quantum inteiro para mudar de codigo)."""
    return np.floor((delta_deg - np.degrees(d0))/q12)*q12 + np.degrees(d0)

fig, ax = plt.subplots(3, 1, figsize=(7.4, 7.6), sharex=True)
casos = [(0.40, '#2e7d32', r'$\Delta P_m = 0{,}40\times$ limiar'),
         (0.60, '#1f4e79', r'$\Delta P_m = 0{,}60\times$ limiar'),
         (1.20, '#c00000', r'$\Delta P_m = 1{,}20\times$ limiar')]
for eixo, (fat, cor, rot) in zip(ax, casos):
    tt, ddg, _ = integra(Pm0 + fat*lim12_Pm, 3.0, n=60001)
    y = np.degrees(ddg) - np.degrees(d0)
    yq = quantiza(np.degrees(ddg)) - np.degrees(d0)
    eixo.plot(tt, y, lw=1.5, color=cor, label=rot + ' (grandeza real)')
    eixo.step(tt, yq, where='post', lw=1.2, color='#444444',
              label='saida do conversor A/D de 12 bits')
    eixo.axhline(0, color='k', lw=0.6, alpha=.5)
    eixo.axhline(q12, color='k', lw=0.7, ls=':', alpha=.8)
    eixo.text(2.92, q12*1.06, r'1 LSB $= q = %.4f^\circ$' % q12,
              ha='right', va='bottom', fontsize=7.5)
    eixo.set_ylim(-0.04*q12, 2.55*q12)
    eixo.set_ylabel(r'$\delta-\delta_0$  [graus]')
    eixo.legend(loc='center right', fontsize=7.4, framealpha=.95)
ax[0].set_title(r'Limiar por quantizacao: $\Delta P_m$ abaixo do limiar nao produz'
                '\n' r'nenhuma mudanca de codigo na saida', pad=8, fontsize=10)
ax[-1].set_xlabel('tempo [s]')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'limiar_quantizacao.pdf')); plt.close(fig)

# ===========================================================================
# FIGURA 2 - limiar por ruido: curva de probabilidade de deteccao
# ===========================================================================
fig2, ax2 = plt.subplots(figsize=(6.4, 4.4))
for N, cor in [(60, '#c00000'), (1200, '#1f4e79')]:
    sd = SIGMA_DEG*np.sqrt(2.0/N)
    lim_N = k_det*sd
    xg = np.linspace(0, 2.0*lim_N, 400)
    pd_teo = norm.sf((z_a*sd - xg)/sd)
    ax2.plot(1e3*xg, 100*pd_teo, lw=1.5, color=cor,
             label=r'$N=%d$ (%.2f s) $\rightarrow$ limiar $=%.4f^\circ$' % (N, N/FS_AMOSTRAGEM, lim_N))
    # Monte Carlo
    xmc = np.linspace(0, 2.0*lim_N, 11)
    pmc = []
    for xv in xmc:
        est = RNG.normal(xv, sd, 40000)
        pmc.append(100*np.mean(est > z_a*sd))
    ax2.plot(1e3*xmc, pmc, 'o', ms=4.0, color=cor, mfc='none', mew=1.1)
    ax2.plot([1e3*lim_N, 1e3*lim_N], [0, 95], ls=':', lw=0.9, color=cor)
ax2.axhline(100*PD, color='k', lw=0.7, ls='--', alpha=.7)
ax2.text(0.30, 0.80, r'$P_d = 95\%$ (definicao adotada de limiar)',
         transform=ax2.transAxes, fontsize=8, va='bottom')
ax2.set_xlabel(r'variacao real da saida  $\Delta\delta$  [$10^{-3}$ graus]')
ax2.set_ylabel(r'probabilidade de deteccao  [\%]'.replace('\\%', '%'))
ax2.set_title(u'Limiar por ruido: curva de deteccao (linhas = teoria, circulos = Monte Carlo)',
              fontsize=9.5)
ax2.legend(loc='lower right', fontsize=8)
ax2.set_ylim(-3, 105)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'limiar_ruido.pdf')); plt.close(fig2)

# ===========================================================================
# FIGURA 3 - limiar x ponto de operacao
# ===========================================================================
dg = np.linspace(5.0, 88.0, 500)
Ps_g = Pmax*np.cos(np.radians(dg))
lim_g = np.radians(q12)*Ps_g
fig3, ax3 = plt.subplots(figsize=(6.4, 4.3))
ax3.plot(dg, 1e3*lim_g, lw=1.7, color='#1f4e79')
ax3.plot([np.degrees(d0)], [1e3*lim12_Pm], 'o', ms=6, color='#c00000', zorder=5)
ax3.annotate(r'ponto de operacao do projeto''\n'r'$\delta_0=23{,}58^\circ$: limiar $=%.2f\times10^{-3}$ pu'
             % (1e3*lim12_Pm),
             xy=(np.degrees(d0), 1e3*lim12_Pm), xytext=(34, 1e3*lim12_Pm*1.02),
             fontsize=8, arrowprops=dict(arrowstyle='->', lw=0.8))
ax3.set_xlabel(r'ponto de operacao  $\delta_0$  [graus]')
ax3.set_ylabel(r'limiar em $P_m$ (12 bits)  [$10^{-3}$ pu]')
ax3.set_title(u'O limiar nao e constante: melhora conforme a maquina se aproxima\n'
              u'do limite de estabilidade ($P_s = P_{max}\\cos\\delta_0 \\rightarrow 0$)',
              fontsize=9.5)
ax3.set_xlim(5, 88); ax3.set_ylim(0, 1e3*np.radians(q12)*Pmax*np.cos(np.radians(5.0))*1.05)
fig3.tight_layout(); fig3.savefig(os.path.join(FIG, 'limiar_ponto_operacao.pdf')); plt.close(fig3)

# ------------------------------------------------------------- resumo em tela
print('delta0 = %.6f rad = %.4f deg | Ps = %.6f pu/rad | S = 1/Ps = %.4f deg/pu'
      % (d0, np.degrees(d0), Ps, np.degrees(S_est)))
print('\n(A) limiar intrinseco -- razao ddelta/dPm (exata) deve ser %.6f rad/pu' % S_est)
for L in sweep_A:
    ex = '  sim: %.6f rad/pu (erro %.3e %%)' % (L['razao_simulada_rad_por_pu'], L['erro_sim_vs_exato_pc']) \
         if 'razao_simulada_rad_por_pu' in L else ''
    print('  dPm=%8.1e  exata=%.6f rad/pu  desvio=%.3e %%%s'
          % (L['dPm_pu'], L['razao_exata_rad_por_pu'], L['desvio_rel_vs_1surPs_pc'], ex))
print('\n(B) limiar por quantizacao (FS = 360 graus):')
for v in quant:
    print('  %2d bits  q=%.6f deg  limiar_Pm=%.4e pu  (%.4f %% do FS de entrada)'
          % (v['bits'], v['q_deg'], v['limiar_Pm_garantido_pu'], v['limiar_pc_FS_entrada']))
print('\n(C) limiar por ruido (sigma=%.3f deg, alpha=%.0e, Pd=%.2f, k=%.4f):'
      % (SIGMA_DEG, ALPHA, PD, k_det))
for v in ruido:
    print('  N=%5d (%6.2f s)  limiar_delta=%.6f deg  limiar_Pm=%.4e pu (%.4f %% FS)'
          % (v['N_amostras'], v['janela_s'], v['limiar_delta_deg'],
             v['limiar_Pm_pu'], v['limiar_pc_FS_entrada']))
mc = R['C_limiar_ruido']['monte_carlo']
print('  Monte Carlo N=60: Pd(limiar)=%.4f (alvo %.2f) | falso alarme=%.5f (alvo %.0e) | Pd(limiar/2)=%.4f'
      % (mc['Pd_no_limiar_medida'], PD, mc['taxa_falso_alarme_medida'], ALPHA, mc['Pd_em_metade_do_limiar']))
d_ = R['D_pico_vs_regime']
print('\n(D) pico x regime:')
print('  G = 1+Mp = %.5f (teoria %.5f, erro %.3e %%) | t_pico=%.4f s (teoria %.4f s) | t_acom=%.2f s'
      % (d_['ganho_transitorio_G'], 1+Mp_teorico, d_['erro_G_vs_teoria_pc'],
         d_['t_pico_s'], d_['t_pico_teorico_s'], d_['t_acomodacao_2pc_s']))
print('  janela util do pico (1%%): %.4f s -> N=%d amostras a 60 Hz (regime: N=%d em 20 s)'
      % (d_['janela_pico_1pc_s'], d_['N_amostras_no_pico'], d_['N_amostras_regime']))
print('  limitado por RUIDO: limiar_pico=%.6f deg x limiar_regime=%.6f deg -> pico e %.2fx PIOR'
      % (d_['limiar_delta_pico_deg'], d_['limiar_delta_regime_deg'], d_['razao_pico_sobre_regime_ruido']))
print('  limitado por QUANTIZACAO: pico e %.4fx o regime -> %.2fx MELHOR'
      % (d_['razao_pico_sobre_regime_quant'], 1/d_['razao_pico_sobre_regime_quant']))
print('\n(E) limiar x ponto de operacao (12 bits):')
for v in op:
    print('  delta0=%6.2f deg  Pm0=%.4f pu  Ps=%.5f  S=%7.2f deg/pu  limiar_Pm=%.4e pu (%.4f %% FS)  zeta=%.5f'
          % (v['delta0_deg'], v['Pm0_pu'], v['Ps_pu_por_rad'], v['sensibilidade_graus_por_pu'],
             v['limiar_Pm_12bits_pu'], v['limiar_pc_FS_entrada'], v['zeta']))
print('\n(F) limiar da cadeia completa (media de %d amostras = %.0f s, sigma=%.3f deg):' % (N_MEDIA, N_MEDIA/FS_AMOSTRAGEM, SIGMA_DEG))
for c in cadeia:
    print('  %2d bits  q=%.6f deg  sigma/q=%6.3f  dither=%-5s  limiar_cadeia=%.6f deg = %.4e pu (%.4f %% FS)  [%s]'
          % (c['bits'], c['q_deg'], c['sigma_sobre_q'], c['dither_efetivo'],
             c['limiar_cadeia_deg'], c['limiar_cadeia_Pm_pu'], c['limiar_cadeia_pc_FS'],
             c['mecanismo_dominante']))
print('  ganho 12 -> 14 bits: %.2fx   |   ganho 14 -> 16 bits: %.3fx  (ja limitado por ruido)'
      % (R['F_limiar_da_cadeia']['ganho_12_para_14_bits'], R['F_limiar_da_cadeia']['ganho_14_para_16_bits']))
print('  ilustracao: em uma base de 100 MVA, o limiar de 14 bits equivale a %.2f kW'
      % R['F_limiar_da_cadeia']['ilustracao_base_100MVA_kW'])

print('\nOK - figuras em figs/, resultados em resultados_limiar.json')
