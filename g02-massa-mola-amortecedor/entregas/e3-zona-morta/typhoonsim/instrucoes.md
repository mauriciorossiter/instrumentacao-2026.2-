# Simulação da Zona Morta de um Instrumento — instruções do modelo TyphoonSim

ECOM060 — Instrumentação Eletrônica (UFAL, 2026.2) · Grupo 02 (massa-mola-amortecedor)

## Visão geral

O arquivo `modelo.tse` reproduz a zona morta (Seção 3.3.5 do livro-texto) de um sensor hipotético. A entrada
x(t) (senoide ou onda triangular) passa pelo instrumento ideal de referência (yid = x, ganho unitário) e, em
seguida, pelo bloco C function `dead_zone`, que aplica uma zona morta de largura Zx. O objetivo é observar os
patamares da saída nas inversões de sentido da entrada e verificar que a largura medida coincide com Zx.

## Topologia (cadeia de blocos)

```
Input (triangular)  ──┬──► [Instrumento Real Descrito por f[]] ──┬──► dead_zone.in ──► DeadZoneOutput
  ou Input (sin)       │      x(t), xm(t), xi(t) ─► y(t)          │        ▲
                       └──► OriginalInput                         └──► RawOutput
spurious_input (0) ──► xm(t) e xi(t)          Valor da Zona Morta (5) ──► dead_zone.val
```

- Subsistema `Instrumento Real Descrito por f[]`: `f0(t)` e `g0(t)` somados em `Sum1` (saída `y(t)`).
  Com `spurious_input = 0`, resulta y = x, ou seja, a função estática fe do instrumento ideal.
- Probes (todos no `Scope1`): `OriginalInput` (x), `RawOutput` (yid = x) e `DeadZoneOutput` (y).
- No arquivo, a fonte ligada é `Input` (onda triangular); o bloco `Input (sin)` está presente, mas desconectado.

## Valores dos elementos

| Elemento | Parâmetro | Valor |
|---|---|---|
| `Valor da Zona Morta` (Constant) | Zx | 5 |
| `spurious_input` (Constant) | xm = xi | 0 |
| `Input` (C function, triangular) | amplitude / período | 10 / 10 s (0 → 10 → 0; \|dx/dt\| = 2 un/s) |
| `Input (sin)` (C function) | amplitude / frequência / offset | 10 / 0,1 Hz (período 10 s) / 0 |
| `dead_zone` | ganho da parte ativa | 1,0 |
| Blocos C function | execution rate | 0,0001 s (100 µs) |
| Simulação | dispositivo / tempo / passo máx. | VHIL+ / 20 s / 1e-4 s |

## Elementos não lineares (blocos C function)

**f0(t)** e **g0(t)** (dentro do subsistema): `y = x*(1 + (xm*0.1))` e `y = (xm*0.2)*(xi)`. Com xm = xi = 0,
a soma reduz-se a yid = x.

**dead_zone** — implementa a zona morta por limitação (clamp), com saída anterior y(t⁻) guardada em `static`:

- y(t) = x(t) − Zx/2, se y(t⁻) < x(t) − Zx/2 (entrada subindo);
- y(t) = x(t) + Zx/2, se y(t⁻) > x(t) + Zx/2 (entrada descendo);
- y(t) = y(t⁻), caso contrário (dentro da zona morta).

```c
static double out_ant = 0.0;          // valor anterior da saída
double Zx = val, ganho = 1.0;         // largura da zona morta; fe: y_id = x
double sup = ganho * in - Zx / 2.0;   // limite quando a entrada sobe
double inf = ganho * in + Zx / 2.0;   // limite quando a entrada desce
double saida = out_ant;
if (saida < sup) saida = sup;
if (saida > inf) saida = inf;
out = saida;  out_ant = saida;
```

**Input** / **Input (sin)** — fontes geradas em C a partir de um tempo interno `static double t`
incrementado de `Ts = 0.0001` a cada passo: triangular via `fmod(t, periodo)` (rampas de subida e descida)
e senoide `offset + amplitude * sin(2*M_PI*freq*t)`.

## Como executar

1. Abrir `modelo.tse` no Schematic Editor do TyphoonSim.
2. Conferir em *Model Settings*: dispositivo VHIL+, tempo de simulação 20 s. Manter o execution rate numérico
   (0,0001) em todos os blocos C function, evitando o erro de compilação por herança de taxa nas fontes.
3. Ajustar Zx, se desejado, na constante `Valor da Zona Morta` (valor usado no relatório: 5).
4. **Ensaio 1 — entrada senoidal:** desconectar `Input` da junção de entrada e ligar `Input (sin)` em seu lugar
   (alimentando `OriginalInput` e `x(t)` do subsistema). Compilar, carregar no (V)HIL e executar.
5. **Ensaio 2 — entrada triangular:** manter/religar `Input` na junção de entrada (configuração do arquivo).
   Compilar, carregar e executar.
6. Em cada ensaio, abrir o `Scope1` e observar `OriginalInput` (azul), `RawOutput` (verde) e `DeadZoneOutput`
   (vermelho). `RawOutput` fica sobreposto a `OriginalInput`.
7. Para a verificação quantitativa, exportar os sinais do Scope em CSV (20 s, passo de 100 µs, 200 001 amostras)
   e traçar y em função de x (característica estática) e os patamares ∆y = 0 no tempo.

## Resultados esperados

- **Senoide (±10):** a saída congela nos picos e vales, com patamares em torno de ±7,5.
- **Triangular (0 → 10 → 0):** saída deslocada de Zx/2 nas rampas, patamares em torno de 7,5 (vértice superior)
  e 2,5 (vértice inferior); amplitude efetiva reduzida em Zx.
- **Verificação:** no plano (x, y) surge o paralelogramo com ∆x = 5,00; cada patamar dura 2,5 s, que a 2 un/s
  dá ∆x = 5. A largura medida, ∆x = 5,0000, coincide com Zx = 5 (erro nulo na resolução do passo).

## Captura de tela (esquemático + painel SCADA)

![Esquemático e painel de instrumentação](captura-scada.png)
