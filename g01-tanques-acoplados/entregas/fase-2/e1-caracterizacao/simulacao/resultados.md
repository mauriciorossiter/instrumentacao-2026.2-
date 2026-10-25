# Resultados — Fase 2, Entrega 01 (G01)

> Parâmetros: Tabela 1 do relatório da Atividade 01 (valores de referência do dossiê do sistema, adotados para simulação; não identificados experimentalmente).

Simulação: solve_ivp RK45, passo máx. 0.1 s, rtol 1e-08, atol 1e-10. Tempos medidos na saída densa do integrador (instante exato do cruzamento), normalizados pelo equilíbrio não linear analítico.

## Parâmetros

| Símbolo | Valor | Unidade |
|---|---|---|
| A1 | 0.5 | m² |
| A2 | 0.5 | m² |
| k1 | 0.01 | m^2,5/s |
| k2 | 0.01 | m^2,5/s |
| q0 | 0.01 | m³/s |
| hmin | 0.1 | m |
| hmax | 1.2 | m |

## R2 — Análise algébrica (ponto nominal)

| Grandeza | Valor | Observação |
|---|---|---|
| h̄1 = (q̄/k1)² | 1.0000 m | equilíbrio exato (não linear) |
| h̄2 = (q̄/k2)² | 1.0000 m | equilíbrio exato (não linear) |
| τ1 = 2A1√h̄1/k1 | 100.00 s | linearização local |
| τ2 = 2A2√h̄2/k2 | 100.00 s | linearização local |
| polos λ1, λ2 | -0.01000, -0.01000 s⁻¹ | reais negativos |
| Kdc (δh2/δq) = 2q̄/k2² | 200.00 s/m² (= m por m³/s) | linearização local |
| Kdc (δh1/δq) = 2q̄/k1² | 200.00 s/m² | linearização local |
| ζ = (τ1+τ2)/(2√(τ1τ2)) | 1.000 | = 1: criticamente amortecido (polo duplo) |
| ωn = 1/√(τ1τ2) | 0.0100 rad/s | parâmetro do polinômio; não há oscilação |
| sobressinal | não se aplica | polos reais |
| t63 (h2) | 214.57 s | linearizado |
| tr 10–90 % (h2) | 335.79 s | linearizado |
| ts 2 % (h2) | 583.39 s | linearizado, banda ±2 % da variação |

## R4 — Validação cruzada

Colunas: (L) modelo linearizado, analítico; (NL) modelo não linear, analítico (só existe para equilíbrios); (S) simulação numérica do modelo não linear.

| Grandeza | L | NL | S | S×L | S×NL |
|---|---|---|---|---|---|
| h̄2 inicial (m) | — | 1.0000 | 1.0000 | — | 0.000 % |
| h2(∞), degrau 1 % (m) | 1.0200 | 1.0201 | 1.0201 | 0.010 % | -0.0000 % |
| h2(∞), degrau 5 % (m) | 1.1000 | 1.1025 | 1.1025 | 0.227 % | -0.0000 % |
| K efetivo = Δh2/Δq, degrau 1 % (s/m²) | 200.00 | 201.00 | 201.00 | 0.50 % | -0.0000 % |
| K efetivo = Δh2/Δq, degrau 5 % (s/m²) | 200.00 | 205.00 | 205.00 | 2.50 % | -0.0000 % |
| τ1 (s), decaimento de h1 em R3(b) | 100.00 | — | 100.03 | 0.03 % | — |
| t63 (s), degrau 1 % | 214.57 | — | 215.96 | 0.65 % | — |
| t63 (s), degrau 5 % | 214.57 | — | 221.54 | 3.25 % | — |
| tr 10–90 % (s), degrau 1 % | 335.79 | — | 338.69 | 0.86 % | — |
| tr 10–90 % (s), degrau 5 % | 335.79 | — | 350.30 | 4.32 % | — |
| ts 2 % (s), degrau 1 % | 583.39 | — | 588.49 | 0.87 % | — |
| ts 2 % (s), degrau 5 % | 583.39 | — | 608.90 | 4.37 % | — |
| pico de δh2 no pulso (m) | 0.0440 em 115.7 s | — | 0.0439 em 118.0 s | -0.29 % | — |
| pico de h1 no pulso (m) | — | — | 1.1039 em 30.0 s | — | — |
| sobressinal, degrau 5 % | 0 | — | 0.0000 % | — | — |

## Convergência numérica (degrau de +5 %, modelo não linear)

