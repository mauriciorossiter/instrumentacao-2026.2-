# Caracterização da planta — instruções da simulação

ECOM060 Instrumentação Eletrônica · UFAL · 2026.2 · Grupo 02 · Fase 2, Entrega 01

## Ferramenta e versão

Python 3.12 com numpy, scipy (`solve_ivp`, RK45, rtol = 1e-10, atol = 1e-12, passo máximo de 1 ms) e matplotlib.
Instalação: `pip install numpy scipy matplotlib`.

## Parâmetros

m = 1,00 kg · c = 6,00 N·s/m · k = 100 N/m · F0 = 10 N · x(0) = 0,10 m (ensaio b) · pulso de 1,5·F0 entre 2,0 e
2,5 s (ensaio c).

## Passos

```bash
cd simulacao
python caracterizacao.py ../relatorio/figuras dados
```

Gera:

| Figura | Requisito | CSV |
|---|---|---|
| `fig-02-ensaios-r3.png` | R3 (a), (b), (c) com a solução analítica sobreposta | `dados/fig-02-ensaios-r3-{a,b,c}.csv` |
| `fig-03-sensibilidade-r5.png` | R5: m, c, k em 5 níveis | `dados/fig-03-sensibilidade-r5.csv` |
| tabela R4 | validação cruzada | `dados/resultados-caracterizacao.json` |

`fig-01-sistema-equivalente.png` é um diagrama (não vem de dados). `estilo.py` define as cores das figuras.
