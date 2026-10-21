"""Gera todas as figuras e numeros do relatorio (R2-R5). python3 ensaios.py"""
import json, time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import brentq
from bldc import *
import estilo

plt.rcParams.update({'font.size': 8, 'axes.grid': True, 'grid.alpha': .3, 'lines.linewidth': 1.1,
                     'legend.fontsize': 6.5, 'figure.dpi': 150, 'savefig.bbox': 'tight'})
C = dict(avg='#1f5fa8', sw='#c0392b', ex='#202020', lin='#16803f', gray='#888888')
R = {}
w4 = 4000 / RPM
d0 = brentq(lambda d: equilibrio(P, d)[0] - w4, 0.1, 1)
weq, ieq = equilibrio(P, d0)
L4 = linear(P, w4); L0 = linear(P, 0.0)
R['d0'] = d0; R['ieq'] = ieq; R['Idc_avg'] = d0 * ieq
R['lin4'] = {k: (v if not isinstance(v, np.ndarray) else [str(x) for x in v]) for k, v in L4.items()}
R['lin0'] = {k: (v if not isinstance(v, np.ndarray) else [str(x) for x in v]) for k, v in L0.items()}
print('d0', d0, 'ieq', ieq, L4)

# ---------- (a) degrau a partir do repouso ----------
tf = 0.08
dstep = lambda t: d0
ta, xa = sim_avg(P, tf, [0, 0, 0], dstep, t_eval=np.linspace(0, tf, 16001))
t0 = time.time()
Ts, Ws, Is, TEs, PINs = sim_sw(P, tf, 0.0, dstep, dec=8)
print('sw time', time.time() - t0)
ma = metrics(ta, xa[1] * RPM)
m_sw = Ts > 0.06; wsw = Ws[m_sw].mean() * RPM
ms = metrics(Ts, Ws * RPM, yss=wsw)
R['a'] = dict(avg=ma, ipk_avg=float(xa[0].max()), t_ipk=float(ta[np.argmax(xa[0])]),
              sw=ms, sw_wss=wsw, ipk_sw=float(np.abs(Is).max()), sw_ripple=float(np.ptp(Ws[m_sw]) * RPM),
              sw_Te_pp=float(np.ptp(TEs[m_sw])), sw_Te_mean=float(TEs[m_sw].mean()))
# referencia linear (degrau sem carga) - solucao fechada exata
Pn = dict(P); Pn['b2'] = 0.0; Pn['clamp'] = False
Pc = dict(P); Pc['b2'] = 0.0
L0n = linear(Pn, 0.0)
tn, xn = sim_avg(Pn, 0.06, [0, 0, 0], dstep, t_eval=np.linspace(0, 0.06, 6001))
wex = step2nd(tn, L0n['wn'], L0n['zeta'], L0n['G'] * d0)
tr4, xr4 = rk4_avg(Pn, 0.06, [0, 0, 0], dstep, dt=2e-6)
wex4 = step2nd(tr4, L0n['wn'], L0n['zeta'], L0n['G'] * d0)
tcl, xcl = sim_avg(Pc, 0.06, [0, 0, 0], dstep, t_eval=np.linspace(0, 0.06, 6001))
R['a_lin'] = dict(dev_clamp=float(np.max(np.abs(xcl[1] - wex))), imin_lin=float(xn[0].min()), G=L0n['G'], wss=L0n['G'] * d0 * RPM, zeta=L0n['zeta'], wn=L0n['wn'], Mp=L0n['Mp'], tp=L0n['tp'],
                  err_dop=float(np.max(np.abs(xn[1] - wex))), err_rk4=float(np.max(np.abs(xr4[1] - wex4))),
                  sim=metrics(tn, xn[1] * RPM))
