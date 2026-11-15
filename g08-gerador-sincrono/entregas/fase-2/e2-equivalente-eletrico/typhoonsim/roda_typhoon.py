# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: roda no TyphoonSim (offline) os ensaios da E01 sobre o
equivalente eletrico e os niveis de sensibilidade de D e X, exportando as sondas em CSV.

Entre um ensaio e outro so mudam valores (tensao inicial do capacitor, degrau temporizado, instantes
da falta, valores padrao dos SCADA Inputs); a topologia e' a do equivalente_eletrico.tse.

Uso (TyphoonSim aberto):
    <python da API do Typhoon> roda_typhoon.py                 (todos)
    <python da API do Typhoon> roda_typhoon.py ensaio_a_degrau (um so)
Saida: dados/<ensaio>.csv com Time e as sondas (delta_graus, delta_omega, Pe_pu, Pm_pu, i_A, vC_V,
vnl_V, Vm_V). A comparacao com a E01 e' feita por ../compara_typhoon.py (Python comum).
"""
import math
import os
import sys
import time

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.dont_write_bytecode = True
import parametros_e02 as P      # noqa: E402
import monta_modelo as MM       # noqa: E402

DADOS = os.path.join(AQUI, 'dados')
T_DEG = 1.0                      # s, instante do degrau temporizado (equilibrio antes dele)


def vc0(delta_graus):
    return (math.radians(delta_graus) - P.DELTA0)*P.KV_DELTA


# nome: dict(vC0 [V], t_degrau [s] ou None, falta (t_ini, duracao) ou None, D, X, tempo [s])
ENSAIOS = {
    'ensaio_a_degrau': dict(vC0=0.0, t_deg=T_DEG, falta=None, D=P.D, X=P.X_TOT, tempo=T_DEG + 60.0),
    'ensaio_b_condicao_inicial': dict(vC0=vc0(P.DELTA_CI_GR), t_deg=None, falta=None, D=P.D, X=P.X_TOT, tempo=30.0),
}
for tc in (0.20, 0.27, 0.287, 0.288, 0.29):
    ENSAIOS['ensaio_c_falta_%03dms' % round(1000*tc)] = dict(vC0=0.0, t_deg=None, falta=(P.T_INICIO_FALTA, tc),
                                                            D=P.D, X=P.X_TOT, tempo=2.6)
for nd in (0.0, 0.1, 0.441, 1.0):                      # R4: D (resistor variavel, SCADA)
    ENSAIOS['sens_D_%s' % repr(nd)] = dict(vC0=0.0, t_deg=T_DEG, falta=None, D=nd, X=P.X_TOT, tempo=T_DEG + 40.0)
for nx in (0.30, 0.45, 0.90, 1.20):                    # R4: X (Pmax no bloco de sinal, SCADA)
    ENSAIOS['sens_X_%s' % repr(nx)] = dict(vC0=0.0, t_deg=80.0, falta=None, D=P.D, X=nx, tempo=80.0 + 40.0)


def aplica(e):
    def prop(nome, chave, valor):
        model.set_property_value(model.prop(model.get_item(nome), chave), valor)
    prop('C_sincron', 'initial_voltage', repr(float(e['vC0'])))
    prop('degrau_temporizado', 'step_time', MM.NUNCA if e['t_deg'] is None else repr(e['t_deg']))
    if e['falta'] is None:
        prop('falta_inicio', 'step_time', MM.NUNCA); prop('falta_fim', 'step_time', MM.NUNCA)
    else:
        ti, tc = e['falta']
        prop('falta_inicio', 'step_time', repr(ti)); prop('falta_fim', 'step_time', repr(ti + tc))
    prop('D', 'def_value', repr(float(e['D'])))
    prop('X', 'def_value', repr(float(e['X'])))
    MM.configura(e['tempo'])


if __name__ == '__main__':
    os.makedirs(DADOS, exist_ok=True)
    nomes = sys.argv[1:] or list(ENSAIOS)
    try:
        for nome in nomes:
            t0 = time.time()
            model.load(MM.TSE)
            aplica(ENSAIOS[nome])
            if not model.compile():
                raise RuntimeError('nao compilou: ' + nome)
            model._start_offline_simulation()
            df = model._get_offline_simulation_results()
            model.close_model()
            if len(df) == 0:
                raise RuntimeError('simulacao sem dados (%s): o TyphoonSim esta aberto? licenca?' % nome)
            df.to_csv(os.path.join(DADOS, nome + '.csv'), index=False)
            print('%-30s pontos=%7d  %.0f s' % (nome, len(df), time.time() - t0), flush=True)
    finally:
        MM.limpa_target()
