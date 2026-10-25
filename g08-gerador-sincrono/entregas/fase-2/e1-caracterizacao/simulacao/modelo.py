# -*- coding: utf-8 -*-
"""
Modelo, solucionador e analise algebrica da swing equation (SMIB, modelo classico).
Definicao unica usada por caracterizacao.py. Depende so de math e numpy.

Estados: x1 = delta [rad] (angulo do rotor em relacao a referencia sincrona)
         x2 = Delta_omega = d(delta)/dt [rad/s eletricos]
    dx1/dt = x2
    dx2/dt = (ws/2H) * (Pm - Pmax*sin(x1) - D*x2)

Invariante de energia (referencia algebrica do sistema nao linear):
    W(delta, omega) = (H/ws)*omega^2 + V(delta),   V(delta) = -Pm*delta - Pmax*cos(delta)
    dW/dt = -D*omega^2   (W e' constante se D = 0)
"""
import math
import cmath
import numpy as np

from parametros import W_S, H, D, PM0, P_MAX, PASSO, E_LINHA, V_BAR, X_TOT


# =============================================================== solucionador
def seg(duracao, Pm=PM0, Pmax=P_MAX, H=H, D=D):
    """Trecho de simulacao com parametros constantes: (duracao, Pm, Pmax, H, D)."""
    return (float(duracao), float(Pm), float(Pmax), float(H), float(D))


def simula(segmentos, delta0, omega0=0.0, passo=PASSO, delta_lim=None, registrar=True):
    """Integra a swing equation com Runge-Kutta classico de 4a ordem, passo fixo.

    Cada trecho usa n = ceil(T/passo) passos de tamanho T/n <= passo, de modo que os
    instantes de chaveamento (aplicacao e eliminacao da falta) caem exatamente na grade.
    O estado e' aumentado com Ed = integral de D*omega^2 dt (energia dissipada), integrada
    pelo mesmo RK4, para o balanco de energia W(t) - W(0) + Ed(t) = 0.
    delta_lim: interrompe se delta ultrapassar esse valor (perda de sincronismo).
    """
    t, d, w, e = 0.0, float(delta0), float(omega0), 0.0
    T_, Dl, Wl, Pel, El, Pml = [], [], [], [], [], []
    perdeu = False
    sen = math.sin
    for (dur, Pm, Pmax, Hh, Dd) in segmentos:
        n = max(1, int(math.ceil(dur/passo - 1e-9)))
        hh = dur/n
        a = W_S/(2.0*Hh)
        t0 = t
        if registrar:   # inicio do trecho, ja com os parametros novos (Pe pode saltar)
            T_.append(t); Dl.append(d); Wl.append(w); Pel.append(Pmax*sen(d)); El.append(e); Pml.append(Pm)
        for i in range(n):
            k1w = a*(Pm - Pmax*sen(d) - Dd*w)
            d2 = d + 0.5*hh*w;   w2 = w + 0.5*hh*k1w
            k2w = a*(Pm - Pmax*sen(d2) - Dd*w2)
            d3 = d + 0.5*hh*w2;  w3 = w + 0.5*hh*k2w
            k3w = a*(Pm - Pmax*sen(d3) - Dd*w3)
            d4 = d + hh*w3;      w4 = w + hh*k3w
            k4w = a*(Pm - Pmax*sen(d4) - Dd*w4)
            e += hh/6.0*Dd*(w*w + 2.0*w2*w2 + 2.0*w3*w3 + w4*w4)
            d += hh/6.0*(w + 2.0*w2 + 2.0*w3 + w4)
            w += hh/6.0*(k1w + 2.0*k2w + 2.0*k3w + k4w)
            t = t0 + (i + 1)*hh
            if registrar:
                T_.append(t); Dl.append(d); Wl.append(w); Pel.append(Pmax*sen(d)); El.append(e); Pml.append(Pm)
            if delta_lim is not None and d > delta_lim:
                perdeu = True
                break
        if perdeu:
            break
    out = dict(perdeu=perdeu, t_fim=t, delta_fim=d, omega_fim=w, Ed_fim=e)
    if registrar:
        out.update(t=np.array(T_), delta=np.array(Dl), omega=np.array(Wl),
                   Pe=np.array(Pel), Ed=np.array(El), Pm=np.array(Pml))
    return out


def energia(delta, omega, Pm=PM0, Pmax=P_MAX, H=H):
    """W = (H/ws) omega^2 - Pm delta - Pmax cos(delta)   [pu.rad]"""
    return (H/W_S)*np.asarray(omega)**2 - Pm*np.asarray(delta) - Pmax*np.cos(delta)


