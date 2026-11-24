# Código das C functions do `modelo_final.tse` (G07, Fase 2, entrega final)

Extraído do próprio `.tse` (o código que roda é o de dentro do modelo). Todos executam a 5 µs (`Ts`). Os blocos da fase b são cópias com sufixo `_b` (outro gerador de ruído). Parâmetros vêm do *Model initialization* (`g07_*`).

## G07_S1_sensibilidade

Sensor: sensibilidade com erro e deriva térmica (entrada modificante).

entradas: `real i;real eS;real T;` · saídas: `real v;real iso;` · parâmetros: `real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
gs1_k = 1.0 + eS/100.0 + g07_dS*(T - 25.0)/g07_S0;
v = g07_S0*gs1_k*i;
iso = gs1_k*i;
```

## G07_S2_zero

Sensor: desvio de zero com deriva térmica (entrada interferente).

entradas: `real v_in;real i;real eQ;real T;` · saídas: `real v;real iso;` · parâmetros: `real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
gs2_dz = eQ/1000.0 + g07_dVQ*(T - 25.0);
v = v_in + g07_VQ + gs2_dz;
iso = i + gs2_dz/g07_S0;
```

## G07_S3_banda

Sensor: dinâmica de 1.ª ordem (Euler regressivo). Também calcula os níveis exagerados r1–r3.

entradas: `real v_in;real i;real fc;` · saídas: `real v;real iso;real r1;real r2;real r3;` · parâmetros: `real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
if (fc > 0.0) {
gs3_w = 6.283185307*fc*1000.0*g07_Tsen;
gs3_a = gs3_w/(1.0 + gs3_w);
gs3_y = gs3_y + gs3_a*(v_in - gs3_y);
gs3_yi = gs3_yi + gs3_a*(i - gs3_yi);
} else {
gs3_y = v_in;
gs3_yi = i;
}
v = gs3_y;
iso = gs3_yi;
gs3_w = 6.283185307*g07_R5_fc1*g07_Tsen;
gs3_a = gs3_w/(1.0 + gs3_w);
gs3_r1 = gs3_r1 + gs3_a*(i - gs3_r1);
r1 = gs3_r1;
gs3_w = 6.283185307*g07_R5_fc2*g07_Tsen;
gs3_a = gs3_w/(1.0 + gs3_w);
gs3_r2 = gs3_r2 + gs3_a*(i - gs3_r2);
r2 = gs3_r2;
gs3_w = 6.283185307*g07_R5_fc3*g07_Tsen;
gs3_a = gs3_w/(1.0 + gs3_w);
gs3_r3 = gs3_r3 + gs3_a*(i - gs3_r3);
r3 = gs3_r3;
```

## G07_S4_ruido

Sensor: ruído gaussiano (Park–Miller com Schrage, soma de 6 uniformes).

entradas: `real v_in;real i;real sg;` · saídas: `real v;real iso;real r1;real r2;real r3;` · parâmetros: `real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
gs4_g1 = 0.0;
for (gs4_q = 0; gs4_q < 6; gs4_q++) {
gs4_hi = gs4_s1/127773;
gs4_lo = gs4_s1 - gs4_hi*127773;
gs4_s1 = 16807*gs4_lo - 2836*gs4_hi;
if (gs4_s1 <= 0) gs4_s1 = gs4_s1 + 2147483647;
gs4_g1 = gs4_g1 + gs4_s1/2147483647.0;
}
gs4_g1 = (gs4_g1 - 3.0)*1.4142136;
gs4_g2 = 0.0;
for (gs4_q = 0; gs4_q < 6; gs4_q++) {
gs4_hi = gs4_s2/127773;
gs4_lo = gs4_s2 - gs4_hi*127773;
gs4_s2 = 16807*gs4_lo - 2836*gs4_hi;
if (gs4_s2 <= 0) gs4_s2 = gs4_s2 + 2147483647;
gs4_g2 = gs4_g2 + gs4_s2/2147483647.0;
}
gs4_g2 = (gs4_g2 - 3.0)*1.4142136;
v = v_in + sg/1000.0*gs4_g1;
iso = i + sg/1000.0*gs4_g2/g07_S0;
r1 = i + g07_R5_sg1*gs4_g2/g07_S0;
r2 = i + g07_R5_sg2*gs4_g2/g07_S0;
r3 = i + g07_R5_sg3*gs4_g2/g07_S0;
```

## G07_C1_filtro_RC

Condicionamento: filtro anti-aliasing RC de 1.ª ordem.

