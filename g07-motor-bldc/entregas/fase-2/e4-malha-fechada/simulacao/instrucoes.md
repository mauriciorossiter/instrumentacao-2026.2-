# Simulação — G07, Fase 2, Entrega 04: malha de corrente com instrumentação real

Planta: equivalente elétrico da E02. Instrumento: sensor Hall ACS712-20A com a cadeia real da E03, agora nas fases **a** e **b** (i_c = −(i_a+i_b)). Grandeza controlada: módulo da corrente do par em condução, (|i_a|+|i_b|+|i_c|)/2. Controlador: PI nativo (`PID controller`), Kp = 0,264, Ki = 222 1/s (ωc = 2500 rad/s).

## Arquivos

- `modelo_malha_fechada.tse` — modelo (Typhoon HIL Control Center **2026.3**, perspectiva **tempo real**, Virtual HIL).
- `painel_malha_fechada.cus` — painel do HIL SCADA: 11 caixas, mostradores e Capture com os presets **Default** (R3, 0,45 s) e **R4_varredura** (R4/R5, 0,5 s), ambos a 100 kS/s com gatilho em `G07_cl_ref`.
- `codigo_c_functions.md` — código das C functions novas ou modificadas.
- `dados-vhil-e4/` — capturas: `e4_r3_ideal`, `e4_r3_real`, `e4_r4_zero`, `e4_r4_rc`, `e4_r4_ruido`, `e4_r5_autocal` (.csv).

## Caixas do painel

As 9 caixas da E03 ficam nos valores padrão (`G07_S_erro` 1.5, `G07_V_zero` 10, `G07_T` 60, `G07_fc_sensor` 80, `G07_ruido` 10, `G07_fc_rc` 15, `G07_fs_adc` 20, `G07_bits` 12, `G07_corr` 1). Novas:

| Caixa | Padrão | Função |
|---|---|---|
| `G07_fb_real` | 1 | 0 = realimenta a medição ideal; 1 = a real |
| `G07_autocal` | 0 | 1 = autocalibração de zero (R5): 5 ms com d = 0 na partida (e a cada nível da varredura) |

## Bloco do Model initialization

Substituir o trecho de `g07_modo` até `g07_cl_ens` pelo bloco abaixo, mudando só as linhas indicadas na tabela.

```
g07_modo = 5
g07_d0 = 0.7074
g07_d_ini = 0.0
g07_d_deg = 0.7074
g07_t_deg = 0.0
g07_t_ci = 0.15
g07_d_ci = 0.0
g07_Td = 0.02
g07_t_p1 = 0.33
g07_t_p2 = 0.39
g07_cl_ens = 1
```

| Captura (CSV) | Mudar no bloco | Painel | Preset | Esperado |
|---|---|---|---|---|
| `e4_r3_ideal` | — | `G07_fb_real` = 0 | Default | planta = 1,500 A; t_s ≈ 1,4 ms; afundamento −0,17 A |
| `e4_r3_real` | — | `G07_fb_real` = 1 | Default | medida 1,500 A, planta ≈ 1,478 A |
| `e4_r4_zero` | `g07_t_p1 = 1.0`, `g07_t_p2 = 1.1`, `g07_cl_ens = 2` | `G07_fb_real` = 1 | R4_varredura | planta 1,48 / 1,38 / 1,22 / 0 A |
| `e4_r4_rc` | idem, `g07_cl_ens = 3` | `G07_fb_real` = 1 | R4_varredura | 1,48 / 1,49 / 1,50 / 1,91 A |
| `e4_r4_ruido` | idem, `g07_cl_ens = 4` | `G07_fb_real` = 1 | R4_varredura | 1,48 / 1,32 / 0,89 / 0,03 A |
| `e4_r5_autocal` | idem, `g07_cl_ens = 2` | `G07_fb_real` = 1, `G07_autocal` = 1 | R4_varredura | 1,47–1,48 A em todos os níveis |

Linha `g07_cl_ens`: 1 = sequência do R3 (degrau 1,0 → 1,5 A em 0,15 s; afundamento Δd = −0,1 de 0,25 a 0,30 s; pulso de carga de 0,33 a 0,39 s); 2, 3, 4 = varredura do R4 (zero não compensado 0/20/50/150 mV; filtro RC 15/3/1/0,3 kHz; ruído 10/100/300/1000 mV), 4 níveis de 0,1 s a partir de 0,1 s.

## Como executar

1. Abrir `modelo_malha_fechada.tse` no Schematic Editor, perspectiva **tempo real**; colar o bloco; compilar e conferir `G07 E04: malha de corrente Kp=0.2639 Ki=222.2`.
2. HIL SCADA: carregar `modelo_malha_fechada Target files/modelo_malha_fechada.cpd` em **Virtual HIL** e abrir `painel_malha_fechada.cus`. Após cada compilação: *Model > Reload Model*.
3. Ajustar `G07_fb_real` e `G07_autocal` no painel e escolher o preset.
4. Com a simulação parada, clicar em **T↑** e depois em *Start simulation*. Exportar (primeiro ícone vermelho da barra inferior do Capture > CSV > *Save data*) para `dados-vhil-e4/`.
5. Demonstração ao vivo (sequência do R3 rodando): `G07_fb_real` 0/1; `G07_corr` = 0; `G07_ruido` = 100; `G07_fc_rc` = 0.3. Comparar `G07_cl_med` (medida) com `G07_cl_planta` (real).
6. Ao terminar, voltar ao bloco acima (`g07_cl_ens = 1`) e a `G07_autocal` = 0.
