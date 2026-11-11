# -*- coding: utf-8 -*-
# Executa os ensaios no HIL virtual (VHIL), o mesmo motor usado pelo HIL SCADA, e captura os sinais.
# Uso: python rodar_vhil_e2.py <modelo.cpd> <pasta_saida> nome=ensaio,duracao_s[,chave:valor...] ...
import sys, os, time, pickle
import typhoon.api.hil as hil

cpd, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
PAD = dict(ensaio=1.0, degrau_pct=20.0, h_ini_m=1.0, amp_pct=10.0, A_m2=0.5, k_valvula=0.01, qd_Ls=0.0)
CH = ["h_m", "qi_Ls", "qo_Ls", "t_fisico_s"]
assert hil.load_model(file=cpd, vhil_device=True)
hil.start_simulation()
time.sleep(1.0)
for caso in sys.argv[3:]:
    nome, resto = caso.split("=", 1)
    partes = resto.split(",")
    vals = dict(PAD); vals["ensaio"] = float(partes[0]); dur = float(partes[1])
    for p in partes[2:]:
        k, v = p.split(":"); vals[k] = float(v)
    for k, v in vals.items():
        hil.set_scada_input_value(k, v)
    dec = int(sys.argv and os.environ.get("DEC", "50"))
    n = int(dur / (2e-5 * dec)); n += n % 2
    buf = []
    hil.start_capture([dec, len(CH), n], ["Forced"], [CH], dataBuffer=buf)
    # disparo: borda de subida zera o relogio do ensaio (pre-carga ate t_ev, depois o ensaio)
    hil.set_scada_input_value("disparo", 0.0); hil.set_scada_input_value("disparo", 1.0)
    t0 = time.time()
    while hil.capture_in_progress():
        time.sleep(0.2)
    hil.set_scada_input_value("disparo", 0.0)
    sig, y, t = buf[0]
    d = {"t": t, **{c: y[i] for i, c in enumerate(sig)}}
    pickle.dump(d, open(os.path.join(outdir, nome + ".pkl"), "wb"))
    # .npz alinhado no disparo (o relogio do ensaio zera na borda de 'disparo')
    import numpy as np
    d = {k: np.asarray(v, dtype=float) for k, v in d.items()}
    i0 = int(np.argmin(d["t_fisico_s"][:len(d["t_fisico_s"]) // 4 + 5]))
    np.savez(os.path.join(outdir, nome + ".npz"), **{k: v[i0:] for k, v in d.items()})
    print(nome, vals, f"{len(t)} amostras, {time.time()-t0:.1f}s de parede para {dur}s de circuito", flush=True)
hil.stop_simulation()
