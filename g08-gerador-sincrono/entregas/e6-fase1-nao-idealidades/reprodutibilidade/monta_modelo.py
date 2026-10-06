# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Monta a cadeia no TyphoonSim, via API do Schematic Editor, e compila.

Regra de construcao:
  * O que veio da Entrega 01 fica EXATAMENTE como era, em C function:
      'referencia' (varredura), 'potenciometro' (x = theta/3600 ; v = x.V(VREF)) e 'receptor',
      e todo o circuito eletrico (buffer, R0, R_IN, XTR115, laco, R_L).
  * O que e da Entrega 02 e feito com BLOCOS NATIVOS, entre a referencia e o potenciometro:
      folga (R6):      theta_c = max(theta, min(theta + b, UnitDelay(theta_c)))
                       [Constant, Sum, Min Max (min), Min Max (max), Unit Delay]
      resolucao (R6):  theta_q = (floor(theta_c.N/theta_FS + 1/2 - phi) + phi) . theta_FS/N
                       [Gain, Constant, Sum, Round (floor), Constant, Sum, Gain]
                       + chave liga/desliga [Constant, Sum (+-), Product, Sum]
      ruido 1/f (R8):  Random Source (normal, media 0, desvio 1) -> filtro de Kellet em forma
                       paralela [6 Discrete Transfer Function + 1 atraso + Gain, Sum de 8 entradas]
                       -> Gain K_ENR = dR_c ; x "cursor em movimento" [Sum (+-), Unit Delay, Abs,
                       Sign] ; x chave ; x I_cursor -> somado a v_cursor [Product, Gain, Sum]
      ordem zero (R7): e o proprio potenciometro da E01 (y = K.x), sem bloco novo.
  * Contrafactual R8 (modelo_r8_sem_buffer.tse): potenciometro como 3 Variable Resistors, sem
    buffer; as resistencias tambem sao calculadas com blocos nativos.

O Random Source nativo nao tem semente: o ruido do TyphoonSim e outra realizacao, com a mesma
estatistica do gabarito. analisa_typhoon.py compara a estatistica e, com a sonda 'ruido_branco',
confere o filtro 1/f nativo amostra a amostra.

Modo 'c' (plano B, automatico se algum bloco nativo falhar): as camadas da E02 dentro de uma
C function, versao conferida bit a bit com o Python (confere_c.py).

Uso (TyphoonSim aberto - ver ../typhoonsim/instrucoes.md):
    <python com typhoon_hil_api> monta_modelo.py      -> ../typhoonsim/modelo.tse
                                                         ../typhoonsim/modelo_r8_sem_buffer.tse
    <python com typhoon_hil_api> monta_modelo.py c    (forca o plano B)
"""
import os
import sys

from typhoon.api.schematic_editor import model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parametros as P
from modelo_camadas import K_ENR, KELLET_P, KELLET_G, KELLET_DIRETO, KELLET_ATRASO

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'modelo.tse'))
SAIDA_R8 = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'modelo_r8_sem_buffer.tse'))
DT = str(P.DT_SINAL)

# =====================================================================================
# codigo C da Entrega 01 (sem alteracao)
# =====================================================================================
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

C_POT_E01 = """/*Begin code section*/
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
GLOBAIS_POT_E01 = 'real THETA_FS;real x;'
INIT_POT_E01 = 'THETA_FS = %.1f;\nx = 0.0;' % P.THETA_FS

C_RECEPTOR = """/*Begin code section*/
/* Receptor: le a tensao sobre R_L e converte em corrente e em angulo */
i_mA = 1000.0 * v_rl / R_L;
theta_med = THETA_FS * (i_mA - 4.0) / 16.0;
/* erro da corrente medida contra a reta ideal 4-20 mA, em % do fundo de escala */
erro_FE = 100.0 * (i_mA - (4.0 + 16.0 * theta_ref / THETA_FS)) / 16.0;
/*End code section*/"""

