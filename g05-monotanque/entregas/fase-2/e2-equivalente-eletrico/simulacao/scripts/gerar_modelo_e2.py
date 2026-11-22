# -*- coding: utf-8 -*-
# Gera monotanque_equivalente_eletrico.tse
# ECOM060 - Fase 2 / Entrega 02 - Equipe G05: equivalente eletrico do Monotanque no TyphoonSim.
#
#   A dh/dt = qi - k*sqrt(h) - qd      (Entrega 01)
#   C dv/dt = i_i - K_e*sqrt(v) - i_d  (circuito)
#
# Uso (Python do Typhoon HIL Control Center 2026.2):
#   "C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe" gerar_modelo_e2.py <saida.tse>
import sys
import json
from typhoon.api.schematic_editor import SchematicAPI

out = sys.argv[1]
m = SchematicAPI()
m.create_new_model("monotanque_equivalente_eletrico")

for k, v in dict(solver_type="DAE", integration_method="BDF", max_sim_step="1e-4", init_sim_step="1e-6",
                 abs_tol="1e-7", rel_tol="1e-7", simulation_time="8.0",
                 simulation_time_step="2e-5").items():
    m.set_model_property_value(k, v)

INIT = """# =====================================================================
#  ECOM060 - Instrumentacao Eletronica - UFAL - 2026.2
#  Fase 2 / Entrega 02 - Equipe G05 - Equivalente eletrico do Monotanque
#  Hidraulico:  A dh/dt = qi - k*sqrt(h) - qd        (Entrega 01)
#  Eletrico:    C dv/dt = i_i - K_e*sqrt(v) - i_d
# =====================================================================
# ---- parametros fisicos (Entrega 01)
A_nom = 0.5             # m2        area da base
k_nom = 0.01            # m^2.5/s   coeficiente do orificio
h0    = 0.5             # m         nivel de operacao
qi0   = k_nom*h0**0.5   # m3/s      vazao de equilibrio (7,071 L/s)

# ---- fatores de escala (R1c)
kv = 10.0               # V por m        : 1 V = 10 cm de agua
ki = 1000.0             # A por m3/s     : 1 A = 1 L/s
kt = 100.0              # s fisicos por s de circuito (1 s no circuito = 100 s no tanque)

# ---- parametros do circuito (R1d)
c_por_m2 = ki/(kv*kt)            # F por m2 de area (= 1)
C_nom = A_nom*c_por_m2           # 0,5 F
K_e   = k_nom*ki/kv**0.5         # 3,162 A/V^0.5 (orificio)
I0    = ki*qi0                   # 7,071 A (bomba no equilibrio)
V0    = kv*h0                    # 5 V
R_lin = 2*V0**0.5/K_e            # 1,414 ohm (resistencia incremental em V0)
tau_c = R_lin*C_nom              # 0,7071 s  (= 70,71 s / kt)
w_c   = 1/tau_c                  # rad/s     frequencia de canto no circuito

# ---- banco de capacitores (area selecionavel no SCADA: 0,125 / 0,25 / 0,5 / 1 / 2 m2)
C1 = 0.125*c_por_m2              # sempre ligado
C2 = 0.125*c_por_m2              # liga se A >= 0,25
C3 = 0.25*c_por_m2               # liga se A >= 0,5
C4 = 0.5*c_por_m2                # liga se A >= 1
C5 = 1.0*c_por_m2                # liga se A >= 2

# ---- condicao inicial (pre-carga) e ensaios
R_pc = 0.001                     # ohm  resistor de pre-carga (constante 0,5 ms com 0,5 F; queda < 1 mm)
t_ev = 0.5                       # s    evento do ensaio no circuito (= 50 s no tanque)
Ts   = 1e-4                      # s    passo dos blocos de sinal
"""
m.set_model_init_code(INIT)


def C(t, name, pos, rot="up", parent=None, **props):
    c = m.create_component(t, name=name, position=pos, rotation=rot, parent=parent)
    for k, v in props.items():
        m.set_property_value(m.prop(c, k), v)
    return c


def W(a, b):
    m.create_connection(a, b)


def J(name, pos, kind="sp", parent=None):
    return m.create_junction(name=name, kind=kind, position=pos, parent=parent)


T = m.term


def const(name, pos, value, parent=None):
    return C("core/Constant", name, pos, parent=parent, value=value, execution_rate="Ts")


def gain(name, pos, g, src, parent=None, rot="up"):
    c = C("core/Gain", name, pos, parent=parent, gain=g, rot=rot)
    W(src, T(c, "in"))
    return T(c, "out")


