# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 03: instrumentacao em malha aberta, medicao ideal x medicao real.

R1 demanda de instrumentacao (numeros tirados do modelo da E01/E02)
R2 sensor ideal e real (estrutura funcional, caracteristicas, ensaios de bancada)
R3 circuitos auxiliares e processamento (projeto do conversor de valor eficaz e do frequencimetro)
R4 ensaios da E01 (degrau, condicao inicial, falta) com grandeza real x medicao ideal x medicao real,
   tabela de erros/atraso/tempo de resposta e contribuicao de cada caracteristica (liga/desliga)
R5 exacerbacao de quatro caracteristicas, com previsao antes de simular

Saidas: ../relatorio/figuras/fig-0[1-7]-*.png, resultados_e03.json, dados/e03_*.csv
Uso:    python e03.py        (numpy, scipy, matplotlib; ~1 min)
"""
import json
import math
import os

import numpy as np

import parametros_e34 as P
import sistema as S
import estilo as E

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, 'dados')
G = np.degrees
CHAVES = ('eps_tp', 'tau_rms', 'nbits', 'sigma', 'n_cic', 'fclk')


# ============================================================== utilitarios de metrica
def limpa_f(t, f):
    """f ideal tem um impulso na amostra em que a fase terminal salta (inicio/fim da falta): interpola."""
    f = f.copy()
    ruim = np.abs(f - np.median(f)) > 5.0
    if ruim.any():
        f[ruim] = np.interp(t[ruim], t[~ruim], f[~ruim])
    return f, ruim


def atraso(t, ideal, real, tmax=0.4):
    """Atraso que minimiza o erro RMS entre real(t) e ideal(t - a), com o desvio medio removido."""
    dt = t[1] - t[0]
    best = None
    for k in range(0, int(tmax/dt)):
        a = real[k:] - ideal[:len(ideal) - k]
        v = np.sqrt(np.mean((a - a.mean())**2))
        if best is None or v < best[1]:
            best = (k, v)
    k = best[0]
    if 0 < k < int(tmax/dt) - 1:                       # refinamento parabolico
        vs = []
        for kk in (k - 1, k, k + 1):
            a = real[kk:] - ideal[:len(ideal) - kk]
            vs.append(np.sqrt(np.mean((a - a.mean())**2)))
        den = vs[0] - 2*vs[1] + vs[2]
        frac = 0.5*(vs[0] - vs[2])/den if den != 0 else 0.0
        return (k + frac)*dt
    return k*dt


def metricas(r):
    t = r['t']
    fid, ruim = limpa_f(t, r['f_id'])
    eV = r['V_re'] - r['V_id']
    eF = (r['f_re'] - fid)[~(ruim & (np.abs(r['f_re'] - 60) > 5))]   # sem a amostra do impulso de fase
    exc_f = fid.max() - fid.min()
    exc_v = r['V_id'].max() - r['V_id'].min()
    m = dict(
        V=dict(err_max=float(np.max(np.abs(eV))), err_rms=float(np.sqrt(np.mean(eV**2))),
               err_medio=float(eV.mean()), err_rel_pct=float(100*np.max(np.abs(eV))/P.VT0),
               err_rel_exc_pct=float(100*np.max(np.abs(eV - eV.mean()))/exc_v),
               atraso_ms=1e3*atraso(t, r['V_id'], r['V_re'])),
        f=dict(err_max=float(np.max(np.abs(eF))), err_rms=float(np.sqrt(np.mean(eF**2))),
               err_medio=float(eF.mean()), err_rel_exc_pct=float(100*np.max(np.abs(eF))/exc_f),
               atraso_ms=1e3*atraso(t, fid, r['f_re'])))
    return m


def caracteristicos(nome, r):
    """Valores caracteristicos de cada ensaio, ideal x real."""
    t = r['t']
    fid, _ = limpa_f(t, r['f_id'])
    Vi, Vr, fr = r['V_id'], r['V_re'], r['f_re']
    out = {}

    def ext(x, i, fn):
        j = np.argmin(x[i]) if fn == 'min' else np.argmax(x[i])
        return float(x[i][j]), float(t[i][j])
    if nome == 'a':
        i = (t > P.T_EV) & (t < P.T_EV + 0.9)
        out['V_min_1o_afundamento'] = dict(ideal=ext(Vi, i, 'min'), real=ext(Vr, i, 'min'))
        out['f_max_1o_pico'] = dict(ideal=ext(fid, i, 'max'), real=ext(fr, i, 'max'))
        out['V_final'] = dict(ideal=float(Vi[-1]), real=float(np.mean(Vr[-500:])))
    elif nome == 'b':
        i = t < 1.0
        out['V_max'] = dict(ideal=ext(Vi, i, 'max'), real=ext(Vr, i, 'max'))
        out['f_min'] = dict(ideal=ext(fid, i, 'min'), real=ext(fr, i, 'min'))
        out['f_max'] = dict(ideal=ext(fid, i, 'max'), real=ext(fr, i, 'max'))
    else:
        i = (t > P.T_EV) & (t < P.T_EV + P.DUR_FALTA)
        out['V_na_falta'] = dict(ideal=ext(Vi, i, 'min'), real=ext(Vr, i, 'min'))
        j = (t > P.T_EV + P.DUR_FALTA) & (t < P.T_EV + 1.0)
        out['f_max_pos_falta'] = dict(ideal=ext(fid, j, 'max'), real=ext(fr, j, 'max'))
        # tempo de resposta (0 -> 90 %) ao afundamento: o ideal e' instantaneo
        v0 = float(np.mean(Vr[t < P.T_EV]))
        vf = float(Vi[i][-1])*(1 + P.REAL['eps_tp']/100)
        k = np.where((t >= P.T_EV) & (Vr <= v0 - 0.9*(v0 - vf)))[0]
        out['t_resp_90_afundamento_ms'] = dict(ideal=0.0, real=float(1e3*(t[k[0]] - P.T_EV)) if len(k) else None)
    return out


def ens_real(nome, **kw):
    return S.simula(S.ensaio(nome), S.cfg_padrao(**kw))


# ============================================================== R1
def r1(res):
    a, b, c = res['a'], res['b'], res['c']
    Vmin = min(x['V_id'].min() for x in (a, b, c)); Vmax = max(x['V_id'].max() for x in (a, b, c))
    fl = [limpa_f(x['t'], x['f_id'])[0] for x in (a, b, c)]
    fmin = min(x.min() for x in fl); fmax = max(x.max() for x in fl)
    dv_a = float(P.VT0 - a['V_id'].min())
    df_a = float(np.max(np.abs(fl[0] - 60.0)))
    # pior caso fisico: separatriz da E01 (|Δω| <= 11,69 rad/s), com fator dθt/dδ <= 1 (falta)
    om_sep = 11.685986077779496
    return dict(
        faixa_V_pu=[float(Vmin), float(Vmax)], faixa_f_Hz=[float(fmin), float(fmax)],
        faixa_instrumento=dict(V_pu=[0.0, 1.5], f_Hz=[55.0, 65.0]),
        separatriz_df_Hz=om_sep/(2*math.pi),
        banda=dict(f_modo_Hz=1.3230, f_ripple_Hz=120.0,
                   atraso_max_V_ms=50.0, atraso_max_f_ms=70.0,
                   justificativa='fase <= 25 graus (V) e <= 33 graus (f) em 1,32 Hz; o PSS da E04 atua no modo'),
        menor_variacao=dict(dV_degrau_pu=dv_a, df_degrau_Hz=df_a),
        resolucao=dict(V_pu=0.0005, f_Hz=0.003),
        incerteza=dict(V_pct=0.5, f_mHz=10.0),
        Vt0_pu=P.VT0, Vt0_kV=P.VT0*P.V_BASE/1e3, theta0_graus=G(P.TH0), dth_ddelta=P.DTH_DDELTA,
        K5=P.K5, K6=P.K6)


# ============================================================== R2 (bancada)
def bancada():
    out = {}
    rv = S.simula(S.ensaio('banco_v'), S.cfg_padrao())
    rf = S.simula(S.ensaio('banco_f'), S.cfg_padrao())
    r0 = S.simula(S.ensaio('banco_0'), S.cfg_padrao())
    for nome, r, k, deg in (('tensao', rv, 'V_re', 0.1), ('frequencia', rf, 'f_re', 0.1)):
        t, x = r['t'], r[k]
        x0, x1 = x[t < 0.5].mean(), x[t > 1.2].mean()
        j90 = np.where((t >= 0.5) & (np.abs(x - x0) >= 0.9*abs(x1 - x0)))[0][0]
        j10 = np.where((t >= 0.5) & (np.abs(x - x0) >= 0.1*abs(x1 - x0)))[0][0]
        out[nome] = dict(degrau=deg, t90_ms=float(1e3*(t[j90] - 0.5)), t10_90_ms=float(1e3*(t[j90] - t[j10])),
                         ganho=float((x1 - x0)/deg), sobressinal_pct=float(100*max(0.0, (np.max(np.abs(x[t > 0.5] - x0)) - abs(x1 - x0))/abs(x1 - x0))))
    i = r0['t'] > 0.3
    out['piso'] = dict(V_dp_pu=float(np.std(r0['V_re'][i])), f_dp_mHz=float(1e3*np.std(r0['f_re'][i])),
                       V_media_pu=float(np.mean(r0['V_re'][i])), f_media=float(np.mean(r0['f_re'][i])),
                       lsb_pu=P.VREF_ADC/2**P.REAL['nbits']/P.V_PU_VD,
                       resol_f_ciclo_mHz=1e3*P.F_REDE**2/P.REAL['fclk'])
    # ondulacao residual de 120 Hz sem ruido e sem ADC
    rr = S.simula(S.ensaio('banco_0'), S.cfg_padrao(sigma=0.0, nbits=0, decim=1))
    i = rr['t'] > 1.0
    out['ripple_pp_pct'] = float(100*(rr['V_re'][i].max() - rr['V_re'][i].min())/rr['V_re'][i].mean())
    return out, (rv, rf)


# ============================================================== R3 (projeto do conversor)
def projeto_rms():
    """Ondulacao de 120 Hz (pico a pico, % da leitura) e atraso equivalente em 1,32 Hz contra CAV."""
    cav = np.logspace(math.log10(0.1), math.log10(47), 80)
    w2 = 2*math.pi*120.0; wm = 2*math.pi*1.3230
    wsk = 2*math.pi*P.FC_SK
    def sk(w):
        s = 1j*w
        return wsk**2/(s*s + wsk/P.Q_SK*s + wsk**2)
    linhas = {}
    for nome, com_sk in (('AD637 só', False), ('AD637 + Sallen-Key 10 Hz', True)):
        tau = P.TAU_POR_UF*cav
        # implicito: ondulacao de pico = 1/(w2*tau) da leitura (datasheet: 50/(6,3*tau*f) %); pico a pico = 2x
        h1 = 1/np.abs(w2*tau + 2j)
        hs = abs(sk(w2)) if com_sk else 1.0
        rip = 200*h1*hs
        fase = np.arctan(wm*tau/2) + (-np.angle(sk(wm)) if com_sk else 0.0)
        linhas[nome] = dict(cav=cav.tolist(), ripple_pp_pct=rip.tolist(), atraso_ms=(1e3*fase/wm).tolist())
    return linhas


# ============================================================== R4 (contribuicoes)
def contribuicoes():
    """Liga/desliga: erro RMS com a cadeia real completa e com cada caracteristica desligada (as demais
    ligadas). A contribuicao de X e' o quanto o erro cai quando so' X e' desligada."""
    out = {}
    for nome in 'abc':
        out[nome] = {}
        base = metricas(ens_real(nome))
        out[nome]['todas'] = dict(V=base['V']['err_rms'], f=base['f']['err_rms'])
        for ch in CHAVES:
            m = metricas(ens_real(nome, **{ch: P.NEUTRO[ch]}))
            out[nome]['sem_' + ch] = dict(V=m['V']['err_rms'], f=m['f']['err_rms'])
        m = metricas(ens_real(nome, **dict(P.NEUTRO)))
        out[nome]['nenhuma'] = dict(V=m['V']['err_rms'], f=m['f']['err_rms'])
    return out


