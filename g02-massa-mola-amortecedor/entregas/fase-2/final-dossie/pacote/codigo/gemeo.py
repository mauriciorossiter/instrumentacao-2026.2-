# -*- coding: utf-8 -*-
"""
Gemeo numerico do sistema instrumentado - G02 (massa-mola-amortecedor), ECOM060 2026.2.

Reproduz, passo a passo (Ts = 1e-4 s), a mesma cadeia montada no TyphoonSim (modelo.tse):

  planta (RLC serie = m, c, k)  ->  y_real = v_C = k*x  [V = N = cm]
  caminho ideal : y_ideal = y_real
  caminho real  : sensor piezo (camada estatica + Thevenin Ct-Rin)  ->  ruido + interferencia
                  -> pre-amplificador G  -> demodulacao sincrona  -> Butterworth fc  -> processamento
  seletor ideal/real  ->  PID (derivada na medicao)  ->  atuador (fonte de tensao = forca)

Uso como modulo:  from gemeo import Param, simular
Uso direto     :  python gemeo.py      (imprime as metricas do ensaio padrao)
"""
import math
from dataclasses import dataclass, replace
import numpy as np

TS = 1e-4  # passo de todos os blocos de sinal [s]


@dataclass
class Param:
    # --- planta (Entrega 01) ---
    m: float = 1.0      # kg   <-> L [H]
    c: float = 6.0      # N.s/m <-> R [ohm]
    k: float = 100.0    # N/m  <-> 1/C [1/F]
    # --- ensaio ---
    ensaio: int = 1     # 1 degrau, 2 condicao inicial, 3 pulso, 4 perturbacao
    A: float = 10.0     # amplitude [cm] (malha fechada) ou [N] (malha aberta)
    t_ev: float = 2.0   # instante do evento [s]
    T: float = 5.0      # duracao [s]
    malha: int = 1      # 0 aberta, 1 fechada
    planta: int = 1     # 1 com planta; 0 = forca do gerador aplicada direto ao sensor (Fase 1)
    seletor: int = 0    # 0 ideal, 1 real
    # --- sensor piezo (Entrega 02 da Fase 1) ---
    S_nom: float = 0.04       # V/N  (400 pC/N / 10 nF)
    S_real: float = 0.0246    # V/N  (320 pC/N / 13 nF, pior caso)
    en_sens: int = 1
    en_lim: int = 1
    en_res: int = 1
    F_lim: float = 0.02       # N
    F_res: float = 0.01       # N
    Ct: float = 10e-9         # F
    Rin: float = 10e6         # ohm
    # --- condicionamento ---
    chop: int = 1             # 1 com chopagem a f_ch, 0 sem
    f_ch: float = 100.0       # Hz
    G: float = 5.0            # pre-amplificador (1 + 4k/1k)
    en_ruido: int = 1
    sigma: float = 0.02       # V (ruido branco na entrada do pre-amp)
    en_interf: int = 1
    a_off: float = 3e-3       # V (TL072)
    a_drift: float = 5e-3     # V
    f_drift: float = 0.05     # Hz
    a_hum: float = 20e-3      # V pico, 60 Hz
    fc: float = 1.0           # Hz (Butterworth 2a ordem do lock-in)
    # --- processamento e compensacao ---
    comp_cal: int = 0         # calibracao de 1 ponto
    S_cal: float = 0.0246     # sensibilidade levantada na calibracao [V/N]
    comp_din: int = 0         # correcao calculada da dinamica do filtro
    fc_corr: float = 1.0      # fc que o corretor assume [Hz] (valor nominal do filtro)
    f_f: float = 10.0         # polos rapidos do corretor [Hz] (o corretor so atua se fc < f_f)
    # --- controlador ---
    Kp: float = 2.0
    Ki: float = 10.0
    Kd: float = 0.2
    Tf: float = 0.01          # filtro da derivada [s]
    umax: float = 60.0        # saturacao do atuador [N]


