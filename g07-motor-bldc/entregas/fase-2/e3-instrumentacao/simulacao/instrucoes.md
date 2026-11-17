# Simulação — G07, Fase 2, Entrega 03: instrumentação da corrente de fase (Hall)

Planta: equivalente elétrico da Entrega 02 (motor BLDC MOONS' R42BLD30L3). Grandeza medida: corrente da fase a. Sensor: efeito Hall, Allegro ACS712ELCTR-20A-T (2,5 V + 100 mV/A, 80 kHz).

## Arquivos

- `modelo_instrumentado.tse` — modelo (Typhoon HIL Control Center **2026.3**, perspectiva **tempo real**, Virtual HIL).
- `painel_instrumentado.cus` — painel do HIL SCADA: 9 caixas das características, mostradores e Capture/Scope com os presets **Default** (R4) e **R5**.
- `codigo_c_functions.md` — código das 7 C functions da cadeia real (o mesmo que está no `.tse`), para leitura.
- `dados-vhil-e3/` — capturas do VHIL: `e3_a.csv`, `e3_b.csv`, `e3_c.csv` (R4) e `e3_r5.csv` (R5).

## Blocos novos no `.tse`

| Nome | Tipo (`core/…`) | Função |
|---|---|---|
| `G07_iS` | Current Measurement (5 µs) | primário do sensor, em série com a fase a |
| `G07_i_verdadeira` | Probe | grandeza real |
| `G07_Med_ideal` + `G07_i_ideal` | Gain (= 1) + Probe | medição ideal |
| `G07_S1_sensibilidade` | C function | erro de sensibilidade + deriva com T (modificante) |
| `G07_S2_zero` | C function | desvio de zero + deriva com T (interferente) |
| `G07_S3_banda` | C function | dinâmica de 1.ª ordem do sensor |
| `G07_S4_ruido` | C function | ruído branco gaussiano |
| `G07_v_sensor` | Probe | saída do sensor [V] |
| `G07_C1_filtro_RC` | C function | filtro anti-aliasing RC |
| `G07_C2_ADC` | C function | amostragem síncrona + quantização, faixa 0–5 V |
| `G07_P1_processamento` | C function | V→A, correção calculada (zero, ganho, T), média por período de PWM |
| `G07_i_real` | Probe | medição real [A] |
| `G07_iso_*` | Probe | cada característica sozinha (R4) |
| `G07_R5_*` | Probe | níveis exagerados de banda, ruído e bits (R5) |

## SCADA Inputs (valores reais padrão; 0 desliga a característica, T = 25 °C anula as derivas)

| Entrada | Padrão | Unidade |
|---|---|---|
| `G07_S_erro` | 1,5 | % |
| `G07_V_zero` | 10 | mV |
| `G07_T` | 60 | °C |
| `G07_fc_sensor` | 80 | kHz |
| `G07_ruido` | 10 | mV rms (a 200 kS/s) |
| `G07_fc_rc` | 15 | kHz |
| `G07_fs_adc` | 20 | kHz |
| `G07_bits` | 12 | bit |
| `G07_corr` | 1 | 0/1 (correção + média) |

## Ensaios (Model initialization)

Substituir o trecho de `g07_modo` até `g07_d0` pelo bloco abaixo, mudando só `g07_modo` (1 = degrau, 2 = condição inicial, 3 = pulso de carga). As 10 linhas são obrigatórias (sem `g07_Td` ou `g07_d0` a compilação falha).

```
g07_modo = 1
g07_d_ini = 0.0
g07_d_deg = 0.7074
g07_t_deg = 0.0
g07_t_ci = 0.15
g07_d_ci = 0.0
g07_Td = 0.02
g07_t_p1 = 0.10
g07_t_p2 = 0.20
g07_d0 = 0.7074
```

| Ensaio | `g07_modo` | CSV | Preset | Esperado |
|---|---|---|---|---|
| (a) degrau do repouso | 1 | `e3_a.csv` | Default | n ≈ 3658 rpm; i_a eficaz 1,14 A; real: viés ≈ 0,5 mA, erro rms ≈ 58 mA, atraso 60 µs |
| (b) condição inicial | 2 | `e3_b.csv` | Default | corrente nula após 150 ms; real ≈ 1 mA (sem correção: 75 mA) |
| (c) pulso de carga | 3 | `e3_c.csv` | Default | Δi eficaz ≈ 0,21 A, real e ideal |
| R5 | 1 | `e3_r5.csv` | R5 | erro rms: banda 60 / 200 / 490 mA; ruído 0,5 / 2 / 10 A; bits 49 / 210 / 1030 mA |

## Como executar

1. Abrir `modelo_instrumentado.tse` no Schematic Editor, perspectiva **tempo real**; colar o bloco do ensaio; compilar e conferir no console `G07 E03: sensor Hall S0=0.100 V/A` e `modo de ensaio = …`.
2. HIL SCADA: carregar `modelo_instrumentado Target files/modelo_instrumentado.cpd` escolhendo **Virtual HIL** e abrir `painel_instrumentado.cus`. Após cada compilação: *Model > Reload Model*.
3. R4: Capture com o preset **Default** (0,3 s, 100 kS/s, 13 sinais; gatilho em `n`, Rising edge, 20, offset 0, **Use first trigger**). Com a simulação parada, clicar em **T↑** e depois em *Start simulation*. Exportar: primeiro ícone vermelho da barra inferior do Capture > CSV > *Save data*.
4. R5: bloco com `g07_modo = 1`, simulação rodando há uns 2 s; trocar o preset para **R5** (0,05 s, 11 sinais) e clicar em **T↑** (se não disparar, **F**). Exportar.
5. Demonstração ao vivo: mudar as caixas do painel (por exemplo `G07_corr` = 0, `G07_ruido` = 200, `G07_fc_sensor` = 0.5, `G07_bits` = 4) e comparar `G07_i_real` com `G07_i_verdadeira`.
6. Ao terminar, deixar o bloco com `g07_modo = 1` e fechar o Schematic Editor sem salvar se não quiser gravar outro ensaio no `.tse`.