# ============================================================== R5 (exacerbacao)
NIVEIS = dict(
    tau_rms=(0.055, 0.25, 1.0, 4.0),         # s   (CAV = 2,2, 10, 40, 160 uF)
    sigma=(0.005, 0.05, 0.2, 1.0),           # V
    n_cic=(1.0, 4.0, 16.0, 64.0),            # ciclos
    fclk=(1e6, 1e5, 1e4, 2e3),               # Hz
)
ENSAIO_EXAC = dict(tau_rms='c', sigma='a', n_cic='b', fclk='a')


def previsao(ch, v):
    """Previsao algebrica feita antes de simular."""
    V2 = P.V_PU_VD*P.VT0*(1 + P.REAL['eps_tp']/100)       # V eficazes na entrada do AD637
    wm = 2*math.pi*1.3230
    if ch == 'tau_rms':        # AD637 implicito: d(Vo²)/dt = 2(Vin² - Vo²)/τ -> Vo² = Vf² + (V0² - Vf²) e^(-2t/τ),
        #                        com o Sallen-Key atrasando ~ √2/ωsk = 22,5 ms
        r = P.terminal(P.DELTA0, P.E_LINHA, 1.0)
        rr = math.hypot(*r)/P.VT0
        tsk = math.sqrt(2)/(2*math.pi*P.FC_SK)
        u = rr**2 + (1 - rr**2)*math.exp(-2*(P.DUR_FALTA - tsk)/v)       # implicito: V² relaxa com tau/2
        return dict(fracao_afundamento=(1 - math.sqrt(u))/(1 - rr), ripple_pp_pct=200*abs(1/(2*math.pi*120*v + 2j))*
                    abs((2*math.pi*P.FC_SK)**2/((1j*2*math.pi*120)**2 + 2*math.pi*P.FC_SK/P.Q_SK*1j*2*math.pi*120 + (2*math.pi*P.FC_SK)**2)))
    if ch == 'sigma':          # vies do valor eficaz verdadeiro: sqrt(V² + σ²) ; jitter de f ∝ σ
        return dict(vies_V_pct=100*(math.sqrt(V2**2 + v**2)/V2 - 1), escala_ruido_f=v/0.005)
    if ch == 'n_cic':          # media exponencial ~ 1a ordem com tau = (N-1)/60 + 1 ciclo de atraso
        tau = (v - 1)/P.F_REDE
        return dict(ganho_1_32Hz=1/math.sqrt(1 + (wm*tau)**2),
                    atraso_ms=1e3*(math.atan(wm*tau)/wm + 1/P.F_REDE), ruido_rel=math.sqrt(1/(2*v - 1)) if v >= 1 else 1)
    if ch == 'fclk':           # resolucao por ciclo: Δf = f²/fclk; captura com ±1 tique -> dp = f²·0,41/fclk por ciclo
        return dict(resol_ciclo_mHz=1e3*P.F_REDE**2/v, dp_ciclo_mHz=1e3*P.F_REDE**2*math.sqrt(2/12)/v)
    return {}


