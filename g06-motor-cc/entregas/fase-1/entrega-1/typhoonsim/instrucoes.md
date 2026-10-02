# TyphoonSim, guia da Entrega 01 (G06)

**Cadeia termopar (Cap. 7.4) e amplificador de instrumentação (Cap. 6.3.3)**

**Software:** Typhoon HIL Control Center / TyphoonSim
**Versão:** 2026.3 (release de 06.08.2026)

A ideia deste guia é montar, no TyphoonSim, a mesma cadeia que projetamos no relatório: o termopar ideal seguido do amplificador de instrumentação. Depois de montar, excitamos a entrada com uma varredura de temperatura que cobre a faixa nominal de 0 a 250 °C e registramos a força eletromotriz de entrada e a saída condicionada de 0 a 5 V, que é o que R4 pede.

## Valores de projeto que vêm do relatório

- **Sensibilidade do termopar Tipo K:** `S_K = 40,6 µV/°C`, ou seja `40.6e-6`.
- **Faixa:** `ΔT = 0 a 250 °C`, o que dá `v_in,FS = 10,15 mV`.
- **Ganho do amplificador de instrumentação:** `G = 494,07`, sendo o 1º estágio `1 + 2·R2/R1 = 494,07` (com `R2 = 24,9 kΩ` e `R1 = 101 Ω`) e o 2º estágio `R4/R3 = 1` (com `R3 = R4 = 10 kΩ`).
- **Saída alvo:** 0 a 5 V, com erro de no máximo 2 % do fundo de escala.

---

## 0. Sobre a versão 2026.3

O fluxo abaixo usa o **Schematic Editor**, onde editamos o modelo, e o **HIL SCADA**, onde fazemos a aquisição e vemos o scope. Esses dois ambientes são estáveis entre versões, então o roteiro vale bem para a 2026.3. Alguns nomes de biblioteca ou de bloco podem aparecer com um rótulo um pouco diferente, e nesses casos indiquei o bloco equivalente. Quando a nomenclatura não bater, a barra de busca de blocos resolve: basta digitar o nome do bloco.

> **A conferir na sua instalação 2026.3:** os rótulos exatos de menu, que descrevo pelo caminho mais comum.

## 1. Criar o projeto e o modelo

1. Abra o Typhoon HIL Control Center (2026.3).
2. No Schematic Editor, crie um modelo novo em **File ▸ New** (arquivo `.tse`).
3. Salve como `entrega01_g06_termopar.tse`, na pasta da entrega.
4. Configure o dispositivo de execução para **Virtual HIL**, que roda por software e não precisa de hardware. Isso fica em **Model ▸ HIL Device Settings** (ou no seletor de dispositivo da barra), onde você escolhe *VHIL / Virtual HIL Device*. Como a cadeia é lenta, um passo de simulação `Ts` de `1e-3 s` (1 ms) já basta. O campo de passo costuma ficar em **Simulation ▸ System settings ▸ Execution rate/Timestep**, que é bom conferir na 2026.3.

## 2. Blocos da cadeia (domínio Signal Processing)

Todos os blocos vêm da biblioteca **Signal Processing**, no painel à esquerda. Se não encontrar algum pelo nome, use a barra de busca de blocos e digite o nome que está na tabela.

| # | Bloco (biblioteca) | Nome sugerido | Parâmetro | Valor | Observação |
|---|--------------------|---------------|-----------|-------|------------|
| 1 | Ramp (Sources) | `T_sweep` | slope / final | varre 0 a 250 (ver §3) | varredura de temperatura |
| 2 | Gain (Math) | `Gain_TC` | Gain | `40.6e-6` | sensibilidade do termopar |
| 3 | Gain (Math) | `Gain_stage1` | Gain | `494.07` | primeiro estágio, 1 + 2·R2/R1 |
| 4 | Gain (Math) | `Gain_stage2` | Gain | `1` | segundo estágio, R4/R3 |
| 5 | Saturation (Signal Processing) | `Sat` | Upper / Lower | `5 / 0` | impõe o fundo de escala |
| 6 | Probe (Signals & Probes) ×3 | `T`, `v_in`, `v_out` | ver §4 | — | pontos de medida |

Usamos só blocos de ganho porque a cadeia é ideal. O termopar é representado pela sua sensibilidade, que é um ganho `S_K` convertendo °C em volts, e o amplificador de instrumentação, pela Eq. 6.28, `v_o = (R4/R3)(1 + 2R2/R1)(v2 − v1)`. Como o sensor ideal entra em modo *single-ended*, o termo `(v2 − v1)` é o próprio `v_in`, e os dois blocos de ganho reproduzem os dois estágios do amplificador.

### Conexões (fio a fio)

```text
T_sweep ──► Gain_TC ──► Gain_stage1 ──► Gain_stage2 ──► Sat ──► (Probe v_out)
   │           │
   │           └─► (Probe v_in)    # f.e.m. do termopar, em mV
   └─► (Probe T)                   # temperatura varrida, em °C
```

Na prática, ligue o Probe `T` na saída de `T_sweep`, para ver a temperatura em °C; o Probe `v_in` na saída de `Gain_TC`, para ver a força eletromotriz em mV; e o Probe `v_out` na saída de `Sat`, para ver a saída condicionada em volts.

