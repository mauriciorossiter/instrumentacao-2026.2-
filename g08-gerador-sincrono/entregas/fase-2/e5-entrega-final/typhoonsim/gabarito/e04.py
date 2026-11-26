# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 04: malha fechada com instrumentacao real.

R1 especificacao de desempenho (CRIT)
R2 AVR PI + PSS projetados com a medicao ideal: polos, margens, erro esperado e verificacao no tempo
R3 o mesmo controlador realimentado pela medicao real: referencia x medido x real da planta
R4 intensidade de 4 caracteristicas (erro do TP, tau do AD637, media do frequencimetro, ruido):
   previsao algebrica, resultado e limiar de cada criterio -> mapa de desempenho
R5 acao de projeto: pre-filtro passa-faixa no frequencimetro (filtragem) -> ganho nos criterios e custo
R6 sintese (texto em resultados_e04.json) e roteiro (instrucoes.md)

Saidas: ../../relatorio/figuras/fig-01..06-*.png, resultados_e04.json, dados/e04_*.csv
Uso:    python e04.py      (numpy, scipy, matplotlib; ~2 min)
"""
import json
import math
import os

import numpy as np
from scipy.optimize import curve_fit

import parametros_e34 as P
import sistema as S
import controle as K
import estilo as E

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, 'dados')
G = np.degrees

# ======================================================================= R1: criterios
CRIT = dict(
    ess_pct=0.5,       # |Vt real - Vref| em regime, % de Vref (precisao tipica de AVR digital: 0,25-0,5 %)
    ts_s=1.5,          # acomodacao no degrau de Vref de 2 %, faixa de ±10 % do degrau (±0,002 pu)
    Mp_pct=15.0,       # sobressinal no degrau de Vref de 2 % (15 % do degrau = 0,3 % de sobretensao)
    efd_pico=P.EFD_MAX,  # o degrau de 2 % nao pode levar Efd ao teto (operacao linear, reserva para faltas)
    dp_efd=0.10,       # pu, desvio-padrao de Efd em regime (atividade aleatoria da excitatriz)
    afund_pct=1.5,     # afundamento maximo de Vt no degrau de Pm de 0,1 pu, % do valor anterior (aberta: 1,25 %)
    zeta=0.10,         # amortecimento do modo eletromecanico (o rotor nao pode oscilar por dezenas de s)
)
ROT_CRIT = dict(ess_pct='erro estac.', ts_s='t_s', Mp_pct='M_p', efd_pico='Efd pico', dp_efd='σ(Efd)',
                afund_pct='afundamento', zeta='ζ eletromec.')


def passa(k, v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return False
    if k == 'zeta':
        return v >= CRIT[k]
    if k == 'efd_pico':
        return v < CRIT[k] - 1e-6
    if k == 'ess_pct':
        return abs(v) <= CRIT[k]
    return v <= CRIT[k]


# ======================================================================= metricas
def media_movel(x, n=10):
    if n <= 1:
        return x
    c = np.cumsum(np.insert(x, 0, 0.0))
    y = (c[n:] - c[:-n])/n
    return np.concatenate([np.full(n - 1, y[0]), y])


def fit_zeta(t, d, t0):
    """ζ do modo eletromecanico por ajuste de c + A e^{-στ} cos(ωτ + φ) em δ(t), τ = t - t0."""
    i = (t >= t0) & (t <= t0 + 7.0)
    tt, y = t[i] - t0, d[i]
    def f(tau, c, A, s, w, ph):
        return c + A*np.exp(-s*tau)*np.cos(w*tau + ph)
    best = None
    for w0 in (7.0, 8.3, 9.5):
        for s0 in (0.3, 1.0, 2.5):
            try:
                p, _ = curve_fit(f, tt, y, p0=[y[-1], (y.max() - y.min())/2, s0, w0, 0.0], maxfev=20000)
                res = np.sum((f(tt, *p) - y)**2)
                if p[3] > 2 and (best is None or res < best[1]):
                    best = (p, res)
            except Exception:                      # noqa: BLE001
                pass
    if best is None:
        return float('nan'), float('nan'), float('nan')
    c, A, s, w, ph = best[0]
    w = abs(w)
    return float(s/math.hypot(s, w)), float(s), float(w)


def roda3(cfg, T_r=6.0, T_p=11.0):
    """Ensaios r (degrau de Vref), p (degrau de Pm) e regime (3 s sem evento)."""
    rr = S.simula(S.ensaio('r', T=T_r), cfg)
    rp = S.simula(S.ensaio('p', T=T_p), cfg)
    e0 = S.ensaio('r', T=3.0); e0['dvref'] = lambda t: 0.0
    r0 = S.simula(e0, cfg)
    return rr, rp, r0


def metr_degrau(t, y, vref_final, y0, dv=P.DVREF):
    y = media_movel(y, 10)                         # media de 10 ms: ruido nao conta como sobressinal
    yf = float(np.mean(y[t > t[-1] - 1.0]))
    i = t > P.T_EV
    Mp = 100*max(0.0, (y[i].max() - yf))/abs(yf - y0)
    fora = np.where(i & (np.abs(y - yf) > 0.1*dv))[0]
    ts = float(t[fora[-1]] - P.T_EV) if len(fora) else 0.0
    return dict(Mp_pct=float(Mp), ts_s=ts, final=yf, ess_pct=float(100*(yf - vref_final)/vref_final))


def metricas(cfg, runs=None):
    rr, rp, r0 = runs or roda3(cfg)
    vref0 = cfg['vref']; vref1 = vref0 + P.DVREF
    med_key = 'V_re' if cfg['fb_v'] == 'real' else 'V_id'
    out = {}
    for lado, key in (('planta', 'V_id'), ('medido', med_key)):
        y0 = float(np.mean(media_movel(rr[key], 10)[(rr['t'] > 0.5) & (rr['t'] < P.T_EV)]))
        m = metr_degrau(rr['t'], rr[key], vref1, y0)
        tp = rp['t']; yp = media_movel(rp[key], 10)
        vpre = float(np.mean(yp[(tp > 0.5) & (tp < P.T_EV)]))
        m['afund_pct'] = float(100*(vpre - yp[tp > P.T_EV].min())/vpre)
        out[lado] = m
    out['efd_pico'] = float(rr['Efd'][rr['t'] > P.T_EV].max())
    out['dp_efd'] = float(np.std(r0['Efd'][r0['t'] > 0.2]))
    out['dp_vt'] = float(np.std(r0['V_id'][r0['t'] > 0.2]))
    z, s, w = fit_zeta(rp['t'], G(rp['delta']), P.T_EV + 0.25)
    out['zeta'] = z; out['sigma_em'] = s; out['wd_em'] = w
    out['avalia'] = {k: passa(k, valor_crit(out, k)) for k in CRIT}
    return out, (rr, rp, r0)


def valor_crit(m, k):
    if k in ('ess_pct', 'ts_s', 'Mp_pct', 'afund_pct'):
        return m['planta'][k]
    return m[k]


def cfg_malha(fb='real', **kw):
    return S.cfg_padrao(malha='fechada', pss=True, fb_v=fb, fb_f=fb, **kw)


# ======================================================================= R2
def r2():
    avr_so = dict(malha='fechada', pss=False)
    com = dict(malha='fechada', pss=True)
    linhas = {}
    for nome, c in (('malha aberta (E02)', dict(malha='aberta')), ('AVR (PI) só', avr_so), ('AVR + PSS', com)):
        ev = K.autovalores(c)
        s, wd, z, lam = K.modo_em(K.modelo(c)[0])
        linhas[nome] = dict(polos=[[float(e.real), float(e.imag)] for e in ev if e.imag >= 0],
                            em=dict(sigma=s, wd=wd, zeta=z))
    # lugar do modo eletromecanico com Kpss
    kps = np.linspace(0, 45, 46)
    lugar = []
    for kp in kps:
        s, wd, z, lam = K.modo_em(K.modelo(dict(com, kpss=kp))[0])
        lugar.append([float(kp), float(-s), float(wd), float(z)])
    # malha de tensao de projeto (rotor travado): L = K6*Ki/s * H_V
    w = np.logspace(-1, 3, 3000)
    def Lproj(tau):
        s = 1j*w
        hv = 1.0 if tau <= 0 else 1/(1 + s*tau/2)*(2*math.pi*P.FC_SK)**2/(s*s + 2*math.pi*P.FC_SK/P.Q_SK*s + (2*math.pi*P.FC_SK)**2)
        return P.K6*K.KI/s*hv
    marg = {}
    for tau in (0.0, P.REAL['tau_rms']):
        L = Lproj(tau)
        i = np.argmin(np.abs(np.abs(L) - 1))
        fase = np.degrees(np.unwrap(np.angle(L)))
        mf = 180 + fase[i]
        j = np.where(fase <= -180)[0]
        mg = -20*math.log10(abs(L[j[0]])) if len(j) else float('inf')
        marg['%g' % tau] = dict(MF=float(mf), wc=float(w[i]), MG_dB=float(mg), w180=float(w[j[0]]) if len(j) else None)
    return dict(polos=linhas, lugar=lugar, margens=marg, Kp=K.KP, Ki=K.KI, wc=K.OMEGA_C, T1=K.T1, T2=K.T2, Tw=K.TW,
                Kpss=K.KPSS, vst=K.VST_MAX, fase_gep=float(math.degrees(K.FASE_GEP)),
                ess_esperado=dict(medido=0.0, planta_pct=-100*P.REAL['eps_tp']/(100 + P.REAL['eps_tp'])),
                Lproj=dict(w=w.tolist(), ideal=Lproj(0.0).tolist(), real=Lproj(P.REAL['tau_rms']).tolist()))


# ======================================================================= R4
NIVEIS = dict(
    eps_tp=(0.0, 0.3, 0.6, 1.2, 3.0),
    tau_rms=(0.055, 0.1, 0.25, 0.5, 1.0),
    n_cic=(1.0, 2.0, 4.0, 8.0, 16.0),
    sigma=(0.0, 0.002, 0.005, 0.01, 0.02),
)


def prev_linear(cfg):
    """Previsao pelo modelo linear: Mp e ts no degrau de Vref, afundamento no degrau de Pm, ζ."""
    t, vt, vm, dd = K.resposta(cfg, 'vref')
    fin = vt[-1]
    Mp = 100*max(0.0, vt.max() - fin)/abs(fin)
    fora = np.where(np.abs(vt - fin) > 0.1*P.DVREF)[0]
    ts = float(t[fora[-1]]) if len(fora) else 0.0
    t2, vt2, _, _ = K.resposta(cfg, 'pm')
    af = float(-100*vt2.min()/P.VT0)
    z = K.modo_em(K.modelo(dict(cfg, malha='fechada'))[0])[2]
    return dict(Mp_pct=float(Mp), ts_s=ts, afund_pct=af, zeta=float(z))


def previsao(ch, v, base=None):
    cfg = dict(malha='fechada', pss=True, fb_v='real', fb_f='real', tau_rms=P.REAL['tau_rms'], n_cic=P.REAL['n_cic'])
    if ch == 'eps_tp':
        return dict(ess_pct=-100*v/(100 + v))
    if ch in ('tau_rms', 'n_cic'):
        cfg[ch] = v
        out = prev_linear(cfg)
        if ch == 'tau_rms':
            s = 1j*K.OMEGA_C
            hsk = (2*math.pi*P.FC_SK)**2/(s*s + 2*math.pi*P.FC_SK/P.Q_SK*s + (2*math.pi*P.FC_SK)**2)
            out['MF_graus'] = 90 - math.degrees(math.atan(K.OMEGA_C*v/2)) + math.degrees(np.angle(hsk))  # AD637: tau/2
        return out
    if ch == 'sigma':
        if base is None:
            return {}
        d0, d5 = base                                     # σ(Efd) sem ruido e com 5 mV
        k = math.sqrt(max(d5**2 - d0**2, 0))/0.005
        return dict(dp_efd=math.sqrt(d0**2 + (k*v)**2), sigma_limiar_mV=1e3*math.sqrt(max(CRIT['dp_efd']**2 - d0**2, 0))/k)
    return {}


def mapa(base_sigma):
    out = {}
    for ch, niveis in NIVEIS.items():
        out[ch] = []
        for v in niveis:
            m, _ = metricas(cfg_malha(**{ch: v}))
            out[ch].append(dict(valor=v, previsao=previsao(ch, v, base_sigma), m=m))
        # limiar: onde cada criterio muda de estado entre niveis vizinhos (interpolacao linear no valor)
        lim = {}
        for k in CRIT:
            vals = [valor_crit(x['m'], k) for x in out[ch]]
            ok = [passa(k, x) for x in vals]
            trans = []
            for j in range(1, len(niveis)):
                if ok[j - 1] != ok[j]:
                    a, b = vals[j - 1], vals[j]
                    alvo = CRIT[k] if k != 'ess_pct' else (CRIT[k] if b >= 0 else -CRIT[k])
                    fr = (alvo - a)/(b - a) if b != a else 0.0
                    trans.append(dict(de=niveis[j - 1], ate=niveis[j], limiar=float(niveis[j - 1] + fr*(niveis[j] - niveis[j - 1])),
                                      sentido='deixa de atender' if ok[j - 1] else 'passa a atender'))
            lim[k] = trans if trans else ('atende em todos' if all(ok) else 'falha em todos')
        out[ch + '_limiar'] = lim
    return out


# ======================================================================= figuras
def fig_projeto(R2):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(10.8, 3.0), gridspec_kw=dict(width_ratios=[1.1, 1, 1]))
    lg = np.array(R2['lugar'])
    sc = ax[0].scatter(lg[:, 1], lg[:, 2], c=lg[:, 0], cmap='Blues', s=10, vmin=-10, vmax=45)
    for nome, cor, mk in (('malha aberta (E02)', E.TINTA2, 's'), ('AVR (PI) só', E.CRITICO, 'x'), ('AVR + PSS', E.AZUL, 'o')):
        em = R2['polos'][nome]['em']
        ax[0].plot(-em['sigma'], em['wd'], mk, color=cor, ms=6, label='%s: ζ = %s' % (nome, E.num(em['zeta'], 3)))
    zz = np.linspace(0, 3, 10)
    ax[0].plot(-CRIT['zeta']/math.sqrt(1 - CRIT['zeta']**2)*np.linspace(0, 10, 10), np.linspace(0, 10, 10), '--',
               color=E.CINZA, lw=0.8)
    ax[0].text(-1.05, 9.6, 'ζ = 0,10', fontsize=6.5, color=E.TINTA2)
    ax[0].set_xlim(-2.0, 0.2); ax[0].set_ylim(6.5, 10)
    ax[0].axvline(0, color=E.TINTA, lw=0.6)
    ax[0].set_xlabel('Re [1/s]'); ax[0].set_ylabel('Im [rad/s]')
    ax[0].set_title('Modo eletromecânico: Kpss de 0 a 45'); ax[0].legend(fontsize=5.8, loc='lower left')
    w = np.array(R2['Lproj']['w'])
    for key, cor, rot in (('ideal', E.TINTA, 'medição ideal'), ('real', E.AZUL, 'AD637 (C_AV 2,2 µF) + SK 10 Hz')):
        L = np.array([complex(*x) if isinstance(x, (list, tuple)) else complex(x) for x in R2['Lproj'][key]])
        ax[1].semilogx(w, 20*np.log10(np.abs(L)), color=cor, label=rot)
        ax[2].semilogx(w, np.degrees(np.unwrap(np.angle(L))), color=cor, label=rot)
    ax[1].axhline(0, color=E.CINZA, lw=0.7); ax[2].axhline(-180, color=E.CRITICO, lw=0.7, ls='--')
    ax[1].set_xlabel('ω [rad/s]'); ax[2].set_xlabel('ω [rad/s]')
    ax[1].set_ylabel('|L| [dB]'); ax[2].set_ylabel('∠L [°]')
    mi, mr = R2['margens']['0'], R2['margens']['%g' % P.REAL['tau_rms']]
    ax[1].set_title('Malha de tensão (rotor travado): ωc = %s rad/s' % E.num(mi['wc'], 2))
    ax[2].set_title('MF: %s° (ideal) → %s° (real)' % (E.num(mi['MF'], 0), E.num(mr['MF'], 0)))
    ax[1].legend(fontsize=6); ax[2].set_ylim(-270, -60)
    for a_ in ax:
        E.virgula(a_)
    for a_ in ax[1:]:
        from matplotlib.ticker import LogFormatterSciNotation
        a_.xaxis.set_major_formatter(LogFormatterSciNotation())
    fig.tight_layout()
    E.salva(fig, 'fig-01-projeto')


def fig_ensaios(runs, nome, titulo, real=False, ideal_ref=None):
    """3 colunas (r, p, f) x 3 linhas (tensao; δ ou f; Efd)."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 3, figsize=(11.0, 6.2), sharex='col')
    tits = dict(r='degrau de Vref (+0,02 pu)', p='perturbação: degrau de Pm 0,8 → 0,9 pu', f='falta franca de 200 ms')
    jan = dict(r=(0.6, 4.0), p=(0.6, 8.0), f=(0.8, 8.0))
    for j, k in enumerate('rpf'):
        r = runs[k]; t = r['t']
        if ideal_ref is not None:
            ax[0, j].plot(ideal_ref[k]['t'], ideal_ref[k]['V_id'], color=E.CINZA, lw=2.4, alpha=0.45, label='planta, malha ideal (R2)')
        ax[0, j].plot(t, r['Vref'] - r['upss'], color=E.CRITICO, lw=0.9, ls='--', label='referência Vref')
        if real:
            ax[0, j].plot(t, r['V_re'], color=E.AZUL, lw=0.7, label='tensão medida (realimentada)')
        ax[0, j].plot(t, r['V_id'], color=E.TINTA, lw=1.1, label='tensão real da planta')
        ax[0, j].set_title(tits[k])
        if k == 'f':
            ax[0, j].set_ylim(0.2, 1.3)
            ax[1, j].plot(t, G(r['delta']), color=E.TINTA, lw=1.0)
            ax[1, j].set_ylabel('δ [°]') if j == 0 else None
        else:
            lo = min(r['V_id'][t > 0.5].min(), (r['Vref'] - r['upss']).min()) - 0.004
            hi = max(r['V_id'][t > 0.5].max(), (r['Vref'] - r['upss']).max()) + 0.004
            ax[0, j].set_ylim(lo, hi)
            ax[1, j].plot(t, G(r['delta']), color=E.TINTA, lw=1.0, label='δ')
        if k == 'f':
            for a_ in ax[:, j]:
                a_.axvspan(P.T_EV, P.T_EV + P.DUR_FALTA, color=E.FAIXA, zorder=0)
        ax[2, j].plot(t, r['Efd'], color=E.LARANJA, lw=0.6)
        ax[2, j].axhline(P.EFD_MAX, color=E.CRITICO, lw=0.6, ls=':')
        ax[2, j].set_xlabel('t [s]'); ax[0, j].set_xlim(*jan[k])
        if k != 'f':
            ax[2, j].set_ylim(min(-0.5, r['Efd'][t > 0.5].min() - 0.2), max(3.0, r['Efd'].max() + 0.2))
    ax[0, 0].set_ylabel('V [pu]'); ax[1, 0].set_ylabel('δ [°]'); ax[2, 0].set_ylabel('Efd [pu]')
    ax[0, 0].legend(fontsize=5.8, loc='lower right')
    for a_ in ax.flat:
        E.virgula(a_)
    fig.suptitle(titulo, x=0.01, ha='left', fontsize=8.5, weight='bold')
    fig.tight_layout()
    E.salva(fig, nome)


