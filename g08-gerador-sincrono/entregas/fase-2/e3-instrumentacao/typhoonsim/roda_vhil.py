# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E03 e E04: roda os ensaios do gabarito no Virtual HIL (VHIL) e captura as sondas.

Substitui o roda_typhoon.py quando a simulacao offline do TyphoonSim nao tem licenca. Para cada ensaio, o
modelo e' remontado com os estados iniciais, os SCADA Inputs e os degraus temporizados daquele ensaio
(monta_modelo.monta + aplica_eventos), compilado, carregado no VHIL e simulado; a captura comeca logo depois
do Start (perde so' as primeiras dezenas de ms; os eventos sao em t = 1 s). A coluna Time e' o tempo de
simulacao estimado; o compara_typhoon.py refina o alinhamento pelo canal V_ideal (sem ruido).

Uso (Schematic Editor aberto, HIL SCADA fechado):
    <python da API> roda_vhil.py                  (todos)
    <python da API> roda_vhil.py e03_a e04_real_r
Saida: dados/<ensaio>.csv
"""
import inspect
import os
import sys
import time

from typhoon.api.schematic_editor import model
import typhoon.api.hil as hil
from typhoon.test import capture as CAP

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.path.insert(0, AQUI)
sys.dont_write_bytecode = True
import monta_modelo as MM        # noqa: E402
from ensaios_e34 import ENSAIOS  # noqa: E402

DADOS = os.path.join(AQUI, 'dados')
CPD = os.path.join(AQUI, 'instrumentacao_controle Target files', 'instrumentacao_controle.cpd')
TAXA = 2000.0                    # amostras/s (a medicao e o controle rodam a 100 us)


def resultados_captura(duracao):
    if hasattr(CAP, 'wait_capture_finish'):
        try:
            CAP.wait_capture_finish(timeout=20*duracao + 120)
        except TypeError:
            CAP.wait_capture_finish()
    params = inspect.signature(CAP.get_capture_results).parameters
    kw = {k: True for k in ('wait_capture', 'wait_capture_finish') if k in params}
    df = CAP.get_capture_results(**kw)
    if isinstance(df, dict):
        import pandas as pd
        df = pd.DataFrame(df)
    return df


def roda(nome):
    ens, cfg = ENSAIOS[nome]
    t0 = time.time()
    MM.monta(tempo=ens['T'] + 5.0, ens=ens, cfg=cfg, compilar=False, fechar=False)
    MM.aplica_eventos(ens)
    if not model.compile():
        raise RuntimeError('nao compilou: ' + nome)
    model.close_model()
    if not hil.load_model(file=CPD, vhil_device=True):
        raise RuntimeError('o VHIL nao carregou ' + CPD)
    hil.start_simulation()
    try:
        t_ini = hil.get_sim_time()
        CAP.start_capture(duration=ens['T'], rate=TAXA, signals=MM.SONDAS)
        df = resultados_captura(ens['T'])
    finally:
        hil.stop_simulation()
    df = df.reset_index()
    col_t = df.columns[0]
    t = df[col_t]
    t = t.dt.total_seconds() if hasattr(t, 'dt') else t.astype(float)
    df = df.drop(columns=[col_t])
    df.insert(0, 'Time', t + t_ini)
    df.to_csv(os.path.join(DADOS, nome + '.csv'), index=False)
    print('%-18s pontos=%7d  T=%.1f s  %.0f s' % (nome, len(df), ens['T'], time.time() - t0), flush=True)


if __name__ == '__main__':
    os.makedirs(DADOS, exist_ok=True)
    nomes = sys.argv[1:] or [n for n in ENSAIOS if n.startswith('e03_')]   # so' os desta entrega
    try:
        for nome in nomes:
            roda(nome)
    finally:
        # deixa o .tse no estado padrao (E03, malha aberta, cadeia real) e compilado, pronto para o SCADA
        MM.monta(compilar=False, fechar=False)
        model.compile()
        model.close_model()
        print('modelo devolvido ao estado padrao e recompilado', flush=True)