def potencial(delta, Pm=PM0, Pmax=P_MAX):
    """V(delta) = -Pm delta - Pmax cos(delta)   [pu.rad]"""
    return -Pm*np.asarray(delta) - Pmax*np.cos(delta)


# =============================================================== utilitarios numericos
def bissecao(f, a, b, tol=1e-14, nmax=300):
    fa = f(a)
    for _ in range(nmax):
        m = 0.5*(a + b)
        fm = f(m)
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
        if abs(b - a) < tol:
            break
    return 0.5*(a + b)


# =============================================================== analise algebrica (R2)
def ponto_de_operacao(Pm=PM0, E=E_LINHA, V=V_BAR, X=X_TOT):
    """Fasores no ponto de operacao: confere a coerencia de E', V, X e Pm."""
    Pmax = E*V/X
    d0 = math.asin(Pm/Pmax)
    Eg = E*cmath.exp(1j*d0)
    I = (Eg - V)/(1j*X)
    Sb = V*I.conjugate()            # potencia entregue ao barramento infinito
    Sg = Eg*I.conjugate()           # potencia atras da reatancia transitoria
    return dict(Pmax=Pmax, delta0_rad=d0, delta0_graus=math.degrees(d0),
                I_mod_pu=abs(I), I_ang_graus=math.degrees(cmath.phase(I)),
                P_barra_pu=Sb.real, Q_barra_pu=Sb.imag, Q_interna_pu=Sg.imag,
                fp_barra=Sb.real/abs(Sb))


def analise_linear(Pm=PM0, Pmax=P_MAX, H=H, D=D):
    """Equilibrios e linearizacao local (referencia auxiliar, rotulada) no equilibrio estavel."""
    if Pm > Pmax:
        return dict(existe=False)
    ds = math.asin(Pm/Pmax)
    du = math.pi - ds
    a = W_S/(2.0*H)
    Ps = Pmax*math.cos(ds)                         # coef. de potencia sincronizante [pu/rad]
    A = np.array([[0.0, 1.0], [-a*Ps, -a*D]])
    lam = np.linalg.eigvals(A)
    Au = np.array([[0.0, 1.0], [a*Ps, -a*D]])      # no equilibrio instavel cos(du) = -cos(ds)
    lam_u = np.sort(np.linalg.eigvals(Au).real)
    wn = math.sqrt(a*Ps)
    sigma = a*D/2.0                                # = zeta*wn = D*ws/(4H)
    zeta = sigma/wn
    r = dict(existe=True, Pm=Pm, Pmax=Pmax, H=H, D=D,
             delta_s_rad=ds, delta_s_graus=math.degrees(ds),
             delta_u_rad=du, delta_u_graus=math.degrees(du),
             Ps=Ps, K_rad_pu=1.0/Ps, K_graus_pu=math.degrees(1.0/Ps),
             A=A.tolist(), polos=[[float(l.real), float(l.imag)] for l in lam],
             autovalores_sela=lam_u.tolist(),
             wn=wn, fn=wn/(2*math.pi), zeta=zeta, sigma=sigma,
             tau=(1.0/sigma if sigma > 0 else math.inf),
             num_ganho=a, den=[1.0, 2*sigma, wn**2])
    taxa_dom = -max(l.real for l in lam)
    r['taxa_dominante'] = taxa_dom
    if 0.0 <= zeta < 1.0 or zeta < 0.0:
        wd = wn*math.sqrt(1.0 - zeta**2)
        r.update(regime='subamortecido' if zeta > 0 else ('sem amortecimento' if zeta == 0 else 'instavel'),
                 wd=wd, fd=wd/(2*math.pi), Td=2*math.pi/wd,
                 Mp=math.exp(-math.pi*zeta/math.sqrt(1 - zeta**2)),
                 tp=math.pi/wd, tr=(math.pi - math.acos(zeta))/wd)
        if zeta > 0:
            r['ts2_envoltoria'] = -math.log(0.02*math.sqrt(1 - zeta**2))/sigma
            r['ts2_4tau'] = 4.0/sigma
        else:
            r['ts2_envoltoria'] = math.inf
            r['ts2_4tau'] = math.inf
    else:
        r.update(regime='sobreamortecido' if zeta > 1 else 'critico',
                 wd=None, fd=None, Td=None, Mp=0.0, tp=None, tr=None,
                 ts2_envoltoria=None, ts2_4tau=4.0/taxa_dom)
    # tempo de acomodacao exato da forma fechada (2 %), avaliada numericamente
    if zeta > 0:
        tt = np.arange(0.0, 12.0/taxa_dom, 2e-4)
        y = degrau_linear(tt, 1.0, r)
        fora = np.where(np.abs(y - r['K_rad_pu']) > 0.02*r['K_rad_pu'])[0]
        r['ts2_forma_fechada'] = float(tt[fora[-1] + 1]) if len(fora) else 0.0
    return r


