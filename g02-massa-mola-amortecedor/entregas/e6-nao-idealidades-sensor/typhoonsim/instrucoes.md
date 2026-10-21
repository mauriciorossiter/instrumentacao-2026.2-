# Entrega 02 — Não idealidades do sensor (TyphoonSim)

ECOM060 Instrumentação Eletrônica · UFAL · 2026.2 · Grupo 02

## Visão geral

A cadeia de medição de força da Entrega 01 é: força em degraus de 0,2 N rms modulada a 100 Hz → disco piezoelétrico
Murata 7BB-20-6 (equivalente de Thévenin `Ct`–`Rin`) → pré-amplificador ×25 → amplificador síncrono (lock-in) com
Butterworth de 2ª ordem em 1 Hz, constante `K = 1 V/N`. Nesta entrega, três camadas de não idealidade do sensor foram
acrescentadas: R6 (estática), R7 (dinâmica passa-alta) e R8 (espectral/chopagem). O R9 compara as camadas isoladas, e
o R10 liga as três ao mesmo tempo. Todos os modelos foram feitos no TyphoonSim 2026.2.

## Arquivos

| Arquivo | Nome original (citado no relatório) | Camada |
|---|---|---|
| `modelo-r6.tse` | `entrega2_E02_R6.tse` | R6 — camada estática (sensibilidade, limiar, resolução) |
| `modelo-r7.tse` | `entrega2_E02_R7.tse` | R7 — camada dinâmica: ramo extra sem chopagem (passa-alta do piezo) |
| `modelo-r8.tse` | `entrega2_E02_R8.tse` | R8 — camada espectral: offset, deriva, 60 Hz e ruído branco |
| `modelo.tse` | `entrega2_E02_R10.tse` | R10 — três camadas em série (sinal degradado + condicionamento) |

Relatórios em `../relatorio/`: `relatorio.pdf` (principal), `relatorio-r6-camada-estatica.pdf` (R6 detalhado) e
`apresentacao.pdf` (slides). O R9 não tem modelo próprio: é a comparação dos resultados de R6, R7 e R8.

## Topologia

Áreas do esquemático (mesma estrutura em todos os modelos):

1. **Force Input Signal (N)**: cinco blocos `Step` (`0,2` … `1,0`), cada um somando 0,2 N, em t = 1, 3, 5, 7 e 9 s →
   `Sum1` (amplitude rms, probe `Videal`) → `Product1` com a senoide `100Hz` (amplitude 1,4142) → força instantânea
   `F(t) = √2·F·sin(2π·100·t)` (probe `F_inst`).
2. **Piezo Model**: C function `camada_estatica` (substitui o antigo `Gain1`) → `vctrl` comanda a fonte `Vsp1`
   → `Ct` em série → `Rin` para o terra. A tensão sobre `Rin` é medida por `OutputVoltage`.
3. **Noise** (R6, R7) / **Noise + Interf. (R8)** (R8, R10): `Sum2` soma `OutputVoltage` + `WhiteNoise.n`
   (+ `interferencia.interf` no R8/R10).
4. **Amplifier Lock In**: `Sum2` → ganho `gain = (1+24e3*1e-3)` = 25 (probe `preAmp`) → `Product2` com a referência
   `100Hz1` (amplitude 1,4142; probe `deMod`) → `ButterWorth fc = 1Hz` → probe `ButterWorthOut`.
5. **Somente R7 — "R7: Piezo sem chopagem (forca direta, passa-alta)"**: `Videal` (força em degrau, sem modulação)
   → ganho `S_nom` = 0,04 (probe `v_ideal_dc`) → fonte `Vsp2` → `Ct2` → `Rin2` → terra; tensão sobre `Rin2` medida
   por `V_semchop`.

## Valores dos elementos

