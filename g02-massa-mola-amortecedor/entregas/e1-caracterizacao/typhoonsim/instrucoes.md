# Entrega 1 — Caracterização do sistema massa-mola-amortecedor

Modelo: `modelo.tse` (TyphoonSim 2026.2, `hil_device = VHIL+`, `simulation_method = exact`,
passo de simulação automático, `dsp_timer_periods = 100e-6, 50e-3`).

## Analogia adotada

Analogia força-tensão (força → tensão, velocidade → corrente). O sistema mecânico de
segunda ordem

    m x'' + b x' + k x = F(t)

vira um circuito **RLC série** alimentado por fonte de tensão:

| Grandeza mecânica | Elemento elétrico | Componente no modelo | Valor |
|---|---|---|---|
| massa `m` = 1 kg | indutância `L` | `L1` | 1 H |
| amortecimento `b` = 6 N·s/m | resistência `R` | `R1` | 6 Ω |
| rigidez `k` = 100 N/m | `1/C` | `C1` | 10e-3 F (`1e-2`) |
| força `F(t)` | fonte de tensão | `Vsp1` | comandada por `C function1` |
| deslocamento `x` | carga no capacitor | `Deslocamento (cm)` | medição de tensão em `C1` |

Com esses valores: `ωn = sqrt(k/m) = 10 rad/s` e `ζ = b/(2·sqrt(k·m)) = 0,3` —
sistema subamortecido, como descrito no relatório.

## Topologia

```
C function1  ──>  Vsp1 (fonte de tensão controlada por sinal)
Vsp1.p_node  ──  L1.p_node
L1.n_node    ──  R1.p_node
R1.n_node    ──  Junction1  ──  C1.p_node
C1.n_node    ──  Junction2  ──  Vsp1.n_node
"Deslocamento (cm)" medido entre Junction1 e Junction2 (tensão sobre C1)
Scope1 registra o sinal de deslocamento
```

- `Junction1` = nó entre `R1` e `C1`
- `Junction2` = nó de retorno (referência da fonte)

## Elemento não linear / gerador de entrada

`C function1` (`execution_rate = 1e-05`) gera o degrau de força:

```c
static real_t t = 0.0;
real_t F0     = 10.0;   /* amplitude do degrau [N] */
real_t t_step = 0.01;   /* instante de aplicação [s] */
real_t ts     = 1e-5;   /* passo de integração [s] */

if (t < t_step) { out = 0.0; }
else            { out = F0;  }

t = t + ts;
```

Não há elemento genuinamente não linear no circuito — o sistema é linear de 2ª ordem.
O bloco em C existe apenas para sintetizar a entrada.

## Como executar cada ensaio

Os três ensaios do relatório são obtidos alterando **apenas** o bloco `C function1` e as
condições iniciais de `L1`/`C1`:

1. **Resposta ao degrau (repouso → degrau de 10 N)**
   Código como acima, `F0 = 10.0`, `t_step = 0.01`.
   `L1.initial_current = 0`, `C1.initial_voltage = 0`.
   Rodar por ~3 s e observar `Deslocamento (cm)` no `Scope1`.

2. **Resposta livre (condição inicial, entrada nula)**
   Trocar a saída para `out = 0.0` (a linha já está no arquivo, comentada:
   `out = F0;//0.0;//F0;`) e definir a condição inicial em `C1.initial_voltage`
   (deslocamento inicial) e/ou `L1.initial_current` (velocidade inicial).

3. **Pulso temporário de força**
   Substituir o `if` por uma janela finita, por exemplo
   `out = (t >= t_step && t < t_step + 0.2) ? F0 : 0.0;`
   e observar a recuperação do regime permanente.

A validação numérica (RK45) e a comparação contra a solução algébrica fechada estão no
notebook `../ECOM060_massa_mola_amortecedor.ipynb`.

## Captura de tela (esquemático + painel SCADA)

<!-- PENDENTE: adicionar captura-scada.png nesta pasta e descomentar a linha abaixo -->
<!-- ![Esquemático e painel de instrumentação](captura-scada.png) -->
