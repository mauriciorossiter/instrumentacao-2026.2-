# Código das C functions do `modelo_instrumentado.tse` (G07, F2 E03)

O mesmo código está dentro do `.tse`. Todos os blocos executam a 5 µs (`Ts`). Parâmetros do *Model initialization*: `g07_S0` (0,1 V/A), `g07_VQ` (2,5 V), `g07_dVQ` (−0,07 mV/°C), `g07_dS` (−0,004 mV/A/°C), `g07_Tsen` (5 µs), `g07_fpwm` (10 kHz) e `g07_R5_*` (níveis do R5). As variáveis globais de cada bloco têm prefixo próprio (`gs1_`, `gs2_`, …).

## G07_S1_sensibilidade

entradas: real i;real eS;real T; | saidas: real v;real iso;

```c
gs1_k = 1.0 + eS/100.0 + g07_dS*(T - 25.0)/g07_S0;
v = g07_S0*gs1_k*i;
iso = gs1_k*i;
```

## G07_S2_zero

entradas: real v_in;real i;real eQ;real T; | saidas: real v;real iso;

```c
gs2_dz = eQ/1000.0 + g07_dVQ*(T - 25.0);
v = v_in + g07_VQ + gs2_dz;
iso = i + gs2_dz/g07_S0;
```

## G07_S3_banda

entradas: real v_in;real i;real fc; | saidas: real v;real iso;real r1;real r2;real r3;

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

entradas: real v_in;real i;real sg; | saidas: real v;real iso;real r1;real r2;real r3;

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

entradas: real v_in;real i;real fc; | saidas: real v;real iso;

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

entradas: real v_in;real i;real fs;real nb; | saidas: real v;real iso;real novo;real r1;real r2;real r3;

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

entradas: real v_adc;real novo;real eS;real eQ;real T;real corr;real fs; | saidas: real i_med;

```c
if (corr > 0.5) {
gp1_Vc = g07_VQ + eQ/1000.0 + g07_dVQ*(T - 25.0);
gp1_Sc = g07_S0*(1.0 + eS/100.0) + g07_dS*(T - 25.0);
} else {
gp1_Vc = g07_VQ;
gp1_Sc = g07_S0;
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

