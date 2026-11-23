# -*- coding: utf-8 -*-
"""
Compila (gcc) o codigo C de todos os blocos C function de um modelo.tse e roda a malha
completa em C (planta e piezo integrados por Euler, como no gemeo), para conferir:
  1) que o codigo C dos blocos compila sem erro;
  2) que o resultado bate com o gemeo numerico (gemeo.py).
Uso: python testar_cfun.py <modelo.tse> <pasta_trabalho>
"""
import re, sys, os, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeo import Param, simular, metricas

tse, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
txt = open(tse, encoding="utf-8").read()


def unq(s):
    return s.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


blocos = {}
for m in re.finditer(r'component "core/C function" (\S+) \{(.*?)\n        \}', txt, re.S):
    nome, body = m.group(1), m.group(2) + "\n"
    get = lambda k: unq(re.search(k + r' = "(.*?)(?<!\\)"\n', body, re.S).group(1))
    ins = re.findall(r"real (\w+);", get("input_terminals"))
    outs = re.findall(r"real (\w+);", get("output_terminals"))
    strip = lambda c: c.replace("/*Begin code section*/", "").replace("/*End code section*/", "")
    blocos[nome] = dict(ins=ins, outs=outs, glob=strip(get("arb_defs")), init=strip(get("init_fnc")),
                        out=strip(get("output_fnc")), upd=strip(get("update_fnc")))

C = ["#include <math.h>", "#include <stdio.h>", ""]
for n, b in blocos.items():
    C.append(f"/* ===== {n} ===== */")
    C.append(b["glob"])
    sig = ", ".join([f"double {i}" for i in b["ins"]] + [f"double *o_{o}" for o in b["outs"]])
    loc = "".join(f"double {o} = *o_{o}; " for o in b["outs"])
    back = "".join(f"*o_{o} = {o}; " for o in b["outs"])
    C.append(f"void {n}_init(void) {{ {b['init']} }}")
    C.append(f"void {n}_out({sig}) {{ {loc}\n{b['out']}\n{back} }}")
    C.append(f"void {n}_upd({sig}) {{ {loc}\n{b['upd']}\n{back} }}")
    C.append("")

MAIN = r"""
int main(int argc, char **argv) {
    /* entradas SCADA: cenario 4 da Entrega Final (real + calibracao + correcao, corretor em 1 Hz) */
    double ensaio = 1, amplitude = 10, disparo = 0, malha = 1, Kp = 2, Ki = 10, Kd = 0.2, seletor = atof(argv[1]);
    double chop = 1, en_sens = 1, S_real = 24.6, en_lim = 1, en_res = 1, en_ruido = 1, sigma = 20, en_interf = 1;
    double fc = 1.0, comp_cal = atof(argv[2]), S_cal = 24.6, comp_din = atof(argv[3]), fc_corr = 1.0, f_f = 10.0;
    double r = 0, d = 0, tens = 0, u = 0, F = 0, car = 0, vctrl = 0, F_inst = 0, n = 0, interf = 0;
    double pre = 0, dem = 0, bw = 0, ymed = 0, yctrl = 0;
    double x = 0, v = 0, vct = 0, TS = 1e-4;
    int i, N = 40000;
    gerador_ensaios_init(); controlador_PID_init(); portadora_chopper_init(); sensor_piezo_init();
    ruido_branco_init(); interferencia_init(); condicionamento_lockin_init(); processamento_compensacao_init();
    seletor_ideal_real_init();
    for (i = 0; i < N; i++) {
        double yreal = 100.0 * x, vpz;
        gerador_ensaios_out(ensaio, amplitude, disparo, &r, &d, &tens);
        portadora_chopper_out(chop, &car);
        sensor_piezo_out(yreal, car, en_sens, S_real, en_lim, en_res, &vctrl, &F_inst);
        vpz = vctrl - vct;
        ruido_branco_out(en_ruido, sigma, &n);
        interferencia_out(en_interf, &interf);
        condicionamento_lockin_out(vpz, n, interf, car, fc, &pre, &dem, &bw);
        processamento_compensacao_out(bw, comp_cal, S_cal, comp_din, fc_corr, f_f, &ymed);
        seletor_ideal_real_out(ymed, yreal, seletor, &yctrl);
        controlador_PID_out(r, yctrl, d, malha, Kp, Ki, Kd, disparo, &u, &F);
        if (i % 20 == 0) printf("%.4f,%.6f,%.6f,%.6f,%.6f\n", i * TS, r, yreal, ymed, u);
        /* updates */
        gerador_ensaios_upd(ensaio, amplitude, disparo, &r, &d, &tens);
        portadora_chopper_upd(chop, &car);
        sensor_piezo_upd(yreal, car, en_sens, S_real, en_lim, en_res, &vctrl, &F_inst);
        ruido_branco_upd(en_ruido, sigma, &n);
        interferencia_upd(en_interf, &interf);
        condicionamento_lockin_upd(vpz, n, interf, car, fc, &pre, &dem, &bw);
        processamento_compensacao_upd(bw, comp_cal, S_cal, comp_din, fc_corr, f_f, &ymed);
        seletor_ideal_real_upd(ymed, yreal, seletor, &yctrl);
        controlador_PID_upd(r, yctrl, d, malha, Kp, Ki, Kd, disparo, &u, &F);
        { double a = (F - 6.0 * v - 100.0 * x) / 1.0; v += a * TS; x += v * TS; }
        vct += (vpz / 10e6) / 10e-9 * TS;
    }
    return 0;
}
"""
C.append("#include <stdlib.h>")
C.append(MAIN)
src = os.path.join(work, "blocos.c")
open(src, "w", encoding="utf-8").write("\n".join(C))
exe = os.path.join(work, "blocos.exe")
cp = subprocess.run(["gcc", "-std=c99", "-Wall", "-Wno-unused-variable", "-Wno-unused-but-set-variable", "-O2",
                     src, "-o", exe, "-lm"], capture_output=True, text=True)
print("gcc:", "OK" if cp.returncode == 0 else "FALHOU")
if cp.stderr.strip():
    print(cp.stderr[:3000])
if cp.returncode:
    sys.exit(1)
for sel, cal, din in ((0, 0, 0), (1, 0, 0), (1, 1, 1)):
    out = subprocess.run([exe, str(sel), str(cal), str(din)], capture_output=True, text=True).stdout
    a = np.array([[float(v) for v in l.split(",")] for l in out.strip().splitlines()])
    p = Param(seletor=sel, comp_cal=cal, comp_din=din, T=4.0, t_ev=2.0)
    g = simular(p, dec=20)
    nmin = min(len(a), len(g["t"]))
    dx = np.max(np.abs(a[:nmin, 2] - g["y_real"][:nmin]))
    du = np.max(np.abs(a[:nmin, 4] - g["u"][:nmin]))
    print(f"seletor={sel} cal={cal} din={din}: max|dx| = {dx:.2e} cm, max|du| = {du:.2e} N, "
          f"x final C = {a[-1,2]:.3f}, gemeo = {g['y_real'][nmin-1]:.3f}")
