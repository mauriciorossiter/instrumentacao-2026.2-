# G07 · Fase 2 · Entrega final: instrumentação não ideal e seus efeitos no controle

Sistema: motor BLDC MOONS' R42BLD30L3 acionando um ventilador. Grandeza instrumentada: **corrente de fase** (fases a e b), com o sensor de efeito Hall **Allegro ACS712ELCTR-20A-T**. Controle: malha de corrente (torque) com PI nativo do Typhoon.

## Versão e arquivos

- **Typhoon HIL Control Center 2026.3**, Schematic Editor na perspectiva **tempo real**, executado no **Virtual HIL** (HIL101) e lido pelo **HIL SCADA**.
- `modelo_final.tse`: modelo único para todos os itens. É o modelo da Entrega 04 com as compensações do item 8.
- `painel_final.cus`: painel do HIL SCADA. Tem 13 caixas (as características do instrumento e as chaves), mostradores e o Capture com 3 presets:
  - **Default**: 0,45 s, 100 kS/s, gatilho em `G07_cl_ref` (sequência de malha fechada).
  - **R4_varredura**: 0,5 s, 100 kS/s, gatilho em `G07_cl_ref` (varreduras).
  - **Item4_malha_aberta**: 0,3 s, 100 kS/s, gatilho em `n` = 20 rpm (leitura ideal × real, cada característica isolada).
- `dados-vhil/`: todas as capturas usadas no relatório (CSV).
- `codigo_c_functions.md`: o código das C functions, para leitura (o mesmo que está no `.tse`).

## Onde está cada bloco da Figura 1 no modelo

| Bloco da Figura 1 | No `modelo_final.tse` |
|---|---|
| Planta (equivalente elétrico) | fases `G07_Rs_x`, `G07_Ls_x`, `G07_e_x`; malha mecânica `G07_L_J` (inércia), `G07_R_B` (atrito), `G07_V_Te`, `G07_V_carga`; acoplamento `G07_Acoplamento` (C function) |
| Ponta de prova ideal | `G07_iS` e `G07_iSb` (`Current Measurement`, em série com as fases a e b) |
| Caminho ideal | `G07_Med_ideal` (`Gain` = 1) e a saída `i_pl` de `G07_CL_realimentacao` |
| Sensor | `G07_S1_sensibilidade`, `G07_S2_zero`, `G07_S3_banda`, `G07_S4_ruido` (e as cópias `_b`) |
| Condicionamento | `G07_C1_filtro_RC`, `G07_C2_ADC` (e `_b`) |
| Processamento e compensação | `G07_P1_processamento` (e `_b`) e `G07_CL_realimentacao` |
| Entradas espúrias | caixas `G07_T` (temperatura) e `G07_ruido` (interferência/ruído) |
| Seletor ideal/real | caixa `G07_fb_real`, dentro de `G07_CL_realimentacao` |
| Referência | `G07_CL_referencia` (C function) |
| Controlador | `G07_CL_erro` (`Sum`) e `G07_CL_PI` (`PID controller`, modo PI) |
| Atuador | `G07_Seletor_duty` + inversor trifásico com PWM de 10 kHz |

O carregamento do sensor (condutor primário de 1,2 mΩ, contra 1,6 Ω por fase) muda a corrente em menos de 0,04 %, por isso não foi inserido no circuito.

## Caixas do painel (valores padrão)

| Caixa | Padrão | O que faz |
|---|---|---|
| `G07_S_erro` | 1.5 | erro de sensibilidade [%] |
| `G07_V_zero` | 10 | desvio de zero [mV] |
| `G07_T` | 60 | temperatura [°C] (25 anula as derivas) |
| `G07_fc_sensor` | 80 | banda do sensor [kHz] |
| `G07_ruido` | 10 | ruído [mV rms] |
| `G07_fc_rc` | 15 | filtro RC [kHz] |
| `G07_fs_adc` | 20 | taxa do ADC [kS/s] |
| `G07_bits` | 12 | resolução do ADC [bit] |
| `G07_corr` | 1 | correção calculada e média por período (0 desliga) |
| `G07_fb_real` | 1 | seletor: 0 = realimenta a medição ideal; 1 = a real |
| `G07_autocal` | 0 | 1 = autocalibração do zero (5 ms com o inversor parado) |
| `G07_hall` | 0 | 1 = processamento pela posição: usa a fase em condução indicada pelos sensores Hall do motor, sem módulo |
| `G07_comp_rc` | 0 | 1 = correção calculada da atenuação do filtro RC na frequência elétrica |

Qualquer caixa pode ser mudada com a simulação rodando: o efeito aparece na hora.

## Como executar (todos os itens)