| Elemento | Valor | Observação |
|---|---|---|
| `Ct`, `Ct2` | 10 nF | Murata 7BB-20-6, 10 nF ±30 % a 1 kHz |
| `Rin`, `Rin2` | 10 MΩ | τ = Rin·Ct = 0,1 s, fc = 1,59 Hz |
| Degraus de força | 0,2 N cada, em t = 1, 3, 5, 7, 9 s | 0 a 1 N rms |
| Portadora `100Hz` / referência `100Hz1` | 100 Hz, amplitude 1,4142 | modulação e demodulação |
| Pré-amplificador | G1 = 1 + 24 kΩ/1 kΩ = 25 | bloco `Gain` |
| Butterworth | `1 / (0,025538 s² + 0,226 s + 1)` | fc = 1 Hz, domínio s |
| `S_NOM` | 0,04 V/N | 400 pC/N / 10 nF (Entrega 01) |
| `D33_REAL`, `CT_REAL` | 320 pC/N, 13 nF | pior caso inferior: S_mín = 24,6 mV/N (−38 %) |
| Caso máximo (alternativo) | 480 pC/N, 7 nF | S_máx = 68,6 mV/N (+71 %) |
| `F_LIM`, `F_RES` | 0,02 N, 0,01 N | estimativas da equipe |
| `SIGMA_N` (ruído branco) | 20 mV (R6, R8, R10); 0 (R7) | retido a cada 10⁻⁴ s |
| `A_OFF_I` | 3 mV | V_IO típico do TL072 |
| `A_DRIFT_I`, `F_DRIFT_I` | 5 mV, 0,05 Hz | estimativa da equipe (piroeletricidade do PZT) |
| `A_HUM_I` | 20 mV de pico, 60 Hz | estimativa da equipe (entrada de 10 MΩ sem blindagem) |
| Tempo de simulação | 10 s (R6); 11 s (R7, R8, R10) | |

## Elementos não lineares / blocos C function

**`camada_estatica`** (execution rate 1 µs; entrada `F`, saída `vctrl`). Chaves `EN_SENS`, `EN_LIM`, `EN_RES` na aba
*Global variables*. Os efeitos são aplicados nesta ordem:

```c
S_use = EN_SENS ? D33_REAL / CT_REAL : S_NOM;      /* sensibilidade */
F_a = F;
if (EN_LIM && fabs(F_a) < F_LIM) F_a = 0.0;          /* limiar (zona morta) */
if (EN_RES) F_a = F_RES * floor(F_a / F_RES + 0.5);  /* resolução (quantização) */
vctrl = S_use * F_a;
```

Com as três chaves em 0 o bloco equivale ao ganho ideal da Entrega 01. Como o limiar atua sobre o valor instantâneo,
uma força só produz saída se `F_rms > F_LIM/√2 = 0,014 N rms`.

**`interferencia`** (R8 e R10; execution rate 10⁻⁴ s; chaves `EN_OFF_I`, `EN_DRIFT_I`, `EN_HUM_I`):

```c
interf = EN_OFF_I*A_OFF_I + EN_DRIFT_I*A_DRIFT_I*sin(2π·F_DRIFT_I·t) + EN_HUM_I*A_HUM_I*sin(2π·60·t);
```

**`WhiteNoise`** (10⁻⁴ s): gerador xorshift32 com semente fixa (610839777) + Box-Muller, `n = SIGMA_N·g`, `g ~ N(0,1)`.
O código foi corrigido em relação à Entrega 01 (antes ficava todo na aba *Output* e gerava um offset constante de
−47,3 mV); agora está distribuído nas abas *Global*, *Init*, *Output* e *Update*.

A demodulação (`Product2`) também é não linear: `√2F·sin(ωt) · √2·sin(ωt) = F − F·cos(2ωt)`; o Butterworth de 1 Hz
remove o termo em 200 Hz.

## Como executar cada ensaio

Em todos os casos: abrir o `.tse` no TyphoonSim 2026.2, compilar, simular e observar os sinais no `Scope1`. Chaves e
parâmetros são editados na aba *Global variables* de cada C function (recompilar depois de editar). A métrica dos
relatórios é a média de `ButterWorthOut` no último 0,8 s de cada patamar.

**R6 — `modelo-r6.tse`** (padrão: `EN_SENS = EN_LIM = EN_RES = 1`, ruído σ = 20 mV). Sinais: `Videal`, `F_inst`,
`vctrl`, `OutputVoltage`, `preAmp`, `ButterWorthOut`. Ensaios (ruído desligado, `SIGMA_N = 0`):

