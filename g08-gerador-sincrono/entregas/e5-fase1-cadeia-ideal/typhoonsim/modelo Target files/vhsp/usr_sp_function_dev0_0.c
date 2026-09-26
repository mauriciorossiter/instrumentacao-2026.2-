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


























//@cmp.def.end


//-----------------------------------------------------------------------------------------
// generated using template: common_variables.template-------------------------------------
// true global variables





// const variables
static const int _i_in_ia1__n_rd_as = 13107200;
static const unsigned int _i_in_ia1__p_addr = 3;
static const char* _i_in_ia1__p_sig_output = "True";

static const int _i_loop_ia1__n_rd_as = 13107200;
static const unsigned int _i_loop_ia1__p_addr = 4;
static const char* _i_loop_ia1__p_sig_output = "True";

static const int _v_ref_va1__n_rd_as = 13107200;
static const unsigned int _v_ref_va1__p_addr = 0;
static const char* _v_ref_va1__p_sig_output = "True";

static const int _v_rl_va1__n_rd_as = 13107200;
static const unsigned int _v_rl_va1__p_addr = 1;
static const char* _v_rl_va1__p_sig_output = "True";

static const int _v_tx_va1__n_rd_as = 13107200;
static const unsigned int _v_tx_va1__p_addr = 2;
static const char* _v_tx_va1__p_sig_output = "True";


static const unsigned char _relogio__p_enb_reset = 0;
static const real _relogio__p_execution_rate = 0.001;
static const real _relogio__p_reset_at = 1.0;

static const char* _a_para_ua__n_multiplication = "Element-wise(K.*u)";
static const real _a_para_ua__p_gain = 1000000.0;

static const char* _xtr115_x100__n_multiplication = "Element-wise(K.*u)";
static const real _xtr115_x100__p_gain = 100.0;

static const char* _a_para_ma__n_multiplication = "Element-wise(K.*u)";
static const real _a_para_ma__p_gain = 1000.0;

static const int _v_rl_v__n_out_size = 1;
static const unsigned int _v_rl_v__p_addr = 16387;

static const int _v_tx_v__n_out_size = 1;
static const unsigned int _v_tx_v__p_addr = 16388;

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
static const unsigned int _xtr115_io_is1__p_addr = 1;
static const int _xtr115_io_is1__p_dtsm_nb = 0;
static const char* _xtr115_io_is1__p_enable_fb_out = "False";
static const unsigned int _xtr115_io_is1__p_spc_nb = 0;

static const int _i_loop_ma__n_out_size = 1;
static const unsigned int _i_loop_ma__p_addr = 16385;

static const int _theta_ref__n_out_size = 1;
static const unsigned int _theta_ref__p_addr = 16391;

static const int _buffer_opa333_vs1__n_spc_baseaddr = 134217728;
static const int _buffer_opa333_vs1__n_spc_off = 4194304;
static const int _buffer_opa333_vs1__n_spc_sp = 2883584;
static const int _buffer_opa333_vs1__n_spc_tv = 3145728;
static const char* _buffer_opa333_vs1__n_val_of_type = "signal controlled";
static const unsigned int _buffer_opa333_vs1__p_addr = 0;
static const unsigned int _buffer_opa333_vs1__p_spc_nb = 0;

static const int _v_cursor__n_out_size = 1;
static const unsigned int _v_cursor__p_addr = 16392;

static const int _i_receptor_ma__n_out_size = 1;
static const unsigned int _i_receptor_ma__p_addr = 16386;

static const int _erro_fe_pc__n_out_size = 1;
static const unsigned int _erro_fe_pc__p_addr = 16389;

static const int _theta_med__n_out_size = 1;
static const unsigned int _theta_med__p_addr = 16390;


//@cmp.var.start
// variables
real _i_in_ia1__out;
real _i_loop_ia1__out;
real _v_ref_va1__out;
real _v_rl_va1__out;
real _v_tx_va1__out;
static real _relogio__out;
static real _a_para_ua__out;
static real _xtr115_x100__out;
static real _a_para_ma__out;






double _referencia__t;

double _referencia__theta_ref;








double _potenciometro__theta;
double _potenciometro__vref;

double _potenciometro__v_cursor;

double _receptor__theta_ref;
double _receptor__v_rl;

double _receptor__erro_FE;
double _receptor__i_mA;
double _receptor__theta_med;

















//@cmp.var.end

//@cmp.svar.start
// state variables















real _relogio__state;

















double _referencia__THETA_FS;

double _referencia__T_MEIO;













double _potenciometro__THETA_FS;