# err float32 (precisao simples): RK4 em float32 aproximado por arredondamento do estado
x32 = np.zeros(3, np.float32); n = 30000; dt = np.float32(2e-6); e32 = 0
for j in range(n):
    f = lambda x: np.array(rhs_avg(0, x, Pn, dstep, lambda t: 0.0), np.float32)
    k1 = f(x32); k2 = f(x32 + dt / 2 * k1); k3 = f(x32 + dt / 2 * k2); k4 = f(x32 + dt * k3)
    x32 = (x32 + dt / np.float32(6) * (k1 + 2 * k2 + 2 * k3 + k4)).astype(np.float32)
wex_end = step2nd(np.array([n * 2e-6]), L0n['wn'], L0n['zeta'], L0n['G'] * d0)[0]
R['a_lin']['err_f32_end'] = float(abs(x32[1] - wex_end))

# pequenos sinais em torno de 4000 rpm
Dd = 0.02
tl, xl = sim_avg(P, 0.04, [ieq, weq, 0], lambda t: d0 + Dd, t_eval=np.linspace(0, 0.04, 8001))
mlin = metrics(tl, xl[1] * RPM)
wl_ex = weq + step2nd(tl, L4['wn'], L4['zeta'], L4['G'] * Dd)
R['ss'] = dict(sim=mlin, gain_sim=float((xl[1, -1] - weq) / Dd), gain_calc=L4['G'],
               Mp_calc=L4['Mp'], tp_calc=L4['tp'], ts_calc=L4['ts2'],
               zeta_sim=float(-np.log(mlin['Mp']) / np.sqrt(np.pi**2 + np.log(mlin['Mp'])**2)),
               dev_lin=float(np.max(np.abs(xl[1] - wl_ex)) / (L4['G'] * Dd)))
R['ss']['wn_sim'] = float(np.pi / (mlin['tp'] * np.sqrt(1 - R['ss']['zeta_sim']**2)))

fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.1))
ax[0].plot(Ts * 1e3, Ws * RPM, color=C['sw'], lw=.8, label='chaveado (Euler, 0,25 µs)')
ax[0].plot(ta * 1e3, xa[1] * RPM, color=C['avg'], label='médio (DOP853)')
ax[0].axhline(weq * RPM, color=C['ex'], ls='--', lw=.7)
ax[0].axhline(wsw, color=C['sw'], ls=':', lw=.7)
ax[0].plot(ma['t90'] * 1e3, .9 * 4000, 'o', ms=3, color=C['avg']); ax[0].plot(ma['ts'] * 1e3, .98 * 4000, 's', ms=3, color=C['avg'])
ax[0].plot(ms['ts'] * 1e3, .98 * wsw, 's', ms=3, color=C['sw'])
ax[0].annotate('4000 rpm (eq. calc.)', (45, 4060), fontsize=6); ax[0].annotate(f'{wsw:.0f} rpm', (45, wsw - 260), fontsize=6, color=C['sw'])
ax[0].annotate(f"$t_s$={ma['ts']*1e3:.1f} ms", (ma['ts'] * 1e3 + 1.5, 3500), fontsize=6, color=C['avg'])
ax[0].set_xlabel('t [ms]'); ax[0].set_ylabel('n [rpm]'); ax[0].legend(loc='lower right'); ax[0].set_ylim(0, 4500)
ax[0].set_title('(a) $n(t)$, degrau $d$: 0→%.3f' % d0, fontsize=7.5)
ax[1].plot(Ts * 1e3, Is[0], color=C['sw'], lw=.5, label='$i_a$ chaveado')
ax[1].plot(ta * 1e3, xa[0], color=C['avg'], label='$i$ médio')
ax[1].axhline(ieq, color=C['ex'], ls='--', lw=.7)
ax[1].plot(R['a']['t_ipk'] * 1e3, R['a']['ipk_avg'], 'v', ms=3.5, color=C['avg'])
ax[1].annotate(f"pico {R['a']['ipk_avg']:.2f} A", (R['a']['t_ipk'] * 1e3 + 2, R['a']['ipk_avg'] - .3), fontsize=6, color=C['avg'])
ax[1].annotate(f"$i_{{eq}}$={ieq:.2f} A", (50, ieq + .4), fontsize=6)
ax[1].set_xlabel('t [ms]'); ax[1].set_ylabel('corrente [A]'); ax[1].legend(loc='upper right'); ax[1].set_title('(b) corrente', fontsize=7.5)
ax[2].plot(tl * 1e3, xl[1] * RPM, color=C['avg'], label='médio, $\\Delta d$=+0,02')
ax[2].plot(tl * 1e3, wl_ex * RPM, '--', color=C['lin'], label='linearizado (fechado)')
ax[2].plot(mlin['tp'] * 1e3, (weq + (1 + mlin['Mp']) * (xl[1, -1] - weq)) * RPM, 'v', ms=3.5, color=C['avg'])
ax[2].annotate(f"$M_p$={mlin['Mp']*100:.2f} %", (mlin['tp'] * 1e3 + 1, (weq + 1.0 * (xl[1, -1] - weq)) * RPM - 40), fontsize=6)
ax[2].set_xlabel('t [ms]'); ax[2].set_ylabel('n [rpm]'); ax[2].legend(loc='lower right'); ax[2].set_title('(c) pequenos sinais em 4000 rpm', fontsize=7.5)
plt.tight_layout(); plt.savefig('fig_degrau.pdf'); plt.close()