| ID | (SENS, LIM, RES) | Degrau | Objetivo |
|---|---|---|---|
| T0 | 0, 0, 0 | 0,2 N | linha de base (cadeia ideal) |
| T1 | 1, 0, 0 | 0,2 N | sensibilidade mínima (24,6 mV/N) |
| T1b | 1, 0, 0 com `D33_REAL = 480e-12`, `CT_REAL = 7e-9` | 0,2 N | sensibilidade máxima (68,6 mV/N) |
| T2 | 0, 1, 1 | 0,01 N | limiar + resolução |
| T2a | 0, 1, 0 | 0,01 N | só limiar |
| T2b | 0, 0, 1 | 0,01 N | só resolução |
| T3 | 1, 1, 1 | 0,2 N | camada estática completa |

Para degraus de 0,01 N, alterar `final_value` dos cinco blocos `Step` de 0.2 para 0.01.

**R7 — `modelo-r7.tse`** (camada estática desligada, `SIGMA_N = 0`). Comparar `V_semchop` (degrau aplicado direto ao
piezo `Ct2`–`Rin2`, sem chopagem) com `v_ideal_dc`, e `ButterWorthOut` (mesma força com chopagem) com `Videal`.

**R8 — `modelo-r8.tse`** (camada estática desligada; `interferencia` e ruído branco σ = 20 mV ligados). Observar
`preAmp` (sinal enterrado em ruído e interferência) e `ButterWorthOut` × `Videal`. Cada interferência pode ser
desligada pelas chaves `EN_OFF_I`, `EN_DRIFT_I`, `EN_HUM_I`.

**R10 — `modelo.tse`** (todas as camadas ligadas: `EN_SENS = EN_LIM = EN_RES = 1`, interferências e ruído ligados).
Observar `ButterWorthOut` × `Videal`. O modelo não tem bloco de calibração: a correção de um ponto é multiplicar
`ButterWorthOut` por 1,625 = S_nom/S_mín.

## Resultados esperados

- **R6**: erro de ganho puro de −38,5 % (S_mín) e +71,3 % (S_máx), constante em todos os patamares. T3 (referência
  numérica): 0,123 / 0,246 / 0,369 / 0,492 / 0,606 V; rodada no TyphoonSim com ruído: 0,127 / 0,247 / 0,367 / 0,494 /
  0,615 V. Relação de pico `vctrl`/`F_inst` medida: 24,8 mV/N. Tensão de pico sobre `Rin` no 2º patamar: 14,01 mV
  (TyphoonSim) contra 14,04 mV (referência), diferença de 0,2 %. Com degraus de 0,01 N, o limiar zera a saída no
  patamar 1 (−100 %) e dá −18,5 % no patamar 2; a resolução sozinha dá −15,9 % no patamar 1. Ruído corrigido: média
  0,03 mV, σ = 19,98 mV.
- **R7**: sem chopagem, cada degrau de 8 mV decai a 0,05 mV em 0,5 s (τ = 0,1 s). Com portadora de 100 Hz o
  passa-alta tem ganho 0,9999 e avanço de fase de 0,9°.
- **R8**: patamares 0,196 / 0,400 / 0,606 / 0,805 / 1,007 V (ideal 0,2 a 1,0 V); desvio residual de 7,45 mV rms,
  devido ao ruído branco em torno de 100 Hz; as interferências (deslocadas para 40, 100 e 160 Hz e atenuadas de 10³ a
  10⁵ vezes) contribuem com menos de 0,3 mV.
- **R9**: estática → erro de ganho de −38 %; dinâmica → a leitura se perde sem chopagem; espectral → praticamente
  transparente com chopagem.
- **R10**: sem correção, ≈ 62 % do valor real (0,119 a 0,623 V); com calibração ×1,625: 0,193 / 0,399 / 0,610 /
  0,808 / 1,012 V. Leitura utilizável para forças acima de ≈ 0,03 N rms.

## Captura de tela (esquemático + painel SCADA)

![Esquemático e painel de instrumentação](captura-scada.png)
