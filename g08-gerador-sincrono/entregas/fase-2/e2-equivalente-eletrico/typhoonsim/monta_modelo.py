# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: monta o equivalente eletrico no TyphoonSim pela API.

Estagio de potencia (biblioteca nativa, malha unica):
    V_m (Signal Controlled Voltage Source)  ->  I_dw (Current Measurement)  ->  L_inercia (Inductor)
    ->  R_amortec (Variable Resistor)  ->  C_sincron (Capacitor)  ->  v_nl (Signal Controlled Voltage
    Source)  ->  terra.   V_vC (Voltage Measurement) le a tensao do capacitor.
Blocos de sinal (nativos, 20 us), so' para o que a biblioteca nao tem como elemento de circuito:
    delta = delta0 + v_C/(KV*Ks);  v_nl = KV*Pmax(t)*sen(delta) - v_C;  Pmax = E'V/X (X do SCADA);
    R = KV*D/KI (D do SCADA);  V_m = KV*(Pm0 + dPm*(degrau));  falta: Pmax(t) = 0.
Nenhuma C function.

O Variable Resistor nativo tem uma indutancia serie interna (propriedade 'inductance', 1 mH de
fabrica). Ela fica em serie com L_inercia; por isso L_inercia = L_EQ - L_VARRES, e a soma e' L_EQ.

Uso (TyphoonSim aberto; ver ../../instrucoes.md):
    <python da API do Typhoon> monta_modelo.py
