# Typhoon HIL: montagem do equivalente elétrico e simulação no SCADA

**Sistema:** Sistema 3, motor CC brushed Electro-Craft E-576
**Disciplina:** ECOM060 Instrumentação Eletrônica, UFAL, 2026.2
**Software:** Typhoon HIL Control Center 2026.2 (Schematic Editor + HIL SCADA), dispositivo Virtual HIL
**Arquivo:** `typhoon/motor_cc_equivalente_eletrico.tse`

Este guia mostra como abrir ou montar o equivalente elétrico do motor no Typhoon e como rodar os três ensaios no HIL SCADA, com os valores esperados para comparar. O modelo substitui o bloco *Permanent Magnet DC Machine* por componentes elétricos comuns.

> **A conferir na sua instalação.** O `.tse` foi escrito à mão, no formato do arquivo da Atividade 01, e não foi compilado fora do Typhoon. Os nomes de menus, propriedades e terminais abaixo são os mais comuns no Control Center 2026.2. Se algum rótulo for diferente, use a busca de blocos (barra de pesquisa da biblioteca) com o nome do bloco.

---

## 1. A ideia do circuito (analogia força-corrente)

O lado mecânico vira um nó elétrico, o nó `omega`. A tensão desse nó é a velocidade e as correntes que entram ou saem dele são torques.

| Grandeza mecânica | Elemento elétrico | Valor |
|---|---|---|
| velocidade ω \[rad/s\] | tensão no nó `omega` \[V\] | 1 V ≡ 1 rad/s |
| torque \[N·m\] | corrente \[A\] | 1 A ≡ 1 N·m |
| inércia J = 100 × 10⁻⁶ kg·m² | capacitor `C_J` | 100 µF |
| atrito viscoso B = 105 × 10⁻⁶ N·m·s/rad | resistor `R_B` = 1/B | 9 523,80952 Ω |
| torque do motor Kt·ia | fonte de corrente `I_Tm`, controlada por ia | ganho 0,05 |
| força contra-eletromotriz Ke·ω | fonte de tensão `E_bemf`, controlada por v(omega) | ganho 0,05 |
| torque de carga TL | fonte de corrente `I_TL`, saindo do nó `omega` | 0 a 0,1 A |

```text
 ARMADURA (malha, KVL)                          EIXO (nó omega, KCL)

 Va_ref ─►[Va]                                  Ia ─►[Gain_Kt 0,05]─►[I_Tm]
   +──── Ra 3 Ω ──── La 6 mH ──[Ia]──┐                                │ (injeta no nó)
   │                                  │          omega ●──────┬───────┬──────┬────────┐
  (Va)                           (E_bemf)                      │       │      │        │
   │                                  │                      I_Tm    C_J    R_B     I_TL
   +──────────────┬───────────────────┘                     (↑)   100µF  9,52kΩ    (↓)
                 ⏚ gnd_el                                    └───────┴──────┴────────┘
                                                                            ⏚ gnd_mec
 omega ─►[Gain_Ke 0,05]─►[E_bemf]                TL_ref ─►[I_TL]
```

A equação do nó `omega` é C_J·dv/dt = Kt·ia − v/R_B − TL, que é a 2ª lei de Newton do eixo. A malha da armadura é va = Ra·ia + La·dia/dt + Ke·v(omega). Por isso o circuito tem exatamente os polos do motor (−9,546 e −491,50 s⁻¹).

---

## 2. Abrir o arquivo pronto

1. Abra o Typhoon HIL Control Center e, nele, o **Schematic Editor**.
2. **File ▸ Open** e escolha `motor_cc_equivalente_eletrico.tse`.
3. Confira se aparecem 16 componentes e as ligações da seção 1 (os blocos podem estar desalinhados; arraste para organizar, isso não muda nada).
4. Vá para a seção 4 (configuração) e depois compile (seção 5).

Se o arquivo não abrir ou algum bloco aparecer em vermelho, monte à mão pela seção 3. Leva uns 15 minutos.

