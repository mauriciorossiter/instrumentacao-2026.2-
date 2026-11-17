# -*- coding: utf-8 -*-
# Executa ensaios no HIL virtual (VHIL), o mesmo motor do HIL SCADA, e grava cada um em .npz
# (alinhado no disparo: t_fisico_s = 0 no disparo; a preparacao dura ate 100 s e o ensaio comeca ai).
# Uso: python.exe rodar_vhil_dev.py <modelo.cpd> <pasta_saida> nome=ensaio,duracao_s[,chave:valor...] ...
#      chaves: entradas SCADA do modelo (degrau_pct, h_op_m, h_ini_m, amp_pct, w_rel, k_valvula, modelo_orif,
#      qd_Ls) e 'dec' (decimacao da captura; padrao 50 -> 1 ms de circuito = 0,1 s de tanque)
import os
import sys
import time

import numpy as np
import typhoon.api.hil as hil

cpd, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
PAD = dict(ensaio=1.0, degrau_pct=20.0, h_op_m=0.5, h_ini_m=1.0, amp_pct=10.0, w_rel=1.0, k_valvula=0.01,
           modelo_orif=0.0, qd_Ls=0.0)
CH = ["h_m", "qi_Ls", "qo_Ls", "e_nl_V", "t_fisico_s"]
assert hil.load_model(file=cpd, vhil_device=True)
hil.start_simulation()
time.sleep(0.5)
for caso in sys.argv[3:]:
    nome, resto = caso.split("=", 1)
    partes = resto.split(",")
    vals = dict(PAD); vals["ensaio"] = float(partes[0]); dur = float(partes[1]); dec = 50
    for p in partes[2:]:
        k, v = p.split(":")
        if k == "dec":
            dec = int(v)
        else:
            vals[k] = float(v)
    for k, v in vals.items():
        hil.set_scada_input_value(k, v)
    n = int(dur / (2e-5 * dec)); n += n % 2
    buf = []
    hil.set_scada_input_value("disparo", 0.0)
    time.sleep(0.05)
    hil.start_capture([dec, len(CH), n], ["Forced"], [CH], dataBuffer=buf)
    hil.set_scada_input_value("disparo", 1.0)
    t0 = time.time()
    while hil.capture_in_progress():
        time.sleep(0.1)
    hil.set_scada_input_value("disparo", 0.0)
    sig, y, t = buf[0]
    d = {c: np.asarray(y[i], dtype=float) for i, c in enumerate(sig)}
    tf = d["t_fisico_s"]
    i0 = int(np.argmin(tf[: len(tf) // 4 + 5]))          # amostra do disparo (relogio zerado)
    d = {k: v[i0:] for k, v in d.items()}
    np.savez(os.path.join(outdir, nome + ".npz"), dec=dec, **d)
    print(f"{nome}: {vals} | {len(tf)} amostras | {time.time() - t0:.1f} s de parede", flush=True)
hil.stop_simulation()
