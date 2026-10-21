"""
G07 - ECOM060 - Fase 2 / Entrega 01
Modelo do motor BLDC MOONS' R42BLD30L3 + carga quadratica.

Dois modelos:
  (1) medio (reduzido): x = [i, w, theta_e], comutacao seis-passos ideal
  (2) chaveado trifasico: correntes de fase, FCEM trapezoidal, Hall, PWM 10 kHz
      no lado baixo (mesma logica do .tse), diodos de roda-livre.

Modulo importado pelos scripts ensaios.py, malha_fechada.py, sens_trifasico.py e typhoon_cmp.py.
Requer: Python >= 3.10, numpy, scipy, matplotlib.
"""
import numpy as np
from math import pi, sqrt, exp, log, cos, sin, atan2

# ---------------- parametros (Tab. 1 do relatorio) ----------------
P = dict(
    Vs=36.0,            # V      tensao nominal [dossie = fabricante]
    RLL=3.2,            # ohm    2 x R de fase 1,60 ohm [dossie]
    LLL=3.8e-3,         # H      2 x L de fase 1,90 mH (Ls = L - M) [dossie]
    k=0.048,            # N.m/A = V.s/rad  kt = ke [dossie = fabricante]
    J=3.3e-6,           # kg.m2  inercia do rotor [dossie]
    B=1e-6,             # N.m.s/rad atrito viscoso [hipotese]
    b2=5e-9,            # N.m/rpm^2  carga T = b2 n^2 (0,08 N.m a 4000 rpm)
    p=4,                # pares de polos
    fpwm=10e3,          # Hz
)
RPM = 60 / (2 * pi)


def c_of(P):          # coef. da carga em N.m/(rad/s)^2
    return P['b2'] * RPM**2


# ---------------- analise algebrica ----------------
def equilibrio(P, d, Td=0.0):
    """ponto de equilibrio do modelo medio (conducao continua)."""
    R, k, B, c, V = P['RLL'], P['k'], P['B'], c_of(P), P['Vs']
    # c w^2 + (B + k^2/R) w + Td - k d V / R = 0
    a2, a1, a0 = c, B + k * k / R, Td - k * d * V / R
    w = (-a1 + sqrt(a1 * a1 - 4 * a2 * a0)) / (2 * a2) if a2 > 0 else -a0 / a1
    i = (B * w + c * w * w + Td) / k
    return w, i


def linear(P, w0):
    R, L, k, B, J, V = P['RLL'], P['LLL'], P['k'], P['B'], P['J'], P['Vs']
    Beff = B + 2 * c_of(P) * w0
    A = np.array([[-R / L, -k / L], [k / J, -Beff / J]])
    lam = np.linalg.eigvals(A)
    wn = sqrt((R * Beff + k * k) / (L * J))
    zeta = (R / L + Beff / J) / (2 * wn)
    G = k * V / (R * Beff + k * k)           # (rad/s) por unidade de d
    Gd = -R / (R * Beff + k * k)             # (rad/s) por N.m de perturbacao
    out = dict(Beff=Beff, lam=lam, wn=wn, zeta=zeta, G=G, Gd=Gd,
               tau_e=L / R, tau_m=J * R / (k * k + R * Beff))
    if zeta < 1:
        wd = wn * sqrt(1 - zeta**2)
        out.update(wd=wd, Mp=exp(-pi * zeta / sqrt(1 - zeta**2)), tp=pi / wd)
    out['ts2'] = 4 / (zeta * wn) if zeta < 1 else 4 / min(abs(lam.real))
    return out


def step2nd(t, wn, zeta, K):
    """resposta exata ao degrau de K*wn^2/(s^2+2 zeta wn s+wn^2)."""
    if zeta < 1:
        wd = wn * sqrt(1 - zeta**2)
        return K * (1 - np.exp(-zeta * wn * t) * (np.cos(wd * t) + zeta / sqrt(1 - zeta**2) * np.sin(wd * t)))
    s1 = -zeta * wn + wn * sqrt(zeta**2 - 1)
    s2 = -zeta * wn - wn * sqrt(zeta**2 - 1)
    return K * (1 + (s2 * np.exp(s1 * t) - s1 * np.exp(s2 * t)) / (s1 - s2))


def coastdown(t, w0, P):
    """solucao exata de J dw/dt = -B w - c w^2 (i = 0)."""
    a = P['B'] / P['J']; cc = c_of(P) / P['J']
    if a == 0:
        return w0 / (1 + cc * w0 * t)
    e = np.exp(-a * t)
    return a * w0 * e / (a + cc * w0 * (1 - e))


# ---------------- modelo medio ----------------
def rhs_avg(t, x, P, dfun, Tdfun):
    i, w, th = x
    R, L, k, B, J, V, p = P['RLL'], P['LLL'], P['k'], P['B'], P['J'], P['Vs'], P['p']
    c = c_of(P)
    v = dfun(t) * V
    di = (v - R * i - k * w) / L
    if P.get('clamp', True) and i <= 0.0 and di < 0.0:        # conducao descontinua: inversor nao regenera
        di = 0.0; i = 0.0
    dw = (k * i - B * w - c * w * abs(w) - Tdfun(t)) / J
    return [di, dw, p * w]