entradas: `real v_in;real i;real fc;` · saídas: `real v;real iso;` · parâmetros: `real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
if (fc > 0.0) {
gc1_w = 6.283185307*fc*1000.0*g07_Tsen;
gc1_a = gc1_w/(1.0 + gc1_w);
gc1_y = gc1_y + gc1_a*(v_in - gc1_y);
gc1_yi = gc1_yi + gc1_a*(i - gc1_yi);
} else {
gc1_y = v_in;
gc1_yi = i;
}
v = gc1_y;
iso = gc1_yi;
```

## G07_C2_ADC

Condicionamento: ADC síncrono com o PWM, faixa 0–5 V, quantização.

entradas: `real v_in;real i;real fs;real nb;` · saídas: `real v;real iso;real novo;real r1;real r2;real r3;` · parâmetros: `real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
if (fs <= 0.0) {
gc2_x = v_in;
gc2_xi = g07_VQ + g07_S0*i;
novo = 1.0;
} else {
gc2_M = (int)(1.0/(fs*1000.0*g07_Tsen) + 0.5);
if (gc2_M < 1) gc2_M = 1;
if (gc2_k % gc2_M == 0) {
gc2_h = v_in;
gc2_hi = g07_VQ + g07_S0*i;
novo = 1.0;
} else {
novo = 0.0;
}
gc2_k = gc2_k + 1;
if (gc2_k >= 1000000000) gc2_k = 0;
gc2_x = gc2_h;
gc2_xi = gc2_hi;
}
if (gc2_x < 0.0) gc2_x = 0.0;
if (gc2_x > 5.0) gc2_x = 5.0;
if (gc2_xi < 0.0) gc2_xi = 0.0;
if (gc2_xi > 5.0) gc2_xi = 5.0;
if (nb > 0.5) {
gc2_N = (int)(nb + 0.5);
gc2_L = 1 << gc2_N;
gc2_lsb = 5.0/gc2_L;
gc2_x = ((int)(gc2_x/gc2_lsb + 0.5))*gc2_lsb;
if (gc2_x > 5.0 - gc2_lsb) gc2_x = 5.0 - gc2_lsb;
gc2_N = (int)(nb + 0.5);
gc2_L = 1 << gc2_N;
gc2_lsb = 5.0/gc2_L;
gc2_xi = ((int)(gc2_xi/gc2_lsb + 0.5))*gc2_lsb;
if (gc2_xi > 5.0 - gc2_lsb) gc2_xi = 5.0 - gc2_lsb;
}
v = gc2_x;
iso = (gc2_xi - g07_VQ)/g07_S0;
gc2_z = g07_VQ + g07_S0*i;
gc2_N = (int)(g07_R5_nb1 + 0.5);
gc2_L = 1 << gc2_N;
gc2_lsb = 5.0/gc2_L;
gc2_z = ((int)(gc2_z/gc2_lsb + 0.5))*gc2_lsb;
if (gc2_z > 5.0 - gc2_lsb) gc2_z = 5.0 - gc2_lsb;
r1 = (gc2_z - g07_VQ)/g07_S0;
gc2_z = g07_VQ + g07_S0*i;
gc2_N = (int)(g07_R5_nb2 + 0.5);
gc2_L = 1 << gc2_N;
gc2_lsb = 5.0/gc2_L;
gc2_z = ((int)(gc2_z/gc2_lsb + 0.5))*gc2_lsb;
if (gc2_z > 5.0 - gc2_lsb) gc2_z = 5.0 - gc2_lsb;
r2 = (gc2_z - g07_VQ)/g07_S0;
gc2_z = g07_VQ + g07_S0*i;
gc2_N = (int)(g07_R5_nb3 + 0.5);
gc2_L = 1 << gc2_N;
gc2_lsb = 5.0/gc2_L;
gc2_z = ((int)(gc2_z/gc2_lsb + 0.5))*gc2_lsb;
if (gc2_z > 5.0 - gc2_lsb) gc2_z = 5.0 - gc2_lsb;
r3 = (gc2_z - g07_VQ)/g07_S0;
```

## G07_P1_processamento

Processamento: V→A, correção calculada (zero, ganho, temperatura), autocalibração do zero e média por período de PWM.

entradas: `real v_adc;real novo;real eS;real eQ;real T;real corr;real fs;real cal;real acal;` · saídas: `real i_med;` · parâmetros: `int g07_Ncal0;real g07_S0;real g07_VQ;real g07_dVQ;real g07_dS;real g07_Tsen;real g07_fpwm;real g07_R5_fc1;real g07_R5_fc2;real g07_R5_fc3;real g07_R5_sg1;real g07_R5_sg2;real g07_R5_sg3;real g07_R5_nb1;real g07_R5_nb2;real g07_R5_nb3;`

