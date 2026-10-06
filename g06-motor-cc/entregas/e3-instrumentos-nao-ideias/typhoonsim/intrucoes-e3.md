# Typhoon HIL, guia da simulação do Instrumento Não Ideal (Motor CC Escovado)

**Sistema:** Sistema 3, Motor CC Escovado, Electro-Craft E-576 Servo Motor
**Disciplina:** ECOM060 Instrumentação Eletrônica, UFAL, 2026.2
**Software:** Typhoon HIL Control Center (Schematic Editor + HIL SCADA), modo Virtual HIL
**Arquivo do modelo:** `instrumento_nao_ideal.tse`

Este guia monta no Typhoon o modelo descrito na Seção 5 do relatório "Projeto do Instrumento Não Ideal". A planta é a mesma dos relatórios anteriores. Sobre os sinais verdadeiros de corrente `i_a(t)` e de velocidade `ω(t)`, constroem-se os modelos dos sensores não ideais (shunt e tacogerador), para verificar a **insensibilidade inerente** a cada entrada espúria.

## Ideia do modelo

Como o carregamento de um shunt de baixo valor e de um tacogerador de alta impedância é desprezível (< 0,1 %), o ponto de operação da planta não muda. Por isso os sensores são modelados como **processamento de sinal** aplicado aos sinais verdadeiros:

- **não idealidades multiplicativas** (deriva térmica, resistência de cabo): blocos `Gain` com o fator de erro para `ΔT = +25 °C`;
- **não idealidades aditivas** (ripple de comutação e ruído eletromagnético): fonte triangular + fonte aleatória, somadas em modo comum nos dois enrolamentos do tacogerador diferencial.

## Valores de projeto que vêm do relatório

**Planta (E-576, igual aos relatórios anteriores):**

| Parâmetro | Valor |
|-----------|-------|
| `Va` | `30` V constante |
| `Ra` | `3` Ω |
| `La` | `6e-3` H |
| `Kt = Ke` | `50e-3` (Vs/rad, equivalente a N·m/A) |
| `J` (motor + carga) | `100e-6` kg·m² |
| `B` (motor + carga) | `105e-6` N·m·s/rad |
| `T_L` | `0` (motor livre) |

**Ponto de operação de referência:** `ω_ss = 532,86 rad/s` e `i_a,ss = 1,119 A`.

**Fatores de não idealidade (`ΔT = +25 °C`):**

| Entrada espúria | Cálculo | Fator |
|-----------------|---------|-------|
| Deriva térmica do shunt de cobre (α ≈ 4000 ppm/°C) | `1 + (4000·10⁻⁶)(25)` | `1,10` |
| Deriva térmica do shunt de manganina (α ≈ 20 ppm/°C) | `1 + (20·10⁻⁶)(25)` | `1,0005` |
| Resistência de cabo a 2 fios (`R_cabo = 0,2·R_sh`) | `1 + 0,2` | `1,20` |
| Deriva térmica do ímã de ferrite (α ≈ −2000 ppm/°C) | `1 − (2000·10⁻⁶)(25)` | `0,95` |
| Ripple de comutação | onda triangular, 100 Hz | `±16 rad/s` (≈ 3 % de `ω_ss`) |
| Ruído eletromagnético | aleatório uniforme | `±8 rad/s` |

---

## 0. Observações sobre menus

Os caminhos de menu são os mais comuns no Typhoon HIL Control Center. Se o rótulo na sua versão for diferente, use a barra de busca de blocos e digite o nome do bloco.

> **A conferir na sua instalação:** nomes exatos de menus, do passo de simulação e dos parâmetros das fontes Triangular Wave Source e Random Source.

## 1. Criar o projeto e o modelo

1. Abra o Typhoon HIL Control Center.
2. No Schematic Editor, crie um modelo novo em **File ▸ New** (arquivo `.tse`).
3. Salve como `instrumento_nao_ideal.tse`, na pasta da entrega.
4. Configure o dispositivo para **Virtual HIL** (**Model ▸ HIL Device Settings**).
5. Ajuste o passo de simulação `Ts`. O ripple triangular tem 100 Hz (período de 10 ms) e a dinâmica rápida do motor tem `τ2 ≈ 2 ms`, então use um passo pequeno, por exemplo `Ts = 100e-6 s` (sugestão, em linha com os relatórios anteriores). O campo costuma ficar em **Simulation ▸ System settings**.