def exacerba():
    out = {}
    curvas = {}
    for ch, niveis in NIVEIS.items():
        ens = ENSAIO_EXAC[ch]
        out[ch] = []
        curvas[ch] = []
        for v in niveis:
            r = ens_real(ens, **{ch: v})
            m = metricas(r)
            c = caracteristicos(ens, r)
            out[ch].append(dict(valor=v, previsao=previsao(ch, v), V=m['V'], f=m['f'], caract=c))
            curvas[ch].append(r)
    # resultados medidos especificos de cada caracteristica
    for k, r in enumerate(curvas['tau_rms']):
        t = r['t']; i = (t > P.T_EV) & (t < P.T_EV + P.DUR_FALTA)
        v0 = np.mean(r['V_re'][t < P.T_EV]); vf = r['V_id'][i][-1]*(1 + P.REAL['eps_tp']/100)
        out['tau_rms'][k]['medido'] = dict(fracao_afundamento=float((v0 - r['V_re'][i].min())/(v0 - vf)))
    ref = ens_real(ENSAIO_EXAC['sigma'], sigma=0.0)              # referencia sem ruido (mesmo ADC)
    i0 = ref['t'] < P.T_EV
    for k, r in enumerate(curvas['sigma']):
        t = r['t']; i = t < P.T_EV
        # mesma trajetoria da planta nas duas corridas: o vies e' a diferenca media ao longo dos 21 s
        out['sigma'][k]['medido'] = dict(vies_V_pct=float(100*np.mean(r['V_re'] - ref['V_re'])/np.mean(ref['V_re'])),
                                         dp_f_mHz=float(1e3*np.std(r['f_re'][i & (t > 0.2)])))
    for k, r in enumerate(curvas['n_cic']):
        t = r['t']; fid, _ = limpa_f(t, r['f_id'])
        i = (t > 1.0) & (t < 6.0)
        A_id = (np.percentile(fid[i], 99) - np.percentile(fid[i], 1))
        A_re = (np.percentile(r['f_re'][i], 99) - np.percentile(r['f_re'][i], 1))
        out['n_cic'][k]['medido'] = dict(ganho_1_32Hz=float(A_re/A_id), atraso_ms=float(1e3*atraso(t, fid, r['f_re'])))
    for k, r in enumerate(curvas['fclk']):
        t = r['t']; i = t < P.T_EV
        out['fclk'][k]['medido'] = dict(dp_f_mHz=float(1e3*np.std(r['f_re'][i & (t > 0.2)])),
                                        erro_rms_mHz=float(1e3*out['fclk'][k]['f']['err_rms']))
    return out, curvas