# ---------- (b) condicao inicial nao nula: desaceleracao livre ----------
tf = 0.2
tb, xb = sim_avg(P, tf, [0, w4, 0], lambda t: 0.0, t_eval=np.linspace(0, tf, 20001))
wcl = coastdown(tb, w4, P)
Tb, Wb, Ib, TEb, _ = sim_sw(P, tf, w4, lambda t: 0.0, dec=40)
wcl_sw = coastdown(Tb, w4, P)
th = brentq(lambda t: coastdown(np.array([t]), w4, P)[0] - w4 / 2, 1e-4, 1)
R['b'] = dict(t_half_calc=th, err_avg=float(np.max(np.abs(xb[1] - wcl))), err_sw=float(np.max(np.abs(Wb - wcl_sw))),
              t_half_sim=float(np.interp(-w4 / 2, -xb[1], tb)), w_end=float(xb[1, -1] * RPM), w_end_calc=float(wcl[-1] * RPM))
# CI acima do equilibrio com d0 -> conducao descontinua
w5 = 4500 / RPM
dci = 0.5
tc, xc = sim_avg(P, 0.08, [0, w5, 0], lambda t: dci, t_eval=np.linspace(0, 0.08, 16001))
Tc, Wc, Ic, _, _ = sim_sw(P, 0.08, w5, lambda t: dci, dec=8)
izero = tc[np.argmax(xc[0] > 1e-6)]
wthr = dci * P['Vs'] / P['k']
weq_ci = equilibrio(P, dci)[0]
R['b2'] = dict(d=dci, t_i0=float(izero), w_thr_rpm=float(wthr * RPM), t_thr_calc=float(brentq(lambda t: coastdown(np.array([t]), w5, P)[0] - wthr, 1e-6, 1)),
               weq_calc=float(weq_ci * RPM), weq_sim=float(xc[1, -1] * RPM), wsw=float(Wc[Tc > 0.06].mean() * RPM))
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.1))
ax[0].plot(tb * 1e3, wcl * RPM, color=C['ex'], lw=2.2, alpha=.35, label='solução fechada (Riccati)')
ax[0].plot(tb * 1e3, xb[1] * RPM, color=C['avg'], label='médio (DOP853)')
ax[0].plot(Tb * 1e3, Wb * RPM, '--', color=C['sw'], lw=.8, label='chaveado')
ax[0].plot(th * 1e3, 2000, 'o', ms=3.5, color=C['ex']); ax[0].annotate(f'$t_{{1/2}}$={th*1e3:.2f} ms', (th * 1e3 + 4, 2050), fontsize=6)
ax[0].set_xlabel('t [ms]'); ax[0].set_ylabel('n [rpm]'); ax[0].legend(); ax[0].set_title('(a) $n(0)$=4000 rpm, $d$=0', fontsize=7.5)
ax[1].semilogy(tb * 1e3, np.abs(xb[1] - wcl) * RPM + 1e-16, color=C['avg'], label='|médio − fechada|')
ax[1].semilogy(Tb * 1e3, np.abs(Wb - wcl_sw) * RPM + 1e-16, color=C['sw'], lw=.8, label='|chaveado − fechada|')
ax[1].set_xlabel('t [ms]'); ax[1].set_ylabel('erro [rpm]'); ax[1].legend(); ax[1].set_title('(b) erro numérico', fontsize=7.5)
ax[2].plot(Tc * 1e3, Wc * RPM, color=C['sw'], lw=.8, label='chaveado')
ax[2].plot(tc * 1e3, xc[1] * RPM, color=C['avg'], label='médio')
ax[2].axhline(wthr * RPM, color=C['ex'], ls='--', lw=.7)
ax[2].axhline(weq_ci * RPM, color=C['ex'], ls=':', lw=.7)
ax[2].annotate('$dV_s/k$ (fim da cond. descontínua)', (12, wthr * RPM + 40), fontsize=5.5)
ax[2].plot(izero * 1e3, np.interp(izero, tc, xc[1]) * RPM, 'o', ms=3.5, color=C['avg'])
ax[2].set_xlabel('t [ms]'); ax[2].set_ylabel('n [rpm]'); ax[2].legend(loc='upper right'); ax[2].set_title('(c) $n(0)$=4500 rpm, $d$=0,5', fontsize=7.5)
plt.tight_layout(); plt.savefig('fig_ci.pdf'); plt.close()