```c
if (corr > 0.5) {
gp1_Vc = g07_VQ + eQ/1000.0 + g07_dVQ*(T - 25.0);
gp1_Sc = g07_S0*(1.0 + eS/100.0) + g07_dS*(T - 25.0);
} else {
gp1_Vc = g07_VQ;
gp1_Sc = g07_S0;
}
if (acal > 0.5) {
if (cal > 0.5) {
gp1_kc = gp1_kc + 1;
if (gp1_kc > g07_Ncal0 && novo > 0.5) {
gp1_acc = gp1_acc + v_adc;
gp1_nacc = gp1_nacc + 1;
}
} else {
if (gp1_nacc > 0) {
gp1_Va = gp1_acc/gp1_nacc;
gp1_tem = 1;
}
gp1_kc = 0;
gp1_acc = 0.0;
gp1_nacc = 0;
}
if (gp1_tem > 0) gp1_Vc = gp1_Va;
}
gp1_im = (v_adc - gp1_Vc)/gp1_Sc;
if (corr > 0.5 && fs > 0.0) {
gp1_L = (int)(fs*1000.0/g07_fpwm + 0.5);
if (gp1_L < 1) gp1_L = 1;
if (gp1_L > 64) gp1_L = 64;
if (novo > 0.5) {
gp1_buf[gp1_p] = gp1_im;
gp1_p = gp1_p + 1;
if (gp1_p >= 64) gp1_p = 0;
}
gp1_s = 0.0;
for (gp1_q = 0; gp1_q < gp1_L; gp1_q++) {
gp1_j = gp1_p - 1 - gp1_q;
if (gp1_j < 0) gp1_j = gp1_j + 64;
gp1_s = gp1_s + gp1_buf[gp1_j];
}
i_med = gp1_s/gp1_L;
} else {
i_med = gp1_im;
}
```

## G07_CL_referencia

Ensaios: referência, afundamento, janelas de calibração e varreduras do item 7.

entradas: `real eQ_sc;real fcrc_sc;real sg_sc;real acal;` · saídas: `real iref;real dd;real cal;real eQ;real fcrc;real sg;` · parâmetros: `int g07_cl_ens;real g07_Tsen;real g07_t_ref;real g07_iref0;real g07_iref1;real g07_t_dd1;real g07_t_dd2;real g07_dd;real g07_t_cal;real g07_t_ini;real g07_T_nivel;real g07_tv_degrau;real g07_tv_dd1;real g07_tv_dd2;real g07_v_eQ0;real g07_v_eQ1;real g07_v_eQ2;real g07_v_eQ3;real g07_v_rc0;real g07_v_rc1;real g07_v_rc2;real g07_v_rc3;real g07_v_sg0;real g07_v_sg1;real g07_v_sg2;real g07_v_sg3;`

```c
gr_t = gr_t + g07_Tsen;
cal = 0.0;
dd = 0.0;
eQ = eQ_sc;
fcrc = fcrc_sc;
sg = sg_sc;
if (g07_cl_ens == 1) {
iref = (gr_t < g07_t_ref) ? g07_iref0 : g07_iref1;
if (gr_t >= g07_t_dd1 && gr_t < g07_t_dd2) dd = g07_dd;
if (acal > 0.5 && gr_t < g07_t_cal) {
cal = 1.0;
iref = 0.0;
}
} else {
iref = g07_iref0;
if (acal > 0.5 && gr_t < g07_t_cal) {
cal = 1.0;
iref = 0.0;
}
if (gr_t >= g07_t_ini) {
gr_j = (int)((gr_t - g07_t_ini)/g07_T_nivel);
if (gr_j > 3) gr_j = 3;
gr_tau = gr_t - g07_t_ini - gr_j*g07_T_nivel;
if (gr_tau >= g07_tv_degrau) iref = g07_iref1;
if (gr_tau >= g07_tv_dd1 && gr_tau < g07_tv_dd2) dd = g07_dd;
if (acal > 0.5 && gr_tau < g07_t_cal) {
cal = 1.0;
iref = 0.0;
}
if (g07_cl_ens == 2) eQ = (gr_j == 0) ? g07_v_eQ0 : ((gr_j == 1) ? g07_v_eQ1 : ((gr_j == 2) ? g07_v_eQ2 : g07_v_eQ3));
if (g07_cl_ens == 3) fcrc = (gr_j == 0) ? g07_v_rc0 : ((gr_j == 1) ? g07_v_rc1 : ((gr_j == 2) ? g07_v_rc2 : g07_v_rc3));
if (g07_cl_ens == 4) sg = (gr_j == 0) ? g07_v_sg0 : ((gr_j == 1) ? g07_v_sg1 : ((gr_j == 2) ? g07_v_sg2 : g07_v_sg3));
}
}
```