# ============================================================== figuras
def fig_demanda(R1, res):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0), gridspec_kw=dict(width_ratios=[1.15, 1, 1]))
    d = np.radians(np.linspace(-30, 180, 600))
    vn = [math.hypot(*P.terminal(x, P.E_LINHA, 0.0)) for x in d]
    vf = [math.hypot(*P.terminal(x, P.E_LINHA, 1.0)) for x in d]
    ax[0].plot(G(d), vn, color=E.AZUL, label='rede normal: (X′d·V + Xe·E′∠δ)/X')
    ax[0].plot(G(d), vf, color=E.CRITICO, label='durante a falta: XT/(X′d+XT)·E′')
    for dg, rot, off in ((G(P.DELTA0), 'δ0', (-14, -11)), (26.74, '(a)', (2, 5)), (60.0, '(b)', (3, 4)), (80.7, '(c) máx.', (3, 4))):
        ax[0].plot(dg, math.hypot(*P.terminal(math.radians(dg), P.E_LINHA, 0.0)), 'o', ms=3.5, color=E.TINTA)
        ax[0].annotate(rot, (dg, math.hypot(*P.terminal(math.radians(dg), P.E_LINHA, 0.0))), xytext=off,
                       textcoords='offset points', fontsize=6.5)
    ax[0].set_xlabel('δ [°]'); ax[0].set_ylabel('|Vt| [pu]')
    ax[0].set_title('Tensão terminal em função do ângulo')
    ax[0].legend(fontsize=6, loc='lower left'); ax[0].set_ylim(0, 1.2)
    # fator dθt/dδ
    fat = []
    d = np.radians(np.linspace(-30, 150, 500))        # perto de 180 graus |Vt| -> 0,1 pu e a fase dispara
    for x in d:
        re1, im1 = P.terminal(x - 1e-6, P.E_LINHA); re2, im2 = P.terminal(x + 1e-6, P.E_LINHA)
        fat.append((math.atan2(im2, re2) - math.atan2(im1, re1))/2e-6)
    ax[1].plot(G(d), fat, color=E.AZUL)
    ax[1].axhline(1.0, color=E.CRITICO, lw=0.9, ls='--')
    ax[1].text(148, 1.04, 'durante a falta = 1', ha='right', fontsize=6.5, color=E.CRITICO)
    ax[1].plot(G(P.DELTA0), P.DTH_DDELTA, 'o', ms=3.5, color=E.TINTA)
    ax[1].annotate('%s em δ0' % E.num(P.DTH_DDELTA, 3), (G(P.DELTA0), P.DTH_DDELTA), xytext=(4, -10),
                   textcoords='offset points', fontsize=6.5)
    ax[1].set_xlabel('δ [°]'); ax[1].set_ylabel('dθt/dδ')
    ax[1].set_title('f terminal = 60 + (dθt/dδ)·Δω/2π')
    ax[1].set_ylim(0, 2.6)
    # espectro da grandeza nos ensaios: amplitude da oscilacao em 1,32 Hz
    for nome, cor in (('a', E.AZUL), ('b', E.LARANJA)):
        r = res[nome]
        t = r['t']; i = t > (1.2 if nome == 'a' else 0.0)
        x = r['V_id'][i] - r['V_id'][i].mean()
        F = np.fft.rfftfreq(len(x), t[1] - t[0]); X = 2*np.abs(np.fft.rfft(x*np.hanning(len(x))))/np.sum(np.hanning(len(x)))
        ax[2].semilogy(F, X, color=cor, lw=0.9, label='|Vt|, ensaio (%s)' % nome)
    ax[2].axvline(1.323, color=E.CINZA, lw=0.8, ls=':'); ax[2].text(1.4, 2e-2, '1,32 Hz', fontsize=6.5, color=E.TINTA2)
    ax[2].set_xlim(0, 6); ax[2].set_ylim(1e-6, 1e-1)
    ax[2].set_xlabel('frequência [Hz]'); ax[2].set_ylabel('amplitude [pu]')
    ax[2].set_title('Conteúdo espectral da grandeza'); ax[2].legend(fontsize=6)
    for a_ in ax:
        E.virgula(a_)
    ax[2].yaxis.set_major_formatter(matplotlib_log())
    fig.tight_layout()
    E.salva(fig, 'fig-01-demanda')