# =====================================================================================
# plano B (modo 'c'): camadas da E02 dentro da C function - conferido bit a bit (confere_c.py)
# =====================================================================================
C_RUIDO = """
/* R8 - ruido de contato 1/f: LCG -> branco (Irwin-Hall) -> filtro de Kellet */
g = 0.0;
for (k = 0; k < 12; k++) {
    s_lcg = fmod(1664525.0 * s_lcg + 1013904223.0, 4294967296.0);
    g = g + s_lcg / 4294967296.0;
}
w = g - 6.0;
b0 = 0.99886 * b0 + w * 0.0555179;
b1 = 0.99332 * b1 + w * 0.0750759;
b2 = 0.96900 * b2 + w * 0.1538520;
b3 = 0.86650 * b3 + w * 0.3104856;
b4 = 0.55000 * b4 + w * 0.5329522;
b5 = -0.7616 * b5 - w * 0.0168980;
rosa = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362;
b6 = w * 0.115926;
dRc = K_ENR * rosa;
"""

C_POT = """/*Begin code section*/
/* PLANO B - camadas da Entrega 02 em C (mesmas operacoes de modelo_camadas.py).
   Flags (init_fnc): CAM_FOLGA, CAM_RES, CAM_RUIDO = 1.0 liga / 0.0 desliga. */
if (primeiro > 0.5) { th_c = theta; }
if (CAM_FOLGA > 0.5) {
    th_min = (theta + FOLGA < th_c) ? theta + FOLGA : th_c;
    th_c = (theta > th_min) ? theta : th_min;
} else {
    th_c = theta;
}
th_out = th_c;
if (th_out < 0.0) th_out = 0.0;
if (th_out > THETA_FS) th_out = THETA_FS;
if (primeiro > 0.5) { th_ant = th_out; primeiro = 0.0; }
movendo = (th_out != th_ant) ? 1.0 : 0.0;
th_ant = th_out;
x = th_out / THETA_FS;
if (CAM_RES > 0.5) {
    x = (floor(x * N_PASSOS + 0.5 - FASE) + FASE) / N_PASSOS;
    if (x > 1.0) x = 1.0;
}
""" + C_RUIDO + """
v_cursor = x * vref;
if (CAM_RUIDO > 0.5 && movendo > 0.5) {
    v_cursor = v_cursor + dRc * I_CURSOR;
}
theta_c = th_out;
/*End code section*/"""

GLOBAIS_POT = ('real THETA_FS;real FOLGA;real N_PASSOS;real FASE;real K_ENR;real I_CURSOR;'
               'real CAM_FOLGA;real CAM_RES;real CAM_RUIDO;'
               'real primeiro;real th_c;real th_min;real th_out;real th_ant;real movendo;real x;'
               'real s_lcg;real g;real w;real rosa;int k;real b0;real b1;real b2;real b3;real b4;real b5;real b6;')

# flags por caso (folga, resolucao, ruido) - os mesmos de modelo_camadas.CASOS / CASOS_R8
FLAGS = {
    'ideal':     (0, 0, 0),
    'estatica':  (1, 1, 0),
    'espectral': (0, 0, 1),
    'completa':  (1, 1, 1),
}
FLAGS_R8 = {
    'r8_sem_buffer':           (1, 1, 1),
    'r8_sem_buffer_sem_ruido': (1, 1, 0),
}


def init_pot(cam_folga=1, cam_res=1, cam_ruido=1):
    """init_fnc da C function do plano B."""
    return '\n'.join([
        'THETA_FS = %.1f;' % P.THETA_FS, 'FOLGA = %.6f;' % P.FOLGA_GRAUS,
        'N_PASSOS = %.1f;' % P.N_PASSOS, 'FASE = %.6f;' % P.FASE_ESPIRA,
        'K_ENR = %.17g;' % K_ENR, 'I_CURSOR = %.6e;' % P.I_CURSOR,
        'CAM_FOLGA = %.1f;' % cam_folga, 'CAM_RES = %.1f;' % cam_res, 'CAM_RUIDO = %.1f;' % cam_ruido,
        'primeiro = 1.0; th_c = 0.0; th_min = 0.0; th_out = 0.0; th_ant = 0.0; movendo = 0.0; x = 0.0;',
        's_lcg = %.1f; g = 0.0; w = 0.0; rosa = 0.0; k = 0;' % P.SEMENTE,
        'b0 = 0.0; b1 = 0.0; b2 = 0.0; b3 = 0.0; b4 = 0.0; b5 = 0.0; b6 = 0.0;'])