def soma(name, pos, a, b, signs="++", parent=None):
    s = C("core/Sum", name, pos, parent=parent, signs=signs)
    W(a, T(s, "in")); W(b, T(s, "in1"))
    return T(s, "out")


def prod(name, pos, a, b, parent=None):
    p = C("core/Product", name, pos, parent=parent)
    W(a, T(p, "in")); W(b, T(p, "in1"))
    return T(p, "out")


def sw(name, pos, thr, ctrl, se_verdadeiro, se_falso, parent=None):
    """Signal switch: out = in se ctrl > limiar, senao in1 (in2 = controle)."""
    s = C("core/Signal switch", name, pos, parent=parent, criterion="ctrl > threshold", threshold=thr)
    W(se_verdadeiro, T(s, "in")); W(se_falso, T(s, "in1")); W(ctrl, T(s, "in2"))
    return T(s, "out")


def probe(name, pos, src):
    p = C("core/Probe", name, pos)
    W(src, T(p, "in"))
    return p


def scada(name, pos, default, lo, hi, unit=""):
    c = C("core/SCADA Input", name, pos, def_value=default, min=lo, max=hi, unit=unit, execution_rate="Ts")
    return T(c, "out")


# ======================================================================== entradas SCADA (raiz)
X0, Y0 = 7000, 7300
SC = {}
for i, (n, d, lo, hi, u) in enumerate([
        ("ensaio", 1.0, 1, 4, ""), ("disparo", 0.0, 0, 1, ""), ("degrau_pct", 20.0, -60, 150, "%"),
        ("h_ini_m", 1.0, 0, 2, "m"), ("amp_pct", 10.0, 0, 50, "%")]):
    SC[n] = scada(n, (X0, Y0 + 70 * i), d, lo, hi, u)
SC["A_m2"] = scada("A_m2", (7700, 7120), 0.5, 0.125, 2.0, "m2")
SC["k_valvula"] = scada("k_valvula", (8330, 7880), 0.01, 0.001, 0.05, "m2.5/s")
SC["qd_Ls"] = scada("qd_Ls", (8560, 7880), 0.0, -5, 10, "L/s")
m.create_comment("ENSAIO (SCADA): 1 = (a) degrau | 2 = (b) cond. inicial, bomba ligada | "
                 "3 = (b) drenagem livre | 4 = (c) senoide", position=(7150, 7180))

# ======================================================================== gerador dos ensaios (sinal)
G = m.create_component("core/Empty Subsystem", name="Gerador_de_ensaios", position=(7280, Y0 + 140))
m.set_size(G, 130, 300)
gp = {}
for i, n in enumerate(["ensaio", "disparo", "degrau_pct", "h_ini_m", "amp_pct"]):
    gp[n] = m.create_port(name=n, parent=G, kind="sp", direction="in", position=(7000, 7200 + 120 * i),
                          terminal_position=("left", "auto"))
    W(SC[n], T(G, n))
for i, n in enumerate(["v_hold_V", "segura", "qi_ref_A", "t_ensaio"]):
    gp[n] = m.create_port(name=n, parent=G, kind="sp", direction="out", position=(8700, 7300 + 160 * i),
                          terminal_position=("right", "auto"))

# relogio do ensaio: integrador de 1, zerado na borda de subida de 'disparo'
one = const("um", (7150, 7080), "1", G)
clk = C("core/Integrator", "relogio_ensaio", (7300, 7100), parent=G, show_reset="rising", init_value="0",
        execution_rate="Ts")
W(T(one, "out"), T(clk, "in")); W(gp["disparo"], T(clk, "reset"))
jt = J("j_t", (7420, 7100), parent=G); W(T(clk, "out"), jt); W(jt, gp["t_ensaio"])
# depois = 1 a partir de t_ev
k1 = const("um_", (7420, 7000), "1", G)
k0 = const("zero_", (7420, 7180), "0", G)
depois = sw("depois_do_evento", (7560, 7080), "t_ev", jt, T(k1, "out"), T(k0, "out"), G)
jd = J("j_depois", (7680, 7080), parent=G); W(depois, jd)
# segura (contator de pre-carga fechado) = 1 - depois
k1s = const("um_s", (7700, 7180), "1", G)
W(soma("segura_ate_evento", (7820, 7160), T(k1s, "out"), jd, "+-", G), gp["segura"])

