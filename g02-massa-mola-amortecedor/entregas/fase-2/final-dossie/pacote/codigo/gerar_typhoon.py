# -*- coding: utf-8 -*-
"""
Gera os modelos TyphoonSim (.tse) e os paineis HIL SCADA (.cus) do G02 (ECOM060, 2026.2)
em texto puro, no formato 4.2 salvo pelo TyphoonSim 2026.2 (o mesmo dos modelos da Entrega 02).

Variantes:
  f1e3   Fase 1, Entrega 03: cadeia do piezo (E01+E02 da Fase 1) + gerador dos 3 ensaios, sem planta
  e2     Fase 2, Entrega 02: equivalente eletrico (RLC serie) + gerador de ensaios
  e3     Fase 2, Entrega 03: planta + caminho ideal + caminho real (malha aberta por padrao)
  final  Fase 2, Entrega 04 e Entrega Final: planta + instrumentacao + seletor + PID + compensacao

Uso:  python gerar_typhoon.py <variante> <pasta_saida>
Saida: <pasta>/modelo.tse e <pasta>/painel.cus
Os blocos C function sao os mesmos do gemeo numerico (gemeo.py), linha a linha.
"""
import sys, os, uuid

TS = "1e-4"

# ======================================================================================
# Codigo C dos blocos (os mesmos algoritmos de gemeo.py)
# ======================================================================================
def sec(code):
    return "/*Begin code section*/\n" + code.strip("\n") + "\n/*End code section*/"


C_GERADOR = dict(
    inputs=["ensaio", "amplitude", "disparo"], outputs=["r", "d", "t_ens"],
    glob="""
/* Gerador dos ensaios. Uma borda de subida em 'disparo' zera o relogio do ensaio. */
double t_G = 0.0;          /* relogio do ensaio [s]       */
double disp_ant_G = 0.0;   /* disparo no passo anterior   */
double TS_G = 1e-4;        /* passo [s]                   */
double T_EV_G = %(t_ev)s;  /* instante do evento [s]      */
int ens_G = 1;
double A_G = 0.0;
""",
    init="t_G = 0.0;\ndisp_ant_G = 0.0;",
    output="""
ens_G = (int)(ensaio + 0.5);
A_G = amplitude;
d = 0.0;
if (ens_G == 1) {                 /* (a) degrau a partir do repouso */
    r = (t_G >= T_EV_G) ? A_G : 0.0;
} else if (ens_G == 2) {          /* (b) condicao inicial nao nula: segura em A e solta */
    r = (t_G < T_EV_G) ? A_G : 0.0;
} else if (ens_G == 3) {          /* (c) transitorio temporario: pulso de 1,5 A por 0,5 s */
    r = (t_G >= T_EV_G && t_G < T_EV_G + 0.5) ? 1.5 * A_G : A_G;
} else {                          /* (d) perturbacao de forca de 0,5 A em t_ev */
    r = (t_G >= 0.5) ? A_G : 0.0;
    d = (t_G >= T_EV_G) ? 0.5 * A_G : 0.0;
}
t_ens = t_G;
""",
    update="""
if (disparo > 0.5 && disp_ant_G <= 0.5) {
    t_G = 0.0;
} else {
    t_G = t_G + TS_G;
}
disp_ant_G = disparo;
""")

C_PID = dict(
    inputs=["r", "y", "d", "malha", "Kp", "Ki", "Kd", "disparo"], outputs=["u", "F"],
    glob="""
/* PID com derivada na medicao (filtro Tf), saturacao do atuador e anti-windup condicional. */
double integ_C = 0.0;
double dfilt_C = 0.0;
double dnovo_C = 0.0;
double yprev_C = 0.0;
int primeiro_C = 1;
double e_C = 0.0;
double ulin_C = 0.0;
double u_C = 0.0;
double disp_ant_C = 0.0;
double TS_C = 1e-4;     /* s */
double TF_C = 0.01;     /* s, filtro da derivada */
double UMAX_C = 60.0;   /* N, limite do atuador  */
""",
    init="integ_C = 0.0;\ndfilt_C = 0.0;\nprimeiro_C = 1;",
    output="""
if (malha > 0.5) {
    e_C = r - y;
    if (primeiro_C) { yprev_C = y; }
    dnovo_C = dfilt_C + TS_C / TF_C * (-Kd * (y - yprev_C) / TS_C - dfilt_C);
    ulin_C = Kp * e_C + Ki * integ_C + dnovo_C;
    u_C = ulin_C;
    if (u_C > UMAX_C) { u_C = UMAX_C; }
    if (u_C < -UMAX_C) { u_C = -UMAX_C; }
} else {
    e_C = 0.0;
    dnovo_C = 0.0;
    ulin_C = r;
    u_C = r;                   /* malha aberta: a referencia e a propria forca */
}
u = u_C;
F = u_C + d;
""",
    update="""
if (disparo > 0.5 && disp_ant_C <= 0.5) {      /* novo ensaio: zera os estados do PID */
    integ_C = 0.0;
    dfilt_C = 0.0;
    primeiro_C = 1;
} else if (malha > 0.5) {
    dfilt_C = dnovo_C;
    yprev_C = y;
    primeiro_C = 0;
    if (u_C == ulin_C || (ulin_C > UMAX_C && e_C < 0.0) || (ulin_C < -UMAX_C && e_C > 0.0)) {
        integ_C = integ_C + e_C * TS_C;
    }
} else {
    integ_C = 0.0;
    dfilt_C = 0.0;
    primeiro_C = 1;
}
disp_ant_C = disparo;
""")

C_PORTADORA = dict(
    inputs=["chop"], outputs=["car"],
    glob="""
/* Portadora da chopagem (modulacao) e da demodulacao sincrona. */
double t_P = 0.0;
double TS_P = 1e-4;
double F_CH_P = 100.0;                    /* Hz */
double PI_P = 3.14159265358979323846;
""",
    init="t_P = 0.0;",
    output="""
if (chop > 0.5) {
    car = 1.41421356237 * sin(2.0 * PI_P * F_CH_P * t_P);
} else {
    car = 1.0;                            /* sem chopagem: forca aplicada direto (DC) */
}
""",
    update="""
t_P = t_P + TS_P;
if (t_P >= 1.0) { t_P = t_P - 1.0; }      /* 100 periodos inteiros por segundo */
""")

C_SENSOR = dict(
    inputs=["Fk", "car", "en_sens", "S_real_mVN", "en_lim", "en_res"], outputs=["vctrl", "F_inst"],
    glob="""
/* Camada estatica do disco piezoeletrico (Murata 7BB-20-6, ceramica APC 850).
 * S nominal = d33/Ct = 400 pC/N / 10 nF = 40 mV/N.
 * Pior caso inferior (padrao): 320 pC/N / 13 nF = 24,6 mV/N (-38 %).
 * Limiar e resolucao: estimativas da equipe. */
double S_NOM_S = 0.04;     /* V/N */
double F_LIM_S = 0.02;     /* N   */
double F_RES_S = 0.01;     /* N   */
double S_use_S = 0.04;
double Fa_S = 0.0;
""",
    init="S_use_S = S_NOM_S;",
    output="""
F_inst = Fk * car;                                  /* forca modulada pela portadora */
S_use_S = (en_sens > 0.5) ? (S_real_mVN * 1e-3) : S_NOM_S;
Fa_S = F_inst;
if (en_lim > 0.5 && fabs(Fa_S) < F_LIM_S) { Fa_S = 0.0; }                 /* limiar    */
if (en_res > 0.5) { Fa_S = F_RES_S * floor(Fa_S / F_RES_S + 0.5); }       /* resolucao */
vctrl = S_use_S * Fa_S;                              /* fonte de Thevenin do piezo */
""",
    update="")