def fig_mapa(Mp_):
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    linhas, rot_l, cel = [], [], []
    unid = dict(eps_tp=('ε_TP', '%', lambda v: E.num(v, 1)), tau_rms=('τ_RMS', 's', lambda v: E.num(v, 3) if v < 0.1 else E.num(v, 2)),
                n_cic=('N', 'ciclos', lambda v: '%d' % v), sigma=('σ', 'mV', lambda v: E.num(1e3*v, 0)))
    fmt = dict(ess_pct=lambda v: E.num(v, 2), ts_s=lambda v: E.num(v, 2), Mp_pct=lambda v: E.num(v, 1),
               efd_pico=lambda v: E.num(v, 2), dp_efd=lambda v: E.num(v, 3), afund_pct=lambda v: E.num(v, 2),
               zeta=lambda v: E.num(v, 3))
    for ch in NIVEIS:
        nm, un, f = unid[ch]
        for x in Mp_[ch]:
            rot_l.append('%s = %s %s%s' % (nm, f(x['valor']), un, '  (padrão)' if abs(x['valor'] - P.REAL[ch]) < 1e-12 else ''))
            linhas.append([1 if x['m']['avalia'][k] else 0 for k in CRIT])
            cel.append([fmt[k](valor_crit(x['m'], k)) for k in CRIT])
    A = np.array(linhas, dtype=float)
    fig, ax = plt.subplots(figsize=(8.8, 6.0))
    cmap = ListedColormap(['#f6d4cc', '#d6eedf'])
    ax.imshow(A, cmap=cmap, aspect='auto', vmin=0, vmax=1)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            ax.text(j, i, cel[i][j], ha='center', va='center', fontsize=6.6,
                    color=E.TINTA if A[i, j] else E.CRITICO, weight='normal' if A[i, j] else 'bold')
    ax.set_xticks(range(len(CRIT)))
    ax.set_xticklabels(['%s\n%s %s' % (ROT_CRIT[k], '≥' if k == 'zeta' else ('<' if k == 'efd_pico' else '≤'),
                                       fmt[k](CRIT[k])) for k in CRIT], fontsize=6.6)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rot_l))); ax.set_yticklabels(rot_l, fontsize=6.6)
    for y in (4.5, 9.5, 14.5):
        ax.axhline(y, color='white', lw=3)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    E.salva(fig, 'fig-05-mapa')


