# Typhoon HIL, guia da simulação do Sistema 3 (Motor CC Brushed)

**Sistema:** Sistema 3, Motor CC (Brushed), Electro-Craft E-576 Servo Motor
**Disciplina:** ECOM060 Instrumentação Eletrônica, UFAL, 2026.2
**Software:** Typhoon HIL Control Center (Schematic Editor + HIL SCADA)

Este guia monta no Typhoon o mesmo sistema não instrumentado do relatório e replica os três ensaios já feitos no MATLAB, para comparar os resultados. Em todos os ensaios:

- **entrada principal:** tensão de armadura `v_a(t)`;
- **saída medida:** velocidade angular `ω(t)`;
- **entrada de distúrbio:** torque de carga `T_L`, injetado na aba *Load* do motor (não confundir com a entrada principal);
- **condições iniciais nulas:** o motor parte do repouso.

## Valores de projeto que vêm do relatório

Parâmetros do motor (datasheet do E-576):

| Parâmetro | Símbolo | Valor | Unidade |
|-----------|---------|-------|---------|
| Resistência de armadura | `Ra` | `3` | Ω |
| Indutância de armadura | `La` | `6e-3` | H |
| Constante de torque | `Kt` | `50e-3` | Vs/rad |
| Constante de f.c.e.m. | `Ke` | `50e-3` | Vs/rad |
| Momento de inércia | `Jm` | `100e-6` | kg·m² |
| Coeficiente de atrito | `Friction coefficient` | `105e-6` | Nms |

Domínio de validade do modelo linear: `0 ≤ v_a(t) ≤ 30 V` e `|i_a(t)| ≤ 2 A`.

Valores teóricos para comparação (MATLAB, Seções 9.2 e 9.3 do relatório de caracterização):

| Grandeza | Valor teórico |
|----------|---------------|
| `ω_ss` (30 V, `T_L = 0`) | 532,86 rad/s |
| `i_a,ss` (30 V, `T_L = 0`) | 1,119 A |
| Constante de tempo dominante `τ1` | ≈ 0,1048 s |
| Constante de tempo rápida `τ2` | ≈ 2 ms |
| Stiffness ratio `\|p2\|/\|p1\|` | ≈ 51,5 |
| `ω` mínimo no ensaio de pulso de torque | ≈ 512,65 rad/s |

---

## 0. Observações sobre menus

Os caminhos de menu abaixo são os mais comuns no Typhoon HIL Control Center. Se o rótulo na sua versão for diferente, use a barra de busca de blocos e digite o nome do bloco.

> **A conferir na sua instalação:** nomes exatos de menus e do passo de simulação.

## 1. Criar o projeto e o modelo

1. Abra o Typhoon HIL Control Center.
2. No Schematic Editor, crie um modelo novo em **File ▸ New** (arquivo `.tse`).
3. Salve como `motor_cc_e576.tse`, na pasta da entrega.
4. Configure o dispositivo de execução para **Virtual HIL** (**Model ▸ HIL Device Settings**), que roda por software e não precisa de hardware.
5. Ajuste o passo de simulação `Ts`. O relatório recomenda amostragem mínima de ≈ 5 kHz, porque `τ2 ≈ 2 ms`. Isso dá `Ts ≤ 200 µs`; um valor como `Ts = 100e-6 s` atende com folga (sugestão). O campo costuma ficar em **Simulation ▸ System settings**.

## 2. Blocos do circuito

O circuito é o da Figura 1 do relatório. Os blocos vêm da biblioteca local do Typhoon (use a busca de blocos).

| # | Bloco | Nome sugerido | Parâmetro | Valor |
|---|-------|---------------|-----------|-------|
| 1 | Permanent Magnet DC Machine (biblioteca `core`) | `E-576 Servo Motor` | ver §3 | ver §3 |
| 2 | Fonte de tensão DC | `Fonte de tensão fixa` | Tensão | `30` V |
| 3 | Current Measurement | `Amperímetro ideal` | n/a | n/a |
| 4 | Voltage Measurement | `Voltímetro Ideal` | n/a | n/a |
| 5 | Constant (Signal Processing) | `Constant2` | Valor | `0` (torque de carga, N·m) |

O Permanent Magnet DC Machine é a representação exata do modelo elétrico/mecânico estudado. O amperímetro e o voltímetro são ideais e não interferem no circuito.

### Conexões

