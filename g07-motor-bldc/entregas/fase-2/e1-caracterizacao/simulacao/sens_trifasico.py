"""R5 na forma original: repete os niveis de sensibilidade no modelo trifasico chaveado
(PWM ideal, Hall continuo), degrau d = 0 -> d0 a partir do repouso. python3 sens_trifasico.py -> sens_trifasico.json"""
import json, numpy as np
from multiprocessing import Pool
from bldc import *
R = json.load(open('resultados.json')); d0 = R['d0']
levels = {
    'J': [('0,1×', 3.3e-7), ('nominal', 3.3e-6), ('pág.', 4.017e-6), ('10×', 3.3e-5), ('60×', 2e-4)],
    'RLL': [('0,31×', 1.0), ('pág.', 2.65), ('nominal', 3.2), ('120 °C', 4.457), ('5×', 16.0)],
    'k': [('0,5×', 0.024), ('Ke', 0.04297), ('nominal', 0.048), ('senoidal', 0.06415), ('2×', 0.096)],
}
def caso(arg):
    par, lab, val, ts_avg = arg
    Q = dict(P); Q[par] = val
    tf = float(min(max(0.08, 5 * ts_avg), 2.0))
    T, W, I, TE, _ = sim_sw(Q, tf, 0.0, lambda t: d0, dec=40)
    n = W * RPM; m = T > 0.8 * tf; nss = float(n[m].mean())
    out = np.where(np.abs(n - nss) > 0.02 * nss)[0]
    ts = float(T[out[-1] + 1]) if len(out) else 0.0
    Mp = float(max(n.max() / nss - 1, 0))
    return par, lab, dict(nss=nss, ts=ts, Mp=Mp, ipk=float(np.abs(I).max()), tf=tf)
if __name__ == '__main__':
    args = []
    for par, lv in levels.items():
        for (lab, val), e in zip(lv, R['sens'][par]):
            args.append((par, lab, val, e['sim']['ts']))
    with Pool(2) as pool:
        res = pool.map(caso, args)
    out = {}
    for par, lab, r in res:
        out.setdefault(par, []).append(dict(lab=lab, **r)); print(par, lab, {k: round(v, 4) for k, v in r.items()})
    json.dump(out, open('sens_trifasico.json', 'w'), indent=1)