def fig_acao(antes, depois, A5):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(10.8, 3.0))
    for (rr, rp, r0), cor, rot in ((antes, E.LARANJA, 'antes: passa-baixas 150 Hz'), (depois, E.AZUL, 'depois: passa-faixa 60 ± 5 Hz')):
        t = r0['t']; i = t > 0.2
        ax[0].plot(t[i], r0['Efd'][i], color=cor, lw=0.6, label='%s (σ = %s pu)' % (rot, E.num(np.std(r0['Efd'][i]), 3)))
        from scipy.signal import welch
        F, X = welch(1e3*(r0['f_re'][i] - r0['f_re'][i].mean()), fs=1.0/(t[1] - t[0]), nperseg=1024)
        ax[1].semilogy(F[1:], X[1:], color=cor, lw=0.9, label=rot)
        ax[2].plot(rp['t'], G(rp['delta']), color=cor, lw=0.9, label=rot)
    ax[0].set_xlabel('t [s]'); ax[0].set_ylabel('Efd [pu]'); ax[0].set_title('Esforço em regime (sem evento)')
    ax[0].legend(fontsize=5.8, loc='upper right'); ax[0].set_ylim(0.3, 2.4)
    ax[1].axvspan(0.8, 3.0, color=E.FAIXA, zorder=0); ax[1].text(0.9, 0.9, 'banda do\nmodo', transform=ax[1].get_xaxis_transform(), fontsize=6, va='top')
    ax[1].set_xlim(0, 30); ax[1].set_ylim(1e-4, 0.3); ax[1].set_xlabel('frequência [Hz]'); ax[1].set_ylabel('DEP de f medida [mHz²/Hz]')
    ax[1].set_title('Ruído na frequência que chega ao PSS'); ax[1].legend(fontsize=5.8)
    ax[2].set_xlim(0.8, 6); ax[2].set_xlabel('t [s]'); ax[2].set_ylabel('δ [°]')
    ax[2].set_title('Perturbação: ζ %s → %s' % (E.num(A5['antes']['zeta'], 3), E.num(A5['depois']['zeta'], 3)))
    ax[2].legend(fontsize=5.8, loc='lower right')
    for a_ in (ax[0], ax[2]):
        E.virgula(a_)
    ax[1].xaxis.set_major_formatter(__import__('matplotlib.ticker', fromlist=['FuncFormatter']).FuncFormatter(lambda x, p: E.num(x, 0)))
    fig.tight_layout()
    E.salva(fig, 'fig-06-acao')