---

## 3. Montar à mão (alternativa ao arquivo pronto)

### 3.1 Criar o modelo

1. No Schematic Editor: **File ▸ New**.
2. Salve como `motor_cc_equivalente_eletrico.tse`.
3. **Model ▸ HIL Device Settings** (ou *Model Settings*): dispositivo **HIL404**, configuração **6**, e marque **Virtual HIL** na hora de carregar (seção 6).

### 3.2 Colocar os blocos (biblioteca `core`)

Arraste cada bloco da biblioteca, renomeie (duplo clique no nome) e ajuste as propriedades (duplo clique no bloco):

| # | Bloco (biblioteca core) | Nome | Propriedades a ajustar |
|---|---|---|---|
| 1 | SCADA Input | `Va_ref` | Default value = `20`; unidade V |
| 2 | Voltage Source | `Va` | **Signal input** (ou *Source type: signal*) marcado |
| 3 | Resistor | `Ra` | Resistance = `3` |
| 4 | Inductor | `La` | Inductance = `6e-3` |
| 5 | Current Measurement | `Ia` | **Signal output** marcado |
| 6 | Voltage Source | `E_bemf` | **Signal input** marcado |
| 7 | Gain | `Gain_Ke` | Gain = `50e-3` |
| 8 | Gain | `Gain_Kt` | Gain = `50e-3` |
| 9 | Current Source | `I_Tm` | **Signal input** marcado |
| 10 | Capacitor | `C_J` | Capacitance = `100e-6` |
| 11 | Resistor | `R_B` | Resistance = `9523.80952` |
| 12 | Current Source | `I_TL` | **Signal input** marcado |
| 13 | SCADA Input | `TL_ref` | Default value = `0`; unidade N·m |
| 14 | Voltage Measurement | `omega` | **Signal output** marcado |
| 15 | Ground | `gnd_el` | — |
| 16 | Ground | `gnd_mec` | — |

Em todos os blocos de sinal e medição (1, 2, 5 a 9, 12 a 14), ponha **Execution rate = `1e-5`** (10 µs).

### 3.3 Ligações da armadura

1. `Va_ref.out` → `Va.in` (entrada de sinal da fonte)
2. `Va` (+) → `Ra` → `La` → `Ia` (+), com `Ia` em série
3. `Ia` (−) → `E_bemf` (+)
4. `E_bemf` (−) → `Va` (−) → `gnd_el`

A seta de corrente do amperímetro `Ia` deve apontar no sentido Va(+) → Ra → La → E_bemf, para que ia seja positiva com o motor acelerando.

### 3.4 Ligações do eixo (nó omega)

1. Crie um nó (junção) superior, o nó `omega`, e um inferior, ligado a `gnd_mec`.
2. Entre esses dois nós, em paralelo: `I_Tm`, `C_J`, `R_B`, `I_TL` e o voltímetro `omega` (+ no nó superior).
3. `I_Tm` deve **injetar** corrente no nó superior; `I_TL` deve **retirar** corrente dele. Confira a seta desenhada em cada fonte.

### 3.5 Acoplamento (os dois ganhos)

1. `Ia.out` → `Gain_Kt.in`; `Gain_Kt.out` → `I_Tm.in`
2. `omega.out` → `Gain_Ke.in`; `Gain_Ke.out` → `E_bemf.in`
3. `TL_ref.out` → `I_TL.in`

---

## 4. Configuração da simulação

| Campo | Valor | Onde fica |
|---|---|---|
| Dispositivo | HIL404, configuração 6, carregado em Virtual HIL | Model ▸ HIL Device Settings |
| Método | exact | Model ▸ Model Settings ▸ Simulation |
| Passo do circuito | auto | idem |
| Taxa de processamento de sinais | 10 µs (`1e-5`) | idem, *Signal processing* / *DSP timer* |

