# Instruções de reprodução — Simulação térmica RC (G04)

Ferramenta: Typhoon HIL Control Center 2026.3.

## Parâmetros da planta

Sistema térmico RC de quatro ramos, equivalente Foster do IGBT IKD04N60RF (datasheet v2.6, Fig. 21):

| Ramo i | Rᵢ [K/W] | τᵢ [s] | Cᵢ = τᵢ/Rᵢ [J/K] |
|---|---|---|---|
| 1 | 0,492466 | 2,0 × 10⁻⁴ | 4,0612 × 10⁻⁴ |
| 2 | 0,884411 | 5,4 × 10⁻⁴ | 6,1058 × 10⁻⁴ |
| 3 | 0,589157 | 2,1 × 10⁻³ | 3,5644 × 10⁻³ |
| 4 | 0,073673 | 3,1658 × 10⁻² | 4,2971 × 10⁻¹ |

Cápsula fixa: Tc = 298,15 K. Potência nominal: 10 W (exceto extrapolação de 100 W).

## Arquivos incluídos

- `G04_<caso>.tse`: modelo para o Typhoon HIL Schematic Editor (16 casos).

Casos disponíveis:

| Arquivo | Descrição |
|---|---|
| `G04_degrau_4r.tse` | Resposta ao degrau de 10 W — 4 ramos |
| `G04_degrau_2r.tse` | Resposta ao degrau de 10 W — 2 ramos |
| `G04_livre_4r.tse` | Resposta livre — 4 ramos |
| `G04_livre_2r.tse` | Resposta livre — 2 ramos |
| `G04_pulso_4r.tse` | Resposta ao pulso de 10 W — 4 ramos |
| `G04_pulso_2r.tse` | Resposta ao pulso de 10 W — 2 ramos |
| `G04_potencia_100W.tse` | Degrau de 100 W (extrapolação numérica) |
| `G04_R1_x0.2.tse`, `G04_R1_x1.tse`, `G04_R1_x5.tse` | Sensibilidade em R₁ |
| `G04_C1_x0.2.tse`, `G04_C1_x1.tse`, `G04_C1_x5.tse` | Sensibilidade em C₁ |
| `G04_R4_x0.2.tse`, `G04_R4_x1.tse`, `G04_R4_x5.tse` | Sensibilidade em R₄ |

## Como rodar no Typhoon HIL

1. Abra o **Typhoon HIL Control Center**.
2. No menu, selecione **File → Open** e carregue o arquivo `.tse` desejado.
3. Clique em **Run TyphoonSim** (botão verde na barra superior).
4. Após a simulação, abra o **Scope** chamado `Resultados`.
5. O sinal `T_j_K` mostra a temperatura da junção em kelvin; o eixo horizontal está em segundos.

Repita o processo para cada caso que deseja observar.

## Observações

- A extrapolação de 100 W é apenas numérica; não representa operação física segura do componente.
- O adaptador elétrico de 1 V/K no Typhoon serve apenas para observação; ele não carrega a planta térmica.
- Todos os arquivos `.tse` usam um único bloco nativo *Thermal network (Foster)*, sem C function.
