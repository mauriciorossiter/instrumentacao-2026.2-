# -*- coding: utf-8 -*-
# Gera o equivalente eletrico v2 do Monotanque (devolutiva da Fase 2 / Entrega 02, Equipe G05).
#
#   Tanque (armazena volume)      A dh/dt  = qi - q - qd        ->  C dv/dt = i_i - i_o - i_d
#   Coluna no tubo de saida       I_h dq/dt = h - q|q|/k^2      ->  L di_o/dt = v - R*i_o - e(i_o)
#   (inercia: a forca rho*g*h*a acelera a massa rho*l*a do liquido; o orificio dissipa q|q|/k^2)
#
# Uso (Python do Typhoon HIL Control Center 2026.2):
#   python.exe gerar_modelo_dev.py <saida.tse> [A_m2=0.5] [l_tubo_m=1.0]
import sys
import json
from typhoon.api.schematic_editor import SchematicAPI

out = sys.argv[1]
A_M2 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
L_TUBO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

m = SchematicAPI()
m.create_new_model("monotanque_equivalente_v2")
for k, v in dict(solver_type="DAE", integration_method="BDF", max_sim_step="1e-4", init_sim_step="1e-6",
                 abs_tol="1e-7", rel_tol="1e-7", simulation_time="8.0",
                 simulation_time_step="2e-5").items():
    m.set_model_property_value(k, v)