# fatores multiplicativos de qi0 para cada ensaio
kd = gain("pct_para_fracao", (7200, 7400), "0.01", gp["degrau_pct"], G)
fa = soma("fator_a", (7600, 7400), T(const("um_a", (7450, 7340), "1", G), "out"),
          prod("degrau_x_depois", (7450, 7420), kd, jd, G), "++", G)                       # (a) 1 + d*depois
fb = T(const("fator_b", (7600, 7520), "1", G), "out")                                      # (b) bomba ligada
fb2 = soma("fator_b_drenagem", (7600, 7620), T(const("um_b", (7450, 7600), "1", G), "out"), jd, "+-", G)  # (b') 1 - depois
# (c) 1 + a*depois*sin(w_c*(t - t_ev))
tm = soma("t_menos_t_ev", (7300, 7760), jt, T(const("t_ev_", (7150, 7800), "t_ev", G), "out"), "+-", G)
sen = C("core/Trigonometric function", "seno", (7560, 7760), parent=G, trigonometric_fn="sin", execution_rate="Ts")
W(gain("w_c_", (7430, 7760), "w_c", tm, G), T(sen, "in"))
ka = gain("amp_para_fracao", (7200, 7700), "0.01", gp["amp_pct"], G)
fc = soma("fator_c", (7900, 7760), T(const("um_c", (7750, 7700), "1", G), "out"),
          prod("amp_x_seno", (7780, 7780), prod("amp_x_depois", (7680, 7720), ka, jd, G), T(sen, "out"), G), "++", G)
mux = C("core/Multiport signal switch", "seletor_ensaio_qi", (8150, 7520), parent=G, number_of_input_terminals=4)
je = J("j_ensaio", (7900, 7250), parent=G); W(gp["ensaio"], je); W(je, T(mux, "ctrl"))
for t, src in zip(["in", "in1", "in2", "in3"], [fa, fb, fb2, fc]):
    W(src, T(mux, t))
W(gain("I0_", (8350, 7520), "I0", T(mux, "out"), G), gp["qi_ref_A"])
# tensao de pre-carga (= nivel inicial convertido): h0 nos ensaios (a) e (c), h_ini nos ensaios (b)
vh = gain("kv_h_ini", (7300, 7950), "kv", gp["h_ini_m"], G)
v0 = T(const("V0_", (7300, 8050), "V0", G), "out")
jvh = J("j_vh", (7500, 7950), parent=G); W(vh, jvh)
jv0 = J("j_v0", (7500, 8050), parent=G); W(v0, jv0)
muxv = C("core/Multiport signal switch", "seletor_ensaio_h", (8150, 8000), parent=G, number_of_input_terminals=4)
W(je, T(muxv, "ctrl"))
for t, src in zip(["in", "in1", "in2", "in3"], [jv0, jvh, jvh, jv0]):
    W(src, T(muxv, t))
W(T(muxv, "out"), gp["v_hold_V"])

# ======================================================================== circuito equivalente (eletrico, raiz)
YT, YB = 7300, 7680            # trilho do no 'nivel' e trilho de terra
xs = {"pc": 7520, "bomba": 7670, "C1": 7820, "C2": 7930, "C3": 8040, "C4": 8150, "C5": 8260,
      "vm": 8380, "orif": 8510, "qd": 8640}
# amperimetros sao horizontais: a fonte fica de um lado (x -/+ 32) e a ligacao ao trilho do outro
dx_top = {"bomba": 32, "orif": -32, "qd": -32}
top = {n: J(f"n_nivel_{n}", (x + dx_top.get(n, 0), YT), "pe") for n, x in xs.items()}
bot = {n: J(f"n_terra_{n}", (x - dx_top.get(n, 0), YB), "pe") for n, x in xs.items()}
names = list(xs)
for a, b in zip(names[:-1], names[1:]):
    W(top[a], top[b]); W(bot[a], bot[b])
gnd = C("core/Ground", "GND", (7820, YB + 50)); W(bot["C1"], T(gnd, "node"))
YS, YA = 7560, 7420            # altura das fontes/capacitores e dos medidores/contatores

# convencao: a fonte de corrente controlada empurra a corrente para fora do p_node
# pre-carga: fonte controlada + resistor + contator (condicao inicial e repouso antes do evento)
vpc = C("core/Signal Controlled Voltage Source", "V_pre_carga", (xs["pc"], YS), rot="right", execution_rate="Ts")
rpc = C("core/Resistor", "R_pre_carga", (xs["pc"], 7470), rot="right", resistance="R_pc")
sca = C("core/Single Pole Single Throw Contactor", "S_pre_carga", (xs["pc"], 7370), rot="right",
        ctrl_src="Model", execution_rate="Ts")