## 2. Planta elétrica (sinais verdadeiros)

É a mesma malha do relatório de simulação anterior, com nomes novos.

| # | Bloco | Nome | Parâmetro | Valor |
|---|-------|------|-----------|-------|
| 1 | Voltage Source | `Vs1` | Tensão | `30` V constante |
| 2 | Current Measurement | `Ia1` | Enable signal output (`sig output`) | `True` |
| 3 | Permanent Magnet DC Machine | `PMDC1` | ver abaixo | ver abaixo |
| 4 | Voltage Measurement | `Va1` | n/a | mede a tensão entre os terminais de alimentação |
| 5 | Constant | `Constant1` | Valor | `0` (torque de carga, N·m) |

**Configuração do `PMDC1`** (as mesmas informações do datasheet do E-576):

- Aba *Electrical*: `Ra = 3`, `La = 6e-3`, `Kt = 50e-3`, `Ke = 50e-3`.
- Aba *Mechanical*: `Jm = 100e-6`, *Friction coefficient* `= 105e-6`, *Unconstrained mechanical angle* `= disabled`.
- Aba *Load*: *Load source* `= Model`, *External/Model load type* `= torque`. Isso habilita a entrada `load in`.
- Habilite a saída **Mechanical speed** do bloco, para obter `ω(t)` verdadeiro (`PMDC1.out`).

**Conexões da planta:**

- `Vs1 (+)` → `Ia1` → terminal `A1` do `PMDC1`.
- Terminal `A2` do `PMDC1` → `Vs1 (−)`.
- `Va1` em paralelo com `Vs1`.
- `Constant1` (valor `0`) → entrada `load in` do `PMDC1`.

**Sinais verdadeiros extraídos da planta:**

- `Ia1.out`: corrente de armadura verdadeira `i_a(t)` (saída de sinal do amperímetro);
- `PMDC1.out`: velocidade angular verdadeira `ω(t)` (saída *Mechanical speed*).

## 3. Ramo do sensor de corrente (shunt)

O sinal `Ia1.out` é distribuído, por junções (*splits*), a **três blocos `Gain` independentes**. Cada um é um cenário de leitura do mesmo shunt, **não** um estágio em cascata.

| Bloco | Ganho | Probe | Cenário |
|-------|-------|-------|---------|
| `Gain1` | `1.10` | `i_Cu` | Shunt de cobre, sem compensação de temperatura |
| `Gain2` | `1.0005` | `i_Mn` | Shunt de manganina (insensibilidade por escolha de material) |
| `Gain3` | `1.20` | `i_2fios` | Leitura a 2 fios (resistência de cabo somada ao shunt) |

```text
                    ┌─► Gain1 (1.10)   ──► Probe i_Cu
Ia1.out (i_a(t)) ───┼─► Gain2 (1.0005) ──► Probe i_Mn
                    └─► Gain3 (1.20)   ──► Probe i_2fios
```

A leitura Kelvin a 4 fios **não precisa de bloco extra**: por definição ela reproduz exatamente o sinal verdadeiro `Ia1.out`, que já serve como referência ideal.

## 4. Ramo do sensor de velocidade (tacogerador)

O sinal `PMDC1.out` (`ω(t)`) alimenta dois sub-ramos independentes.

### 4.1 Leitura por amplitude absoluta

- `Gain4 = 0.95`, aplicado diretamente a `ω(t)`, saindo no `Probe w_abs`.
- Modela a deriva do ganho do tacogerador com o ímã aquecido, sem compensação.

### 4.2 Tacogerador diferencial

Construído com blocos somadores (`Sum`) que representam os dois enrolamentos, `chA` e `chB`.

| Bloco | Tipo | Parâmetro | Função |
|-------|------|-----------|--------|
| `Triangular` | Triangular Wave Source | `100 Hz`, amplitude `±16` | ripple de comutação |
| `Random` | Random Source | distribuição uniforme, `±8` | ruído eletromagnético |
| `Sum n` | Sum | `++` | gera a interferência de modo comum `n(t)` |
| `Kg_neg` | Gain | `-1` | inverte `ω(t)` para o segundo enrolamento |
| `chA` | Sum | `++` | `chA = ω(t) + n(t)` |
| `chB` | Sum | `++` | `chB = −ω(t) + n(t)` |
| `dif` | Sum | signs `+-` | `chA − chB = 2·ω(t)` |
| `half` | Gain | `0.5` | normaliza, resultando em `ω(t)` |