## 3. Configurar a varredura de temperatura (R4)

A meta é varrer `ΔT` de forma linear de 0 a 250 °C. Para isso, escolhemos um tempo de simulação `t_sim` e ajustamos a rampa para chegar a 250 no fim.

**Opção A, com o bloco Ramp direto.** Configure o `T_sweep` (Ramp) para iniciar em 0 e ter inclinação `slope = 250 / t_sim`. Por exemplo, com `t_sim = 10 s` a inclinação fica em 25 °C/s, então em 10 s a temperatura vai de 0 a 250 °C. Na 2026.3 o bloco Ramp costuma expor *Slope*, *Start time* e, às vezes, *Initial value*; se ele tiver valor inicial, deixe em 0.

**Opção B, com Constant somado a Ramp.** Serve quando queremos partir de um offset, como no modelo antigo da equipe: um Constant com o offset em °C mais um Ramp entram num Sum, e a soma vai para o `Gain_TC`. Nesta entrega o offset é 0, porque a junta fria ideal está em 0 °C, então a Opção A já resolve.

A orientação também aceita um degrau no lugar da varredura. Para o termopar, a varredura cobrindo a faixa nominal mostra a reta de calibração entre entrada e saída, que é mais informativa, e por isso é a que recomendamos aqui.

## 4. Probes e SCADA (aquisição)

Renomeie cada Probe para `T`, `v_in` e `v_out`, porque esse nome é o que aparece no scope depois. Se a sua versão exigir, habilite o *streaming* do Probe para o SCADA em **Probe ▸ properties**.

## 5. Compilar e executar

1. No Schematic Editor, clique em **Compile** (`Ctrl+B` ou o botão Compile) e corrija eventuais erros de conexão.
2. Abra o **HIL SCADA** pelo Control Center (o caminho costuma ser **Model ▸ Load to SCADA** ou equivalente na 2026.3).
3. Carregue o modelo compilado no Virtual HIL e clique em **Run / Start simulation**.
4. Adicione um widget de **Scope / Graph** no SCADA e selecione os sinais `T`, `v_in` e `v_out`. Fica melhor separar em dois eixos, um para `v_in` em mV e outro para `v_out` em V, usando `T` como referência.
5. Ajuste a base de tempo do scope para cobrir todo o `t_sim`, por exemplo os 10 s. O Capture/Scope fica no painel do SCADA, que é bom localizar na 2026.3.

## 6. Verificação dos resultados (R5)

Com a tolerância declarada de 2 % do fundo de escala, confira no scope os pontos abaixo:

| ΔT (°C) | v_in esperado | v_out esperado | % do FS |
|--------:|--------------:|---------------:|--------:|
| 0   | 0 mV     | 0 V     | 0 %     |
| 50  | 2,03 mV  | 1,003 V | 20,1 %  |
| 125 | 5,075 mV | 2,507 V | 50,1 %  |
| 200 | 8,12 mV  | 4,012 V | 80,2 %  |
| 250 | 10,15 mV | 5,015 V | 100,3 % |

No fundo de escala a saída chega a cerca de 5,015 V, ou seja, um erro de 0,30 %, que cabe dentro dos 2 %. Como a cadeia é ideal, sem efeitos não ideais, a curva de `v_out` em função de `ΔT` deve sair uma reta; esses efeitos não ideais entram só na Entrega 02. Se a saída saturar antes de 250 °C ou o erro passar de 2 %, ajuste o `Gain_stage1`, que equivale a mexer no `R1`, e refaça a conferência.

## 7. Capturas para o relatório

Salve as duas imagens na pasta `figs/`, porque o `.tex` já aponta para elas:

1. `figs/fig_topologia_typhoon.png`, um print do Schematic Editor com a cadeia completa (`T_sweep` → `Gain_TC` → `Gain_stage1` → `Gain_stage2` → `Sat`, mais os probes).
2. `figs/fig_scope_varredura.png`, um print do scope do SCADA com `v_in` e `v_out` durante a varredura de 0 a 250 °C.

Depois de colocar os PNGs, recompile o `.tex` e as figuras entram no lugar dos espaços reservados.

---

## Checklist final (mapeado à orientação)

- **R1**, termopar Tipo K, ativo e por deflexão, com `S_K = 40,6 µV/°C` (fonte: datasheet Pyromation e Tabela 7.4 do Aguirre).
- **R2**, saída de 0 a 5 V, erro de no máximo 2 % do fundo de escala e ruído referido à entrada de poucos µV.
- **R3**, memória de cálculo (ganho alvo 492,6, resistores escolhidos, ganho obtido 494,07 e erro de 0,30 %).
- **R3b**, justificativa da escolha (alta impedância de entrada, CMRR e sinal diferencial flutuante) comparada com os circuitos 6.3.1 e 6.3.2.
- **R4**, cadeia montada e simulada no TyphoonSim 2026.3, com as capturas salvas em `figs/`.
- **R5**, verificação com erro de fundo de escala de 0,30 %, abaixo dos 2 %.