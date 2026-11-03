# Simulação — G05, Fase 2, Entrega 01 (Monotanque)

Todas as figuras e todos os números do relatório saem de um único script:
`caracterizacao_monotanque.py`.

## Ferramenta e versão

| Item | Versão usada |
|---|---|
| Python | 3.12.10 |
| NumPy | 2.5.3 |
| SciPy | 1.18.1 (`scipy.integrate.solve_ivp`) |
| Matplotlib | 3.11.2 |

Instalação das dependências:

```bash
pip install -r requirements.txt
```

## Modelo

Modelo não linear do dossiê (balanço de massa + Torricelli):

    A dh/dt = qi(t) - k*sqrt(h) - qd(t)

| Parâmetro | Símbolo | Valor | Unidade |
|---|---|---|---|
| Área da seção transversal | A | 0,50 | m² |
| Coeficiente de descarga agregado | k | 0,010 | m^2,5/s |
| Altura máxima / mínima | h_max / h_min | 1,20 / 0,10 | m |
| Ponto de operação | h0 | 0,50 | m |
| Vazão nominal | qi0 = k·√h0 | 0,0070711 | m³/s |

Os parâmetros estão no início do script (`A`, `K`, `H_MAX`, `H_MIN`, `H0`).

## Solver

`solve_ivp`, método `RK45` (Dormand–Prince), passo variável limitado a
`max_step = 0,1 s`, `rtol = 1e-10`, `atol = 1e-12`, saída gravada a cada 0,05 s.
Na drenagem livre a integração para por evento quando h chega a 1e-12 m.

## Como executar

```bash
cd simulacao
python caracterizacao_monotanque.py
```

Tempo de execução: cerca de 1 min. O script grava:

- as figuras em `../relatorio/figuras/` (`fig-01` a `fig-10`);
- todos os valores numéricos em `resultados.json`.

## O que gera cada figura

| Figura | Arquivo | Ensaio / conteúdo | Condições |
|---|---|---|---|
| 1 | `fig-01-esquema-tanque.png` | esquema físico (R1a) | — |
| 2 | `fig-02-diagrama-blocos.png` | diagrama de blocos (R1a) | — |
| 3 | `fig-03-equilibrio-linearizacao.png` | equilíbrio e reta tangente (R2) | qi0, h0 |
| 4 | `fig-04-ensaio-a-degrau.png` | R3(a) degrau a partir do equilíbrio | h(0) = 0,50 m; qi de qi0 para 1,2·qi0 em t = 50 s; 650 s |
| 5 | `fig-05-ensaio-b-condicao-inicial.png` | R3(b) condição inicial não nula | h(0) = 1,0 m com qi = qi0 (600 s) e com qi = 0 (drenagem livre) |
| 6 | `fig-06-ensaio-c-senoide.png` | R3(c) senoide | qi = qi0·(1 + 0,1·sen ωt), ω = 1/τ; 8 períodos |
| 7 | `fig-07-erro-simulacao-fechada.png` | R4 erro simulado × solução fechada | ensaios (a) e (b) |
| 8 | `fig-08-sensibilidade-area.png` | R5 parâmetro A | A = 0,125; 0,25; 0,5; 1; 2 m², degrau +20 % |
| 9 | `fig-09-sensibilidade-k.png` | R5 parâmetro k | k = 0,005; 0,0075; 0,01; 0,015; 0,02, h(0) = 0,50 m, qi = qi0 |
| 10 | `fig-10-sensibilidade-amplitude.png` | R5 amplitude do degrau | degrau de −50, −20, +20, +50 e +100 % em qi |

## Validação embutida

O script calcula a solução em forma fechada do modelo não linear
(`t_fechado`/`h_fechado`, variável u = √h) e compara com a simulação.
Os tempos característicos (10 %, 63,2 %, 90 %, ±2 %) de cada ensaio são gravados nas
chaves `sim` e `fechado` de `resultados.json`. A Tabela 7 do relatório é montada a partir delas.