**Por que 10 µs.** As fontes controladas são atualizadas pelo processamento de sinais, com atraso de um passo. Com 10 µs o erro em ω fica em 0,006 rad/s; com 100 µs, em 0,066 rad/s (0,12 % da variação no ensaio a). Se o Typhoon reclamar que 10 µs é rápido demais, use `1e-4` em todos os blocos: o resultado continua aceitável.

---

## 5. Compilar e corrigir erros

1. **Compile** (`Ctrl+B`).
2. Erros comuns e o que fazer:

| Sintoma | Causa provável | Correção |
|---|---|---|
| Bloco em vermelho ou propriedade desconhecida | nome de propriedade diferente na sua versão | abra o bloco e preencha o valor pela janela de propriedades |
| Terminal sem ligação | o terminal de sinal (`in`/`out`) só aparece depois de marcar *Signal input/output* | marque a opção e refaça a ligação |
| ω fica negativa ou cresce sem parar | sentido de `I_Tm` invertido: o acoplamento virou realimentação positiva | inverta `I_Tm` (gire 180°) ou use `Gain_Kt = -50e-3` |
| ω sobe quando TL aumenta | sentido de `I_TL` invertido | inverta `I_TL` ou use ganho negativo para TL |
| ω estabiliza em valor errado (≠ 355,24 rad/s a 20 V) | valor de R_B, C_J ou dos ganhos digitado errado | confira a tabela 3.2 |

---

## 6. Montar o painel no HIL SCADA

O painel antigo (`dc-brushed-motor-cus.cus`) usa sinais do bloco `PMDC1` e não serve para este modelo. Monte um novo:

1. No Control Center, abra o **HIL SCADA** e carregue o modelo compilado (**Load model**), marcando **Virtual HIL**.
2. **File ▸ New panel** e salve como `motor_cc_equivalente_eletrico.cus`, na mesma pasta do `.tse`.
3. Adicione os widgets (arraste da *Widget Library*; duplo clique para configurar):

| Widget | Ligado a | Ajustes |
|---|---|---|
| Slider ou Text box (entrada) | SCADA Input `Va_ref` | faixa 0 a 30 V, passo 0,01 |
| Slider ou Text box (entrada) | SCADA Input `TL_ref` | faixa 0 a 0,1 N·m, passo 0,001 |
| Digital Display | `omega` | unidade rad/s, 2 casas |
| Digital Display | `Ia` | unidade A, 3 casas |
| Trace Display | `omega` | eixo y "Velocidade (rad/s)", janela de 2 s |
| Trace Display | `Ia` | eixo y "Corrente (A)", janela de 2 s |
| Capture/Scope | `omega` e `Ia` | ver seção 7 para cada ensaio |

4. **Start simulation**. Com `Va_ref` = 20 V, os displays devem chegar a ω = 355,24 rad/s e ia = 0,746 A em menos de 1 s.

> **Partida.** Ligar o modelo direto em 20 V é um degrau a partir do repouso: a corrente passa de 2 A por alguns milissegundos (pico ≈ 6,3 A). É só o modelo chegando ao equilíbrio, não um ensaio. Para evitar isso, comece com `Va_ref` = 0 e suba de 3,9 V em 3,9 V, esperando estabilizar a cada passo.

---

## 7. Ensaios

Em todos: espere o regime (≈ 0,5 s, cinco vezes τ1) antes de mudar a entrada, e capture **omega** e **Ia** juntos.

### 7.1 Ensaio (a): degrau de tensão a partir do equilíbrio

1. `Va_ref` = 20 V, `TL_ref` = 0. Espere estabilizar.
2. No Capture/Scope: janela de 1 s, gatilho em `omega` com borda de subida e nível 360 rad/s, pré-gatilho de 10 %.
3. Arme a captura e mude `Va_ref` para **23 V**.

| Grandeza | Esperado | Medido |
|---|---|---|
| ω antes do degrau | 355,24 rad/s | |
| ω final | 408,53 rad/s | |
| ia antes / final | 0,746 A / 0,858 A | |
| pico de ia | 1,693 A, cerca de 8,4 ms após o degrau | |
| tempo de subida (10–90 %) | 230 ms | |
| tempo de acomodação (2 %) | 412 ms | |
| sobressinal | 0 % | |

