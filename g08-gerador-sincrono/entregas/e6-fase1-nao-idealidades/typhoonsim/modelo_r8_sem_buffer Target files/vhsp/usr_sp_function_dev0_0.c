// generated using template: cop_main.template---------------------------------------------
/******************************************************************************************
**
**  Module Name: cop_main.c
**  NOTE: Automatically generated file. DO NOT MODIFY!
**  Description:
**            Main file
**
******************************************************************************************/
// generated using template: arm/custom_include.template-----------------------------------


#ifdef __cplusplus
#include <limits>

extern "C" {
#endif

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdint.h>
#include <complex.h>
#include <time.h>
#include <stdarg.h>

// x86 libraries:
#include "../include/sp_functions_dev0.h"


#ifdef __cplusplus
}
#endif



// ----------------------------------------------------------------------------------------                // generated using template:generic_macros.template-----------------------------------------
/*********************** Macros (Inline Functions) Definitions ***************************/

// ----------------------------------------------------------------------------------------

#ifndef MAX
#define MAX(value, limit) (((value) > (limit)) ? (value) : (limit))
#endif
#ifndef MIN
#define MIN(value, limit) (((value) < (limit)) ? (value) : (limit))
#endif

// generated using template: VirtualHIL/custom_defines.template----------------------------

typedef unsigned char X_UnInt8;
typedef char X_Int8;
typedef signed short X_Int16;
typedef unsigned short X_UnInt16;
typedef int X_Int32;
typedef unsigned int X_UnInt32;
typedef unsigned int uint;
typedef double real;

// ----------------------------------------------------------------------------------------
// generated using template: custom_consts.template----------------------------------------

// arithmetic constants
#define C_SQRT_2                    1.4142135623730950488016887242097f
#define C_SQRT_3                    1.7320508075688772935274463415059f
#define C_PI                        3.1415926535897932384626433832795f
#define C_E                         2.7182818284590452353602874713527f
#define C_2PI                       6.283185307179586476925286766559f

//@cmp.def.start
//component defines
















double  _ruido_branco_c_function__u1, _ruido_branco_c_function__u2, _ruido_branco_c_function__z0, _ruido_branco_c_function__u, _ruido_branco_c_function__u_exp;

























































//@cmp.def.end


//-----------------------------------------------------------------------------------------
// generated using template: common_variables.template-------------------------------------
// true global variables





// const variables
static const int _i_in_ia1__n_rd_as = 13107200;
static const unsigned int _i_in_ia1__p_addr = 5;
static const char* _i_in_ia1__p_sig_output = "True";

static const int _i_loop_ia1__n_rd_as = 13107200;
static const unsigned int _i_loop_ia1__p_addr = 6;
static const char* _i_loop_ia1__p_sig_output = "True";


static const real _r_c0__p_value = 110.0;


static const real _r_min__p_value = 10.0;


static const real _r_p__p_value = 10000.0;

static const int _v_cursor_va1__n_rd_as = 13107200;
static const unsigned int _v_cursor_va1__p_addr = 2;
static const char* _v_cursor_va1__p_sig_output = "True";

static const int _v_rl_va1__n_rd_as = 13107200;
static const unsigned int _v_rl_va1__p_addr = 3;
static const char* _v_rl_va1__p_sig_output = "True";

static const int _v_tx_va1__n_rd_as = 13107200;
static const unsigned int _v_tx_va1__p_addr = 4;
static const char* _v_tx_va1__p_sig_output = "True";


static const real _folga_b__p_value = 1.0;


static const real _folga_memoria__p_init_value = 0.0;


static const real _mov_memoria__p_init_value = 0.0;


static const unsigned char _relogio__p_enb_reset = 0;
static const real _relogio__p_execution_rate = 0.001;
static const real _relogio__p_reset_at = 1.0;


static const real _res_fase__p_value = 0.25;


static const real _res_liga__p_value = 1.0;


static const real _res_meio_menos_fase__p_value = 0.25;


static const real _ruido_liga__p_value = 1.0;

static const char* _a_para_ua__n_multiplication = "Element-wise(K.*u)";
static const real _a_para_ua__p_gain = 1000000.0;

static const char* _xtr115_x100__n_multiplication = "Element-wise(K.*u)";
static const real _xtr115_x100__p_gain = 100.0;

static const char* _a_para_ma__n_multiplication = "Element-wise(K.*u)";
static const real _a_para_ma__p_gain = 1000.0;

static const int _v_cursor_1__n_out_size = 1;
static const unsigned int _v_cursor_1__p_addr = 16396;

static const int _v_rl_v__n_out_size = 1;
static const unsigned int _v_rl_v__p_addr = 16387;

static const int _v_tx_v__n_out_size = 1;
static const unsigned int _v_tx_v__p_addr = 16388;

static const char* _kellet_direto__n_multiplication = "Element-wise(K.*u)";
static const real _kellet_direto__p_gain = 0.5362;

static const int _ruido_branco_n01__n_out_size = 1;
static const unsigned int _ruido_branco_n01__p_addr = 16391;

static const int _i_in_ua__n_out_size = 1;
static const unsigned int _i_in_ua__p_addr = 16384;

static const int _xtr115_io_is1__n_rd_ds = 16252928;
static const int _xtr115_io_is1__n_spc_baseaddr = 134217728;
static const int _xtr115_io_is1__n_spc_do_baseaddr = 1039;
static const int _xtr115_io_is1__n_spc_do_mem_width = 15;
static const int _xtr115_io_is1__n_spc_dt = 2621440;
static const int _xtr115_io_is1__n_spc_dt_sw_ctrl_val = 256;
static const int _xtr115_io_is1__n_spc_off = 4194304;
static const int _xtr115_io_is1__n_spc_sp = 2883584;
static const int _xtr115_io_is1__n_spc_tv = 3145728;
static const char* _xtr115_io_is1__n_val_of_type = "signal controlled";
static const unsigned int _xtr115_io_is1__p_addr = 0;
static const unsigned int _xtr115_io_is1__p_dtsm_nb = 0;
static const char* _xtr115_io_is1__p_enable_fb_out = "False";
static const unsigned int _xtr115_io_is1__p_spc_nb = 0;

static const int _i_loop_ma__n_out_size = 1;
static const unsigned int _i_loop_ma__p_addr = 16385;

static const int _folga_theta_mais_b__n_in_size = 1;
static const int _folga_theta_mais_b__n_num_of_inputs = 2;
static const unsigned char _folga_theta_mais_b__n_signs_bool[2] = {1, 1};


