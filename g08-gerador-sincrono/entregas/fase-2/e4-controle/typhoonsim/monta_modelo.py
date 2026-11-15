# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entregas 03 e 04: monta pela API o modelo unico do TyphoonSim
(instrumentacao_controle.tse): planta da E02 + campo + tensao terminal + medicao ideal + medicao real
(TP, AD637, Sallen-Key, ADC, frequencimetro) + AVR PI + PSS. So' biblioteca nativa (core), sem C function.

Cada bloco e' a transcricao de uma linha de ../sistema.py (o gabarito Python), com os mesmos coeficientes.
Duas taxas: planta a 20 us (identica a E02) e medicao/controle a 100 us.

SCADA Inputs (valor padrao = cadeia real da E03, malha aberta):
  ensaio:     Pm0, dPm, degrau, Vref0, dVref, degrau_Vref, falta
  malha:      malha (0 aberta / 1 fechada), realim_V e realim_f (0 ideal / 1 real), pss (0/1), Kpss
  cadeia real (0 desliga cada uma): eps_tp [%], tau_rms [s], nbits, sigma [V], n_cic, fclk [Hz]
  acao R5:    passa_faixa (0 = pre-filtro passa-baixas 150 Hz; 1 = passa-faixa 60 ± 5 Hz)

Uso (TyphoonSim aberto; ver ../instrucoes.md):  <python da API do Typhoon> monta_modelo.py
"""
import math
import os
import shutil
import sys

from typhoon.api.schematic_editor import model

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.dont_write_bytecode = True
import parametros_e34 as P   # noqa: E402
import sistema as S          # noqa: E402
import controle as K         # noqa: E402

TSE = os.path.join(AQUI, 'instrumentacao_controle.tse')
TP_ = repr(P.TS_SP)          # 20 us (planta)
TM_ = repr(P.TS_M)           # 100 us (medicao e controle)
NUNCA = '1e6'
SCADA = {   # nome: (padrao, min, max, unidade)
    'Pm0': (P.PM0, 0.0, 1.5, 'pu'), 'dPm': (P.DPM_DEGRAU, -0.5, 0.9, 'pu'), 'degrau': (0.0, 0.0, 1.0, '0/1'),
    'Vref0': (P.VT0, 0.8, 1.2, 'pu'), 'dVref': (P.DVREF, -0.1, 0.1, 'pu'), 'degrau_Vref': (0.0, 0.0, 1.0, '0/1'),
    'falta': (0.0, 0.0, 1.0, '0/1'),
    'malha': (0.0, 0.0, 1.0, '0/1'), 'realim_V': (1.0, 0.0, 1.0, '0/1'), 'realim_f': (1.0, 0.0, 1.0, '0/1'),
    'pss': (1.0, 0.0, 1.0, '0/1'), 'Kpss': (K.KPSS, 0.0, 100.0, 'pu/pu'),
    'eps_tp': (P.REAL['eps_tp'], -10.0, 10.0, '%'), 'tau_rms': (P.REAL['tau_rms'], 0.0, 10.0, 's'),
    'nbits': (float(P.REAL['nbits']), 0.0, 24.0, 'bits'), 'sigma': (P.REAL['sigma'], 0.0, 2.0, 'V'),
    'n_cic': (P.REAL['n_cic'], 0.0, 200.0, 'ciclos'), 'fclk': (P.REAL['fclk'], 0.0, 1e8, 'Hz'),
    'passa_faixa': (0.0, 0.0, 1.0, '0/1'),
}
# estado das entradas SCADA, lido de volta pelo painel (as caixas de texto e os botoes nao mostram o valor em uso)
ESTADOS = ['malha', 'realim_V', 'pss', 'passa_faixa', 'degrau', 'degrau_Vref', 'falta',
           'eps_tp', 'tau_rms', 'nbits', 'sigma', 'n_cic', 'fclk', 'Kpss']
SONDAS = ['V_ideal', 'V_real', 'f_ideal', 'f_real', 'Vref_ef', 'Efd', 'upss', 'delta_graus', 'Pe_pu', 'E_linha',
          'x_cond']


class Montador:
    """Pequena 'linguagem' para descrever o diagrama: cada chamada cria um bloco nativo, liga as entradas e
    devolve o terminal de saida. As posicoes seguem uma grade por secao."""

    def __init__(self):
        self.cont = {}

    def pos(self, sec):
        x0, y0 = SECOES[sec]
        k = self.cont.get(sec, 0)
        self.cont[sec] = k + 1
        return (x0 + 140*(k % 8), y0 + 90*(k // 8))

    def bloco(self, tipo, nome, sec, ent=(), taxa=TM_, saida='out', **props):
        c = model.create_component(tipo, name=nome)
        if taxa is not None:
            props.setdefault('execution_rate', taxa)
        for k, v in props.items():
            model.set_property_value(model.prop(c, k), v)
        model.set_position(c, self.pos(sec))
        for term, origem in ent:
            model.create_connection(origem, model.term(c, term))
        return model.term(c, saida) if saida else c

    # ---- atalhos
    def const(self, nome, v, sec, taxa=TM_):
        return self.bloco('core/Constant', nome, sec, taxa=taxa, value=repr(float(v)))

    def ganho(self, nome, k, x, sec, taxa=TM_):
        return self.bloco('core/Gain', nome, sec, [('in', x)], taxa=taxa, gain=repr(float(k)))

    def soma(self, nome, sinais, xs, sec, taxa=TM_):
        ts = ['in'] + ['in%d' % i for i in range(1, len(xs))]
        return self.bloco('core/Sum', nome, sec, list(zip(ts, xs)), taxa=taxa, signs=sinais)

    def prod(self, nome, xs, sec, sinais=None, taxa=TM_):
        ts = ['in'] + ['in%d' % i for i in range(1, len(xs))]
        sinais = sinais or ('*'*len(xs) if len(xs) > 2 else None)   # o numero de entradas vem de 'signs'
        kw = dict(signs=sinais) if sinais else {}
        return self.bloco('core/Product', nome, sec, list(zip(ts, xs)), taxa=taxa, **kw)

    def atraso(self, nome, x, init, sec):
        return self.bloco('core/Unit Delay', nome, sec, [('in', x)], init_value=repr(float(init)))

    def minmax(self, nome, op, a, b, sec):
        return self.bloco('core/Min Max', nome, sec, [('in', a), ('in1', b)], operation=op)

    def chave(self, nome, ctrl, se_sim, se_nao, sec, limiar=0.5):
        """out = se_sim se ctrl > limiar, senao se_nao. Terminais conferidos no codigo C gerado pela 2026.2:
        in = entrada 1, in1 = entrada 2, in2 = controle."""
        return self.bloco('core/Signal switch', nome, sec, [('in', se_sim), ('in1', se_nao), ('in2', ctrl)],
                          criterion='ctrl > threshold', threshold=repr(float(limiar)))

    def rt(self, nome, x, taxa, init, sec):
        """Rate Transition entre a planta (20 us) e a medicao/controle (100 us)."""
        return self.bloco('core/Rate Transition', nome, sec, [('in', x)], taxa=taxa, init_value=repr(float(init)))

    def arred(self, nome, x, fn, sec):
        return self.bloco('core/Round', nome, sec, [('in', x)], round_fn=fn)

    def mat(self, nome, x, fn, sec):
        return self.bloco('core/Mathematical function', nome, sec, [('in', x)], mathematical_fn=fn)

    def trig(self, nome, x, fn, sec, taxa=TM_, x2=None):
        ent = [('in', x)] + ([('in1', x2)] if x2 is not None else [])
        return self.bloco('core/Trigonometric function', nome, sec, ent, taxa=taxa, trigonometric_fn=fn, angle='Radians')

    def biquad(self, nome, x, b, a, ini, sec):
        """y = b0 x + b1 x1 + b2 x2 - a1 y1 - a2 y2 (forma direta I, com estados iniciais)."""
        x1i, x2i, y1i, y2i = ini
        sec_ = sec
        # os atrasos da saida precisam do proprio y: cria a soma primeiro com entradas ligadas depois
        x1 = self.atraso(nome + '_x1', x, x1i, sec_)
        x2 = self.atraso(nome + '_x2', x1, x2i, sec_)
        s = model.create_component('core/Sum', name=nome)
        model.set_property_value(model.prop(s, 'signs'), '+++--')
        model.set_property_value(model.prop(s, 'execution_rate'), TM_)
        model.set_position(s, self.pos(sec_))
        y = model.term(s, 'out')
        y1 = self.atraso(nome + '_y1', y, y1i, sec_)
        y2 = self.atraso(nome + '_y2', y1, y2i, sec_)
        for t, (k, v) in zip(('in', 'in1', 'in2', 'in3', 'in4'),
                             ((b[0], x), (b[1], x1), (b[2], x2), (a[1], y1), (a[2], y2))):
            model.create_connection(self.ganho(nome + '_c_' + t, k, v, sec_), model.term(s, t))
        return y


SECOES = {'scada': (6000, 6000), 'planta': (7600, 8200), 'rede': (7600, 7400), 'campo': (9000, 7400),
          'terminal': (9000, 6400), 'ideal': (10400, 6400), 'onda': (10400, 7200), 'tensao': (11800, 6400),
          'adc': (11800, 7200), 'freq': (11800, 8000), 'freq2': (11800, 8800), 'avr': (13400, 6400),
          'pss': (13400, 7200), 'sondas': (15000, 6400)}


def limpa_target():
    shutil.rmtree(TSE.replace('.tse', ' Target files'), ignore_errors=True)


def configura(tempo):
    cfg = {'hil_device': 'HIL101', 'hil_configuration_id': '1',
           'simulation_method': 'exact', 'simulation_time_step': 'auto',
           'solver_type': 'DAE', 'integration_method': 'BDF',
           'max_sim_step': TP_, 'init_sim_step': '1e-6', 'abs_tol': '1e-9', 'rel_tol': '1e-9',
           'simulation_time': repr(float(tempo))}
    for k, v in cfg.items():
        try:
            model.set_model_property_value(k, v)
        except Exception as e:                       # noqa: BLE001
            print('   (aviso) %s: %s' % (k, e))


def scada_de(cfg):
    """Valores dos SCADA Inputs que reproduzem uma configuracao do gabarito (sistema.cfg_padrao)."""
    return dict(malha=1.0 if cfg['malha'] == 'fechada' else 0.0,
                realim_V=1.0 if cfg['fb_v'] == 'real' else 0.0, realim_f=1.0 if cfg['fb_f'] == 'real' else 0.0,
                pss=1.0 if cfg['pss'] else 0.0, Kpss=cfg['kpss'], Vref0=cfg['vref'],
                eps_tp=cfg['eps_tp'], tau_rms=cfg['tau_rms'], nbits=float(cfg['nbits']), sigma=cfg['sigma'],
                n_cic=cfg['n_cic'], fclk=cfg['fclk'], passa_faixa=1.0 if cfg.get('pf_bw', 0) > 0 else 0.0)


def eventos_de(ens):
    """Instantes dos degraus temporizados de cada ensaio (os demais ficam em 'nunca')."""
    n = ens['nome']
    ev = dict(degrau_temporizado=NUNCA, degrau_Vref_temporizado=NUNCA, falta_inicio=NUNCA, falta_fim=NUNCA)
    if n in ('a', 'p'):
        ev['degrau_temporizado'] = repr(P.T_EV)
    if n == 'r':
        ev['degrau_Vref_temporizado'] = repr(P.T_EV)
    if n in ('c', 'f'):
        ev['falta_inicio'] = repr(P.T_EV); ev['falta_fim'] = repr(P.T_EV + P.DUR_FALTA)
    return ev


def monta(tempo=12.0, ens=None, cfg=None, destino=TSE, compilar=True, fechar=True):
    """Monta o .tse no estado de um ensaio: estados iniciais (capacitor, atrasos, filtros, integrador),
    SCADA Inputs e degraus temporizados. Padrao: ensaio (a) da E03, malha aberta, cadeia real, sem degrau
    temporizado (o degrau e' dado no painel)."""
    sc_val = dict(SCADA)
    if cfg is not None:                       # ensaio do gabarito: SCADA Inputs reproduzem a configuracao
        for k_, v_ in scada_de(cfg).items():
            sc_val[k_] = (v_,) + SCADA[k_][1:]
    ens = ens or S.ensaio('a')
    cfg = cfg or S.cfg_padrao()               # padrao: malha aberta (realim. real e PSS prontos no SCADA)
    ini = S.estado_inicial(ens, cfg)
    m = Montador()
    model.create_new_model('instrumentacao_controle')
    T = model.term

    # ================================================= SCADA Inputs
    sc = {nome: m.bloco('core/SCADA Input', nome, 'scada', def_value=repr(float(v)), min=repr(float(lo)),
                        max=repr(float(hi)), unit=un)
          for nome, (v, lo, hi, un) in sc_val.items()}

    # ================================================= planta: estagio de potencia da E02 (malha unica)
    # Signal Controlled Voltage Source: na 2026.2, a 'Voltage Source' com sig_input='True' compilou como fonte
    # constante de 0 V e ignorou o sinal de Pm (visto na E02)
    vm = m.bloco('core/Signal Controlled Voltage Source', 'V_m', 'planta', taxa=None, saida=None)
    model.set_rotation(vm, 'right')
    idw = m.bloco('core/Current Measurement', 'I_dw', 'planta', taxa=TP_, saida=None, sig_output='True')
    lin = m.bloco('core/Inductor', 'L_inercia', 'planta', taxa=None, saida=None, inductance=repr(P.L_EQ),
                  initial_current='0.0')
    res = m.bloco('core/Resistor', 'R_amortec', 'planta', taxa=None, saida=None, resistance=repr(P.KV*P.D/P.KI))
    cap = m.bloco('core/Capacitor', 'C_sincron', 'planta', taxa=None, saida=None, capacitance=repr(P.C_EQ),
                  initial_voltage=repr(ini['vC0']))
    fnl = m.bloco('core/Signal Controlled Voltage Source', 'v_nl', 'planta', taxa=None, saida=None)
    vvc = m.bloco('core/Voltage Measurement', 'V_vC', 'planta', taxa=TP_, saida=None, sig_output='True')
    gnd = m.bloco('core/Ground', 'terra', 'planta', taxa=None, saida=None)
    lig = model.create_connection
    lig(T(vm, 'p_node'), T(idw, 'p_node')); lig(T(idw, 'n_node'), T(lin, 'p_node'))
    lig(T(lin, 'n_node'), T(res, 'p_node')); lig(T(res, 'n_node'), T(cap, 'p_node'))
    lig(T(cap, 'p_node'), T(vvc, 'p_node')); lig(T(cap, 'n_node'), T(vvc, 'n_node'))
    lig(T(cap, 'n_node'), T(fnl, 'p_node')); lig(T(fnl, 'n_node'), T(gnd, 'node'))
    lig(T(vm, 'n_node'), T(gnd, 'node'))
    vC = T(vvc, 'out')

    # ================================================= entradas da planta e rede (100 us)
    st_pm = m.bloco('core/Step', 'degrau_temporizado', 'rede', step_time=NUNCA, initial_value='0.0', final_value='1.0')
    dg = m.soma('degrau_total', '++', [sc['degrau'], st_pm], 'rede')
    Pm = m.soma('Pm', '++', [sc['Pm0'], m.prod('dPm_x_degrau', [sc['dPm'], dg], 'rede')], 'rede')
    model.create_connection(m.ganho('KV_x_Pm', P.KV, m.rt('RT_Pm', Pm, TP_, P.PM0, 'rede'), 'rede', taxa=TP_), T(vm, 'in'))
    f_ini = m.bloco('core/Step', 'falta_inicio', 'rede', step_time=NUNCA, initial_value='0.0', final_value='1.0')
    f_fim = m.bloco('core/Step', 'falta_fim', 'rede', step_time=NUNCA, initial_value='0.0', final_value='1.0')
    falta = m.minmax('falta_0_1', 'min', m.soma('falta_total', '++-', [sc['falta'], f_ini, f_fim], 'rede'),
                     m.const('um_falta', 1.0, 'rede'), 'rede')
    sem_falta = m.soma('rede_1_menos_falta', '+-', [m.const('um', 1.0, 'rede'), falta], 'rede')

    # ================================================= campo: ΔE'[k+1] = ezf ΔE'[k] + (1-ezf)(Efd - E'0)
    Ep0 = m.const('E_linha_0', ini['Ep0'], 'campo')
    efd_ap_holder = model.create_component('core/Signal switch', name='Efd_aplicado')
    for k_, v_ in (('criterion', 'ctrl > threshold'), ('threshold', '0.5'), ('execution_rate', TM_)):
        model.set_property_value(model.prop(efd_ap_holder, k_), v_)
    model.set_position(efd_ap_holder, m.pos('campo'))
    Efd_ap = T(efd_ap_holder, 'out')
    dEfd = m.soma('dEfd', '+-', [Efd_ap, Ep0], 'campo')
    ezf = math.exp(-P.TS_M/P.TDO)
    s_campo = model.create_component('core/Sum', name='campo_novo')
    model.set_property_value(model.prop(s_campo, 'signs'), '++')
    model.set_property_value(model.prop(s_campo, 'execution_rate'), TM_)
    model.set_position(s_campo, m.pos('campo'))
    dE_novo = T(s_campo, 'out')
    dE = m.atraso('campo_dE', dE_novo, 0.0, 'campo')
    lig(m.ganho('campo_ezf', ezf, dE, 'campo'), T(s_campo, 'in'))
    lig(m.ganho('campo_1_menos_ezf', 1 - ezf, dEfd, 'campo'), T(s_campo, 'in1'))
    E_med = m.soma('E_linha_med', '++', [Ep0, dE], 'campo')            # E' visto pela medicao (amostra k)
    E_pl = m.soma('E_linha_planta', '++', [Ep0, dE_novo], 'campo')  # E' aplicado a planta ate k+1
    pmax = m.prod('Pmax_t', [m.ganho('V_sobre_X', P.V_BAR/P.X_TOT, E_pl, 'campo'), sem_falta], 'campo')

    # ================================================= fonte nao linear (20 us, como na E02)
    d20 = m.soma('delta', '++', [m.ganho('vC_para_rad', 1/P.KV_DELTA, vC, 'planta', taxa=TP_),
                                  m.const('delta0', P.DELTA0, 'planta', taxa=TP_)], 'planta', taxa=TP_)
    pmax0 = ini['Ep0']*P.V_BAR/P.X_TOT*(1.0 - ens['falta'](0.0))
    pe = m.prod('Pe', [m.rt('RT_Pmax', pmax, TP_, pmax0, 'planta'), m.trig('sen_delta', d20, 'sin', 'planta', taxa=TP_)], 'planta', taxa=TP_)
    vnl = m.soma('menos_vC', '+-', [m.ganho('KV_x_Pe', P.KV, pe, 'planta', taxa=TP_), vC], 'planta', taxa=TP_)
    lig(vnl, T(fnl, 'in'))

    # ================================================= tensao terminal (100 us)
    dm = m.soma('delta_m', '++', [m.ganho('vC_para_rad_m', 1/P.KV_DELTA, m.rt('RT_vC', vC, TM_, ini['vC0'], 'terminal'), 'terminal'),
                                   m.const('delta0_m', P.DELTA0, 'terminal')], 'terminal')
    vth = m.ganho('Vth', P.V_BAR, sem_falta, 'terminal')
    xth = m.soma('Xth', '++', [m.const('Xe', P.XE, 'terminal'), m.ganho('XT_menos_Xe', P.XT - P.XE, falta, 'terminal')], 'terminal')
    den = m.soma('Xd_mais_Xth', '++', [m.const('Xdp', P.XDP, 'terminal'), xth], 'terminal')
    Ecos = m.prod('E_cos', [E_med, m.trig('cos_delta', dm, 'cos', 'terminal')], 'terminal')
    Esin = m.prod('E_sen', [E_med, m.trig('sen_delta_m', dm, 'sin', 'terminal')], 'terminal')
    re = m.prod('Vt_re', [m.soma('num_re', '++', [m.ganho('Xdp_Vth', P.XDP, vth, 'terminal'),
                                                  m.prod('Xth_Ecos', [xth, Ecos], 'terminal')], 'terminal'), den],
                'terminal', sinais='*/')
    im = m.prod('Vt_im', [m.prod('Xth_Esen', [xth, Esin], 'terminal'), den], 'terminal', sinais='*/')
    Vt = m.mat('Vt_mod', m.soma('Vt_quad', '++', [m.prod('re2', [re, re], 'terminal'), m.prod('im2', [im, im], 'terminal')], 'terminal'),
               'sqrt', 'terminal')
    th = m.trig('theta_t', im, 'atan2', 'terminal', x2=re)        # 2026.2 gera atan2(in, in1): in = y (imag.), in1 = x (real)

    # ================================================= medicao IDEAL
    th_ant = m.atraso('theta_ant', th, ini['th0'], 'ideal')
    dth = m.soma('dtheta', '+-', [th, th_ant], 'ideal')
    volta = m.arred('voltas', m.ganho('dtheta_sobre_2pi', 1/(2*math.pi), dth, 'ideal'), 'round', 'ideal')
    dthw = m.soma('dtheta_desdobrado', '+-', [dth, m.ganho('2pi_voltas', 2*math.pi, volta, 'ideal')], 'ideal')
    f_id = m.soma('f_ideal_calc', '++', [m.const('f0', P.F_REDE, 'ideal'),
                                    m.ganho('dtheta_para_Hz', 1/(2*math.pi*P.TS_M), dthw, 'ideal')], 'ideal')
    V_id = Vt

    # ================================================= forma de onda: TP + divisor + ruido
    # reset em 1 s - Ts/2: somar 10 000 vezes 1e-4 da' 0,99999999999991 < 1,0, e com reset_at = 1,0 o relogio
    # ganhava um passo a mais (100 us) a cada segundo; a fase da onda e o frequencimetro saltavam juntos, e o
    # pre-filtro passa-faixa (memoria de ~30 ms) transformava o salto num erro de 0,06 Hz por segundo
    relogio = m.bloco('core/Clock', 'relogio_1s', 'onda', enb_reset='True', reset_at=repr(1.0 - P.TS_M/2))
    fase = m.soma('fase', '++', [m.ganho('omega_s', P.W_S, relogio, 'onda'), th], 'onda')
    v_p = m.prod('v_primario', [m.ganho('pico_primario', math.sqrt(2)*P.V_BASE, Vt, 'onda'),
                                m.trig('cos_fase', fase, 'cos', 'onda')], 'onda')
    um_eps = m.soma('um_mais_eps', '++', [m.const('um_tp', 1.0, 'onda'), m.ganho('eps_pct', 0.01, sc['eps_tp'], 'onda')], 'onda')
    v_s = m.prod('TP_relacao', [m.ganho('TP_1_sobre_RTP', 1/P.RTP, v_p, 'onda'), um_eps], 'onda')
    v_d = m.ganho('divisor', P.K_DIV, v_s, 'onda')
    rnd = m.bloco('core/Random Source', 'ruido_branco', 'onda', distribution='Normal', mean='0.0', stddev='1.0')
    x = m.soma('x_condicionado', '++', [v_d, m.prod('ruido_x_sigma', [rnd, sc['sigma']], 'onda')], 'onda')

    # ================================================= tensao REAL: AD637 implicito + Sallen-Key + ADC
    tau = sc['tau_rms']
    ts_tau = m.prod('Ts_sobre_tau', [m.const('Ts_m', P.TS_M, 'tensao'),
                                     m.minmax('tau_min', 'max', tau, m.const('tau_piso', 1e-9, 'tensao'), 'tensao')],
                    'tensao', sinais='*/')
    a1 = m.soma('a1', '+-', [m.const('um_a1', 1.0, 'tensao'), m.mat('exp_menos', m.ganho('menos', -1.0, ts_tau, 'tensao'),
                                                                     'exponential', 'tensao')], 'tensao')
    s_ad = model.create_component('core/Sum', name='AD637_saida')
    model.set_property_value(model.prop(s_ad, 'signs'), '++')
    model.set_property_value(model.prop(s_ad, 'execution_rate'), TM_)
    model.set_position(s_ad, m.pos('tensao'))
    u_novo = T(s_ad, 'out')
    u = m.atraso('AD637_Cav', u_novo, ini['u0'], 'tensao')
    q = m.prod('x2_sobre_Vo', [m.prod('x_quadrado', [x, x], 'tensao'),
                                m.minmax('Vo_min', 'max', u, m.const('Vo_piso', 1e-3, 'tensao'), 'tensao')], 'tensao', sinais='*/')
    lig(u, T(s_ad, 'in'))
    lig(m.prod('a1_x_erro', [a1, m.soma('erro_AD637', '+-', [q, u], 'tensao')], 'tensao'), T(s_ad, 'in1'))
    sk = m.biquad('SallenKey', u_novo, S.B_SK, S.A_SK, (ini['u0'],)*4, 'tensao')
    v_byp = m.ganho('rms_exato', P.V_PU_VD, m.prod('Vt_x_1eps', [Vt, um_eps], 'tensao'), 'tensao')
    s_conv = m.chave('dinamica_ligada', tau, sk, v_byp, 'tensao', limiar=0.0)
    # ADC: lsb = Vref/2^n ; cod = min(max(round(s/lsb), 0), 2^n - 1) ; s = cod*lsb
    nb = sc['nbits']
    dois_n = m.mat('dois_a_n', m.ganho('n_ln2', math.log(2), nb, 'adc'), 'exponential', 'adc')
    lsb = m.prod('lsb', [m.const('Vref_adc', P.VREF_ADC, 'adc'), dois_n], 'adc', sinais='*/')
    cod = m.arred('codigo', m.prod('s_sobre_lsb', [s_conv, lsb], 'adc', sinais='*/'), 'round', 'adc')
    cod = m.minmax('codigo_max', 'min', m.minmax('codigo_min', 'max', cod, m.const('zero_adc', 0.0, 'adc'), 'adc'),
                   m.soma('n_codigos', '+-', [dois_n, m.const('um_adc', 1.0, 'adc')], 'adc'), 'adc')
    s_adc = m.chave('adc_ligado', nb, m.prod('cod_x_lsb', [cod, lsb], 'adc'), s_conv, 'adc', limiar=0.0)
    V_re = m.ganho('V_por_pu', 1/P.V_PU_VD, s_adc, 'adc')

    # ================================================= frequencia REAL
    y_pb = m.biquad('prefiltro_pb', x, S.B_PF, S.A_PF, ini['pf']['pb'], 'freq')
    bpf, apf = S.biquad_pf(P.F_REDE, 10.0)
    y_pf = m.biquad('prefiltro_pf', x, bpf, apf, ini['pf']['pf'], 'freq')
    y = m.chave('prefiltro_escolha', sc['passa_faixa'], y_pf, y_pb, 'freq')
    hst = m.bloco('core/Hysteresis Function', 'comparador', 'freq', [('in', y)], up_thr=repr(P.HIST),
                  low_thr=repr(-P.HIST), high_out='1', low_out='0', init_state='high' if ini['hist_alto'] else 'low')
    hst_ant = m.atraso('comparador_ant', hst, 1.0 if ini['hist_alto'] else 0.0, 'freq')
    borda = m.prod('borda_subida', [hst, m.soma('nao_ant', '+-', [m.const('um_b', 1.0, 'freq'), hst_ant], 'freq')], 'freq')
    y_ant = m.atraso('y_ant', y, ini['yant'], 'freq')
    fi = m.prod('fracao', [m.soma('y_menos_h', '+-', [y, m.const('histerese', P.HIST, 'freq')], 'freq'),
                           m.minmax('dy_min', 'max', m.soma('dy', '+-', [y, y_ant], 'freq'),
                                    m.const('dy_piso', 1e-9, 'freq'), 'freq')], 'freq', sinais='*/')
    tc = m.soma('t_cruzamento', '+-', [relogio, m.ganho('fi_x_Ts', P.TS_M, fi, 'freq')], 'freq')
    fclk = sc['fclk']
    fck = m.minmax('fclk_min', 'max', fclk, m.const('fclk_piso', 1.0, 'freq2'), 'freq2')
    qc = m.prod('captura_q', [m.arred('captura_tiques', m.prod('tc_x_fclk', [tc, fck], 'freq2'), 'floor', 'freq2'), fck],
                'freq2', sinais='*/')
    qq = m.chave('relogio_ligado', fclk, qc, tc, 'freq2', limiar=0.0)
    s_q = model.create_component('core/Signal switch', name='q_trava')
    for k_, v_ in (('criterion', 'ctrl > threshold'), ('threshold', '0.5'), ('execution_rate', TM_)):
        model.set_property_value(model.prop(s_q, k_), v_)
    model.set_position(s_q, m.pos('freq2'))
    q_ult = m.atraso('q_ultimo', T(s_q, 'out'), 0.0, 'freq2')
    lig(qq, T(s_q, 'in')); lig(q_ult, T(s_q, 'in1')); lig(borda, T(s_q, 'in2'))   # in2 = controle
    s_g = model.create_component('core/Min Max', name='porta_nova')
    model.set_property_value(model.prop(s_g, 'operation'), 'min')
    model.set_property_value(model.prop(s_g, 'execution_rate'), TM_)
    model.set_position(s_g, m.pos('freq2'))
    porta = m.atraso('porta', T(s_g, 'out'), 0.0, 'freq2')
    lig(m.soma('porta_mais_borda', '++', [porta, borda], 'freq2'), T(s_g, 'in')); lig(m.const('dois', 2.0, 'freq2'), T(s_g, 'in1'))
    valido = m.prod('valido', [borda, m.minmax('porta_1', 'min', porta, m.const('um_p', 1.0, 'freq2'), 'freq2')], 'freq2')
    Tq = m.soma('periodo_bruto', '+-', [qq, q_ult], 'freq2')
    Tp = m.soma('periodo', '+-', [Tq, m.arred('volta_relogio', Tq, 'floor', 'freq2')], 'freq2')
    fc = m.prod('f_ciclo', [m.const('um_f', 1.0, 'freq2'), m.minmax('T_min', 'max', Tp, m.const('T_piso', 1e-3, 'freq2'), 'freq2')],
                'freq2', sinais='*/')
    s_F = model.create_component('core/Sum', name='F_nova')
    model.set_property_value(model.prop(s_F, 'signs'), '++')
    model.set_property_value(model.prop(s_F, 'execution_rate'), TM_)
    model.set_position(s_F, m.pos('freq2'))
    F_novo = T(s_F, 'out')
    F = m.atraso('F_media', F_novo, P.F_REDE, 'freq2')
    ncic = sc['n_cic']
    passo = m.prod('passo_media', [valido, m.soma('fc_menos_F', '+-', [fc, F], 'freq2'),
                                   m.minmax('N_min', 'max', ncic, m.const('N_piso', 1.0, 'freq2'), 'freq2')], 'freq2', sinais='**/')
    lig(F, T(s_F, 'in')); lig(passo, T(s_F, 'in1'))
    f_re = m.chave('frequencimetro_ligado', ncic, F_novo, f_id, 'freq2', limiar=0.0)

    # ================================================= controle: AVR PI + PSS
    Vfb = m.chave('realimenta_V', sc['realim_V'], V_re, V_id, 'avr')
    ffb = m.chave('realimenta_f', sc['realim_f'], f_re, f_id, 'pss')
    xin = m.ganho('df_pu', 1/P.F_REDE, m.soma('f_menos_60', '+-', [ffb, m.const('f0_pss', P.F_REDE, 'pss')], 'pss'), 'pss')
    z = xin
    for j, (b0, b1, a1_) in enumerate(K.PSS_Z):
        z = m.bloco('core/Discrete Transfer Function', ['PSS_lavagem', 'PSS_avanco_1', 'PSS_avanco_2'][j], 'pss',
                    [('in', z)], domain='Z-domain', b_coeff=repr([b0, b1]), a_coeff=repr([1.0, a1_]))
    upss = m.bloco('core/Limit', 'PSS_limite', 'pss',
                   [('in', m.prod('PSS_ganho', [z, sc['Kpss'], sc['pss']], 'pss'))],
                   upper_limit=repr(K.VST_MAX), lower_limit=repr(-K.VST_MAX))
    st_vr = m.bloco('core/Step', 'degrau_Vref_temporizado', 'avr', step_time=NUNCA, initial_value='0.0', final_value='1.0')
    vref = m.soma('Vref', '++', [sc['Vref0'],
                                 m.prod('dVref_x_degrau', [sc['dVref'],
                                                           m.soma('degrau_Vref_total', '++', [sc['degrau_Vref'], st_vr], 'avr')], 'avr')], 'avr')
    e = m.soma('erro_V', '++-', [vref, upss, Vfb], 'avr')
    s_xi = model.create_component('core/Limit', name='PI_integrador_limite')
    for k_, v_ in (('upper_limit', repr(P.EFD_MAX)), ('lower_limit', repr(P.EFD_MIN)), ('execution_rate', TM_)):
        model.set_property_value(model.prop(s_xi, k_), v_)
    model.set_position(s_xi, m.pos('avr'))
    xI = m.atraso('PI_integrador', T(s_xi, 'out'), ini['xI0'], 'avr')
    lig(m.soma('PI_acumula', '++', [xI, m.ganho('Ki_Ts', K.KI*P.TS_M, e, 'avr')], 'avr'), T(s_xi, 'in'))
    Efd = m.bloco('core/Limit', 'Efd_limite', 'avr', [('in', m.soma('PI_saida', '++', [m.ganho('Kp', K.KP, e, 'avr'), xI], 'avr'))],
                  upper_limit=repr(P.EFD_MAX), lower_limit=repr(P.EFD_MIN))
    lig(Efd, T(efd_ap_holder, 'in')); lig(Ep0, T(efd_ap_holder, 'in1')); lig(sc['malha'], T(efd_ap_holder, 'in2'))   # in2 = controle

    # ================================================= sondas
    vref_ef = m.soma('Vref_efetiva', '++', [vref, upss], 'sondas')
    for nome, origem in (('V_ideal', V_id), ('V_real', V_re), ('f_ideal', f_id), ('f_real', f_re), ('Vref_ef', vref_ef),
                         ('Efd', Efd_ap), ('upss', upss), ('delta_graus', m.ganho('rad_graus', 180/math.pi, dm, 'sondas')),
                         ('Pe_pu', pe), ('E_linha', E_med), ('x_cond', x)):
        lig(origem, T(m.bloco('core/Probe', nome, 'sondas', taxa=None, saida=None), 'in'))
    m.bloco('core/Scope', 'Scope_e3e4', 'sondas', taxa=None, saida=None, selected_signals=SONDAS)
    for nome in ESTADOS:
        lig(sc[nome], T(m.bloco('core/Probe', 'ver_' + nome, 'sondas', taxa=None, saida=None), 'in'))

    configura(tempo)
    model.save_as(destino)
    ok = model.compile() if compilar else None
    if fechar:
        model.close_model()
        limpa_target()
    return ok


def aplica_eventos(ens):
    for nome, t in eventos_de(ens).items():
        model.set_property_value(model.prop(model.get_item(nome), 'step_time'), t)


if __name__ == '__main__':
    print('modelo salvo em %s | compilou = %s' % (TSE, monta()))