W(T(vpc, "n_node"), bot["pc"]); W(T(vpc, "p_node"), T(rpc, "n_node")); W(T(rpc, "p_node"), T(sca, "a_out"))
W(T(sca, "a_in"), top["pc"])
W(T(G, "v_hold_V"), T(vpc, "in")); W(T(G, "segura"), T(sca, "ctrl_in"))

# bomba qi: fonte de corrente controlada (entra no no 'nivel') + amperimetro
ib = C("core/Signal Controlled Current Source", "q_i_bomba", (xs["bomba"] - dx_top["bomba"], YS), rot="right", execution_rate="Ts")
amb = C("core/Current Measurement", "A_qi", (xs["bomba"], YA), rot="up", sig_output="True", execution_rate="Ts")
W(T(ib, "n_node"), bot["bomba"]); W(T(ib, "p_node"), T(amb, "p_node")); W(T(amb, "n_node"), top["bomba"])
W(T(G, "qi_ref_A"), T(ib, "in"))

# area A: banco de capacitores (C1 fixo, C2..C5 por contatores comandados pelo SCADA)
cap = {}
for i, (n, val) in enumerate([("C1", "C1"), ("C2", "C2"), ("C3", "C3"), ("C4", "C4"), ("C5", "C5")]):
    cap[n] = C("core/Capacitor", f"C_area_{i + 1}", (xs[n], YS), rot="right", capacitance=val,
               initial_voltage="V0" if n in ("C1", "C2", "C3") else "0",
               # sem 'pole shifting': no HIL ele equivale a um resistor de fuga em paralelo (~200 ohm com 0,5 F),
               # que tiraria corrente do no e baixaria o nivel de equilibrio
               pole_shift_ignore="True")
    W(T(cap[n], "n_node"), bot[n])
    if n == "C1":
        W(T(cap[n], "p_node"), top[n])
    else:
        s_ = C("core/Single Pole Single Throw Contactor", f"S_area_{i + 1}", (xs[n], YA), rot="right",
               ctrl_src="Model", execution_rate="Ts", initial_state="on" if n in ("C2", "C3") else "off")
        W(T(s_, "a_in"), top[n]); W(T(s_, "a_out"), T(cap[n], "p_node"))
        cap[n + "_sw"] = s_
# selecao da area (subsistema): contator i fecha se A >= limiar (codigo termometro)
SA = m.create_component("core/Empty Subsystem", name="Selecao_da_area", position=(7930, 7120))
m.set_size(SA, 260, 60)
pa = m.create_port(name="A_m2", parent=SA, kind="sp", direction="in", position=(7000, 7300),
                   terminal_position=("left", "auto"))
W(SC["A_m2"], T(SA, "A_m2"))
ja = J("j_A", (7150, 7300), parent=SA); W(pa, ja)
for i, (n, lim) in enumerate([("C2", "0.2"), ("C3", "0.4"), ("C4", "0.8"), ("C5", "1.6")]):
    ro = C("core/Relational operator", f"A_maior_{n}", (7350, 7200 + 120 * i), relational_op=">=",
           execution_rate="Ts", parent=SA)
    W(ja, T(ro, "in")); W(T(const(f"lim_{n}", (7220, 7240 + 120 * i), lim, SA), "out"), T(ro, "in1"))
    po = m.create_port(name=f"liga_{n}", parent=SA, kind="sp", direction="out", position=(7550, 7200 + 120 * i),
                       terminal_position=("right", "auto"))
    W(T(ro, "out"), po)
    W(T(SA, f"liga_{n}"), T(cap[n + "_sw"], "ctrl_in"))

# voltimetro do nivel
vm = C("core/Voltage Measurement", "V_nivel", (xs["vm"], 7490), rot="up", sig_output="True", execution_rate="Ts")
W(T(vm, "p_node"), top["vm"]); W(T(vm, "n_node"), bot["vm"])