| passo máx. (s) | rtol | atol | h2(∞) (m) | erro vs NL analítico (m) | t63 (s) | tr (s) | ts 2 % (s) |
|---|---|---|---|---|---|---|---|
| 0.1 | 1e-06 | 1e-08 | 1.102500 | -1.1e-08 | 221.54 | 350.30 | 608.90 |
| 0.1 | 1e-08 | 1e-10 | 1.102500 | -1.1e-08 | 221.54 | 350.30 | 608.90 |
| 0.05 | 1e-08 | 1e-10 | 1.102500 | -1.1e-08 | 221.54 | 350.30 | 608.90 |
| 0.01 | 1e-10 | 1e-12 | 1.102500 | -1.1e-08 | 221.54 | 350.30 | 608.90 |

## R5 — Sensibilidade paramétrica (degrau de +5 % a partir do equilíbrio de cada caso)

Domínio adotado: 0.1 m ≤ h1, h2 ≤ 1.2 m. Casos fora dele são extrapolações matemáticas do modelo, não operações da planta; seus tempos não são medições de operação válida.

### k2 (coef. do orifício de saída do T2)

| nível | h̄1 [m] | h̄2 [m] | τ1 [s] | τ2 [s] | Kdc [s/m²] | ts 2 % lin. [s] | ts 2 % sim. [s] | domínio |
|---|---|---|---|---|---|---|---|---|
| ×0.25 | 1 | 16 | 100.0 | 1600.0 | 3200 | 6362 | (6639) | extrapolação: equilíbrio fora do domínio |
| ×0.5 | 1 | 4 | 100.0 | 400.0 | 800 | 1680 | (1752) | extrapolação: equilíbrio fora do domínio |
| ×1 | 1 | 1 | 100.0 | 100.0 | 200 | 583 | 609 | válido |
| ×2 | 1 | 0.25 | 100.0 | 25.0 | 50 | 420 | 439 | válido |
| ×3 | 1 | 0.1111 | 100.0 | 11.1 | 22.22 | 403 | 421 | válido |
| ×4 | 1 | 0.0625 | 100.0 | 6.2 | 12.5 | 398 | (415) | extrapolação: equilíbrio fora do domínio |

### A2 (área transversal do T2)

| nível | h̄1 [m] | h̄2 [m] | τ1 [s] | τ2 [s] | Kdc [s/m²] | ts 2 % lin. [s] | ts 2 % sim. [s] | domínio |
|---|---|---|---|---|---|---|---|---|
| ×0.25 | 1 | 1 | 100.0 | 25.0 | 200 | 420 | 439 | válido |
| ×0.5 | 1 | 1 | 100.0 | 50.0 | 200 | 460 | 480 | válido |
| ×1 | 1 | 1 | 100.0 | 100.0 | 200 | 583 | 609 | válido |
| ×2 | 1 | 1 | 100.0 | 200.0 | 200 | 920 | 959 | válido |
| ×4 | 1 | 1 | 100.0 | 400.0 | 200 | 1680 | 1752 | válido |

### q̄in (vazão de operação)

| nível | h̄1 [m] | h̄2 [m] | τ1 [s] | τ2 [s] | Kdc [s/m²] | ts 2 % lin. [s] | ts 2 % sim. [s] | domínio |
|---|---|---|---|---|---|---|---|---|
| ×0.25 | 0.0625 | 0.0625 | 25.0 | 25.0 | 50 | 146 | (152) | extrapolação: equilíbrio fora do domínio |
| ×0.5 | 0.25 | 0.25 | 50.0 | 50.0 | 100 | 292 | 304 | válido |
| ×0.75 | 0.5625 | 0.5625 | 75.0 | 75.0 | 150 | 438 | 457 | válido |
| ×1 | 1 | 1 | 100.0 | 100.0 | 200 | 583 | 609 | válido |
| ×2 | 4 | 4 | 200.0 | 200.0 | 400 | 1167 | (1218) | extrapolação: equilíbrio fora do domínio |
| ×4 | 16 | 16 | 400.0 | 400.0 | 800 | 2334 | (2436) | extrapolação: equilíbrio fora do domínio |

### k1 (coef. do orifício T1→T2)

