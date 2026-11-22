# -*- coding: utf-8 -*-
# Gera painel_monotanque_e2.cus - painel HIL SCADA da Fase 2 / Entrega 02 (Equipe G05)
# Uso (Python do Typhoon HIL Control Center 2026.2):
#   python gerar_painel_e2.py <saida.cus>
import sys
from typhoon.api.scada import panel
import typhoon.api.scada.const as c

out = sys.argv[1]
panel.create_new_panel()

INIT = """# Painel da Fase 2 / Entrega 02 - Equipe G05 (ECOM060, UFAL 2026.2)
# Funcoes comuns a todas as macros.
import time

ENSAIOS = ['(a) Degrau na bomba', '(b) Condicao inicial, bomba ligada',
           '(b) Drenagem livre, bomba desligada', '(c) Senoide na bomba']
AREAS = ['0,125 m2', '0,25 m2', '0,5 m2 (nominal)', '1 m2', '2 m2']
AREAS_V = [0.125, 0.25, 0.5, 1.0, 2.0]


def disparar():
    # borda de subida em 'disparo' zera o relogio do ensaio: o nivel fica preso no valor inicial
    # ate t = 0,5 s (50 s no tanque) e entao o ensaio comeca
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
    ini = ("# ao iniciar a simulacao o widget E a entrada do modelo voltam ao valor padrao\n"
           f"widgetValue = {default!r}\n")
    if modelo:
        ini += f"hil.set_scada_input_value({modelo[0]!r}, {float(modelo[1])!r})\n"
    P(h, c.PROP_ON_START, ini)
    P(h, c.PROP_ON_START_ENABLED, True)
    return h


def digital(name, label, sig, unit, dec, pos, size=(200, 64)):
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


# ------------------------------------------------------------------ cabecalho
t = note("Titulo", "G05 - Fase 2, Entrega 02: equivalente eletrico do Monotanque  "
         "(C dv/dt = i_i - K_e*sqrt(v) - i_d)", (16, 8), (1560, 32))
P(t, c.PROP_PANEL_INIT, INIT)
note("Escalas", "Escalas: 1 V = 10 cm de agua  |  1 A = 1 L/s  |  1 s no grafico = 100 s no tanque.  "
     "O nivel fica preso no valor inicial ate t = 0,5 s do ensaio (50 s no tanque).", (16, 40), (1560, 32))

# ------------------------------------------------------------------ coluna de controles
X, W = 16, 340
note("Sec_ensaio", "1) ENSAIO (R3)", (X, 84), (W, 32))
macro(c.WT_COMBO_MACRO, "Ensaio", "Ensaio", (X, 112), (W, 56),
      "hil.set_scada_input_value('ensaio', float(ENSAIOS.index(inputValue) + 1))\ndisparar()\n",
      "(a) Degrau na bomba",
      {c.PROP_COMBO_VALUES: ["(a) Degrau na bomba", "(b) Condicao inicial, bomba ligada",
                             "(b) Drenagem livre, bomba desligada", "(c) Senoide na bomba"]}, ("ensaio", 1))
b = panel.create_widget(c.WT_BUTTON_MACRO, name="Disparar", position=(X, 176))
P(b, c.PROP_LABEL, "DISPARAR / REPETIR ENSAIO"); P(b, c.PROP_USE_LABEL, True); P(b, c.PROP_SIZE, (W, 44))
P(b, c.PROP_ON_USE, "disparar()\n")
macro(c.WT_TEXT_MACRO, "Degrau", "Degrau na bomba [%]  (ensaio a)", (X, 230), (W, 56),
      "hil.set_scada_input_value('degrau_pct', float(inputValue))\ndisparar()\n", 20.0, modelo=("degrau_pct", 20))
macro(c.WT_TEXT_MACRO, "h_inicial", "Nivel inicial h(0) [m]  (ensaios b)", (X, 290), (W, 56),
      "hil.set_scada_input_value('h_ini_m', float(inputValue))\ndisparar()\n", 1.0, modelo=("h_ini_m", 1))
macro(c.WT_TEXT_MACRO, "Amplitude", "Amplitude da senoide [%]  (ensaio c)", (X, 350), (W, 56),
      "hil.set_scada_input_value('amp_pct', float(inputValue))\ndisparar()\n", 10.0, modelo=("amp_pct", 10))

note("Sec_param", "2) PARAMETROS DA PLANTA (R4)", (X, 420), (W, 32))
macro(c.WT_COMBO_MACRO, "Area", "Area A do tanque = capacitores ligados", (X, 448), (W, 56),
      "hil.set_scada_input_value('A_m2', AREAS_V[AREAS.index(inputValue)])\ndisparar()\n",
      "0,5 m2 (nominal)", {c.PROP_COMBO_VALUES: ["0,125 m2", "0,25 m2", "0,5 m2 (nominal)", "1 m2", "2 m2"]}, ("A_m2", 0.5))
macro(c.WT_TEXT_MACRO, "k", "Coeficiente da valvula k [m^2,5/s]", (X, 508), (W, 56),
      "hil.set_scada_input_value('k_valvula', float(inputValue))\ndisparar()\n", 0.01, modelo=("k_valvula", 0.01))
macro(c.WT_TEXT_MACRO, "qd", "Retirada qd [L/s] (aplicada na hora)", (X, 568), (W, 56),
      "hil.set_scada_input_value('qd_Ls', float(inputValue))\n", 0.0, modelo=("qd_Ls", 0))

# ------------------------------------------------------------------ leituras
note("Sec_leituras", "3) LEITURAS (ja na escala do tanque)", (X, 638), (W, 32))
digital("d_h", "Nivel h", "h_m", "m", 4, (X, 668), (165, 64))
digital("d_t", "Tempo do ensaio", "t_fisico_s", "s", 1, (X + 175, 668), (165, 64))
digital("d_qi", "Bomba qi", "qi_Ls", "L/s", 3, (X, 738), (165, 64))
digital("d_qo", "Orificio qo", "qo_Ls", "L/s", 3, (X + 175, 738), (165, 64))
digital("d_v", "Tensao no capacitor", "v_C_V", "V", 3, (X, 808), (165, 64))
digital("d_qd", "Retirada qd", "qd_Ls_med", "L/s", 3, (X + 175, 808), (165, 64))

# ------------------------------------------------------------------ graficos
XG, WG = 380, 1200
trace("Grafico_nivel", "Nivel do tanque h [m]  (eixo do tempo: 1 s = 100 s no tanque)", ["h_m"], (XG, 84),
      (WG, 470), "h [m]", [0.0, 2.1])
trace("Grafico_vazoes", "Vazoes [L/s] = correntes [A]", ["qi_Ls", "qo_Ls", "qd_Ls_med"], (XG, 564), (WG, 320),
      "vazao [L/s]", [-1.0, 13.0])

panel.save_panel_as(out)
print("painel salvo:", out)
