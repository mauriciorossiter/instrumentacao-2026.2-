# E2 — Minimização de entradas espúrias por correções calculadas (TyphoonSim)

ECOM060 — Instrumentação Eletrônica (UFAL, 2026.2) — Grupo 02 (massa-mola-amortecedor)

## Visão geral

O modelo `modelo.tse` simula uma célula de carga strain-gauge (Zemic H8C) medindo um peso
constante enquanto a temperatura ambiente varia entre 21 °C e 38 °C. A temperatura atua
como entrada **de interferência** (erro de zero) e **modificante** (erro de span). Um sensor
auxiliar de temperatura (TI TMP117) mede a temperatura, e um bloco de **correção calculada**
remove o erro térmico estimado da saída. Todos os subsistemas são blocos *C function*.

## Topologia

```
C function2 (T) ──┬──> xm(t), xi(t) ─┐
                  │                  │
Weight1 (w) ──────┼──> x(t) ─────────┤
                  │                  ▼
                  │   Subsistema "Instrumento Real Descrito por f[]"
                  │     f0(t): y_id + e_span  ─┐
                  │     g0(t): e_zero         ─┴─> Sum1 ──> y(t) [V]
                  │                                          │
                  └──> TMP117 (Sensor)1 ── Tmed ──┐          │
                                                  ▼          ▼
                                     CalCorrection1 (in = y, sin = Tmed) ──> out [V]
y(t)  ──> V2Kg2 ──> SpuriousOut [kg]           out ──> V2Kg3 ──> CorrectedOut [kg]
```

- Subsistema `Instrumento Real Descrito por f[]`: modelo generalizado
  y(t) = f0[x(t)] + g0[xi(t)] (Aguirre, cap. 2), com `xm` e `xi` ligados ao mesmo sinal de temperatura.
- Probes: `OriginalInput` (peso w), `RawOutput` (y bruto, V), `CorrectedRaw` (saída corrigida, V),
  `SpuriousOut` (bruto em kg), `CorrectedOut` (corrigido em kg).
- `Scope1`: viewport 1 = `RawOutput`, `CorrectedRaw`; viewport 2 = `SpuriousOut`, `OriginalInput`, `CorrectedOut`.

## Valores dos elementos

| Bloco / parâmetro | Símbolo | Valor | Origem |
|---|---|---|---|
| Fundo de escala da célula | FS | 500 kg | H8C |
| Excitação | VEXC | 10 V | H8C |
| Sensibilidade | SENS | 3,0 mV/V | H8C |
| Saída de fundo de escala | VFS = VEXC·SENS | 0,030 V | calculado |
| Temperatura de calibração | TCAL | 20 °C | H8C |
| Efeito térmico no zero | ZTC | 0,015 %FS/10 °C = 1,5·10⁻⁵ /°C | H8C |
| Efeito térmico no span | STC | 0,011 %FS/10 °C = 1,1·10⁻⁵ /°C | H8C |
| Faixa compensada | — | −10 a +40 °C | H8C |
| Resolução do TMP117 | LSB | 0,0078125 °C | TMP117 |
| Offset de acurácia (exemplar) | OFFSET | 0,05 °C (≤ 0,1 °C) | TMP117 |
| Sensibilidade à fonte (não usada) | PSR | 0,006 °C/V | TMP117 |
| Peso aplicado (`Weight1`) | w | 350 kg | modelo |
| Temperatura média / amplitude (`C function2`) | TMED / AMP | 29,5 °C / 8,5 °C | modelo |
| Frequência do ciclo diário | FREQ | 1 Hz (= 1/Tsim) | modelo |
| Execution rate das fontes e de f0/g0 | — | 100 µs (`0.0001`) | modelo |
| Tempo de simulação / passo máximo | — | 1,0 s / 1·10⁻⁴ s | modelo |
| Dispositivo | — | VHIL+ | modelo |

## Elementos não lineares / blocos C function

- **f0(t)** (resposta ao mensurando + erro modificante):
  `y_id = (x/FS)·VFS`, `e_span = STC·(xm − TCAL)·y_id`, `y = y_id + e_span`.
- **g0(t)** (interferência): `e_zero = ZTC·(xi − TCAL)·VFS`, `y = e_zero`. `Sum1` soma f0 + g0.
- **TMP117 (Sensor)1** (não linear — quantização):
  `Tm = in + OFFSET; Tm = floor(Tm/LSB + 0.5)·LSB`.
- **CalCorrection1** (não linear — divisão pela temperatura medida, `sin` = Tmed):
  `y = in − ZTC·(sin − TCAL)·VFS` (remove zero); `y = y / (1 + STC·(sin − TCAL))` (remove span).
- **V2Kg2 / V2Kg3**: `kg = (v/VFS)·FS` (conversão V → kg).
- **C function2** (fonte senoidal): `T = TMED + AMP·sin(2π·FREQ·t_acc)`, `t_acc += 100e-6` a cada passo.
- **Weight1**: `w = 350.0`.

O relatório também descreve um termo residual r(t) (não-linearidade, histerese da célula) que
não tem contrapartida na correção e constitui o piso de erro do método.

## Como executar

1. Abrir `modelo.tse` no **Schematic Editor** do TyphoonSim.
2. Conferir que o *execution rate* dos blocos de fonte é numérico (`0.0001`). O valor `inherit`
   nas fontes gera erro de compilação, pois elas não têm de quem herdar a taxa.
3. **Compile** o modelo e carregue-o no dispositivo configurado (VHIL+) ou rode a simulação.
4. Abrir o `Scope1` (ou um painel SCADA com os mesmos probes) e observar/exportar
   `OriginalInput`, `SpuriousOut`, `CorrectedOut` (kg) e `RawOutput`, `CorrectedRaw` (V).

### Ensaio 1 — Rampa de temperatura (21 °C → 38 °C)

1. Substituir a fonte de temperatura `C function2` por uma rampa (bloco *Ramp* ou equivalente em C),
   ligada à mesma junção (entradas `xm`, `xi` e TMP117), com:
   `Initial value = 21`, `Slope = (38 − 21)/Tsim`, `Start time = 0` (com Tsim = 1,0 s, slope = 17 °C/s).
2. Manter `Weight1` em 350 kg; compilar e simular.
3. Comparar `SpuriousOut` × `CorrectedOut` × `OriginalInput`; ler o erro no fim da rampa (T = 38 °C).

### Ensaio 2 — Ciclo diário senoidal (configuração atual do modelo)

1. Usar `C function2` como está: TMED = 29,5 °C, AMP = 8,5 °C, FREQ = 1/Tsim = 1 Hz, fase 0.
2. Compilar e simular por 1,0 s (um "dia" comprimido).
3. Observar `SpuriousOut` oscilando com a temperatura e `CorrectedOut` estável; conferir que a
   correção atua tanto para T > TCAL quanto para T < TCAL.

## Resultados esperados

| Ensaio | Saída bruta (`SpuriousOut`) | Saída corrigida (`CorrectedOut`) |
|---|---|---|
| Rampa (T = 38 °C) | ≈ 350,19 kg (erro ≈ +0,19 kg, ≈ 0,055 %) | ≈ 349,999 kg (erro ≈ 10⁻³ kg, ≈ 0,0003 %) |
| Senoide 21–38 °C | oscila, erro ≈ ±0,19 kg nos picos | ≈ 350 kg ao longo de todo o ciclo |

Redução de mais de 99 % do erro sistemático de deriva térmica; o residual vem do modelo
incompleto da célula (r(t)), não do TMP117.

## Captura de tela (esquemático + painel SCADA)

![Esquemático e painel de instrumentação](captura-scada.png)
