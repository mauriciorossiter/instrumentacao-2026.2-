# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 01
Roda o modelo TyphoonSim (simulacao offline) e exporta os sinais das sondas em CSV.

Uso (com o Typhoon HIL Control Center / TyphoonSim ABERTO):
    <python com typhoon_hil_api> roda_typhoon.py
Gera:
    ../typhoonsim/dados/varredura_cabo_nominal.csv   (R_cabo = 50 ohm, modelo.tse como salvo)
    ../typhoonsim/dados/varredura_cabo_maximo.csv    (R_cabo = 550 ohm, alterado so em memoria)
A analise e as figuras ficam em analisa_typhoon.py (Python comum, com matplotlib).
"""
import os
import sys

from typhoon.api.schematic_editor import model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parametros as P

AQUI = os.path.dirname(os.path.abspath(__file__))
TSE = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'modelo.tse'))
DADOS = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'dados'))
os.makedirs(DADOS, exist_ok=True)

CASOS = [
    ('varredura_cabo_nominal', P.R_CABO),
    ('varredura_cabo_maximo', P.R_CABO_TESTE),
]

# Modo so-exportar (experimental): depois de rodar a simulacao pela INTERFACE do TyphoonSim,
#   <python da API> roda_typhoon.py --so-exportar varredura_cabo_nominal
# tenta ler os resultados da ultima simulacao offline, sem iniciar outra.
# Observacao: neste Windows, a simulacao iniciada pela API travou apos "Simulation ready!"
# (o mesmo aconteceu em 22/08); pela interface ela roda normalmente.
if len(sys.argv) == 3 and sys.argv[1] == '--so-exportar':
    df = model._get_offline_simulation_results()
    df.to_csv(os.path.join(DADOS, sys.argv[2] + '.csv'), index=False)
    print('exportado %s: pontos=%d colunas=%s' % (sys.argv[2], len(df), list(df.columns)))
    sys.exit(0)

for nome, r_cabo in CASOS:
    model.load(TSE)
    rc = model.get_item('R_cabo')
    model.set_property_value(model.prop(rc, 'resistance'), str(r_cabo))
    if not model.compile():
        raise RuntimeError('nao compilou: ' + nome)
    model._start_offline_simulation()
    df = model._get_offline_simulation_results()
    df.to_csv(os.path.join(DADOS, nome + '.csv'), index=False)
    print('%-26s R_cabo=%6.1f ohm  pontos=%d  colunas=%s'
          % (nome, r_cabo, len(df), list(df.columns)))
    model.close_model()
