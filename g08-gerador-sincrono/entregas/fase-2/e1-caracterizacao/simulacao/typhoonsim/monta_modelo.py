# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 01: a mesma planta no TyphoonSim (segunda ferramenta).

Monta, via API do Schematic Editor, o diagrama de blocos da Figura 1b com BLOCOS NATIVOS de
processamento de sinal (nenhuma C function), salva swing_equation.tse e compila:

    Pm(t)    = Pm0 + Step(t_degrau; 0 -> dPm)                 [Constant, Step, Sum]
    Pmax(t)  = Pmax * (1 - Step(t_f) + Step(t_f + t_c))       [Constant, Step x2, Sum, Product]
    Pe       = Pmax(t) * sen(delta)                           [Trigonometric function, Product]
    Pa       = Pm - Pe - D*dw                                 [Gain, Sum]
    dw       = Integrator( ws/2H * Pa )                       [Gain, Integrator]
    delta    = Integrator( dw + h * ws/2H * Pa )              [Gain, Sum, Integrator]

Discretizacao (h = 1 ms, taxa de execucao dos blocos). Medido nos dados (compara_typhoon.py): o
Integrator nativo e' um Euler progressivo, y[k+1] = y[k] + h*u[k], com saida = estado (sem passagem
direta). Ligar dw direto na entrada do integrador de delta daria um Euler explicito, que injeta
energia na oscilacao: amortecimento negativo de ~w^2 h/2 = 0,035 1/s, 18 % do sigma da planta. A
primeira versao deste modelo ainda tinha um Unit Delay nesse caminho, o que dobrou o efeito
(sigma medido 0,122 em vez de 0,189 1/s). A correcao entrega ao integrador de delta o valor JA
atualizado de dw, dw + h*(ws/2H)*Pa = dw[k+1], o que torna o par um Euler simpletico:
    dw[k+1]    = dw[k] + h*(ws/2H)*(Pm - Pmax*sen(delta[k]) - D*dw[k])
    delta[k+1] = delta[k] + h*dw[k+1]
Esse esquema nao cria nem destroi energia de oscilacao; o amortecimento fica so o fisico (D).

Os parametros vem de ../parametros.py, a mesma fonte do Python. O .tse sai configurado para o
ensaio (a); roda_typhoon.py muda as constantes de cada ensaio sem mexer na topologia.

Uso (TyphoonSim e Schematic Editor abertos; ver ../instrucoes.md):
    <python da API do Typhoon> monta_modelo.py
