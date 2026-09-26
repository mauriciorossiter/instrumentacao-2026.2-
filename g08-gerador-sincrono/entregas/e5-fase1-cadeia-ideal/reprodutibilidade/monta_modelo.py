# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 01
Monta a cadeia ideal  potenciometro -> transmissor 4-20 mA (XTR115) -> laco -> receptor
no TyphoonSim, via API do Schematic Editor, e compila.

Uso (com o Typhoon HIL Control Center / TyphoonSim ABERTO):
    <python com typhoon_hil_api> monta_modelo.py
Gera ../typhoonsim/modelo.tse

Topologia (ver ../typhoonsim/instrucoes.md):
  LADO DO SENSOR (referido a IRET)
    VREF (2,5 V) -+- R_pot (10 k, carga do potenciometro sobre VREF)
                  +- R0 (62,6 k) ----------------+
    buffer (fonte controlada, v = x.VREF) - R_IN (15,6 k) -+- I_IN (amperimetro) - IRET
  LADO DO LACO
    V_LOOP (24 V) + -> XTR115 (fonte de corrente controlada, Io = 100 I_IN) -> R_cabo -> I_LOOP -> R_L (250) -> V_LOOP -
"""
import os
import sys

from typhoon.api.schematic_editor import model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parametros as P

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'modelo.tse'))
DT = str(P.DT_SINAL)

# ---------------------------------------------------------------- codigo C
C_REFERENCIA = """/*Begin code section*/
/* Sinal de referencia (R2): varredura triangular 0 -> THETA_FS -> 0 graus */
if (t <= T_MEIO) {
    theta_ref = THETA_FS * t / T_MEIO;
} else {
    theta_ref = THETA_FS * (2.0 * T_MEIO - t) / T_MEIO;
}
if (theta_ref < 0.0) theta_ref = 0.0;
if (theta_ref > THETA_FS) theta_ref = THETA_FS;
/*End code section*/"""

C_POT = """/*Begin code section*/
/* Potenciometro IDEAL (Entrega 01): divisor razao-metrico sem carga
   (o cursor alimenta o buffer OPA333, impedancia de entrada ~infinita).
   x = theta / THETA_FS ;  v_cursor = x * V(VREF)
   As camadas nao ideais da Entrega 02 (resolucao, histerese, ruido de
   contato) entram aqui, sobre x. */