def degrau_linear(t, dPm, lin):
    """Forma fechada da linearizacao (rotulada): Delta delta(t) para degrau dPm."""
    t = np.asarray(t, dtype=float)
    K, s, wn, z = lin['K_rad_pu'], lin['sigma'], lin['wn'], lin['zeta']
    if z < 1.0:
        wd = wn*math.sqrt(1 - z**2)
        return K*dPm*(1.0 - np.exp(-s*t)*(np.cos(wd*t) + (s/wd)*np.sin(wd*t)))
    l1 = -s + math.sqrt(s*s - wn*wn)
    l2 = -s - math.sqrt(s*s - wn*wn)
    return K*dPm*(1.0 - (l2*np.exp(l1*t) - l1*np.exp(l2*t))/(l2 - l1))


def livre_linear(t, x0, v0, lin):
    """Forma fechada da linearizacao (rotulada): resposta livre a Delta delta(0)=x0, Delta omega(0)=v0."""
    t = np.asarray(t, dtype=float)
    s, wn, z = lin['sigma'], lin['wn'], lin['zeta']
    wd = wn*math.sqrt(1 - z**2)
    return np.exp(-s*t)*(x0*np.cos(wd*t) + ((v0 + s*x0)/wd)*np.sin(wd*t))


def trajetoria_falta(t, d0, Pm=PM0, H=H, D=D):
    """Forma fechada EXATA durante a falta (Pe = 0): a equacao fica linear.
    Retorna (delta, omega). Para D = 0: delta = d0 + ws Pm t^2/(4H)."""
    t = np.asarray(t, dtype=float)
    a = W_S/(2.0*H)
    if D == 0.0:
        return d0 + 0.5*a*Pm*t**2, a*Pm*t
    k = a*D
    return d0 + (Pm/D)*(t - (1.0 - np.exp(-k*t))/k), (Pm/D)*(1.0 - np.exp(-k*t))


def criterio_areas_falta(Pm=PM0, Pmax=P_MAX, H=H):
    """Angulo e tempo criticos de eliminacao (falta com Pe = 0; rede pos-falta = pre-falta; D = 0)."""
    d0 = math.asin(Pm/Pmax)
    du = math.pi - d0
    c = (Pm/Pmax)*(du - d0) + math.cos(du)
    if c >= 1.0:
        return dict(delta_cr_rad=d0, delta_cr_graus=math.degrees(d0), t_cr=0.0)
    dcr = math.acos(c)
    tcr = math.sqrt(4.0*H*(dcr - d0)/(W_S*Pm))
    A1 = Pm*(dcr - d0)                                       # area acelerante
    A2 = Pmax*(math.cos(dcr) - math.cos(du)) - Pm*(du - dcr) # area desacelerante disponivel
    return dict(delta0_rad=d0, delta_u_rad=du, delta_cr_rad=dcr,
                delta_cr_graus=math.degrees(dcr), t_cr=tcr, A1=A1, A2=A2)


def delta_max_areas(Pm1, d0, Pmax=P_MAX):
    """1o maximo de delta apos degrau (D = 0), pelo criterio das areas:
       Pm1 (dm - d0) + Pmax (cos dm - cos d0) = 0, com dm em (d1, du1].  None se instavel."""
    if Pm1 >= Pmax:
        return None
    d1 = math.asin(Pm1/Pmax)
    du1 = math.pi - d1
    F = lambda x: Pm1*(x - d0) + Pmax*(math.cos(x) - math.cos(d0))
    if F(du1) > 0:
        return None
    return bissecao(F, d1, du1)


def degrau_critico_areas(Pm0=PM0, Pmax=P_MAX):
    """Maior degrau de Pm que ainda preserva o sincronismo (D = 0, criterio das areas)."""
    d0 = math.asin(Pm0/Pmax)
    def G(Pm1):
        du1 = math.pi - math.asin(Pm1/Pmax)
        return Pm1*(du1 - d0) + Pmax*(math.cos(du1) - math.cos(d0))
    Pm1 = bissecao(G, Pm0 + 1e-12, Pmax)
    return Pm1 - Pm0


def pontos_de_retorno(E, Pm=PM0, Pmax=P_MAX):
    """Angulos em que omega = 0 para energia E (D = 0): V(delta) = E dos dois lados de delta_s."""
    ds = math.asin(Pm/Pmax)
    du = math.pi - ds
    V = lambda x: -Pm*x - Pmax*math.cos(x)
    if E >= V(du):
        return None
    da = bissecao(lambda x: V(x) - E, du - 2*math.pi, ds)
    db = bissecao(lambda x: V(x) - E, ds, du)
    return da, db