static const int _theta_ref__n_out_size = 1;
static const unsigned int _theta_ref__p_addr = 16394;

static const int _kellet_soma__n_in_size = 1;
static const int _kellet_soma__n_num_of_inputs = 8;
static const unsigned char _kellet_soma__n_signs_bool[8] = {1, 1, 1, 1, 1, 1, 1, 1};



static const char* _folga_min__p_operation = "min";

static const int _i_receptor_ma__n_out_size = 1;
static const unsigned int _i_receptor_ma__p_addr = 16386;

static const int _erro_fe_pc__n_out_size = 1;
static const unsigned int _erro_fe_pc__p_addr = 16390;

static const int _theta_med__n_out_size = 1;
static const unsigned int _theta_med__p_addr = 16393;

static const char* _ruido_k_enr__n_multiplication = "Element-wise(K.*u)";
static const real _ruido_k_enr__p_gain = 9.268124000249522;


static const char* _folga_max__p_operation = "max";

static const int _drc_ohm__n_out_size = 1;
static const unsigned int _drc_ohm__p_addr = 16389;

static const int _mov_desvio__n_in_size = 1;
static const int _mov_desvio__n_num_of_inputs = 2;
static const unsigned char _mov_desvio__n_signs_bool[2] = {1, 0};


static const char* _res_espiras_por_grau__n_multiplication = "Element-wise(K.*u)";
static const real _res_espiras_por_grau__p_gain = 1.3888888888888888;

static const int _theta_cursor__n_out_size = 1;
static const unsigned int _theta_cursor__p_addr = 16392;




static const int _res_soma_a__n_in_size = 1;
static const int _res_soma_a__n_num_of_inputs = 2;
static const unsigned char _res_soma_a__n_signs_bool[2] = {1, 1};






static const char* _res_espira__p_round_fn = "floor";

static const int _ruido_x_movimento__n_in_size = 1;
static const int _ruido_x_movimento__n_num_of_terminals = 2;
static const unsigned char _ruido_x_movimento__n_signs_bool[2] = {1, 1};


static const int _res_soma_fase__n_in_size = 1;
static const int _res_soma_fase__n_num_of_inputs = 2;
static const unsigned char _res_soma_fase__n_signs_bool[2] = {1, 1};


static const int _ruido_chave__n_in_size = 1;
static const int _ruido_chave__n_num_of_terminals = 2;
static const unsigned char _ruido_chave__n_signs_bool[2] = {1, 1};


static const char* _res_graus_por_espira__n_multiplication = "Element-wise(K.*u)";
static const real _res_graus_por_espira__p_gain = 0.72;

static const int _r_c_base_mais_ruido__n_in_size = 1;
static const int _r_c_base_mais_ruido__n_num_of_inputs = 2;
static const unsigned char _r_c_base_mais_ruido__n_signs_bool[2] = {1, 1};


static const int _res_desvio__n_in_size = 1;
static const int _res_desvio__n_num_of_inputs = 2;
static const unsigned char _res_desvio__n_signs_bool[2] = {1, 0};


static const int _r_contato_vs__n_spc_baseaddr = 134217728;
static const int _r_contato_vs__n_spc_off = 4194304;
static const int _r_contato_vs__n_spc_sp = 2883584;
static const int _r_contato_vs__n_spc_tv = 3145728;
static const char* _r_contato_vs__n_val_of_type = "tve";
static const unsigned int _r_contato_vs__p_addr = 0;
static const unsigned int _r_contato_vs__p_spc_nb = 0;

static const int _res_chave__n_in_size = 1;
static const int _res_chave__n_num_of_terminals = 2;
static const unsigned char _res_chave__n_signs_bool[2] = {1, 1};


static const int _res_saida__n_in_size = 1;
static const int _res_saida__n_num_of_inputs = 2;
static const unsigned char _res_saida__n_signs_bool[2] = {1, 1};


static const char* _r_inf_rp_x__n_multiplication = "Element-wise(K.*u)";
static const real _r_inf_rp_x__p_gain = 2.7777777777777777;

static const int _theta_resolucao__n_out_size = 1;
static const unsigned int _theta_resolucao__p_addr = 16395;


static const char* _r_inf_minimo__p_operation = "max";

static const int _r_sup_rp_menos__n_in_size = 1;
static const int _r_sup_rp_menos__n_num_of_inputs = 2;
static const unsigned char _r_sup_rp_menos__n_signs_bool[2] = {1, 0};



static const char* _r_inf_maximo__p_operation = "min";


static const char* _r_sup_minimo__p_operation = "max";

static const int _r_trilha_inf_vs__n_spc_baseaddr = 134217728;
static const int _r_trilha_inf_vs__n_spc_off = 4194304;
static const int _r_trilha_inf_vs__n_spc_sp = 2883584;
static const int _r_trilha_inf_vs__n_spc_tv = 3145728;
static const char* _r_trilha_inf_vs__n_val_of_type = "tve";
static const unsigned int _r_trilha_inf_vs__p_addr = 1;
static const unsigned int _r_trilha_inf_vs__p_spc_nb = 0;

static const int _r_trilha_sup_vs__n_spc_baseaddr = 134217728;
static const int _r_trilha_sup_vs__n_spc_off = 4194304;
static const int _r_trilha_sup_vs__n_spc_sp = 2883584;
static const int _r_trilha_sup_vs__n_spc_tv = 3145728;
static const char* _r_trilha_sup_vs__n_val_of_type = "tve";
static const unsigned int _r_trilha_sup_vs__p_addr = 2;
static const unsigned int _r_trilha_sup_vs__p_spc_nb = 0;


//@cmp.var.start
// variables
real _i_in_ia1__out;
real _i_loop_ia1__out;
static real _r_c0__out;
static real _r_min__out;
static real _r_p__out;
real _v_cursor_va1__out;
real _v_rl_va1__out;
real _v_tx_va1__out;
static real _folga_b__out;
static real _folga_memoria__out;
double _kellet_atraso__out;
double _kellet_atraso__b_coeff[1] = {0.115926};
double _kellet_atraso__a_coeff[2] = {1.0, 0.0};
double _kellet_atraso__a_sum;
double _kellet_atraso__b_sum;
double _kellet_atraso__delay_line_in;
static real _mov_memoria__out;
static real _relogio__out;
static real _res_fase__out;
static real _res_liga__out;
static real _res_meio_menos_fase__out;

double _ruido_branco_c_function__out;

