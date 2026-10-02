# -*- coding: utf-8 -*-
"""
Gera modulador_am.tse — modulador AM (DSB-LC) montado no TyphoonSim.

Cadeia:
  mensagem m(t)  ---------\\
                           (1 + ma*m_norm) * Ac * cos(wc t)   -> s_AM(t)
  portadora cos(wc t) ----/
  + ruido de canal gaussiano (gerado no bloco C).

O sinal AM e as referencias (mensagem, portadora) sao registrados por probes.
A demodulacao (envoltoria x sincrona) e o estudo de sensibilidade a erro de
fase/frequencia sao feitos em pos-processamento (Python) sobre esses dados.
"""
import io

MODEL_NAME = "modulador_am"

C, J, W = [], [], []
def comp(t, n, props, pos): C.append((t, n, props, pos)); return n
def junc(n, pos, kind="sp"): J.append((n, kind, pos)); return n
def wire(a, b, bp=None): W.append((a, b, bp))

SIN = "core/Sinusoidal Source"
CST = "core/Constant"
SUM = "core/Sum"
PRD = "core/Product"
GAI = "core/Gain"
PRB = "core/Probe"
CFN = "core/C function"

# ------------------------------------------------------------- bloco C: AM+ruido
ARB_DEFS = """/*Begin code section*/
/* Modulador AM (DSB-LC) com ruido de canal.
   s_AM(t) = (1 + ma*m_norm(t)) * Ac * cos(wc t)  +  ruido.
   m_norm ja chega normalizado em [-1, 1]. */
double env;        /* envoltoria instantanea (1 + ma*m_norm)          */
double s_clean;    /* sinal AM sem ruido                               */
double s_noisy;    /* sinal AM com ruido (escrito na saida)            */
double u1, u2, g;  /* gerador gaussiano (Box-Muller)                   */
int    seeded;
/*End code section*/"""

INIT_FNC = """/*Begin code section*/
env = 0.0; s_clean = 0.0; s_noisy = 0.0; u1 = u2 = g = 0.0; seeded = 0;
/*End code section*/"""

UPDATE_FNC = """/*Begin code section*/
if (seeded == 0) { srand(2025u); seeded = 1; }

/* envoltoria e sinal AM limpo */
env     = 1.0 + in_ma * in_mnorm;
s_clean = in_Ac * env * in_carrier;

/* ruido de canal gaussiano.
   Valor padrao do rand() de 32 bits (2^31 - 1) usado diretamente. */
u1 = ((double)rand() + 1.0) / (2147483647.0 + 2.0);
u2 = ((double)rand() + 1.0) / (2147483647.0 + 2.0);
g  = sqrt(-2.0*log(u1)) * cos(6.283185307179586*u2);

/* sinal AM ja com ruido, guardado em variavel interna;
   os terminais de saida (direct-feedthrough) sao escritos apenas
   na output_fnc, como o TyphoonSim exige. */
s_noisy = s_clean + in_sigma * g;
/*End code section*/"""

OUTPUT_FNC = """/*Begin code section*/
out_env = env;
out_am  = s_noisy;
/*End code section*/"""

def cfunc(name, pos):
    return comp(CFN, name, {
        "arb_defs": ARB_DEFS, "init_fnc": INIT_FNC,
        "update_fnc": UPDATE_FNC, "output_fnc": OUTPUT_FNC,
        "input_terminals": "real in_mnorm;real in_carrier;real in_ma;real in_Ac;real in_sigma;",
        "input_terminals_dimensions": "inherit;inherit;inherit;inherit;inherit",
        "input_terminals_feedthrough": "True;True;True;True;True",
        "input_terminals_show_labels": "True;True;True;True;True",
        "output_terminals": "real out_env;real out_am;",
        "output_terminals_dimensions": "inherit;inherit",
        "output_terminals_feedthrough": "True;True",
        "output_terminals_show_labels": "True;True",
        "execution_rate": "Ts",
    }, pos)

# ------------------------------------------------------- mensagem (dois tons)
comp(SIN, "msg1", {"amplitude": "0.7", "frequency": "fm1", "phase": "0",
                   "execution_rate": "Ts"}, (8080, 8060))
comp(SIN, "msg2", {"amplitude": "0.3", "frequency": "fm2", "phase": "0",
                   "execution_rate": "Ts"}, (8080, 8160))
comp(SUM, "SUM_msg", {"signs": "++"}, (8240, 8110))
junc("J_M", (8380, 8110))
comp(PRB, "p1_mensagem", {}, (8520, 8010))

wire("msg1.out", "SUM_msg.in")
wire("msg2.out", "SUM_msg.in1")
wire("SUM_msg.out", "J_M")
wire("J_M", "p1_mensagem.in")

# ------------------------------------------------------- portadora
comp(SIN, "portadora", {"amplitude": "1.0", "frequency": "fc", "phase": "0",
                        "execution_rate": "Ts"}, (8080, 8320))
junc("J_C", (8380, 8320))
comp(PRB, "p2_portadora", {}, (8520, 8420))

wire("portadora.out", "J_C")
wire("J_C", "p2_portadora.in")

# ------------------------------------------------------- parametros AM
comp(CST, "idx_mod", {"value": "ma", "execution_rate": "Ts"}, (8080, 8460))
comp(CST, "amp_port", {"value": "Ac", "execution_rate": "Ts"}, (8080, 8560))
comp(CST, "sigma_canal", {"value": "sigma", "execution_rate": "Ts"}, (8080, 8660))