```text
                  ┌──────────────┐
 Constant2 (0) ──►│ entrada Load │
                  │              │
                  │  E-576 Servo │ A1 ──► [Amperímetro ideal] ──┬── (+) Fonte 30 V ──┬── (+) Voltímetro
                  │    Motor     │                              │                    │
                  │              │ A2 ──────────────────────────┴────── (−) ─────────┴── (−)
                  └──────────────┘
```

Em palavras:

- O terminal `A1` do motor vai ao amperímetro, e o amperímetro ao polo positivo da fonte.
- O terminal `A2` vai ao polo negativo da fonte.
- O voltímetro fica em paralelo com a fonte (mede a tensão de armadura).
- O `Constant2` com valor `0` liga na entrada de torque de carga do motor (a entrada aparece depois de configurar a aba *Load*, §3).

## 3. Configurar o Permanent Magnet DC Machine

Clique duas vezes no motor e preencha as abas:

**Aba Electrical (Figura 2 do relatório)**

| Campo | Valor |
|-------|-------|
| `Ra` | `3` Ω |
| `La` | `6e-3` H |
| `Kt` | `50e-3` Vs/rad |
| `Ke` | `50e-3` Vs/rad |

**Aba Mechanical (Figura 3)**

| Campo | Valor |
|-------|-------|
| `Jm` | `100e-6` kg·m² |
| Friction coefficient | `105e-6` Nms |
| Unconstrained mechanical angle | `disabled` |

**Aba Load (Figura 4)**

| Campo | Valor |
|-------|-------|
| Load source | `Model` |
| External/Model load type | `torque` |

Os campos *Load ai pin / offset / gain* ficam desabilitados e não precisam de ajuste. Ao escolher `Model`, o bloco ganha uma entrada, que é interpretada como **torque de carga `T_L` em N·m**.

A aba *Feedback* fica com os valores padrão.

## 4. Probes e SCADA (aquisição)

Marque os sinais a serem vistos no SCADA e dê nomes claros:

| Sinal | Nome sugerido | Unidade |
|-------|---------------|---------|
| Tensão de armadura | `Voltímetro Ideal` | V |
| Corrente de armadura | `Amperímetro ideal` | A |
| Velocidade angular | `E-576 Servo Motor.mechanical speed` | rad/s |
| Torque de carga (ensaio 3) | `T_L` | N·m |

Se a sua versão exigir, habilite o *streaming* do sinal para o SCADA nas propriedades do bloco/probe.

## 5. Compilar e executar

1. No Schematic Editor, clique em **Compile** (`Ctrl+B`) e corrija erros de conexão.
2. Abra o **HIL SCADA** pelo Control Center (**Model ▸ Load to SCADA** ou equivalente).
3. Carregue o modelo compilado no Virtual HIL e clique em **Run / Start simulation**.
4. Monte o painel como na Figura 6 do relatório: um **Scope/Graph** com `ω(t)` e três displays numéricos (voltímetro, amperímetro e velocidade angular).
5. Use a mesma escala de tempo do relatório, **1,0 s/div**, para facilitar a comparação visual entre os ensaios.
6. Em todos os ensaios, exiba ao mesmo tempo tensão, corrente e velocidade, mesmo que o foco seja só uma delas, para manter a rastreabilidade da entrada aplicada.

---

## 6. Ensaio 1: degrau de tensão a partir do repouso

Este é o ensaio já realizado no relatório (Figura 6) e serve de referência.

**Configuração:** fonte fixa em 30 V e `Constant2 = 0` (`T_L = 0`, motor em livre funcionamento).

**Resultados esperados:**

| Grandeza | Teórico | Medido no relatório |
|----------|---------|---------------------|
| Tensão | 30 V | 30,00 V |
| `ω_ss` | 532,86 rad/s | 532,86 rad/s |
| `i_a,ss` | 1,119 A | 1,12 A |

A diferença na corrente é inferior a 0,1 %, compatível com a resolução do amperímetro ideal e com arredondamentos do solver.

**Prints sugeridos:**

1. Esquemático completo com fonte de 30 V, amperímetro e voltímetro visíveis.
2. Curva de `ω(t)` com cursores marcando `ω_ss` e, se possível, o tempo de subida (10 % a 90 %).
3. Painel numérico (voltímetro, amperímetro, velocidade) em regime permanente.

## 7. Ensaio 2: condição livre de entrada (inércia livre)