## G07_CL_realimentacao

Seletor ideal/real e processamento da corrente do par em condução: módulo (E04), seleção pela posição (G07_hall) e correção do RC (G07_comp_rc).

entradas: `real ia_i;real ib_i;real ia_r;real ib_r;real fb;real hA;real hB;real hC;real hall;real crc;real fcrc;` · saídas: `real i_fb;real i_pl;real i_mr;real i_mod;real i_hall;real i_hall_i;real fe;` · parâmetros: `real g07_Tsen;real g07_hall0;real g07_comp0;`

```c
gfb_ci = -(ia_i + ib_i);
gfb_cr = -(ia_r + ib_r);
i_pl = 0.5*((ia_i >= 0.0 ? ia_i : -ia_i) + (ib_i >= 0.0 ? ib_i : -ib_i) + (gfb_ci >= 0.0 ? gfb_ci : -gfb_ci));
i_mod = 0.5*((ia_r >= 0.0 ? ia_r : -ia_r) + (ib_r >= 0.0 ? ib_r : -ib_r) + (gfb_cr >= 0.0 ? gfb_cr : -gfb_cr));
if (hA > 0.5 && hB < 0.5 && hC < 0.5) gfb_hr = ia_r;
else if (hA > 0.5 && hB < 0.5 && hC > 0.5) gfb_hr = -(ib_r);
else if (hA > 0.5 && hB > 0.5 && hC < 0.5) gfb_hr = -(gfb_cr);
else if (hA < 0.5 && hB > 0.5 && hC < 0.5) gfb_hr = ib_r;
else if (hA < 0.5 && hB > 0.5 && hC > 0.5) gfb_hr = -(ia_r);
else if (hA < 0.5 && hB < 0.5 && hC > 0.5) gfb_hr = gfb_cr;
if (hA > 0.5 && hB < 0.5 && hC < 0.5) gfb_hi = ia_i;
else if (hA > 0.5 && hB < 0.5 && hC > 0.5) gfb_hi = -(ib_i);
else if (hA > 0.5 && hB > 0.5 && hC < 0.5) gfb_hi = -(gfb_ci);
else if (hA < 0.5 && hB > 0.5 && hC < 0.5) gfb_hi = ib_i;
else if (hA < 0.5 && hB > 0.5 && hC > 0.5) gfb_hi = -(ia_i);
else if (hA < 0.5 && hB < 0.5 && hC > 0.5) gfb_hi = gfb_ci;
i_hall = gfb_hr;
i_hall_i = gfb_hi;
gfb_k = gfb_k + 1;
if (hA > 0.5 && gfb_hA0 < 0.5) {
if (gfb_k > 20) gfb_fe = 1.0/(gfb_k*g07_Tsen);
gfb_k = 0;
}
gfb_hA0 = hA;
if (gfb_k*g07_Tsen > 0.05) gfb_fe = 0.0;
fe = gfb_fe;
gfb_g = 1.0;
if ((crc > 0.5 || g07_comp0 > 0.5) && fcrc > 0.0) {
gfb_v = 1.0 + (gfb_fe/(fcrc*1000.0))*(gfb_fe/(fcrc*1000.0));
gfb_g = 0.5*(1.0 + gfb_v);
for (gfb_q = 0; gfb_q < 6; gfb_q++) gfb_g = 0.5*(gfb_g + gfb_v/gfb_g);
}
i_mr = ((hall > 0.5 || g07_hall0 > 0.5) ? i_hall : i_mod)*gfb_g;
i_fb = (fb > 0.5) ? i_mr : i_pl;
```

## G07_Seletor_duty

Atuador: escolhe a razão cíclica (modo 5 = saída do PI; 0 durante a calibração).

entradas: `real in;real dc;real cal;` · saídas: `` · parâmetros: `int g07_modo;real g07_d0;real g07_d_ini;real g07_d_deg;int g07_N_deg;int g07_N_ci;real g07_d_ci;`

```c
if (g07_modo == 1) {
    out = (g07_sel_ticks >= g07_N_deg) ? g07_d_deg : g07_d_ini;
} else if (g07_modo == 2) {
    out = (g07_sel_ticks >= g07_N_ci) ? g07_d_ci : in;
} else if (g07_modo == 3) {
    out = g07_d0;
} else if (g07_modo == 5) {
    out = (cal > 0.5) ? 0.0 : dc;
    if (out < 0.0) out = 0.0;
    if (out > 1.0) out = 1.0;
} else {
    out = in;
}
```