1. Abrir `modelo_final.tse` no Schematic Editor, perspectiva **tempo real**.
2. Em *Model > Model settings > Model initialization*, substituir o trecho de `g07_modo` até `g07_comp0` pelo bloco do ensaio (tabela abaixo) e compilar. O console deve mostrar `G07 FINAL: modelo unico dos itens 4 a 8`.
3. No HIL SCADA, carregar `modelo_final Target files/modelo_final.cpd` em **Virtual HIL** e abrir `painel_final.cus`. Depois de cada compilação: *Model > Reload Model*.
4. Ajustar as caixas indicadas e escolher o preset no Capture.
5. Com a simulação **parada**, clicar em **T↑** (arma o gatilho) e depois em *Start simulation*. A engrenagem verde ao lado de "Capture" só importa configurações: não usar.
6. Exportar: primeiro ícone vermelho da barra inferior do Capture > CSV > *Save data*, com o nome da tabela, na pasta `dados-vhil/`.

### Blocos do Model initialization

Bloco A (malha aberta, item 4). Mudar só `g07_modo` (1 = degrau, 2 = condição inicial, 3 = pulso de carga):

```
g07_modo = 1
g07_d0 = 0.7074
g07_d_ini = 0.0
g07_d_deg = 0.7074
g07_t_deg = 0.0
g07_t_ci = 0.15
g07_d_ci = 0.0
g07_Td = 0.02
g07_t_p1 = 0.10
g07_t_p2 = 0.20
g07_cl_ens = 1
g07_hall0 = 0
g07_comp0 = 0
```

