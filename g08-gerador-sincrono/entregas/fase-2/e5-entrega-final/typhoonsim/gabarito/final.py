# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega Final: instrumentacao nao ideal e seus efeitos no controle.

Reorganiza as entregas 01-04 pelos itens do Quadro 1 e acrescenta o que elas nao tinham:

  item 3  assinatura de cada caracteristica num ensaio de bancada (onda sintetica no TP)
  item 4  malha aberta com CADA caracteristica ligada SOZINHA (a E03 desligava uma de cada vez)
  item 5  controle com a medicao ideal (criterios do R1 da E04)
  item 6  o mesmo controle com a medicao real: referencia x medido x real da planta
  item 7  ponto de ruptura: a previsao (modelo linear / formula) e' calculada e gravada ANTES das
          simulacoes nao lineares; depois, a varredura por niveis (a mesma da E04) e a bissecao do limiar
  item 8  compensacao (pre-filtro passa-faixa, metodo da filtragem do Cap. 2) e o ganho sobre o item 7

Tudo roda no gabarito Python do modelo do TyphoonSim (sistema.py: os mesmos blocos e coeficientes do .tse;
confere_fiacao.py executa a fiacao do .tse bloco a bloco com diferenca <= 1e-12). As capturas do Virtual HIL
das E03/E04 estao em ../dados e sao comparadas por compara_typhoon.py.