C_RUIDO = dict(
    inputs=["en_ruido", "sigma_mV"], outputs=["n"],
    glob="""
/* Ruido branco gaussiano: xorshift32 (semente fixa) + Box-Muller, retido a cada 1e-4 s. */
unsigned int x_N = 610839777u;
double g_N = 0.0;
double u1_N = 0.5;
double u2_N = 0.5;
double PI_N = 3.14159265358979323846;
""",
    init="""
x_N = 610839777u;
x_N ^= x_N << 13; x_N ^= x_N >> 17; x_N ^= x_N << 5;
u1_N = ((x_N >> 8) + 0.5) / 16777216.0;
x_N ^= x_N << 13; x_N ^= x_N >> 17; x_N ^= x_N << 5;
u2_N = ((x_N >> 8) + 0.5) / 16777216.0;
g_N = sqrt(-2.0 * log(u1_N)) * cos(2.0 * PI_N * u2_N);
""",
    output="n = (en_ruido > 0.5) ? (sigma_mV * 1e-3 * g_N) : 0.0;",
    update="""
x_N ^= x_N << 13; x_N ^= x_N >> 17; x_N ^= x_N << 5;
u1_N = ((x_N >> 8) + 0.5) / 16777216.0;
x_N ^= x_N << 13; x_N ^= x_N >> 17; x_N ^= x_N << 5;
u2_N = ((x_N >> 8) + 0.5) / 16777216.0;
g_N = sqrt(-2.0 * log(u1_N)) * cos(2.0 * PI_N * u2_N);
""")

C_INTERF = dict(
    inputs=["en_interf"], outputs=["interf"],
    glob="""
/* Entradas espurias na entrada do pre-amplificador (10 MOhm):
 * offset 3 mV (VIO tipico do TL072), deriva 5 mV a 0,05 Hz (piroeletricidade do PZT, estimativa),
 * zumbido de 60 Hz com 20 mV de pico (entrada sem blindagem, estimativa). */
double A_OFF_I = 3e-3;
double A_DRIFT_I = 5e-3;
double F_DRIFT_I = 0.05;
double A_HUM_I = 20e-3;
double TS_I = 1e-4;
double PI_I = 3.14159265358979323846;
double t_I = 0.0;
""",
    init="t_I = 0.0;",
    output="""
if (en_interf > 0.5) {
    interf = A_OFF_I + A_DRIFT_I * sin(2.0 * PI_I * F_DRIFT_I * t_I) + A_HUM_I * sin(2.0 * PI_I * 60.0 * t_I);
} else {
    interf = 0.0;
}
""",
    update="t_I = t_I + TS_I;\nif (t_I >= 20.0) { t_I = t_I - 20.0; }")


def c_lockin(G):
    return dict(
        inputs=["v_piezo", "n", "interf", "car", "fc_Hz"], outputs=["pre_amp", "demod", "bw"],
        glob="""
/* Condicionamento: pre-amplificador nao inversor (G = %(G)s) + demodulacao sincrona (lock-in)
 * + Butterworth de 2a ordem com fc ajustavel, discretizado por Tustin a 10 kHz. */
double G_L = %(G)s;
double PI_L = 3.14159265358979323846;
double TS_L = 1e-4;
double fc_ant_L = -1.0;
double B0_L = 0.0, B1_L = 0.0, B2_L = 0.0, A1_L = 0.0, A2_L = 0.0;
double z0_L = 0.0, z1_L = 0.0;
double dem_L = 0.0, y_L = 0.0;
double wb_L = 0.0, K_L = 0.0, a2_L = 0.0, a1_L = 0.0, A0_L = 0.0, fcu_L = 1.0;
""" % dict(G=G),
        init="fc_ant_L = -1.0;\nz0_L = 0.0;\nz1_L = 0.0;",
        output="""
fcu_L = (fc_Hz < 0.05) ? 0.05 : fc_Hz;
if (fcu_L != fc_ant_L) {                   /* recalcula os coeficientes quando fc muda */
    wb_L = 2.0 * PI_L * fcu_L;
    K_L = 2.0 / TS_L;
    a2_L = 1.0 / (wb_L * wb_L);
    a1_L = 1.41421356237 / wb_L;
    A0_L = a2_L * K_L * K_L + a1_L * K_L + 1.0;
    B0_L = 1.0 / A0_L;
    B1_L = 2.0 / A0_L;
    B2_L = 1.0 / A0_L;
    A1_L = (2.0 - 2.0 * a2_L * K_L * K_L) / A0_L;
    A2_L = (a2_L * K_L * K_L - a1_L * K_L + 1.0) / A0_L;
    fc_ant_L = fcu_L;
}
pre_amp = G_L * (v_piezo + n + interf);
dem_L = pre_amp * car;
y_L = B0_L * dem_L + z0_L;
demod = dem_L;
bw = y_L;
""",
        update="""
z0_L = B1_L * dem_L - A1_L * y_L + z1_L;
z1_L = B2_L * dem_L - A2_L * y_L;
""")


def c_proc(G):
    return dict(
        inputs=["bw", "comp_cal", "S_cal_mVN", "comp_din", "fc_corr_Hz", "f_f_Hz"], outputs=["y_med"],
        glob="""
/* Processamento: escala K = 1/(S_nom*G) (1 V = 1 N = 1 cm), calibracao de 1 ponto e
 * correcao calculada da dinamica do filtro: C(s) = (s^2/wb^2 + sqrt2 s/wb + 1)/(s/wf + 1)^2. */
double S_NOM_P = 0.04;
double G_P = %(G)s;
double PI_P2 = 3.14159265358979323846;
double TS_P2 = 1e-4;
double ym_P = 0.0, yc_P = 0.0;
double fcc_ant_P = -1.0, ff_ant_P = -1.0;
double C0_P = 1.0, C1_P = 0.0, C2_P = 0.0, D1_P = 0.0, D2_P = 0.0;
double zc0_P = 0.0, zc1_P = 0.0;
double wb_P = 0.0, wf_P = 0.0, K_P = 0.0, b2_P = 0.0, b1_P = 0.0, a2_P = 0.0, a1_P = 0.0, A0_P = 0.0;
double fcu_P = 1.0, ffu_P = 10.0;
""" % dict(G=G),
        init="fcc_ant_P = -1.0;\nzc0_P = 0.0;\nzc1_P = 0.0;",
        output="""
fcu_P = (fc_corr_Hz < 0.05) ? 0.05 : fc_corr_Hz;
ffu_P = (f_f_Hz < fcu_P) ? fcu_P : f_f_Hz;
if (fcu_P != fcc_ant_P || ffu_P != ff_ant_P) {
    wb_P = 2.0 * PI_P2 * fcu_P;
    wf_P = 2.0 * PI_P2 * ffu_P;
    K_P = 2.0 / TS_P2;
    b2_P = 1.0 / (wb_P * wb_P);  b1_P = 1.41421356237 / wb_P;
    a2_P = 1.0 / (wf_P * wf_P);  a1_P = 2.0 / wf_P;
    A0_P = a2_P * K_P * K_P + a1_P * K_P + 1.0;
    C0_P = (b2_P * K_P * K_P + b1_P * K_P + 1.0) / A0_P;
    C1_P = (2.0 - 2.0 * b2_P * K_P * K_P) / A0_P;
    C2_P = (b2_P * K_P * K_P - b1_P * K_P + 1.0) / A0_P;
    D1_P = (2.0 - 2.0 * a2_P * K_P * K_P) / A0_P;
    D2_P = (a2_P * K_P * K_P - a1_P * K_P + 1.0) / A0_P;
    fcc_ant_P = fcu_P;
    ff_ant_P = ffu_P;
}
ym_P = bw / (S_NOM_P * G_P);
if (comp_cal > 0.5 && S_cal_mVN > 0.1) { ym_P = ym_P * S_NOM_P / (S_cal_mVN * 1e-3); }
yc_P = C0_P * ym_P + zc0_P;                /* o corretor roda sempre; a chave escolhe a saida */
y_med = (comp_din > 0.5) ? yc_P : ym_P;
""",
        update="""
zc0_P = C1_P * ym_P - D1_P * yc_P + zc1_P;
zc1_P = C2_P * ym_P - D2_P * yc_P;
""")