"""
import math
import os
import shutil
import sys

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.dont_write_bytecode = True
import parametros_e02 as P   # noqa: E402

TSE = os.path.join(AQUI, 'equivalente_eletrico.tse')
DT = repr(P.TS_SP)
L_VARRES = 1e-3                     # H, indutancia interna do Variable Resistor (valor de fabrica)
NUNCA = '1e6'                       # s, instante "nunca" dos degraus temporizados
SONDAS = ['delta_graus', 'delta_omega', 'Pe_pu', 'Pm_pu', 'i_A', 'vC_V', 'vnl_V', 'Vm_V']
# SCADA Inputs: nome -> (valor padrao, minimo, maximo, unidade)
SCADA = {
    'Pm0': (P.PM0, 0.0, 1.5, 'pu'),
    'dPm': (P.DPM_DEGRAU, -0.5, 0.9, 'pu'),
    'degrau': (0.0, 0.0, 1.0, '0/1'),
    'D': (P.D, 0.0, 2.0, 'pu/(rad/s)'),
    'X': (P.X_TOT, 0.25, 2.0, 'pu'),
    'falta': (0.0, 0.0, 1.0, '0/1'),
}


def limpa_target():
    shutil.rmtree(TSE.replace('.tse', ' Target files'), ignore_errors=True)


def configura(tempo):
    cfg = {'hil_device': 'HIL101', 'hil_configuration_id': '1',
           'simulation_method': 'exact', 'simulation_time_step': 'auto',
           'solver_type': 'DAE', 'integration_method': 'BDF',
           'max_sim_step': DT, 'init_sim_step': '1e-6', 'abs_tol': '1e-9', 'rel_tol': '1e-9',
           'simulation_time': repr(float(tempo))}
    for k, v in cfg.items():
        try:
            model.set_model_property_value(k, v)
        except Exception as e:                       # noqa: BLE001
            print('   (aviso) %s: %s' % (k, e))


def monta(tempo=121.0):
    model.create_new_model('equivalente_eletrico')

    def novo(tipo, nome, pos, rot=None, **props):
        c = model.create_component(tipo, name=nome)
        for k, v in props.items():
            model.set_property_value(model.prop(c, k), v)
        model.set_position(c, pos)
        if rot:
            model.set_rotation(c, rot)
        return c

    def jun(nome, pos):
        j = model.create_junction(name=nome, kind='pe')
        model.set_position(j, pos)
        return j

    T = model.term
    lig = model.create_connection
    sp = dict(execution_rate=DT)

    # ================================================= estagio de potencia (malha unica)
    # Signal Controlled Voltage Source (o mesmo bloco de v_nl): na 2026.2, a 'Voltage Source' com
    # sig_input='True' compilou como fonte constante de 0 V e ignorou o sinal de Pm.
    vm = novo('core/Signal Controlled Voltage Source', 'V_m', (7600, 8300), rot='right')
    idw = novo('core/Current Measurement', 'I_dw', (7720, 8160), sig_output='True', execution_rate=DT)
    lin = novo('core/Inductor', 'L_inercia', (7860, 8160), inductance=repr(P.L_EQ - L_VARRES),
               initial_current='0.0')
    rv = novo('core/Variable Resistor', 'R_amortec', (8000, 8160), inductance=repr(L_VARRES))
    cap = novo('core/Capacitor', 'C_sincron', (8140, 8260), rot='right', capacitance=repr(P.C_EQ),
               initial_voltage='0.0')
    fnl = novo('core/Signal Controlled Voltage Source', 'v_nl', (8140, 8420), rot='right')
    vvc = novo('core/Voltage Measurement', 'V_vC', (8260, 8260), rot='right', sig_output='True',
               execution_rate=DT)
    gnd = novo('core/Ground', 'terra', (7600, 8540))
    j1, j2, j3, j4, j5 = (jun('no_topo', (8140, 8160)), jun('no_meio', (8140, 8340)),
                          jun('no_vC_topo', (8260, 8160)), jun('no_vC_baixo', (8260, 8340)),
                          jun('no_terra', (7600, 8500)))
    lig(T(vm, 'p_node'), T(idw, 'p_node'))
    lig(T(idw, 'n_node'), T(lin, 'p_node'))
    lig(T(lin, 'n_node'), T(rv, 'p_node'))
    lig(T(rv, 'n_node'), j1)
    lig(j1, T(cap, 'p_node')); lig(j1, j3); lig(j3, T(vvc, 'p_node'))
    lig(T(cap, 'n_node'), j2); lig(j2, j4); lig(j4, T(vvc, 'n_node'))
    lig(j2, T(fnl, 'p_node'))
    lig(T(fnl, 'n_node'), j5); lig(T(vm, 'n_node'), j5); lig(T(gnd, 'node'), j5)

    # ================================================= SCADA Inputs
    sc = {}
    for k, (nome, (v, lo, hi, un)) in enumerate(SCADA.items()):
        sc[nome] = novo('core/SCADA Input', nome, (7300, 7600 + 70*k), def_value=repr(float(v)),
                        min=repr(float(lo)), max=repr(float(hi)), unit=un, **sp)

    # ================================================= entrada: V_m = KV*(Pm0 + dPm*(degrau + Step))
    st = novo('core/Step', 'degrau_temporizado', (7300, 8100), step_time=NUNCA, initial_value='0.0',
              final_value='1.0', **sp)
    s_dg = novo('core/Sum', 'degrau_total', (7420, 7700), signs='++', **sp)
    p_dg = novo('core/Product', 'dPm_x_degrau', (7520, 7680), **sp)
    s_pm = novo('core/Sum', 'Pm', (7620, 7620), signs='++', **sp)
    g_vm = novo('core/Gain', 'KV_x_Pm', (7720, 7620), gain=repr(P.KV), **sp)
    lig(T(sc['degrau'], 'out'), T(s_dg, 'in')); lig(T(st, 'out'), T(s_dg, 'in1'))
    lig(T(sc['dPm'], 'out'), T(p_dg, 'in')); lig(T(s_dg, 'out'), T(p_dg, 'in1'))
    lig(T(sc['Pm0'], 'out'), T(s_pm, 'in')); lig(T(p_dg, 'out'), T(s_pm, 'in1'))
    lig(T(s_pm, 'out'), T(g_vm, 'in')); lig(T(g_vm, 'out'), T(vm, 'in'))

    # ================================================= amortecimento: R = KV*D/KI (>= 1 uohm)
    g_r = novo('core/Gain', 'KV_sobre_KI_x_D', (7520, 7900), gain=repr(P.KV/P.KI), **sp)
    rmin = novo('core/Constant', 'R_minimo', (7520, 7980), value='1e-6', **sp)
    mx = novo('core/Min Max', 'R_nao_nulo', (7640, 7920), operation='max', **sp)
    lig(T(sc['D'], 'out'), T(g_r, 'in')); lig(T(g_r, 'out'), T(mx, 'in')); lig(T(rmin, 'out'), T(mx, 'in1'))
    lig(T(mx, 'out'), T(rv, 'In'))

    # ================================================= rede: Pmax(t) = (E'V/X)*(1 - falta)
    ev = novo('core/Constant', 'EV', (8400, 7600), value=repr(P.E_LINHA*P.V_BAR), **sp)
    pmx = novo('core/Product', 'Pmax_EV_sobre_X', (8520, 7620), signs='*/', **sp)
    um = novo('core/Constant', 'um', (8400, 7700), value='1.0', **sp)
    f_ini = novo('core/Step', 'falta_inicio', (8400, 7760), step_time=NUNCA, initial_value='0.0',
                 final_value='1.0', **sp)
    f_fim = novo('core/Step', 'falta_fim', (8400, 7820), step_time=NUNCA, initial_value='0.0',
                 final_value='1.0', **sp)
    rede = novo('core/Sum', 'rede_1_menos_falta', (8520, 7760), signs='+--+', **sp)
    pmt = novo('core/Product', 'Pmax_t', (8640, 7700), **sp)
    lig(T(ev, 'out'), T(pmx, 'in')); lig(T(sc['X'], 'out'), T(pmx, 'in1'))
    lig(T(um, 'out'), T(rede, 'in')); lig(T(sc['falta'], 'out'), T(rede, 'in1'))
    lig(T(f_ini, 'out'), T(rede, 'in2')); lig(T(f_fim, 'out'), T(rede, 'in3'))
    lig(T(pmx, 'out'), T(pmt, 'in')); lig(T(rede, 'out'), T(pmt, 'in1'))

    # ================================================= fonte nao linear: v_nl = KV*Pmax(t)*sen(delta) - v_C
    g_d = novo('core/Gain', 'vC_para_rad', (8400, 7960), gain=repr(1.0/P.KV_DELTA), **sp)
    d0 = novo('core/Constant', 'delta0', (8400, 8040), value=repr(P.DELTA0), **sp)
    s_d = novo('core/Sum', 'delta', (8520, 7980), signs='++', **sp)
    sen = novo('core/Trigonometric function', 'sen_delta', (8640, 7980), trigonometric_fn='sin',
               angle='Radians', **sp)
    pe = novo('core/Product', 'Pe', (8760, 7900), **sp)
    g_kv = novo('core/Gain', 'KV_x_Pe', (8880, 7900), gain=repr(P.KV), **sp)
    s_nl = novo('core/Sum', 'menos_vC', (9000, 7920), signs='+-', **sp)
    lig(T(vvc, 'out'), T(g_d, 'in')); lig(T(g_d, 'out'), T(s_d, 'in')); lig(T(d0, 'out'), T(s_d, 'in1'))
    lig(T(s_d, 'out'), T(sen, 'in')); lig(T(pmt, 'out'), T(pe, 'in')); lig(T(sen, 'out'), T(pe, 'in1'))
    lig(T(pe, 'out'), T(g_kv, 'in')); lig(T(g_kv, 'out'), T(s_nl, 'in')); lig(T(vvc, 'out'), T(s_nl, 'in1'))
    lig(T(s_nl, 'out'), T(fnl, 'in'))

    # ================================================= leituras reconvertidas e sondas
    g_w = novo('core/Gain', 'i_para_dw', (7720, 8040), gain=repr(1.0/P.KI), **sp)
    g_g = novo('core/Gain', 'rad_para_graus', (8640, 8060), gain=repr(180.0/math.pi), **sp)
    lig(T(idw, 'out'), T(g_w, 'in')); lig(T(s_d, 'out'), T(g_g, 'in'))
    for nome, origem, pos in (('delta_graus', T(g_g, 'out'), (8760, 8060)),
                              ('delta_omega', T(g_w, 'out'), (7840, 8040)),
                              ('Pe_pu', T(pe, 'out'), (8760, 7820)),
                              ('Pm_pu', T(s_pm, 'out'), (7620, 7540)),
                              ('i_A', T(idw, 'out'), (7840, 7980)),
                              ('vC_V', T(vvc, 'out'), (8400, 8120)),
                              ('vnl_V', T(s_nl, 'out'), (9120, 7920)),
                              ('Vm_V', T(g_vm, 'out'), (7840, 7620))):
        lig(origem, T(novo('core/Probe', nome, pos), 'in'))
    novo('core/Scope', 'Scope_equivalente', (9120, 8100), selected_signals=SONDAS)

    configura(tempo)
    model.save_as(TSE)
    ok = model.compile()
    model.close_model()
    limpa_target()
    return ok


if __name__ == '__main__':
    print('modelo salvo em %s | compilou = %s' % (TSE, monta()))