Saidas: ../../relatorio/figuras/fig-*.png (as figuras de dados do relatorio), resultados_final.json
Uso:    python final.py            (numpy, scipy, matplotlib; ~8 min)
"""
import json
import math
import os
import sys
import time
from datetime import datetime

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.dont_write_bytecode = True
import parametros_e34 as P          # noqa: E402
import sistema as S                 # noqa: E402
import controle as K                # noqa: E402
import estilo as E                  # noqa: E402
import e03 as E3                    # noqa: E402
import e04 as E4                    # noqa: E402

G = np.degrees
CHAVES = ('eps_tp', 'tau_rms', 'nbits', 'sigma', 'n_cic', 'fclk')
SAIDA = os.path.join(AQUI, 'resultados_final.json')
T0 = time.time()


def log(*a):
    print('[%5.0f s]' % (time.time() - T0), *a, flush=True)


def estilo_final():
    """Estilo das entregas anteriores, com letras maiores: as mesmas figuras vao para os slides."""
    E.aplica_estilo()
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10.5, 'axes.titlesize': 10.5, 'axes.labelsize': 10.5,
                         'legend.fontsize': 8.8, 'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5,
                         'lines.linewidth': 1.6})


# =========================================================================== item 3: assinaturas
def cfg_so(ch, valor=None, **kw):
    """Cadeia com UMA caracteristica ligada. Ruido e relogio so' agem dentro do frequencimetro: para eles a
    estrutura do frequencimetro fica ligada com N = 1 (periodo de cada ciclo, sem media)."""
    c = dict(P.NEUTRO)
    if ch is not None:
        c[ch] = P.REAL[ch] if valor is None else valor
        if ch in ('sigma', 'fclk'):
            c['n_cic'] = 1.0
    c.update(kw)
    return S.cfg_padrao(**c)


def t90(t, x, t_ev=0.5):
    x0, x1 = x[t < t_ev].mean(), x[t > t[-1] - 0.3].mean()
    j = np.where((t >= t_ev) & (np.abs(x - x0) >= 0.9*abs(x1 - x0)))[0]
    return float(1e3*(t[j[0]] - t_ev)) if len(j) else float('nan')


def item3():
    out, curvas = {}, {}
    # AD637 sozinho: degrau de amplitude 1,00 -> 1,10 pu
    r = S.simula(S.ensaio('banco_v'), cfg_so('tau_rms'))
    out['t90_V_ms'] = t90(r['t'], r['V_re']); curvas['V'] = r
    # media de N ciclos sozinha (N = 4) e estrutura (N = 1): degrau 60,0 -> 60,1 Hz
    r4 = S.simula(S.ensaio('banco_f'), cfg_so('n_cic'))
    r1 = S.simula(S.ensaio('banco_f'), cfg_so('n_cic', 1.0))
    out['t90_f_ms'] = t90(r4['t'], r4['f_re']); out['t90_f_N1_ms'] = t90(r1['t'], r1['f_re'])
    curvas['f4'], curvas['f1'] = r4, r1
    # ruido sozinho (N = 1) e com a media do instrumento real (N = 4): 1 pu, 60 Hz
    rs1 = S.simula(S.ensaio('banco_0'), cfg_so('sigma'))
    rs4 = S.simula(S.ensaio('banco_0'), cfg_so('sigma', n_cic=4.0))
    rc1 = S.simula(S.ensaio('banco_0'), cfg_so('fclk'))
    for nome, rr in (('ruido_N1', rs1), ('ruido_N4', rs4), ('relogio_N1', rc1)):
        i = rr['t'] > 0.3
        out['dp_f_%s_mHz' % nome] = float(1e3*np.std(rr['f_re'][i]))
    curvas['s1'], curvas['s4'] = rs1, rs4
    # estatico: erro da leitura em funcao de V (TP e ADC), formula dos blocos
    v = np.linspace(1.060, 1.090, 3001)
    lsb = P.VREF_ADC/2**P.REAL['nbits']
    tp = (1 + P.REAL['eps_tp']/100)*v
    adc = np.round(v*P.V_PU_VD/lsb)*lsb/P.V_PU_VD
    ambos = np.round(tp*P.V_PU_VD/lsb)*lsb/P.V_PU_VD
    curvas['estatica'] = dict(v=v, tp=100*(tp/v - 1), adc=100*(adc/v - 1), ambos=100*(ambos/v - 1))
    out['lsb_pct'] = 100*lsb/P.V_PU_VD
    out['resol_f_ciclo_mHz'] = 1e3*P.F_REDE**2/P.REAL['fclk']
    return out, curvas


def fig_assinaturas(A, C):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(13.2, 3.3))
    st = C['estatica']
    ax[0].plot(st['v'], st['adc'], color=E.AMARELO, lw=1.2, label='só ADC 12 bits (±½ LSB)')
    ax[0].plot(st['v'], st['tp'], color=E.AZUL, lw=2.0, label='só TP classe 0,3')
    ax[0].set_ylim(-0.1, 0.45); ax[0].set_xlabel('V real [pu]'); ax[0].set_ylabel('erro da leitura [%]')
    ax[0].set_title('(a) Estática: TP e ADC'); ax[0].legend(loc='center right')
    r = C['V']; t = r['t'] - 0.5; k = (t > -0.1) & (t < 0.45)
    ax[1].plot(t[k], r['V_id'][k], color=E.CINZA, lw=2.6, alpha=0.6, label='entrada (ideal)')
    ax[1].plot(t[k], r['V_re'][k], color=E.LARANJA, label='só AD637 + Sallen-Key')
    ax[1].axvline(A['t90_V_ms']/1e3, color=E.TINTA2, lw=0.8, ls=':')
    ax[1].text(A['t90_V_ms']/1e3 + 0.01, 1.02, 't₉₀ = %s ms' % E.num(A['t90_V_ms'], 0), fontsize=9.5)
    ax[1].set_xlabel('t após o degrau [s]'); ax[1].set_ylabel('V [pu]'); ax[1].set_title('(b) Dinâmica: conversor RMS')
    ax[1].legend(loc='lower right')
    for rr, cor, rot in ((C['s1'], E.MAGENTA, 'N = 1: σ = %s mHz' % E.num(A['dp_f_ruido_N1_mHz'], 1)),
                         (C['s4'], E.VIOLETA, 'N = 4: σ = %s mHz' % E.num(A['dp_f_ruido_N4_mHz'], 1))):
        t = rr['t']; k = (t > 0.3) & (t < 1.3)
        ax[2].plot(t[k] - 0.3, 1e3*(rr['f_re'][k] - 60.0), color=cor, lw=1.0, label=rot)
    ax[2].set_xlabel('t [s]'); ax[2].set_ylabel('f medida − 60 Hz [mHz]')
    ax[2].set_title('(c) Espúria: 5 mV de ruído'); ax[2].legend(loc='upper right', fontsize=8.3)
    for rr, cor, rot in ((C['f1'], E.CINZA, 'N = 1 (sem média)'), (C['f4'], E.VIOLETA, 'N = 4 (instrumento)')):
        t = rr['t'] - 0.5; k = (t > -0.1) & (t < 0.45)
        ax[3].plot(t[k], 1e3*(rr['f_re'][k] - 60.0), color=cor, lw=1.4 if cor == E.VIOLETA else 1.0, label=rot)
    t = C['f4']['t'] - 0.5; k = (t > -0.1) & (t < 0.45)
    ax[3].plot(t[k], 1e3*(C['f4']['f_id'][k] - 60.0), color=E.CINZA, lw=2.6, alpha=0.4, label='entrada (ideal)')
    ax[3].axvline(A['t90_f_ms']/1e3, color=E.TINTA2, lw=0.8, ls=':')
    ax[3].text(A['t90_f_ms']/1e3 + 0.01, 55, 't₉₀ = %s ms' % E.num(A['t90_f_ms'], 0), fontsize=9.5)
    ax[3].set_xlabel('t após o degrau [s]'); ax[3].set_ylabel('f − 60 Hz [mHz]')
    ax[3].set_title('(d) Processamento: média de N ciclos'); ax[3].legend(loc='lower right', fontsize=8.3)
    for a in ax:
        E.virgula(a)
    fig.tight_layout()
    E.salva(fig, 'fig-04-assinaturas')


# =========================================================================== item 4: cada uma sozinha
def item4():
    """Ensaios (a) degrau de Pm e (c) falta de 200 ms com: a cadeia real inteira; cada caracteristica sozinha;
    a estrutura do frequencimetro sem caracteristicas (N = 1). Erro = leitura real - leitura ideal."""
    out, curvas = {}, {}
    for ens in 'ac':
        out[ens], curvas[ens] = {}, {}
        casos = [('todas', S.cfg_padrao()), ('nenhuma', cfg_so(None)), ('estrutura_f', cfg_so('n_cic', 1.0))]
        casos += [('so_' + ch, cfg_so(ch)) for ch in CHAVES]
        for nome, cfg in casos:
            r = S.simula(S.ensaio(ens), cfg)
            m = E3.metricas(r)
            out[ens][nome] = dict(V=m['V'], f=m['f'])
            curvas[ens][nome] = r
        log('item 4, ensaio', ens)
    # parcela de cada uma na variancia do erro (as caracteristicas sao quase independentes)
    for ens in 'ac':
        o = out[ens]
        for gr, chs in (('V', ('eps_tp', 'tau_rms', 'nbits', 'sigma')), ('f', ('n_cic', 'sigma', 'fclk'))):
            soma = sum(o['so_' + c][gr]['err_rms']**2 for c in chs)
            o['parcela_' + gr] = {c: 100*o['so_' + c][gr]['err_rms']**2/soma for c in chs}
            o['soma_quadratica_' + gr] = math.sqrt(soma)
    return out, curvas


ROT = dict(eps_tp='só TP (ε = 0,3 %)', tau_rms='só AD637 (τ = 55 ms)', nbits='só ADC (12 bits)',
           sigma='só ruído (5 mV)', n_cic='só média N = 4', fclk='só relógio 1 MHz')
COR = dict(eps_tp=E.AZUL, tau_rms=E.LARANJA, nbits=E.AMARELO, sigma=E.MAGENTA, n_cic=E.VIOLETA, fclk=E.AQUA)


def fig_isoladas(R, C):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(13.2, 6.2), gridspec_kw=dict(width_ratios=[1.25, 1.25, 1]))
    c = C['a']; t = c['todas']['t']; k = (t > 0.85) & (t < 3.2)
    # tensao
    ax[0, 0].plot(t[k], c['todas']['V_id'][k], color=E.CINZA, lw=3.0, alpha=0.5, label='ideal (= planta)')
    for ch in ('eps_tp', 'tau_rms'):
        ax[0, 0].plot(t[k], c['so_' + ch]['V_re'][k], color=COR[ch], lw=1.4, label=ROT[ch])
    ax[0, 0].plot(t[k], c['todas']['V_re'][k], color=E.TINTA, lw=1.0, ls='--', label='real (todas)')
    ax[0, 0].set_title('Tensão lida: o TP desloca, o AD637 atrasa'); ax[0, 0].set_ylabel('V [pu]')
    ax[0, 0].legend(loc='upper right', fontsize=8.2, ncol=2)
    lo, hi = c['todas']['V_id'][k].min(), c['todas']['V_re'][k].max()
    ax[0, 0].set_ylim(lo - 0.002, hi + 0.006)
    kz = (t > 1.25) & (t < 1.75)
    ax[0, 1].plot(t[kz], c['todas']['V_id'][kz], color=E.CINZA, lw=3.0, alpha=0.5, label='ideal')
    for ch in ('nbits', 'sigma'):
        ax[0, 1].plot(t[kz], c['so_' + ch]['V_re'][kz], color=COR[ch], lw=1.2, label=ROT[ch])
    ax[0, 1].set_title('Zoom: ADC e ruído quase não aparecem na tensão'); ax[0, 1].legend(loc='upper left', fontsize=8.2)
    # frequencia
    fid, _ = E3.limpa_f(t, c['todas']['f_id'])
    ax[1, 0].plot(t[k], fid[k], color=E.CINZA, lw=3.0, alpha=0.5, label='ideal (terminais)')
    ax[1, 0].plot(t[k], c['so_n_cic']['f_re'][k], color=COR['n_cic'], lw=1.4, label=ROT['n_cic'])
    ax[1, 0].plot(t[k], c['todas']['f_re'][k], color=E.TINTA, lw=1.0, ls='--', label='real (todas)')
    ax[1, 0].set_title('Frequência lida: a média de N ciclos atrasa'); ax[1, 0].set_ylabel('f [Hz]')
    ax[1, 0].legend(loc='upper right', fontsize=8.2)
    ax[1, 1].plot(t[kz], fid[kz], color=E.CINZA, lw=3.0, alpha=0.5, label='ideal')
    for ch in ('sigma', 'fclk'):
        ax[1, 1].plot(t[kz], c['so_' + ch]['f_re'][kz], color=COR[ch], lw=1.1, label=ROT[ch] + ', N = 1')
    ax[1, 1].set_title('Zoom: o ruído aparece na frequência'); ax[1, 1].legend(loc='upper left', fontsize=8.2)
    for a in ax[:, :2].flat:
        a.set_xlabel('t [s]'); E.virgula(a)
    # barras: erro RMS de cada uma sozinha x todas
    o = R['a']
    for i, (gr, chs, esc, un) in enumerate((('V', ('eps_tp', 'tau_rms', 'nbits', 'sigma'), 1e3, 'mpu'),
                                            ('f', ('n_cic', 'sigma', 'fclk'), 1e3, 'mHz'))):
        nomes = ['todas'] + ['so_' + ch for ch in chs] + (['estrutura_f'] if gr == 'f' else [])
        vals = [esc*o[n][gr]['err_rms'] for n in nomes]
        cores = [E.TINTA] + [COR[ch] for ch in chs] + (['#cfcdc6'] if gr == 'f' else [])
        rot = ['real (todas)'] + [ROT[ch].replace('só ', '') + (', N = 1' if ch in ('sigma', 'fclk') else '') for ch in chs] +             (['referência: N = 1 sozinho'] if gr == 'f' else [])
        y = np.arange(len(nomes))[::-1]
        ax[i, 2].barh(y, vals, color=cores, height=0.62)
        for yy, v_ in zip(y, vals):
            ax[i, 2].text(v_ + max(vals)*0.02, yy, E.num(v_, 2 if v_ < 1 else 1), va='center', fontsize=9)
        ax[i, 2].set_yticks(y); ax[i, 2].set_yticklabels(rot, fontsize=9)
        ax[i, 2].set_xlim(0, max(vals)*1.3); ax[i, 2].grid(axis='y', visible=False)
        ax[i, 2].set_xlabel('erro RMS da leitura [%s]' % un)
        ax[i, 2].set_title('Quanto cada uma contribui (%s)' % ('tensão' if gr == 'V' else 'frequência'))
        ax[i, 2].xaxis.set_major_formatter(__import__('matplotlib.ticker', fromlist=['FuncFormatter']).FuncFormatter(lambda x, p: E.num(x, 1)))
    fig.tight_layout()
    E.salva(fig, 'fig-05-malha-aberta-isoladas')


# =========================================================================== itens 5 e 6
def metr(cfg):
    m, runs = E4.metricas(cfg)
    return m, runs


def falta(cfg):
    r = S.simula(S.ensaio('f'), cfg)
    t = r['t']; v = E4.media_movel(r['V_id'], 10)
    fora = np.where((t > P.T_EV + P.DUR_FALTA) & (np.abs(v - r['Vref']) > 0.05*P.VT0))[0]
    return dict(delta_max=float(G(r['delta']).max()), V_min=float(r['V_id'].min()),
                t_recupera_5pct_s=float(t[fora[-1]] - P.T_EV - P.DUR_FALTA) if len(fora) else 0.0,
                efd_teto_s=float(np.sum(r['Efd'] >= P.EFD_MAX - 1e-9)*(t[1] - t[0]))), r


def fig_ideal(m, runs):
    import matplotlib.pyplot as plt
    rr, rp, r0 = runs
    fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.5))
    t = rr['t']; k = (t > 0.7) & (t < 4.0)
    v1 = P.VT0 + P.DVREF
    ax[0].axhspan(v1 - 0.1*P.DVREF, v1 + 0.1*P.DVREF, color=E.FAIXA, zorder=0, label='±10 % do degrau (t_s)')
    ax[0].axhline(v1 + 0.15*P.DVREF, color=E.CRITICO, lw=0.8, ls=':', label='limite de sobressinal (15 %)')
    ax[0].plot(t[k], (rr['Vref'] - rr['upss'])[k], color=E.CRITICO, lw=1.0, ls='--', label='referência')
    ax[0].plot(t[k], rr['V_id'][k], color=E.TINTA, lw=1.6, label='tensão da planta')
    ax[0].set_title('Degrau de Vref: M_p = %s %%, t_s = %s s' % (E.num(m['planta']['Mp_pct'], 1), E.num(m['planta']['ts_s'], 2)))
    ax[0].set_ylabel('V [pu]'); ax[0].legend(loc='lower right', fontsize=8.2)
    tp = rp['t']; kp = (tp > 0.7) & (tp < 8)
    ax[1].plot(tp[kp], G(rp['delta'][kp]), color=E.AZUL, lw=1.4)
    ax[1].set_title('Degrau de Pm: ζ = %s (≥ 0,10)' % E.num(m['zeta'], 3)); ax[1].set_ylabel('δ [°]')
    ax[1].text(0.97, 0.06, 'afundamento de Vt: %s %% (≤ 1,5 %%)' % E.num(m['planta']['afund_pct'], 2),
               transform=ax[1].transAxes, ha='right', fontsize=9)
    ax[2].plot(t[k], rr['Efd'][k], color=E.LARANJA, lw=1.2, label='degrau de Vref')
    ax[2].axhline(P.EFD_MAX, color=E.CRITICO, lw=0.8, ls=':', label='teto da excitatriz (6 pu)')
    ax[2].set_ylim(0, 6.6)
    ax[2].set_title('Esforço: Efd pico %s pu, σ(Efd) = %s' % (E.num(m['efd_pico'], 2), E.num(m['dp_efd'], 3)))
    ax[2].set_ylabel('Efd [pu]'); ax[2].legend(loc='upper right', fontsize=8.2)
    for a in ax:
        a.set_xlabel('t [s]'); E.virgula(a)
    fig.tight_layout()
    E.salva(fig, 'fig-07-controle-ideal')


def fig_real(mi, ri, mr, rrl):
    import matplotlib.pyplot as plt
    rri, rpi, r0i = ri
    rr, rp, r0 = rrl
    fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.7))
    t = rr['t']; k = (t > 0.7) & (t < 4.0)
    ax[0].plot(rri['t'][k], rri['V_id'][k], color=E.CINZA, lw=3.0, alpha=0.45, label='planta, medição ideal')
    ax[0].plot(t[k], (rr['Vref'] - rr['upss'])[k], color=E.CRITICO, lw=1.0, ls='--', label='referência')
    ax[0].plot(t[k], E4.media_movel(rr['V_re'], 10)[k], color=E.AZUL, lw=1.2, label='tensão medida (realimentada)')
    ax[0].plot(t[k], rr['V_id'][k], color=E.TINTA, lw=1.6, label='tensão real da planta')
    ax[0].set_title('Degrau de Vref: a planta fica %s %% abaixo' % E.num(mr['planta']['ess_pct'], 2))
    ax[0].set_ylabel('V [pu]'); ax[0].legend(loc='lower right', fontsize=8.2)
    tp = rp['t']; kp = (tp > 0.7) & (tp < 8)
    ax[1].plot(rpi['t'][kp], G(rpi['delta'][kp]), color=E.CINZA, lw=3.0, alpha=0.45, label='medição ideal: ζ = %s' % E.num(mi['zeta'], 3))
    ax[1].plot(tp[kp], G(rp['delta'][kp]), color=E.TINTA, lw=1.3, label='medição real: ζ = %s' % E.num(mr['zeta'], 3))
    ax[1].set_title('Degrau de Pm: o rotor continua amortecido'); ax[1].set_ylabel('δ [°]')
    ax[1].legend(loc='lower right', fontsize=8.2)
    t0 = r0['t']; k0 = t0 > 0.2
    ax[2].plot(t0[k0], r0i['Efd'][k0], color=E.CINZA, lw=2.2, alpha=0.6, label='medição ideal: σ = %s' % E.num(mi['dp_efd'], 3))
    ax[2].plot(t0[k0], r0['Efd'][k0], color=E.LARANJA, lw=0.7, label='medição real: σ = %s' % E.num(mr['dp_efd'], 3))
    ax[2].axhspan(P.E_LINHA - E4.CRIT['dp_efd'], P.E_LINHA + E4.CRIT['dp_efd'], color=E.FAIXA, zorder=0)
    ax[2].set_title('Regime: Efd ruidoso, σ(Efd) > 0,10 pu ✗'); ax[2].set_ylabel('Efd [pu]')
    ax[2].legend(loc='upper right', fontsize=8.2); ax[2].set_ylim(0.6, 1.95)
    for a in ax:
        a.set_xlabel('t [s]'); E.virgula(a)
    fig.tight_layout()
    E.salva(fig, 'fig-08-controle-real')


# =========================================================================== item 7: ponto de ruptura
def crit_r(cfg):
    """Degrau de Vref: Mp, ts e erro estacionario da tensao da planta (mesmas contas de e04.metricas)."""
    rr = S.simula(S.ensaio('r', T=6.0), cfg)
    v1 = cfg['vref'] + P.DVREF
    y0 = float(np.mean(E4.media_movel(rr['V_id'], 10)[(rr['t'] > 0.5) & (rr['t'] < P.T_EV)]))
    return E4.metr_degrau(rr['t'], rr['V_id'], v1, y0)


def crit_p(cfg):
    rp = S.simula(S.ensaio('p', T=11.0), cfg)
    tp = rp['t']; yp = E4.media_movel(rp['V_id'], 10)
    vpre = float(np.mean(yp[(tp > 0.5) & (tp < P.T_EV)]))
    z, s, w = E4.fit_zeta(tp, G(rp['delta']), P.T_EV + 0.25)
    return dict(afund_pct=float(100*(vpre - yp[tp > P.T_EV].min())/vpre), zeta=z)


def crit_0(cfg):
    e0 = S.ensaio('r', T=3.0); e0['dvref'] = lambda t: 0.0
    r0 = S.simula(e0, cfg)
    return dict(dp_efd=float(np.std(r0['Efd'][r0['t'] > 0.2])))


FUNC = dict(ess_pct=crit_r, Mp_pct=crit_r, ts_s=crit_r, afund_pct=crit_p, zeta=crit_p, dp_efd=crit_0)


def bissecao(ch, k, lo, hi, n=7, **extra):
    """Limiar de 'ch' para o criterio 'k' entre lo e hi (o estado do criterio muda entre os dois)."""
    def ok(v):
        cfg = E4.cfg_malha(**dict(extra, **{ch: v}))
        val = FUNC[k](cfg)[k]
        return E4.passa(k, val), val
    olo, vlo = ok(lo); ohi, vhi = ok(hi)
    if olo == ohi:
        return dict(limiar=None, nota='o criterio nao muda de estado entre %g e %g' % (lo, hi), lo=[lo, vlo], hi=[hi, vhi])
    pts = [[lo, vlo], [hi, vhi]]
    for _ in range(n):
        m = 0.5*(lo + hi)
        om, vm = ok(m)
        pts.append([m, vm])
        if om == olo:
            lo, vlo = m, vm
        else:
            hi, vhi = m, vm
    # interpolacao linear do valor do criterio entre os dois ultimos pontos
    alvo = E4.CRIT[k] if k != 'ess_pct' else -E4.CRIT[k]
    fr = (alvo - vlo)/(vhi - vlo) if vhi != vlo else 0.5
    lim = lo + min(max(fr, 0.0), 1.0)*(hi - lo)
    return dict(limiar=float(lim), sentido='deixa de atender' if olo else 'passa a atender', pontos=sorted(pts))


def previsoes():
    """Previsao do limiar de cada caracteristica, SEM simulacao nao linear (gravada antes das varreduras)."""
    pv = {}
    # erro do TP: a malha zera o erro da medicao -> a planta fica em Vref/(1+eps): |ess| = eps/(1+eps)
    lim = E4.CRIT['ess_pct']
    pv['eps_tp'] = dict(criterio='ess_pct', formula='|e_ss| = ε/(1+ε)', limiar=100*(lim/100)/(1 - lim/100))
    # AD637: modelo linear com o polo do AD637 (tau/2) e o Sallen-Key
    tau = np.concatenate([np.linspace(0.02, 0.3, 29), np.linspace(0.35, 1.0, 14)])
    prev = [E4.prev_linear(dict(malha='fechada', pss=True, fb_v='real', fb_f='real', tau_rms=v, n_cic=P.REAL['n_cic'])) for v in tau]
    curva = dict(tau=tau.tolist(), Mp=[p['Mp_pct'] for p in prev], ts=[p['ts_s'] for p in prev],
                 afund=[p['afund_pct'] for p in prev], zeta=[p['zeta'] for p in prev])
    pv['tau_rms'] = dict(criterio='Mp_pct', curva=curva,
                         limiar=cruza(tau, curva['Mp'], E4.CRIT['Mp_pct']),
                         limiar_afund=cruza(tau, curva['afund'], E4.CRIT['afund_pct']),
                         limiar_ts=cruza(tau, curva['ts'], E4.CRIT['ts_s']),
                         formula='modelo linearizado (Heffron-Phillips) + 1ª ordem τ/2 + Sallen-Key 10 Hz')
    # media de N ciclos: zeta do modo eletromecanico no modelo linear (atraso de 1 ciclo + media de 1a ordem)
    nn = np.linspace(1.0, 16.0, 61)
    zz = [K.modo_em(K.modelo(dict(malha='fechada', pss=True, fb_v='real', fb_f='real', tau_rms=P.REAL['tau_rms'], n_cic=v))[0])[2]
          for v in nn]
    pv['n_cic'] = dict(criterio='zeta', curva=dict(N=nn.tolist(), zeta=[float(z) for z in zz]),
                       limiar=cruza(nn, zz, E4.CRIT['zeta']),
                       formula='modelo linearizado com atraso de 1 ciclo (Padé) + média de 1ª ordem (N−1)/60 s na entrada do PSS')
    return pv


def cruza(x, y, alvo):
    x = np.asarray(x, float); y = np.asarray(y, float)
    for i in range(1, len(x)):
        if (y[i - 1] - alvo)*(y[i] - alvo) <= 0 and y[i] != y[i - 1]:
            return float(x[i - 1] + (alvo - y[i - 1])/(y[i] - y[i - 1])*(x[i] - x[i - 1]))
    return None


def prev_sigma(pf_bw=0.0):
    """Lei prevista para o ruido: σ(Efd)² = σ0² + (k·σ)², o ruido e' independente do residuo de quantizacao.
    k e σ0 sao calibrados com DOIS pontos (0 e 5 mV); o limiar e os outros niveis sao previsao."""
    d0 = crit_0(E4.cfg_malha(sigma=0.0, pf_bw=pf_bw))['dp_efd']
    d5 = crit_0(E4.cfg_malha(sigma=0.005, pf_bw=pf_bw))['dp_efd']
    k = math.sqrt(max(d5**2 - d0**2, 0.0))/0.005
    lim = math.sqrt(max(E4.CRIT['dp_efd']**2 - d0**2, 0.0))/k
    return dict(criterio='dp_efd', sigma0=d0, k_por_V=k, limiar=lim, formula='σ(Efd) = √(σ0² + (k·σ)²)')


def item7(P7):
    """Varredura por niveis (a mesma da E04) e bissecao do limiar."""
    d0 = crit_0(E4.cfg_malha(sigma=0.0))['dp_efd']
    d5 = crit_0(E4.cfg_malha())['dp_efd']
    niveis = E4.mapa((d0, d5))
    log('item 7: niveis')
    bis = {}
    bis['eps_tp'] = dict(ess_pct=bissecao('eps_tp', 'ess_pct', 0.3, 0.6))
    bis['tau_rms'] = dict(Mp_pct=bissecao('tau_rms', 'Mp_pct', 0.055, 0.25),
                          afund_pct=bissecao('tau_rms', 'afund_pct', 0.1, 0.25),
                          ts_s=bissecao('tau_rms', 'ts_s', 0.25, 0.5))
    log('item 7: bissecao eps, tau')
    bis['n_cic'] = dict(zeta=bissecao('n_cic', 'zeta', 4.0, 8.0), dp_efd=bissecao('n_cic', 'dp_efd', 4.0, 8.0))
    bis['sigma'] = dict(dp_efd=bissecao('sigma', 'dp_efd', 0.002, 0.005), ts_s=bissecao('sigma', 'ts_s', 0.01, 0.02))
    log('item 7: bissecao N, sigma')
    return dict(niveis=niveis, bissecao=bis)


def fig_ruptura(P7, R7, R8):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(13.2, 3.6))
    niv = R7['niveis']; bis = R7['bissecao']
    paineis = (
        ('eps_tp', 'ess_pct', lambda v: v, 'erro do TP ε [%]', '|erro estacionário| [%]', lambda y: abs(y)),
        ('tau_rms', 'Mp_pct', lambda v: 1e3*v, 'τ do AD637 [ms]', 'sobressinal M_p [%]', lambda y: y),
        ('n_cic', 'zeta', lambda v: v, 'média do frequencímetro N [ciclos]', 'ζ do modo eletromecânico', lambda y: y),
        ('sigma', 'dp_efd', lambda v: 1e3*v, 'ruído no secundário σ [mV]', 'σ(Efd) [pu]', lambda y: y),
    )
    for a, (ch, kc, fx, xl, yl, fy) in zip(ax, paineis):
        # previsao (linha tracejada)
        if ch == 'eps_tp':
            xs = np.linspace(0, 3.0, 100); a.plot(xs, 100*(xs/100)/(1 + xs/100), color=E.CINZA, ls='--', lw=1.4, label='previsão')
        elif ch == 'tau_rms':
            c = P7['tau_rms']['curva']; a.plot(1e3*np.array(c['tau']), c['Mp'], color=E.CINZA, ls='--', lw=1.4, label='previsão')
        elif ch == 'n_cic':
            c = P7['n_cic']['curva']; a.plot(c['N'], c['zeta'], color=E.CINZA, ls='--', lw=1.4, label='previsão')
        else:
            ps = P7['sigma']; xs = np.linspace(0, 0.02, 100)
            a.plot(1e3*xs, np.sqrt(ps['sigma0']**2 + (ps['k_por_V']*xs)**2), color=E.CINZA, ls='--', lw=1.4, label='previsão')
        # simulado: niveis + pontos da bissecao
        xs_ = [fx(x['valor']) for x in niv[ch]]; ys_ = [fy(E4.valor_crit(x['m'], kc)) for x in niv[ch]]
        b = bis[ch][kc]
        if b.get('pontos'):
            xb = [fx(p[0]) for p in b['pontos']]; yb = [fy(p[1]) for p in b['pontos']]
            a.plot(xb, yb, 'o', color=E.AZUL, ms=3.2, alpha=0.7)
        a.plot(xs_, ys_, 'o', color=E.AZUL, ms=6, label='simulado (não linear)')
        lim = E4.CRIT[kc]
        a.axhline(lim, color=E.CRITICO, lw=1.0)
        if b.get('limiar') is not None:
            xl_ = fx(b['limiar'])
            a.axvline(xl_, color=E.CRITICO, lw=1.0, ls=':')
            nd = 2 if ch == 'eps_tp' else (1 if ch in ('n_cic', 'sigma') else 0)
            pv = P7[ch]['limiar']
            a.annotate('simulado: %s\nprevisto: %s' % (E.num(xl_, nd), E.num(fx(pv), nd)),
                       (xl_, lim), xytext=(8, 10 if kc != 'zeta' else -34), textcoords='offset points', color=E.CRITICO,
                       fontsize=9.3, weight='bold', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))
        a.axvline(fx(P.REAL[ch]), color=E.VERDE, lw=1.0, ls='-', alpha=0.6)
        a.set_xlabel(xl); a.set_ylabel(yl)
        E.virgula(a)
    ax[0].set_xlim(0, 1.3); ax[0].set_ylim(0, 1.3)
    ax[1].set_xlim(0, 300); ax[1].set_ylim(0, 40)
    ax[2].set_xlim(0, 17); ax[2].set_ylim(0, 0.26)
    ax[3].set_xlim(0, 21); ax[3].set_ylim(0, 0.5)
    ax[0].set_title('TP → erro estacionário'); ax[1].set_title('AD637 → sobressinal')
    ax[2].set_title('média N → amortecimento'); ax[3].set_title('ruído → esforço')
    for a, ch, fx in zip(ax, ('eps_tp', 'tau_rms', 'n_cic', 'sigma'), (lambda v: v, lambda v: 1e3*v, lambda v: v, lambda v: 1e3*v)):
        a.text(fx(P.REAL[ch]), 0.97, ' nosso', transform=a.get_xaxis_transform(), color=E.VERDE, fontsize=8.5, va='top')
    ax[0].legend(loc='upper left', fontsize=8.2)
    fig.tight_layout()
    E.salva(fig, 'fig-11-ruptura')


# =========================================================================== item 8: compensacao
def item8():
    ma, ra = metr(E4.cfg_malha())
    mb, rb = metr(E4.cfg_malha(pf_bw=10.0))
    log('item 8: antes/depois')
    banco = {}
    for nome, c in (('antes', S.cfg_padrao()), ('depois', S.cfg_padrao(pf_bw=10.0))):
        r = S.simula(S.ensaio('banco_f'), c)
        r0 = S.simula(S.ensaio('banco_0'), c)
        banco[nome] = dict(t90_ms=t90(r['t'], r['f_re']), dp_f_mHz=float(1e3*np.std(r0['f_re'][r0['t'] > 0.3])))
    fa, _ = falta(E4.cfg_malha()); fb, _ = falta(E4.cfg_malha(pf_bw=10.0))
    prev_pf = prev_sigma(pf_bw=10.0)
    lim = dict(sigma_dp_efd=bissecao('sigma', 'dp_efd', 0.005, 0.02, pf_bw=10.0),
               n_zeta=bissecao('n_cic', 'zeta', 4.0, 8.0, pf_bw=10.0),
               n_dp_efd=bissecao('n_cic', 'dp_efd', 1.0, 4.0, pf_bw=10.0))
    log('item 8: limiares com o passa-faixa')
    niv_sig = []
    for v in (0.0, 0.002, 0.005, 0.01, 0.02):
        niv_sig.append(dict(valor=v, dp_efd=crit_0(E4.cfg_malha(sigma=v, pf_bw=10.0))['dp_efd']))
    return dict(antes=dict(ma, banco=banco['antes'], falta=fa), depois=dict(mb, banco=banco['depois'], falta=fb),
                previsao_sigma_pf=prev_pf, limiares_pf=lim, niveis_sigma_pf=niv_sig), ra, rb


def fig_compensacao(R8, P7, R7, ra, rb):
    import matplotlib.pyplot as plt
    from scipy.signal import welch
    fig, ax = plt.subplots(1, 3, figsize=(13.2, 3.6))
    for (rr, rp, r0), cor, rot in ((ra, E.LARANJA, 'antes: passa-baixas 150 Hz'), (rb, E.AQUA, 'depois: passa-faixa 60 ± 5 Hz')):
        t = r0['t']; i = t > 0.2
        F, X = welch(1e3*(r0['f_re'][i] - r0['f_re'][i].mean()), fs=1.0/(t[1] - t[0]), nperseg=1024)
        ax[0].semilogy(F[1:], X[1:], color=cor, lw=1.3, label=rot)
        ax[1].plot(t[i], r0['Efd'][i], color=cor, lw=0.8, label='%s: σ = %s pu' % (rot.split(':')[0], E.num(np.std(r0['Efd'][i]), 3)))
    ax[0].axvspan(0.8, 3.0, color=E.FAIXA, zorder=0)
    ax[0].text(0.9, 0.95, 'modo de\n1,32 Hz', transform=ax[0].get_xaxis_transform(), fontsize=8.5, va='top')
    ax[0].set_xlim(0, 30); ax[0].set_ylim(1e-4, 0.3)
    ax[0].set_xlabel('frequência [Hz]'); ax[0].set_ylabel('DEP de f medida [mHz²/Hz]')
    ax[0].set_title('Ruído na frequência que chega ao PSS'); ax[0].legend(loc='upper right', fontsize=8.2)
    ax[1].axhspan(P.E_LINHA - E4.CRIT['dp_efd'], P.E_LINHA + E4.CRIT['dp_efd'], color=E.FAIXA, zorder=0)
    ax[1].set_xlabel('t [s]'); ax[1].set_ylabel('Efd [pu]'); ax[1].set_ylim(0.6, 1.95)
    ax[1].set_title('Esforço em regime'); ax[1].legend(loc='upper right', fontsize=8.2)
    # limiar de ruido antes x depois
    ps = P7['sigma']; pf = R8['previsao_sigma_pf']; xs = np.linspace(0, 0.02, 100)
    for prev, niv, cor, rot in ((ps, [(x['valor'], x['m']['dp_efd']) for x in R7['niveis']['sigma']], E.LARANJA, 'antes'),
                                (pf, [(x['valor'], x['dp_efd']) for x in R8['niveis_sigma_pf']], E.AQUA, 'depois')):
        ax[2].plot(1e3*xs, np.sqrt(prev['sigma0']**2 + (prev['k_por_V']*xs)**2), color=cor, ls='--', lw=1.2)
        ax[2].plot([1e3*a for a, b in niv], [b for a, b in niv], 'o', color=cor, ms=6, label=rot)
    ax[2].axhline(E4.CRIT['dp_efd'], color=E.CRITICO, lw=1.0)
    l0 = R7['bissecao']['sigma']['dp_efd']['limiar']; l1 = R8['limiares_pf']['sigma_dp_efd']['limiar']
    for l_, cor in ((l0, E.LARANJA), (l1, E.AQUA)):
        ax[2].axvline(1e3*l_, color=cor, lw=1.0, ls=':')
    ax[2].annotate('', xy=(1e3*l1, 0.06), xytext=(1e3*l0, 0.06), arrowprops=dict(arrowstyle='->', color=E.TINTA, lw=1.2))
    ax[2].text(1e3*(l0 + l1)/2, 0.035, '%s → %s mV' % (E.num(1e3*l0, 1), E.num(1e3*l1, 1)), ha='center', fontsize=9.5, weight='bold')
    ax[2].axvline(1e3*P.REAL['sigma'], color=E.VERDE, lw=1.0, alpha=0.6)
    ax[2].set_xlim(0, 21); ax[2].set_ylim(0, 0.5)
    ax[2].set_xlabel('ruído no secundário σ [mV]'); ax[2].set_ylabel('σ(Efd) [pu]')
    ax[2].set_title('Ponto de ruptura do ruído'); ax[2].legend(loc='upper left', fontsize=8.2)
    for a in ax[1:]:
        E.virgula(a)
    ax[0].xaxis.set_major_formatter(__import__('matplotlib.ticker', fromlist=['FuncFormatter']).FuncFormatter(lambda x, p: E.num(x, 0)))
    fig.tight_layout()
    E.salva(fig, 'fig-13-compensacao')


# =========================================================================== main
def limpa(o):
    return E4.limpa(o)


def main():
    estilo_final()
    out = dict(gerado_em=datetime.now().isoformat(timespec='seconds'), CRIT=E4.CRIT, REAL=P.REAL)
    # ---- item 7, parte 1: previsoes ANTES de qualquer simulacao nao linear em malha fechada
    P7 = previsoes()
    out['item7_previsao'] = dict(P7, registrada_em=datetime.now().isoformat(timespec='seconds'))
    log('previsoes (modelo linear) gravadas')
    P7['sigma'] = prev_sigma()            # calibra a lei do ruido com 2 simulacoes (0 e 5 mV)
    out['item7_previsao']['sigma'] = P7['sigma']
    with open(SAIDA, 'w', encoding='utf-8') as fh:      # grava ja' (registro antes das varreduras)
        json.dump(limpa(out), fh, ensure_ascii=False, indent=1)
    # ---- item 3
    A3, C3 = item3(); out['item3'] = A3; fig_assinaturas(A3, C3); log('item 3')
    # ---- item 4
    R4, C4 = item4(); out['item4'] = R4; fig_isoladas(R4, C4)
    # ---- itens 5 e 6
    mi, ri = metr(E4.cfg_malha('ideal')); fi, _ = falta(E4.cfg_malha('ideal'))
    mr, rr = metr(E4.cfg_malha('real')); fr, _ = falta(E4.cfg_malha('real'))
    R2 = E4.r2()
    out['item5'] = dict(m=mi, falta=fi, projeto=dict(Kp=K.KP, Ki=K.KI, wc=K.OMEGA_C, T1=K.T1, T2=K.T2, Tw=K.TW, Kpss=K.KPSS,
                                                       margens=R2['margens'], polos=R2['polos']))
    out['item6'] = dict(m=mr, falta=fr, ess_previsto_pct=-100*P.REAL['eps_tp']/(100 + P.REAL['eps_tp']))
    fig_ideal(mi, ri); fig_real(mi, ri, mr, rr); log('itens 5 e 6')
    # ---- item 7
    R7 = item7(P7); out['item7'] = R7
    # ---- item 8
    R8, ra, rb = item8(); out['item8'] = R8
    fig_ruptura(P7, R7, R8); fig_compensacao(R8, P7, R7, ra, rb)
    with open(SAIDA, 'w', encoding='utf-8') as fh:
        json.dump(limpa(out), fh, ensure_ascii=False, indent=1)
    log('fim')
    resumo = dict(previsto={k: P7[k]['limiar'] for k in ('eps_tp', 'tau_rms', 'n_cic', 'sigma')},
                  simulado={ch: {k: v.get('limiar') for k, v in d.items()} for ch, d in R7['bissecao'].items()},
                  pf={k: v.get('limiar') for k, v in R8['limiares_pf'].items()},
                  item4_a={n: (round(1e3*v['V']['err_rms'], 3), round(1e3*v['f']['err_rms'], 2)) for n, v in R4['a'].items() if isinstance(v, dict) and 'V' in v})
    print(json.dumps(limpa(resumo), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