def _biquad(b2, b1, b0, a2, a1, a0, ts=TS):
    """Tustin de (b2 s^2 + b1 s + b0)/(a2 s^2 + a1 s + a0). Retorna (B0,B1,B2,A1,A2) normalizados."""
    K = 2.0 / ts
    K2 = K * K
    B0 = b2 * K2 + b1 * K + b0
    B1 = 2.0 * b0 - 2.0 * b2 * K2
    B2 = b2 * K2 - b1 * K + b0
    A0 = a2 * K2 + a1 * K + a0
    A1 = 2.0 * a0 - 2.0 * a2 * K2
    A2 = a2 * K2 - a1 * K + a0
    return B0 / A0, B1 / A0, B2 / A0, A1 / A0, A2 / A0


def coef_butter(fc):
    wb = 2 * math.pi * fc
    return _biquad(0.0, 0.0, 1.0, 1.0 / wb**2, math.sqrt(2) / wb, 1.0)


def coef_corretor(fc, f_f):
    wb = 2 * math.pi * fc
    wf = 2 * math.pi * max(f_f, fc)
    return _biquad(1.0 / wb**2, math.sqrt(2) / wb, 1.0, 1.0 / wf**2, 2.0 / wf, 1.0)


class Xorshift:
    """Mesmo gerador do bloco WhiteNoise (xorshift32 + Box-Muller, semente 610839777)."""

    def __init__(self, seed=610839777):
        self.x = seed & 0xFFFFFFFF

    def _u(self):
        x = self.x
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.x = x
        return ((x >> 8) + 0.5) / 16777216.0

    def g(self):
        u1 = self._u()
        u2 = self._u()
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def gerador(p, t):
    """Referencia r [cm] (ou forca em malha aberta [N]) e perturbacao d [N]."""
    A, te = p.A, p.t_ev
    d = 0.0
    if p.ensaio == 1:      # degrau a partir do repouso
        r = A if t >= te else 0.0
    elif p.ensaio == 2:    # condicao inicial nao nula: segura em A e solta em t_ev
        r = A if t < te else 0.0
    elif p.ensaio == 3:    # transitorio temporario: regime A, pulso 1,5 A por 0,5 s
        r = 1.5 * A if te <= t < te + 0.5 else A
    else:                  # perturbacao de forca (malha fechada)
        r = A if t >= 0.5 else 0.0
        d = 0.5 * A if t >= te else 0.0
    return r, d


