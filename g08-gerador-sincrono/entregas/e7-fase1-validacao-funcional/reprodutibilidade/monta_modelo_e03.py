# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03
Monta no TyphoonSim (API do Schematic Editor) a cadeia completa das Entregas 01 e 02 com um
GERADOR DE ENSAIOS e as ENTRADAS DO PAINEL SCADA, e compila -> ../typhoonsim/modelo_e03.tse

O que muda em relacao ao modelo da E02 (../../e6-fase1-nao-idealidades/reprodutibilidade/
monta_modelo.py, que fica intacto):
  1. Gerador de ensaios em BLOCOS NATIVOS, em paralelo a C function 'referencia' da E01 (que
     continua igual e vira o ensaio 0). Seletor 'ens_ensaio':
        0 varredura da E01 | 1 (a) degrau | 2 (b) condicao inicial | 3 (c) pulso
     theta_ref = e0.varredura + e1.(base + A.d) + e2.theta0 + e3.(base + A.p)
        d  = disparo (chave do SCADA 'ens_disparo' OU degrau automatico em 'ens_t_auto')
        p  = pulso de 'ens_largura_s' segundos a partir da borda de subida de d
        e_k = 1 - sign(|ens_ensaio - k|)   (indicador do ensaio k)
     So usa tipos de bloco que ja compilaram na E02 (Constant, Sum, Gain, Product, Unit Delay,
     Min Max, Abs, Sign, Clock) + SCADA Input.
  2. Condicao inicial (ensaio b): na borda do disparo, o estado da folga (theta_c[k-1], bloco
     'folga_memoria') recebe theta_ref + delta0 durante UMA amostra. Nenhum bloco da E02 muda:
     entra um Sum/Product entre 'folga_max' e 'folga_memoria' que vale exatamente theta_c fora
     desse instante. A referencia nao muda (sem novo estimulo).
  3. As chaves das camadas viram SCADA Inputs, para ligar/desligar ao vivo:
        folga_liga (0/1) -> Gain 'folga_b' (= 1,0 grau . folga_liga) ; res_liga ; ruido_liga
     Mesmos nomes da E02 para res_liga/ruido_liga; a topologia das camadas nao muda.
  4. Tempo de simulacao de T_SIM_SCADA (600 s), para operar o painel com folga.
O circuito eletrico e as C functions 'potenciometro' e 'receptor' sao os da E01, sem alteracao.

Plano B (modo 'c', automatico se um bloco nativo da E02 falhar): camadas da E02 na C function
conferida da E02 e gerador de ensaios nativo; nesse modo as camadas ficam fixas na compilacao
(sem liga/desliga ao vivo) e o ensaio (b) nao tem a injecao de condicao inicial.

Uso (TyphoonSim + Schematic Editor abertos - ver ../typhoonsim/instrucoes.md):
    <python com typhoon_hil_api> monta_modelo_e03.py      -> ../typhoonsim/modelo_e03.tse
    <python com typhoon_hil_api> monta_modelo_e03.py c    (forca o plano B)