Bloco B (malha fechada, sequência dos itens 5 e 6):

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
g07_hall0 = 0
g07_comp0 = 0
```

Bloco C (varreduras dos itens 7 e 8): o bloco B com `g07_t_p1 = 1.0`, `g07_t_p2 = 1.1` e `g07_cl_ens` = 2 (zero), 3 (filtro RC) ou 4 (ruído).

Todas as 13 linhas são obrigatórias: sem `g07_Td`, `g07_d0`, `g07_hall0` ou `g07_comp0` a compilação falha.

`g07_hall0 = 1` e `g07_comp0 = 1` ligam as compensações do item 8 desde o instante zero, sem depender do painel (as caixas `G07_hall` e `G07_comp_rc` voltam a 0 a cada carga do modelo e só valem depois de digitadas com Enter, o que não dá tempo de fazer antes do gatilho). Com o parâmetro em 0, a caixa liga a compensação ao vivo.

Sequência da malha fechada (bloco B): degrau de referência de 1,0 para 1,5 A em 0,15 s; afundamento de 10 % na tensão (Δd = −0,1) de 0,25 a 0,30 s; pulso de carga de 0,33 a 0,39 s.
Varreduras (bloco C): 4 níveis de 0,1 s a partir de 0,1 s; em cada nível, degrau de 1,0 para 1,5 A e afundamento. Níveis: zero não compensado 0/20/50/150 mV; filtro RC 15/3/1/0,3 kHz; ruído 10/100/300/1000 mV.

### Capturas

| Item | CSV | Bloco | Caixas (as demais no padrão) | Preset | Resultado esperado |
|---|---|---|---|---|---|
| 4 | `e3_a` | A, `g07_modo = 1` | — | Item4_malha_aberta | viés da medida real ≈ 0,5 mA; erro ≈ 58 mA rms; atraso 60 µs; zero sem correção 75 mA |
| 4 | `e3_b` | A, `g07_modo = 2` | — | Item4_malha_aberta | corrente nula: real ≈ 1 mA (sem correção: 75 mA) |
| 4 | `e3_c` | A, `g07_modo = 3` | — | Item4_malha_aberta | Δi eficaz ≈ 0,21 A, ideal e real |
| 5 | `e4_r3_ideal` | B | `G07_fb_real` = 0 | Default | planta 1,491 A; acomodação 1,4 ms; sobressinal 5 % |
| 6 | `e4_r3_real` | B | `G07_fb_real` = 1 | Default | medida 1,500 A; planta ≈ 1,478 A |
| 7 | `e4_r4_zero` | C, `g07_cl_ens = 2` | — | R4_varredura | planta 1,48 / 1,38 / 1,22 / 0 A |
| 7 | `e4_r4_rc` | C, `g07_cl_ens = 3` | — | R4_varredura | 1,48 / 1,49 / 1,50 / 1,91 A |
| 7 | `e4_r4_ruido` | C, `g07_cl_ens = 4` | — | R4_varredura | 1,48 / 1,32 / 0,89 / 0,03 A |
| 8 | `e4_r5_autocal` | C, `g07_cl_ens = 2` | `G07_autocal` = 1 | R4_varredura | 1,47–1,48 A em todos os níveis |
| 8 | `final_r3` | B com `g07_hall0 = 1`, `g07_comp0 = 1` | — | Default | planta 1,489 A (erro 11 mA); acomodação 2,2 ms; sobressinal 8 % |
| 8 | `final_ruido_hall` | C, `g07_cl_ens = 4`, `g07_hall0 = 1` | — | R4_varredura | erro 17 / 34 / 219 / 687 mA |
| 8 | `final_rc_hall` | C, `g07_cl_ens = 3`, `g07_hall0 = 1` | — | R4_varredura | erro 17 / 9 / −1 / −556 mA |
| 8 | `final_rc_hall_comp` | C, `g07_cl_ens = 3`, `g07_hall0 = 1`, `g07_comp0 = 1` | — | R4_varredura | erro 14 / 15 / 38 / −105 mA |

Os CSV `e3_*` foram gravados com o modelo da Entrega 03 e os `e4_*` com o da Entrega 04. O `modelo_final.tse` contém os dois sem alteração nesses caminhos (as caixas novas ficam em 0), então os mesmos blocos reproduzem os mesmos resultados.

## Previsões do item 8 (registradas em 22/11/2026, antes das capturas `final_*`)

Feitas a partir das fórmulas do relatório e das capturas da Entrega 04:

- **`final_r3`** (sequência B com as duas compensações): planta ≈ 1,491 A (erro ≈ 9 mA, o mesmo da medição ideal, vindo da FCEM em rampa); medida ≈ planta; `G07_cl_hall_ideal` = `G07_cl_planta` (confere a tabela de setores); sobressinal ≈ 7 %; desvio de d ≈ 0,050.
- **`final_ruido_hall`**: sem retificação, o ruído deixa de gerar viés. Planta ≈ 1,50 A com 10 e 100 mV; o erro só falha quando a razão cíclica satura (acima de 300 mV). Em troca, o ruído realimentado cresce 1,4 vez (a fase c, calculada, tem o dobro da variância): o sobressinal passa a falhar com ≈ 19 mV (antes 25 mV), o esforço com ≈ 37 mV (antes 58 mV) e a rejeição com ≈ 185 mV (antes 220 mV). O limite mais exigente passa de 15 mV (erro) para ≈ 19 mV (sobressinal).
- **`final_rc_hall`** (sem correção do RC): planta = 1,5/|H(f_e)| = 1,500 / 1,505 / 1,545 / 1,94 A; o erro falha a partir de f_c ≈ 1,2 kHz.
- **`final_rc_hall_comp`**: planta ≈ 1,50 A nos 4 níveis; o erro deixa de falhar até 0,3 kHz. O atraso do filtro não é corrigido, então o sobressinal continua falhando perto de 0,8 kHz.

### Resultado do item 8 contra as previsões

- `final_r3`: planta 11 mA abaixo da referência (previsto ≈ 9 mA); seleção pela posição sobre as correntes verdadeiras = planta (0,2 mA). Confirmado.
- `final_ruido_hall`: o erro falha a partir de 78 mV (antes 15 mV; previsto > 300 mV, mas a razão cíclica começa a saturar já com 100 mV). Sobressinal falha com 17 mV (previsto ≈ 19 mV): o limite global passa de 15 para 17 mV. Esforço falha com 64 mV (previsto ≈ 37 mV).
- `final_rc_hall`: o erro falha a partir de 0,96 kHz (previsto ≈ 1,2 kHz).
- `final_rc_hall_comp`: **previsão errada**. A correção por |H(f_e)| ajuda com 0,3 kHz (556 → 105 mA), mas piora com 1 kHz (1 → 38 mA), e a ruptura sobe para 1,7 kHz: a medida pela posição lê cada fase depois que o filtro já assentou, então não há atenuação a corrigir quando τ_RC é bem menor que um setor.

## Demonstração ao vivo (sequência B rodando)

- `G07_fb_real` 0 → 1: o mesmo PI, a planta cai de 1,491 para ≈ 1,478 A (comparar `G07_cl_med` com `G07_cl_planta`).
- `G07_hall` = 1 (com `g07_hall0 = 0`): a planta sobe para ≈ 1,49 A.
- `G07_ruido` = 100: com `G07_hall` = 0 a planta cai para ≈ 1,33 A; com `G07_hall` = 1 fica em ≈ 1,47 A, mais ruidosa.
- `G07_fc_rc` = 0.3: a planta sobe para ≈ 1,9 A; `G07_comp_rc` = 1 a traz para ≈ 1,6 A.
- `G07_corr` = 0: o zero deixa de ser descontado e a planta cai ≈ 65 mA.

Ao terminar, voltar as caixas ao padrão e o bloco ao B.
