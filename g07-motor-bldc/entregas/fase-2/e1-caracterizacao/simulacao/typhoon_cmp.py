"""Compara os CSV exportados do TyphoonSim (pasta dados-typhoon) com o modelo trifasico em Python
nas mesmas condicoes do .tse (portadora/comparador amostrados a Ts = 5 us, Hall a 50 us).
python3 typhoon_cmp.py  -> fig_typhoon.pdf, typhoon_cmp.json"""
import json, sys, numpy as np, matplotlib
from multiprocessing import Pool
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from bldc import *
import estilo
TS = 5e-6; D0 = 0.7074; TD = 0.02
pulse = lambda t: TD if 0.10 <= t < 0.20 else 0.0

class Desliga:
    def __init__(s, c, t1, d1): s.c, s.t1, s.d1 = c, t1, d1
    def __call__(s, t, w, i, h):
        d = s.c(t, w, i, h)
        return s.d1 if t >= s.t1 else d

CASOS = {
    'modo_0': dict(ctrl='mf'),
    'modo_1_repouso': dict(d=lambda t: D0),
    'modo_1_equilibrio': dict(d=lambda t: 0.867 if t < 0.15 else 0.887),
    'modo_2': dict(ctrl='ci'),
    'modo_3': dict(d=lambda t: D0, Td=pulse),
    'modo_4': dict(ctrl='mf', Td=pulse),
}

def roda(nome):
    c = CASOS[nome]
    ctrl = None
    if c.get('ctrl') == 'mf': ctrl = MalhaTSE()
    if c.get('ctrl') == 'ci': ctrl = Desliga(MalhaTSE(), 0.15, 0.0)
    T, W, I, TE, _ = sim_sw(P, 0.3, 0.0, c.get('d'), c.get('Td', lambda t: 0.0), dec=40, ctrl=ctrl, Th=50e-6, Tq=TS)
    return nome, T, W * RPM

if __name__ == '__main__':
    with Pool(6) as pool:
        res = pool.map(roda, list(CASOS))
    out = {}
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.2)); ax = ax.ravel()
    tit = {'modo_0': '(a) modo 0: malha fechada', 'modo_1_repouso': '(b) modo 1: degrau $0\\to0{,}7074$',
           'modo_1_equilibrio': '(c) modo 1: $0{,}867\\to0{,}887$ em 0,15 s', 'modo_2': '(d) modo 2: $d=0$ após 0,15 s',
           'modo_3': '(e) modo 3: pulso de carga (MA)', 'modo_4': '(f) modo 4: pulso de carga (MF)'}
    for k, (nome, T, n) in enumerate(res):
        D = np.genfromtxt(f'dados-typhoon/{nome}.csv', delimiter=',', names=True)
        tt, nt = D['Time'], D['n']
        npy = np.interp(tt, T, n)
        # media em janelas de regime
        def med(t0, t1, t, y): m = (t >= t0) & (t <= t1); return float(y[m].mean())
        r = dict(t=tt.tolist(), n_ty=nt.tolist(), n_py=npy.tolist(),
                 err_max=float(np.max(np.abs(nt[3:] - npy[3:]))), err_rel=float(np.max(np.abs(nt[3:] - npy[3:]) / np.maximum(nt[3:], 1))))
        if nome in ('modo_0', 'modo_1_repouso'):
            r.update(reg_ty=med(0.05, 0.3, tt, nt), reg_py=med(0.05, 0.3, T, n))
        if nome == 'modo_1_equilibrio':
            r.update(antes_ty=med(0.05, 0.15, tt, nt), depois_ty=med(0.17, 0.3, tt, nt), antes_py=med(0.05, 0.15, T, n), depois_py=med(0.17, 0.3, T, n))
        if nome in ('modo_3', 'modo_4'):
            r.update(antes_ty=med(0.05, 0.1, tt, nt), durante_ty=med(0.12, 0.2, tt, nt), antes_py=med(0.05, 0.1, T, n), durante_py=med(0.12, 0.2, T, n))
        if nome == 'modo_2':
            w0 = np.interp(0.15, T, n) / RPM
            tc = tt[(tt > 0.15)]; ncl = coastdown(tc - 0.15, w0, P) * RPM
            r.update(n_fechada=ncl.tolist(), err_fechada_rel=float(np.max(np.abs(nt[tt > 0.15] - ncl) / ncl)))
        out[nome] = r
        a = ax[k]
        a.plot(T * 1e3, n, color='#1f5fa8', lw=.6, label='Python (trifásico)')
        a.plot(tt * 1e3, nt, 'o', ms=2.6, mfc='none', color='#c0392b', label='TyphoonSim (CSV, 10 ms)')
        if nome == 'modo_2':
            a.plot(tc * 1e3, ncl, '--', color='k', lw=.8, label='sol. fechada')
        if nome in ('modo_0', 'modo_1_repouso'):
            a.axhline(r['reg_ty'], color='#c0392b', ls=':', lw=.7)
            a.annotate(f"regime: {r['reg_ty']:.0f} (Ty) / {r['reg_py']:.0f} (Py)", (60, r['reg_ty'] - 90), fontsize=5.5)
        if nome == 'modo_1_equilibrio':
            a.axvline(150, color='k', ls=':', lw=.7)
            a.annotate(f"degrau em 150 ms: $\\Delta n$ = {r['depois_ty']-r['antes_ty']:+.1f} rpm (Ty)", (20, r['antes_ty'] - 90), fontsize=5.5)
        if nome == 'modo_2':
            from scipy.optimize import brentq
            th = brentq(lambda x: coastdown(np.array([x]), w0, P)[0] * RPM - w0 * RPM / 2, 1e-4, 0.1)
            a.plot((0.15 + th) * 1e3, w0 * RPM / 2, 'D', ms=3.5, color='k')
            a.annotate(f"$t_{{1/2}}$ = {th*1e3:.1f} ms", ((0.15 + th) * 1e3 + 8, w0 * RPM / 2), fontsize=5.5)
        if nome == 'modo_3':
            a.axhline(r['antes_ty'], color='#c0392b', ls=':', lw=.7); a.axhline(r['durante_ty'], color='#c0392b', ls=':', lw=.7)
            a.annotate(f"$\\Delta n$ = {r['durante_ty']-r['antes_ty']:.0f} (Ty) / {r['durante_py']-r['antes_py']:.0f} (Py) rpm", (20, (r['antes_ty'] + r['durante_ty']) / 2), fontsize=5.5)
        if nome == 'modo_4':
            km = int(np.argmin(nt[5:20])) + 5
            a.plot(tt[km] * 1e3, nt[km], 'v', ms=3.5, color='k')
            a.annotate(f"mín. {nt[km]:.0f} rpm", (tt[km] * 1e3 + 8, nt[km] - 40), fontsize=5.5)
        a.set_title(tit[nome], fontsize=7.5); a.set_xlabel('t [ms]'); a.set_ylabel('n [rpm]')
        if nome != 'modo_2': a.set_ylim(max(0, nt[3:].min() - 250), nt.max() + 150)
        a.legend(fontsize=5.5, loc='lower right' if nome != 'modo_2' else 'upper right')
    plt.tight_layout(); plt.savefig('fig_typhoon.pdf', bbox_inches='tight'); plt.close()
    json.dump(out, open('typhoon_cmp.json', 'w'), indent=1)
    for k, v in out.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else '...') for a, b in v.items()})
