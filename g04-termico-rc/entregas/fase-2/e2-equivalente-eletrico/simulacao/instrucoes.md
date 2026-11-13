# Instruções de reprodução — Equivalente elétrico RC (G04)

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

## Arquivos incluídos

- `G04_E02_degrau.tse`: resposta ao degrau de 10 W.
- `G04_E02_livre.tse`: resposta livre a partir de condição inicial não nula.
- `G04_E02_pulso.tse`: resposta ao pulso de 10 W.
- `G04_Fase2_Entrega02.cus`: painel SCADA com botões para seleção dos casos.

## Como rodar no Typhoon HIL

### Modelos `.tse`

1. Abra o **Typhoon HIL Control Center**.
2. Selecione **File → Open** e carregue o arquivo `.tse` desejado.
3. Clique em **Run TyphoonSim**.
4. Após a simulação, abra o **Scope** `Resultados_offline`.

Sinais principais:
- `T_planta_K`: temperatura da junção em kelvin.
- `P_W`: potência térmica aplicada em watts.
- `theta1_K` a `theta4_K`: elevação térmica de cada ramo RC.

### Painel SCADA `.cus`

1. No Typhoon HIL Control Center, abra o arquivo `G04_Fase2_Entrega02.cus` em **HIL SCADA**.
2. Inicie a simulação.
3. Use os botões `DEGRAU`, `LIVRE` e `PULSO` para carregar o caso desejado.

## Observações

- A planta usa componentes elétricos nativos (resistores e capacitores) para emular a rede térmica Foster.
- O modelo não contém C functions.
- A resposta livre inicia com condição inicial nos capacitores equivalente a 10 W de pré-aquecimento.