def sim_avg(P, tf, x0, dfun, Tdfun=lambda t: 0.0, method='DOP853', rtol=1e-12, atol=1e-12, max_step=1e-4, t_eval=None):
    from scipy.integrate import solve_ivp
    if t_eval is None:
        t_eval = np.linspace(0, tf, 20001)
    s = solve_ivp(rhs_avg, (0, tf), x0, method=method, args=(P, dfun, Tdfun),
                  rtol=rtol, atol=atol, max_step=max_step, t_eval=t_eval)
    x = s.y.copy()
    if P.get('clamp', True): x[0] = np.maximum(x[0], 0)
    return s.t, x


def rk4_avg(P, tf, x0, dfun, dt=2e-6, Tdfun=lambda t: 0.0):
    n = int(round(tf / dt)); X = np.zeros((3, n + 1)); X[:, 0] = x0
    x = np.array(x0, float); t = 0.0
    f = lambda t, x: np.array(rhs_avg(t, x, P, dfun, Tdfun))
    for j in range(n):
        k1 = f(t, x); k2 = f(t + dt / 2, x + dt / 2 * k1)
        k3 = f(t + dt / 2, x + dt / 2 * k2); k4 = f(t + dt, x + dt * k3)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        if P.get('clamp', True): x[0] = max(x[0], 0.0)
        t += dt; X[:, j + 1] = x
    return np.linspace(0, n * dt, n + 1), X


# ---------------- modelo chaveado trifasico ----------------
def ftrap(th):
    """forma normalizada da FCEM de fase (trapezio, topo plano de 120 graus)."""
    d = (th % (2 * pi)) * 180 / pi
    if d < 30: return d / 30
    if d < 150: return 1.0
    if d < 210: return (180 - d) / 30
    if d < 330: return -1.0
    return (d - 360) / 30


# tabela de comutacao do .tse (Hall A,B,C) -> (top a,b,c), (bot a,b,c)
TAB = {(1, 0, 0): ((1, 0, 0), (0, 0, 1)), (1, 0, 1): ((1, 0, 0), (0, 1, 0)),
       (1, 1, 0): ((0, 1, 0), (0, 0, 1)), (0, 1, 0): ((0, 1, 0), (1, 0, 0)),
       (0, 1, 1): ((0, 0, 1), (1, 0, 0)), (0, 0, 1): ((0, 0, 1), (0, 1, 0))}


def hall(te):
    hA = int(pi / 6 <= te <= 7 * pi / 6)
    hB = int(5 * pi / 6 <= te <= 11 * pi / 6)
    hC = int(te >= 3 * pi / 2 or te <= pi / 2)
    return hA, hB, hC


def sim_sw(P, tf, w0, dfun, Tdfun=lambda t: 0.0, dt=0.25e-6, dec=40, Th=None, nd=0, ctrl=None, Tq=None):
    R = P['RLL'] / 2; L = P['LLL'] / 2; kph = P['k'] / 2
    V, J, B, c, p, fp = P['Vs'], P['J'], P['B'], c_of(P), P['p'], P['fpwm']
    n = int(round(tf / dt)); m = n // dec + 1
    T = np.zeros(m); W = np.zeros(m); I = np.zeros((3, m)); TE = np.zeros(m); PIN = np.zeros(m)
    i = [0.0, 0.0, 0.0]; w = w0; thm = 0.0; t = 0.0; idc_acc = 0.0; te_acc = 0.0
    sh = (0.0, 2 * pi / 3, 4 * pi / 3)
    nh = None if Th is None else max(1, int(round(Th / dt)))
    hbuf = [hall(0.0)] * (nd + 1)
    for j in range(n + 1):
        te = (p * thm) % (2 * pi)
        if nh is None:
            top, bot = TAB[hall(te)]
        else:
            if j % nh == 0:
                hbuf = hbuf[1:] + [hall(te)]
            top, bot = TAB[hbuf[0]]
        tc = t if Tq is None else Tq * int(t / Tq + 1e-9)   # comparador/portadora amostrados (Typhoon: Ts = 5 us)
        car = (tc * fp) % 1.0; car = 2 * car if car < 0.5 else 2 - 2 * car
        dcur = ctrl(t, w, i, hbuf[0] if nh is not None else hall(te)) if ctrl is not None else dfun(tc)
        pwm = 1 if dcur > car else 0
        f = [ftrap(te - s) for s in sh]
        e = [kph * w * fk for fk in f]
        # tensoes de terminal
        v = [None, None, None]
        for q in range(3):
            if top[q]: v[q] = V
            elif bot[q] and pwm: v[q] = 0.0
            elif i[q] > 1e-9: v[q] = 0.0          # diodo inferior
            elif i[q] < -1e-9: v[q] = V           # diodo superior
        for _ in range(3):
            D = [q for q in range(3) if v[q] is not None]
            if len(D) >= 2:
                vn = sum(v[q] - R * i[q] - e[q] for q in D) / len(D)
            elif len(D) == 1:
                vn = v[D[0]] - e[D[0]]
            else:
                vn = 0.0
            chg = False
            for q in range(3):
                if v[q] is None:
                    vt = vn + e[q]
                    if vt > V: v[q] = V; chg = True
                    elif vt < 0: v[q] = 0.0; chg = True
            if not chg: break
        D = [q for q in range(3) if v[q] is not None]
        di = [0.0, 0.0, 0.0]
        if len(D) >= 2:
            for q in D:
                di[q] = (v[q] - vn - R * i[q] - e[q]) / L
        Te = kph * (f[0] * i[0] + f[1] * i[1] + f[2] * i[2])
        pin = sum(v[q] * i[q] for q in D) if len(D) >= 2 else 0.0
        if j % dec == 0:
            k_ = j // dec
            T[k_] = t; W[k_] = w; I[:, k_] = i; TE[k_] = Te; PIN[k_] = pin if ctrl is None else dcur
        # integracao (Euler explicito, dt = 0,25 us)
        inew = [i[q] + dt * di[q] for q in range(3)]
        for q in range(3):   # diodo bloqueia ao cruzar zero
            switched = top[q] or (bot[q] and pwm)
            if not switched and i[q] != 0 and inew[q] * i[q] < 0:
                inew[q] = 0.0
        if len(D) >= 2:
            s = sum(inew) / len(D)
            for q in D: inew[q] -= s
        i = inew
        dw = (Te - B * w - c * w * abs(w) - Tdfun(t)) / J
        w += dt * dw; thm += dt * w; t += dt
    return T, W, I, TE, PIN