# ---------- (c) perturbacao: pulso de torque de carga ----------
Td0 = 0.02; t1, t2 = 0.10, 0.20; tf = 0.30
Tdf = lambda t: Td0 if t1 <= t < t2 else 0.0
tc_, xc_ = sim_avg(P, tf, [ieq, weq, 0], lambda t: d0, Tdf, t_eval=np.linspace(0, tf, 30001), max_step=2e-5)
Tp, Wp, Ip, TEp, _ = sim_sw(P, tf, 0.0, lambda t: d0, Tdf, dec=40)
wd_eq, id_eq = equilibrio(P, d0, Td0)
dw_lin = L4['Gd'] * Td0
mdis = (tc_ > 0.18) & (tc_ < 0.2)
wsw_pre = Wp[(Tp > 0.08) & (Tp < 0.1)].mean(); wsw_dur = Wp[(Tp > 0.18) & (Tp < 0.2)].mean()
R['c'] = dict(dw_calc_nl=float((wd_eq - weq) * RPM), dw_calc_lin=float(dw_lin * RPM),
              dw_sim=float((xc_[1, mdis].mean() - weq) * RPM), di_calc=float(id_eq - ieq),
              di_sim=float(xc_[0, mdis].mean() - ieq), dw_sw=float((wsw_dur - wsw_pre) * RPM),
              rec=metrics(tc_, xc_[1] * RPM, yss=weq * RPM, t0=t2))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.1))