C_SELETOR = dict(
    inputs=["y_real_med", "y_ideal", "seletor"], outputs=["y_ctrl"],
    glob="/* Seletor ideal/real: escolhe qual leitura chega ao controlador. */\nint dummy_SEL = 0;",
    init="dummy_SEL = 0;",
    output="y_ctrl = (seletor > 0.5) ? y_real_med : y_ideal;",
    update="")

# ======================================================================================
# Escritor do .tse
# ======================================================================================
DEFAULTS = {
    "core/C function": '''            input_terminals = "real in;"
            input_terminals_show_labels = "False;"
            input_terminals_feedthrough = "True;"
            input_terminals_dimensions = "inherit;"
            output_terminals = "real out;"
            output_terminals_show_labels = "False;"
            output_terminals_feedthrough = "True;"
            output_terminals_dimensions = "inherit;"
            output_fnc = ""
            update_fnc = ""
            init_fnc = ""
            global_variables = ""
            parameters = ""
            library_load_type = "Compile-time load"
            dll_file_path = ""
            dll_file_path_full = ""
            arm_a9_file_path = ""
            arm_a9_file_path_full = ""
            arm_a53_file_path = ""
            arm_a53_file_path_full = ""
            h_file_path = ""
            h_file_path_full = ""
            add_src_path = ""
            add_src_path_full = ""
            convert_to_relative_dll = "True"
            convert_to_relative_a = "True"
            convert_to_relative_src = "True"
            arb_defs = ""
            add_macros = ""
            skip_pre_cmpl_check = "False"
            generate_for_hil = "True"
            execution_rate = "inherit"
            _supported_platforms = "[\\'generic\\']"
            refresh = "refresh"''',
    "core/Capacitor": '''            signal_access = "inherit"
            capacitance = "1e-6"
            initial_voltage = "0"
            pole_shift_ignore = "False"
            visible = "True"''',
    "core/Inductor": '''            signal_access = "inherit"
            inductance = "1e-3"
            initial_current = "0.0"
            pole_shift_ignore = "False"
            visible = "True"''',
    "core/Resistor": '''            resistance = "1"
            param_set = ""''',
    "core/Gain": '''            gain = "1"
            multiplication = "Element-wise(K.*u)"
            force_tml = "True"
            _tunable = "False"
            execution_rate = "inherit"''',
    "core/Probe": '''            signal_access = "inherit"
            addr = "0"
            override_signal_name = "False"
            signal_name = ""
            signal_type = "generic"
            streaming_en = "False"
            streaming_er_idx = "0"
            execution_rate = "inherit"''',
    "core/Scope": '''            signals_data = "{}"
            selected_signals = "[]"
            user_range_data = "{}"''',
    "core/SCADA Input": '''            signal_access = "inherit"
            addr = "0"
            format = "real"
            override_signal_name = "False"
            signal_name = ""
            signal_type = "real"
            min = "-1e6"
            max = "1e6"
            def_value = "0"
            unit = " "
            execution_rate = "100e-6"''',
    "core/Signal Controlled Voltage Source": '''            execution_rate = "inherit"''',
}
MEAS = '''            signal_access = "inherit"
            bw_limit = "False"
            frequency = "10e3"
            comparator_enable = "False"
            operator = "greater"
            threshold = "0"
            cmp_abs_value = "False"
            feed_forward = "false"
            sig_output = "False"
            sig_output_filt_and_full_bw = "False"
            execution_rate = "100e-6"
            addr = "0"
            nd_msr_estimation = "false"
            dev_cpl_msr = "false"
            host_device = "0"
            output_to_device = "0"
            dev_cpl_index = "0"
            dev_cpl_var_nb = "0"
            visible = "True"
            override_signal_name = "False"
            signal_name = ""'''
DEFAULTS["core/Voltage Measurement"] = MEAS
DEFAULTS["core/Current Measurement"] = MEAS

CONFIG = '''    configuration {
        hil_device = "VHIL+"
        hil_configuration_id = 1
        simulation_method = exact
        simulation_time_step = auto
        simulation_discret_scaling = 1.0
        dsp_timer_periods = 100e-6, 50e-3
        ss_calc_method = "systematic elimination"
        enb_pole_shift = True
        enb_gds_oversampling = True
        show_modes = False
        device_ao_limit_enable = False
        reset_analog_outputs_on_sim_stop = True
        reset_analog_outputs_on_sim_stop_mode = Offset values
        reset_digital_outputs_on_sim_stop = True
        vhil_adio_loopback = False
        dma_enable = False
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
        ground_scope_core = False
        dss_num_tol = 1e-15
        cce_platform = "generic"
        cce_use_relative_names = False
        cce_type_mapping_real = "double"
        cce_type_mapping_uint = "unsigned int"
        cce_type_mapping_int = "int"
        cce_term_var_location = "local"
        cce_directory = ""
        cce_custom_type_int = ""
        cce_custom_type_uint = ""
        cce_custom_type_real = ""
        tunable_params = "component defined"
        sp_compiler_type = "C compiler"
        sig_stim = "off"
        export_resource_list = ""
        export_dependency_list = ""
        excluded_resource_list = ""
        excluded_component_from_locking_list = ""
        export_out_file = ""
        export_lock_top_level = True
        export_encrypt_library = True
        export_encrypt_resources = True
        solver_type = "DAE"
        integration_method = "BDF"
        max_sim_step = 1e-4
        simulation_time = %(tsim)s
        abs_tol = 1e-3
        rel_tol = 1e-3
        init_sim_step = 1e-6
        r_on_sw = 1e-3
        v_on_diode = 0.1
        data_sampling_rate = 0
        feedthrough_validation_error_level = error
    }
'''


