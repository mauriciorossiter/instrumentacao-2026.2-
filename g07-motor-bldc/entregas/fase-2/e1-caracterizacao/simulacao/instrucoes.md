# Simulação — G07, Fase 2, Entrega 1: Caracterização da Planta

Motor BLDC MOONS' R42BLD30L3, caracterizado no domínio de origem (eletromecânico).

## Ferramentas e versões

| Ferramenta | Versão | Uso |
|---|---|---|
| Python | 3.13 | modelos médio (reduzido) e trifásico chaveado, figuras 2 a 8 |
| NumPy / SciPy / Matplotlib | 2.5 / 1.18 / 3.11 | integração, análise e gráficos |
| Typhoon HIL Schematic Editor + TyphoonSim | 2026.3 | `modelo.tse`, ensaios cujos dados estão em `dados-typhoon/` |

Instalação (Python): `pip install numpy scipy matplotlib`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `bldc.py` | parâmetros (dicionário `P`), modelo médio, modelo trifásico chaveado, controle da malha fechada do `.tse`, soluções fechadas |
| `estilo.py` | vírgula decimal nas figuras (importado pelos scripts) |
| `ensaios.py` | ensaios (a), (b) e (c), validade da redução e sensibilidade no modelo reduzido; gera `resultados.json` |
| `malha_fechada.py` | malha fechada original do `.tse` (modo 0) no modelo trifásico |
| `sens_trifasico.py` | sensibilidade (R5) na forma original trifásica; lê `resultados.json` |
| `typhoon_cmp.py` | compara os CSV do TyphoonSim com o modelo trifásico nas condições do `.tse` |
| `modelo.tse` | modelo Typhoon com seletor de ensaio (`g07_modo`) |
| `dados-typhoon/modo_*.csv` | dados exportados do `Scope_motor` do TyphoonSim, um arquivo por ensaio |

## Parâmetros

Valores nominais do dossiê oficial, iguais ao catálogo MOONS (Tab. 1 do relatório). Estão em `P`, em `bldc.py`, e em *Model initialization* no `modelo.tse`.

| Símbolo | Valor | Observação |
|---|---|---|
| `Vs` | 36 V | tensão do barramento |
| `Rs` | 1,60 Ω por fase (`R_LL` = 3,2 Ω) | dossiê |
| `Ls` | 1,90 mH por fase, igual a L − M (`L_LL` = 3,8 mH) | dossiê |
| `k = kt = ke` | 0,048 N·m/A | dossiê |
| `J` | 3,3×10⁻⁶ kg·m² | dossiê |
| `B` | 1×10⁻⁶ N·m·s/rad | hipótese; o dossiê não fornece |
| `p` | 4 pares de polos | |
| carga | `T_L = b2·n²`, `b2` = 5×10⁻⁹ N·m/rpm² | 0,08 N·m a 4000 rpm |
| PWM | 10 kHz; controle a `Ts` = 5 µs | |
| `Emf` (Typhoon) | k·1000·2π/60 = 5,027 V/krpm | FCEM de pico linha-linha, trapezoidal |

Configuração numérica:
- **Modelo médio:** DOP853 (`solve_ivp`), rtol = atol = 1e-12. Para conferência, também RK4 com passo fixo de 2 µs.
- **Modelo trifásico:** Euler explícito com passo fixo de 0,25 µs.

## Como gerar cada figura (Python)

Execute dentro desta pasta, nesta ordem. `sens_trifasico.py` depende do `resultados.json` gerado por `ensaios.py`. Tempo total: cerca de 6 min.

```
python ensaios.py
python malha_fechada.py
python sens_trifasico.py
python typhoon_cmp.py
```