double _potenciometro__x;




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
        _relogio__state = 0;
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
    {
        HIL_OutAO(0x4000, 0);
    }
    {
        HIL_OutFloat(0x82c0001, 0.0);
    }
    {
        HIL_OutAO(0x4001, 0);
    }
    {
        _potenciometro__THETA_FS = 3600.0 ;
        _potenciometro__x = 0.0 ;
    }
    {
        _receptor__THETA_FS = 3600.0 ;
        _receptor__R_L = 250.000 ;
    }
    {
        HIL_OutAO(0x4007, 0);
    }
    {
        HIL_OutFloat(0x82c0000, 0.0);
    }
    {
        HIL_OutAO(0x4008, 0);
    }
    {
        HIL_OutAO(0x4002, 0);
    }
    {
        HIL_OutAO(0x4005, 0);
    }
    {
        HIL_OutAO(0x4006, 0);
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
        tac_tmp1 = HIL_InFloat(0xc80003);
        _i_in_ia1__out = tac_tmp1;
    }
    // Generated from the component: I_LOOP.Ia1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80004);
        _i_loop_ia1__out = tac_tmp1;
    }
    // Generated from the component: V_REF.Va1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80000);
        _v_ref_va1__out = tac_tmp1;
    }
    // Generated from the component: V_RL.Va1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80001);
        _v_rl_va1__out = tac_tmp1;
    }
    // Generated from the component: V_TX.Va1
    {
        real tac_tmp1;
        tac_tmp1 = HIL_InFloat(0xc80002);
        _v_tx_va1__out = tac_tmp1;
    }
    // Generated from the component: relogio
    {
        _relogio__out = _relogio__state;
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
    // Generated from the component: I_IN_uA
    {
        HIL_OutAO(0x4000, _a_para_ua__out);
    }
    // Generated from the component: XTR115_Io.Is1
    {
        {
            HIL_OutFloat(0x82c0001, _xtr115_x100__out);
        }
    }
    // Generated from the component: I_LOOP_mA
    {
        HIL_OutAO(0x4001, _a_para_ma__out);
    }
    // Generated from the component: potenciometro
    _potenciometro__theta = _referencia__theta_ref;
    _potenciometro__vref = _v_ref_va1__out;
    {
        _potenciometro__x = _potenciometro__theta / _potenciometro__THETA_FS ;
        if ( _potenciometro__x < 0.0 ) _potenciometro__x = 0.0 ;
        if ( _potenciometro__x > 1.0 ) _potenciometro__x = 1.0 ;
        _potenciometro__v_cursor = _potenciometro__x * _potenciometro__vref ;
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
        HIL_OutAO(0x4007, _referencia__theta_ref);
    }
    // Generated from the component: buffer_OPA333.Vs1
    {
        HIL_OutFloat(0x82c0000, _potenciometro__v_cursor);
    }
    // Generated from the component: v_cursor
    {
        HIL_OutAO(0x4008, _potenciometro__v_cursor);
    }
    // Generated from the component: I_receptor_mA
    {
        HIL_OutAO(0x4002, _receptor__i_mA);
    }
    // Generated from the component: erro_FE_pc
    {
        HIL_OutAO(0x4005, _receptor__erro_FE);
    }
    // Generated from the component: theta_med
    {
        HIL_OutAO(0x4006, _receptor__theta_med);
    }
//@cmp.out.block.end
    //////////////////////////////////////////////////////////////////////////
    // Update block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.update.block.start
    // Generated from the component: I_IN.Ia1
    // Generated from the component: I_LOOP.Ia1
    // Generated from the component: V_REF.Va1
    // Generated from the component: V_RL.Va1
    // Generated from the component: V_TX.Va1
    // Generated from the component: relogio
    {
        _relogio__state += _relogio__p_execution_rate;
        if((_relogio__p_enb_reset == 1)) {
            if((_relogio__state >= _relogio__p_reset_at)) {
                _relogio__state = 0.0;
            }
        }
    }
    // Generated from the component: A_para_uA
    // Generated from the component: XTR115_x100
    // Generated from the component: A_para_mA
    // Generated from the component: V_RL_V
    // Generated from the component: V_TX_V
    // Generated from the component: referencia
    {
    }
    // Generated from the component: I_IN_uA
    // Generated from the component: XTR115_Io.Is1
    // Generated from the component: I_LOOP_mA
    // Generated from the component: potenciometro
    {
    }
    // Generated from the component: receptor
    {
    }
    // Generated from the component: theta_ref
    // Generated from the component: buffer_OPA333.Vs1
    // Generated from the component: v_cursor
    // Generated from the component: I_receptor_mA
    // Generated from the component: erro_FE_pc
    // Generated from the component: theta_med
    //@cmp.update.block.end
}
// ----------------------------------------------------------------------------------------
//-----------------------------------------------------------------------------------------