INIT = f"""# =====================================================================
#  ECOM060 - Instrumentacao Eletronica - UFAL - 2026.2
#  Devolutiva da Fase 2 / Entrega 02 - Equipe G05 - Equivalente eletrico v2
#  Tanque:          A dh/dt   = qi - q - qd
#  Tubo de saida:   I_h dq/dt = h - q|q|/k^2     (inercia + resistencia turbulenta)
# =====================================================================
# ---- construcao (para outra area ou outro tubo: mudar aqui e recompilar)
A      = {A_M2!r}            # m2       area da base (Entrega 01: 0,5)
l_tubo = {L_TUBO!r}            # m        comprimento do tubo de saida (estimativa: 1 m)

# ---- parametros fisicos (Entrega 01)
k_nom = 0.01            # m^2.5/s  coeficiente agregado do orificio
h0    = 0.5             # m        nivel de operacao
qi0   = k_nom*h0**0.5   # m3/s     vazao de equilibrio (7,071 L/s)
g     = 9.81            # m/s2
Cd    = 0.60            # -        coeficiente de descarga (borda viva)
a_or  = k_nom/(Cd*(2*g)**0.5)    # m2   area do orificio/tubo (3,76e-3 m2, d = 6,9 cm)
I_h   = l_tubo/(g*a_or)          # s2/m2 inertancia da coluna de liquido (27,1 s2/m2 por metro)

# ---- fatores de escala
kv = 10.0               # V por m        : 1 V = 10 cm de agua
ki = 1000.0             # A por m3/s     : 1 A = 1 L/s
kt = 100.0              # 1 s no circuito = 100 s no tanque

# ---- parametros do circuito
C     = A*ki/(kv*kt)             # F   tanque           (0,5 F)
L     = kv*I_h/(ki*kt)           # H   inercia no tubo  (2,71 mH por metro de tubo)
K_e   = k_nom*ki/kv**0.5         # A/V^0.5  orificio    (3,162)
V0    = kv*h0                    # V   (5 V)
I0    = ki*qi0                   # A   (7,071 A)
R_or  = 2*V0**0.5/K_e            # ohm resistencia de escoamento linearizada em h0 (1,414 ohm)
w_c   = 1/(R_or*C)               # rad/s frequencia de canto nominal no circuito

# ---- ensaios
t_ev  = 1.0                      # s   fim da preparacao (= 100 s no tanque): a bomba leva o nivel ao valor inicial
Kp    = 50.0                     # A/V ganho da bomba na preparacao
Q_MAX = 40.0                     # A   vazao maxima da bomba na preparacao (40 L/s)
Ts    = 2e-5                     # s   passo dos blocos de sinal (= passo do circuito)
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
    return T(C("core/Constant", name, pos, parent=parent, value=value, execution_rate="Ts"), "out")


def gain(name, pos, g, src, parent=None):
    c = C("core/Gain", name, pos, parent=parent, gain=g, execution_rate="Ts")
    W(src, T(c, "in"))
    return T(c, "out")


def soma(name, pos, a, b, signs="++", parent=None):
    s = C("core/Sum", name, pos, parent=parent, signs=signs, execution_rate="Ts")
    W(a, T(s, "in")); W(b, T(s, "in1"))
    return T(s, "out")


def prod(name, pos, a, b, parent=None):
    p = C("core/Product", name, pos, parent=parent, execution_rate="Ts")
    W(a, T(p, "in")); W(b, T(p, "in1"))
    return T(p, "out")


def fn(name, pos, f, src, parent=None):
    c = C("core/Mathematical function", name, pos, parent=parent, mathematical_fn=f, execution_rate="Ts")
    W(src, T(c, "in"))
    return T(c, "out")


def limit(name, pos, lo, hi, src, parent=None):
    c = C("core/Limit", name, pos, parent=parent, lower_limit=lo, upper_limit=hi, execution_rate="Ts")
    W(src, T(c, "in"))
    return T(c, "out")


def sw(name, pos, thr, ctrl, se_maior, senao, parent=None):
    """Signal switch: out = in se ctrl > limiar, senao in1."""
    s = C("core/Signal switch", name, pos, parent=parent, criterion="ctrl > threshold", threshold=thr,
          execution_rate="Ts")
    W(se_maior, T(s, "in")); W(senao, T(s, "in1")); W(ctrl, T(s, "in2"))
    return T(s, "out")


def junc(name, src, pos, parent=None):
    j = J(name, pos, parent=parent); W(src, j)
    return j


def porta(sub, name, direction, pos, side):
    return m.create_port(name=name, parent=sub, kind="sp", direction=direction, position=pos,
                         terminal_position=(side, "auto"))


def probe(name, pos, src):
    p = C("core/Probe", name, pos)
    W(src, T(p, "in"))


def scada(name, pos, default, lo, hi, unit=""):
    return T(C("core/SCADA Input", name, pos, def_value=default, min=lo, max=hi, unit=unit,
               execution_rate="Ts"), "out")


# ======================================================================== entradas SCADA
SC = {}
for i, (n, d, lo, hi, u) in enumerate([
        ("ensaio", 1.0, 1, 4, ""), ("disparo", 0.0, 0, 1, ""), ("degrau_pct", 20.0, -90, 150, "%"),
        ("h_op_m", 0.5, 0.05, 2, "m"), ("h_ini_m", 1.0, 0.0, 2, "m"), ("amp_pct", 10.0, 0, 50, "%"),
        ("w_rel", 1.0, 0.01, 3000, "")]):
    SC[n] = scada(n, (6900, 7100 + 70 * i), d, lo, hi, u)
SC["k_valvula"] = scada("k_valvula", (6900, 7650), 0.01, 0.001, 0.05, "m2.5/s")
SC["modelo_orif"] = scada("modelo_orif", (6900, 7720), 0.0, 0, 1, "")
SC["qd_Ls"] = scada("qd_Ls", (8780, 7880), 0.0, -5, 20, "L/s")
m.create_comment("ENSAIO: 1 = (a) degrau a partir de h_op | 2 = (b) de h_ini volta a h_op | 3 = (b) drenagem livre "
                 "a partir de h_ini | 4 = (c) senoide em h_op com w = w_rel * w_c\n"
                 "modelo_orif: 0 = nao linear (q = k*sqrt(h)) | 1 = linearizado em h_op (so o resistor)",
                 position=(7000, 6950))
jk = junc("j_k", SC["k_valvula"], (7020, 7650))
jhop = junc("j_hop", SC["h_op_m"], (7020, 7310))

# ======================================================================== gerador de ensaios (sinal)
G = m.create_component("core/Empty Subsystem", name="Gerador_de_ensaios", position=(7230, 7330))
m.set_size(G, 140, 420)
gin = ["ensaio", "disparo", "degrau_pct", "h_op_m", "h_ini_m", "amp_pct", "w_rel", "k_valvula", "v_medido"]
gp = {n: porta(G, n, "in", (6800, 7000 + 110 * i), "left") for i, n in enumerate(gin)}
for n in gin[:-1]:
    W({"h_op_m": jhop, "k_valvula": jk}.get(n, SC.get(n)), T(G, n))
for i, n in enumerate(["qi_ref_A", "t_ensaio"]):
    gp[n] = porta(G, n, "out", (9000, 7300 + 300 * i), "right")

# relogio do ensaio, zerado na borda de subida de 'disparo'
clk = C("core/Integrator", "relogio_ensaio", (7050, 6900), parent=G, show_reset="rising", init_value="0",
        execution_rate="Ts")
W(const("um", (6930, 6880), "1", G), T(clk, "in")); W(gp["disparo"], T(clk, "reset"))
jt = junc("j_t", T(clk, "out"), (7180, 6900), G); W(jt, gp["t_ensaio"])
depois = junc("j_depois", sw("depois_de_t_ev", (7300, 6880), "t_ev", jt, const("um_", (7180, 6820), "1", G),
                             const("zero_", (7180, 6960), "0", G), G), (7420, 6880), G)
je = junc("j_ensaio", gp["ensaio"], (6950, 7000), G)

# --- preparacao: a bomba leva o nivel ao valor inicial do ensaio (feed-forward + proporcional)
jvop = junc("j_vop", gain("kv_hop", (6950, 7330), "kv", gp["h_op_m"], G), (7060, 7330), G)
jvini = junc("j_vini", gain("kv_hini", (6950, 7440), "kv", gp["h_ini_m"], G), (7060, 7440), G)
mv = C("core/Multiport signal switch", "nivel_inicial", (7200, 7400), parent=G, number_of_input_terminals=4,
       execution_rate="Ts")
W(je, T(mv, "ctrl"))
for t_, s_ in zip(["in", "in1", "in2", "in3"], [jvop, jvini, jvini, jvop]):
    W(s_, T(mv, t_))
jva = junc("j_valvo", T(mv, "out"), (7320, 7400), G)
ke = gain("Ke_de_k", (6950, 7770), "ki/kv**0.5", gp["k_valvula"], G)
qff = prod("q_equilibrio", (7560, 7480), fn("raiz_alvo", (7440, 7460), "sqrt",
                                            limit("alvo_pos", (7380, 7500), 0, 1e6, jva, G), G), ke, G)
qp = gain("Kp_", (7560, 7560), "Kp", soma("erro", (7440, 7560), jva, gp["v_medido"], "+-", G), G)
qprep = limit("bomba_0_a_Qmax", (7800, 7520), 0, "Q_MAX", soma("ff_mais_p", (7680, 7520), qff, qp, "++", G), G)

# --- ensaio: bomba no valor de equilibrio de h_op (k nominal) vezes o fator do ensaio
qbase = gain("Ke_nom", (7440, 7330), "K_e", fn("raiz_vop", (7320, 7330), "sqrt", jvop, G), G)
fa = soma("fator_a", (7440, 7660), const("um_a", (7300, 7640), "1", G),
          gain("pct_degrau", (7300, 7700), "0.01", gp["degrau_pct"], G), "++", G)
fb = const("fator_b", (7440, 7740), "1", G)
fb2 = const("fator_b_drenagem", (7440, 7800), "0", G)
tm = soma("t_menos_t_ev", (7300, 7880), jt, const("t_ev_", (7180, 7900), "t_ev", G), "+-", G)
wt = prod("w_vezes_t", (7440, 7900), gain("w_c_", (7300, 7960), "w_c", gp["w_rel"], G), tm, G)
sen = C("core/Trigonometric function", "seno", (7560, 7900), parent=G, trigonometric_fn="sin", execution_rate="Ts")
W(wt, T(sen, "in"))
fc = soma("fator_c", (7800, 7900), const("um_c", (7680, 7860), "1", G),
          prod("amp_x_seno", (7680, 7940), gain("pct_amp", (7560, 7980), "0.01", gp["amp_pct"], G),
               T(sen, "out"), G), "++", G)
mf = C("core/Multiport signal switch", "fator_do_ensaio", (7950, 7750), parent=G, number_of_input_terminals=4,
       execution_rate="Ts")
W(je, T(mf, "ctrl"))
for t_, s_ in zip(["in", "in1", "in2", "in3"], [fa, fb, fb2, fc]):
    W(s_, T(mf, t_))
qtest = prod("q_ensaio", (8100, 7600), qbase, T(mf, "out"), G)
W(sw("preparo_ou_ensaio", (8300, 7550), "0.5", depois, qtest, qprep, G), gp["qi_ref_A"])

# ======================================================================== circuito (dominio eletrico)
YT, YB, YM = 7300, 7760, 7420
xs = {"bomba": 7680, "C": 7830, "vm": 7960, "saida": 8150, "qd": 8380}
dx = {"bomba": 32, "saida": -32, "qd": -32}       # amperimetros horizontais: fonte de um lado, trilho do outro
top = {n: J(f"n_nivel_{n}", (x + dx.get(n, 0), YT), "pe") for n, x in xs.items()}
bot = {n: J(f"n_terra_{n}", (x - dx.get(n, 0), YB), "pe") for n, x in xs.items()}
for a_, b_ in zip(list(xs)[:-1], list(xs)[1:]):
    W(top[a_], top[b_]); W(bot[a_], bot[b_])
W(bot["C"], T(C("core/Ground", "GND", (7830, YB + 50)), "node"))

# bomba qi: fonte de vazao (descarga livre por cima: a vazao nao depende do nivel)
ib = C("core/Signal Controlled Current Source", "q_i_bomba", (xs["bomba"] - 32, 7600), rot="right",
       execution_rate="Ts")
amb = C("core/Current Measurement", "A_qi", (xs["bomba"], YM), sig_output="True", execution_rate="Ts")
W(T(ib, "n_node"), bot["bomba"]); W(T(ib, "p_node"), T(amb, "p_node")); W(T(amb, "n_node"), top["bomba"])
W(T(G, "qi_ref_A"), T(ib, "in"))

# tanque: UM capacitor (C = A em F)
cap = C("core/Capacitor", "C_tanque", (xs["C"], 7530), rot="right", capacitance="C", initial_voltage="V0",
        pole_shift_ignore="True")
W(T(cap, "p_node"), top["C"]); W(T(cap, "n_node"), bot["C"])

# voltimetro do nivel
vm = C("core/Voltage Measurement", "V_nivel", (xs["vm"], 7530), sig_output="True", execution_rate="Ts")
W(T(vm, "p_node"), top["vm"]); W(T(vm, "n_node"), bot["vm"])

# saida: amperimetro -> L (inercia) -> R (resistencia de escoamento) -> e (parte nao linear) -> terra
xo = xs["saida"] + 32
amo = C("core/Current Measurement", "A_qo", (xs["saida"], YM), sig_output="True", execution_rate="Ts")
ind = C("core/Inductor", "L_tubo", (xo, 7500), rot="right", inductance="L", initial_current="I0",
        pole_shift_ignore="True")
res = C("core/Resistor", "R_escoamento", (xo, 7590), rot="right", resistance="R_or")
ecs = C("core/Signal Controlled Voltage Source", "e_nao_linear", (xo, 7680), rot="right", execution_rate="Ts")
W(top["saida"], T(amo, "p_node")); W(T(amo, "n_node"), T(ind, "p_node"))
W(T(ind, "n_node"), T(res, "p_node")); W(T(res, "n_node"), T(ecs, "p_node")); W(T(ecs, "n_node"), bot["saida"])

# retirada qd (consumo por bomba dosadora): fonte de vazao
idd = C("core/Signal Controlled Current Source", "q_d_consumo", (xs["qd"] + 32, 7600), rot="left",
        execution_rate="Ts")
amd = C("core/Current Measurement", "A_qd", (xs["qd"], YM), sig_output="True", execution_rate="Ts")
W(top["qd"], T(amd, "p_node")); W(T(amd, "n_node"), T(idd, "n_node")); W(T(idd, "p_node"), bot["qd"])
W(SC["qd_Ls"], T(idd, "in"))

m.create_comment("CIRCUITO: bomba (fonte de vazao) | C = tanque | voltimetro = nivel | saida: L = inercia da agua "
                 "no tubo, R = resistencia de escoamento, e = parte nao linear de k*sqrt(h) | consumo qd",
                 position=(7700, 7180))

# --- parte nao linear da resistencia de saida (subsistema)
#     queda total no orificio:  v_or = i|i| / K^2   (nao linear)   ou   R_op*i - v_op   (tangente em h_op)
#     o resistor fisico ja da R_or*i; a fonte completa o resto:  e = v_or - R_or*i
NL = m.create_component("core/Empty Subsystem", name="Parte_nao_linear", position=(8000, 7900))
m.set_size(NL, 150, 110)
np_ = {n: porta(NL, n, "in", (6800, 7000 + 130 * i), "left") for i, n in enumerate(["i_o", "k", "modelo", "h_op"])}
pe = porta(NL, "e", "out", (8200, 7300), "right")
ji = junc("j_i", np_["i_o"], (6950, 7000), NL)
Kk = gain("K_de_k", (6950, 7130), "ki/kv**0.5", np_["k"], NL)
jK = junc("j_K", Kk, (7060, 7130), NL)
inv_K2 = fn("um_sobre_K2", (7300, 7180), "reciprocal", fn("K2", (7180, 7180), "square", jK, NL), NL)
ab = C("core/Abs", "abs_i", (7060, 7060), parent=NL, execution_rate="Ts")
W(ji, T(ab, "in"))
iai = prod("i_vezes_abs_i", (7180, 7020), ji, T(ab, "out"), NL)
v_nl = prod("v_or_nao_linear", (7440, 7040), iai, inv_K2, NL)
jvo = junc("j_vop_nl", gain("kv_", (6950, 7390), "kv", np_["h_op"], NL), (7060, 7390), NL)
R_op = prod("R_op", (7440, 7330), gain("dois_raiz", (7300, 7330), "2", fn("raiz_vop", (7180, 7330), "sqrt", jvo, NL),
                                       NL), fn("um_sobre_K", (7300, 7250), "reciprocal", jK, NL), NL)
v_lin = soma("v_or_tangente", (7680, 7360), prod("R_op_vezes_i", (7560, 7330), R_op, ji, NL), jvo, "+-", NL)
v_or = sw("modelo_do_orificio", (7820, 7200), "0.5", np_["modelo"], v_lin, v_nl, NL)
W(soma("e_menos_R_i", (8000, 7300), v_or, gain("R_or_i", (7820, 7420), "R_or", ji, NL), "+-", NL), pe)

jio = junc("j_io", T(amo, "out"), (8150, 7860))
W(jio, T(NL, "i_o")); W(jk, T(NL, "k")); W(SC["modelo_orif"], T(NL, "modelo")); W(jhop, T(NL, "h_op"))
je_ = junc("j_e", T(NL, "e"), (8260, 7900)); W(je_, T(ecs, "in"))

jv = junc("j_v", T(vm, "out"), (7960, 7860)); W(jv, T(G, "v_medido"))

# ======================================================================== leituras (escala do tanque)
XP = 8950
probe("qi_Ls", (XP, 7300), T(amb, "out"))
probe("qo_Ls", (XP, 7370), jio)
probe("qd_Ls_med", (XP, 7440), T(amd, "out"))
probe("h_m", (XP, 7560), gain("v_para_h", (XP - 110, 7560), "1/kv", jv))
probe("v_C_V", (XP, 7630), jv)
probe("e_nl_V", (XP, 7700), je_)
probe("t_fisico_s", (7450, 7900), gain("t_para_tanque", (7350, 7900), "kt", T(G, "t_ensaio")))

scp = C("core/Scope", "Scope_nivel", (9100, 7500))
vp = {"h_m": 1, "qi_Ls": 2, "qo_Ls": 2, "qd_Ls_med": 2, "t_fisico_s": 3}
sd = {"plot_settings": {"layout": "Vertical", "background_color": "white", "legend_visible": True,
                        "signals_tooltips_enabled": True},
      "signals": {k: {"viewports": [v], "type": "analog", "display": {str(v): "solid"},
                      "is_manual": {str(v): False}} for k, v in vp.items()},
      "viewports": {str(i): {"log_scale_x": False, "log_scale_y": False, "y_axis_db": False} for i in range(1, 4)}}
m.set_property_value(m.prop(scp, "selected_signals"), list(vp.keys()))
m.set_property_value(m.prop(scp, "signals_data"), json.dumps(sd))

m.save_as(out)
print("A =", A_M2, "l_tubo =", L_TUBO, "-> compile:", m.compile())
