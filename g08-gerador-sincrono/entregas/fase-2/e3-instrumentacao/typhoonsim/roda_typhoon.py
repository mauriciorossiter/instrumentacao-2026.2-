# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E03 e E04: roda no TyphoonSim (offline) os ensaios do gabarito e exporta as
sondas em CSV (typhoonsim/dados/<ensaio>.csv). Para cada ensaio o modelo e' remontado com os estados iniciais,
os SCADA Inputs e os degraus temporizados daquele ensaio (monta_modelo.monta), compilado e simulado.
No fim, o instrumentacao_controle.tse volta ao estado padrao (E03, ensaio a, sem degrau temporizado).

Uso (TyphoonSim aberto):
    <python da API do Typhoon> roda_typhoon.py                (todos, ~20 ensaios)
    <python da API do Typhoon> roda_typhoon.py e03_a e04_real_r
A comparacao com o gabarito e' ../compara_typhoon.py (Python comum).
"""
import os
import sys
import time

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.path.insert(0, AQUI)
sys.dont_write_bytecode = True
import monta_modelo as MM      # noqa: E402
from ensaios_e34 import ENSAIOS  # noqa: E402

DADOS = os.path.join(AQUI, 'dados')


def roda(nome):
    ens, cfg = ENSAIOS[nome]
    MM.monta(tempo=ens['T'], ens=ens, cfg=cfg, compilar=False, fechar=False)
    MM.aplica_eventos(ens)
    if not model.compile():
        raise RuntimeError('nao compilou: ' + nome)
    model._start_offline_simulation()
    df = model._get_offline_simulation_results()
    model.close_model()
    if len(df) == 0:
        raise RuntimeError('simulacao sem dados (%s): o TyphoonSim esta aberto? licenca?' % nome)
    df.to_csv(os.path.join(DADOS, nome + '.csv'), index=False)
    return len(df)


if __name__ == '__main__':
    os.makedirs(DADOS, exist_ok=True)
    nomes = sys.argv[1:] or list(ENSAIOS)
    try:
        for nome in nomes:
            t0 = time.time()
            n = roda(nome)
            print('%-18s pontos=%7d  %.0f s' % (nome, n, time.time() - t0), flush=True)
    finally:
        MM.monta()          # deixa o .tse no estado padrao