static real _ruido_liga__out;
static real _a_para_ua__out;
static real _xtr115_x100__out;
static real _a_para_ma__out;









double _referencia__t;

double _referencia__theta_ref;

static real _kellet_direto__out;
double _kellet_polo0__out;
double _kellet_polo0__b_coeff[2] = {0.0555179, 0.0};
double _kellet_polo0__a_coeff[2] = {1.0, -0.99886};
double _kellet_polo0__a_sum;
double _kellet_polo0__b_sum;
double _kellet_polo0__delay_line_in;
double _kellet_polo1__out;
double _kellet_polo1__b_coeff[2] = {0.0750759, 0.0};
double _kellet_polo1__a_coeff[2] = {1.0, -0.99332};
double _kellet_polo1__a_sum;
double _kellet_polo1__b_sum;
double _kellet_polo1__delay_line_in;
double _kellet_polo2__out;
double _kellet_polo2__b_coeff[2] = {0.153852, 0.0};
double _kellet_polo2__a_coeff[2] = {1.0, -0.969};
double _kellet_polo2__a_sum;
double _kellet_polo2__b_sum;
double _kellet_polo2__delay_line_in;
double _kellet_polo3__out;
double _kellet_polo3__b_coeff[2] = {0.3104856, 0.0};
double _kellet_polo3__a_coeff[2] = {1.0, -0.8665};
double _kellet_polo3__a_sum;
double _kellet_polo3__b_sum;
double _kellet_polo3__delay_line_in;
double _kellet_polo4__out;
double _kellet_polo4__b_coeff[2] = {0.5329522, 0.0};
double _kellet_polo4__a_coeff[2] = {1.0, -0.55};
double _kellet_polo4__a_sum;
double _kellet_polo4__b_sum;
double _kellet_polo4__delay_line_in;
double _kellet_polo5__out;
double _kellet_polo5__b_coeff[2] = {-0.016898, 0.0};
double _kellet_polo5__a_coeff[2] = {1.0, 0.7616};
double _kellet_polo5__a_sum;
double _kellet_polo5__b_sum;
double _kellet_polo5__delay_line_in;









static real _folga_theta_mais_b__out;
double _receptor__theta_ref;
double _receptor__v_rl;

double _receptor__erro_FE;
double _receptor__i_mA;
double _receptor__theta_med;




static real _kellet_soma__out;
static real _folga_min__out;









static real _ruido_k_enr__out;
static real _folga_max__out;



static real _mov_desvio__out;
static real _res_espiras_por_grau__out;



static real _mov_abs__out;
static real _res_soma_a__out;
static real _mov_cursor_movendo__out;
static real _res_espira__out;
static real _ruido_x_movimento__out;
static real _res_soma_fase__out;
static real _ruido_chave__out;
static real _res_graus_por_espira__out;
static real _r_c_base_mais_ruido__out;
static real _res_desvio__out;

static real _res_chave__out;
static real _res_saida__out;
static real _r_inf_rp_x__out;



static real _r_inf_minimo__out;
static real _r_sup_rp_menos__out;
static real _r_inf_maximo__out;
static real _r_sup_minimo__out;


//@cmp.var.end

//@cmp.svar.start
// state variables



























real _folga_memoria__state;


double _kellet_atraso__states[1];
real _mov_memoria__state;


real _relogio__state;



































double _referencia__THETA_FS;

double _referencia__T_MEIO;







double _kellet_polo0__states[1];
double _kellet_polo1__states[1];
double _kellet_polo2__states[1];
double _kellet_polo3__states[1];
double _kellet_polo4__states[1];
double _kellet_polo5__states[1];















double _receptor__THETA_FS;

double _receptor__R_L;







































































































//@cmp.svar.end

// IO shared variables

//
// Tunable parameters
//
static struct Tunable_params {
} __attribute__((__packed__)) tunable_params;

void *tunable_params_dev0_cpu0_ptr = &tunable_params;

// Dll function pointers
#if defined(_WIN64)
#else
// Define handles for loading dlls
#endif





// generated using template: \templates\virtual_hil\fmi_custom_logger_fncs.template---------------------------------
#include <stdarg.h>



//
// DMA buffers
//













































































































































































































































































// generated using template: virtual_hil/custom_functions.template---------------------------------
void ReInit_user_sp_cpu0_dev0() {
#if DEBUG_MODE
    printf("\n\rReInitTimer");
#endif
    //@cmp.init.block.start
    {
        _folga_memoria__state = _folga_memoria__p_init_value;
    }
    X_UnInt32 _kellet_atraso__i;
    for (_kellet_atraso__i = 0; _kellet_atraso__i < 1; _kellet_atraso__i++) {
        _kellet_atraso__states[_kellet_atraso__i] = 0;
    }
    {
        _mov_memoria__state = _mov_memoria__p_init_value;
    }
    {
        _relogio__state = 0;
    }
    {
    }
    {
        HIL_OutAO(0x400c, 0);
    }
    {
        HIL_OutAO(0x4003, 0);
    }
    {
        HIL_OutAO(0x4004, 0);
    }
    {
        _referencia__THETA_FS = 3600.0 ;
        _referencia__T_MEIO = 10.0000 ;
    }
    X_UnInt32 _kellet_polo0__i;
    for (_kellet_polo0__i = 0; _kellet_polo0__i < 1; _kellet_polo0__i++) {
        _kellet_polo0__states[_kellet_polo0__i] = 0;
    }
    X_UnInt32 _kellet_polo1__i;
    for (_kellet_polo1__i = 0; _kellet_polo1__i < 1; _kellet_polo1__i++) {
        _kellet_polo1__states[_kellet_polo1__i] = 0;
    }
    X_UnInt32 _kellet_polo2__i;
    for (_kellet_polo2__i = 0; _kellet_polo2__i < 1; _kellet_polo2__i++) {
        _kellet_polo2__states[_kellet_polo2__i] = 0;
    }
    X_UnInt32 _kellet_polo3__i;
    for (_kellet_polo3__i = 0; _kellet_polo3__i < 1; _kellet_polo3__i++) {
        _kellet_polo3__states[_kellet_polo3__i] = 0;
    }
    X_UnInt32 _kellet_polo4__i;
    for (_kellet_polo4__i = 0; _kellet_polo4__i < 1; _kellet_polo4__i++) {
        _kellet_polo4__states[_kellet_polo4__i] = 0;
    }
    X_UnInt32 _kellet_polo5__i;
    for (_kellet_polo5__i = 0; _kellet_polo5__i < 1; _kellet_polo5__i++) {
        _kellet_polo5__states[_kellet_polo5__i] = 0;
    }
    {
        HIL_OutAO(0x4007, 0);
    }
    {
        HIL_OutAO(0x4000, 0);
    }
    {
        HIL_OutFloat(0x82c0000, 0.0);
    }
    {
        HIL_OutAO(0x4001, 0);
    }
    {
        _receptor__THETA_FS = 3600.0 ;
        _receptor__R_L = 250.000 ;
    }
    {
        HIL_OutAO(0x400a, 0);
    }
    {
        HIL_OutAO(0x4002, 0);
    }
    {
        HIL_OutAO(0x4006, 0);
    }
    {
        HIL_OutAO(0x4009, 0);
    }
    {
        HIL_OutAO(0x4005, 0);
    }
    {
        HIL_OutAO(0x4008, 0);
    }
    {
        HIL_OutFloat(0x8300000, 0.0);
    }
    {
        HIL_OutAO(0x400b, 0);
    }
    {
        HIL_OutFloat(0x8300001, 0.0);
    }
    {
        HIL_OutFloat(0x8300002, 0.0);
    }
    //@cmp.init.block.end
}