def metrics(t, y, yss=None, t0=0.0):
    m = t >= t0; t = t[m] - t0; y = y[m]
    y0 = y[0]; yss = y[-1] if yss is None else yss
    dy = yss - y0
    yn = (y - y0) / dy
    def cross(lv):
        idx = np.argmax(yn >= lv);
        if idx == 0: return np.nan
        return t[idx - 1] + (lv - yn[idx - 1]) / (yn[idx] - yn[idx - 1]) * (t[idx] - t[idx - 1])
    tr = cross(0.9) - cross(0.1)
    out = np.where(np.abs(yn - 1) > 0.02)[0]
    ts = t[out[-1] + 1] if len(out) and out[-1] + 1 < len(t) else np.nan
    ip = np.argmax(yn); Mp = max(yn[ip] - 1, 0)
    return dict(tr=tr, ts=ts, Mp=Mp, tp=t[ip], yss=yss, t10=cross(0.1), t90=cross(0.9))


class MalhaTSE:
    """Reproduz o subsistema Regulators do .tse: prefiltro 1/(0,004 s+1) sobre 5,05*Throttle,
    PI de velocidade (kp 0,042, ki 10,5, sat 0..5 A) a 50 us, PI de corrente (kp 0,72, ki 460, sat 0..1)
    a 25 us, corrente realimentada = fase alimentada pelo lado alto (C function 'Current sampling')."""
    def __init__(s, throttle=82.9, Ts=5e-6, kps=0.042, kis=10.5, kpi=0.72, kii=460.0, imax=5.0):
        s.r = 5.05 * throttle; s.Tw = 10 * Ts; s.Ti = 5 * Ts
        s.kps, s.kis, s.kpi, s.kii, s.imax = kps, kis, kpi, kii, imax
        s.yf = 0.0; s.Is = 0.0; s.iref = 0.0; s.Ii = 0.0; s.d = 0.0; s.Imeas = 0.0
        s.nw = -1; s.ni = -1
    def __call__(s, t, w, i, h):
        kw = int(t / s.Tw)
        if kw != s.nw:
            s.nw = kw
            s.yf += s.Tw / 0.004 * (s.r - s.yf)
            e = s.yf - w
            u = s.kps * e + s.Is
            if 0.0 < u < s.imax or (u >= s.imax and e < 0) or (u <= 0 and e > 0):
                s.Is += s.kis * s.Tw * e
            s.iref = min(max(s.kps * e + s.Is, 0.0), s.imax)
        ki_ = int(t / s.Ti)
        if ki_ != s.ni:
            s.ni = ki_
            hA, hB, hC = h
            m = {(1,0,0): i[0], (1,0,1): -i[1], (1,1,0): -i[2], (0,1,0): i[1], (0,1,1): -i[0], (0,0,1): i[2]}
            s.Imeas = m.get((hA, hB, hC), s.Imeas)
            e = s.iref - s.Imeas
            u = s.kpi * e + s.Ii
            if 0.0 < u < 1.0 or (u >= 1.0 and e < 0) or (u <= 0 and e > 0):
                s.Ii += s.kii * s.Ti * e
            s.d = min(max(s.kpi * e + s.Ii, 0.0), 1.0)
        return s.d
