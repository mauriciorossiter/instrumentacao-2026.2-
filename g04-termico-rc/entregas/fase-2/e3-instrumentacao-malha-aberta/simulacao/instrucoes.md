# Instruções de reprodução — Instrumentação em malha aberta (G04)

Ferramenta: Typhoon HIL Control Center 2026.3.

## Parâmetros da planta

Equivalente elétrico do sistema térmico RC de quatro ramos (IGBT IKD04N60RF, datasheet v2.6, Fig. 21), com escala elétrica:

| Ramo i | Rᵢ [K/W] | τᵢ [s] | Cᵢ [J/K] | R_eq [Ω] | C_eq [F] |
|---|---|---|---|---|---|
| 1 | 0,492466 | 2,0 × 10⁻⁴ | 4,0612 × 10⁻⁴ | 4,92466 | 4,0612 × 10⁻⁶ |
| 2 | 0,884411 | 5,4 × 10⁻⁴ | 6,1058 × 10⁻⁴ | 8,84411 | 6,1058 × 10⁻⁶ |
| 3 | 0,589157 | 2,1 × 10⁻³ | 3,5644 × 10⁻³ | 5,89157 | 3,5644 × 10⁻⁵ |
| 4 | 0,073673 | 3,1658 × 10⁻² | 4,2971 × 10⁻¹ | 0,73673 | 4,2971 × 10⁻³ |

Escala: **0,1 V ≡ 1 K** de elevação térmica; **0,01 A ≡ 1 W** de potência.

Cápsula fixa: Tc = 298,15 K. Potência nominal: 10 W.

## Cadeia de instrumentação

Além da planta RC elétrica, cada modelo inclui:

1. **Sensor (termopar)**
   - Dinâmica térmica de primeira ordem (`Tau_sensor_s` ≈ 3 ms).
   - Desvio de offset (`Desvio_sensor_C` = 0,3 K).
   - Não-linearidade NIST do termopar tipo T.
   - Compensação de junta fria.

2. **Condicionamento analógico**
   - Fonte termoelétrica equivalente.
   - Cabo de 10 Ω.
   - Offset de entrada (`Vos_uV` = 10 µV) e interferência senoidal de 20 kHz.
   - Amplificador com ganho selecionável em quatro níveis.
   - Filtro anti-alias RC de 5 kHz.

3. **ADC e processamento digital**
   - Conversor de 12 bits, 3,3 V, 100 kS/s.
   - Quantização, limites e conversão de código para tensão.
   - Correção NIST inversa com compensação de junta fria.

Todos os blocos são nativos da biblioteca Typhoon (sem C function).

## Arquivos incluídos

- `G04_E03_degrau.tse`: resposta ao degrau de 10 W com instrumentação.
- `G04_E03_livre.tse`: resposta livre com instrumentação.
- `G04_E03_pulso.tse`: resposta ao pulso de 10 W com instrumentação.
- `G04_Fase2_Entrega03.cus`: painel SCADA com botões para seleção dos casos.

## Como rodar no Typhoon HIL

### Modelos `.tse`

1. Abra o **Typhoon HIL Control Center**.
2. Selecione **File → Open** e carregue o arquivo `.tse` desejado.
3. Clique em **Run TyphoonSim**.
4. Após a simulação, abra os Scopes disponíveis para visualizar os sinais.

Sinais principais:
- `T_planta_K`: temperatura real da junção (planta).
- `T_real_K`: temperatura estimada pelo sistema de instrumentação.
- `V_ADC_V`: tensão amostrada pelo ADC.
- `Medicao_valida`: sinal de inicialização concluída.

### Painel SCADA `.cus`

1. No Typhoon HIL Control Center, abra o arquivo `G04_Fase2_Entrega03.cus` em **HIL SCADA**.
2. Inicie a simulação.
3. Use os botões `DEGRAU`, `LIVRE` e `PULSO` para carregar o caso desejado.

## Observações

- A instrumentação opera em malha aberta: o sensor não altera a planta térmica.
- As entradas SCADA permitem ativar/desativar efeitos individuais (dinâmica do sensor, não-linearidade, offset, interferência, filtro, ADC, erro de CJC, correção NIST).
- A resposta livre inicia com condição inicial equivalente a 10 W de pré-aquecimento.