def q(s):
    """Escapa uma string para o .tse."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def nome(n):
    return f'"{n}"' if any(ch in n for ch in " ,()=+") or n[0].isdigit() else n


class Modelo:
    def __init__(self, nome_modelo):
        self.nome = nome_modelo
        self.comps = []      # (tipo, nome, props, pos, extra)
        self.nets = {}       # chave -> (kind, [terminais])
        self.areas = []
        self.tipos = set()

    def comp(self, tipo, n, pos, props=None, size=None, rot=None):
        self.comps.append((tipo, n, props or {}, pos, size, rot))
        self.tipos.add(tipo)
        return n

    def cfun(self, n, spec, pos, fmt=None):
        fmt = fmt or {}
        ins, outs = spec["inputs"], spec["outputs"]
        props = {
            "arb_defs": sec(spec["glob"] % fmt if fmt else spec["glob"]),
            "execution_rate": TS,
            "init_fnc": sec(spec["init"]),
            "input_terminals": "".join(f"real {i};" for i in ins),
            "input_terminals_dimensions": ";".join("inherit" for _ in ins),
            "input_terminals_feedthrough": ";".join("True" for _ in ins),
            "input_terminals_show_labels": ";".join("True" for _ in ins),
            "output_fnc": sec(spec["output"]),
            "output_terminals": "".join(f"real {o};" for o in outs),
            "output_terminals_dimensions": ";".join("1" for _ in outs),
            "output_terminals_feedthrough": ";".join("True" for _ in outs),
            "output_terminals_show_labels": ";".join("True" for _ in outs),
            "update_fnc": sec(spec["update"] or "/* sem estados */"),
        }
        h = max(len(ins), len(outs)) * 24 + 24
        return self.comp("core/C function", n, pos, props, size=(112, h))

    def liga(self, chave, terminal, kind="sp"):
        k, lst = self.nets.setdefault(chave, (kind, []))
        lst.append(terminal)

    def area(self, titulo, pos, size, cor):
        self.areas.append((titulo, pos, size, cor))

    def texto(self, tsim):
        L = ["version = 4.2", "", "//", "// Saved by sw version: 2026.2", "//", "",
             f'model "{self.nome}" {{', CONFIG % dict(tsim=tsim), "    component Subsystem Root {"]
        for tipo, n, props, pos, size, rot in self.comps:
            L.append(f'        component "{tipo}" {nome(n)} {{')
            for k, v in props.items():
                L.append(f'            {k} = "{q(str(v))}"')
            L.append("        }")
            L.append("        [")
            L.append(f"            position = {pos[0]}, {pos[1]}")
            if rot:
                L.append(f"            rotation = {rot}")
            if size:
                L.append(f"            size = {size[0]}, {size[1]}")
            L.append("        ]")
            L.append("")
        conns = []
        jn = 0
        for chave, (kind, terms) in self.nets.items():
            if len(terms) < 2:
                continue
            if len(terms) == 2:
                conns.append((terms[0], terms[1]))
            else:
                jn += 1
                j = f"J_{chave}"
                # posicao da juncao: perto do primeiro terminal
                L.append(f"        junction {j} {kind}")
                L.append("        [")
                L.append(f"            position = {self._pos_term(terms[0])}")
                L.append("        ]")
                L.append("")
                for t in terms:
                    conns.append((j, t))
        for i, (titulo, pos, size, cor) in enumerate(self.areas):
            L.append(f"        scheme_area Area{i+1} {{")
            L.append('            title = <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '
                     '"http://www.w3.org/TR/REC-html40/strict.dtd"><html><head><meta name="qrichtext" content="1" />'
                     '<meta charset="utf-8" /><style type="text/css">p, li { white-space: pre-wrap; }hr { height: 1px; '
                     'border-width: 0; }li.unchecked::marker { content: "\\2610"; }li.checked::marker { content: '
                     '"\\2612"; }</style></head><body style=" font-family:\'Tahoma\'; font-size:14pt; font-weight:100; '
                     'font-style:normal;"><p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; '
                     'margin-right:0px; -qt-block-indent:0;text-indent:0px;">' + titulo + '</p></body></html>')
            L.append("        }")
            L.append("        [")
            L.append(f"            position = {pos[0]}, {pos[1]}")
            L.append(f"            size = {size[0]}, {size[1]}")
            L.append(f"            background_color = {cor}")
            L.append("        ]")
            L.append("")
        for i, (a, b) in enumerate(conns):
            L.append(f"        connect {self._t(a)} {self._t(b)} as Connection{i+1}")
        L.append("    }")
        L.append("")
        L.append("    default {")
        for tipo in sorted(self.tipos):
            if tipo in DEFAULTS:
                L.append(f'        "{tipo}" {{')
                L.append(DEFAULTS[tipo])
                L.append("        }")
                L.append("")
        L.append("    }")
        L.append("}")
        return "\n".join(L) + "\n"

    def _t(self, t):
        if "." not in t:
            return t
        c, term = t.rsplit(".", 1)
        if any(ch in c for ch in " ,()=+") or c[0].isdigit():
            return f'"{c}.{term}"'
        return t

    def _pos_term(self, t):
        c = t.rsplit(".", 1)[0]
        for tipo, n, props, pos, size, rot in self.comps:
            if n == c:
                return f"{pos[0] + 40}, {pos[1]}"
        return "8000, 8000"


# ======================================================================================
# Montagem das variantes
# ======================================================================================
def scada(m, n, pos, default, lo, hi, unit=""):
    m.comp("core/SCADA Input", n, pos, {"def_value": str(default), "execution_rate": TS, "max": str(hi),
                                         "min": str(lo), "unit": unit or " "})
    return f"{n}.out"


def probe(m, n, pos, chave):
    m.comp("core/Probe", n, pos)
    m.liga(chave, f"{n}.in")


def planta(m, x0, y0, chave_F):
    """RLC serie: m <-> L, c <-> R, 1/k <-> C. v_C = k x = forca na mola [V = N = cm]."""
    m.comp("core/Signal Controlled Voltage Source", "Vf_atuador", (x0, y0 + 100), rot="right", size=(64, 32))
    m.comp("core/Inductor", "L_massa", (x0 + 100, y0), {"inductance": "1"})
    m.comp("core/Current Measurement", "v_massa", (x0 + 210, y0), {"execution_rate": TS, "sig_output": "True"},
           size=(64, 32))
    m.comp("core/Resistor", "R_amortecedor", (x0 + 320, y0), {"resistance": "6"})
    m.comp("core/Capacitor", "C_mola", (x0 + 420, y0 + 100), {"capacitance": "0.01"}, rot="right")
    m.comp("core/Voltage Measurement", "y_real", (x0 + 520, y0 + 100), {"execution_rate": TS, "sig_output": "True"},
           rot="right", size=(64, 32))
    m.comp("core/Ground", "gnd_planta", (x0 + 260, y0 + 230))
    m.liga(chave_F, "Vf_atuador.in")
    m.liga("p1", "Vf_atuador.p_node", "pe"); m.liga("p1", "L_massa.p_node", "pe")
    m.liga("p2", "L_massa.n_node", "pe"); m.liga("p2", "v_massa.p_node", "pe")
    m.liga("p3", "v_massa.n_node", "pe"); m.liga("p3", "R_amortecedor.p_node", "pe")
    m.liga("p4", "R_amortecedor.n_node", "pe"); m.liga("p4", "C_mola.p_node", "pe"); m.liga("p4", "y_real.p_node", "pe")
    for t in ("C_mola.n_node", "y_real.n_node", "Vf_atuador.n_node", "gnd_planta.node"):
        m.liga("p0", t, "pe")
    m.area("Planta: equivalente eletrico (L = m = 1 H, R = c = 6 ohm, C = 1/k = 10 mF; 1 V = 1 N = 1 cm)",
           (x0 + 280, y0 + 80), (720, 360), "#0e2a78d6")


def cadeia_real(m, x0, y0, chave_F, G):
    """Sensor piezo + entradas espurias + condicionamento + processamento."""
    m.cfun("portadora_chopper", C_PORTADORA, (x0, y0 - 180))
    m.liga("chop", "portadora_chopper.chop")
    m.liga("car", "portadora_chopper.car")
    m.cfun("sensor_piezo", C_SENSOR, (x0, y0))
    m.liga(chave_F, "sensor_piezo.Fk"); m.liga("car", "sensor_piezo.car")
    for i in ("en_sens", "S_real_mVN", "en_lim", "en_res"):
        m.liga(i, f"sensor_piezo.{i}")
    m.liga("vctrl", "sensor_piezo.vctrl"); m.liga("F_inst", "sensor_piezo.F_inst")
    probe(m, "vctrl", (x0 + 110, y0 - 90), "vctrl")
    probe(m, "F_inst", (x0 + 110, y0 + 90), "F_inst")
    # Thevenin do piezo: Vs em serie com Ct, carga Rin
    m.comp("core/Signal Controlled Voltage Source", "Vs_piezo", (x0 + 200, y0 + 80), rot="right", size=(64, 32))
    m.comp("core/Capacitor", "Ct_piezo", (x0 + 290, y0), {"capacitance": "10e-9"})
    m.comp("core/Resistor", "Rin_preamp", (x0 + 390, y0 + 80), {"resistance": "10e6"}, rot="right")
    m.comp("core/Voltage Measurement", "v_piezo", (x0 + 480, y0 + 80), {"execution_rate": TS, "sig_output": "True"},
           rot="right", size=(64, 32))
    m.comp("core/Ground", "gnd_piezo", (x0 + 330, y0 + 200))
    m.liga("vctrl", "Vs_piezo.in")
    m.liga("q1", "Vs_piezo.p_node", "pe"); m.liga("q1", "Ct_piezo.p_node", "pe")
    m.liga("q2", "Ct_piezo.n_node", "pe"); m.liga("q2", "Rin_preamp.p_node", "pe"); m.liga("q2", "v_piezo.p_node", "pe")
    for t in ("Rin_preamp.n_node", "v_piezo.n_node", "Vs_piezo.n_node", "gnd_piezo.node"):
        m.liga("q0", t, "pe")
    m.liga("vpz", "v_piezo.out")
    m.area("Sensor (elemento primario): disco piezoeletrico 7BB-20-6, Thevenin Ct-Rin", (x0 + 230, y0 + 20),
           (700, 420), "#0eeb6834")
    # entradas espurias
    m.cfun("ruido_branco", C_RUIDO, (x0 + 640, y0 - 160))
    m.liga("en_ruido", "ruido_branco.en_ruido"); m.liga("sigma_mV", "ruido_branco.sigma_mV")
    m.liga("n", "ruido_branco.n")
    m.cfun("interferencia", C_INTERF, (x0 + 640, y0 + 200))
    m.liga("en_interf", "interferencia.en_interf"); m.liga("interf", "interferencia.interf")
    m.area("Entradas espurias (60 Hz, offset, deriva, ruido)", (x0 + 640, y0 + 20), (200, 520), "#0e1baf7a")
    # condicionamento
    m.cfun("condicionamento_lockin", c_lockin(G), (x0 + 820, y0))
    m.liga("vpz", "condicionamento_lockin.v_piezo"); m.liga("n", "condicionamento_lockin.n")
    m.liga("interf", "condicionamento_lockin.interf"); m.liga("car", "condicionamento_lockin.car")
    m.liga("fc_Hz", "condicionamento_lockin.fc_Hz")
    for o in ("pre_amp", "demod", "bw"):
        m.liga(o, f"condicionamento_lockin.{o}")
    probe(m, "pre_amp", (x0 + 960, y0 - 120), "pre_amp")
    probe(m, "demod", (x0 + 960, y0 - 60), "demod")
    probe(m, "bw", (x0 + 960, y0 + 120), "bw")
    m.area(f"Condicionamento: pre-amp G = {G} + lock-in (Butterworth fc)", (x0 + 860, y0 + 20), (300, 420),
           "#0eeda100")
    # processamento
    m.cfun("processamento_compensacao", c_proc(G), (x0 + 1080, y0))
    m.liga("bw", "processamento_compensacao.bw")
    for i in ("comp_cal", "S_cal_mVN", "comp_din", "fc_corr_Hz", "f_f_Hz"):
        m.liga(i, f"processamento_compensacao.{i}")
    m.liga("ymed", "processamento_compensacao.y_med")
    probe(m, "y_med", (x0 + 1220, y0 - 80), "ymed")
    m.area("Processamento e compensacao (escala, calibracao, correcao do filtro)", (x0 + 1120, y0 + 20),
           (260, 420), "#0e6250d6")


def scada_cadeia(m, x0, y0, d):
    """Entradas SCADA das caracteristicas do instrumento real."""
    lst = [("chop", 1, 0, 1), ("en_sens", 1, 0, 1), ("S_real_mVN", 24.6, 1, 200), ("en_lim", 1, 0, 1),
           ("en_res", 1, 0, 1), ("en_ruido", 1, 0, 1), ("sigma_mV", 20, 0, 1000), ("en_interf", 1, 0, 1),
           ("fc_Hz", d.get("fc", 1.0), 0.05, 1000), ("comp_cal", 0, 0, 1), ("S_cal_mVN", 24.6, 1, 200),
           ("comp_din", 0, 0, 1), ("fc_corr_Hz", 1.0, 0.05, 1000), ("f_f_Hz", 10.0, 0.05, 1000)]
    for i, (n, dv, lo, hi) in enumerate(lst):
        m.liga(n, scada(m, n, (x0 + (i // 7) * 160, y0 + (i % 7) * 60), dv, lo, hi))
    m.area("Painel: caracteristicas do instrumento real (SCADA Inputs)", (x0 + 80, y0 + 180), (400, 480),
           "#0e898781")


def scope(m, pos, sinais):
    vp = {s: [i + 1] for i, s in enumerate(sinais)}
    data = {"plot_settings": {"layout": "Vertical", "background_color": "white", "legend_visible": True,
                              "signals_tooltips_enabled": True},
            "signals": {s: {"viewports": vp[s], "type": "analog", "color": {str(vp[s][0]): "#FF0000"},
                            "display": {str(vp[s][0]): "solid"}, "is_manual": {str(vp[s][0]): False}}
                        for s in sinais},
            "viewports": {str(i): {"log_scale_x": False, "log_scale_y": False, "y_axis_db": False}
                          for i in range(1, 7)}}
    import json
    m.comp("core/Scope", "Scope1", pos, {"selected_signals": "[" + ", ".join(f"'{s}'" for s in sinais) + "]",
                                          "signals_data": json.dumps(data)})


def montar(var):
    if var == "f1e3":
        m = Modelo("g02_fase1_e03_validacao_funcional")
        m.cfun("gerador_ensaios", C_GERADOR, (7000, 7800), fmt=dict(t_ev="1.0"))
        for i, (n, dv, lo, hi) in enumerate([("ensaio", 1, 1, 3), ("amplitude", 0.6, 0, 2), ("disparo", 0, 0, 1)]):
            m.liga(n, scada(m, n, (6800, 7740 + i * 60), dv, lo, hi))
            m.liga(n, f"gerador_ensaios.{n}")
        m.liga("Fref", "gerador_ensaios.r"); m.liga("dd", "gerador_ensaios.d"); m.liga("tens", "gerador_ensaios.t_ens")
        probe(m, "Videal", (7140, 7700), "Fref")
        probe(m, "t_ensaio", (7140, 7920), "tens")
        m.area("Gerador dos ensaios (forca rms em N, modulada a 100 Hz)", (6930, 7800), (420, 360), "#0e52514e")
        cadeia_real(m, 7400, 7800, "Fref", G=25)
        scada_cadeia(m, 6700, 8300, {})
        scope(m, (8700, 7500), ["Videal", "y_med", "pre_amp", "v_piezo"])
        return m, 12.0
    m = Modelo({"e2": "g02_fase2_e02_equivalente_eletrico", "e3": "g02_fase2_e03_malha_aberta",
                "final": "g02_fase2_final_sistema_instrumentado"}[var])
    # gerador
    m.cfun("gerador_ensaios", C_GERADOR, (6500, 7000), fmt=dict(t_ev="2.0"))
    for i, (n, dv, lo, hi) in enumerate([("ensaio", 1, 1, 4), ("amplitude", 10, -20, 20), ("disparo", 0, 0, 1)]):
        m.liga(n, scada(m, n, (6300, 6940 + i * 60), dv, lo, hi))
        m.liga(n, f"gerador_ensaios.{n}")
    m.liga("r", "gerador_ensaios.r"); m.liga("d", "gerador_ensaios.d"); m.liga("tens", "gerador_ensaios.t_ens")
    probe(m, "r", (6640, 6900), "r")
    probe(m, "t_ensaio", (6640, 7120), "tens")
    m.area("Gerador de ensaios e referencia r", (6440, 7000), (420, 360), "#0e52514e")
    # controlador / atuador
    if var == "e2":
        planta(m, 6900, 6900, "r")
    else:
        m.cfun("controlador_PID", C_PID, (6700, 7700))
        m.liga("r", "controlador_PID.r"); m.liga("yctrl", "controlador_PID.y"); m.liga("d", "controlador_PID.d")
        for i, (n, dv, lo, hi) in enumerate([("malha", 0 if var == "e3" else 1, 0, 1), ("Kp", 2.0, 0, 100),
                                             ("Ki", 10.0, 0, 1000), ("Kd", 0.2, 0, 10)]):
            m.liga(n, scada(m, n, (6450, 7620 + i * 60), dv, lo, hi))
            m.liga(n, f"controlador_PID.{n}")
        m.liga("disparo", "controlador_PID.disparo")
        m.liga("u", "controlador_PID.u"); m.liga("F", "controlador_PID.F")
        probe(m, "u", (6850, 7640), "u")
        probe(m, "F_atuador", (6850, 7760), "F")
        m.area("Controlador PID (derivada na medicao) e atuador (forca = tensao)", (6620, 7700), (520, 380),
               "#0e6250d6")
        planta(m, 6900, 6900, "F")
    # caminho ideal
    m.liga("yreal", "y_real.out")
    probe(m, "x_real", (7560, 6860), "yreal")
    if var == "e2":
        scope(m, (7700, 6600), ["x_real", "v_massa", "r"])
        return m, 10.0
    m.comp("core/Gain", "caminho_ideal", (7700, 7000), {"gain": "1"})
    m.liga("yreal", "caminho_ideal.in")
    m.liga("yideal", "caminho_ideal.out")
    probe(m, "y_ideal", (7820, 6940), "yideal")
    m.area("Ponta de prova ideal e caminho ideal (ganho 1, sem atraso)", (7720, 6980), (300, 200), "#0e1baf7a")
    cadeia_real(m, 7400, 7900, "yreal", G=5)
    # seletor
    m.cfun("seletor_ideal_real", C_SELETOR, (8700, 7400))
    m.liga("ymed", "seletor_ideal_real.y_real_med"); m.liga("yideal", "seletor_ideal_real.y_ideal")
    m.liga("seletor", scada(m, "seletor", (8560, 7300), 0, 0, 1))
    m.liga("seletor", "seletor_ideal_real.seletor")
    m.liga("yctrl", "seletor_ideal_real.y_ctrl")
    probe(m, "y_ctrl", (8840, 7340), "yctrl")
    m.area("Seletor ideal / real (o que chega ao controlador)", (8720, 7400), (320, 220), "#0e898781")
    scada_cadeia(m, 6300, 8500, {})
    scope(m, (8900, 7000), ["r", "x_real", "y_med", "y_ctrl", "u"])
    return m, 10.0


# ======================================================================================
# Painel .cus
# ======================================================================================
def uid():
    return uuid.uuid1().hex


def _ws(x, y, w, h, label, use_label=True, bg=False):
    return f"""                <widget_settings>
                    <x>{x}</x>
                    <y>{y}</y>
                    <width>{w}</width>
                    <height>{h}</height>
                    <appearance><![CDATA[Flat]]></appearance>
                    <hierarchy_position><![CDATA[1]]></hierarchy_position>
                    <is_background><![CDATA[False]]></is_background>
                    <label><![CDATA[{label}]]></label>
                    <use_label>{use_label}</use_label>
                </widget_settings>