**Equações do tacogerador diferencial:**

```text
chA = ω(t) + n(t)       (enrolamento em fase)
chB = −ω(t) + n(t)      (enrolamento em oposição)
w_dif = 0,5·(chA − chB) = ω(t)      ← n(t) cancelado por construção
```

**Conexões:**

```text
                       ┌─► Gain4 (0.95) ──────────────────────► Probe w_abs
                       │
PMDC1.out (ω(t)) ──────┼────────────────┐
                       │                ▼
                       │            [ chA = Sum ] ◄── n ──► Probe w_se   (chA)
                       │                │         ▲
                       │                │         │
 Triangular ─┐         │                │       [Sum n] ◄── Random
             └────────►┘ (via Sum n)    │
                       │                ▼
                       └─► Kg_neg (−1) ► [ chB = Sum ] ◄── n
                                        │
                                  [ dif: chA − chB ] ► [ half 0.5 ] ► Probe w_dif
```

Em palavras:

1. `Triangular` e `Random` entram em `Sum n`, que gera `n(t)`.
2. `chA` soma `ω(t)` com `n(t)`. A saída de `chA` vai ao `Probe w_se` (leitura single-ended, sem cancelamento) e à entrada `+` de `dif`.
3. `Kg_neg` inverte `ω(t)`. `chB` soma esse resultado com o **mesmo** `n(t)`. A saída de `chB` vai à entrada `−` de `dif`.
4. A saída de `dif` passa por `half` e chega ao `Probe w_dif`.

> O mesmo `n(t)` precisa chegar aos dois somadores. Se `chA` e `chB` receberem ruídos diferentes, o cancelamento não acontece.

A leitura **ratiométrica** (insensível à temperatura) também não exige bloco: ela coincide com o sinal verdadeiro `PMDC1.out`.

## 5. Probes e variáveis

Dê estes nomes aos probes (sem espaços, porque o Typhoon os usa no SCADA):

| Variável | Origem | Significado | Expressão |
|----------|--------|-------------|-----------|
| `Ia1` | Amperímetro (saída de sinal) | Corrente verdadeira; referência ideal (= Kelvin 4 fios) | `i_a` |
| `mech. speed` | Saída da máquina `PMDC1` | Velocidade verdadeira; referência ideal (= ratiométrico) | `ω` |
| `i_Cu` | Probe ← `Gain1` | Shunt de cobre sob `ΔT` | `1,10·i_a` |
| `i_Mn` | Probe ← `Gain2` | Shunt de manganina | `1,0005·i_a` |
| `i_2fios` | Probe ← `Gain3` | Leitura a 2 fios | `1,20·i_a` |
| `w_abs` | Probe ← `Gain4` | Tacogerador, leitura absoluta com ímã aquecido | `0,95·ω` |
| `w_se` | Probe ← `chA` | Single-ended, com ripple + ruído | `ω + n(t)` |
| `w_dif` | Probe ← `half` | Diferencial, modo comum cancelado | `½(chA − chB)` |

Se a sua versão exigir, habilite o *streaming* de cada probe para o SCADA nas propriedades.

## 6. Compilar e executar

1. No Schematic Editor, clique em **Compile** (`Ctrl+B`) e corrija erros de conexão.
2. Abra o **HIL SCADA** (**Model ▸ Load to SCADA** ou equivalente).
3. Carregue o modelo no Virtual HIL e clique em **Run / Start simulation**.
4. Todos os cenários são avaliados em **uma única simulação**, a partir do repouso. Espere a estabilização (≈ 0,5 s) antes de ler os valores em regime.
5. Monte o painel como na Figura 5 do relatório:
   - displays numéricos: `Ia1`, `i_Mn`, `i_Cu`, `i_2fios`, `w_se`, `w_dif`, `w_abs`;
   - scopes: `w_dif`, `w_abs` e `w_se` (escala de 1,0 s/div como no relatório).
6. Para a Figura 6, abra um scope com `w_se` e `w_dif` sobrepostos e reduza a base de tempo para ≈ 0 a 0,01 s (uma janela de 10 ms, que contém um período do ripple de 100 Hz).

## 7. Resultados esperados

