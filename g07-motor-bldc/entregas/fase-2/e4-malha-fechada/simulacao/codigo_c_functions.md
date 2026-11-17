# Código das C functions novas ou modificadas — `modelo_malha_fechada.tse` (G07, F2 E04)

O mesmo código está no `.tse`. Os blocos da cadeia real (`G07_S1` a `G07_P1`) são os da Entrega 03 (ver `e3-instrumentacao/simulacao/codigo_c_functions.md`); a fase b usa cópias com sufixo `_b` e outra semente do gerador de ruído. Parâmetros vêm do *Model initialization* (bloco da Entrega 04).

## G07_CL_referencia

Gera a referência de corrente, a perturbação Δd e a janela de calibração; na varredura (g07_cl_ens = 2, 3, 4) troca o nível da característica a cada 0,1 s.

Entradas: `real eQ_sc;real fcrc_sc;real sg_sc;real acal;` — saídas: `real iref;real dd;real cal;real eQ;real fcrc;real sg;`

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

Módulo da corrente do par em condução, (|ia|+|ib|+|ic|)/2, com ic = −(ia+ib), para as correntes verdadeiras (planta) e medidas (real); escolhe a realimentada por `G07_fb_real`.

Entradas: `real ia_i;real ib_i;real ia_r;real ib_r;real fb;` — saídas: `real i_fb;real i_pl;real i_mr;`

```c
gfb_ci = -(ia_i + ib_i);
gfb_cr = -(ia_r + ib_r);
i_pl = 0.5*((ia_i >= 0.0 ? ia_i : -ia_i) + (ib_i >= 0.0 ? ib_i : -ib_i) + (gfb_ci >= 0.0 ? gfb_ci : -gfb_ci));
i_mr = 0.5*((ia_r >= 0.0 ? ia_r : -ia_r) + (ib_r >= 0.0 ? ib_r : -ib_r) + (gfb_cr >= 0.0 ? gfb_cr : -gfb_cr));
i_fb = (fb > 0.5) ? i_mr : i_pl;
```

## G07_P1_processamento

Processamento da E03 com a autocalibração de zero (R5): na janela `cal`, média das amostras após 3 ms; depois usa a média como zero.

Entradas: `real v_adc;real novo;real eS;real eQ;real T;real corr;real fs;real cal;real acal;` — saídas: `real i_med;`

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

## G07_Seletor_duty

Seletor de razão cíclica da E01, com o modo 5 (malha de corrente): d = saída do PI + Δd, limitada a 0–1, e 0 durante a calibração.

Entradas: `real in;real dc;real cal;` — saídas: `real out;`

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