"""


def w_note(n, texto, x, y, w, h):
    return f"""        <component_data>
                <id>{uid()}</id>
                <name><![CDATA[{n}]]></name>
                <type>TextNote</type>
                <description><![CDATA[]]></description>
                <text><![CDATA[{texto}]]></text>
                <widget_settings>
                    <x>{x}</x>
                    <y>{y}</y>
                    <width>{w}</width>
                    <height>{h}</height>
                    <background_color><![CDATA[None]]></background_color>
                    <background_type><![CDATA[Transparent]]></background_type>
                    <appearance><![CDATA[Flat]]></appearance>
                    <hierarchy_position>1</hierarchy_position>
                    <label><![CDATA[]]></label>
                    <use_label>False</use_label>
                </widget_settings>
            </component_data>
"""


_STOP = """                <on_stop_code active="False"><![CDATA[widgetValue = None
]]></on_stop_code>
                <on_timer_code active="False"><![CDATA[widgetValue = None
]]></on_timer_code>
"""


def w_text(n, label, sig, default, x, y, w=300, h=52, disparar=False):
    use = f"hil.set_scada_input_value('{sig}', float(inputValue))\n" + ("disparar()\n" if disparar else "")
    start = f"widgetValue = {float(default)!r}\nhil.set_scada_input_value('{sig}', {float(default)!r})\n"
    return f"""        <component_data>
                <id>{uid()}</id>
                <name><![CDATA[{n}]]></name>
                <type>TextBoxMacro</type>
                <description><![CDATA[]]></description>
                <on_use_code active="True"><![CDATA[{use}]]></on_use_code>
                <on_start_code active="True"><![CDATA[{start}]]></on_start_code>
{_STOP}                <on_start_code_source><![CDATA[Custom code]]></on_start_code_source>
                <inputValue><![CDATA[{float(default)}]]></inputValue>
                <inputValueType>float</inputValueType>
                <unit><![CDATA[]]></unit>
                <widget_settings>
                    <x>{x}</x>
                    <y>{y}</y>
                    <width>{w}</width>
                    <height>{h}</height>
                    <inputWidgetWidth>80</inputWidgetWidth>
                    <appearance><![CDATA[Flat]]></appearance>
                    <hierarchy_position>1</hierarchy_position>
                    <label><![CDATA[{label}]]></label>
                    <use_label>True</use_label>
                </widget_settings>
            </component_data>