x = theta / THETA_FS;
if (x < 0.0) x = 0.0;
if (x > 1.0) x = 1.0;
v_cursor = x * vref;
/*End code section*/"""

C_RECEPTOR = """/*Begin code section*/
/* Receptor: le a tensao sobre R_L e converte em corrente e em angulo */
i_mA = 1000.0 * v_rl / R_L;
theta_med = THETA_FS * (i_mA - 4.0) / 16.0;
/* erro da corrente medida contra a reta ideal 4-20 mA, em % do fundo de escala */
erro_FE = 100.0 * (i_mA - (4.0 + 16.0 * theta_ref / THETA_FS)) / 16.0;
/*End code section*/"""


def monta(r_cabo=P.R_CABO, nome='modelo', salvar=SAIDA):
    model.create_new_model(nome)

    def novo(tipo, nome_c, pos, rot=None, **props):
        c = model.create_component(tipo, name=nome_c)
        for k, v in props.items():
            model.set_property_value(model.prop(c, k), v)
        model.set_position(c, pos)
        if rot:
            model.set_rotation(c, rot)
        return c

    T = model.term
    lig = model.create_connection

    def jun(nome_j, pos):
        j = model.create_junction(name=nome_j, kind='pe')
        model.set_position(j, pos)
        return j

    # ======================================================= sinal
    clk = novo('core/Clock', 'relogio', (7600, 7800), execution_rate=DT)
    ref = novo('core/C function', 'referencia', (7760, 7800),
               execution_rate='inherit',
               input_terminals='real t;', output_terminals='real theta_ref;',
               input_terminals_dimensions='inherit', output_terminals_dimensions='inherit',
               input_terminals_feedthrough='True;', output_terminals_feedthrough='True;',
               input_terminals_show_labels='True;', output_terminals_show_labels='True;',
               global_variables='real THETA_FS;real T_MEIO;',
               init_fnc='THETA_FS = %.1f;\nT_MEIO = %.4f;' % (P.THETA_FS, P.T_VARREDURA / 2),
               output_fnc=C_REFERENCIA)

    pot = novo('core/C function', 'potenciometro', (7960, 7840),
               execution_rate='inherit',
               input_terminals='real theta;real vref;', output_terminals='real v_cursor;',
               input_terminals_dimensions='inherit;inherit', output_terminals_dimensions='inherit',
               input_terminals_feedthrough='True;True;', output_terminals_feedthrough='True;',
               input_terminals_show_labels='True;True;', output_terminals_show_labels='True;',
               global_variables='real THETA_FS;real x;',
               init_fnc='THETA_FS = %.1f;\nx = 0.0;' % P.THETA_FS,
               output_fnc=C_POT)

    rx = novo('core/C function', 'receptor', (9560, 8200),
              execution_rate='inherit',
              input_terminals='real v_rl;real theta_ref;',
              output_terminals='real i_mA;real theta_med;real erro_FE;',
              input_terminals_dimensions='inherit;inherit',
              output_terminals_dimensions='inherit;inherit;inherit',
              input_terminals_feedthrough='True;True;', output_terminals_feedthrough='True;True;True;',
              input_terminals_show_labels='True;True;', output_terminals_show_labels='True;True;True;',
              global_variables='real THETA_FS;real R_L;',
              init_fnc='THETA_FS = %.1f;\nR_L = %.3f;' % (P.THETA_FS, P.R_L),
              output_fnc=C_RECEPTOR)
    # A API so gera os terminais nomeados de um C function ao carregar o arquivo:
    # salva, fecha e recarrega antes de ligar os blocos.
    tmp = (salvar or SAIDA).replace('.tse', '_tmp.tse')
    model.save_as(tmp)
    model.close_model()
    model.load(tmp)
    clk, ref, pot, rx = (model.get_item(n) for n in ('relogio', 'referencia', 'potenciometro', 'receptor'))

    # ======================================================= lado do sensor (IRET)
    vref = novo('core/Voltage Source', 'VREF_XTR115', (7960, 8160), rot='right',
                init_source_nature='Constant', init_const_value=str(P.VREF))
    rpot = novo('core/Resistor', 'R_pot', (8080, 8160), rot='right', resistance=str(P.R_POT))
    vm_ref = novo('core/Voltage Measurement', 'V_REF', (8180, 8160), rot='right',
                  sig_output='True', execution_rate=DT)
    r0 = novo('core/Resistor', 'R0', (8340, 8040), resistance=str(P.R0))
    buf = novo('core/Signal Controlled Voltage Source', 'buffer_OPA333', (8200, 8340), rot='right')
    rin = novo('core/Resistor', 'R_IN', (8340, 8240), resistance=str(P.RIN))
    iin = novo('core/Current Measurement', 'I_IN', (8480, 8160), rot='right',
               sig_output='True', execution_rate=DT)
    gnd1 = novo('core/Ground', 'gnd_IRET', (8200, 8520))

    j_vref = jun('no_VREF', (7960, 8040))
    j_vref2 = jun('no_VREF2', (8080, 8040))
    j_vref3 = jun('no_VREF3', (8180, 8040))
    j_cur = jun('no_cursor', (8200, 8240))
    j_iin = jun('no_IIN', (8480, 8040))
    j_iin2 = jun('no_IIN2', (8480, 8240))
    j_iret = jun('no_IRET', (8200, 8460))

    lig(T(vref, 'p_node'), j_vref); lig(j_vref, j_vref2); lig(j_vref2, j_vref3)
    lig(T(rpot, 'p_node'), j_vref2); lig(T(vm_ref, 'p_node'), j_vref3)
    lig(j_vref3, T(r0, 'p_node')); lig(T(r0, 'n_node'), j_iin)
    lig(T(buf, 'p_node'), j_cur); lig(j_cur, T(rin, 'p_node')); lig(T(rin, 'n_node'), j_iin2)
    lig(j_iin, j_iin2); lig(j_iin2, T(iin, 'p_node'))
    for c in (vref, rpot, vm_ref, buf, iin):
        lig(T(c, 'n_node'), j_iret)
    lig(T(gnd1, 'node'), j_iret)

    # ======================================================= transmissor (ganho de corrente)
    k100 = novo('core/Gain', 'XTR115_x100', (8620, 8160), gain=str(P.GANHO_XTR))
    # ======================================================= lado do laco
    vloop = novo('core/Voltage Source', 'V_LOOP', (8760, 8360), rot='right',
                 init_source_nature='Constant', init_const_value=str(P.V_LOOP))
    xtr = novo('core/Signal Controlled Current Source', 'XTR115_Io', (8900, 8160), rot='right')
    vtx = novo('core/Voltage Measurement', 'V_TX', (9000, 8160), rot='right',
               sig_output='True', execution_rate=DT)
    rcabo = novo('core/Resistor', 'R_cabo', (9100, 8280), rot='right', resistance=str(r_cabo))
    iloop = novo('core/Current Measurement', 'I_LOOP', (9100, 8400), rot='right',
                 sig_output='True', execution_rate=DT)
    rl = novo('core/Resistor', 'R_L', (9240, 8460), rot='right', resistance=str(P.R_L))
    vrl = novo('core/Voltage Measurement', 'V_RL', (9360, 8460), rot='right',
               sig_output='True', execution_rate=DT)
    gnd2 = novo('core/Ground', 'gnd_laco', (8760, 8620))

    j_lp = jun('no_V+', (8900, 8040)); j_lp2 = jun('no_V+2', (8760, 8040)); j_lp3 = jun('no_V+3', (9000, 8040))
    j_io = jun('no_IO', (8900, 8240)); j_io2 = jun('no_IO2', (9000, 8240))
    j_rx = jun('no_RX', (9240, 8400)); j_rx2 = jun('no_RX2', (9360, 8400))
    j_g = jun('no_GND', (8760, 8560)); j_g2 = jun('no_GND2', (9240, 8560)); j_g3 = jun('no_GND3', (9360, 8560))

    lig(T(vloop, 'p_node'), j_lp2); lig(j_lp2, j_lp); lig(j_lp, j_lp3)
    lig(T(xtr, 'n_node'), j_lp)            # corrente entra no transmissor pelo V+ ...
    lig(T(xtr, 'p_node'), j_io)            # ... e sai pelo pino IO
    lig(T(vtx, 'p_node'), j_lp3); lig(T(vtx, 'n_node'), j_io2); lig(j_io, j_io2)
    lig(j_io2, T(rcabo, 'p_node')); lig(T(rcabo, 'n_node'), T(iloop, 'p_node'))
    lig(T(iloop, 'n_node'), j_rx); lig(j_rx, j_rx2)
    lig(j_rx, T(rl, 'p_node')); lig(j_rx2, T(vrl, 'p_node'))
    lig(T(vloop, 'n_node'), j_g); lig(j_g, j_g2); lig(j_g2, j_g3)
    lig(T(rl, 'n_node'), j_g2); lig(T(vrl, 'n_node'), j_g3)
    lig(T(gnd2, 'node'), j_g)

    # ======================================================= receptor + sondas
    k_uA = novo('core/Gain', 'A_para_uA', (8620, 8300), gain='1e6')
    k_mA = novo('core/Gain', 'A_para_mA', (9240, 8300), gain='1000')

    sondas = {}
    def sonda(nome_s, pos):
        sondas[nome_s] = novo('core/Probe', nome_s, pos)
        return sondas[nome_s]

    lig(T(clk, 'out'), T(ref, 't'))
    lig(T(ref, 'theta_ref'), T(pot, 'theta'))
    lig(T(vm_ref, 'out'), T(pot, 'vref'))
    lig(T(pot, 'v_cursor'), T(buf, 'in'))
    lig(T(iin, 'out'), T(k100, 'in'))
    lig(T(k100, 'out'), T(xtr, 'in'))
    lig(T(vrl, 'out'), T(rx, 'v_rl'))
    lig(T(ref, 'theta_ref'), T(rx, 'theta_ref'))

    lig(T(ref, 'theta_ref'), T(sonda('theta_ref', (7960, 7700)), 'in'))
    lig(T(pot, 'v_cursor'), T(sonda('v_cursor', (8160, 7760)), 'in'))
    lig(T(iin, 'out'), T(k_uA, 'in')); lig(T(k_uA, 'out'), T(sonda('I_IN_uA', (8760, 8300)), 'in'))
    lig(T(iloop, 'out'), T(k_mA, 'in')); lig(T(k_mA, 'out'), T(sonda('I_LOOP_mA', (9360, 8300)), 'in'))
    lig(T(vtx, 'out'), T(sonda('V_TX_V', (9120, 8120)), 'in'))
    lig(T(vrl, 'out'), T(sonda('V_RL_V', (9500, 8460)), 'in'))
    lig(T(rx, 'theta_med'), T(sonda('theta_med', (9760, 8200)), 'in'))
    lig(T(rx, 'erro_FE'), T(sonda('erro_FE_pc', (9760, 8280)), 'in'))
    lig(T(rx, 'i_mA'), T(sonda('I_receptor_mA', (9760, 8120)), 'in'))

    sinais = ['theta_ref', 'theta_med', 'I_LOOP_mA', 'V_RL_V', 'V_TX_V', 'I_IN_uA',
              'v_cursor', 'erro_FE_pc', 'I_receptor_mA']
    novo('core/Scope', 'Scope_cadeia', (7600, 8300), selected_signals=sinais)

    # ======================================================= solver TyphoonSim (offline, DAE)
    cfg = {
        'hil_device': 'HIL101', 'hil_configuration_id': '1',
        'simulation_method': 'exact', 'simulation_time_step': 'auto',
        'solver_type': 'DAE', 'integration_method': 'BDF',
        'max_sim_step': DT, 'init_sim_step': '1e-6',
        'abs_tol': '1e-9', 'rel_tol': '1e-9',
        'simulation_time': str(P.T_SIM),
    }
    for k, v in cfg.items():
        try:
            model.set_model_property_value(k, v)
        except Exception as e:
            print('   (aviso) %s: %s' % (k, e))

    if salvar:
        os.makedirs(os.path.dirname(salvar), exist_ok=True)
        model.save_as(salvar)
    ok = model.compile()
    try:
        os.remove(tmp)
    except OSError:
        pass
    return ok


if __name__ == '__main__':
    ok = monta()
    print('modelo salvo em', SAIDA, '| compilou =', ok)