ax[0].plot(tc_ * 1e3, xc_[1] * RPM, color=C['avg'], label='médio')
ax[0].plot(Tp * 1e3, Wp * RPM, color=C['sw'], lw=.6, label='chaveado (parte do repouso)')
ax[0].axhline(wd_eq * RPM, color=C['ex'], ls='--', lw=.7); ax[0].axhline(weq * RPM, color=C['ex'], ls=':', lw=.7)
ax[0].annotate(f"Δn calc.={R['c']['dw_calc_nl']:.0f} rpm | sim.={R['c']['dw_sim']:.0f} rpm", (105, wd_eq * RPM - 130), fontsize=6)
ax[0].annotate(f"Δn chaveado={R['c']['dw_sw']:.0f} rpm", (105, wsw_dur * RPM - 200), fontsize=6, color=C['sw'])
ax[0].set_xlabel('t [ms]'); ax[0].set_ylabel('n [rpm]'); ax[0].legend(loc='lower right', ncol=2); ax[0].set_ylim(2400, 4300)
ax[0].set_title('(a) pulso $T_d$=+0,02 N·m em 100–200 ms ($d=d_0$)', fontsize=7.5)
ax[1].plot(tc_ * 1e3, xc_[0], color=C['avg'], label='$i$ médio')
ax[1].plot(Tp * 1e3, TEp / P['k'], color=C['sw'], lw=.4, alpha=.7, label='$T_e/k$ chaveado')
ax[1].axhline(id_eq, color=C['ex'], ls='--', lw=.7)
ax[1].set_xlim(50, 300); ax[1].set_ylim(0, 3.5)
ax[1].set_xlabel('t [ms]'); ax[1].set_ylabel('corrente equivalente [A]'); ax[1].legend(loc='upper right'); ax[1].set_title('(b) corrente / torque', fontsize=7.5)
plt.tight_layout(); plt.savefig('fig_pert.pdf'); plt.close()

# ---------- validade da reducao: torque chaveado / medio a velocidade fixa ----------
Q = dict(P); Q['J'] = 1e3; Q['b2'] = 0.0
ws_ = np.array([10, 25, 50, 100, 150, 200, 300, 418.9, 520])
ratio = []
for w in ws_:
    tf_ = max(0.02, 12 * 2 * np.pi / (P['p'] * w))
    T_, W_, I_, TE_, _ = sim_sw(Q, tf_, w, lambda t: 1.0, dec=2)
    m_ = T_ > tf_ / 2
    ratio.append(TE_[m_].mean() / (P['k'] * (P['Vs'] - P['k'] * w) / P['RLL']))
ratio = np.array(ratio)
xi = P['LLL'] / P['RLL'] * 6 * P['p'] * ws_ / (2 * np.pi)   # tau_e / T_setor
R['val'] = dict(w=ws_.tolist(), ratio=ratio.tolist(), xi=xi.tolist())
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.0))
ax[0].plot(ws_ * RPM, ratio, 'o-', color=C['sw'], ms=3)
ax[0].axhline(0.95, color=C['gray'], ls=':', lw=.7); ax[0].annotate('95 %', (100, .955), fontsize=6)
ax[0].axvline(4000, color=C['ex'], ls='--', lw=.7); ax[0].annotate('nominal', (4050, .85), fontsize=6)
ax[0].set_xlabel('n [rpm] (fixa)'); ax[0].set_ylabel('$T_{e,chav}/T_{e,médio}$'); ax[0].set_title('(a) torque médio, $d$=1', fontsize=7.5)
ax[1].semilogx(xi, ratio, 'o-', color=C['sw'], ms=3)
ax[1].set_xlabel('$\\xi=\\tau_e/T_{setor}$'); ax[1].set_ylabel('$T_{e,chav}/T_{e,médio}$'); ax[1].set_title('(b) parâmetro adimensional', fontsize=7.5)
plt.tight_layout(); plt.savefig('fig_validade.pdf'); plt.close()