| Figura do relatório | Arquivo gerado | Script |
|---|---|---|
| Fig. 1 — diagrama de blocos | diagrama do modelo, desenhado no relatório; não é resultado de simulação | — |
| Fig. 2 — degrau (ensaio a) | `fig_degrau.pdf` | `ensaios.py` |
| Fig. 3 — condição inicial não nula (ensaio b) | `fig_ci.pdf` | `ensaios.py` |
| Fig. 4 — pulso de carga (ensaio c) | `fig_pert.pdf` | `ensaios.py` |
| Fig. 5 — malha fechada original (modo 0) | `fig_mf.pdf` | `malha_fechada.py` |
| Fig. 6 — validade da redução | `fig_validade.pdf` | `ensaios.py` |
| Fig. 7 — TyphoonSim × Python | `fig_typhoon.pdf` | `typhoon_cmp.py` (lê `dados-typhoon/`) |
| Fig. 8 — sensibilidade | `fig_sens.pdf` | `ensaios.py` |
| Tab. 5, colunas "forma original" | `sens_trifasico.json` | `sens_trifasico.py` |
| Tabelas 3 e 4 (números) | `resultados.json`, `malha_fechada.json`, `typhoon_cmp.json` | scripts acima |

Os PNG de `relatorio/figuras/` são esses PDFs convertidos para PNG a 220 dpi. Cada script grava seus arquivos na pasta em que é executado.

## Como executar os ensaios no TyphoonSim (`modelo.tse`)

1. Abra `modelo.tse` no Typhoon HIL Schematic Editor 2026.3 e vá em **View > Change perspective > TyphoonSim**.
2. Em **Model > Model settings > Model initialization**, escolha o ensaio pela variável `g07_modo`:

| `g07_modo` | Ensaio | Ajustes |
|---|---|---|
| 0 | malha fechada original (Throttle 82,9 % → 4000 rpm) | — |
| 1 | (a) degrau em malha aberta a partir do repouso | `g07_d_ini = 0`, `g07_d_deg = 0.7074`, `g07_t_deg = 0` |
| 1 | (a) degrau a partir do equilíbrio de cerca de 4000 rpm | `g07_d_ini = 0.867`, `g07_d_deg = 0.887`, `g07_t_deg = 0.15` |
| 2 | (b) condição inicial não nula: malha fechada até 0,15 s, depois `d = g07_d_ci` | `g07_d_ci = 0`: desaceleração livre |
| 3 | (c) pulso de carga de 0,02 N·m entre 0,10 e 0,20 s, malha aberta com `d = 0.7074` | — |
| 4 | (c) o mesmo pulso, em malha fechada | — |

3. Compile, inicie a simulação e abra o `Scope_motor`. Sinais disponíveis: `n` [rpm], `torque` [N·m], `Ia`, `Ib`, `Ic` [A], `G07_motor_duty`, Hall A/B/C e `G07_torque_carga` [N·m].
4. Exporte o Scope em CSV com o nome `modo_<n>.csv`, ou `modo_1_repouso.csv` / `modo_1_equilibrio.csv`, e salve em `dados-typhoon/`. Depois rode `python typhoon_cmp.py` para gerar a Fig. 7.

Resultados de referência no TyphoonSim (Tab. 4 do relatório):

| Ensaio | Resultado |
|---|---|
| modo 0 | ≈ 4001 rpm |
| modo 1 do repouso | ≈ 3622 rpm |
| modo 1 do equilíbrio | ≈ 3941 rpm, sem resposta ao degrau |
| modo 2 | n = 2533 / 1848 / 1018 rpm em 0,16 / 0,17 / 0,20 s |
| modo 3 | Δn ≈ −232 rpm durante o pulso |
| modo 4 | ≈ 4000 rpm; o controle compensa o pulso de carga |

No modo 1, a portadora é amostrada a 5 µs, então a razão cíclica efetiva varia em passos de 0,1. Por isso 0,7074 equivale a 0,75, e 0,867 e 0,887 equivalem ambos a 0,85.

**Verificação:** em regime, `torque` ÷ corrente de fase deve dar cerca de 0,048 N·m/A.