# =====================================================================================
# montagem
# =====================================================================================

def monta(r_cabo=P.R_CABO, nome='modelo', salvar=SAIDA, camadas=FLAGS['completa'], modo='nativo',
          sem_buffer=False):
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

    def cfunc(nome_c, pos, ent, sai, globais, init, codigo):
        ne, ns = len(ent), len(sai)
        return novo('core/C function', nome_c, pos, execution_rate='inherit',
                    input_terminals=''.join('real %s;' % e for e in ent),
                    output_terminals=''.join('real %s;' % s for s in sai),
                    input_terminals_dimensions=';'.join(['inherit'] * ne),
                    output_terminals_dimensions=';'.join(['inherit'] * ns),
                    input_terminals_feedthrough='True;' * ne, output_terminals_feedthrough='True;' * ns,
                    input_terminals_show_labels='True;' * ne, output_terminals_show_labels='True;' * ns,
                    global_variables=globais, init_fnc=init, output_fnc=codigo)

    # ======================================================= C functions (criadas antes do reload)
    clk = novo('core/Clock', 'relogio', (7600, 7800), execution_rate=DT)
    cfunc('referencia', (7760, 7800), ['t'], ['theta_ref'], 'real THETA_FS;real T_MEIO;',
          'THETA_FS = %.1f;\nT_MEIO = %.4f;' % (P.THETA_FS, P.T_VARREDURA / 2), C_REFERENCIA)
    if modo == 'c':
        cfunc('potenciometro', (7960, 7840), ['theta', 'vref'], ['v_cursor', 'theta_c', 'dRc'],
              GLOBAIS_POT, init_pot(*camadas), C_POT)
    elif not sem_buffer:
        cfunc('potenciometro', (8440, 7840), ['theta', 'vref'], ['v_cursor'],
              GLOBAIS_POT_E01, INIT_POT_E01, C_POT_E01)
    cfunc('receptor', (9560, 8200), ['v_rl', 'theta_ref'], ['i_mA', 'theta_med', 'erro_FE'],
          'real THETA_FS;real R_L;', 'THETA_FS = %.1f;\nR_L = %.3f;' % (P.THETA_FS, P.R_L), C_RECEPTOR)
    # A API so gera os terminais nomeados de um C function ao carregar o arquivo:
    # salva, fecha e recarrega antes de ligar os blocos.
    tmp = (salvar or SAIDA).replace('.tse', '_tmp.tse')
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    model.save_as(tmp)
    model.close_model()
    model.load(tmp)
    clk, ref, rx = (model.get_item(n) for n in ('relogio', 'referencia', 'receptor'))
    pot = model.get_item('potenciometro')

    # ======================================================= camadas da E02 em blocos nativos
    if modo == 'nativo':
        sp = dict(execution_rate=DT)

        def const(nome_c, pos, valor):
            return novo('core/Constant', nome_c, pos, value=repr(float(valor)), **sp)

        def soma(nome_c, pos, sinais='++'):
            return novo('core/Sum', nome_c, pos, signs=sinais, **sp)

        th_ref = T(ref, 'theta_ref')
        # ---- R6a folga: theta_c = max(theta, min(theta + b, theta_c[k-1]))
        b = const('folga_b', (7840, 7560), P.FOLGA_GRAUS * camadas[0])
        s_b = soma('folga_theta_mais_b', (7920, 7600))
        m_min = novo('core/Min Max', 'folga_min', (8000, 7600), operation='min', **sp)
        m_max = novo('core/Min Max', 'folga_max', (8080, 7640), operation='max', **sp)
        ud = novo('core/Unit Delay', 'folga_memoria', (8000, 7520), init_value='0', **sp)
        lig(th_ref, T(s_b, 'in')); lig(T(b, 'out'), T(s_b, 'in1'))
        lig(T(s_b, 'out'), T(m_min, 'in')); lig(T(ud, 'out'), T(m_min, 'in1'))
        lig(th_ref, T(m_max, 'in')); lig(T(m_min, 'out'), T(m_max, 'in1'))
        lig(T(m_max, 'out'), T(ud, 'in'))
        th_c = T(m_max, 'out')
        # ---- R6b resolucao: theta_q = (floor(theta_c.N/theta_FS + 1/2 - phi) + phi) . theta_FS/N
        g_n = novo('core/Gain', 'res_espiras_por_grau', (8160, 7440), gain=repr(P.N_PASSOS / P.THETA_FS), **sp)
        c_a = const('res_meio_menos_fase', (8160, 7380), 0.5 - P.FASE_ESPIRA)
        s_a = soma('res_soma_a', (8240, 7440))
        rnd = novo('core/Round', 'res_espira', (8320, 7440), round_fn='floor', **sp)
        c_f = const('res_fase', (8320, 7380), P.FASE_ESPIRA)
        s_f = soma('res_soma_fase', (8400, 7440))
        g_q = novo('core/Gain', 'res_graus_por_espira', (8480, 7440), gain=repr(P.THETA_FS / P.N_PASSOS), **sp)
        lig(th_c, T(g_n, 'in')); lig(T(g_n, 'out'), T(s_a, 'in')); lig(T(c_a, 'out'), T(s_a, 'in1'))
        lig(T(s_a, 'out'), T(rnd, 'in')); lig(T(rnd, 'out'), T(s_f, 'in')); lig(T(c_f, 'out'), T(s_f, 'in1'))
        lig(T(s_f, 'out'), T(g_q, 'in'))
        # chave: theta_pot = theta_c + k_res . (theta_q - theta_c)   (k_res = 0 -> exatamente theta_c)
        k_res = const('res_liga', (8480, 7380), camadas[1])
        d_q = soma('res_desvio', (8560, 7440), '+-')
        p_q = novo('core/Product', 'res_chave', (8640, 7440), **sp)
        s_q = soma('res_saida', (8720, 7520))
        lig(T(g_q, 'out'), T(d_q, 'in')); lig(th_c, T(d_q, 'in1'))
        lig(T(d_q, 'out'), T(p_q, 'in')); lig(T(k_res, 'out'), T(p_q, 'in1'))
        lig(th_c, T(s_q, 'in')); lig(T(p_q, 'out'), T(s_q, 'in1'))
        th_pot = T(s_q, 'out')
        # ---- R8 ruido de contato 1/f: Random Source -> filtro de Kellet (forma paralela) -> K_ENR
        rs = novo('core/Random Source', 'ruido_branco', (7760, 7200), distribution='Normal',
                  mean='0.0', stddev='1.0', **sp)
        s8 = soma('kellet_soma', (8080, 7200), '+' * 8)
        ent8 = ['in'] + ['in%d' % i for i in range(1, 8)]
        for i, (p_i, g_i) in enumerate(zip(KELLET_P, KELLET_G)):
            tf = novo('core/Discrete Transfer Function', 'kellet_polo%d' % i, (7920, 6960 + 60 * i),
                      domain='Z-domain', b_coeff='[%r, 0.0]' % g_i, a_coeff='[1.0, %r]' % (-p_i), **sp)
            lig(T(rs, 'out'), T(tf, 'in')); lig(T(tf, 'out'), T(s8, ent8[i]))
        tf_at = novo('core/Discrete Transfer Function', 'kellet_atraso', (7920, 7320),
                     domain='Z-domain', b_coeff='[0.0, %r]' % KELLET_ATRASO, a_coeff='[1.0, 0.0]', **sp)
        g_d = novo('core/Gain', 'kellet_direto', (7920, 7380), gain=repr(KELLET_DIRETO), **sp)
        lig(T(rs, 'out'), T(tf_at, 'in')); lig(T(tf_at, 'out'), T(s8, ent8[6]))
        lig(T(rs, 'out'), T(g_d, 'in')); lig(T(g_d, 'out'), T(s8, ent8[7]))
        g_enr = novo('core/Gain', 'ruido_K_ENR', (8160, 7200), gain=repr(K_ENR), **sp)
        lig(T(s8, 'out'), T(g_enr, 'in'))
        dRc = T(g_enr, 'out')
        # cursor em movimento: sign(|theta_c - theta_c[k-1]|) ; ENR so existe com o eixo girando
        ud_m = novo('core/Unit Delay', 'mov_memoria', (8160, 7300), init_value='0', **sp)
        d_m = soma('mov_desvio', (8240, 7300), '+-')
        a_m = novo('core/Abs', 'mov_abs', (8320, 7300), **sp)
        sg_m = novo('core/Sign', 'mov_cursor_movendo', (8400, 7300), **sp)
        lig(th_c, T(ud_m, 'in')); lig(th_c, T(d_m, 'in')); lig(T(ud_m, 'out'), T(d_m, 'in1'))
        lig(T(d_m, 'out'), T(a_m, 'in')); lig(T(a_m, 'out'), T(sg_m, 'in'))
        k_r = const('ruido_liga', (8400, 7200), camadas[2])
        p_m = novo('core/Product', 'ruido_x_movimento', (8480, 7240), **sp)
        p_k = novo('core/Product', 'ruido_chave', (8560, 7240), **sp)
        lig(dRc, T(p_m, 'in')); lig(T(sg_m, 'out'), T(p_m, 'in1'))
        lig(T(p_m, 'out'), T(p_k, 'in')); lig(T(k_r, 'out'), T(p_k, 'in1'))
        dRc_ativo = T(p_k, 'out')

    # ======================================================= lado do sensor (IRET)
    vref = novo('core/Voltage Source', 'VREF_XTR115', (7960, 8160), rot='right',
                init_source_nature='Constant', init_const_value=str(P.VREF))
    r0 = novo('core/Resistor', 'R0', (8340, 8040), resistance=str(P.R0))
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
    lig(j_vref3, T(r0, 'p_node')); lig(T(r0, 'n_node'), j_iin)
    lig(j_cur, T(rin, 'p_node')); lig(T(rin, 'n_node'), j_iin2)
    lig(j_iin, j_iin2); lig(j_iin2, T(iin, 'p_node'))
    for c in (vref, iin):
        lig(T(c, 'n_node'), j_iret)
    lig(T(gnd1, 'node'), j_iret)

    if not sem_buffer:
        # E01: R_pot = carga do potenciometro sobre VREF; buffer = fonte de tensao controlada
        rpot = novo('core/Resistor', 'R_pot', (8080, 8160), rot='right', resistance=str(P.R_POT))
        vm_ref = novo('core/Voltage Measurement', 'V_REF', (8180, 8160), rot='right',
                      sig_output='True', execution_rate=DT)
        buf = novo('core/Signal Controlled Voltage Source', 'buffer_OPA333', (8200, 8340), rot='right')
        lig(T(rpot, 'p_node'), j_vref2); lig(T(vm_ref, 'p_node'), j_vref3)
        lig(T(buf, 'p_node'), j_cur)
        for c in (rpot, vm_ref, buf):
            lig(T(c, 'n_node'), j_iret)
        lig(T(vm_ref, 'out'), T(pot, 'vref'))
        if modo == 'c':
            lig(T(ref, 'theta_ref'), T(pot, 'theta'))
            lig(T(pot, 'v_cursor'), T(buf, 'in'))
            v_cur = T(pot, 'v_cursor')
        else:
            # E01 intacto recebe o angulo ja com folga e resolucao; o ruido soma na saida dele
            lig(th_pot, T(pot, 'theta'))
            g_ic = novo('core/Gain', 'ruido_x_I_cursor', (8640, 7240), gain=repr(P.I_CURSOR), **sp)
            s_v = soma('v_cursor_mais_ruido', (8640, 7880))
            lig(dRc_ativo, T(g_ic, 'in'))
            lig(T(pot, 'v_cursor'), T(s_v, 'in')); lig(T(g_ic, 'out'), T(s_v, 'in1'))
            lig(T(s_v, 'out'), T(buf, 'in'))
            v_cur = T(s_v, 'out')
    else:
        # contrafactual R8: VREF -> R_sup -> trilha -> R_inf -> IRET ; trilha -> R_c -> cursor -> R_IN
        r_sup = novo('core/Variable Resistor', 'R_trilha_sup', (8080, 8120), rot='right')
        r_inf = novo('core/Variable Resistor', 'R_trilha_inf', (8080, 8360), rot='right')
        r_c = novo('core/Variable Resistor', 'R_contato', (8140, 8240))
        j_tr = jun('no_trilha', (8080, 8240))
        lig(T(r_sup, 'p_node'), j_vref2); lig(T(r_sup, 'n_node'), j_tr)
        lig(j_tr, T(r_inf, 'p_node')); lig(T(r_inf, 'n_node'), j_iret)
        lig(j_tr, T(r_c, 'p_node')); lig(T(r_c, 'n_node'), j_cur)
        # resistencias com blocos nativos: R_inf = min(max(Rp.x, Rmin), Rp) ; R_sup = max(Rp - Rp.x, Rmin) ;
        # R_c = R_C0 + dR_c (com movimento e chave)
        rmin = const('R_min', (8560, 7700), P.R_MIN_POT)
        g_inf = novo('core/Gain', 'R_inf_Rp_x', (8560, 7760), gain=repr(P.R_POT / P.THETA_FS), **sp)
        m_inf = novo('core/Min Max', 'R_inf_minimo', (8640, 7760), operation='max', **sp)
        rp = const('R_p', (8560, 7820), P.R_POT)
        s_sup = soma('R_sup_Rp_menos', (8640, 7840), '+-')
        m_sup = novo('core/Min Max', 'R_sup_minimo', (8720, 7840), operation='max', **sp)
        rc0 = const('R_C0', (8560, 7920), P.R_C0)
        s_rc = soma('R_c_base_mais_ruido', (8640, 7940))
        # o cursor nao passa do fim da trilha (x <= 1, como no potenciometro da E01): R_inf <= R_p
        m_inf2 = novo('core/Min Max', 'R_inf_maximo', (8720, 7760), operation='min', **sp)
        lig(th_pot, T(g_inf, 'in')); lig(T(g_inf, 'out'), T(m_inf, 'in')); lig(T(rmin, 'out'), T(m_inf, 'in1'))
        lig(T(m_inf, 'out'), T(m_inf2, 'in')); lig(T(rp, 'out'), T(m_inf2, 'in1'))
        lig(T(rp, 'out'), T(s_sup, 'in')); lig(T(g_inf, 'out'), T(s_sup, 'in1'))
        lig(T(s_sup, 'out'), T(m_sup, 'in')); lig(T(rmin, 'out'), T(m_sup, 'in1'))
        lig(T(rc0, 'out'), T(s_rc, 'in')); lig(dRc_ativo, T(s_rc, 'in1'))
        lig(T(m_sup, 'out'), T(r_sup, 'In')); lig(T(m_inf2, 'out'), T(r_inf, 'In')); lig(T(s_rc, 'out'), T(r_c, 'In'))
        vm_cur = novo('core/Voltage Measurement', 'V_CURSOR', (8260, 8340), rot='right',
                      sig_output='True', execution_rate=DT)
        lig(T(vm_cur, 'p_node'), j_cur); lig(T(vm_cur, 'n_node'), j_iret)
        v_cur = T(vm_cur, 'out')

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

    def sonda(nome_s, pos):
        return novo('core/Probe', nome_s, pos)

    lig(T(clk, 'out'), T(ref, 't'))
    lig(T(iin, 'out'), T(k100, 'in'))
    lig(T(k100, 'out'), T(xtr, 'in'))
    lig(T(vrl, 'out'), T(rx, 'v_rl'))
    lig(T(ref, 'theta_ref'), T(rx, 'theta_ref'))

    lig(T(ref, 'theta_ref'), T(sonda('theta_ref', (7960, 7720)), 'in'))
    lig(v_cur, T(sonda('v_cursor', (8760, 7960)), 'in'))
    if modo == 'c':
        lig(T(pot, 'theta_c'), T(sonda('theta_cursor', (8160, 7680)), 'in'))
        lig(T(pot, 'dRc'), T(sonda('dRc_ohm', (8240, 7680)), 'in'))
    else:
        lig(th_c, T(sonda('theta_cursor', (8160, 7680)), 'in'))
        lig(th_pot, T(sonda('theta_resolucao', (8800, 7520)), 'in'))
        lig(dRc, T(sonda('dRc_ohm', (8240, 7120)), 'in'))
        lig(T(rs, 'out'), T(sonda('ruido_branco_N01', (7840, 7120)), 'in'))
    lig(T(iin, 'out'), T(k_uA, 'in')); lig(T(k_uA, 'out'), T(sonda('I_IN_uA', (8760, 8300)), 'in'))
    lig(T(iloop, 'out'), T(k_mA, 'in')); lig(T(k_mA, 'out'), T(sonda('I_LOOP_mA', (9360, 8300)), 'in'))
    lig(T(vtx, 'out'), T(sonda('V_TX_V', (9120, 8120)), 'in'))
    lig(T(vrl, 'out'), T(sonda('V_RL_V', (9500, 8460)), 'in'))
    lig(T(rx, 'theta_med'), T(sonda('theta_med', (9760, 8200)), 'in'))
    lig(T(rx, 'erro_FE'), T(sonda('erro_FE_pc', (9760, 8280)), 'in'))
    lig(T(rx, 'i_mA'), T(sonda('I_receptor_mA', (9760, 8120)), 'in'))

    sinais = ['theta_ref', 'theta_med', 'I_LOOP_mA', 'V_RL_V', 'V_TX_V', 'I_IN_uA',
              'v_cursor', 'erro_FE_pc', 'I_receptor_mA', 'theta_cursor', 'dRc_ohm']
    if modo != 'c':
        sinais += ['theta_resolucao', 'ruido_branco_N01']
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
        model.save_as(salvar)
    ok = model.compile()
    try:
        os.remove(tmp)
    except OSError:
        pass
    return ok


