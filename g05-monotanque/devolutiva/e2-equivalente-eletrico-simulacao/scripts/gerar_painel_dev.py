# -*- coding: utf-8 -*-
# Gera painel_monotanque_v2.cus - painel HIL SCADA do equivalente eletrico v2 (devolutiva da F2/E02, G05)
# Uso (Python do Typhoon HIL Control Center 2026.2):  python.exe gerar_painel_dev.py <saida.cus>
import sys
from typhoon.api.scada import panel
import typhoon.api.scada.const as c

out = sys.argv[1]
panel.create_new_panel()

INIT = """# Painel do equivalente eletrico v2 - Equipe G05 (ECOM060, UFAL 2026.2)
import time

ENSAIOS = ['(a) Degrau na bomba a partir de h_op', '(b) De h(0) volta a h_op, bomba ligada',
           '(b) Drenagem livre a partir de h(0)', '(c) Senoide na bomba em h_op']
MODELOS = ['Nao linear: q = k*sqrt(h)', 'Linearizado em h_op: so o resistor R']


def disparar():
    # borda de subida em 'disparo' zera o relogio: ate t = 100 s (1 s no circuito) a bomba leva o nivel
    # ao valor inicial; ai o ensaio comeca
    hil.set_scada_input_value('disparo', 0.0)
    hil.set_scada_input_value('disparo', 1.0)
    time.sleep(0.1)
    hil.set_scada_input_value('disparo', 0.0)
"""


def P(h, prop, v):
    panel.set_property_value(h, prop, v)


def note(name, text, pos, size):
    h = panel.create_widget(c.WT_TEXT_NOTE, name=name, position=pos)
    P(h, c.PROP_TEXT, text); P(h, c.PROP_SIZE, size)
    return h


def macro(wt, name, label, pos, size, on_use, default, extra=None, modelo=None):
    h = panel.create_widget(wt, name=name, position=pos)
    P(h, c.PROP_LABEL, label); P(h, c.PROP_USE_LABEL, True); P(h, c.PROP_SIZE, size)
    for k, v in (extra or {}).items():
        P(h, k, v)
    P(h, c.PROP_ON_USE, "# HIL API: 'hil'; valor digitado/selecionado: 'inputValue'\n" + on_use)
    ini = f"widgetValue = {default!r}\n"
    if modelo:
        ini += f"hil.set_scada_input_value({modelo[0]!r}, {float(modelo[1])!r})\n"
    P(h, c.PROP_ON_START, ini)
    P(h, c.PROP_ON_START_ENABLED, True)
    return h


def texto(name, label, sig, default, pos, W):
    return macro(c.WT_TEXT_MACRO, name, label, pos, (W, 56),
                 f"hil.set_scada_input_value({sig!r}, float(inputValue))\ndisparar()\n", default,
                 modelo=(sig, default))


def digital(name, label, sig, unit, dec, pos, size=(165, 64)):
    h = panel.create_widget(c.WT_DIGITAL, name=name, position=pos)
    P(h, c.PROP_SIGNALS, sig); P(h, c.PROP_LABEL, label); P(h, c.PROP_USE_LABEL, True)
    P(h, c.PROP_UNIT, unit); P(h, c.PROP_AUTO_UNIT, False); P(h, c.PROP_DECIMALS, dec)
    P(h, c.PROP_SIZE, size); P(h, c.PROP_UPDATE_RATE, 250)
    return h


def trace(name, label, sigs, pos, size, ytitle, yrange=None, janela=12):
    h = panel.create_widget(c.WT_TRACE, name=name, position=pos)
    P(h, c.PROP_SIGNALS, [sigs, []]); P(h, c.PROP_LABEL, label); P(h, c.PROP_USE_LABEL, True)
    P(h, c.PROP_SIZE, size); P(h, c.PROP_TIME_WINDOW, janela); P(h, c.PROP_UPDATE_RATE, 250)
    P(h, c.PROP_LEGEND_ENABLED, True)
    P(h, c.PROP_Y_TITLE, ytitle); P(h, c.PROP_Y_TITLE_ENABLED, True)
    if yrange:
        P(h, c.PROP_AUTO_SCALE_ENABLED, False); P(h, c.PROP_Y_RANGE, yrange)
    return h


t = note("Titulo", "G05 - Equivalente eletrico v2 do Monotanque (devolutiva da E02): bomba -> C (tanque) -> "
         "L (inercia) + R (escoamento) + e (parte nao linear)", (16, 8), (1560, 32))