// Dll function pointers and dll reload function
#if defined(_WIN64)
// Define method for reloading dll functions
void ReloadDllFunctions_user_sp_cpu0_dev0(void) {
    // Load each library and setup function pointers
}

void FreeDllFunctions_user_sp_cpu0_dev0(void) {
}

#else
// Define method for reloading dll functions
void ReloadDllFunctions_user_sp_cpu0_dev0(void) {
    // Load each library and setup function pointers
}

void FreeDllFunctions_user_sp_cpu0_dev0(void) {
}
#endif

void load_fmi_libraries_user_sp_cpu0_dev0(void) {
#if defined(_WIN64)
#else
#endif
}


void ReInit_sp_scope_user_sp_cpu0_dev0() {
    // initialise SP Scope buffer pointer
}


// generated using template: virtual_hil/common_timer_counter_handler.template-------------------------

/*****************************************************************************************/
/**
* This function is the handler which performs processing for the timer counter.
* It is called from an interrupt context such that the amount of processing
* performed should be minimized.  It is called when the timer counter expires
* if interrupts are enabled.
*
*
* @param    None
*
* @return   None
*
* @note     None
*
*****************************************************************************************/

void TimerCounterHandler_0_user_sp_cpu0_dev0() {
#if DEBUG_MODE
    printf("\n\rTimerCounterHandler_0");
#endif
    //////////////////////////////////////////////////////////////////////////
    // Output block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.out.block.start
    // Generated from the component: I_IN.Ia1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80005);
        _i_in_ia1__out = tac_tmp1;
    }
    // Generated from the component: I_LOOP.Ia1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80006);
        _i_loop_ia1__out = tac_tmp1;
    }
    // Generated from the component: R_C0
    {
        _r_c0__out = _r_c0__p_value;
    }
    // Generated from the component: R_min
    {
        _r_min__out = _r_min__p_value;
    }
    // Generated from the component: R_p
    {
        _r_p__out = _r_p__p_value;
    }
    // Generated from the component: V_CURSOR.Va1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80002);
        _v_cursor_va1__out = tac_tmp1;
    }
    // Generated from the component: V_RL.Va1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80003);
        _v_rl_va1__out = tac_tmp1;
    }
    // Generated from the component: V_TX.Va1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80004);
        _v_tx_va1__out = tac_tmp1;
    }
    // Generated from the component: folga_b
    {
        _folga_b__out = _folga_b__p_value;
    }
    // Generated from the component: folga_memoria
    {
        _folga_memoria__out = _folga_memoria__state;
    }
    // Generated from the component: kellet_atraso
    X_UnInt32 _kellet_atraso__i;
    _kellet_atraso__a_sum = 0.0f;
    _kellet_atraso__b_sum = 0.0f;
    _kellet_atraso__delay_line_in = 0.0f;
    for (_kellet_atraso__i = 0; _kellet_atraso__i < 1; _kellet_atraso__i++) {
        _kellet_atraso__b_sum += _kellet_atraso__b_coeff[_kellet_atraso__i] * _kellet_atraso__states[_kellet_atraso__i + 0];
    }
    _kellet_atraso__out = _kellet_atraso__b_sum;
    // Generated from the component: mov_memoria
    {
        _mov_memoria__out = _mov_memoria__state;
    }
    // Generated from the component: relogio
    {
        _relogio__out = _relogio__state;
    }
    // Generated from the component: res_fase
    {
        _res_fase__out = _res_fase__p_value;
    }
    // Generated from the component: res_liga
    {
        _res_liga__out = _res_liga__p_value;
    }
    // Generated from the component: res_meio_menos_fase
    {
        _res_meio_menos_fase__out = _res_meio_menos_fase__p_value;
    }
    // Generated from the component: ruido_branco.C function
    {
        switch ( 2 )     {
        case 1 :
            _ruido_branco_c_function__out = 0.0 + ( 5.0 - 0.0 ) * ( ( rand (  ) + 1.0 ) / ( RAND_MAX + 1.0 ) ) ;
            break;
        case 2 :
            _ruido_branco_c_function__u1 = ( rand (  ) + 1.0 ) / ( RAND_MAX + 1.0 ) ;
            _ruido_branco_c_function__u2 = ( rand (  ) + 1.0 ) / ( RAND_MAX + 1.0 ) ;
            _ruido_branco_c_function__z0 = sqrt ( - 2.0 * log ( _ruido_branco_c_function__u1 ) ) * cos ( 2.0 * M_PI * _ruido_branco_c_function__u2 ) ;
            _ruido_branco_c_function__out = 0.0 + 1.0 * _ruido_branco_c_function__z0 ;
            break;
        case 3 :
            _ruido_branco_c_function__u = rand (  ) / ( RAND_MAX + 1.0 ) ;
            _ruido_branco_c_function__out = 2.0 * pow ( - log ( 1.0 - _ruido_branco_c_function__u ), 1.0 / 1.0 ) ;
            break;
        case 4 :
            _ruido_branco_c_function__u_exp = rand (  ) / ( RAND_MAX + 1.0 ) ;
            _ruido_branco_c_function__out = - log ( 1.0 - _ruido_branco_c_function__u_exp ) / 1.0 ;
            break;
        default :
            printf ( "Invalid distribution type\n" ) ;
            break;
        }
    }
    // Generated from the component: ruido_liga
    {
        _ruido_liga__out = _ruido_liga__p_value;
    }
    // Generated from the component: A_para_uA
    {
        _a_para_ua__out = (_a_para_ua__p_gain * _i_in_ia1__out);
    }
    // Generated from the component: XTR115_x100
    {
        _xtr115_x100__out = (_xtr115_x100__p_gain * _i_in_ia1__out);
    }
    // Generated from the component: A_para_mA
    {
        _a_para_ma__out = (_a_para_ma__p_gain * _i_loop_ia1__out);
    }
    // Generated from the component: v_cursor
    {
        HIL_OutAO(0x400c, _v_cursor_va1__out);
    }
    // Generated from the component: V_RL_V
    {
        HIL_OutAO(0x4003, _v_rl_va1__out);
    }
    // Generated from the component: V_TX_V
    {
        HIL_OutAO(0x4004, _v_tx_va1__out);
    }
    // Generated from the component: referencia
    _referencia__t = _relogio__out;
    {
        if ( _referencia__t <= _referencia__T_MEIO )     {
            _referencia__theta_ref = _referencia__THETA_FS * _referencia__t / _referencia__T_MEIO ;
        }
        else     {
            _referencia__theta_ref = _referencia__THETA_FS * ( 2.0 * _referencia__T_MEIO - _referencia__t ) / _referencia__T_MEIO ;
        }
        if ( _referencia__theta_ref < 0.0 ) _referencia__theta_ref = 0.0 ;
        if ( _referencia__theta_ref > _referencia__THETA_FS ) _referencia__theta_ref = _referencia__THETA_FS ;
    }
    // Generated from the component: kellet_direto
    {
        _kellet_direto__out = (_kellet_direto__p_gain * _ruido_branco_c_function__out);
    }
    // Generated from the component: kellet_polo0
    X_UnInt32 _kellet_polo0__i;
    _kellet_polo0__a_sum = 0.0f;
    _kellet_polo0__b_sum = 0.0f;
    _kellet_polo0__delay_line_in = 0.0f;
    for (_kellet_polo0__i = 0; _kellet_polo0__i < 1; _kellet_polo0__i++) {
        _kellet_polo0__b_sum += _kellet_polo0__b_coeff[_kellet_polo0__i + 1] * _kellet_polo0__states[_kellet_polo0__i];
    }
    _kellet_polo0__a_sum += _kellet_polo0__states[0] * _kellet_polo0__a_coeff[1];
    _kellet_polo0__delay_line_in = _ruido_branco_c_function__out - _kellet_polo0__a_sum;
    _kellet_polo0__b_sum += _kellet_polo0__b_coeff[0] * _kellet_polo0__delay_line_in;
    _kellet_polo0__out = _kellet_polo0__b_sum;
    // Generated from the component: kellet_polo1
    X_UnInt32 _kellet_polo1__i;
    _kellet_polo1__a_sum = 0.0f;
    _kellet_polo1__b_sum = 0.0f;
    _kellet_polo1__delay_line_in = 0.0f;
    for (_kellet_polo1__i = 0; _kellet_polo1__i < 1; _kellet_polo1__i++) {
        _kellet_polo1__b_sum += _kellet_polo1__b_coeff[_kellet_polo1__i + 1] * _kellet_polo1__states[_kellet_polo1__i];
    }
    _kellet_polo1__a_sum += _kellet_polo1__states[0] * _kellet_polo1__a_coeff[1];
    _kellet_polo1__delay_line_in = _ruido_branco_c_function__out - _kellet_polo1__a_sum;
    _kellet_polo1__b_sum += _kellet_polo1__b_coeff[0] * _kellet_polo1__delay_line_in;
    _kellet_polo1__out = _kellet_polo1__b_sum;
    // Generated from the component: kellet_polo2
    X_UnInt32 _kellet_polo2__i;
    _kellet_polo2__a_sum = 0.0f;
    _kellet_polo2__b_sum = 0.0f;
    _kellet_polo2__delay_line_in = 0.0f;
    for (_kellet_polo2__i = 0; _kellet_polo2__i < 1; _kellet_polo2__i++) {
        _kellet_polo2__b_sum += _kellet_polo2__b_coeff[_kellet_polo2__i + 1] * _kellet_polo2__states[_kellet_polo2__i];
    }
    _kellet_polo2__a_sum += _kellet_polo2__states[0] * _kellet_polo2__a_coeff[1];
    _kellet_polo2__delay_line_in = _ruido_branco_c_function__out - _kellet_polo2__a_sum;
    _kellet_polo2__b_sum += _kellet_polo2__b_coeff[0] * _kellet_polo2__delay_line_in;
    _kellet_polo2__out = _kellet_polo2__b_sum;
    // Generated from the component: kellet_polo3
    X_UnInt32 _kellet_polo3__i;
    _kellet_polo3__a_sum = 0.0f;
    _kellet_polo3__b_sum = 0.0f;
    _kellet_polo3__delay_line_in = 0.0f;
    for (_kellet_polo3__i = 0; _kellet_polo3__i < 1; _kellet_polo3__i++) {
        _kellet_polo3__b_sum += _kellet_polo3__b_coeff[_kellet_polo3__i + 1] * _kellet_polo3__states[_kellet_polo3__i];
    }
    _kellet_polo3__a_sum += _kellet_polo3__states[0] * _kellet_polo3__a_coeff[1];
    _kellet_polo3__delay_line_in = _ruido_branco_c_function__out - _kellet_polo3__a_sum;
    _kellet_polo3__b_sum += _kellet_polo3__b_coeff[0] * _kellet_polo3__delay_line_in;
    _kellet_polo3__out = _kellet_polo3__b_sum;
    // Generated from the component: kellet_polo4
    X_UnInt32 _kellet_polo4__i;
    _kellet_polo4__a_sum = 0.0f;
    _kellet_polo4__b_sum = 0.0f;
    _kellet_polo4__delay_line_in = 0.0f;
    for (_kellet_polo4__i = 0; _kellet_polo4__i < 1; _kellet_polo4__i++) {
        _kellet_polo4__b_sum += _kellet_polo4__b_coeff[_kellet_polo4__i + 1] * _kellet_polo4__states[_kellet_polo4__i];
    }
    _kellet_polo4__a_sum += _kellet_polo4__states[0] * _kellet_polo4__a_coeff[1];
    _kellet_polo4__delay_line_in = _ruido_branco_c_function__out - _kellet_polo4__a_sum;
    _kellet_polo4__b_sum += _kellet_polo4__b_coeff[0] * _kellet_polo4__delay_line_in;
    _kellet_polo4__out = _kellet_polo4__b_sum;
    // Generated from the component: kellet_polo5
    X_UnInt32 _kellet_polo5__i;
    _kellet_polo5__a_sum = 0.0f;
    _kellet_polo5__b_sum = 0.0f;
    _kellet_polo5__delay_line_in = 0.0f;
    for (_kellet_polo5__i = 0; _kellet_polo5__i < 1; _kellet_polo5__i++) {
        _kellet_polo5__b_sum += _kellet_polo5__b_coeff[_kellet_polo5__i + 1] * _kellet_polo5__states[_kellet_polo5__i];
    }
    _kellet_polo5__a_sum += _kellet_polo5__states[0] * _kellet_polo5__a_coeff[1];
    _kellet_polo5__delay_line_in = _ruido_branco_c_function__out - _kellet_polo5__a_sum;
    _kellet_polo5__b_sum += _kellet_polo5__b_coeff[0] * _kellet_polo5__delay_line_in;
    _kellet_polo5__out = _kellet_polo5__b_sum;
    // Generated from the component: ruido_branco_N01
    {
        HIL_OutAO(0x4007, _ruido_branco_c_function__out);
    }
    // Generated from the component: I_IN_uA
    {
        HIL_OutAO(0x4000, _a_para_ua__out);
    }
    // Generated from the component: XTR115_Io.Is1
    {
        {
            HIL_OutFloat(0x82c0000, _xtr115_x100__out);
        }
    }
    // Generated from the component: I_LOOP_mA
    {
        HIL_OutAO(0x4001, _a_para_ma__out);
    }
    // Generated from the component: folga_theta_mais_b
    {
        _folga_theta_mais_b__out = 0;
        _folga_theta_mais_b__out += _referencia__theta_ref;
        _folga_theta_mais_b__out += _folga_b__out;
    }
    // Generated from the component: receptor
    _receptor__theta_ref = _referencia__theta_ref;
    _receptor__v_rl = _v_rl_va1__out;
    {
        _receptor__i_mA = 1000.0 * _receptor__v_rl / _receptor__R_L ;
        _receptor__theta_med = _receptor__THETA_FS * ( _receptor__i_mA - 4.0 ) / 16.0 ;
        _receptor__erro_FE = 100.0 * ( _receptor__i_mA - ( 4.0 + 16.0 * _receptor__theta_ref / _receptor__THETA_FS ) ) / 16.0 ;
    }
    // Generated from the component: theta_ref
    {
        HIL_OutAO(0x400a, _referencia__theta_ref);
    }
    // Generated from the component: kellet_soma
    {
        _kellet_soma__out = 0;
        _kellet_soma__out += _kellet_polo0__out;
        _kellet_soma__out += _kellet_polo1__out;
        _kellet_soma__out += _kellet_polo2__out;
        _kellet_soma__out += _kellet_polo3__out;
        _kellet_soma__out += _kellet_polo4__out;
        _kellet_soma__out += _kellet_polo5__out;
        _kellet_soma__out += _kellet_atraso__out;
        _kellet_soma__out += _kellet_direto__out;
    }
    // Generated from the component: folga_min
    {
        real _folga_min__t_in[2];
        _folga_min__t_in[0] = _folga_theta_mais_b__out;
        _folga_min__t_in[1] = _folga_memoria__out;
        real inputs[2];
        int t_tmp1;
        for(t_tmp1 = 0; t_tmp1 < 2; t_tmp1++) {
            inputs[t_tmp1] = _folga_min__t_in[t_tmp1];
        }
        if((1)) {
            /*min begin*/
            real tac_tmp1;
            tac_tmp1 = inputs[0];
            int h_tmp1;
            for(h_tmp1 = 1; h_tmp1 < 2; h_tmp1++) {
                if(!(inputs[h_tmp1] >= tac_tmp1)) {
                    tac_tmp1 = inputs[h_tmp1];
                }
            }
            /*min end*/
            _folga_min__out = tac_tmp1;
        }
        else {
            /*max begin*/
            real tac_tmp2;
            tac_tmp2 = inputs[0];
            int h_tmp2;
            for(h_tmp2 = 1; h_tmp2 < 2; h_tmp2++) {
                if(!(inputs[h_tmp2] <= tac_tmp2)) {
                    tac_tmp2 = inputs[h_tmp2];
                }
            }
            /*max end*/
            _folga_min__out = tac_tmp2;
        }
    }
    // Generated from the component: I_receptor_mA
    {
        HIL_OutAO(0x4002, _receptor__i_mA);
    }
    // Generated from the component: erro_FE_pc
    {
        HIL_OutAO(0x4006, _receptor__erro_FE);
    }
    // Generated from the component: theta_med
    {
        HIL_OutAO(0x4009, _receptor__theta_med);
    }
    // Generated from the component: ruido_K_ENR
    {
        _ruido_k_enr__out = (_ruido_k_enr__p_gain * _kellet_soma__out);
    }
    // Generated from the component: folga_max
    {
        real _folga_max__t_in[2];
        _folga_max__t_in[0] = _referencia__theta_ref;
        _folga_max__t_in[1] = _folga_min__out;
        real inputs[2];
        int t_tmp1;
        for(t_tmp1 = 0; t_tmp1 < 2; t_tmp1++) {
            inputs[t_tmp1] = _folga_max__t_in[t_tmp1];
        }
        if((0)) {
            /*min begin*/
            real tac_tmp1;
            tac_tmp1 = inputs[0];
            int h_tmp1;
            for(h_tmp1 = 1; h_tmp1 < 2; h_tmp1++) {
                if(!(inputs[h_tmp1] >= tac_tmp1)) {
                    tac_tmp1 = inputs[h_tmp1];
                }
            }
            /*min end*/
            _folga_max__out = tac_tmp1;
        }
        else {
            /*max begin*/
            real tac_tmp2;
            tac_tmp2 = inputs[0];
            int h_tmp2;
            for(h_tmp2 = 1; h_tmp2 < 2; h_tmp2++) {
                if(!(inputs[h_tmp2] <= tac_tmp2)) {
                    tac_tmp2 = inputs[h_tmp2];
                }
            }
            /*max end*/
            _folga_max__out = tac_tmp2;
        }
    }
    // Generated from the component: dRc_ohm
    {
        HIL_OutAO(0x4005, _ruido_k_enr__out);
    }
    // Generated from the component: mov_desvio
    {
        _mov_desvio__out = 0;
        _mov_desvio__out += _folga_max__out;
        _mov_desvio__out -= _mov_memoria__out;
    }
    // Generated from the component: res_espiras_por_grau
    {
        _res_espiras_por_grau__out = (_res_espiras_por_grau__p_gain * _folga_max__out);
    }
    // Generated from the component: theta_cursor
    {
        HIL_OutAO(0x4008, _folga_max__out);
    }
    // Generated from the component: mov_abs
    {
        _mov_abs__out = fabs(_mov_desvio__out);
    }
    // Generated from the component: res_soma_a
    {
        _res_soma_a__out = 0;
        _res_soma_a__out += _res_espiras_por_grau__out;
        _res_soma_a__out += _res_meio_menos_fase__out;
    }
    // Generated from the component: mov_cursor_movendo
    {
        real tac_tmp1;
        tac_tmp1 = (_mov_abs__out < 0 ? -1 : (_mov_abs__out > 0 ? 1 : 0));
        real tac_tmp2;
        tac_tmp2 = ((real) tac_tmp1);
        _mov_cursor_movendo__out = tac_tmp2;
    }
    // Generated from the component: res_espira
    {
        if((1)) {
            _res_espira__out = floor(_res_soma_a__out);
        }
        else {
            if((0)) {
                _res_espira__out = ceil(_res_soma_a__out);
            }
            else {
                if((0)) {
                    _res_espira__out = round(_res_soma_a__out);
                }
                else {
                    if((0)) {
                        _res_espira__out = trunc(_res_soma_a__out);
                    }
                    else {
                        _res_espira__out = 0;
                    }
                }
            }
        }
    }
    // Generated from the component: ruido_x_movimento
    {
        _ruido_x_movimento__out = 1;
        _ruido_x_movimento__out *= _ruido_k_enr__out;
        _ruido_x_movimento__out *= _mov_cursor_movendo__out;
    }
    // Generated from the component: res_soma_fase
    {
        _res_soma_fase__out = 0;
        _res_soma_fase__out += _res_espira__out;
        _res_soma_fase__out += _res_fase__out;
    }
    // Generated from the component: ruido_chave
    {
        _ruido_chave__out = 1;
        _ruido_chave__out *= _ruido_x_movimento__out;
        _ruido_chave__out *= _ruido_liga__out;
    }
    // Generated from the component: res_graus_por_espira
    {
        _res_graus_por_espira__out = (_res_graus_por_espira__p_gain * _res_soma_fase__out);
    }
    // Generated from the component: R_c_base_mais_ruido
    {
        _r_c_base_mais_ruido__out = 0;
        _r_c_base_mais_ruido__out += _r_c0__out;
        _r_c_base_mais_ruido__out += _ruido_chave__out;
    }
    // Generated from the component: res_desvio
    {
        _res_desvio__out = 0;
        _res_desvio__out += _res_graus_por_espira__out;
        _res_desvio__out -= _folga_max__out;
    }
    // Generated from the component: R_contato.Vs
    {
        HIL_OutFloat(0x8300000, _r_c_base_mais_ruido__out);
    }
    // Generated from the component: res_chave
    {
        _res_chave__out = 1;
        _res_chave__out *= _res_desvio__out;
        _res_chave__out *= _res_liga__out;
    }
    // Generated from the component: res_saida
    {
        _res_saida__out = 0;
        _res_saida__out += _folga_max__out;
        _res_saida__out += _res_chave__out;
    }
    // Generated from the component: R_inf_Rp_x
    {
        _r_inf_rp_x__out = (_r_inf_rp_x__p_gain * _res_saida__out);
    }
    // Generated from the component: theta_resolucao
    {
        HIL_OutAO(0x400b, _res_saida__out);
    }
    // Generated from the component: R_inf_minimo
    {
        real _r_inf_minimo__t_in[2];
        _r_inf_minimo__t_in[0] = _r_inf_rp_x__out;
        _r_inf_minimo__t_in[1] = _r_min__out;
        real inputs[2];
        int t_tmp1;
        for(t_tmp1 = 0; t_tmp1 < 2; t_tmp1++) {
            inputs[t_tmp1] = _r_inf_minimo__t_in[t_tmp1];
        }
        if((0)) {
            /*min begin*/
            real tac_tmp1;
            tac_tmp1 = inputs[0];
            int h_tmp1;
            for(h_tmp1 = 1; h_tmp1 < 2; h_tmp1++) {
                if(!(inputs[h_tmp1] >= tac_tmp1)) {
                    tac_tmp1 = inputs[h_tmp1];
                }
            }
            /*min end*/
            _r_inf_minimo__out = tac_tmp1;
        }
        else {
            /*max begin*/
            real tac_tmp2;
            tac_tmp2 = inputs[0];
            int h_tmp2;
            for(h_tmp2 = 1; h_tmp2 < 2; h_tmp2++) {
                if(!(inputs[h_tmp2] <= tac_tmp2)) {
                    tac_tmp2 = inputs[h_tmp2];
                }
            }
            /*max end*/
            _r_inf_minimo__out = tac_tmp2;
        }
    }
    // Generated from the component: R_sup_Rp_menos
    {
        _r_sup_rp_menos__out = 0;
        _r_sup_rp_menos__out += _r_p__out;
        _r_sup_rp_menos__out -= _r_inf_rp_x__out;
    }
    // Generated from the component: R_inf_maximo
    {
        real _r_inf_maximo__t_in[2];
        _r_inf_maximo__t_in[0] = _r_inf_minimo__out;
        _r_inf_maximo__t_in[1] = _r_p__out;
        real inputs[2];
        int t_tmp1;
        for(t_tmp1 = 0; t_tmp1 < 2; t_tmp1++) {
            inputs[t_tmp1] = _r_inf_maximo__t_in[t_tmp1];
        }
        if((1)) {
            /*min begin*/
            real tac_tmp1;
            tac_tmp1 = inputs[0];
            int h_tmp1;
            for(h_tmp1 = 1; h_tmp1 < 2; h_tmp1++) {
                if(!(inputs[h_tmp1] >= tac_tmp1)) {
                    tac_tmp1 = inputs[h_tmp1];
                }
            }
            /*min end*/
            _r_inf_maximo__out = tac_tmp1;
        }
        else {
            /*max begin*/
            real tac_tmp2;
            tac_tmp2 = inputs[0];
            int h_tmp2;
            for(h_tmp2 = 1; h_tmp2 < 2; h_tmp2++) {
                if(!(inputs[h_tmp2] <= tac_tmp2)) {
                    tac_tmp2 = inputs[h_tmp2];
                }
            }
            /*max end*/
            _r_inf_maximo__out = tac_tmp2;
        }
    }
    // Generated from the component: R_sup_minimo
    {
        real _r_sup_minimo__t_in[2];
        _r_sup_minimo__t_in[0] = _r_sup_rp_menos__out;
        _r_sup_minimo__t_in[1] = _r_min__out;
        real inputs[2];
        int t_tmp1;
        for(t_tmp1 = 0; t_tmp1 < 2; t_tmp1++) {
            inputs[t_tmp1] = _r_sup_minimo__t_in[t_tmp1];
        }
        if((0)) {
            /*min begin*/
            real tac_tmp1;
            tac_tmp1 = inputs[0];
            int h_tmp1;
            for(h_tmp1 = 1; h_tmp1 < 2; h_tmp1++) {
                if(!(inputs[h_tmp1] >= tac_tmp1)) {
                    tac_tmp1 = inputs[h_tmp1];
                }
            }
            /*min end*/
            _r_sup_minimo__out = tac_tmp1;
        }
        else {
            /*max begin*/
            real tac_tmp2;
            tac_tmp2 = inputs[0];
            int h_tmp2;
            for(h_tmp2 = 1; h_tmp2 < 2; h_tmp2++) {
                if(!(inputs[h_tmp2] <= tac_tmp2)) {
                    tac_tmp2 = inputs[h_tmp2];
                }
            }
            /*max end*/
            _r_sup_minimo__out = tac_tmp2;
        }
    }
    // Generated from the component: R_trilha_inf.Vs
    {
        HIL_OutFloat(0x8300001, _r_inf_maximo__out);
    }
    // Generated from the component: R_trilha_sup.Vs
    {
        HIL_OutFloat(0x8300002, _r_sup_minimo__out);
    }