| nível | h̄1 [m] | h̄2 [m] | τ1 [s] | τ2 [s] | Kdc [s/m²] | ts 2 % lin. [s] | ts 2 % sim. [s] | domínio |
|---|---|---|---|---|---|---|---|---|
| ×0.25 | 16 | 1 | 1600.0 | 100.0 | 200 | 6362 | (6642) | extrapolação: equilíbrio fora do domínio |
| ×0.5 | 4 | 1 | 400.0 | 100.0 | 200 | 1680 | (1754) | extrapolação: equilíbrio fora do domínio |
| ×1 | 1 | 1 | 100.0 | 100.0 | 200 | 583 | 609 | válido |
| ×2 | 0.25 | 1 | 25.0 | 100.0 | 200 | 420 | 438 | válido |
| ×3 | 0.1111 | 1 | 11.1 | 100.0 | 200 | 403 | 420 | válido |
| ×4 | 0.0625 | 1 | 6.2 | 100.0 | 200 | 398 | (415) | extrapolação: equilíbrio fora do domínio |


## Ordem de convergência do RK4

Referência DOP853, rtol=1e-13, atol=1e-15, passo máximo de 5 s; comparação em 300 s.

| Δt (s) | Erro em h2 (m) |
|---|---|
| 10 | 1.553064e-08 |
| 5 | 9.005150e-10 |
| 2.5 | 5.418888e-11 |
| 1.25 | 3.322898e-12 |
| 0.625 | 2.060574e-13 |

Ordem medida: **4.0486**.


## Balanço integral de massa

Integração simultânea de h1, h2, volume de entrada e volume de saída.

| Ensaio | Resíduo máximo (m³) | Volume de entrada (m³) | Resíduo relativo |
|---|---|---|---|
| degrau | 4.835243e-12 | 21.000000 | 2.302497e-13 |
| condição inicial | 5.019984e-12 | 20.000000 | 2.509992e-13 |
| pulso | 5.165646e-12 | 20.060000 | 2.575098e-13 |

## R5.4 — Amplitude do degrau

| Degrau (%) | Kef (s/m²) | Kef/Kdc | Exato 1+δ/2 | ts (s) | ts/ts,lin |
|---|---|---|---|---|---|
| -30 | 170.000000 | 0.850000 | 0.850000 | 433.025 | 0.742254 |
| -20 | 180.000000 | 0.900000 | 0.900000 | 482.528 | 0.827107 |
| -10 | 189.999999 | 0.950000 | 0.950000 | 532.698 | 0.913104 |
| -5 | 194.999997 | 0.975000 | 0.975000 | 557.987 | 0.956452 |
| +1 | 200.999990 | 1.005000 | 1.005000 | 588.486 | 1.008732 |
| +5 | 204.999979 | 1.025000 | 1.025000 | 608.902 | 1.043727 |
| +9 | 208.999958 | 1.045000 | 1.045000 | 629.379 | 1.078826 |

## R5.5 — Elasticidades no ponto nominal

Diferença central: ±0,01% no linearizado; entre parênteses, ±10% no parâmetro e degrau de 1% no não linear. Esses testes locais podem extrapolar o domínio físico.

| Métrica | A1 | A2 | k1 | k2 | q0 |
|---|---|---|---|---|---|
| h2 | +0.000 | +0.000 | +0.000 | -2.000 | +2.000 |
| K2 | +0.000 (-0.000) | +0.000 (-0.000) | +0.000 (-0.000) | -2.000 (-2.041) | +1.000 (+1.000) |
| t1 | +1.000 | +0.000 | -2.000 | +0.000 | +1.000 |
| t2 | +0.000 | +1.000 | +0.000 | -2.000 | +1.000 |
| t63 | +0.500 (+0.500) | +0.500 (+0.500) | -1.000 (-1.017) | -1.000 (-1.018) | +1.000 (+1.000) |
| ts | +0.500 (+0.500) | +0.500 (+0.499) | -1.000 (-1.030) | -1.000 (-1.029) | +1.000 (+1.000) |


## Verificações das hipóteses H2-H5

H2/H3: estimativa ilustrativa com c entre 0,6 e 1,0, g=9,81 m/s² e viscosidade cinemática de 1e-6 m²/s. Esses valores não entram nas EDOs da planta.

Área estimada do orifício: 0.00225762 a 0.0037627 m²; diâmetro: 0.05361 a 0.06922 m.
Reynolds ilustrativo: 75098.2 a 335849.6; máximo de (a/A1)² = 5.66316e-05.

H4: bomba de primeira ordem, partindo da vazão nominal, com degrau de +5%.

| tau da bomba (s) | ts de h2 (s) | Aumento sobre a bomba ideal (%) |
|---|---|---|
| 1 | 609.907 | 0.1650 |
| 5 | 614.009 | 0.8388 |
| 10 | 619.341 | 1.7144 |

H5: com descarga afogada, o equilíbrio exigiria h1 = h2 + (qi/k1)² = 2.00 m, acima de hmax = 1.20 m.