# ======================================================================= R5
def r5():
    base = cfg_malha()
    nova = cfg_malha(pf_bw=10.0)
    ma, ra = metricas(base)
    mb, rb = metricas(nova)
    fa = S.simula(S.ensaio('f'), base); fb = S.simula(S.ensaio('f'), nova)
    # custo: atraso do frequencimetro (bancada) e erro transitorio na falta
    banco = {}
    for nome, c in (('antes', S.cfg_padrao()), ('depois', S.cfg_padrao(pf_bw=10.0))):
        r = S.simula(S.ensaio('banco_f'), c)
        t, x = r['t'], r['f_re']
        x0, x1 = x[t < 0.5].mean(), x[t > 1.2].mean()
        j = np.where((t >= 0.5) & (np.abs(x - x0) >= 0.9*abs(x1 - x0)))[0][0]
        r0 = S.simula(S.ensaio('banco_0'), c)
        banco[nome] = dict(t90_ms=float(1e3*(t[j] - 0.5)), dp_f_mHz=float(1e3*np.std(r0['f_re'][r0['t'] > 0.3])))
    falta = {}
    for nome, r in (('antes', fa), ('depois', fb)):
        t = r['t']
        falta[nome] = dict(delta_max=float(G(r['delta']).max()), efd_teto_s=float(np.sum(r['Efd'] >= P.EFD_MAX - 1e-9)*(t[1] - t[0])))
    # mapa de ruido com o pre-filtro novo (limiar de sigma)
    sig = []
    for v in NIVEIS['sigma']:
        m, _ = metricas(cfg_malha(pf_bw=10.0, sigma=v))
        sig.append(dict(valor=v, dp_efd=m['dp_efd'], zeta=m['zeta']))
    return dict(antes=dict(ma, banco=banco['antes'], falta=falta['antes']),
                depois=dict(mb, banco=banco['depois'], falta=falta['depois']), sigma_depois=sig), ra, rb


