# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E03 e E04: simulacao no tempo de planta + medicao (ideal e real) + controle.

Tudo e' escrito como equacoes a diferencas, na mesma ordem e com os mesmos coeficientes dos blocos nativos
do TyphoonSim (typhoonsim/monta_modelo.py). Duas taxas, como no modelo:
  * planta (circuito da E02): R-L-C exato entre amostras (ZOH) + fonte controlada a cada 20 us;
  * medicao e controle: a cada TS_M = 100 us (ADC a 10 kS/s).

Planta:      E02 com Pmax(t) = E'(t)*V/X*(1 - falta). Na E03 (malha aberta) E' = 1,2 pu constante.
Terminais:   Vt = (X'd*Vth + Xth*E'∠δ)/(X'd + Xth); normal (Vth, Xth) = (V, Xe), falta (0, XT).
Forma de onda no primario do TP (tensao de linha): v_p = √2*V_BASE*|Vt|*cos(ωs*t + θt).

Medicao IDEAL (ganho unitario, sem atraso, sem ruido): V_id = |Vt|; f_id = 60 + Δθt/(2π*TS_M).
Medicao REAL (cada caracteristica num bloco; valor 0 desliga):
  tensao:     TP (1 + eps_tp) -> divisor (2 V/pu) -> + ruido (sigma) -> AD637 implicito: Vo = media(x²/Vo),
              media de 1a ordem (tau_rms) -> Sallen-Key 10 Hz -> ADC (nbits, 0-4,096 V) -> pu
  frequencia: mesmo sinal com ruido -> pre-filtro 150 Hz -> comparador com histerese (±20 mV)
              -> periodo entre bordas de subida, com interpolacao linear da passagem -> quantizacao no relogio
              do contador (fclk) -> 1/T -> media exponencial de n_cic ciclos
Controle (E04): PI de tensao (AVR) -> Efd com limites e anti-windup por grampeamento do integrador;
              PSS sobre a frequencia: lavagem + 2 avanco-atraso + ganho + limite, somado a Vref.
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import parametros_e34 as P          # noqa: E402
import circuito as C2               # noqa: E402  (E02: discretiza)
import controle as K                # noqa: E402

DOIS_PI = 2.0*math.pi
RAIZ2 = math.sqrt(2.0)


def biquad_pb(fc, Ts=P.TS_M):
    """Passa-baixas 2a ordem Butterworth digital (bilinear com pre-distorcao), como no TyphoonSim."""
    from scipy.signal import butter
    b, a = butter(2, fc, btype='low', fs=1.0/Ts)
    return [float(v) for v in b], [float(v) for v in a]


def biquad_pf(f0, bw, Ts=P.TS_M):
    """Passa-faixa 2a ordem Butterworth digital centrado em f0 com banda bw (Hz)."""
    from scipy.signal import butter
    b, a = butter(1, [f0 - bw/2.0, f0 + bw/2.0], btype='band', fs=1.0/Ts)
    return [float(v) for v in b], [float(v) for v in a]


B_SK, A_SK = biquad_pb(P.FC_SK)
B_PF, A_PF = biquad_pb(P.FC_PF)


def estado_biquad_senoide(b, a, amp, fase, w, Ts):
    """Estados (x[-1], x[-2], y[-1], y[-2]) do regime senoidal de entrada amp*cos(w t + fase)."""
    z = np.exp(1j*w*Ts)
    Hz = (b[0] + b[1]/z + b[2]/z**2)/(a[0] + a[1]/z + a[2]/z**2)
    xm = [amp*math.cos(w*(-k*Ts) + fase) for k in (1, 2)]
    ym = [abs(Hz)*amp*math.cos(w*(-k*Ts) + fase + np.angle(Hz)) for k in (1, 2)]
    return xm[0], xm[1], ym[0], ym[1]


# ============================================================================ ensaios
def ensaio(nome, T=None):
    """Roteiro de eventos de cada ensaio. Retorna dict(delta0, T, pm(t), vref_deg(t), falta(t))."""
    ev = P.T_EV
    d = dict(nome=nome, delta0=P.DELTA0, pm=lambda t: P.PM0, dvref=lambda t: 0.0, falta=lambda t: 0.0)
    if nome == 'a':                                             # degrau de Pm (E01/E02)
        d.update(T=T or 21.0, pm=lambda t: P.PM0 + (P.DPM_DEGRAU if t >= ev else 0.0))
    elif nome == 'b':                                           # condicao inicial delta(0) = 60 graus
        d.update(T=T or 10.0, delta0=math.radians(P.DELTA_CI_GR))
    elif nome == 'c':                                           # falta franca de 200 ms
        d.update(T=T or 6.0, falta=lambda t: 1.0 if ev <= t < ev + P.DUR_FALTA else 0.0)
    elif nome == 'r':                                           # E04: degrau de referencia de tensao
        d.update(T=T or 6.0, dvref=lambda t: P.DVREF if t >= ev else 0.0)
    elif nome == 'p':                                           # E04: perturbacao = degrau de Pm
        d.update(T=T or 11.0, pm=lambda t: P.PM0 + (P.DPM_DEGRAU if t >= ev else 0.0))
    elif nome == 'f':                                           # E04: falta franca de 200 ms em malha fechada
        d.update(T=T or 8.0, falta=lambda t: 1.0 if ev <= t < ev + P.DUR_FALTA else 0.0)
    elif nome == 'banco_v':                                     # bancada: degrau de amplitude 1,00 -> 1,10 pu
        d.update(T=T or 1.5, banco=lambda t: (1.0 if t < 0.5 else 1.1, 0.0))
    elif nome == 'banco_f':                                     # bancada: degrau de frequencia 60,0 -> 60,1 Hz
        d.update(T=T or 1.5, banco=lambda t: (1.0, 0.0 if t < 0.5 else 2*math.pi*0.1*(t - 0.5)))
    elif nome == 'banco_0':                                     # bancada: 1 pu, 60 Hz (piso de ruido/resolucao)
        d.update(T=T or 3.0, banco=lambda t: (1.0, 0.0))
    else:
        raise ValueError(nome)
    return d


def cfg_padrao(**kw):
    c = dict(P.REAL)                    # caracteristicas da cadeia real
    c.update(malha='aberta', fb_v='ideal', fb_f='ideal', pss=False,
             kp=K.KP, ki=K.KI, kpss=K.KPSS, pss_coef=K.PSS_Z, vst=K.VST_MAX,
             vref=P.VT0, semente=P.SEMENTE, decim=10, pf_bw=0.0)
    c.update(kw)
    return c


def equilibrio(cfg, Pm=P.PM0):
    """Regime em malha fechada: Pe = Pm e a tensao MEDIDA igual a Vref. Com o TP lendo (1 + eps) a mais,
    a tensao real fica em Vref/(1 + eps). Retorna (delta, E') (bissecao em delta)."""
    eps = cfg['eps_tp']/100.0 if cfg['fb_v'] == 'real' else 0.0
    alvo = cfg['vref']/(1.0 + eps)

    def vt(d):
        Ep = Pm*P.X_TOT/(P.V_BAR*math.sin(d))
        re, im = P.terminal(d, Ep)
        return math.hypot(re, im) - alvo, Ep
    a, b = 0.2, 1.2                       # |Vt| cai com delta nesse trecho (E' = Pm X / sen d)
    for _ in range(80):
        m = 0.5*(a + b)
        if vt(a)[0]*vt(m)[0] <= 0:
            b = m
        else:
            a = m
    d = 0.5*(a + b)
    return d, vt(d)[1]


def estado_inicial(ens, cfg):
    """Estados iniciais de todos os blocos com memoria (os mesmos 'init' que roda_typhoon.py grava no .tse)."""
    d_ini, Ep = ens['delta0'], P.E_LINHA
    if cfg['malha'] == 'fechada' and ens['delta0'] == P.DELTA0:
        d_ini, Ep = equilibrio(cfg)
    falta0 = ens['falta'](0.0)
    if ens.get('banco') is None:
        vre, vim = P.terminal(d_ini, Ep, falta0)
        Vt = math.hypot(vre, vim); th = math.atan2(vim, vre)
    else:
        Vt, th = ens['banco'](0.0)
    kvd = RAIZ2*P.V_PU_VD*(1.0 + cfg['eps_tp']/100.0)
    amp0 = kvd*Vt
    u0 = math.sqrt(0.5*amp0*amp0 + cfg['sigma']**2)
    pf = {}
    for nome, (b, a) in (('pb', (B_PF, A_PF)), ('pf', biquad_pf(P.F_REDE, 10.0))):
        pf[nome] = estado_biquad_senoide(b, a, amp0, th, P.W_S, P.TS_M)
    usa = 'pf' if cfg.get('pf_bw', 0) > 0 else 'pb'
    return dict(vC0=(d_ini - P.DELTA0)*P.KV_DELTA, delta0=d_ini, Ep0=Ep, xI0=Ep, Vt0=Vt, th0=th, u0=u0,
                pf=pf, hist_alto=pf[usa][2] > 0, yant=pf[usa][2])


# ============================================================================ simulacao
def simula(ens, cfg):
    """Roda um ensaio. cfg: ver cfg_padrao. Retorna dict de arrays decimados (1 ms) e metadados."""
    Ts, Tp, nsub = P.TS_M, P.TS_SP, P.N_SUB
    T = ens['T']
    n = int(round(T/Ts))
    dec = cfg['decim']

    # ---- planta (E02): matrizes ZOH do R-L-C para o passo de 20 us
    R = P.KV*P.D/P.KI
    Phi, Gam = C2.discretiza(R, P.L_EQ, P.C_EQ, Tp)
    p00, p01, p10, p11 = (float(Phi[0, 0]), float(Phi[0, 1]), float(Phi[1, 0]), float(Phi[1, 1]))
    g0, g1 = float(Gam[0]), float(Gam[1])
    KV, KVD, D0, KI = P.KV, P.KV_DELTA, P.DELTA0, P.KI
    i_L = 0.0
    d_ini, Ep = ens['delta0'], P.E_LINHA
    if cfg['malha'] == 'fechada' and ens['delta0'] == P.DELTA0:
        d_ini, Ep = equilibrio(cfg)            # regime que a malha impoe com esta medicao (erro do TP)
    vC = (d_ini - D0)*KVD
    ezf = math.exp(-Ts/P.TDO)                  # campo: E' exato entre amostras (Efd constante na amostra)
    Efd = Ep

    # ---- caracteristicas da cadeia real
    eps = cfg['eps_tp']/100.0
    tau = cfg['tau_rms']
    a1 = 1.0 - math.exp(-Ts/tau) if tau > 0 else 1.0
    nb = int(cfg['nbits'])
    lsb = P.VREF_ADC/2**nb if nb > 0 else 0.0
    cmax = 2**nb - 1
    sig = cfg['sigma']
    ncic = cfg['n_cic']
    fclk = cfg['fclk']
    kvd = RAIZ2*P.V_PU_VD*(1.0 + eps)          # V de pico na entrada do condicionamento por pu de |Vt|
    rng = np.random.default_rng(cfg['semente'])
    ruido = (sig*rng.standard_normal(n + 1)).tolist() if sig > 0 else None

    # ---- estado inicial (regime no ponto inicial: filtros ja assentados, como os 'init' do TyphoonSim)
    falta0 = ens['falta'](0.0)
    banco = ens.get('banco')                   # ensaio de bancada: forma de onda sintetica no primario do TP
    if banco is None:
        vre, vim = P.terminal(d_ini, Ep, falta0)
        Vt = math.hypot(vre, vim); th = math.atan2(vim, vre)
    else:
        Vt, th = banco(0.0)
    th_ant = th
    amp0 = kvd*Vt
    u = math.sqrt(0.5*amp0*amp0 + sig*sig)     # AD637: saida em regime = valor eficaz de x
    r0 = u
    sx1 = sx2 = sy1 = sy2 = r0                 # Sallen-Key (ganho DC 1)
    bs0, bs1, bs2 = B_SK; as1, as2 = A_SK[1], A_SK[2]
    bpf, apf = (B_PF, A_PF) if cfg.get('pf_bw', 0) <= 0 else biquad_pf(P.F_REDE, cfg['pf_bw'])
    bp0, bp1, bp2 = bpf; ap1, ap2 = apf[1], apf[2]
    px1, px2, py1, py2 = estado_biquad_senoide(bpf, apf, amp0, th, P.W_S, Ts)
    hst = 1.0 if py1 > 0 else 0.0              # estado do comparador
    yant = py1
    q_ult = 0.0; porta = 0.0
    F = P.F_REDE
    h = P.HIST

    # ---- controle
    fechada = cfg['malha'] == 'fechada'
    kp, ki = cfg['kp'], cfg['ki']
    xI = Ep                                    # integrador do PI carrega o Efd de regime
    vref0 = cfg['vref']
    usa_pss = cfg['pss'] and fechada
    kpss, vst = cfg['kpss'], cfg['vst']
    # PSS: tres secoes de 1a ordem (lavagem, avanco 1, avanco 2), Tustin: y = b0 x + b1 x1 - a1 y1
    sec = [list(s) for s in cfg['pss_coef']]
    ps_x = [0.0, 0.0, 0.0]; ps_y = [0.0, 0.0, 0.0]
    upss = 0.0
    fb_v_real = cfg['fb_v'] == 'real'
    fb_f_real = cfg['fb_f'] == 'real'

    pm_f, dvref_f, falta_f = ens['pm'], ens['dvref'], ens['falta']
    rec = {k: [] for k in ('t', 'delta', 'dw', 'Ep', 'Efd', 'Pm', 'Pe', 'Vref', 'falta', 'V_id', 'V_re', 'f_id',
                           'f_re', 'upss', 'x_vd')}
    sw = P.W_S
    for k in range(n + 1):
        t = k*Ts
        Pm = pm_f(t); fl = falta_f(t); vref = vref0 + dvref_f(t)
        # ------------------------------------------------ tensao terminal e medicao ideal
        delta = D0 + vC/KVD
        if banco is None:
            vre, vim = P.terminal(delta, Ep, fl)
            Vt = math.hypot(vre, vim); th = math.atan2(vim, vre)
        else:
            Vt, th = banco(t)
        dth = th - th_ant
        dth -= DOIS_PI*round(dth/DOIS_PI)
        f_id = P.F_REDE + dth/(DOIS_PI*Ts)
        th_ant = th
        V_id = Vt
        # ------------------------------------------------ forma de onda no condicionamento (+ ruido)
        tm = t - math.floor(t)                         # relogio com reinicio a cada 1 s (60 ciclos inteiros)
        x = kvd*Vt*math.cos(sw*tm + th)
        if ruido is not None:
            x += ruido[k]
        # ------------------------------------------------ tensao: AD637 + Sallen-Key + ADC
        if tau > 0:
            # AD637, calculo implicito: Vo <- Vo + a1*(x²/Vo - Vo)   (divisor protegido em 1 mV)
            u += a1*(x*x/(u if u > 1e-3 else 1e-3) - u)
            r = u
            s = bs0*r + bs1*sx1 + bs2*sx2 - as1*sy1 - as2*sy2
            sx2, sx1, sy2, sy1 = sx1, r, sy1, s
        else:
            s = kvd*Vt/RAIZ2                           # dinamica desligada: valor eficaz exato do sinal
        if nb > 0:
            cod = round(s/lsb)
            cod = 0 if cod < 0 else (cmax if cod > cmax else cod)
            s = cod*lsb
        V_re = s/P.V_PU_VD
        # ------------------------------------------------ frequencia: pre-filtro + comparador + periodo
        if ncic > 0:
            y = bp0*x + bp1*px1 + bp2*px2 - ap1*py1 - ap2*py2
            px2, px1, py2, py1 = px1, x, py1, y
            hn = 1.0 if y > h else (0.0 if y < -h else hst)
            borda = hn*(1.0 - hst)
            if borda:
                fi = (y - h)/(y - yant) if y != yant else 0.0
                tc = tm - fi*Ts                          # instante da passagem (relogio de 1 s)
                q = math.floor(tc*fclk)/fclk if fclk > 0 else tc     # captura do temporizador
                if porta >= 1.0:
                    Tper = q - q_ult
                    if Tper < 0.0:
                        Tper += 1.0                      # o relogio reiniciou entre as duas bordas
                    F += (1.0/Tper - F)/ncic
                porta = 2.0 if porta >= 1.0 else 1.0
                q_ult = q
            hst = hn
            yant = y
            f_re = F
        else:
            f_re = f_id
        # ------------------------------------------------ controle
        if fechada:
            Vfb = V_re if fb_v_real else V_id
            if usa_pss:
                ffb = f_re if fb_f_real else f_id
                xin = (ffb - P.F_REDE)/P.F_REDE              # pu de frequencia
                for j in range(3):
                    b0, b1, aa1 = sec[j]
                    yj = b0*xin + b1*ps_x[j] - aa1*ps_y[j]
                    ps_x[j] = xin; ps_y[j] = yj
                    xin = yj
                upss = kpss*xin
                upss = vst if upss > vst else (-vst if upss < -vst else upss)
            e = vref + upss - Vfb
            Efd = kp*e + xI
            Efd = P.EFD_MAX if Efd > P.EFD_MAX else (P.EFD_MIN if Efd < P.EFD_MIN else Efd)
            xI += ki*Ts*e
            xI = P.EFD_MAX if xI > P.EFD_MAX else (P.EFD_MIN if xI < P.EFD_MIN else xI)
        # ------------------------------------------------ registro (antes de avancar a planta)
        if k % dec == 0:
            rec['t'].append(t); rec['delta'].append(delta); rec['dw'].append(i_L/KI); rec['Ep'].append(Ep)
            rec['Efd'].append(Efd); rec['Pm'].append(Pm)
            rec['Pe'].append(Ep*P.V_BAR/P.X_TOT*(1.0 - fl)*math.sin(delta))
            rec['Vref'].append(vref + upss); rec['falta'].append(fl)
            rec['V_id'].append(V_id); rec['V_re'].append(V_re); rec['f_id'].append(f_id); rec['f_re'].append(f_re)
            rec['upss'].append(upss); rec['x_vd'].append(x)
        if k == n:
            break
        # ------------------------------------------------ campo (E' exato com Efd constante na amostra)
        if fechada:
            Ep = Efd + (Ep - Efd)*ezf
        # ------------------------------------------------ planta: 5 subpassos de 20 us (E02)
        vm = KV*Pm
        pmax = Ep*P.V_BAR/P.X_TOT*(1.0 - fl)
        for _ in range(nsub):
            vnl = KV*pmax*math.sin(D0 + vC/KVD) - vC
            uu = vm - vnl
            i_L, vC = p00*i_L + p01*vC + g0*uu, p10*i_L + p11*vC + g1*uu
    out = {k: np.array(v) for k, v in rec.items()}
    out['cfg'] = cfg
    out['ens'] = ens['nome']
    return out
