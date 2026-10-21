"""Ensaio extra: reproduz o modo 0 do .tse (malha fechada original) no modelo trifasico. python3 malha_fechada.py"""
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from bldc import *
import estilo
plt.rcParams.update({'font.size': 8, 'axes.grid': True, 'grid.alpha': .3, 'lines.linewidth': 1.0, 'legend.fontsize': 6.5, 'savefig.bbox': 'tight'})
c = MalhaTSE()
T, W, I, TE, D = sim_sw(P, 0.3, 0.0, None, dec=20, ctrl=c, Th=50e-6)
n = W * RPM; m = T > 0.2
x = n[m] - n[m].mean(); F = np.fft.rfftfreq(len(x), T[1] - T[0]); A = np.abs(np.fft.rfft(x))
out = dict(n_med=float(n[m].mean()), n_pp=float(np.ptp(n[m])), f_rip=float(F[np.argmax(A[1:]) + 1]),
           d_med=float(D[m].mean()), n_pico=float(n.max()), t_pico=float(T[np.argmax(n)]),
           ts=float(T[np.where(np.abs(n - 4000) > 80)[0][-1] + 1]))
json.dump(out, open('malha_fechada.json', 'w'), indent=1); print(out)
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.1))
ax[0].plot(T * 1e3, n, color='#1f5fa8'); ax[0].axhline(4000, color='k', ls='--', lw=.7)
ax[0].plot(out['t_pico'] * 1e3, out['n_pico'], 'v', ms=3.5, color='#c0392b')
ax[0].annotate(f"pico {out['n_pico']:.0f} rpm", (out['t_pico'] * 1e3 + 10, out['n_pico'] - 400), fontsize=6)
ax[0].plot(out['ts'] * 1e3, 4000 * 0.98, 's', ms=3, color='#c0392b'); ax[0].annotate(f"$t_s$(2 %)={out['ts']*1e3:.0f} ms", (out['ts'] * 1e3 + 10, 3300), fontsize=6)
ax[0].set_xlabel('t [ms]'); ax[0].set_ylabel('n [rpm]'); ax[0].set_title('(a) $n(t)$, modo 0 (Throttle 82,9 %)', fontsize=7.5)
mz = (T > 0.25) & (T < 0.26)
ax[1].plot(T[mz] * 1e3, n[mz], color='#1f5fa8'); ax[1].axhline(out['n_med'], color='k', ls=':', lw=.7)
ax[1].set_xlabel('t [ms]'); ax[1].set_ylabel('n [rpm]'); ax[1].set_title(f"(b) zoom: {out['n_pp']:.1f} rpm p-p a {out['f_rip']:.0f} Hz", fontsize=7.5)
ax[2].plot(T[mz] * 1e3, I[0][mz], color='#c0392b', lw=.7, label='$i_a$ [A]')
ax[2].plot(T[mz] * 1e3, D[mz], color='#16803f', lw=.7, label='$d$ (PI corrente)')
ax[2].set_xlabel('t [ms]'); ax[2].legend(loc='lower right'); ax[2].set_title(f"(c) $i_a$ e $d$ (média {out['d_med']:.3f})", fontsize=7.5)
plt.tight_layout(); plt.savefig('fig_mf.pdf'); plt.close()