"""


def w_combo(n, label, sig, opcoes, valores, default_idx, x, y, w=300, h=52, disparar=False):
    use = (f"OPC = {opcoes!r}\nVAL = {valores!r}\n"
           f"hil.set_scada_input_value('{sig}', float(VAL[OPC.index(inputValue)]))\n"
           + ("disparar()\n" if disparar else ""))
    start = f"widgetValue = {opcoes[default_idx]!r}\nhil.set_scada_input_value('{sig}', {float(valores[default_idx])!r})\n"
    return f"""        <component_data>
                <id>{uid()}</id>
                <name><![CDATA[{n}]]></name>
                <type>ComboBoxMacro</type>
                <description><![CDATA[]]></description>
                <on_use_code active="True"><![CDATA[{use}]]></on_use_code>
                <on_start_code active="True"><![CDATA[{start}]]></on_start_code>
{_STOP}                <on_start_code_source><![CDATA[Custom code]]></on_start_code_source>
                <inputValue><![CDATA[0.0]]></inputValue>
                <availableValues><![CDATA[{opcoes!r}]]></availableValues>
                <unit><![CDATA[]]></unit>
                <autocomplete_enabled>False</autocomplete_enabled>
{_ws(x, y, w, h, label)}            </component_data>
"""


def w_button(n, label, code, x, y, w=300, h=40):
    return f"""        <component_data>
                <id>{uid()}</id>
                <name><![CDATA[{n}]]></name>
                <type>MacroButton</type>
                <description><![CDATA[]]></description>
                <on_use_code active="True"><![CDATA[{code}]]></on_use_code>
                <on_start_code active="False"><![CDATA[
]]></on_start_code>
                <on_stop_code active="False"><![CDATA[
]]></on_stop_code>
                <on_start_code_source><![CDATA[Custom code]]></on_start_code_source>
{_ws(x, y, w, h, label)}            </component_data>
"""


def w_digital(n, label, sig, unit, x, y, w=145, h=60, dec=3):
    return f"""        <component_data>
                <id>{uid()}</id>
                <name><![CDATA[{n}]]></name>
                <type>DigitalDisplay</type>
                <description><![CDATA[]]></description>
                <data_type>Analog signal</data_type>
                <code><![CDATA[displayValue = 0.0
]]></code>
                <signal_name><![CDATA[{sig}]]></signal_name>
                <unit><![CDATA[{unit}]]></unit>
                <automatic_unit>False</automatic_unit>
                <decimals><![CDATA[{dec}]]></decimals>
                <updateRate>250</updateRate>
                <scaling_factor>1.0</scaling_factor>
{_ws(x, y, w, h, label)}                <advance_widget_settings>
                    <color_range>False</color_range>
                    <green_range>(0, 0, 0, 0)</green_range>
                    <orange_range>(0, 0, 0, 0)</orange_range>
                    <red_range>(0, 0, 0, 0)</red_range>
                </advance_widget_settings>
            </component_data>