### 7.2 Ensaio (b): condição inicial não nula (armadura em curto)

1. `Va_ref` = **5,63 V**, `TL_ref` = 0. Espere ω = 100,00 rad/s (ia = 0,210 A).
2. No Capture/Scope: janela de 0,6 s, gatilho em `omega` com borda de descida e nível 99 rad/s, pré-gatilho de 5 %.
3. Arme e mude `Va_ref` para **0 V**.

| Grandeza | Esperado | Medido |
|---|---|---|
| ω inicial | 100,00 rad/s | |
| ia mínima (frenagem) | −1,568 A, cerca de 8,4 ms após o corte | |
| ω em t = τ1 = 104,8 ms | 37,5 rad/s | |
| tempo até 36,8 rad/s | 106,8 ms | |
| τ1 pela inclinação de ln ω (de 0,1 a 0,6 s) | 104,8 ms | |

No relatório o ensaio parte de ia(0) = 0; aqui parte de 0,21 A, por isso ω(τ1) é 37,5 em vez de 37,4 rad/s. O τ1 é o mesmo.

### 7.3 Ensaio (c): torque de carga

Um pulso de 50 ms não dá para aplicar com precisão mexendo à mão no SCADA. Use o degrau de carga (opção A) e, se quiser, a macro (opção B).

**Opção A: degrau de carga (recomendado)**

1. `Va_ref` = 20 V, `TL_ref` = 0. Espere estabilizar.
2. Capture/Scope: janela de 1,2 s, gatilho em `omega` com borda de descida e nível 354 rad/s.
3. Arme e mude `TL_ref` para **0,05**.

| Grandeza | Esperado | Medido |
|---|---|---|
| ω antes / final | 355,24 rad/s / 301,95 rad/s | |
| ia antes / final | 0,746 A / 1,634 A | |
| tempo de acomodação (2 %) | ≈ 0,41 s | |

**Opção B: pulso de 50 ms por macro (aproximado)**

Adicione um widget **Macro** (botão) com o código abaixo. O tempo de 50 ms depende do computador, então confira a largura real do pulso na captura.

```python
import time
hil.set_scada_input_value('TL_ref', 0.05)
time.sleep(0.05)
hil.set_scada_input_value('TL_ref', 0.0)
```

Com pulso de exatamente 50 ms, o esperado é ω mínimo de 335,03 rad/s no fim do pulso, ia máxima de 1,077 A e retorno a 355,20 rad/s 650 ms depois do fim do pulso.

---

## 8. Exportar e documentar

1. Em cada captura: **Export ▸ CSV** (`ensaio_a.csv`, `ensaio_b.csv`, `ensaio_c.csv`) para sobrepor às curvas do Python.
2. Prints sugeridos: esquemático compilado; painel do SCADA em regime; captura de cada ensaio com cursores nos pontos das tabelas.
3. Preencha a coluna **Medido** das tabelas da seção 7 e leve as diferenças para a tabela de validação cruzada (R4) do relatório.

## Checklist

- [ ] Modelo aberto ou montado com os 16 blocos e as ligações da seção 3
- [ ] Valores: Ra 3 Ω, La 6 mH, C_J 100 µF, R_B 9 523,8 Ω, ganhos 0,05
- [ ] Taxa de execução de 10 µs (ou 100 µs, anotando no relatório)
- [ ] A 20 V: ω = 355,24 rad/s e ia = 0,746 A
- [ ] Ensaio (a): 408,53 rad/s e pico de 1,693 A
- [ ] Ensaio (b): ia mínima de −1,568 A e τ1 de 104,8 ms
- [ ] Ensaio (c): 301,95 rad/s com TL = 0,05 (ou mínimo de 335,03 rad/s com o pulso)
- [ ] CSVs exportados e prints salvos