P(t, c.PROP_PANEL_INIT, INIT)
note("Escalas", "Escalas: 1 V = 10 cm de agua | 1 A = 1 L/s | 1 s no grafico = 100 s no tanque. "
     "A cada disparo a bomba leva o nivel ao valor inicial em 100 s (1 s no grafico) e o ensaio comeca.",
     (16, 40), (1560, 32))

X, W = 16, 340
note("Sec_ensaio", "1) ENSAIO", (X, 84), (W, 32))
macro(c.WT_COMBO_MACRO, "Ensaio", "Ensaio", (X, 112), (W, 56),
      "hil.set_scada_input_value('ensaio', float(ENSAIOS.index(inputValue) + 1))\ndisparar()\n",
      "(a) Degrau na bomba a partir de h_op",
      {c.PROP_COMBO_VALUES: ["(a) Degrau na bomba a partir de h_op", "(b) De h(0) volta a h_op, bomba ligada",
                             "(b) Drenagem livre a partir de h(0)", "(c) Senoide na bomba em h_op"]}, ("ensaio", 1))
b = panel.create_widget(c.WT_BUTTON_MACRO, name="Disparar", position=(X, 176))
P(b, c.PROP_LABEL, "DISPARAR / REPETIR ENSAIO"); P(b, c.PROP_USE_LABEL, True); P(b, c.PROP_SIZE, (W, 44))
P(b, c.PROP_ON_USE, "disparar()\n")
texto("h_op", "Ponto de operacao h_op [m]  (a, c)", "h_op_m", 0.5, (X, 228), W)
texto("Degrau", "Degrau na bomba [%]  (a)", "degrau_pct", 20.0, (X, 288), W)
texto("h_inicial", "Nivel inicial h(0) [m]  (b)", "h_ini_m", 1.0, (X, 348), W)
texto("Amplitude", "Amplitude da senoide [%]  (c)", "amp_pct", 10.0, (X, 408), W)
texto("Frequencia", "Frequencia da senoide [x w_c = 1/70,7 s]  (c)", "w_rel", 1.0, (X, 468), W)

note("Sec_planta", "2) PLANTA", (X, 534), (W, 32))
macro(c.WT_COMBO_MACRO, "Modelo", "Resistencia de saida", (X, 562), (W, 56),
      "hil.set_scada_input_value('modelo_orif', float(MODELOS.index(inputValue)))\ndisparar()\n",
      "Nao linear: q = k*sqrt(h)",
      {c.PROP_COMBO_VALUES: ["Nao linear: q = k*sqrt(h)", "Linearizado em h_op: so o resistor R"]},
      ("modelo_orif", 0))
texto("k", "Coeficiente da valvula k [m^2,5/s]", "k_valvula", 0.01, (X, 622), W)
macro(c.WT_TEXT_MACRO, "qd", "Consumo qd [L/s] (aplicado na hora)", (X, 682), (W, 56),
      "hil.set_scada_input_value('qd_Ls', float(inputValue))\n", 0.0, modelo=("qd_Ls", 0))

note("Sec_leituras", "3) LEITURAS (escala do tanque)", (X, 750), (W, 32))
digital("d_h", "Nivel h", "h_m", "m", 4, (X, 780))
digital("d_t", "Tempo do ensaio", "t_fisico_s", "s", 1, (X + 175, 780))
digital("d_qi", "Bomba qi", "qi_Ls", "L/s", 3, (X, 850))
digital("d_qo", "Saida q (corrente no L)", "qo_Ls", "L/s", 3, (X + 175, 850))
digital("d_v", "Tensao no capacitor", "v_C_V", "V", 3, (X, 920))
digital("d_e", "Fonte nao linear e", "e_nl_V", "V", 3, (X + 175, 920))

XG, WG = 380, 1200
trace("Grafico_nivel", "Nivel do tanque h [m]  (1 s = 100 s no tanque)", ["h_m"], (XG, 84), (WG, 440), "h [m]",
      [0.0, 2.1])
trace("Grafico_vazoes", "Vazoes [L/s] = correntes [A]", ["qi_Ls", "qo_Ls", "qd_Ls_med"], (XG, 534), (WG, 290),
      "vazao [L/s]", [-1.0, 16.0])
trace("Grafico_e", "Parte nao linear e [V] (zero = so o resistor)", ["e_nl_V"], (XG, 834), (WG, 160), "e [V]")

panel.save_panel_as(out)
print("painel salvo:", out)