//@cmp.out.block.end
    //////////////////////////////////////////////////////////////////////////
    // Update block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.update.block.start
    // Generated from the component: I_IN.Ia1
    // Generated from the component: I_LOOP.Ia1
    // Generated from the component: R_C0
    // Generated from the component: R_min
    // Generated from the component: R_p
    // Generated from the component: V_CURSOR.Va1
    // Generated from the component: V_RL.Va1
    // Generated from the component: V_TX.Va1
    // Generated from the component: folga_b
    // Generated from the component: folga_memoria
    {
        _folga_memoria__state = _folga_max__out;
    }
    // Generated from the component: kellet_atraso
    _kellet_atraso__a_sum += _kellet_atraso__states[0] * _kellet_atraso__a_coeff[1];
    _kellet_atraso__delay_line_in = _ruido_branco_c_function__out - _kellet_atraso__a_sum;
    _kellet_atraso__states[0] = _kellet_atraso__delay_line_in;
    // Generated from the component: mov_memoria
    {
        _mov_memoria__state = _folga_max__out;
    }
    // Generated from the component: relogio
    {
        _relogio__state += _relogio__p_execution_rate;
        if((_relogio__p_enb_reset == 1)) {
            if((_relogio__state >= _relogio__p_reset_at)) {
                _relogio__state = 0.0;
            }
        }
    }
    // Generated from the component: res_fase
    // Generated from the component: res_liga
    // Generated from the component: res_meio_menos_fase
    // Generated from the component: ruido_branco.C function
    {
    }
    // Generated from the component: ruido_liga
    // Generated from the component: A_para_uA
    // Generated from the component: XTR115_x100
    // Generated from the component: A_para_mA
    // Generated from the component: v_cursor
    // Generated from the component: V_RL_V
    // Generated from the component: V_TX_V
    // Generated from the component: referencia
    {
    }
    // Generated from the component: kellet_direto
    // Generated from the component: kellet_polo0
    _kellet_polo0__states[0] = _kellet_polo0__delay_line_in;
    // Generated from the component: kellet_polo1
    _kellet_polo1__states[0] = _kellet_polo1__delay_line_in;
    // Generated from the component: kellet_polo2
    _kellet_polo2__states[0] = _kellet_polo2__delay_line_in;
    // Generated from the component: kellet_polo3
    _kellet_polo3__states[0] = _kellet_polo3__delay_line_in;
    // Generated from the component: kellet_polo4
    _kellet_polo4__states[0] = _kellet_polo4__delay_line_in;
    // Generated from the component: kellet_polo5
    _kellet_polo5__states[0] = _kellet_polo5__delay_line_in;
    // Generated from the component: ruido_branco_N01
    // Generated from the component: I_IN_uA
    // Generated from the component: XTR115_Io.Is1
    // Generated from the component: I_LOOP_mA
    // Generated from the component: folga_theta_mais_b
    // Generated from the component: receptor
    {
    }
    // Generated from the component: theta_ref
    // Generated from the component: kellet_soma
    // Generated from the component: folga_min
    // Generated from the component: I_receptor_mA
    // Generated from the component: erro_FE_pc
    // Generated from the component: theta_med
    // Generated from the component: ruido_K_ENR
    // Generated from the component: folga_max
    // Generated from the component: dRc_ohm
    // Generated from the component: mov_desvio
    // Generated from the component: res_espiras_por_grau
    // Generated from the component: theta_cursor
    // Generated from the component: mov_abs
    // Generated from the component: res_soma_a
    // Generated from the component: mov_cursor_movendo
    // Generated from the component: res_espira
    // Generated from the component: ruido_x_movimento
    // Generated from the component: res_soma_fase
    // Generated from the component: ruido_chave
    // Generated from the component: res_graus_por_espira
    // Generated from the component: R_c_base_mais_ruido
    // Generated from the component: res_desvio
    // Generated from the component: R_contato.Vs
    // Generated from the component: res_chave
    // Generated from the component: res_saida
    // Generated from the component: R_inf_Rp_x
    // Generated from the component: theta_resolucao
    // Generated from the component: R_inf_minimo
    // Generated from the component: R_sup_Rp_menos
    // Generated from the component: R_inf_maximo
    // Generated from the component: R_sup_minimo
    // Generated from the component: R_trilha_inf.Vs
    // Generated from the component: R_trilha_sup.Vs
    //@cmp.update.block.end
}
// ----------------------------------------------------------------------------------------
//-----------------------------------------------------------------------------------------