A tensão de armadura é levada a zero depois que o motor atinge o regime permanente, mantendo `T_L = 0`.

**Alteração no modelo:** troque a fonte de tensão fixa por uma fonte de tensão **controlada por sinal** e alimente-a com um bloco **Step** (degrau negativo, de 30 V para 0 V). Alternativa: alternar manualmente a fonte durante a simulação em tempo real.

| Parâmetro do Step | Valor sugerido |
|-------------------|----------------|
| Valor inicial | `30` V |
| Valor final | `0` V |
| Instante do degrau | `t ≥ 1 s` (sugestão: com `τ1 ≈ 0,1048 s`, o motor já está em regime permanente depois de ≈ 5·τ1 ≈ 0,52 s) |

**Resultado esperado:** `ω(t)` decai de 532,86 rad/s até o repouso, com constante de tempo dominante `τ1 ≈ 0,1048 s`.

**Prints sugeridos:**

1. Configuração do bloco de tensão (Step ou fonte controlada), mostrando o instante em que `v_a` vai a zero.
2. Curva de `ω(t)` com cursor indicando a constante de tempo dominante.
3. Painel numérico no instante inicial (regime permanente antes do corte) e ao final do transitório (velocidade próxima de zero).

## 8. Ensaio 3: transitório temporário (pulso de torque de carga)

A tensão de armadura fica fixa em 30 V e o distúrbio é aplicado como um pulso em `T_L`, na entrada da aba *Load*.

**Alteração no modelo:** substitua o `Constant2 = 0` por um bloco **Pulse**:

| Parâmetro do Pulse | Valor |
|--------------------|-------|
| Amplitude | `0,05` N·m |
| Início | `t = 0,10 s` |
| Fim | `t = 0,15 s` |
| Valor fora do pulso | `0` N·m |

**Resultado esperado:** `ω(t)` cai durante o pulso e recupera parcialmente depois do fim dele. O valor mínimo teórico é `ω ≈ 512,65 rad/s`.

> **Atenção ao instante do pulso:** o relatório descreve este ensaio com o regime permanente já estabelecido. Partindo do repouso, porém, o motor só chega perto de 532,86 rad/s depois de ≈ 0,5 s (≈ 5·τ1). Se o pulso de 0,10 s a 0,15 s for aplicado partindo do repouso, o mínimo de `ω` não será comparável a 512,65 rad/s. Para essa comparação, atrase o pulso para depois do regime permanente (por exemplo, início em `t = 1,0 s` e fim em `t = 1,05 s`, mantendo a duração de 50 ms) ou confirme no MATLAB que o cenário simulado é o mesmo.

**Prints sugeridos:**

1. Configuração do bloco Pulse, mostrando amplitude e instantes de início e fim.
2. Curva de `T_L(t)` (sobreposta ou em painel separado), evidenciando a janela do pulso.
3. Curva de `ω(t)` com cursores no valor mínimo atingido e no valor ao final da janela de observação.
4. Painel numérico nos instantes de regime permanente inicial, mínimo de velocidade e recuperação final.

## 9. Capturas e exportação

1. Salve os prints de cada ensaio com nomes claros, por exemplo `fig_ensaio1_esquematico.png`, `fig_ensaio1_scope.png`, `fig_ensaio2_scope.png`, `fig_ensaio3_scope.png`.
2. Sempre que possível, exporte os dados numéricos (**CSV**) do HIL SCADA para sobrepor as curvas às obtidas no MATLAB (Seção 9.2 do relatório de caracterização).

## Checklist final

- [ ] Modelo montado conforme a Figura 1: motor, fonte de 30 V, amperímetro e voltímetro ideais, `Constant2 = 0`.
- [ ] Abas *Electrical*, *Mechanical* e *Load* configuradas com os valores do E-576.
- [ ] Passo de simulação com `Ts ≤ 200 µs` (amostragem ≥ 5 kHz).
- [ ] Ensaio 1: `ω_ss = 532,86 rad/s` e `i_a,ss ≈ 1,12 A`.
- [ ] Ensaio 2: decaimento livre com `τ1 ≈ 0,1048 s`.
- [ ] Ensaio 3: pulso de 0,05 N·m por 50 ms e `ω` mínimo comparado com ≈ 512,65 rad/s (com o pulso aplicado em regime permanente).
- [ ] Prints salvos e CSVs exportados para a comparação MATLAB vs Typhoon.