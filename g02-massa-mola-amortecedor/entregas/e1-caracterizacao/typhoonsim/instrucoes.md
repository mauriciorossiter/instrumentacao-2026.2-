# Caracterização do Sistema Massa–Mola–Amortecedor — instruções do modelo TyphoonSim

ECOM060 — Instrumentação Eletrônica (UFAL, 2026.2) · Grupo 02 (massa-mola-amortecedor)

## Visão geral

O arquivo `modelo.tse` implementa o massa–mola–amortecedor (m ẍ + c ẋ + k x = F(t)) pelo seu análogo elétrico
direto, o circuito RLC série (L q̈ + R q̇ + q/C = v(t)), com o mapeamento usado no relatório:
m ↔ L, c ↔ R, k ↔ 1/C, x ↔ q, F ↔ v. Uma fonte de tensão controlada por sinal faz o papel da força F(t) e a
tensão no capacitor é a grandeza observada como deslocamento. O objetivo é repetir no TyphoonSim os ensaios de
caracterização do relatório, como via independente de verificação da solução numérica (RK45) e analítica.

## Topologia (circuito elétrico equivalente)

```
 C function1 (F(t)) ──► Vsp1.in

   Vsp1 (+) ──[ L1 = m ]──[ R1 = c ]──●── Junction1 ──┬── "Deslocamento (cm)" (+)
                                     │                │
                                  [ C1 = 1/k ]        │
                                     │                │
   Vsp1 (−) ─────────────────────────●── Junction2 ──┴── "Deslocamento (cm)" (−)
```

- Malha série única: `Vsp1` → `L1` → `R1` → `C1` → retorno a `Vsp1`. A corrente da malha é i = q̇ (análoga à
  velocidade ẋ) e a carga do capacitor q é análoga ao deslocamento x.
- O voltímetro `Deslocamento (cm)` mede a tensão em `C1`: v_C = q/C = 100·q. Como q ↔ x [m], v_C em volts
  corresponde numericamente ao deslocamento em centímetros (por isso o nome do sinal).
- `Scope1` exibe apenas o sinal `Deslocamento (cm)` (vermelho).

## Valores dos elementos

| Elemento | Análogo mecânico | Valor no `.tse` | Valor no relatório |
|---|---|---|---|
| `L1` (Inductor) | massa m | 1 H | 1,00 kg |
| `R1` (Resistor) | amortecimento c | 6 Ω | 6,00 N·s/m |
| `C1` (Capacitor) | 1/k | 1e-2 F | k = 100 N/m |
| `C function1` (F(t)) | força F0 | degrau de 10 V em t_step = 0,01 s | F0 = 10 N |
| `C1` / `L1` | condições iniciais | v_C(0) = 0 V, i_L(0) = 0 A (padrão) | x(0) = 0, ẋ(0) = 0 |
| `C function1` | execution rate / incremento de tempo interno | 1e-5 s / ts = 1e-5 s | — |
| `Deslocamento (cm)` | execution rate | 100e-6 s | — |
| Simulação | dispositivo / método / passo máx. / tempo | VHIL+ / exact / 1e-4 s / 2,5 s | 2,5 s (Cenários 1 e 2) |

Grandezas derivadas (iguais nas duas vias): ωn = 1/√(LC) = 10 rad/s, ζ = (R/2)·√(C/L) = 0,30,
G(s) = 1/(s² + 6s + 100), polos −3,000 ± j 9,53939 rad/s.

## Elementos não lineares

Não há elementos não lineares: o circuito é RLC série linear e invariante no tempo, coerente com as hipóteses
do relatório (Hooke linear, amortecimento viscoso puro, sem atrito seco). O único bloco C function é a fonte
de entrada, que gera um degrau a partir de um tempo interno `static`:

```c
static real_t t = 0.0;
real_t F0 = 10.0;  real_t t_step = 0.01;  real_t ts = 1e-5;
if (t < t_step) { out = 0.0; } else { out = F0; }
t = t + ts;
```

## Como executar cada ensaio

1. Abrir `modelo.tse` no Schematic Editor do TyphoonSim e conferir em *Model Settings*: dispositivo VHIL+,
   passo máximo 1e-4 s, tempo de simulação 2,5 s.
2. Compilar o modelo, carregá-lo no (V)HIL e iniciar a simulação; abrir o `Scope1` e observar
   `Deslocamento (cm)`. Para análise quantitativa, exportar o sinal do Scope em CSV.
3. **Ensaio 1 — degrau a partir do repouso** (configuração do arquivo): `C1` e `L1` com condição inicial nula
   e `C function1` com F0 = 10. Executar por 2,5 s.
4. **Ensaio 2 — resposta livre:** no `C function1`, fazer a saída nula (o código já traz a alternativa
   comentada `//0.0`) e definir `initial_voltage` de `C1` em 10 V (x(0) = 0,10 m ↔ q = 0,1 C). Executar por 2,5 s.
5. **Ensaio 3 — pulso de força:** partir do regime permanente (`initial_voltage` de `C1` = 10 V, saída = 10)
   e alterar o código do `C function1` para gerar 15 (1,5 F0) entre t = 2,0 s e 2,5 s, retornando a 10 em
   seguida; ajustar o tempo de simulação para 6,0 s. Esta variante não está salva no arquivo.

## Resultados esperados (relatório, em V ≙ cm)

- **Degrau:** valor final 10 (x∞ = 0,100 m); primeiro pico 13,72 (x = 0,137233 m) cerca de Tp = 0,3293 s após
  o degrau; overshoot 37,23%; tempo de subida 10–90% medido 0,132 s; entrada na faixa de ±2% 1,123 s após
  o degrau. No `.tse` o degrau ocorre em t = 0,01 s, então os instantes ficam deslocados de 0,01 s.
- **Resposta livre:** oscilação em torno de 0 com período Td ≈ 0,659 s (ωd = 9,54 rad/s, fd = 1,52 Hz);
  picos positivos 1,386 (t = 0,6586 s) e 0,192 (t = 1,3174 s), que pelo decremento logarítmico
  (δ = 1,97597) devolvem ζ = 0,300.
- **Pulso:** pico 16,86 (x ≈ 0,16862 m) em t ≈ 2,329 s, vale 7,98 (x ≈ 0,07980 m) em t ≈ 2,806 s e retorno
  definitivo à faixa de ±2% em torno de 10 em t = 3,549 s; deslocamento máximo dentro de |x| ≤ 0,20 m.

## Captura de tela (esquemático + painel SCADA)

![Esquemático e painel de instrumentação](captura-scada.png)