# orificio: fonte de corrente comandada por K_e*sqrt(v) (sai do no 'nivel') + amperimetro
io = C("core/Signal Controlled Current Source", "q_o_orificio", (xs["orif"] - dx_top["orif"], YS), rot="left", execution_rate="Ts")
amo = C("core/Current Measurement", "A_qo", (xs["orif"], YA), rot="up", sig_output="True", execution_rate="Ts")
W(top["orif"], T(amo, "p_node")); W(T(amo, "n_node"), T(io, "n_node")); W(T(io, "p_node"), bot["orif"])
# lei do orificio (subsistema): i = (ki/sqrt(kv)) * k * sqrt(max(v, 0))
TO = m.create_component("core/Empty Subsystem", name="Lei_do_orificio", position=(8440, 7800))
m.set_size(TO, 120, 70)
pv = m.create_port(name="v", parent=TO, kind="sp", direction="in", position=(7000, 7300), terminal_position=("left", "auto"))
pkk = m.create_port(name="k", parent=TO, kind="sp", direction="in", position=(7000, 7450), terminal_position=("left", "auto"))
pio = m.create_port(name="i_o", parent=TO, kind="sp", direction="out", position=(7700, 7300), terminal_position=("right", "auto"))
lim0 = C("core/Limit", "nivel_nao_negativo", (7120, 7300), upper_limit="1e6", lower_limit="0", execution_rate="Ts", parent=TO)
W(pv, T(lim0, "in"))
rq = C("core/Mathematical function", "raiz_quadrada", (7250, 7300), mathematical_fn="sqrt", execution_rate="Ts", parent=TO)
W(T(lim0, "out"), T(rq, "in"))
pk = prod("k_vezes_raiz", (7400, 7320), T(rq, "out"), pkk, TO)
W(gain("ki_sobre_raiz_kv", (7550, 7300), "ki/kv**0.5", pk, TO), pio)
jv = J("j_v", (8380, 7800)); W(T(vm, "out"), jv)
W(jv, T(TO, "v")); W(SC["k_valvula"], T(TO, "k")); W(T(TO, "i_o"), T(io, "in"))

# retirada qd (disturbio): fonte de corrente controlada (sai do no 'nivel') + amperimetro
idd = C("core/Signal Controlled Current Source", "q_d_retirada", (xs["qd"] - dx_top["qd"], YS), rot="left", execution_rate="Ts")
amd = C("core/Current Measurement", "A_qd", (xs["qd"], YA), rot="up", sig_output="True", execution_rate="Ts")
W(top["qd"], T(amd, "p_node")); W(T(amd, "n_node"), T(idd, "n_node")); W(T(idd, "p_node"), bot["qd"])
W(SC["qd_Ls"], T(idd, "in"))      # 1 A = 1 L/s

m.create_comment("CIRCUITO EQUIVALENTE - no 'nivel': v = kv*h | pre-carga | bomba qi | area A = banco de C | "
                 "voltimetro | orificio K_e*sqrt(v) | retirada qd", position=(8080, 7240))

# ======================================================================== leituras (reconvertidas a escala original)
XP = 8880
probe("qi_Ls", (XP, 7300), gain("i_para_qi", (XP - 100, 7300), "1", T(amb, "out")))
probe("qo_Ls", (XP, 7390), gain("i_para_qo", (XP - 100, 7390), "1", T(amo, "out")))
probe("qd_Ls_med", (XP, 7480), gain("i_para_qd", (XP - 100, 7480), "1", T(amd, "out")))
jv2 = J("j_v2", (8700, 7800)); W(jv, jv2)
probe("h_m", (XP, 7740), gain("v_para_h", (XP - 100, 7740), "1/kv", jv2))
probe("v_C_V", (XP, 7830), jv2)
probe("t_fisico_s", (7520, 7880), gain("t_para_fisico", (7420, 7880), "kt", T(G, "t_ensaio")))

# ======================================================================== Scope (TyphoonSim offline)
scp = C("core/Scope", "Scope_nivel", (9030, 7600))
vp = {"h_m": 1, "qi_Ls": 2, "qo_Ls": 2, "qd_Ls_med": 2, "t_fisico_s": 3}
cor = {"h_m": "#185079", "qi_Ls": "#C86E1E", "qo_Ls": "#3A86B0", "qd_Ls_med": "#7F7F7F", "t_fisico_s": "#000000"}
sd = {"plot_settings": {"layout": "Vertical", "background_color": "white",
                        "legend_visible": True, "signals_tooltips_enabled": True},
      "signals": {k: {"viewports": [v], "type": "analog", "color": {str(v): cor[k]},
                      "display": {str(v): "solid"}, "is_manual": {str(v): False}} for k, v in vp.items()},
      "viewports": {str(i): {"log_scale_x": False, "log_scale_y": False, "y_axis_db": False} for i in range(1, 4)}}
m.set_property_value(m.prop(scp, "selected_signals"), list(vp.keys()))
m.set_property_value(m.prop(scp, "signals_data"), json.dumps(sd))

m.save_as(out)
print("compile:", m.compile())