def periodo_energia(E, Pm=PM0, Pmax=P_MAX, H=H, n=4000):
    """Periodo da oscilacao nao linear (D = 0) pelo invariante de energia:
         T = 2 * integral_{da}^{db} d(delta) / omega(delta),  omega = sqrt((ws/H)(E - V)).
    Mudanca delta = c - r cos(theta) remove as singularidades nos pontos de retorno;
    a regra do ponto medio converge exponencialmente no integrando suave resultante."""
    pr = pontos_de_retorno(E, Pm, Pmax)
    if pr is None:
        return math.inf, None, None
    da, db = pr
    c, r = 0.5*(da + db), 0.5*(db - da)
    th = (np.arange(n) + 0.5)*math.pi/n
    x = c - r*np.cos(th)
    folga = np.maximum(E - potencial(x, Pm, Pmax), 1e-300)
    g = r*np.sin(th)/np.sqrt((W_S/H)*folga)
    return float(2.0*np.sum(g)*math.pi/n), da, db


def separatriz(Pm=PM0, Pmax=P_MAX, H=H, n=1500):
    """Curva omega(delta) da separatriz (D = 0): nivel de energia do equilibrio instavel."""
    ds = math.asin(Pm/Pmax)
    du = math.pi - ds
    Ecr = float(potencial(du, Pm, Pmax))
    dL = bissecao(lambda x: float(potencial(x, Pm, Pmax)) - Ecr, du - 2*math.pi + 1e-9, ds)
    x = np.linspace(dL, du, n)
    w = np.sqrt(np.maximum((W_S/H)*(Ecr - potencial(x, Pm, Pmax)), 0.0))
    return x, w, dL, du, Ecr


# =============================================================== metricas medidas na simulacao
def picos(t, y):
    """Maximos locais com interpolacao parabolica (tempo e valor)."""
    i = np.where((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:]))[0] + 1
    if len(i) == 0:
        return np.array([]), np.array([])
    y0, y1, y2 = y[i - 1], y[i], y[i + 1]
    den = y0 - 2*y1 + y2
    fr = np.where(den != 0, 0.5*(y0 - y2)/np.where(den != 0, den, 1.0), 0.0)
    h = t[i + 1] - t[i]
    return t[i] + fr*h, y1 - 0.25*(y0 - y2)*fr


def cruzamentos_subida(t, y, nivel):
    i = np.where((y[:-1] < nivel) & (y[1:] >= nivel))[0]
    return t[i] + (nivel - y[i])/(y[i + 1] - y[i])*(t[i + 1] - t[i])


def metricas_degrau(r, d_ini, d_fim, n_ciclos=10, faixa=0.02):
    """Pontos caracteristicos medidos na resposta simulada delta(t)."""
    t, y = r['t'], r['delta']
    A = d_fim - d_ini
    dev = y - d_fim
    m = dict(valor_final_rad=float(d_fim), ganho_rad_pu=None)
    tp, yp = picos(t, y)
    if len(tp):
        m['tp'] = float(tp[0])
        m['delta_pico_rad'] = float(yp[0])
        m['Mp'] = float((yp[0] - d_fim)/A)
    else:
        m['tp'], m['delta_pico_rad'], m['Mp'] = None, float(np.max(y)), 0.0
    tc = cruzamentos_subida(t, y, d_fim)
    m['tr'] = float(tc[0]) if len(tc) else None
    fora = np.where(np.abs(dev) > faixa*abs(A))[0]
    if len(fora) == 0:
        m['ts2'] = 0.0
    elif fora[-1] >= len(t) - 2:
        m['ts2'] = math.inf
    else:
        k = fora[-1]
        y1, y2 = abs(dev[k]), abs(dev[k + 1])
        m['ts2'] = float(t[k] + (y1 - faixa*abs(A))/(y1 - y2)*(t[k + 1] - t[k]))
    if len(tc) >= 3:
        nc = min(n_ciclos, len(tc) - 1)
        Tm = (tc[nc] - tc[0])/nc
        m['Td'] = float(Tm)
        m['wd'] = float(2*math.pi/Tm)
    else:
        m['Td'], m['wd'] = None, None
    # taxa de decaimento: regressao de ln(pico - valor final) contra o tempo
    ok = (yp - d_fim) > 1e-7*abs(A)
    if np.count_nonzero(ok) >= 3:
        cf = np.polyfit(tp[ok][:40], np.log(yp[ok][:40] - d_fim), 1)
        m['sigma'] = float(-cf[0])
    else:
        m['sigma'] = None
    return m
