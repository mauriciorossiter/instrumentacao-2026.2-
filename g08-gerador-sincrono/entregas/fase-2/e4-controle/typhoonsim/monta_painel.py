# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E03 e E04: monta o painel SCADA (painel_e3e4.cus) pela API.

Coluna 1 (ensaios):     botoes degrau de Pm, degrau de Vref, falta; malha aberta/fechada; realimentacao
                        ideal/real; PSS liga/desliga; passa-faixa (acao do R5 da E04)
Coluna 2 (instrumento): caixas de texto com as seis caracteristicas da cadeia real (0 desliga cada uma)
                        e o ganho do PSS; botoes "cadeia ideal" e "cadeia real (padrao)"
Graficos: tensao (ideal, real, Vref efetiva); frequencia (ideal, real); Efd e saida do PSS; δ.
Mostradores: V real, V ideal, f real, Efd.

Uso: <python da API do Typhoon> monta_painel.py   (TyphoonSim aberto)
"""
import os
import re
import sys

from typhoon.api.scada import panel
from typhoon.api.scada import const as api_const

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.dont_write_bytecode = True
import parametros_e34 as P   # noqa: E402
import controle as K         # noqa: E402

CUS = os.path.join(AQUI, 'painel_e3e4.cus')


def sc(nome, v):
    return "hil.set_scada_input_value('%s', %r)" % (nome, float(v))


# nomes curtos: o SCADA mostra o NOME do widget ao lado do botao, cortado em ~7 caracteres
BOTOES = (
    ('Pm ON', sc('degrau', 1)), ('Pm OFF', sc('degrau', 0)),
    ('Vref ON', sc('degrau_Vref', 1)), ('VrefOFF', sc('degrau_Vref', 0)),
    ('FaltaON', sc('falta', 1)), ('FaltOFF', sc('falta', 0)),
    ('FECHAR', sc('malha', 1)), ('ABRIR', sc('malha', 0)),
    ('FB REAL', sc('realim_V', 1) + '\n' + sc('realim_f', 1)),
    ('FBIDEAL', sc('realim_V', 0) + '\n' + sc('realim_f', 0)),
    ('PSS ON', sc('pss', 1)), ('PSS OFF', sc('pss', 0)),
    ('PF  R5', sc('passa_faixa', 1)), ('PB 150', sc('passa_faixa', 0)),
)
CAIXAS = (('eps_tp', 'erro do TP [%]  (0 desliga)', P.REAL['eps_tp']),
          ('tau_rms', 'tau do AD637 [s]  (25 ms/uF x C_AV; 0 desliga)', P.REAL['tau_rms']),
          ('nbits', 'bits do ADC  (0 desliga)', P.REAL['nbits']),
          ('sigma', 'ruido no secundario [V rms]  (0 desliga)', P.REAL['sigma']),
          ('n_cic', 'media do frequencimetro [ciclos]  (0 = f ideal)', P.REAL['n_cic']),
          ('fclk', 'relogio do contador [Hz]  (0 desliga)', P.REAL['fclk']),
          ('Kpss', 'ganho do PSS [pu/pu]', K.KPSS))
CAIXA_SONDA = {'eps_tp': 'ver_eps_tp', 'tau_rms': 'ver_tau_rms', 'nbits': 'ver_nbits', 'sigma': 'ver_sigma',
               'n_cic': 'ver_n_cic', 'fclk': 'ver_fclk', 'Kpss': 'ver_Kpss'}
ESTADO = (('ver_malha', 'malha (1 = fechada)'), ('ver_realim_V', 'realimentacao (1 = real)'), ('ver_pss', 'PSS (1 = ligado)'),
          ('ver_passa_faixa', 'prefiltro (1 = passa-faixa)'), ('ver_degrau', 'degrau Pm'), ('ver_degrau_Vref', 'degrau Vref'),
          ('ver_falta', 'falta'))
TRACES = (('Tensao terminal [pu]', ['V_ideal', 'V_real', 'Vref_ef']), ('Frequencia [Hz]', ['f_ideal', 'f_real']),
          ('Efd e PSS [pu]', ['Efd', 'upss']), ('Angulo delta [graus]', ['delta_graus']))
DISPLAYS = (('V_real', 'V medida [pu]'), ('V_ideal', 'V real da planta [pu]'), ('f_real', 'f medida [Hz]'), ('Efd', 'Efd [pu]'))


def nome_ok(texto):
    return re.sub(r'[^A-Za-z0-9_]+', '_', texto).strip('_')


def prop(w, nome, valor):
    try:
        panel.set_property_value(w, nome, valor)
    except Exception as e:                           # noqa: BLE001
        print('   (aviso) %s: %s' % (nome, e))


def monta():
    panel.create_new_panel()
    y = 20
    for nome, codigo in BOTOES:
        w = panel.create_widget(api_const.WT_BUTTON_MACRO, name=nome_ok(nome), position=(20, y))
        prop(w, api_const.PROP_ON_USE, codigo)
        prop(w, api_const.PROP_LABEL, nome)
        y += 48
    y = 20
    for nome, rot, padrao in CAIXAS:
        w = panel.create_widget(api_const.WT_TEXT_MACRO, name=nome, position=(250, y))
        prop(w, api_const.PROP_LABEL, rot)
        prop(w, api_const.PROP_ON_USE, "hil.set_scada_input_value('%s', float(inputValue))" % nome)
        # sem ON_START: na 2026.2 a SCADA API nao tem set_widget_value (a caixa comeca vazia; o modelo ja
        # parte do valor padrao, mostrado no rotulo)
        prop(w, api_const.PROP_LABEL, '%s  [padrao %s]' % (rot, repr(padrao)))
        d = panel.create_widget(api_const.WT_DIGITAL, name='em_uso_' + nome, position=(400, y))
        prop(d, api_const.PROP_SIGNALS, CAIXA_SONDA[nome])
        prop(d, api_const.PROP_DECIMALS, 4)
        prop(d, api_const.PROP_LABEL, 'em uso')
        y += 68
    neutro = '\n'.join(sc(k, 0) for k in ('eps_tp', 'tau_rms', 'nbits', 'sigma', 'n_cic', 'fclk'))
    real = '\n'.join(sc(k, P.REAL[k]) for k in ('eps_tp', 'tau_rms', 'nbits', 'sigma', 'n_cic', 'fclk'))
    for k, (rot, cod) in enumerate((('IDEAL', neutro), ('REAL', real))):   # cadeia ideal / cadeia real (padrao)
        w = panel.create_widget(api_const.WT_BUTTON_MACRO, name=nome_ok(rot), position=(250, y + 48*k))
        prop(w, api_const.PROP_ON_USE, cod)
        prop(w, api_const.PROP_LABEL, rot)
    x, y = 620, 20
    for k, (nome, sinais) in enumerate(TRACES):
        w = panel.create_widget(api_const.WT_TRACE, name=nome_ok(nome), position=(x + 470*(k % 2), y + 300*(k // 2)))
        prop(w, api_const.PROP_SIGNALS, [sinais, []])
        prop(w, api_const.PROP_TIME_WINDOW, 10)
        prop(w, api_const.PROP_SIZE, (450, 280))
        prop(w, api_const.PROP_LABEL, nome)
    for k, (sinal, rot) in enumerate(DISPLAYS):
        w = panel.create_widget(api_const.WT_DIGITAL, name='mostrador_' + sinal, position=(620 + 235*k, 640))
        prop(w, api_const.PROP_SIGNALS, sinal)
        prop(w, api_const.PROP_DECIMALS, 4)
        prop(w, api_const.PROP_LABEL, rot)
    for k, (sinal, rot) in enumerate(ESTADO):
        w = panel.create_widget(api_const.WT_DIGITAL, name='estado_' + sinal[4:], position=(20 + 180*k, 740))
        prop(w, api_const.PROP_SIGNALS, sinal)
        prop(w, api_const.PROP_DECIMALS, 0)
        prop(w, api_const.PROP_LABEL, rot)
    panel.save_panel_as(CUS)
    return CUS


if __name__ == '__main__':
    print('painel salvo em', monta())