# ---------- R5: sensibilidade ----------
levels = {
    'J': [('0,1×', 3.3e-7), ('nominal 3,3e-6', 3.3e-6), ('pág. 4,017e-6', 4.017e-6), ('10×', 3.3e-5), ('60× 2e-4', 2e-4)],
    'RLL': [('0,31× 1,0', 1.0), ('pág. 2,65', 2.65), ('nominal 3,2', 3.2), ('120 °C 4,46', 4.457), ('5×', 16.0)],
    'k': [('0,5×', 0.024), ('$K_e$ 0,0430', 0.04297), ('nominal 0,048', 0.048), ('senoidal 0,0642', 0.06415), ('2×', 0.096)],
}
units = {'J': 'kg·m²', 'RLL': 'Ω', 'k': 'N·m/A'}
sens = {}
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.2))
cols = ['#6a1b9a', '#1976d2', '#111111', '#e67e22', '#2e7d32']
for a_, (par, lv) in zip(ax, levels.items()):
    sens[par] = []
    for jj, (lab, val) in enumerate(lv):
        Q = dict(P); Q[par] = val
        we, ie = equilibrio(Q, d0); Lq = linear(Q, we)
        tfq = min(max(8 * Lq['ts2'], 0.03), 2.0)
        tq, xq = sim_avg(Q, tfq, [0, 0, 0], dstep, t_eval=np.linspace(0, tfq, 12001), max_step=tfq / 2000)
        mq = metrics(tq, xq[1] * RPM)
        pred = dict(wss=we * RPM, zeta=Lq['zeta'], wn=Lq['wn'], ts=Lq['ts2'], ibound=d0 * P['Vs'] / Q['RLL'], Mp=Lq.get('Mp', 0.0))
        sens[par].append(dict(lab=lab, val=val, pred=pred, sim=dict(wss=float(xq[1, -1] * RPM), Mp=mq['Mp'], ts=mq['ts'], ipk=float(xq[0].max()))))
        tp_ = tq[tq <= 0.06]
        col_ = ('#111111' if 'nominal' in lab else cols[jj if jj < 2 else jj + 1 if jj + 1 < 5 else 4])
        if mq['ts'] <= 0.06:
            a_.plot(mq['ts'] * 1e3, np.interp(mq['ts'], tq, xq[1]) * RPM, 's', ms=3, mfc='none', color=col_)
        if mq['Mp'] > 0.005 and mq['tp'] <= 0.06:
            a_.plot(mq['tp'] * 1e3, (1 + mq['Mp']) * xq[1, -1] * RPM, 'v', ms=3.5, color=col_)
        a_.plot(tp_ * 1e3, xq[1, :len(tp_)] * RPM, color=('#111111' if 'nominal' in lab else cols[jj if jj < 2 else jj + 1 if jj + 1 < 5 else 4]), lw=1.6 if 'nominal' in lab else .9, ls='-' if 'nominal' in lab else '--' if 'pág' in lab or '120' in lab or '60×' in lab or '0,31' in lab or 'senoidal' in lab or 'K_e' in lab else '-', label=lab)
    a_.set_xlabel('t [ms]'); a_.set_ylabel('n [rpm]'); a_.legend(fontsize=5.5, loc='lower right')
    a_.set_title({'J': '(a) inércia $J$', 'RLL': '(b) resistência $R_{LL}$', 'k': '(c) constante $k$'}[par], fontsize=7.5)
plt.tight_layout(); plt.savefig('fig_sens.pdf'); plt.close()
R['sens'] = sens

# amplitude do degrau (d = 1)
t1_, x1_ = sim_avg(P, 0.05, [0, 0, 0], lambda t: 1.0)
R['d1'] = dict(ipk=float(x1_[0].max()), wss=float(x1_[1, -1] * RPM))
# B: demonstracao do procedimento de identificacao (degrau de corrente + desaceleracao), sem carga
Pb = dict(P); Pb['b2'] = 0.0
i0 = 1.0; tt = np.linspace(0, 0.02, 2001)
wacc = (P['k'] * i0 / P['B']) * (1 - np.exp(-P['B'] / P['J'] * tt))
rng = np.random.default_rng(7)
wn_ = wacc + rng.normal(0, 0.05, tt.size)              # ruido de 0,05 rad/s (encoder)
alpha = np.polyfit(tt[:400], wn_[:400], 1)[0]; J_id = P['k'] * i0 / alpha
tc2 = np.linspace(0, 2.0, 2001); wc2 = 400 * np.exp(-P['B'] / P['J'] * tc2) + rng.normal(0, .05, tc2.size)
B_id = -np.polyfit(tc2, np.log(wc2), 1)[0] * J_id
R['ident'] = dict(J_id=J_id, B_id=B_id)
json.dump(R, open('resultados.json', 'w'), indent=1, default=float)
print(json.dumps(R, indent=1, default=float)[:6000])