def aplica_caso(caso, modo):
    """Com o modelo carregado, liga/desliga as camadas do 'caso' sem mudar a topologia."""
    flags = FLAGS.get(caso) or FLAGS_R8[caso]
    if modo == 'c':
        pot = model.get_item('potenciometro')
        model.set_property_value(model.prop(pot, 'init_fnc'), init_pot(*flags))
        return
    for nome_c, valor in (('folga_b', P.FOLGA_GRAUS * flags[0]), ('res_liga', flags[1]), ('ruido_liga', flags[2])):
        model.set_property_value(model.prop(model.get_item(nome_c), 'value'), repr(float(valor)))


def modo_salvo():
    """'nativo' se o modelo carregado tem os blocos da E02, 'c' se nao."""
    try:
        return 'nativo' if model.get_item('folga_b') is not None else 'c'
    except Exception:
        return 'c'


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'nativo'
    try:
        ok = monta(modo=modo)
    except Exception as e:
        if modo != 'nativo':
            raise
        print('\n!!! modo nativo falhou (%s)\n!!! montando o plano B (camadas em C).'
              '\n!!! Para corrigir, rode inspeciona_blocos.py e mande a saida.\n' % e)
        try:
            model.close_model()
        except Exception:
            pass
        modo = 'c'
        ok = monta(modo='c')
    print('modelo (%s) salvo em %s | compilou = %s | K_ENR = %r' % (modo, SAIDA, ok, K_ENR))
    if modo == 'nativo':
        try:
            model.close_model()
            ok8 = monta(nome='modelo_r8_sem_buffer', salvar=SAIDA_R8, sem_buffer=True)
            print('contrafactual R8 salvo em %s | compilou = %s' % (SAIDA_R8, ok8))
        except Exception as e:
            print('\n!!! contrafactual R8 falhou: %s\n!!! O resto da entrega nao depende dele.' % e)