# ======================================================================= main
def limpa(o):
    if isinstance(o, dict):
        return {str(k): limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpa(v) for v in o]
    if isinstance(o, complex):
        return [o.real, o.imag]
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if isinstance(o, np.ndarray):
        return limpa(o.tolist())
    return o


def grava_csv(runs, rot):
    os.makedirs(DADOS, exist_ok=True)
    for k, r in runs.items():
        cab = 'Time,Vref_pu,V_planta_pu,V_medida_pu,f_ideal_Hz,f_medida_Hz,delta_graus,Efd_pu,upss_pu'
        M = np.column_stack([r['t'], r['Vref'] - r['upss'], r['V_id'], r['V_re'], r['f_id'], r['f_re'], G(r['delta']),
                             r['Efd'], r['upss']])
        np.savetxt(os.path.join(DADOS, 'e04_%s_%s.csv' % (rot, k)), M, delimiter=',', header=cab, comments='', fmt='%.6f')


def main():
    # copia da Entrega Final: as figuras da E04 vao para gabarito/figuras_e04 (nao misturar com as do relatorio final)
    E.DIR_PNG = os.path.join(AQUI, 'figuras_e04')
    E.aplica_estilo()
    R2 = r2()
    fig_projeto(R2)
    # R2: verificacao com medicao ideal; R3: medicao real
    mi, (rri, rpi, r0i) = metricas(cfg_malha('ideal'))
    mr, (rrr, rpr, r0r) = metricas(cfg_malha('real'))
    fi = S.simula(S.ensaio('f'), cfg_malha('ideal'))
    fr = S.simula(S.ensaio('f'), cfg_malha('real'))
    ideal = dict(r=rri, p=rpi, f=fi); real = dict(r=rrr, p=rpr, f=fr)
    # avr so', para mostrar por que o PSS
    ms, _ = metricas(dict(cfg_malha('ideal'), pss=False))
    falta = {}
    for nome, r in (('ideal', fi), ('real', fr)):
        t = r['t']; v = media_movel(r['V_id'], 10)
        fora = np.where((t > P.T_EV + P.DUR_FALTA) & (np.abs(v - r['Vref']) > 0.05*P.VT0))[0]
        falta[nome] = dict(delta_max=float(G(r['delta']).max()), V_min=float(r['V_id'].min()),
                           t_recupera_5pct_s=float(t[fora[-1]] - P.T_EV - P.DUR_FALTA) if len(fora) else 0.0,
                           efd_teto_s=float(np.sum(r['Efd'] >= P.EFD_MAX - 1e-9)*(t[1] - t[0])))
    fig_ensaios(ideal, 'fig-02-ideal', 'R2 — AVR (PI) + PSS realimentados pela medição IDEAL')
    fig_ensaios(real, 'fig-03-real', 'R3 — o mesmo controlador realimentado pela medição REAL', real=True, ideal_ref=ideal)
    grava_csv(ideal, 'ideal'); grava_csv(real, 'real')
    # R4
    d0 = metricas(cfg_malha(sigma=0.0))[0]['dp_efd']
    Mp_ = mapa((d0, mr['dp_efd']))
    fig_mapa(Mp_)
    # R5
    A5, ra, rb = r5()
    fig_acao(ra, rb, A5)
    out = dict(R1=CRIT, R2=dict(R2, verificacao_ideal=mi, avr_so=ms), R3=dict(ideal=mi, real=mr, falta=falta),
               R4=Mp_, R5=A5)
    out['R2'].pop('Lproj')
    with open(os.path.join(AQUI, 'resultados_e04.json'), 'w', encoding='utf-8') as fh:
        json.dump(limpa(out), fh, ensure_ascii=False, indent=1)
    resumo = dict(ideal={k: valor_crit(mi, k) for k in CRIT}, real={k: valor_crit(mr, k) for k in CRIT},
                  avr_so={k: valor_crit(ms, k) for k in CRIT},
                  limiares={ch: Mp_[ch + '_limiar'] for ch in NIVEIS}, R5={k: (valor_crit(A5['antes'], k), valor_crit(A5['depois'], k)) for k in CRIT},
                  falta=falta)
    print(json.dumps(limpa(resumo), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
