# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E04: projeto do controle (AVR PI + PSS) e modelo linear para a previsao
algebrica (polos em malha fechada, margens, efeito de cada caracteristica do instrumento).

Modelo linear em torno do ponto de operacao (Heffron-Phillips sem reacao de armadura, K4 = 0):
    Δδ' = Δω ;  M Δω' = ΔPm - K1 Δδ - K2 ΔE' - D Δω
    T'd0 ΔE'' = ΔEfd - ΔE'
    ΔVt = K5 Δδ + K6 ΔE'                    (K5 < 0: com o rotor adiantado a tensao terminal cai)
    Δft = (dθt/dδ Δω + dθt/dE' ΔE'')/2π      (frequencia que o TP enxerga, nao a do rotor)
Medicao de tensao real ~ AD637 (implicito: 1a ordem com tau_rms/2) + Sallen-Key (2a ordem, 10 Hz);
medicao de frequencia real ~ atraso de 1 ciclo (Pade) + media exponencial de n_cic ciclos ((n_cic-1)*T).
AVR: PI com o zero cancelando o polo do campo (Kp/Ki = T'd0)  =>  L(s) = K6*Ki/s  =>  ωc = K6*Ki.
PSS: lavagem Tw + dois avanco-atraso iguais compensando a fase de ΔPe/ΔVref em ω do modo eletromecanico.
"""
import math

import numpy as np

import parametros_e34 as P

# ------------------------------------------------------------------ constantes do ponto de operacao
K1 = P.KS
DTH_DE = (P.XE/P.X_TOT)*(P.XDP/P.X_TOT*P.V_BAR)*math.sin(P.DELTA0)/P.VT0**2    # dθt/dE' (rad/pu)
T_CICLO = 1.0/P.F_REDE

# ------------------------------------------------------------------ AVR (R2 da E04)
OMEGA_C = 5.0                    # rad/s, cruzamento da malha de tensao: ts(2 %) ~ 4/ωc = 0,8 s, sem sobressinal
KI = OMEGA_C/P.K6                # 1/s
KP = KI*P.TDO                    # pu/pu (zero do PI em 1/T'd0)

# ------------------------------------------------------------------ PSS (R2 da E04)
TW = 3.0                         # s, lavagem (so' passa oscilacoes; regime de f nao mexe na tensao)
VST_MAX = 0.10                   # pu, limite da saida do PSS (IEEE 421.5-2016, PSS1A de exemplo: VSTmax 0,1)
W_EM = 8.31                      # rad/s, modo eletromecanico da E01 (1,32 Hz)


def ganho_pi(s, kp=KP, ki=KI):
    return kp + ki/s


def fase_gep(w, kp=KP, ki=KI):
    """Fase de ΔPe/ΔVref com δ travado (o que o PSS precisa compensar), medicao ideal."""
    s = 1j*w
    gf = 1.0/(1.0 + s*P.TDO)
    c = ganho_pi(s, kp, ki)
    de_dvref = c*gf/(1.0 + c*gf*P.K6)
    return np.angle(P.K2*de_dvref)


def projeta_avanco(fase_rad, w=W_EM):
    """Dois avanco-atraso iguais que somam 'fase_rad' de avanco em w."""
    fs = fase_rad/2.0
    alfa = (1 + math.sin(fs))/(1 - math.sin(fs))
    T2 = 1.0/(w*math.sqrt(alfa))
    return alfa*T2, T2


FASE_GEP = fase_gep(W_EM)
_lav = math.atan(1.0/(W_EM*TW))                       # a lavagem ja' adianta um pouco
T1, T2 = projeta_avanco(-FASE_GEP - _lav)
KPSS = 20.0                      # pu/pu; zeta do modo eletromecanico 0,135 com medicao ideal (e04.py, R2)


def tustin_1a(num, den, Ts=P.TS_M):
    """(n1 s + n0)/(d1 s + d0) -> y = b0 x + b1 x1 - a1 y1 (Tustin)."""
    n1, n0 = num; d1, d0 = den
    c = 2.0/Ts
    a0 = d1*c + d0
    return ((n1*c + n0)/a0, (n0 - n1*c)/a0, (d0 - d1*c)/a0)


def coef_pss(Tw=TW, T1_=None, T2_=None, Ts=P.TS_M):
    T1_ = T1 if T1_ is None else T1_
    T2_ = T2 if T2_ is None else T2_
    return (tustin_1a((Tw, 0.0), (Tw, 1.0), Ts),
            tustin_1a((T1_, 1.0), (T2_, 1.0), Ts),
            tustin_1a((T1_, 1.0), (T2_, 1.0), Ts))


PSS_Z = coef_pss()


# ================================================================== modelo linear (previsao)
def _equacoes(cfg):
    """Equacoes lineares com Efd de ENTRADA externa. Retorna (f(x, efd_in) -> (dx, efd_saida), nomes).
    cfg: pss, kpss, fb_v/fb_f ('ideal'/'real'), tau_rms, n_cic, kp, ki, T1, T2, Tw, malha."""
    nomes = ['dd', 'dw', 'dE', 'xI']
    vreal = cfg.get('fb_v') == 'real' and cfg.get('tau_rms', 0) > 0
    freal = cfg.get('fb_f') == 'real' and cfg.get('n_cic', 0) > 0
    usa_pss = bool(cfg.get('pss'))
    if vreal:
        nomes += ['u', 's1', 's2']                     # AD637 e Sallen-Key
    if usa_pss:
        if freal:
            nomes += ['pd', 'fm']                      # Pade do atraso de 1 ciclo e media exponencial
        nomes += ['w', 'l1', 'l2']
    idx = {k: i for i, k in enumerate(nomes)}
    n = len(nomes)
    kp, ki = cfg.get('kp', KP), cfg.get('ki', KI)
    T1_, T2_, Tw = cfg.get('T1', T1), cfg.get('T2', T2), cfg.get('Tw', TW)
    kpss = cfg.get('kpss', KPSS)
    fechada = cfg.get('malha', 'fechada') == 'fechada'
    wsk = 2*math.pi*P.FC_SK
    tf = (cfg.get('n_cic', 1.0) - 1.0)*T_CICLO

    def f(x, efd_in, vref=0.0, pm=0.0, saidas=None):
        dx = np.zeros(n)
        dd, dw, dE, xI = x[idx['dd']], x[idx['dw']], x[idx['dE']], x[idx['xI']]
        dx[idx['dd']] = dw
        dx[idx['dw']] = (pm - K1*dd - P.K2*dE - P.D*dw)/P.M
        dEdot = (efd_in - dE)/P.TDO if fechada else 0.0
        dx[idx['dE']] = dEdot
        dvt = P.K5*dd + P.K6*dE
        if vreal:
            u, s1, s2 = x[idx['u']], x[idx['s1']], x[idx['s2']]
            dx[idx['u']] = (dvt - u)/(0.5*cfg['tau_rms'])   # AD637 implicito: tau/2 em pequenos sinais
            dx[idx['s1']] = s2
            dx[idx['s2']] = wsk*wsk*(u - s1) - wsk/P.Q_SK*s2
            vm = s1
        else:
            vm = dvt
        upss = 0.0
        if usa_pss:
            dft = (P.DTH_DDELTA*dw + DTH_DE*dEdot)/(2*math.pi)/P.F_REDE      # pu de frequencia
            if freal:
                pd = x[idx['pd']]
                dx[idx['pd']] = (dft - pd)*2.0/T_CICLO        # Pade 1a ordem de exp(-sT)
                yd = -dft + 2.0*pd
                if tf > 1e-9:
                    fm = x[idx['fm']]
                    dx[idx['fm']] = (yd - fm)/tf
                    fin = fm
                else:
                    fin = yd
            else:
                fin = dft
            w = x[idx['w']]                                   # lavagem: y = fin - w, w' = y/Tw
            yw = fin - w
            dx[idx['w']] = yw/Tw
            l1 = x[idx['l1']]                                 # avanco-atraso
            y1 = T1_/T2_*yw + (1 - T1_/T2_)*l1
            dx[idx['l1']] = (yw - l1)/T2_
            l2 = x[idx['l2']]
            y2 = T1_/T2_*y1 + (1 - T1_/T2_)*l2
            dx[idx['l2']] = (y1 - l2)/T2_
            upss = kpss*y2
        e = vref + upss - vm
        dx[idx['xI']] = ki*e if fechada else 0.0
        if saidas is not None:
            saidas.update(vt=dvt, vm=vm, dd=dd)
        return dx, (kp*e + xI if fechada else 0.0)
    return f, nomes


def _ss(cfg):
    """(A, B, C, D) com Efd de entrada e Efd do controlador de saida (exato: o modelo e' linear)."""
    f, nomes = _equacoes(cfg)
    n = len(nomes)
    z = np.zeros(n)
    dx0, y0 = f(z, 0.0)
    A = np.zeros((n, n)); C = np.zeros(n)
    for j in range(n):
        ej = np.zeros(n); ej[j] = 1.0
        dxj, yj = f(ej, 0.0)
        A[:, j] = dxj - dx0; C[j] = yj - y0
    dxu, yu = f(z, 1.0)
    return A, dxu - dx0, C, yu - y0, nomes


def modelo(cfg):
    """Matriz A da malha fechada (Efd_entrada = Efd_saida, inclusive a parcela algebrica do PSS)."""
    A, B, C, D, nomes = _ss(cfg)
    if cfg.get('malha', 'fechada') != 'fechada':
        return A, nomes
    return A + np.outer(B, C)/(1.0 - D), nomes


def modo_em(A):
    """Modo oscilatorio MENOS amortecido com ωd entre 2 e 20 rad/s (o eletromecanico ou o que ele vira
    quando o PSS e a medicao o deslocam): (sigma, wd, zeta, autovalor)."""
    ev = np.linalg.eigvals(A)
    osc = [e for e in ev if 2.0 < e.imag < 20.0]
    lam = min(osc, key=lambda e: -e.real/abs(e))
    return -lam.real, lam.imag, -lam.real/abs(lam), lam


def autovalores(cfg):
    return np.linalg.eigvals(modelo(cfg)[0])


def malha_avr(cfg, w):
    """L(jw) = -ΔEfd_saida/ΔEfd_entrada (malha de tensao aberta no Efd, rotor e PSS dentro)."""
    A, B, C, D, nomes = _ss(dict(cfg, malha='fechada'))
    n = len(nomes)
    return np.array([-(C @ np.linalg.solve(1j*wi*np.eye(n) - A, B) + D) for wi in w])


def margens_avr(cfg, w=None):
    """Margem de fase (graus) no ultimo cruzamento de |L| = 1 e margem de ganho (dB) na fase -180."""
    w = np.logspace(-1.5, 2.5, 8000) if w is None else w
    L = malha_avr(cfg, w)
    mag = np.abs(L)
    fase = np.degrees(np.unwrap(np.angle(L)))
    ic = np.where(np.diff(np.sign(mag - 1.0)) != 0)[0]
    mf = wc = float('nan')
    if len(ic):
        i = ic[-1]
        wc = float(w[i]); mf = float(((fase[i] + 180.0) + 180.0) % 360.0 - 180.0)
    fr = (fase + 180.0) % 360.0 - 180.0                       # fase relativa a -180
    i1 = np.where((np.diff(np.sign(fr)) != 0) & (np.abs(fr[:-1]) < 30))[0]
    mg, w180 = float('inf'), float('nan')
    cand = [(i, mag[i]) for i in i1 if w[i] > (wc if wc == wc else 0)]
    if cand:
        i, m = cand[0]
        mg, w180 = -20*math.log10(m), float(w[i])
    return mf, wc, mg, w180


def resposta(cfg, entrada='vref', amp=None, T=6.0, dt=1e-3):
    """Resposta do modelo LINEAR em malha fechada a um degrau em Vref (amp pu) ou em Pm (amp pu).
    Retorna t, ΔVt da planta, Δ medida, Δδ. E' a previsao algebrica usada no R4 (antes de simular)."""
    from scipy.linalg import expm
    f, nomes = _equacoes(dict(cfg, malha='fechada'))
    n = len(nomes)
    amp = (P.DVREF if entrada == 'vref' else P.DPM_DEGRAU) if amp is None else amp
    kw = {entrada: 1.0}

    def lin(x, efd, u):
        s = {}
        dx, eo = f(x, efd, **({entrada: u}), saidas=s)
        return dx, eo, s
    z = np.zeros(n)
    dx0, e0, _ = lin(z, 0.0, 0.0)
    _, e1, _ = lin(z, 1.0, 0.0)
    Dl = e1 - e0
    A = np.zeros((n, n)); Ce = np.zeros(n); Cv = np.zeros(n); Cm = np.zeros(n); Cd = np.zeros(n)
    for j in range(n):
        ej = np.zeros(n); ej[j] = 1.0
        dx, eo, s = lin(ej, 0.0, 0.0)
        A[:, j] = dx; Ce[j] = eo; Cv[j] = s['vt']; Cm[j] = s['vm']; Cd[j] = s['dd']
    dxu, eu, su = lin(z, 0.0, 1.0)
    dxe, _, se = lin(z, 1.0, 0.0)
    Be = dxe                                         # efeito de Efd nas derivadas
    # efd = (Ce x + eu*u)/(1 - Dl)
    Acl = A + np.outer(Be, Ce)/(1 - Dl)
    Bcl = dxu + Be*eu/(1 - Dl)
    Phi = expm(Acl*dt)
    Gam = np.linalg.solve(Acl, (Phi - np.eye(n)) @ Bcl) if abs(np.linalg.det(Acl)) > 1e-12 else Bcl*dt
    N = int(round(T/dt))
    x = np.zeros(n); t = np.arange(N + 1)*dt
    vt = np.zeros(N + 1); vm = np.zeros(N + 1); dd = np.zeros(N + 1)
    for k in range(N + 1):
        vt[k] = Cv @ x; vm[k] = Cm @ x; dd[k] = Cd @ x
        x = Phi @ x + Gam*amp
    return t, vt, vm, dd