"""
import math
import os
import shutil
import sys

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.dont_write_bytecode = True
from parametros import W_S, H, D, PM0, P_MAX, DPM_DEGRAU, TY_PASSO, TY_T_DEGRAU, TY_T_POS_DEGRAU

TSE = os.path.join(AQUI, 'swing_equation.tse')
DT = repr(TY_PASSO)
SEM_FALTA = '1e6'          # s: instante "nunca" para os degraus da falta
SONDAS = ['delta_graus', 'delta_rad', 'delta_omega', 'Pe_pu', 'Pm_pu', 'Pmax_pu']


def limpa_target():
    """A compilacao gera '<modelo> Target files/' ao lado do .tse; nao faz parte da entrega."""
    shutil.rmtree(TSE.replace('.tse', ' Target files'), ignore_errors=True)


def configura(tempo):
    cfg = {'hil_device': 'HIL101', 'hil_configuration_id': '1',
           'simulation_method': 'exact', 'simulation_time_step': 'auto',
           'solver_type': 'DAE', 'integration_method': 'BDF',
           'max_sim_step': DT, 'init_sim_step': '1e-6', 'abs_tol': '1e-9', 'rel_tol': '1e-9',
           'simulation_time': repr(float(tempo))}
    for k, v in cfg.items():
        model.set_model_property_value(k, v)


def monta():
    model.create_new_model('swing_equation')

    def novo(tipo, nome, pos, **props):
        c = model.create_component(tipo, name=nome)
        for k, v in props.items():
            model.set_property_value(model.prop(c, k), v)
        model.set_position(c, pos)
        return c

    T = model.term
    lig = model.create_connection
    sp = dict(execution_rate=DT)
    d0 = math.asin(PM0/P_MAX)

    # ------------------------------------------------ entrada Pm(t) = Pm0 + degrau
    pm0 = novo('core/Constant', 'Pm0', (7600, 7700), value=repr(PM0), **sp)
    deg = novo('core/Step', 'degrau_dPm', (7600, 7780), step_time=repr(TY_T_DEGRAU),
               initial_value='0.0', final_value=repr(DPM_DEGRAU), **sp)
    pm = novo('core/Sum', 'Pm', (7720, 7740), signs='++', **sp)
    lig(T(pm0, 'out'), T(pm, 'in')); lig(T(deg, 'out'), T(pm, 'in1'))

    # ------------------------------------------------ disturbio: Pmax(t) (falta franca -> Pe = 0)
    pmax = novo('core/Constant', 'Pmax', (7600, 8000), value=repr(P_MAX), **sp)
    um = novo('core/Constant', 'um', (7600, 8080), value='1.0', **sp)
    f_ini = novo('core/Step', 'falta_inicio', (7600, 8140), step_time=SEM_FALTA,
                 initial_value='0.0', final_value='1.0', **sp)
    f_fim = novo('core/Step', 'falta_fim', (7600, 8200), step_time=SEM_FALTA,
                 initial_value='0.0', final_value='1.0', **sp)
    rede = novo('core/Sum', 'rede_1_menos_falta', (7720, 8140), signs='+-+', **sp)
    pmax_t = novo('core/Product', 'Pmax_t', (7840, 8040), **sp)
    lig(T(um, 'out'), T(rede, 'in')); lig(T(f_ini, 'out'), T(rede, 'in1')); lig(T(f_fim, 'out'), T(rede, 'in2'))
    lig(T(pmax, 'out'), T(pmax_t, 'in')); lig(T(rede, 'out'), T(pmax_t, 'in1'))

    # ------------------------------------------------ malha da swing equation
    sen = novo('core/Trigonometric function', 'sen_delta', (8360, 8000), trigonometric_fn='sin',
               angle='Radians', **sp)
    pe = novo('core/Product', 'Pe', (8000, 7960), **sp)
    g_d = novo('core/Gain', 'D_vezes_dw', (8000, 7860), gain=repr(D), **sp)
    pa = novo('core/Sum', 'Pa', (8000, 7740), signs='+--', **sp)
    g_k = novo('core/Gain', 'ws_sobre_2H', (8120, 7740), gain=repr(W_S/(2*H)), **sp)
    i_w = novo('core/Integrator', 'integ_dw', (8240, 7740), init_value='0.0', **sp)
    g_h = novo('core/Gain', 'vezes_h', (8240, 7640), gain=DT, **sp)
    prox = novo('core/Sum', 'dw_proximo', (8360, 7740), signs='++', **sp)
    i_d = novo('core/Integrator', 'integ_delta', (8480, 7740), init_value=repr(d0), **sp)
    graus = novo('core/Gain', 'rad_para_graus', (8600, 7740), gain=repr(180.0/math.pi), **sp)
    lig(T(pm, 'out'), T(pa, 'in')); lig(T(pe, 'out'), T(pa, 'in1')); lig(T(g_d, 'out'), T(pa, 'in2'))
    lig(T(pa, 'out'), T(g_k, 'in')); lig(T(g_k, 'out'), T(i_w, 'in')); lig(T(g_k, 'out'), T(g_h, 'in'))
    lig(T(i_w, 'out'), T(prox, 'in')); lig(T(g_h, 'out'), T(prox, 'in1'))
    lig(T(prox, 'out'), T(i_d, 'in')); lig(T(i_w, 'out'), T(g_d, 'in'))
    lig(T(i_d, 'out'), T(sen, 'in')); lig(T(pmax_t, 'out'), T(pe, 'in')); lig(T(sen, 'out'), T(pe, 'in1'))
    lig(T(i_d, 'out'), T(graus, 'in'))

    # ------------------------------------------------ sondas e scope
    for nome, origem, pos in (('delta_graus', T(graus, 'out'), (8720, 7740)),
                              ('delta_rad', T(i_d, 'out'), (8600, 7660)),
                              ('delta_omega', T(i_w, 'out'), (8300, 7840)),
                              ('Pe_pu', T(pe, 'out'), (8000, 8060)),
                              ('Pm_pu', T(pm, 'out'), (7720, 7660)),
                              ('Pmax_pu', T(pmax_t, 'out'), (7840, 8120))):
        lig(origem, T(novo('core/Probe', nome, pos), 'in'))
    novo('core/Scope', 'Scope_swing', (8720, 7880), selected_signals=SONDAS)

    configura(TY_T_DEGRAU + TY_T_POS_DEGRAU)
    model.save_as(TSE)
    ok = model.compile()
    model.close_model()
    limpa_target()
    return ok


if __name__ == '__main__':
    print('modelo salvo em %s | compilou = %s' % (TSE, monta()))