def matplotlib_log():
    from matplotlib.ticker import LogFormatterSciNotation
    return LogFormatterSciNotation()


def fig_cadeia():
    """Diagrama da cadeia: caminho ideal e caminho real, com o bloco nativo do TyphoonSim de cada etapa."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(11.5, 4.6))
    ax.set_xlim(0, 115); ax.set_ylim(0, 47); ax.axis('off')

    def caixa(x, y, w, h, titulo, sub='', blocos='', cor=E.AZUL, tag=None):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.25,rounding_size=0.8', fc='white',
                                    ec=cor, lw=1.1))
        ax.text(x + w/2, y + h - 1.6, titulo, ha='center', va='top', fontsize=7.2 if len(titulo) < 30 else 6.6, weight='bold', color=E.TINTA)
        if sub:
            ax.text(x + w/2, y + h - 4.3, sub, ha='center', va='top', fontsize=6.3, color=E.TINTA2)
        if blocos:
            ax.text(x + w/2, y + 0.9, blocos, ha='center', va='bottom', fontsize=5.6, color=E.CINZA, style='italic')
        if tag:
            ax.text(x + w - 0.3, y + h + 0.4, tag, ha='right', va='bottom', fontsize=5.8, color='white',
                    bbox=dict(boxstyle='round,pad=0.2', fc=E.LARANJA, ec='none'))

    def seta(x1, y1, x2, y2, cor=E.TINTA2):
        ax.annotate('', (x2, y2), (x1, y1), arrowprops=dict(arrowstyle='-|>', color=cor, lw=0.9, shrinkA=0, shrinkB=0))
    # planta
    caixa(0.5, 15, 13, 13, 'Planta (E02)', 'RLC + fonte do\nresíduo; δ, Δω, E′', 'circuito nativo', cor=E.TINTA2)
    caixa(16, 15, 14, 13, 'Tensão terminal', 'Vt = (X′d·V + Xe·E′∠δ)/X\nfalta: XT/(X′d+XT)·E′', 'Trig., Product, Sum', cor=E.TINTA2)
    caixa(33, 15, 13, 13, 'Primário do TP', 'v_p = √2·13,8 kV·|Vt|\n·cos(ωs t + θt)', 'Clock, Trig., Gain', cor=E.TINTA2)
    seta(13.8, 21.5, 15.7, 21.5); seta(30.3, 21.5, 32.7, 21.5)
    # ideal
    caixa(52, 33, 30, 8.5, 'Medição IDEAL: ganho 1, sem atraso, sem ruído',
          'V = |Vt|      f = 60 + Δθt/(2π·Ts)', 'Gain, Sum, Round (desdobra fase)', cor=E.AQUA)
    seta(23, 28.3, 23, 37); seta(23, 37, 51.7, 37, cor=E.AQUA)
    # real: TP e condicionamento
    caixa(48.5, 15, 12, 13, 'TP', '13,8 kV : 115 V\nclasse 0,3 · (1 + ε)', 'Gain (ε do SCADA)', tag='ε_TP')
    caixa(62.5, 15, 10, 13, 'Divisor', '115 V → 2 V\n(1 pu = 2 V)', 'Gain')
    caixa(75, 15, 8, 13, '+ ruído', 'σ branco\n5 kHz', 'Random Source', tag='σ')
    seta(46.3, 21.5, 48.7, 21.5); seta(60.3, 21.5, 62.2, 21.5); seta(72.8, 21.5, 74.7, 21.5)
    # ramo tensao
    caixa(87, 27.5, 13, 9.5, 'AD637', 'Vo = média(x²/Vo)\nτ = 25 ms/µF·C_AV', 'Product, Sum, Unit Delay', tag='τ_RMS')
    caixa(101.5, 27.5, 13, 9.5, 'Sallen-Key + ADC', '10 Hz · 12 bits\n0–4,096 V → pu', 'Unit Delay, Round', tag='n bits')
    # ramo frequencia
    caixa(87, 3, 13, 11, 'Comparador', 'pré-filtro 150 Hz\nhisterese ±20 mV', 'Unit Delay, Hysteresis', cor=E.VIOLETA)
    caixa(101.5, 3, 13, 11, 'Período → f', 'interpola cruzamento\nrelógio fclk · média N', 'Sum, Round, Signal switch',
          cor=E.VIOLETA, tag='fclk · N')
    seta(83.3, 21.5, 85, 21.5); seta(85, 21.5, 85, 32); seta(85, 32, 86.7, 32); seta(85, 21.5, 85, 8.5); seta(85, 8.5, 86.7, 8.5, cor=E.VIOLETA)
    seta(100.3, 32, 101.2, 32); seta(100.3, 8.5, 101.2, 8.5, cor=E.VIOLETA)
    ax.text(108, 26.6, 'V_med [pu]', ha='center', va='top', fontsize=6.6, color=E.AZUL, weight='bold')
    ax.text(108, 2.3, 'f_med [Hz]', ha='center', va='top', fontsize=6.6, color=E.VIOLETA, weight='bold')
    ax.text(0.5, 46.5, 'Caminho ideal (verde) e caminho real (azul: tensão; violeta: frequência) no mesmo modelo. '
            'Etiqueta laranja = característica ajustável no SCADA (0 desliga).', fontsize=6.6, color=E.TINTA2, va='top')
    ax.text(0.5, 1.0, 'Taxas: planta 20 µs (E02); medição e controle 100 µs (ADC a 10 kS/s, 166,7 amostras/ciclo).',
            fontsize=6.3, color=E.CINZA)
    E.salva(fig, 'fig-02-cadeia')


def fig_bancada(B, rv, rf):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 2.9))
    t = rv['t']
    ax[0].plot(t, 1.0 + 0.1*(t >= 0.5), color=E.CINZA, lw=2.2, alpha=0.6, label='entrada (ideal)')
    ax[0].plot(t, rv['V_re']/(1 + P.REAL['eps_tp']/100), color=E.AZUL, lw=1.0, label='medição real ÷ (1+ε_TP)')
    ax[0].set_xlim(0.4, 0.8); ax[0].set_xlabel('t [s]'); ax[0].set_ylabel('V [pu]')
    ax[0].set_title('Degrau de amplitude 1,0 → 1,1 pu: t₉₀ = %s ms' % E.num(B['tensao']['t90_ms'], 0))
    ax[0].legend(fontsize=6, loc='lower right')
    t = rf['t']
    ax[1].plot(t, 60 + 0.1*(t >= 0.5), color=E.CINZA, lw=2.2, alpha=0.6, label='entrada (ideal)')
    ax[1].plot(t, rf['f_re'], color=E.VIOLETA, lw=1.0, label='medição real')
    ax[1].set_xlim(0.4, 0.9); ax[1].set_xlabel('t [s]'); ax[1].set_ylabel('f [Hz]')
    ax[1].set_title('Degrau de frequência 60,0 → 60,1 Hz: t₉₀ = %s ms' % E.num(B['frequencia']['t90_ms'], 0))
    ax[1].legend(fontsize=6, loc='lower right')
    r0 = S.simula(S.ensaio('banco_0'), S.cfg_padrao())
    i = r0['t'] > 0.3
    ax[2].plot(r0['t'][i], 1e3*(r0['f_re'][i] - 60), color=E.VIOLETA, lw=0.7, label='f − 60 [mHz]')
    ax[2].plot(r0['t'][i], 1e4*(r0['V_re'][i] - r0['V_re'][i].mean()), color=E.AZUL, lw=0.5, alpha=0.55, label='(V − média)×10⁴ [pu] (±1 LSB = ±5)')
    ax[2].set_xlabel('t [s]'); ax[2].set_title('Piso: σ_V = %s pu · σ_f = %s mHz' % (
        E.cient(B['piso']['V_dp_pu'], 1), E.num(B['piso']['f_dp_mHz'], 2)))
    ax[2].legend(fontsize=6, loc='upper right'); ax[2].set_ylim(-6, 8)
    for a_ in ax:
        E.virgula(a_)
    fig.tight_layout()
    E.salva(fig, 'fig-04-bancada')


def fig_projeto_rms(L):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 2.9))
    for (nome, d), cor in zip(L.items(), (E.LARANJA, E.AZUL)):
        ax[0].loglog(d['cav'], d['ripple_pp_pct'], color=cor, label=nome)
        ax[1].semilogx(d['cav'], d['atraso_ms'], color=cor, label=nome)
    ax[0].axhline(0.05, color=E.CRITICO, ls='--', lw=0.8); ax[0].text(0.12, 0.06, 'resolução exigida 0,05 %', fontsize=6.5, color=E.CRITICO)
    ax[1].axhline(50, color=E.CRITICO, ls='--', lw=0.8); ax[1].text(0.12, 55, 'atraso máximo 50 ms', fontsize=6.5, color=E.CRITICO)
    for a_ in ax:
        a_.axvline(P.CAV_UF, color=E.TINTA2, lw=0.8, ls=':')
        a_.set_xlabel('C_AV [µF]  (τ = 25 ms/µF)')
    ax[0].set_ylabel('ondulação de 120 Hz [% pico a pico]'); ax[1].set_ylabel('atraso em 1,32 Hz [ms]')
    ax[0].set_title('Ondulação: só o AD637 exigiria C_AV > 100 µF'); ax[1].set_title('Atraso: com o Sallen-Key, 2,2 µF basta')
    ax[0].legend(fontsize=6.5); ax[1].set_ylim(0, 400)
    ax[0].text(P.CAV_UF*1.1, 3e-4, 'adotado\n2,2 µF', fontsize=6.5, color=E.TINTA2)
    E.virgula(ax[1])
    fig.tight_layout()
    E.salva(fig, 'fig-03-projeto-rms')


def fig_ensaios(res, M):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(11.0, 5.0))
    janelas = dict(a=(0.6, 5.0), b=(0.0, 4.0), c=(0.9, 2.6))
    tit = dict(a='(a) degrau de Pm 0,8 → 0,9 pu', b='(b) δ(0) = 60°', c='(c) falta franca de 200 ms')
    for j, nome in enumerate('abc'):
        r = res[nome]; t = r['t']
        fid, ruim = limpa_f(t, r['f_id'])
        ax[0, j].plot(t, r['V_id'], color=E.CINZA, lw=3.0, alpha=0.55, label='grandeza real (|Vt|)')
        ax[0, j].plot(t, r['V_id'], '--', color=E.TINTA, lw=0.8, label='medição ideal')
        ax[0, j].plot(t, r['V_re'], color=E.AZUL, lw=0.9, label='medição real')
        ax[1, j].plot(t, fid, color=E.CINZA, lw=3.0, alpha=0.55, label='grandeza real (f terminal)')
        ax[1, j].plot(t, fid, '--', color=E.TINTA, lw=0.8, label='medição ideal')
        ax[1, j].plot(t, r['f_re'], color=E.VIOLETA, lw=0.9, label='medição real')
        for tt in t[ruim]:
            ax[1, j].axvline(tt, color=E.CRITICO, lw=0.6, ls=':')
        ax[0, j].set_xlim(*janelas[nome]); ax[1, j].set_xlim(*janelas[nome])
        ax[0, j].set_title(tit[nome]); ax[1, j].set_xlabel('t [s]')
        m = M[nome]
        ax[0, j].text(0.98, 0.03, 'erro RMS %s pu · atraso %s ms' % (E.cient(m['V']['err_rms'], 1), E.num(m['V']['atraso_ms'], 0)),
                      transform=ax[0, j].transAxes, ha='right', fontsize=6.3, color=E.AZUL,
                      bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=E.GRADE, lw=0.5))
        ax[1, j].text(0.98, 0.03, 'erro RMS %s mHz · atraso %s ms' % (E.num(1e3*m['f']['err_rms'], 1), E.num(m['f']['atraso_ms'], 0)),
                      transform=ax[1, j].transAxes, ha='right', fontsize=6.3, color=E.VIOLETA,
                      bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=E.GRADE, lw=0.5))
        if nome == 'c':
            ax[0, j].axvspan(P.T_EV, P.T_EV + P.DUR_FALTA, color=E.FAIXA, zorder=0)
            ax[1, j].axvspan(P.T_EV, P.T_EV + P.DUR_FALTA, color=E.FAIXA, zorder=0)
            ax[1, j].text(P.T_EV + 0.01, 0.97, 'salto de fase', transform=ax[1, j].get_xaxis_transform(), fontsize=6, color=E.CRITICO, va='top')
    ax[0, 0].set_ylabel('V [pu]'); ax[1, 0].set_ylabel('f [Hz]')
    ax[0, 0].legend(fontsize=6, loc='upper right'); ax[1, 0].legend(fontsize=6, loc='upper right')
    for a_ in ax.flat:
        E.virgula(a_)
    E.rotulo_solver(ax[0, 1], x=0.98, y=0.97, va='top', texto='planta 20 µs · medição 100 µs · E′ = 1,2 pu (malha aberta)')
    fig.tight_layout()
    E.salva(fig, 'fig-05-ensaios')


def fig_contribuicoes(Cn):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 2.9))
    nomes = list(CHAVES)
    cores = [E.AZUL, E.LARANJA, E.AQUA]
    larg = 0.26
    for j, (g, esc, un) in enumerate((('V', 1e3, 'erro RMS de V [10⁻³ pu]'), ('f', 1e3, 'erro RMS de f [mHz]'))):
        for k, ens in enumerate('abc'):
            tot = Cn[ens]['todas'][g]
            contrib = [max(0.0, tot - Cn[ens]['sem_' + ch][g])*esc for ch in nomes]
            x = np.arange(len(nomes)) + (k - 1)*larg
            ax[j].bar(x, contrib, larg, color=cores[k], label='ensaio (%s): total %s' % (ens, E.num(tot*esc, 2)))
        ax[j].set_yscale('log'); ax[j].set_ylim(1e-3, 300)
        ax[j].set_xticks(np.arange(len(nomes)))
        ax[j].set_xticklabels([P.ROTULO[c].replace(' do ', '\ndo ').replace(' no ', '\nno ') for c in nomes], fontsize=6.3)
        ax[j].set_ylabel(un); ax[j].legend(fontsize=6, loc='upper right')
        ax[j].set_title('Quanto o erro de %s cai ao desligar cada característica' % ('tensão' if g == 'V' else 'frequência'))
        ax[j].grid(axis='x', visible=False)
    fig.tight_layout()
    E.salva(fig, 'fig-06-contribuicoes')


def fig_exacerbacao(X, curvas):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(10.5, 5.2))
    cores = E.rampa(4)
    # tau_rms na falta (V)
    a_ = ax[0, 0]
    r0 = curvas['tau_rms'][0]
    a_.plot(r0['t'], r0['V_id'], color=E.CINZA, lw=2.6, alpha=0.5, label='grandeza real')
    for k, r in enumerate(curvas['tau_rms']):
        v = NIVEIS['tau_rms'][k]
        a_.plot(r['t'], r['V_re'], color=cores[k], lw=0.9, label='τ = %s s (prev. %s %% / med. %s %%)' % (
            E.num(v, 3 if v < 0.1 else 2), E.num(100*X['tau_rms'][k]['previsao']['fracao_afundamento'], 0),
            E.num(100*X['tau_rms'][k]['medido']['fracao_afundamento'], 0)))
    a_.set_xlim(0.9, 3.0); a_.set_ylabel('V [pu]'); a_.legend(fontsize=5.8, loc='lower right')
    a_.set_title('τ do AD637 (C_AV), ensaio (c): fração do afundamento que a leitura alcança')
    a_.axvspan(P.T_EV, P.T_EV + P.DUR_FALTA, color=E.FAIXA, zorder=0)
    # sigma (f no ensaio a)
    a_ = ax[0, 1]
    for k, r in enumerate(curvas['sigma']):
        v = NIVEIS['sigma'][k]
        m = X['sigma'][k]
        a_.plot(r['t'], r['f_re'], color=cores[k], lw=0.7 if k < 3 else 0.5,
                label='σ = %s mV: viés V prev. %s %% / med. %s %%' % (E.num(1e3*v, 0), E.num(m['previsao']['vies_V_pct'], 2),
                                                                     E.num(m['medido']['vies_V_pct'], 2)), zorder=5 - k)
    fid, _ = limpa_f(r['t'], r['f_id'])
    a_.plot(r['t'], fid, color=E.TINTA, lw=0.8, ls='--', label='medição ideal')
    a_.set_xlim(0.0, 4.0); a_.set_ylim(59.8, 60.25); a_.set_ylabel('f [Hz]'); a_.legend(fontsize=5.6, loc='upper right')
    a_.set_title('Ruído no secundário, ensaio (a): frequência medida')
    # n_cic (f no ensaio b)
    a_ = ax[1, 0]
    r0 = curvas['n_cic'][0]
    fid, _ = limpa_f(r0['t'], r0['f_id'])
    a_.plot(r0['t'], fid, color=E.CINZA, lw=2.6, alpha=0.5, label='grandeza real')
    for k, r in enumerate(curvas['n_cic']):
        v = NIVEIS['n_cic'][k]; m = X['n_cic'][k]
        a_.plot(r['t'], r['f_re'], color=cores[k], lw=0.9, label='N = %d: ganho prev. %s / med. %s' % (
            v, E.num(m['previsao']['ganho_1_32Hz'], 2), E.num(m['medido']['ganho_1_32Hz'], 2)))
    a_.set_xlim(0, 4); a_.set_ylabel('f [Hz]'); a_.set_xlabel('t [s]'); a_.legend(fontsize=5.8, loc='upper right')
    a_.set_title('Média do frequencímetro, ensaio (b): amplitude e atraso em 1,32 Hz')
    # fclk (f no ensaio a)
    a_ = ax[1, 1]
    r0 = curvas['fclk'][0]
    fid, _ = limpa_f(r0['t'], r0['f_id'])
    for k, r in enumerate(curvas['fclk']):
        v = NIVEIS['fclk'][k]; m = X['fclk'][k]
        a_.plot(r['t'], r['f_re'], color=cores[k], lw=0.8, zorder=5 - k, label='fclk = %s: dp/ciclo prev. %s mHz' % (
            ('%g MHz' % (v/1e6)).replace('.', ',') if v >= 1e6 else ('%g kHz' % (v/1e3)).replace('.', ','),
            E.num(m['previsao']['dp_ciclo_mHz'], 1)))
    a_.plot(r0['t'], fid, color=E.TINTA, lw=0.8, ls='--', label='medição ideal')
    a_.set_xlim(0.6, 4.0); a_.set_ylim(59.5, 60.5); a_.set_xlabel('t [s]'); a_.set_ylabel('f [Hz]')
    a_.legend(fontsize=5.8, loc='upper right')
    a_.set_title('Relógio do contador, ensaio (a): captura com ±1 tique (f²/fclk por ciclo)')
    for a_ in ax.flat:
        E.virgula(a_)
    fig.tight_layout()
    E.salva(fig, 'fig-08-exacerbacao')


# ============================================================== csv e json
def grava_csv(res):
    os.makedirs(DADOS, exist_ok=True)
    for nome, r in res.items():
        fid, _ = limpa_f(r['t'], r['f_id'])
        cab = 'Time,delta_graus,V_ideal_pu,V_real_pu,f_ideal_Hz,f_real_Hz'
        M = np.column_stack([r['t'], G(r['delta']), r['V_id'], r['V_re'], fid, r['f_re']])
        np.savetxt(os.path.join(DADOS, 'e03_ensaio_%s.csv' % nome), M, delimiter=',', header=cab, comments='',
                   fmt='%.6f')


def limpa(o):
    if isinstance(o, dict):
        return {str(k): limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpa(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


def main():
    E.aplica_estilo()
    res = {n: ens_real(n) for n in 'abc'}
    M = {n: metricas(res[n]) for n in 'abc'}
    Car = {n: caracteristicos(n, res[n]) for n in 'abc'}
    R1 = r1(res)
    B, (rv, rf) = bancada()
    L = projeto_rms()
    Cn = contribuicoes()
    X, curvas = exacerba()
    fig_demanda(R1, res)
    fig_cadeia()
    fig_bancada(B, rv, rf)
    fig_projeto_rms(L)
    fig_ensaios(res, M)
    fig_contribuicoes(Cn)
    fig_exacerbacao(X, curvas)
    grava_csv(res)
    out = dict(R1=R1, R2=dict(bancada=B, real=P.REAL, neutro=P.NEUTRO),
               R3=dict(projeto=dict(K_DIV=P.K_DIV, RTP=P.RTP, V_por_pu=P.V_PU_VD, CAV_uF=P.CAV_UF,
                                    tau_rms=P.REAL['tau_rms'], FC_SK=P.FC_SK, VREF_ADC=P.VREF_ADC,
                                    FC_PF=P.FC_PF, HIST=P.HIST, fclk=P.REAL['fclk'], n_cic=P.REAL['n_cic'])),
               R4=dict(metricas=M, caracteristicos=Car, contribuicoes=Cn),
               R5=X)
    with open(os.path.join(AQUI, 'resultados_e03.json'), 'w', encoding='utf-8') as fh:
        json.dump(limpa(out), fh, ensure_ascii=False, indent=1)
    print('E03 ok:', json.dumps(limpa(dict(M=M, bancada=B)), ensure_ascii=False)[:1500])


if __name__ == '__main__':
    main()