# ------------------------------------------------------- modulador (bloco C)
cfunc("MOD_AM", (8620, 8240))
junc("J_ENV", (8900, 8220))
junc("J_AM", (8900, 8320))
comp(PRB, "p3_envoltoria", {}, (9040, 8120))
comp(PRB, "p4_sinal_am", {}, (9040, 8420))

wire("J_M", "MOD_AM.in_mnorm", [(8380, 8180), (8580, 8180)])
wire("J_C", "MOD_AM.in_carrier", [(8380, 8260), (8580, 8260)])
wire("idx_mod.out", "MOD_AM.in_ma", [(8300, 8460), (8580, 8300)])
wire("amp_port.out", "MOD_AM.in_Ac", [(8320, 8560), (8580, 8340)])
wire("sigma_canal.out", "MOD_AM.in_sigma", [(8340, 8660), (8580, 8380)])
wire("MOD_AM.out_env", "J_ENV")
wire("MOD_AM.out_am", "J_AM")
wire("J_ENV", "p3_envoltoria.in")
wire("J_AM", "p4_sinal_am.in")

# ---------------------------------------------------------------------------
CONFIG = """    configuration {
        hil_device = "HIL402"
        hil_configuration_id = 1
        simulation_method = exact
        simulation_time_step = 1e-6
        simulation_discret_scaling = 1.0
        dsp_timer_periods = 100e-6, 50e-3
        ss_calc_method = "systematic elimination"
        enb_pole_shift = True
        enb_gds_oversampling = True
        show_modes = False
        device_ao_limit_enable = False
        cpl_stb = False
        enb_dep_sw_detect = False
        code_section = "internal memory"
        data_section = "internal memory"
        sys_sp_rate_1 = 0.0001
        sys_sp_rate_2 = 0.05
        sys_real_type_precision = "default"
        user_real_type_precision = "default"
        sys_cpu_optimization = "high"
        user_cpu_optimization = "high"
        user_cpu_part_option = "default"
        matrix_based_reduction = True
        cpl_dynamics_analysis = False
        export_ss_to_pickle = False
        cce_platform = "generic"
        cce_use_relative_names = False
        cce_type_mapping_real = "double"
        cce_type_mapping_uint = "unsigned int"
        cce_type_mapping_int = "int"
        cce_directory = ""
        cce_custom_type_int = ""
        cce_custom_type_uint = ""
        cce_custom_type_real = ""
        tunable_params = "component defined"
        sp_compiler_type = "C compiler"
        sig_stim = "off"
        dae_solver = "BDF"
        max_sim_step = 1e-4
        simulation_time = 0.2
        abs_tol = 1e-6
        rel_tol = 1e-6
        init_sim_step = 1e-6
        r_on_sw = 1e-3
        v_on_diode = 0.2
        data_sampling_rate = 0
        feedthrough_validation_error_level = error
    }"""

MODEL_INIT = '''    CODE model_init
        # =====================================================================
        #  MODULADOR AM (DSB-LC)  -  ECOM060 / Cap. 5.3 - Demodulacao
        #  UFAL - 2026.2
        #
        #  s_AM(t) = (1 + ma*m_norm(t)) * Ac * cos(2*pi*fc*t)  + ruido
        #
        #  A mensagem e a soma de dois tons normalizada a [-1,1] (amp 0,7+0,3).
        #  Portadora em fc, indice de modulacao ma (ma<1: sem sobremodulacao).
        # =====================================================================

        # ---- taxa de execucao -----------------------------------------------
        Ts = 1e-5                # 100 kHz  (portadora bem amostrada)

        # ---- mensagem (banda-base) ------------------------------------------
        fm1 = 50.0               # Hz  (tom principal)
        fm2 = 120.0              # Hz  (segundo tom)

        # ---- portadora ------------------------------------------------------
        fc = 2000.0              # Hz
        Ac = 1.0                 # amplitude da portadora

        # ---- indice de modulacao --------------------------------------------
        ma = 0.5                 # 50%  (0<ma<1 -> AM convencional sem sobremod.)

        # ---- ruido de canal -------------------------------------------------
        sigma = 0.02             # desvio-padrao do ruido aditivo
    ENDCODE'''


def render():
    out = io.StringIO(); w = out.write
    w("version = 4.2\n\n//\n")
    w("// Modelo: modulador AM (DSB-LC) para estudo de demodulacao\n")
    w("// ECOM060 - Instrumentacao Eletronica - UFAL - 2026.2\n//\n\n")
    w('model "%s" {\n' % MODEL_NAME)
    w(CONFIG + "\n\n")
    w("    component Subsystem Root {\n")
    for t, n, props, pos in C:
        w('        component "%s" %s {\n' % (t, n))
        for k in sorted(props): w('            %s = "%s"\n' % (k, props[k]))
        w("        }\n        [\n            position = %d, %d\n        ]\n\n" % pos)
    for n, kind, pos in J:
        w("        junction %s %s\n        [\n            position = %d, %d\n        ]\n\n"
          % (n, kind, pos[0], pos[1]))
    for i, (a, b, bp) in enumerate(W, start=1):
        w("        connect %s %s as Connection%d\n" % (a, b, i))
        if bp:
            w("        [\n            breakpoints = %s\n        ]\n"
              % "; ".join("%d, %d" % p for p in bp))
    w("    }\n\n")
    w(MODEL_INIT + "\n}\n")
    return out.getvalue()


if __name__ == "__main__":
    txt = render()
    open("/home/claude/out/%s.tse" % MODEL_NAME, "w", encoding="utf-8").write(txt)
    print("componentes:", len(C), "| junctions:", len(J), "| conexoes:", len(W))
