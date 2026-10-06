# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Roda os modelos TyphoonSim (simulacao offline), um caso de camadas por vez, e exporta os
sinais das sondas em CSV. Entre um caso e outro so mudam as flags/constantes das camadas
(monta_modelo.aplica_caso: as constantes folga_b, res_liga e ruido_liga dos blocos nativos);
a topologia e o circuito sao os mesmos.

Uso (com o TyphoonSim e o SCHEMATIC EDITOR abertos - sem ele a API trava em
"Simulation ready!", ver ../typhoonsim/instrucoes.md):
    <python com typhoon_hil_api> monta_modelo.py      (uma vez: gera os .tse)
    <python com typhoon_hil_api> roda_typhoon.py
Gera em ../typhoonsim/dados/:
    varredura_ideal.csv       camadas desligadas (deve repetir a Entrega 01)
    varredura_estatica.csv    folga + resolucao (R6)
    varredura_espectral.csv   ruido de contato 1/f (R8)
    varredura_completa.csv    as tres camadas (R10)
    varredura_r8_sem_buffer.csv, varredura_r8_sem_buffer_sem_ruido.csv
                              contrafactual R8 (so se modelo_r8_sem_buffer.tse existir)
A analise fica em analisa_typhoon.py (Python comum).

Rodar so alguns casos:  roda_typhoon.py completa r8_sem_buffer
"""
import os
import sys

from typhoon.api.schematic_editor import model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monta_modelo as M

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'dados'))
os.makedirs(DADOS, exist_ok=True)

casos = sys.argv[1:] or (list(M.FLAGS) + list(M.FLAGS_R8))

# versao alternativa (camadas em C function): G08_MODELO=c roda_typhoon.py
#   -> usa ../typhoonsim/alternativa_c_function/modelo_c_function.tse e grava os CSV em
#      ../typhoonsim/alternativa_c_function/dados/ (o contrafactual R8 so existe na versao nativa)
if os.environ.get('G08_MODELO') == 'c':
    M.SAIDA = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'alternativa_c_function', 'modelo_c_function.tse'))
    DADOS = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'alternativa_c_function', 'dados'))
    os.makedirs(DADOS, exist_ok=True)
    casos = [c for c in casos if c in M.FLAGS]

for caso in casos:
    r8 = caso in M.FLAGS_R8
    tse = M.SAIDA_R8 if r8 else M.SAIDA
    if not os.path.exists(tse):
        print('%-26s pulado: %s nao existe' % (caso, os.path.basename(tse)))
        continue
    model.load(tse)
    modo = M.modo_salvo()
    M.aplica_caso(caso, modo)
    if not model.compile():
        raise RuntimeError('nao compilou: ' + caso)
    model._start_offline_simulation()
    df = model._get_offline_simulation_results()
    df.to_csv(os.path.join(DADOS, 'varredura_%s.csv' % caso), index=False)
    flags = M.FLAGS.get(caso) or M.FLAGS_R8[caso]
    print('%-26s modo=%-20s flags=%s  pontos=%d' % (caso, modo, flags, len(df)))
    model.close_model()
