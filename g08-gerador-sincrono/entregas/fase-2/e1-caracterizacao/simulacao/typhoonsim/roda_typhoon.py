# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 01: roda os ensaios no TyphoonSim (simulacao offline) e
exporta as sondas em CSV. Entre um ensaio e outro so mudam constantes (condicao inicial do
integrador de delta, degrau de Pm, instantes da falta, tempo de simulacao); a topologia e' a do
swing_equation.tse gerado por monta_modelo.py.

Uso (TyphoonSim e SCHEMATIC EDITOR abertos; sem o Schematic Editor a simulacao pela API nao
produz dados):
    <python da API do Typhoon> roda_typhoon.py              (todos os ensaios)
    <python da API do Typhoon> roda_typhoon.py ensaio_a_degrau
Gera dados/<ensaio>.csv com as colunas Time, delta_graus, delta_rad, delta_omega, Pe_pu, Pm_pu, Pmax_pu.
A comparacao com o Python fica em ../compara_typhoon.py (Python comum).
"""
import math
import os
import sys
import time

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.dont_write_bytecode = True
from parametros import (PM0, P_MAX, DPM_DEGRAU, DELTA_CI_GR, T_INICIO_FALTA, TY_T_DEGRAU,
                        TY_T_POS_DEGRAU, TY_T_CI, TY_T_FALTA, TY_DURACOES_FALTA)
import monta_modelo as MM

DADOS = os.path.join(AQUI, 'dados')
D0 = math.asin(PM0/P_MAX)

# ensaio: (delta(0) [rad], degrau de Pm [pu], inicio da falta [s] ou None, duracao [s], tempo [s])
ENSAIOS = {
    'ensaio_a_degrau': (D0, DPM_DEGRAU, None, 0.0, TY_T_DEGRAU + TY_T_POS_DEGRAU),
    'ensaio_b_condicao_inicial': (math.radians(DELTA_CI_GR), 0.0, None, 0.0, TY_T_CI),
}
for tc in TY_DURACOES_FALTA:
    ENSAIOS['ensaio_c_falta_%03dms' % round(1000*tc)] = (D0, 0.0, T_INICIO_FALTA, tc, TY_T_FALTA)


def aplica(delta0, dpm, t_falta, t_c, tempo):
    """Com o modelo carregado, ajusta as constantes do ensaio."""
    def prop(nome, chave, valor):
        model.set_property_value(model.prop(model.get_item(nome), chave), valor)
    prop('integ_delta', 'init_value', repr(float(delta0)))
    prop('degrau_dPm', 'final_value', repr(float(dpm)))
    prop('falta_inicio', 'step_time', MM.SEM_FALTA if t_falta is None else repr(t_falta))
    prop('falta_fim', 'step_time', MM.SEM_FALTA if t_falta is None else repr(t_falta + t_c))
    MM.configura(tempo)


if __name__ == '__main__':
    os.makedirs(DADOS, exist_ok=True)
    nomes = sys.argv[1:] or list(ENSAIOS)
    try:
        for nome in nomes:
            t0 = time.time()
            model.load(MM.TSE)
            aplica(*ENSAIOS[nome])
            if not model.compile():
                raise RuntimeError('nao compilou: ' + nome)
            model._start_offline_simulation()
            df = model._get_offline_simulation_results()
            model.close_model()
            if len(df) == 0:
                raise RuntimeError('simulacao sem dados (%s): o Schematic Editor esta aberto?' % nome)
            df.to_csv(os.path.join(DADOS, nome + '.csv'), index=False)
            print('%-30s pontos=%6d  %.0f s' % (nome, len(df), time.time() - t0), flush=True)
    finally:
        MM.limpa_target()
