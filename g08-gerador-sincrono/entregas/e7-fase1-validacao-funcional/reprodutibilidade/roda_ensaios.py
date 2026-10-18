# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03
Roda os tres ensaios no modelo_e03.tse em simulacao OFFLINE (sem operador, para conferir
contra o gabarito): o disparo vem do degrau automatico em t = 1 s ('ens_t_auto'), janela de
3 s. Para cada ensaio, duas rodadas: camadas ligadas (completa) e desligadas (ideal da E01).
No fim, devolve o modelo aos valores do painel (disparo manual, 600 s) e recompila.

Uso (TyphoonSim + Schematic Editor abertos):
    <python com typhoon_hil_api> roda_ensaios.py            -> ../typhoonsim/dados/ensaio_<a|b|c>_<caso>.csv
    <python com typhoon_hil_api> roda_ensaios.py b          (so o ensaio b)
Depois:  python compara_ensaios.py
"""
import os
import sys

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import monta_modelo_e03 as M   # noqa: E402

DADOS = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'dados'))
os.makedirs(DADOS, exist_ok=True)
LETRA = {'a': 1, 'b': 2, 'c': 3}
CASOS = {'completa': (1, 1, 1), 'ideal': (0, 0, 0)}

if not os.path.exists(M.SAIDA):
    sys.exit('nao achei %s: rode antes monta_modelo_e03.py' % M.SAIDA)

letras = sys.argv[1:] or list(LETRA)
try:
    for letra in letras:
        for caso, cam in CASOS.items():
            model.load(M.SAIDA)
            M.aplica_ensaio_offline(LETRA[letra], cam)
            if not model.compile():
                raise RuntimeError('nao compilou: %s %s' % (letra, caso))
            model._start_offline_simulation()
            df = model._get_offline_simulation_results()
            arq = os.path.join(DADOS, 'ensaio_%s_%s.csv' % (letra, caso))
            df.to_csv(arq, index=False)
            print('ensaio (%s) %-8s camadas=%s  pontos=%d -> %s' % (letra, caso, cam, len(df), arq))
            model.close_model()
finally:
    # o .tse da entrega fica sempre com os valores do painel
    model.load(M.SAIDA)
    M.prepara_painel()
    model.save_as(M.SAIDA)
    print('modelo devolvido aos valores do painel | compilou =', model.compile())
    model.close_model()