"""
import os
import sys

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import parametros_e03 as E                                   # noqa: E402 (poe a E02 no sys.path)
import parametros as P                                       # noqa: E402
from modelo_camadas import K_ENR, KELLET_P, KELLET_G, KELLET_DIRETO, KELLET_ATRASO  # noqa: E402
# codigo C da E01 e plano B da E02, importados do monta_modelo da E02 SEM ALTERACAO
import monta_modelo as M02                                   # noqa: E402

SAIDA = os.path.abspath(os.path.join(AQUI, '..', 'typhoonsim', 'modelo_e03.tse'))
DT = str(P.DT_SINAL)

# SCADA Inputs: nome -> (valor inicial, minimo, maximo, descricao). E a lista que o painel usa.
ENTRADAS_SCADA = {
    'ens_ensaio':      (E.ENSAIO_PADRAO, 0, 3, 'ensaio: 0 varredura E01, 1 degrau, 2 cond. inicial, 3 pulso'),
    'ens_disparo':     (0, 0, 1, 'chave de disparo (0 -> 1 dispara o ensaio)'),
    'ens_theta_base':  (E.THETA_BASE, 0, P.THETA_FS, 'repouso dos ensaios (a) e (c) [graus]'),
    'ens_amplitude':   (E.AMPLITUDE, -P.THETA_FS, P.THETA_FS, 'amplitude do degrau e do pulso [graus]'),
    'ens_theta0':      (E.THETA0, 0, P.THETA_FS, 'referencia fixa do ensaio (b) [graus]'),
    'ens_delta0':      (E.DELTA0, -20, 20, 'deslocamento inicial do cursor no ensaio (b) [graus]'),
    'ens_largura_s':   (E.LARGURA, 0.001, 10, 'duracao do pulso do ensaio (c) [s]'),
    'ens_t_auto':      (E.T_AUTO_NUNCA, 0, E.T_AUTO_NUNCA, 'disparo automatico [s] (1e9 = nunca)'),
    'folga_liga':      (E.CAMADAS_PADRAO['folga_liga'], 0, 1, 'R6 folga de 1,0 grau (1 liga, 0 desliga)'),
    'res_liga':        (E.CAMADAS_PADRAO['res_liga'], 0, 1, 'R6 resolucao de 0,72 grau (1 liga, 0 desliga)'),
    'ruido_liga':      (E.CAMADAS_PADRAO['ruido_liga'], 0, 1, 'R8 ruido de contato 1/f (1 liga, 0 desliga)'),
}
# flags (folga, resolucao, ruido) por caso, como na E02
FLAGS = dict(M02.FLAGS)


def monta(nome='modelo_e03', salvar=SAIDA, modo='nativo', camadas_c=(1, 1, 1)):
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

    # ======================================================= C functions da E01 (antes do reload)
    novo('core/Clock', 'relogio', (7600, 7800), execution_rate=DT)
    cfunc('referencia', (7760, 7800), ['t'], ['theta_ref'], 'real THETA_FS;real T_MEIO;',
          'THETA_FS = %.1f;\nT_MEIO = %.4f;' % (P.THETA_FS, P.T_VARREDURA / 2), M02.C_REFERENCIA)
    if modo == 'c':
        cfunc('potenciometro', (7960, 7840), ['theta', 'vref'], ['v_cursor', 'theta_c', 'dRc'],
              M02.GLOBAIS_POT, M02.init_pot(*camadas_c), M02.C_POT)
    else:
        cfunc('potenciometro', (8440, 7840), ['theta', 'vref'], ['v_cursor'],
              M02.GLOBAIS_POT_E01, M02.INIT_POT_E01, M02.C_POT_E01)
    cfunc('receptor', (9560, 8200), ['v_rl', 'theta_ref'], ['i_mA', 'theta_med', 'erro_FE'],
          'real THETA_FS;real R_L;', 'THETA_FS = %.1f;\nR_L = %.3f;' % (P.THETA_FS, P.R_L), M02.C_RECEPTOR)
    # A API so gera os terminais nomeados de um C function ao carregar o arquivo (como na E02)
    tmp = salvar.replace('.tse', '_tmp.tse')
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    model.save_as(tmp)
    model.close_model()
    model.load(tmp)
    clk, ref, rx = (model.get_item(n) for n in ('relogio', 'referencia', 'receptor'))
    pot = model.get_item('potenciometro')

    sp = dict(execution_rate=DT)

    def const(nome_c, pos, valor):
        return novo('core/Constant', nome_c, pos, value=repr(float(valor)), **sp)

    def soma(nome_c, pos, sinais='++'):
        return novo('core/Sum', nome_c, pos, signs=sinais, **sp)

    def ganho(nome_c, pos, k):
        return novo('core/Gain', nome_c, pos, gain=repr(float(k)), **sp)

    def produto(nome_c, pos, a, b):
        p = novo('core/Product', nome_c, pos, **sp)
        lig(a, T(p, 'in')); lig(b, T(p, 'in1'))
        return T(p, 'out')

    def scada(nome_c, pos):
        """SCADA Input com o valor inicial de ENTRADAS_SCADA. So 'def_value' e obrigatorio; os
        demais nomes de propriedade variam entre versoes e entram se existirem."""
        valor, vmin, vmax, _ = ENTRADAS_SCADA[nome_c]
        c = model.create_component('core/SCADA Input', name=nome_c)
        model.set_property_value(model.prop(c, 'def_value'), repr(float(valor)))
        for k, v in (('execution_rate', DT), ('signal_type', 'real'),
                     ('min', repr(float(vmin))), ('max', repr(float(vmax)))):
            try:
                model.set_property_value(model.prop(c, k), v)
            except Exception as e:                  # propriedade opcional
                print('   (aviso) SCADA Input %s: propriedade %s nao aplicada (%s)' % (nome_c, k, e))
        model.set_position(c, pos)
        return T(c, 'out')

    # ======================================================= GERADOR DE ENSAIOS (E03, nativo)
    sc = {n: scada(n, (6640, 7400 + 60 * i)) for i, n in enumerate(ENTRADAS_SCADA)}
    um = T(const('ens_um', (6800, 7300), 1.0), 'out')
    zero = T(const('ens_zero', (6800, 7260), 0.0), 'out')
    meio_dt = T(const('ens_meio_dt', (6800, 7220), P.DT_SINAL / 2), 'out')
    dt_c = T(const('ens_dt', (6800, 7180), P.DT_SINAL), 'out')

    def meio_mais_meio_sinal(nome_c, pos, x):
        """(1 + sign(x)) / 2 : 1 se x > 0, 0 se x < 0 (os argumentos nunca sao exatamente 0)."""
        sg = novo('core/Sign', nome_c + '_sinal', pos, **sp)
        lig(x, T(sg, 'in'))
        s = soma(nome_c + '_mais1', (pos[0] + 60, pos[1]))
        lig(T(sg, 'out'), T(s, 'in')); lig(um, T(s, 'in1'))
        g = ganho(nome_c, (pos[0] + 120, pos[1]), 0.5)
        lig(T(s, 'out'), T(g, 'in'))
        return T(g, 'out')

    # disparo automatico: d_auto = [t > t_auto - DT/2]  (relogio da E01)
    s_ta = soma('ens_t_menos_tauto', (6900, 7900), '+-+')
    lig(T(clk, 'out'), T(s_ta, 'in')); lig(sc['ens_t_auto'], T(s_ta, 'in1')); lig(meio_dt, T(s_ta, 'in2'))
    d_auto = meio_mais_meio_sinal('ens_disparo_auto', (6960, 7900), T(s_ta, 'out'))
    m_d = novo('core/Min Max', 'ens_disparo_total', (7160, 7900), operation='max', **sp)
    lig(sc['ens_disparo'], T(m_d, 'in')); lig(d_auto, T(m_d, 'in1'))
    d = T(m_d, 'out')
    # borda de subida (1 amostra): max(d - d[k-1], 0)
    ud_d = novo('core/Unit Delay', 'ens_disparo_anterior', (7240, 7960), init_value='0', **sp)
    lig(d, T(ud_d, 'in'))
    s_b = soma('ens_borda_dif', (7300, 7900), '+-')
    lig(d, T(s_b, 'in')); lig(T(ud_d, 'out'), T(s_b, 'in1'))
    m_b = novo('core/Min Max', 'ens_borda', (7360, 7900), operation='max', **sp)
    lig(T(s_b, 'out'), T(m_b, 'in')); lig(zero, T(m_b, 'in1'))
    borda = T(m_b, 'out')
    # tempo desde o disparo: c = d . (c[k-1] + DT)
    ud_c = novo('core/Unit Delay', 'ens_cronometro_anterior', (7240, 8060), init_value='0', **sp)
    s_c = soma('ens_cronometro_mais_dt', (7300, 8020))
    lig(T(ud_c, 'out'), T(s_c, 'in')); lig(dt_c, T(s_c, 'in1'))
    cron = produto('ens_cronometro', (7360, 8020), T(s_c, 'out'), d)
    lig(cron, T(ud_c, 'in'))
    # pulso: p = d . [c < largura + DT/2]
    s_p = soma('ens_pulso_resta', (7420, 8020), '++-')
    lig(sc['ens_largura_s'], T(s_p, 'in')); lig(meio_dt, T(s_p, 'in1')); lig(cron, T(s_p, 'in2'))
    ativo = meio_mais_meio_sinal('ens_pulso_ativo', (7480, 8020), T(s_p, 'out'))
    pulso = produto('ens_pulso', (7660, 8020), ativo, d)
    # indicadores do seletor: e_k = 1 - sign(|ensaio - k|)
    e = []
    for k in range(4):
        y = 7560 + 60 * k
        ck = const('ens_k%d' % k, (6900, y + 20), k)
        sd = soma('ens_sel%d_dif' % k, (6960, y), '+-')
        lig(sc['ens_ensaio'], T(sd, 'in')); lig(T(ck, 'out'), T(sd, 'in1'))
        ab = novo('core/Abs', 'ens_sel%d_abs' % k, (7020, y), **sp)
        sg = novo('core/Sign', 'ens_sel%d_sinal' % k, (7080, y), **sp)
        ek = soma('ens_sel%d' % k, (7140, y), '+-')
        lig(T(sd, 'out'), T(ab, 'in')); lig(T(ab, 'out'), T(sg, 'in'))
        lig(um, T(ek, 'in')); lig(T(sg, 'out'), T(ek, 'in1'))
        e.append(T(ek, 'out'))
    # ramos: degrau = base + A.d ; pulso = base + A.p
    r_deg = soma('ens_ramo_degrau', (7300, 7720))
    lig(sc['ens_theta_base'], T(r_deg, 'in'))
    lig(produto('ens_A_x_disparo', (7240, 7720), sc['ens_amplitude'], d), T(r_deg, 'in1'))
    r_pul = soma('ens_ramo_pulso', (7300, 7780))
    lig(sc['ens_theta_base'], T(r_pul, 'in'))
    lig(produto('ens_A_x_pulso', (7240, 7780), sc['ens_amplitude'], pulso), T(r_pul, 'in1'))
    ramos = [T(ref, 'theta_ref'), T(r_deg, 'out'), sc['ens_theta0'], T(r_pul, 'out')]
    s_ref = soma('ens_theta_ref', (7480, 7680), '++++')
    for k, (ek, rk) in enumerate(zip(e, ramos)):
        lig(produto('ens_e%d_x_ramo' % k, (7400, 7560 + 60 * k), ek, rk),
            T(s_ref, ['in', 'in1', 'in2', 'in3'][k]))
    th_ref = T(s_ref, 'out')                    # <- a referencia que entra na cadeia e no receptor
    inj = produto('ens_injecao_ci', (7480, 7900), borda, e[2])

    # ======================================================= camadas da E02 em blocos nativos
    if modo == 'nativo':
        # ---- R6a folga: theta_c = max(theta, min(theta + b, theta_c[k-1])) ; b = 1,0 grau . folga_liga
        b = ganho('folga_b', (7840, 7560), P.FOLGA_GRAUS)
        lig(sc['folga_liga'], T(b, 'in'))
        s_b = soma('folga_theta_mais_b', (7920, 7600))
        m_min = novo('core/Min Max', 'folga_min', (8000, 7600), operation='min', **sp)
        m_max = novo('core/Min Max', 'folga_max', (8080, 7640), operation='max', **sp)
        ud = novo('core/Unit Delay', 'folga_memoria', (8000, 7520), init_value='0', **sp)
        lig(th_ref, T(s_b, 'in')); lig(T(b, 'out'), T(s_b, 'in1'))
        lig(T(s_b, 'out'), T(m_min, 'in')); lig(T(ud, 'out'), T(m_min, 'in1'))
        lig(th_ref, T(m_max, 'in')); lig(T(m_min, 'out'), T(m_max, 'in1'))
        th_c = T(m_max, 'out')
        # ---- E03: condicao inicial -> memoria = theta_c + inj . (theta_ref + delta0 - theta_c)
        s_ci = soma('ci_alvo_menos_cursor', (8080, 7440), '++-')
        lig(th_ref, T(s_ci, 'in')); lig(sc['ens_delta0'], T(s_ci, 'in1')); lig(th_c, T(s_ci, 'in2'))
        s_mem = soma('ci_memoria', (8160, 7480))
        lig(th_c, T(s_mem, 'in'))
        lig(produto('ci_injecao', (8120, 7440), T(s_ci, 'out'), inj), T(s_mem, 'in1'))
        lig(T(s_mem, 'out'), T(ud, 'in'))
        # ---- R6b resolucao (igual a E02)
        g_n = ganho('res_espiras_por_grau', (8160, 7380), P.N_PASSOS / P.THETA_FS)
        c_a = const('res_meio_menos_fase', (8160, 7320), 0.5 - P.FASE_ESPIRA)
        s_a = soma('res_soma_a', (8240, 7380))
        rnd = novo('core/Round', 'res_espira', (8320, 7380), round_fn='floor', **sp)
        c_f = const('res_fase', (8320, 7320), P.FASE_ESPIRA)
        s_f = soma('res_soma_fase', (8400, 7380))
        g_q = ganho('res_graus_por_espira', (8480, 7380), P.THETA_FS / P.N_PASSOS)
        lig(th_c, T(g_n, 'in')); lig(T(g_n, 'out'), T(s_a, 'in')); lig(T(c_a, 'out'), T(s_a, 'in1'))
        lig(T(s_a, 'out'), T(rnd, 'in')); lig(T(rnd, 'out'), T(s_f, 'in')); lig(T(c_f, 'out'), T(s_f, 'in1'))
        lig(T(s_f, 'out'), T(g_q, 'in'))
        d_q = soma('res_desvio', (8560, 7380), '+-')
        s_q = soma('res_saida', (8720, 7460))
        lig(T(g_q, 'out'), T(d_q, 'in')); lig(th_c, T(d_q, 'in1'))
        lig(th_c, T(s_q, 'in'))
        lig(produto('res_chave', (8640, 7380), T(d_q, 'out'), sc['res_liga']), T(s_q, 'in1'))
        th_pot = T(s_q, 'out')
        # ---- R8 ruido de contato 1/f (igual a E02)
        rs = novo('core/Random Source', 'ruido_branco', (7760, 7140), distribution='Normal',
                  mean='0.0', stddev='1.0', **sp)
        s8 = soma('kellet_soma', (8080, 7140), '+' * 8)
        ent8 = ['in'] + ['in%d' % i for i in range(1, 8)]
        for i, (p_i, g_i) in enumerate(zip(KELLET_P, KELLET_G)):
            tf = novo('core/Discrete Transfer Function', 'kellet_polo%d' % i, (7920, 6900 + 60 * i),
                      domain='Z-domain', b_coeff='[%r, 0.0]' % g_i, a_coeff='[1.0, %r]' % (-p_i), **sp)
            lig(T(rs, 'out'), T(tf, 'in')); lig(T(tf, 'out'), T(s8, ent8[i]))
        tf_at = novo('core/Discrete Transfer Function', 'kellet_atraso', (7920, 7260),
                     domain='Z-domain', b_coeff='[0.0, %r]' % KELLET_ATRASO, a_coeff='[1.0, 0.0]', **sp)
        g_d = ganho('kellet_direto', (7920, 7320), KELLET_DIRETO)
        lig(T(rs, 'out'), T(tf_at, 'in')); lig(T(tf_at, 'out'), T(s8, ent8[6]))
        lig(T(rs, 'out'), T(g_d, 'in')); lig(T(g_d, 'out'), T(s8, ent8[7]))
        g_enr = ganho('ruido_K_ENR', (8160, 7140), K_ENR)
        lig(T(s8, 'out'), T(g_enr, 'in'))
        dRc = T(g_enr, 'out')
        ud_m = novo('core/Unit Delay', 'mov_memoria', (8160, 7240), init_value='0', **sp)
        d_m = soma('mov_desvio', (8240, 7240), '+-')
        a_m = novo('core/Abs', 'mov_abs', (8320, 7240), **sp)
        sg_m = novo('core/Sign', 'mov_cursor_movendo', (8400, 7240), **sp)
        lig(th_c, T(ud_m, 'in')); lig(th_c, T(d_m, 'in')); lig(T(ud_m, 'out'), T(d_m, 'in1'))
        lig(T(d_m, 'out'), T(a_m, 'in')); lig(T(a_m, 'out'), T(sg_m, 'in'))
        p_m = produto('ruido_x_movimento', (8480, 7180), dRc, T(sg_m, 'out'))
        dRc_ativo = produto('ruido_chave', (8560, 7180), p_m, sc['ruido_liga'])
    else:
        print('   (aviso) plano B: camadas fixas na compilacao %s; sem injecao de condicao inicial'
              % (camadas_c,))

    # ======================================================= lado do sensor (IRET) - E01
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
        lig(th_ref, T(pot, 'theta'))
        lig(T(pot, 'v_cursor'), T(buf, 'in'))
        v_cur = T(pot, 'v_cursor')
    else:
        lig(th_pot, T(pot, 'theta'))
        g_ic = ganho('ruido_x_I_cursor', (8640, 7180), P.I_CURSOR)
        s_v = soma('v_cursor_mais_ruido', (8640, 7880))
        lig(dRc_ativo, T(g_ic, 'in'))
        lig(T(pot, 'v_cursor'), T(s_v, 'in')); lig(T(g_ic, 'out'), T(s_v, 'in1'))
        lig(T(s_v, 'out'), T(buf, 'in'))
        v_cur = T(s_v, 'out')

    # ======================================================= transmissor e laco - E01
    k100 = novo('core/Gain', 'XTR115_x100', (8620, 8160), gain=str(P.GANHO_XTR))
    vloop = novo('core/Voltage Source', 'V_LOOP', (8760, 8360), rot='right',
                 init_source_nature='Constant', init_const_value=str(P.V_LOOP))
    xtr = novo('core/Signal Controlled Current Source', 'XTR115_Io', (8900, 8160), rot='right')
    vtx = novo('core/Voltage Measurement', 'V_TX', (9000, 8160), rot='right',
               sig_output='True', execution_rate=DT)
    rcabo = novo('core/Resistor', 'R_cabo', (9100, 8280), rot='right', resistance=str(P.R_CABO))
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
    lig(T(xtr, 'n_node'), j_lp)
    lig(T(xtr, 'p_node'), j_io)
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
    lig(th_ref, T(rx, 'theta_ref'))

    lig(th_ref, T(sonda('theta_ref', (7560, 7480)), 'in'))
    lig(T(ref, 'theta_ref'), T(sonda('theta_ref_E01', (7960, 7720)), 'in'))
    lig(d, T(sonda('ens_disparo_sinal', (7240, 7840)), 'in'))
    lig(pulso, T(sonda('ens_pulso_sinal', (7720, 8080)), 'in'))
    lig(v_cur, T(sonda('v_cursor', (8760, 7960)), 'in'))
    if modo == 'c':
        lig(T(pot, 'theta_c'), T(sonda('theta_cursor', (8160, 7680)), 'in'))
        lig(T(pot, 'dRc'), T(sonda('dRc_ohm', (8240, 7680)), 'in'))
    else:
        lig(th_c, T(sonda('theta_cursor', (8160, 7680)), 'in'))
        lig(th_pot, T(sonda('theta_resolucao', (8800, 7460)), 'in'))
        lig(dRc, T(sonda('dRc_ohm', (8240, 7060)), 'in'))
        lig(T(rs, 'out'), T(sonda('ruido_branco_N01', (7840, 7060)), 'in'))
    lig(T(iin, 'out'), T(k_uA, 'in')); lig(T(k_uA, 'out'), T(sonda('I_IN_uA', (8760, 8300)), 'in'))
    lig(T(iloop, 'out'), T(k_mA, 'in')); lig(T(k_mA, 'out'), T(sonda('I_LOOP_mA', (9360, 8300)), 'in'))
    lig(T(vtx, 'out'), T(sonda('V_TX_V', (9120, 8120)), 'in'))
    lig(T(vrl, 'out'), T(sonda('V_RL_V', (9500, 8460)), 'in'))
    lig(T(rx, 'theta_med'), T(sonda('theta_med', (9760, 8200)), 'in'))
    lig(T(rx, 'erro_FE'), T(sonda('erro_FE_pc', (9760, 8280)), 'in'))
    lig(T(rx, 'i_mA'), T(sonda('I_receptor_mA', (9760, 8120)), 'in'))

    sinais = ['theta_ref', 'theta_med', 'I_LOOP_mA', 'V_RL_V', 'V_TX_V', 'I_IN_uA', 'v_cursor',
              'erro_FE_pc', 'I_receptor_mA', 'theta_cursor', 'dRc_ohm', 'theta_ref_E01',
              'ens_disparo_sinal', 'ens_pulso_sinal']
    if modo != 'c':
        sinais += ['theta_resolucao', 'ruido_branco_N01']
    novo('core/Scope', 'Scope_cadeia', (7600, 8300), selected_signals=sinais)

    # ======================================================= solver (igual a E02; tempo maior)
    cfg = {
        'hil_device': 'HIL101', 'hil_configuration_id': '1',
        'simulation_method': 'exact', 'simulation_time_step': 'auto',
        'solver_type': 'DAE', 'integration_method': 'BDF',
        'max_sim_step': DT, 'init_sim_step': '1e-6',
        'abs_tol': '1e-9', 'rel_tol': '1e-9',
        'simulation_time': str(E.T_SIM_SCADA),
    }
    for k, v in cfg.items():
        try:
            model.set_model_property_value(k, v)
        except Exception as ex:
            print('   (aviso) %s: %s' % (k, ex))

    model.save_as(salvar)
    ok = model.compile()
    try:
        os.remove(tmp)
    except OSError:
        pass
    return ok


# =====================================================================================
# ajustes sem mudar a topologia (usados por roda_ensaios.py)
# =====================================================================================

def ajusta_scada(**valores):
    """Com o modelo carregado, muda o valor inicial (def_value) dos SCADA Inputs dados."""
    for nome, valor in valores.items():
        model.set_property_value(model.prop(model.get_item(nome), 'def_value'), repr(float(valor)))


def aplica_ensaio_offline(ensaio, camadas=(1, 1, 1), t_auto=E.T_DISPARO, t_sim=E.T_SIM_ENSAIO):
    """Prepara uma rodada offline (sem operador): disparo automatico em t_auto."""
    ajusta_scada(ens_ensaio=ensaio, ens_disparo=0, ens_t_auto=t_auto,
                 folga_liga=camadas[0], res_liga=camadas[1], ruido_liga=camadas[2])
    model.set_model_property_value('simulation_time', str(t_sim))


def prepara_painel():
    """Volta aos valores do painel (disparo manual, tempo longo)."""
    ajusta_scada(**{n: v[0] for n, v in ENTRADAS_SCADA.items()})
    model.set_model_property_value('simulation_time', str(E.T_SIM_SCADA))


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'nativo'
    try:
        ok = monta(modo=modo)
    except Exception as ex:
        if modo != 'nativo':
            raise
        print('\n!!! modo nativo falhou (%s)\n!!! montando o plano B (camadas da E02 em C).'
              '\n!!! Para corrigir, rode inspeciona_blocos_e03.py e mande a saida.\n' % ex)
        try:
            model.close_model()
        except Exception:
            pass
        modo = 'c'
        ok = monta(modo='c')
    print('modelo E03 (%s) salvo em %s | compilou = %s' % (modo, SAIDA, ok))
    print('SCADA Inputs para o painel:')
    for n, (v, a, b, txt) in ENTRADAS_SCADA.items():
        print('   %-16s inicial=%-10g faixa=[%g, %g]  %s' % (n, v, a, b, txt))
