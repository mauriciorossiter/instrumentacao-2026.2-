# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: simulacao do CIRCUITO equivalente (em unidades eletricas).

Duas versoes, ambas so com numpy:
  simula_continuo : RK4 de passo fixo (1 ms) sobre os estados eletricos (i_L, v_C); a fonte controlada
                    e' avaliada continuamente. Mostra que o circuito, com os valores de R, L e C
                    calculados, e' a mesma equacao da E01 (R1b).
  simula_amostrado: o que o TyphoonSim faz. A malha R-L-C e' resolvida de forma exata (ZOH) entre
                    amostras, e a fonte controlada so muda a cada TS_SP (100 us), calculada com v_C
                    medido no inicio da amostra (blocos de sinal). 'atraso' acrescenta amostras de
                    atraso entre a medicao e a fonte, para cercar a implementacao do simulador.

Segmentos: lista de (duracao [s], Pm [pu], Pmax [pu], D [pu/(rad/s)]); R = KV*D/KI muda por trecho
(resistor variavel controlado pelo SCADA); L e C sao fixos do circuito montado.
Saidas ja reconvertidas: delta = delta0 + v_C/(KV*Ks), Delta_omega = i/KI, Pe = (v_C + v_nl)/KV.
"""
import math
import numpy as np

import parametros_e02 as P


def expm2(A):
    """Exponencial de matriz 2x2 (Taylor com escalonamento e quadratura)."""
    A = np.asarray(A, dtype=float)
    nrm = np.max(np.sum(np.abs(A), axis=1))
    s = max(0, int(math.ceil(math.log2(nrm))) + 1) if nrm > 0.5 else 0
    As = A/(2**s)
    E, T = np.eye(2), np.eye(2)
    for k in range(1, 20):
        T = T @ As/k
        E = E + T
    for _ in range(s):
        E = E @ E
    return E


def discretiza(R, L, C, Ts):
    """x[k+1] = Phi x[k] + Gam u[k] para x = (i, v_C), u = tensao liquida aplicada a malha R-L-C."""
    A = np.array([[-R/L, -1.0/L], [1.0/C, 0.0]])
    Ab = np.zeros((3, 3))
    Ab[:2, :2] = A
    Ab[0, 2] = 1.0/L
    # expm do bloco aumentado (3x3) via Taylor com escalonamento
    nrm = np.max(np.sum(np.abs(Ab*Ts), axis=1))
    s = max(0, int(math.ceil(math.log2(nrm))) + 1) if nrm > 0.5 else 0
    As = Ab*Ts/(2**s)
    E, T = np.eye(3), np.eye(3)
    for k in range(1, 22):
        T = T @ As/k
        E = E + T
    for _ in range(s):
        E = E @ E
    return E[:2, :2].copy(), E[:2, 2].copy()


def v_nl(vC, Pmax, delta_ref=P.DELTA0, kvd=P.KV_DELTA):
    """Fonte controlada: resto nao linear da 'mola' sincronizante, em volts."""
    return P.KV*Pmax*math.sin(delta_ref + vC/kvd) - vC


def simula_amostrado(segmentos, vC0=0.0, i0=0.0, L=P.L_EQ, C=P.C_EQ, Ts=P.TS_SP, atraso=0,
                     delta_lim=None, decimar=1):
    """Circuito com a fonte controlada amostrada a cada Ts (o que o TyphoonSim executa)."""
    x0, x1 = float(i0), float(vC0)
    t = 0.0
    fila = [v_nl(x1, segmentos[0][2])]*(atraso + 1)
    T_, I_, V_, N_, PM_ = [], [], [], [], []
    perdeu = False
    k_tot = 0
    for (dur, Pm, Pmax, Dd) in segmentos:
        R = P.KV*Dd/P.KI
        Phi, Gam = discretiza(R, L, C, Ts)
        p00, p01, p10, p11 = Phi[0, 0], Phi[0, 1], Phi[1, 0], Phi[1, 1]
        g0, g1 = Gam[0], Gam[1]
        n = max(1, int(round(dur/Ts)))
        vm = P.KV*Pm
        for _ in range(n):
            fila.append(v_nl(x1, Pmax))          # mede v_C no inicio da amostra
            vn = fila.pop(0)                     # valor aplicado (com 'atraso' amostras)
            if k_tot % decimar == 0:
                T_.append(t); I_.append(x0); V_.append(x1); N_.append(P.KV*Pmax*math.sin(P.DELTA0 + x1/P.KV_DELTA) - x1)
                PM_.append(Pm)
            u = vm - vn
            x0, x1 = p00*x0 + p01*x1 + g0*u, p10*x0 + p11*x1 + g1*u
            t += Ts
            k_tot += 1
            if delta_lim is not None and P.DELTA0 + x1/P.KV_DELTA > delta_lim:
                perdeu = True
                break
        if perdeu:
            break
    T_.append(t); I_.append(x0); V_.append(x1); N_.append(v_nl(x1, segmentos[-1][2])); PM_.append(segmentos[-1][1])
    return reconverte(np.array(T_), np.array(I_), np.array(V_), np.array(N_), np.array(PM_), perdeu)


def simula_continuo(segmentos, vC0=0.0, i0=0.0, L=P.L_EQ, C=P.C_EQ, h=P.PASSO_CIRC, delta_lim=None):
    """RK4 de passo fixo nos estados eletricos, com a fonte controlada continua."""
    i, vC, t = float(i0), float(vC0), 0.0
    T_, I_, V_, N_, PM_ = [], [], [], [], []
    perdeu = False
    for (dur, Pm, Pmax, Dd) in segmentos:
        R = P.KV*Dd/P.KI
        vm = P.KV*Pm
        n = max(1, int(math.ceil(dur/h - 1e-9)))
        hh = dur/n

        def f(i_, v_):
            return (vm - R*i_ - v_ - v_nl(v_, Pmax))/L, i_/C
        T_.append(t); I_.append(i); V_.append(vC); N_.append(v_nl(vC, Pmax)); PM_.append(Pm)
        t0 = t
        for k in range(n):
            a1, b1 = f(i, vC)
            a2, b2 = f(i + 0.5*hh*a1, vC + 0.5*hh*b1)
            a3, b3 = f(i + 0.5*hh*a2, vC + 0.5*hh*b2)
            a4, b4 = f(i + hh*a3, vC + hh*b3)
            i += hh/6*(a1 + 2*a2 + 2*a3 + a4)
            vC += hh/6*(b1 + 2*b2 + 2*b3 + b4)
            t = t0 + (k + 1)*hh
            T_.append(t); I_.append(i); V_.append(vC); N_.append(v_nl(vC, Pmax)); PM_.append(Pm)
            if delta_lim is not None and P.DELTA0 + vC/P.KV_DELTA > delta_lim:
                perdeu = True
                break
        if perdeu:
            break
    return reconverte(np.array(T_), np.array(I_), np.array(V_), np.array(N_), np.array(PM_), perdeu)


def reconverte(t, i, vC, vn, Pm, perdeu):
    return dict(t=t, i=i, vC=vC, vnl=vn, vm=P.KV*Pm, perdeu=perdeu,
                delta=P.DELTA0 + vC/P.KV_DELTA, omega=i/P.KI, Pe=(vC + vn)/P.KV, Pm=Pm)