def simular(p: Param, dec=10):
    n = int(round(p.T / TS))
    # estados da planta (RLC: q = x [m], i = v [m/s])
    x = 0.0
    v = 0.0
    # piezo: tensao no Ct
    vct = 0.0
    # filtros
    bw = coef_butter(p.fc)
    cr = coef_corretor(p.fc_corr, p.f_f)
    zb = [0.0, 0.0]   # forma direta II transposta
    zc = [0.0, 0.0]
    # PID
    integ = 0.0
    dfilt = 0.0
    yprev = None
    rng = Xorshift()
    gn = rng.g()
    S = p.S_real if p.en_sens else p.S_nom
    Kproc = 1.0 / (p.S_nom * p.G)
    w = 2 * math.pi * p.f_ch
    out = {k: np.empty(n // dec + 1) for k in
           ("t", "r", "y_real", "y_ideal", "y_med", "y_ctrl", "u", "v_piezo", "pre_amp", "demod", "bw")}
    j = 0
    for i in range(n):
        t = i * TS
        r, d = gerador(p, t)
        y_real = p.k * x if p.planta else r   # forca na mola [N] = tensao no capacitor [V] = deslocamento [cm]
        # ---------------- sensor ----------------
        if p.chop:
            car = math.sqrt(2) * math.sin(w * t)
            F_inst = y_real * car
        else:
            car = 1.0
            F_inst = y_real
        Fa = F_inst
        if p.en_lim and abs(Fa) < p.F_lim:
            Fa = 0.0
        if p.en_res:
            Fa = p.F_res * math.floor(Fa / p.F_res + 0.5)
        vs = S * Fa
        v_piezo = vs - vct                      # tensao sobre Rin
        # ---------------- condicionamento ----------------
        e_in = v_piezo
        if p.en_ruido:
            e_in += p.sigma * gn
        if p.en_interf:
            e_in += p.a_off + p.a_drift * math.sin(2 * math.pi * p.f_drift * t) + p.a_hum * math.sin(2 * math.pi * 60 * t)
        pre = p.G * e_in
        dem = pre * car
        B0, B1, B2, A1, A2 = bw
        yb = B0 * dem + zb[0]
        zb[0] = B1 * dem - A1 * yb + zb[1]
        zb[1] = B2 * dem - A2 * yb
        # ---------------- processamento ----------------
        ym = Kproc * yb
        if p.comp_cal:
            ym *= p.S_nom / p.S_cal
        if p.comp_din:
            C0, C1, C2, D1, D2 = cr
            yc = C0 * ym + zc[0]
            zc[0] = C1 * ym - D1 * yc + zc[1]
            zc[1] = C2 * ym - D2 * yc
            ym = yc
        y_ctrl = ym if p.seletor else y_real
        # ---------------- controlador ----------------
        if p.malha:
            e = r - y_ctrl
            if yprev is None:
                yprev = y_ctrl
            dfilt += TS / p.Tf * (-p.Kd * (y_ctrl - yprev) / TS - dfilt)
            yprev = y_ctrl
            u_lin = p.Kp * e + p.Ki * integ + dfilt
            u = min(p.umax, max(-p.umax, u_lin))
            if u == u_lin or (u_lin > p.umax and e < 0) or (u_lin < -p.umax and e > 0):
                integ += e * TS               # anti-windup por integracao condicional
        else:
            u = r
        F = u + d
        if j * dec == i:
            for kk, vv in (("t", t), ("r", r), ("y_real", y_real), ("y_ideal", y_real), ("y_med", ym),
                           ("y_ctrl", y_ctrl), ("u", u), ("v_piezo", v_piezo), ("pre_amp", pre),
                           ("demod", dem), ("bw", yb)):
                out[kk][j] = vv
            j += 1
        # ---------------- atualizacao dos estados ----------------
        # planta (Euler semi-implicito, passo 1e-4 << 1/wn)
        a = (F - p.c * v - p.k * x) / p.m
        v += a * TS
        x += v * TS
        # piezo: Ct carregado pela corrente em Rin
        vct += (v_piezo / p.Rin) / p.Ct * TS
        gn = rng.g()
    return {k: vv[:j] for k, vv in out.items()}


def metricas(res, p: Param, sinal="y_real"):
    """Erro de regime, acomodacao 2 %, sobressinal e esforco para o degrau (ensaio 1)."""
    t = res["t"]
    y = res[sinal]
    u = res["u"]
    A = p.A
    msk = t >= p.t_ev
    tt, yy = t[msk] - p.t_ev, y[msk]
    fim = tt >= tt[-1] - 0.5
    yinf = float(np.mean(yy[fim]))
    ess = (yinf - A) / A * 100.0
    os_ = max(0.0, (yy.max() - A) / A * 100.0)
    fora = np.where(np.abs(yy - A) > 0.02 * A)[0]
    ts = float(tt[fora[-1]]) if len(fora) else 0.0
    if len(fora) and fora[-1] >= len(tt) - 2:
        ts = float("inf")
    umax = float(np.max(np.abs(u[msk])))
    u_rms_ripple = float(np.std(u[msk][fim]))
    return dict(ess=ess, ts=ts, os=os_, umax=umax, u_rip=u_rms_ripple, yinf=yinf)


CRIT = dict(ess=2.0, ts=1.0, os=10.0, umax=30.0, u_rip=1.0)


def atende(mt):
    return (abs(mt["ess"]) <= CRIT["ess"] and mt["ts"] <= CRIT["ts"] and mt["os"] <= CRIT["os"]
            and mt["umax"] <= CRIT["umax"] and mt["u_rip"] <= CRIT["u_rip"])


if __name__ == "__main__":
    import time
    for sel, extra in ((0, {}), (1, {}), (1, dict(comp_cal=1)), (1, dict(comp_cal=1, comp_din=1))):
        p = replace(Param(), seletor=sel, **extra)
        t0 = time.time()
        r = simular(p)
        print(sel, extra, {k: round(v, 3) for k, v in metricas(r, p).items()}, f"{time.time()-t0:.1f}s")