"""


def w_trace(n, label, sinais, ytitle, ymin, ymax, x, y, w, h, janela=8, auto=False):
    return f"""        <component_data>
                <id>{uid()}</id>
                <name><![CDATA[{n}]]></name>
                <type>TraceDisplay</type>
                <description><![CDATA[]]></description>
                <data_type>Signals</data_type>
                <code><![CDATA[data = {{"analog_names": [], "analog_values": [], "digital_names": [], "digital_values": []}}
displayValue = data
]]></code>
                <analog_signals><![CDATA[{sinais!r}]]></analog_signals>
                <digital_signals><![CDATA[[]]]></digital_signals>
                <streaming_analog_signals><![CDATA[[]]]></streaming_analog_signals>
                <streaming_digital_signals><![CDATA[[]]]></streaming_digital_signals>
                <analog_signals_scaling_factors><![CDATA[{{}}]]></analog_signals_scaling_factors>
                <streaming_analog_signals_scaling_factors><![CDATA[{{}}]]></streaming_analog_signals_scaling_factors>
                <update_rate>250</update_rate>
                <execution_rate>None</execution_rate>
                <background_color>white</background_color>
{_ws(x, y, w, h, label)}                <advance_widget_settings>
                    <x_title><![CDATA[t [s]]]></x_title>
                    <y_title><![CDATA[{ytitle}]]></y_title>
                    <y_range_min>{ymin}</y_range_min>
                    <y_range_max>{ymax}</y_range_max>
                    <time_window>{janela}</time_window>
                    <auto_scale_enabled>{auto}</auto_scale_enabled>
                    <legend_enabled>True</legend_enabled>
                    <x_axis_title_enabled>False</x_axis_title_enabled>
                    <y_axis_title_enabled>True</y_axis_title_enabled>
                    <use_reference_curve>False</use_reference_curve>
                    <reference_curve_code><![CDATA[referenceCurves = []
]]></reference_curve_code>
                </advance_widget_settings>
            </component_data>
"""


INIT_PANEL = """# Painel G02 (ECOM060, UFAL 2026.2) - funcoes comuns as macros
import time


def disparar():
    # borda de subida em 'disparo' zera o relogio do ensaio e os estados do PID
    hil.set_scada_input_value('disparo', 0.0)
    hil.set_scada_input_value('disparo', 1.0)
    time.sleep(0.1)
    hil.set_scada_input_value('disparo', 0.0)


def aplicar(valores):
    for nome, valor in valores.items():
        hil.set_scada_input_value(nome, float(valor))
    disparar()


IDEAL_CADEIA = dict(en_sens=0, en_lim=0, en_res=0, en_ruido=0, en_interf=0, chop=1, comp_cal=0, comp_din=0)
REAL_E02 = dict(en_sens=1, S_real_mVN=24.6, en_lim=1, en_res=1, en_ruido=1, sigma_mV=20, en_interf=1, chop=1,
                fc_Hz=1.0, comp_cal=0, comp_din=0)
