# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: monta o painel SCADA (painel_equivalente.cus) pela API.

Widgets (todos nativos do HIL SCADA):
  - caixas de texto (TextBoxMacro): Pm0, dPm, D, X  -> hil.set_scada_input_value(...)
  - botoes (MacroButton): "Aplicar degrau" / "Retirar degrau"; "Falta ON" / "Falta OFF"
  - Trace Display: delta [graus]; Pe e Pm [pu]; Delta_omega [rad/s]; grandezas eletricas (i, v_C, v_nl, V_m)
  - Digital Display: delta, Pe, i, v_C

Uso: <python da API do Typhoon> monta_painel.py   (TyphoonSim aberto)
"""
import os
import re

from typhoon.api.scada import panel
from typhoon.api.scada import const as api_const

AQUI = os.path.dirname(os.path.abspath(__file__))
CUS = os.path.join(AQUI, 'painel_equivalente.cus')

CAIXAS = (('Pm0', 'Pm0 [pu]', 0.8), ('dPm', 'dPm do degrau [pu]', 0.1),
          ('D', 'D [pu/(rad/s)]  (R = 25 D ohm)', 0.01), ('X', "X [pu]  (Pmax = 1,2/X)", 0.6))
BOTOES = (('Aplicar degrau', "hil.set_scada_input_value('degrau', 1.0)"),
          ('Retirar degrau', "hil.set_scada_input_value('degrau', 0.0)"),
          ('Falta ON (Pe = 0)', "hil.set_scada_input_value('falta', 1.0)"),
          ('Falta OFF', "hil.set_scada_input_value('falta', 0.0)"))
TRACES = (('delta [graus]', ['delta_graus']), ('Pe e Pm [pu]', ['Pe_pu', 'Pm_pu']),
          ('Delta omega [rad/s]', ['delta_omega']), ('circuito [V] e [A]', ['vC_V', 'vnl_V', 'Vm_V', 'i_A']))
DISPLAYS = (('delta_graus', 'delta [graus]'), ('Pe_pu', 'Pe [pu]'), ('i_A', 'i [A]'), ('vC_V', 'v_C [V]'),
            ('Pm_pu', 'Pm [pu]'), ('delta_omega', 'Delta omega [rad/s]'), ('Vm_V', 'V_m [V]'), ('vnl_V', 'v_nl [V]'))


def nome_ok(texto):
    """O SCADA so aceita nomes com letras, numeros e '_'."""
    return re.sub(r'[^A-Za-z0-9_]+', '_', texto).strip('_')


def prop(w, nome, valor):
    try:
        panel.set_property_value(w, nome, valor)
    except Exception as e:                           # noqa: BLE001
        print('   (aviso) %s: %s' % (nome, e))


def monta():
    panel.create_new_panel()
    y = 20
    for nome, rot, padrao in CAIXAS:
        w = panel.create_widget(api_const.WT_TEXT_MACRO, name='entrada_' + nome, position=(20, y))
        prop(w, api_const.PROP_LABEL, rot)
        prop(w, api_const.PROP_ON_USE, "hil.set_scada_input_value('%s', float(inputValue))" % nome)
        # (na 2026.2 a SCADA API nao tem set_widget_value: a caixa comeca vazia; o modelo ja
        #  comeca com o valor padrao, e o valor so' muda quando se digita e aperta Enter)
        y += 70
    for nome, codigo in BOTOES:
        w = panel.create_widget(api_const.WT_BUTTON_MACRO, name=nome_ok(nome), position=(20, y))
        prop(w, api_const.PROP_ON_USE, codigo)
        prop(w, api_const.PROP_LABEL, nome)
        y += 55
    x, y = 300, 20
    for k, (nome, sinais) in enumerate(TRACES):
        w = panel.create_widget(api_const.WT_TRACE, name=nome_ok(nome), position=(x + 470*(k % 2), y + 300*(k // 2)))
        prop(w, api_const.PROP_SIGNALS, [sinais, []])   # [analogicos, digitais]
        prop(w, api_const.PROP_TIME_WINDOW, 10)
        prop(w, api_const.PROP_SIZE, (450, 280))
        prop(w, api_const.PROP_LABEL, nome)
    for k, (sinal, rot) in enumerate(DISPLAYS):
        w = panel.create_widget(api_const.WT_DIGITAL, name='mostrador_' + sinal,
                                position=(300 + 235*(k % 4), 640 + 110*(k // 4)))
        prop(w, api_const.PROP_SIGNALS, sinal)
        prop(w, api_const.PROP_DECIMALS, 4)
        prop(w, api_const.PROP_LABEL, rot)
    panel.save_panel_as(CUS)
    return CUS


if __name__ == '__main__':
    print('painel salvo em', monta())