Erros percentuais relativos ao valor ideal (`i_a,ss = 1,119 A`; `ω_ss = 532,86 rad/s`). Unidades: corrente em A, velocidade em rad/s.

| Instrumento / cenário | Estratégia | Variável | Typhoon (relatório) | Teórico |
|-----------------------|------------|----------|---------------------|---------|
| Corrente ideal (referência) | n/a | `Ia1` | 1,12 | 1,119 |
| Velocidade ideal (referência) | n/a | `mech. speed` | 532,86 | 532,86 |
| Corrente sem comp. (cobre) | modificadora, deriva térmica | `i_Cu` | 1,23 (+10,0 %) | 1,2309 |
| Corrente com comp. (manganina) | insensibilidade por material | `i_Mn` | 1,12 (+0,05 %) | 1,1196 |
| Velocidade sem comp. (absoluto) | modificadora, deriva térmica | `w_abs` | 506,22 (−5,0 %) | 506,22 |
| Velocidade com comp. (ratiométrico) | medição por razão | (= ideal) | 532,86 (≈ 0 %) | 532,86 |
| Corrente sem comp. (2 fios) | interferente, resistência de cabo | `i_2fios` | 1,34 (+20,0 %) | 1,3428 |
| Corrente com comp. (Kelvin 4 fios) | eliminação do caminho de acoplamento | (= ideal) | 1,12 (≈ 0 %) | 1,119 |
| Velocidade sem comp. (single-ended) | interferente aditiva | `w_se` | oscila ±≈24 | `ω + n(t)` |
| Velocidade com comp. (diferencial) | configuração diferencial | `w_dif` | 532,86 (plano) | `ω` |

**Pontos para conferir:**

- `w_se` oscila em torno de 532,86 rad/s com pico de ≈ ±24 rad/s (≈ ±4,5 %), soma de 16 do ripple e 8 do ruído. O display mostra um valor instantâneo (537,90 na Figura 5), então ele varia a cada leitura.
- `w_dif` fica plano em 532,86 rad/s. Na prática, o resíduo seria limitado pelo CMRR: com descasamento de 1 % entre canais, o erro residual seria da ordem de 0,03 %. No modelo ideal ele é nulo.
- Os valores medidos coincidem com os teóricos dentro da resolução do mostrador do painel.

## 8. Capturas para o relatório

Salve as figuras com nomes claros, por exemplo:

1. `fig_esquematico_nao_ideal.png`: esquemático completo no Schematic Editor (planta, ramo de corrente, ramo de velocidade e tacogerador diferencial), como na Figura 4.
2. `fig_painel_scada.png`: painel do HIL SCADA com as leituras em regime, como na Figura 5.
3. `fig_w_se_vs_w_dif.png`: scope com `w_se` e `w_dif` sobrepostos, janela de ≈ 10 ms, como na Figura 6.

As Figuras 2 e 3 do relatório são diagramas de blocos do ramo de corrente e do ramo de velocidade. Se quiser refazê-las a partir do modelo, use as conexões das seções 3 e 4.

## Checklist final

- [ ] Planta montada: `Vs1 = 30 V`, `Ia1` com `sig output = True`, `PMDC1` com os parâmetros do E-576, `Va1`, `Constant1 = 0` na entrada `load in`.
- [ ] Saída *Mechanical speed* do `PMDC1` habilitada.
- [ ] Ramo de corrente: `Gain1 = 1.10`, `Gain2 = 1.0005`, `Gain3 = 1.20`, cada um com seu probe, todos ligados a `Ia1.out`.
- [ ] Ramo de velocidade: `Gain4 = 0.95` com `w_abs`; `Triangular` (100 Hz, ±16) + `Random` (uniforme, ±8) em `Sum n`; `Kg_neg = −1`; `chA`, `chB`, `dif` (`+-`) e `half = 0.5`.
- [ ] O mesmo `n(t)` chega a `chA` e `chB`.
- [ ] Referências em regime: `ω = 532,86 rad/s`, `i_a = 1,12 A`, `Va = 30,00 V`.
- [ ] Leituras: `i_Cu ≈ 1,23`, `i_Mn ≈ 1,12`, `i_2fios ≈ 1,34`, `w_abs ≈ 506,22`, `w_dif = 532,86`, `w_se` oscilando.
- [ ] Figuras 4, 5 e 6 salvas.