"""

LIGA = (["desligado", "ligado"], [0, 1])


def painel(var):
    W = []
    X, CW = 16, 300
    y = 8
    titulos = {
        "f1e3": "G02 - Fase 1, Entrega 03: validacao funcional da cadeia piezo + lock-in (forca em N rms)",
        "e2": "G02 - Fase 2, Entrega 02: equivalente eletrico do massa-mola-amortecedor (1 V = 1 N = 1 cm)",
        "e3": "G02 - Fase 2, Entrega 03: medicao ideal x real em malha aberta (1 V = 1 N = 1 cm)",
        "final": "G02 - Entrega Final: instrumentacao nao ideal e seus efeitos no controle (1 V = 1 N = 1 cm)",
    }
    W.append(w_note("Titulo", titulos[var], X, y, 1560, 30)); y += 34
    if var == "f1e3":
        ens = ["(a) Degrau a partir do repouso", "(b) Condicao inicial nao nula (solta em t = 1 s)",
               "(c) Pulso breve (1,5 A por 0,5 s)"]
        W.append(w_combo("Ensaio", "Ensaio (R11)", "ensaio", ens, [1, 2, 3], 0, X, y + 10, disparar=True)); y += 70
        W.append(w_text("Amplitude", "Amplitude da forca A [N rms]", "amplitude", 0.6, X, y, disparar=True)); y += 58
    else:
        ens = ["(a) Degrau a partir do repouso", "(b) Condicao inicial nao nula", "(c) Pulso de 1,5 A por 0,5 s"]
        vals = [1, 2, 3]
        if var == "final":
            ens.append("(d) Perturbacao de forca 0,5 A"); vals.append(4)
        W.append(w_combo("Ensaio", "Ensaio (evento em t = 2 s)", "ensaio", ens, vals, 0, X, y + 10, disparar=True))
        y += 70
        W.append(w_text("Amplitude", "Amplitude A [cm em malha fechada | N em aberta]", "amplitude", 10.0, X, y,
                        disparar=True)); y += 58
    W.append(w_button("Disparar", "DISPARAR / REPETIR ENSAIO", "disparar()\n", X, y)); y += 50
    if var in ("e3", "final"):
        W.append(w_combo("Malha", "Malha", "malha", ["aberta (forca = A)", "fechada (PID)"], [0, 1],
                         0 if var == "e3" else 1, X, y, disparar=True)); y += 58
        W.append(w_combo("Seletor", "Seletor: leitura que vai ao controlador", "seletor",
                         ["ideal (ponta de prova)", "real (sensor + condicionamento)"], [0, 1], 0, X, y,
                         disparar=True)); y += 64
    if var == "final":
        W.append(w_note("Sec_cen", "CENARIOS PRONTOS (mesmo controlador, mesmo ensaio)", X, y, CW, 24)); y += 26
        cen = [("Cen1", "1) Instrumento IDEAL", "hil.set_scada_input_value('seletor', 0.0)\naplicar(dict(malha=1))\n"),
               ("Cen2", "2) Instrumento REAL (cadeia da E02)",
                "hil.set_scada_input_value('seletor', 1.0)\naplicar(dict(REAL_E02, malha=1))\n"),
               ("Cen3", "3) REAL + calibracao (x1,625)",
                "hil.set_scada_input_value('seletor', 1.0)\naplicar(dict(REAL_E02, malha=1, comp_cal=1, S_cal_mVN=24.6))\n"),
               ("Cen4", "4) REAL + calibracao + correcao do filtro",
                "hil.set_scada_input_value('seletor', 1.0)\naplicar(dict(REAL_E02, malha=1, comp_cal=1, S_cal_mVN=24.6, comp_din=1, fc_corr_Hz=1.0))\n")]
        for n, lab, code in cen:
            W.append(w_button(n, lab, code, X, y, h=36)); y += 40
    if var in ("e3", "final", "f1e3"):
        X2 = X + CW + 16
        y2 = 42
        W.append(w_note("Sec_car", "CARACTERISTICAS DO INSTRUMENTO REAL", X2, y2, CW, 24)); y2 += 26
        itens = [("chop", "Chopagem a 100 Hz", "combo", 1), ("en_sens", "Desvio de sensibilidade", "combo", 1),
                 ("S_real_mVN", "S real [mV/N] (nominal 40)", "text", 24.6),
                 ("en_lim", "Limiar (0,02 N)", "combo", 1), ("en_res", "Resolucao (0,01 N)", "combo", 1),
                 ("en_ruido", "Ruido branco", "combo", 1), ("sigma_mV", "sigma do ruido [mV]", "text", 20.0),
                 ("en_interf", "Offset + deriva + 60 Hz", "combo", 1),
                 ("fc_Hz", "fc do Butterworth do lock-in [Hz]", "text", 1.0)]
        if var != "f1e3":
            itens += [("comp_cal", "Calibracao de 1 ponto", "combo", 0),
                      ("S_cal_mVN", "S levantada na calibracao [mV/N]", "text", 24.6),
                      ("comp_din", "Correcao calculada do filtro", "combo", 0),
                      ("fc_corr_Hz", "fc assumido pelo corretor [Hz]", "text", 1.0),
                      ("f_f_Hz", "Polos rapidos do corretor [Hz]", "text", 10.0)]
        else:
            itens += [("comp_cal", "Calibracao de 1 ponto (x1,625)", "combo", 0),
                      ("S_cal_mVN", "S levantada na calibracao [mV/N]", "text", 24.6)]
        for sig, lab, tipo, dv in itens:
            if tipo == "combo":
                W.append(w_combo("w_" + sig, lab, sig, *LIGA, int(dv), X2, y2, h=50)); y2 += 54
            else:
                W.append(w_text("w_" + sig, lab, sig, dv, X2, y2, h=50)); y2 += 54
        if var == "final":
            W.append(w_note("Sec_pid", "CONTROLADOR PID", X, y + 6, CW, 24)); y += 32
            for sig, lab, dv in (("Kp", "Kp [N/cm]", 2.0), ("Ki", "Ki [N/(cm s)]", 10.0), ("Kd", "Kd [N s/cm]", 0.2)):
                W.append(w_text("w_" + sig, lab, sig, dv, X, y, h=46)); y += 50
        XG = X2 + CW + 16
    else:
        XG = X + CW + 16
    WG = 1580 - XG
    if var == "f1e3":
        W.append(w_trace("G1", "Forca: referencia ideal x medida (saida do lock-in, K = 1 V/N)", ["Videal", "y_med"],
                         "F [N rms]", -0.2, 1.4, XG, 42, WG, 380, janela=6))
        W.append(w_trace("G2", "Pre-amplificador (sinal modulado + ruido + interferencias)", ["pre_amp"], "V",
                         -3, 3, XG, 432, WG, 250, janela=6, auto=True))
        W.append(w_trace("G3", "Tensao sobre Rin (saida do piezo)", ["v_piezo"], "V", -0.1, 0.1, XG, 692, WG, 200,
                         janela=6, auto=True))
        W.append(w_digital("D1", "Forca ideal", "Videal", "N", X, y + 10))
        W.append(w_digital("D2", "Forca medida", "y_med", "N", X + 155, y + 10))
    elif var == "e2":
        W.append(w_trace("G1", "Deslocamento x [cm] = tensao no capacitor [V] = forca na mola [N]", ["x_real", "r"],
                         "x [cm]", -5, 20, XG, 42, WG, 470))
        W.append(w_trace("G2", "Velocidade [m/s] = corrente da malha [A]", ["v_massa"], "v [m/s]", -1.5, 1.5,
                         XG, 522, WG, 300))
        W.append(w_digital("D1", "Deslocamento x", "x_real", "cm", X, y + 10))
        W.append(w_digital("D2", "Velocidade", "v_massa", "m/s", X + 155, y + 10))
    else:
        W.append(w_trace("G1", "Referencia, grandeza REAL da planta e grandeza MEDIDA [cm]",
                         ["r", "x_real", "y_med", "y_ctrl"], "x [cm]", -5, 25, XG, 42, WG, 430))
        W.append(w_trace("G2", "Esforco do controlador u e forca no atuador [N]", ["u", "F_atuador"], "N", -65, 65,
                         XG, 482, WG, 230))
        W.append(w_trace("G3", "Dentro da cadeia: pre-amp, demodulado, saida do Butterworth [V]",
                         ["pre_amp", "demod", "bw"], "V", -10, 10, XG, 722, WG, 230, auto=True))
        yd = max(y, 0) + 10
        W.append(w_digital("D1", "x real", "x_real", "cm", X, yd))
        W.append(w_digital("D2", "x medido", "y_med", "cm", X + 155, yd))
        W.append(w_digital("D3", "esforco u", "u", "N", X, yd + 66))
        W.append(w_digital("D4", "tempo do ensaio", "t_ensaio", "s", X + 155, yd + 66, dec=2))
    init = INIT_PANEL
    out = ["<ui_settings>", "    <version>2.9</version>", "    <model_locked>False</model_locked>",
           "    <canvas_bg_color>#ffffff</canvas_bg_color>",
           f"    <initialization_code><![CDATA[{init}]]></initialization_code>", "    <components>"]
    out += W
    out += ["        </components>", "</ui_settings>"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    var, pasta = sys.argv[1], sys.argv[2]
    os.makedirs(pasta, exist_ok=True)
    m, tsim = montar(var)
    with open(os.path.join(pasta, "modelo.tse"), "w", encoding="utf-8", newline="\n") as f:
        f.write(m.texto(tsim))
    with open(os.path.join(pasta, "painel.cus"), "w", encoding="utf-8", newline="\n") as f:
        f.write(painel(var))
    print(var, "->", pasta, f"{len(m.comps)} componentes")
