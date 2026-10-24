# Instruções de reprodução — Pêndulo Invertido (ECOM060, Equipe G03)

Caracterização no domínio de origem: ensaios, validação cruzada e sensibilidade.

## Ambiente
- Python 3 (resultados do relatório gerados com Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, Matplotlib 3.10.8)
- `pip install -r requirements.txt`

## Execução
Na pasta `g03-pendulo-invertido/entregas/fase-2/e1-caracterizacao/simulacao/`:

```bash
python simulacao.py   # ensaios, validação, sensibilidade, retrato de fase (~15 s)
python diagrama.py    # Figura 1 (diagrama de blocos)
```

## Solver
`scipy.integrate.solve_ivp`, método `DOP853`, `rtol=1e-10`, `atol=1e-12`.

## Parâmetros nominais
m = 0,50 kg; l = 1,00 m; b = 0,05 N·m·s/rad; g = 9,81 m/s²; J = m·l² = 0,50 kg·m².

## Ensaios
| Ensaio | Topo (θ = 0) | Base (θ = π) |
|---|---|---|
| Degrau | u0 = 0,5 N·m | u0 = 2,5 N·m |
| Condição inicial | θ0 = 0,05 rad | δ0 = 0,30 rad (δ = θ − π) |
| Pulso | 1,0 N·m por 0,5 s | 1,0 N·m por 0,5 s |

## Saídas
| Arquivo | Seção do relatório |
|---|---|
| `figuras/fig_diagrama.png` | 1.1 (Figura 1) |
| `figuras/fig_degrau.png` | 3.1 (Figura 2) |
| `figuras/fig_ci.png` | 3.2 (Figura 3) |
| `figuras/fig_pulso.png` | 3.3 (Figura 4) |
| `figuras/fig_fase.png` | 3.4 (Figura 5) |
| `figuras/fig_validacao.png` | 4.2 (Figura 6) |
| `figuras/fig_sensibilidade.png` | 5 (Figura 7) |
| `resultados/resultados.json` | todos os valores numéricos citados (polos, ζ, ωn, torque crítico, tabelas de validação e sensibilidade) |
