# Simulação — Fase 2, Entrega 01 (G08): caracterização da planta

Gerador síncrono ligado a barramento infinito (SMIB), modelo clássico (*swing equation*):

    (2H/ws) d²δ/dt² = Pm − Pmax·sen δ − D·dδ/dt ,   Pmax = E'V/X

Estados: δ [rad] e Δω = dδ/dt [rad/s elétricos]; potências em pu ("forma A").

A planta foi simulada em duas ferramentas independentes, com os mesmos parâmetros (`parametros.py`):

1. **Python** (referência): RK4 próprio de passo fixo; gera as figuras 1–7 e 9–12 e todos os números de R2–R5.
2. **TyphoonSim** (segunda ferramenta): o diagrama de blocos da Figura 1b só com blocos nativos (`typhoonsim/`);
   os três ensaios são comparados com o Python na figura 8.

## Ferramenta e versão

| Item | Versão usada nesta entrega |
|---|---|
| Python | 3.12.10 (Windows 11) |
| NumPy | 2.4.6 |
| Matplotlib | 3.11.1 |
| Solver (Python) | Runge–Kutta clássico de 4ª ordem, **passo fixo h = 1 ms**, implementado em `modelo.py` (função `simula`) |
| TyphoonSim | 2026.2, simulação offline (Schematic Editor), blocos de sinal com taxa de execução de **1 ms** |
| API do Typhoon | `typhoon_hil_api` 1.31.3, num Python 3.12.10 à parte (o da instalação do Typhoon também serve) |

A parte em Python não tem outras dependências: não usa SciPy nem integrador de biblioteca. O script também rodou
com Python 3.14.6, NumPy 2.5.3 e Matplotlib 3.11.2, e os resultados coincidiram com diferença ≤ 10⁻¹⁰ relativo,
exceto em grandezas que são zero numérico. A única grandeza que muda de máquina para máquina é o tempo de CPU
(`R4_numerico.cpu_por_s_simulado`).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `parametros.py` | todos os parâmetros, com a fonte de cada um ao lado; níveis da sensibilidade; ensaios do TyphoonSim |
| `modelo.py` | RK4 de passo fixo, função energia, linearização, critério das áreas, período por energia, métricas medidas nas curvas |
| `caracterizacao.py` | executa R2–R5, gera as figuras 1–7 e 9–12, `resultados.json` e `dados/*.csv` |
| `compara_typhoon.py` | lê `typhoonsim/dados/*.csv`, confere contra o esquema discreto e contra o RK4, gera a figura 8 e `resultados_typhoon.json` |
| `estilo.py` | estilo comum das figuras (cores, vírgula decimal, rótulo do solver) |
| `resultados.json` | todos os números do Python citados no relatório |
| `resultados_typhoon.json` | os números do TyphoonSim citados no relatório (R3.5 e Tabela 6) |
| `dados/ensaio_a_degrau.csv` | ensaio (a), 0–30 s a cada 10 ms: `t_s, delta_rad, delta_omega_rad_s, Pe_pu` |
| `dados/ensaio_b_condicao_inicial.csv` | ensaio (b), mesmo formato |
| `dados/ensaio_c_falta.csv` | ensaio (c), 0–2 s a cada 1 ms; três colunas (δ, Δω, Pe) por duração de falta (200, 270 e 290 ms) |
| `typhoonsim/swing_equation.tse` | **o modelo do TyphoonSim** (configurado para o ensaio a) |
| `typhoonsim/monta_modelo.py` | monta o `.tse` pela API, só com blocos nativos, e compila |
| `typhoonsim/roda_typhoon.py` | roda os 7 ensaios pela API e exporta as sondas |
| `typhoonsim/dados/*.csv` | saída do TyphoonSim, 1 ms: `Time, delta_graus, delta_rad, delta_omega, Pe_pu, Pm_pu, Pmax_pu` |

## Parâmetros utilizados (`parametros.py`)

| Parâmetro | Valor | Unidade | Fonte |
|---|---|---|---|
| f, ωs = 2πf | 60; 376,99 | Hz; rad/s | rede brasileira |
| H | 5,0 | s | Kundur (1994), Tab. 3.2 |
| E' | 1,20 | pu | máquina sobre-excitada (coerência conferida em `modelo.ponto_de_operacao`) |
| V | 1,00 | pu | barramento infinito |
| X = X'd + Xe | 0,60 | pu | X'd 0,15–0,40 pu, Kundur (1994), Tab. 4.2 |
| Pmax = E'V/X | 2,00 | pu | derivado |
| D | 0,01 | pu/(rad/s) | escolha da equipe (ζ = 2,3 %) |
| Pm0 | 0,80 | pu | ponto de operação |
| h | 1 | ms | passo do RK4 e taxa dos blocos do TyphoonSim |

Ensaios: degrau ΔPm = 0,10 pu; δ(0) = 60°; falta (Pe = 0) a partir de t = 0,10 s com duração de 200, 270 e 290 ms.
No TyphoonSim, o degrau ocorre em t = 1 s (equilíbrio antes dele), seguido de 60 s; o ensaio (b) dura 30 s; as faltas
também incluem 287 e 288 ms, que cercam o tempo crítico.
Sensibilidade: H ∈ {1; 2,5; 5; 10; 25} s; D ∈ {−0,005; 0; 0,01; 0,1; 0,441; 1,0}; X ∈ {0,30; 0,45; 0,60; 0,90; 1,20; 1,40} pu;
ΔPm ∈ {0,01; 0,10; 0,30; 0,60} pu; δ(0) ∈ {150°, 160°}.

## Como reproduzir

### 1. Python (referência)

```
pip install numpy matplotlib
cd simulacao
python caracterizacao.py
```

O script leva cerca de 50 s e imprime um resumo dos números principais. Ele grava:

- `../relatorio/figuras/fig-01-*.png` … `fig-07-*.png` e `fig-09-*.png` … `fig-12-*.png` (sobrescreve as do relatório);
- `resultados.json` e `dados/*.csv`.

### 2. TyphoonSim

Abra o TyphoonSim **e o Schematic Editor** (na tela inicial do TyphoonSim). Sem o Schematic Editor aberto, a
simulação pela API termina sem dados. Use o Python que tem a `typhoon_hil_api`:

```powershell
cd simulacao\typhoonsim
$PY = "<python com typhoon_hil_api>"
& $PY monta_modelo.py        # (opcional) regera swing_equation.tse a partir de parametros.py e compila
& $PY roda_typhoon.py        # 7 ensaios, ~15–25 s cada -> dados\<ensaio>.csv
cd ..
python compara_typhoon.py    # Python comum: figura 8 e resultados_typhoon.json (~5 s)
```

`roda_typhoon.py ensaio_a_degrau` roda um ensaio só. A compilação cria `swing_equation Target files/`, que os
scripts apagam ao terminar: não faz parte da entrega.

**Pela interface:** Schematic Editor → File → Open → `swing_equation.tse` → Compile → Start Simulation (61 s).
O `Scope_swing` mostra `delta_graus`, `delta_omega`, `Pe_pu` e `Pm_pu`.

**Modelo no TyphoonSim** (diagrama da Figura 1b, só blocos nativos):

| Bloco | Tipo | Função |
|---|---|---|
| `Pm0`, `degrau_dPm`, `Pm` | Constant, Step, Sum | Pm(t) = 0,80 + 0,10 pu a partir de t = 1 s |
| `Pmax`, `um`, `falta_inicio`, `falta_fim`, `rede_1_menos_falta`, `Pmax_t` | Constant, Step, Sum, Product | Pmax(t) = 2·(1 − falta), com falta = 1 entre t_f e t_f + t_c |
| `sen_delta`, `Pe` | Trigonometric function, Product | Pe = Pmax(t)·sen δ |
| `D_vezes_dw`, `Pa`, `ws_sobre_2H` | Gain, Sum, Gain | Pa = Pm − Pe − D·Δω, multiplicado por ωs/2H |
| `integ_dw` | Integrator | Δω |
| `vezes_h`, `dw_proximo`, `integ_delta` | Gain, Sum, Integrator | δ, integrado a partir de Δω[k+1] = Δω + h·(ωs/2H)·Pa |

O Integrator nativo é um Euler progressivo (saída = estado anterior). Por isso o integrador de δ recebe Δω já
atualizado: o par vira um Euler simplético, que não cria nem destrói energia de oscilação. Ligado direto, seria um
Euler explícito, com cerca de −0,035 1/s de amortecimento artificial (ver R3.5 do relatório).

### Modo de teste (não altera a entrega)

Para rodar sem alterar nenhum arquivo da entrega, desvie toda a saída (figuras, `resultados*.json` e `dados/`) para
outra pasta. No bash: `G08_TESTE=C:/caminho/teste python caracterizacao.py`. No PowerShell:
`$env:G08_TESTE="C:\caminho\teste"; python caracterizacao.py`. O mesmo vale para `compara_typhoon.py`. Os scripts
não criam `__pycache__`.

Para outro cenário, altere `parametros.py` e rode de novo. Todas as figuras e números são recalculados.

## Como cada figura é gerada

As simulações em Python usam `modelo.simula` (RK4, h = 1 ms). Cada trecho de parâmetros constantes usa n = ⌈T/h⌉
passos iguais, de modo que os chaveamentos (início e fim da falta) caem exatamente na grade.

| Figura | Script / função | O que é simulado / calculado |
|---|---|---|
| fig-01-diagrama-blocos | `caracterizacao.py` / `fig01` | desenho do sistema e do diagrama de blocos (sem simulação) |
| fig-02-potencia-angulo | `fig02` | curva Pe(δ), equilíbrios δs e δu, energia potencial V(δ) e energia crítica (álgebra) |
| fig-03-polos-frequencia | `fig03` | autovalores da linearização em função de Pm0 e \|G(jω)\| (álgebra) |
| fig-04-degrau | `fig04` | **ensaio (a)**: degrau Pm 0,80 → 0,90 pu em t = 0, a partir de δ0; 120 s simulados; forma fechada linear sobreposta |
| fig-05-condicao-inicial | `fig05` | **ensaio (b)**: δ(0) = 60°, Δω(0) = 0, Pm = 0,80 pu; 60 s; repetido com D = 0 para a referência por energia; plano de fase com a separatriz |
| fig-06-falta | `fig06` | **ensaio (c)**: Pe = 0 de t = 0,10 s até 0,10 + {0,20; 0,27; 0,29} s, depois 2,5 s com a rede pré-falta; critério das áreas |
| fig-07-validacao-numerica | `fig07` | balanço de energia W(t) − W(0) + Ed(t) no ensaio (b) com h = 1 e 10 ms; erro de δ(10 s) para h de 0,5 a 40 ms, contra h = 0,1 ms |
| fig-08-typhoon | `compara_typhoon.py` | **TyphoonSim × RK4** nos ensaios (a), (b) e (c) (faltas de 200, 270, 287, 288 e 290 ms); diferenças contra o RK4 e contra o esquema discreto dos blocos |
| fig-09-sens-inercia | `caracterizacao.py` / `fig09` | degrau de 0,10 pu para cada nível de H; métricas normalizadas (álgebra × simulação) |
| fig-10-sens-amortecimento | `fig10` | idem para D (os níveis D ≤ 0 rodam 80 s) |
| fig-11-sens-reatancia | `fig11` | idem para X (Pmax = E'V/X) |
| fig-12-sens-amplitude-ci | `fig12` | degraus de 0,01 a 0,60 pu; degrau crítico (bisseção, ±0,005 pu); δ(0) = 150° e 160° |

Grandezas obtidas por bisseção sobre simulações (tolerância de 10⁻⁶): tempo crítico de eliminação da falta (`tcr_simulado`) e degrau
crítico (`degrau_critico_simulado`). A perda de sincronismo é declarada quando δ passa de 180°.

## Onde estão os números do relatório

`resultados.json`: `R2` (equilíbrios, linearização em δ0 e δ1, critério das áreas, energia crítica), `R3a`, `R3b`,
`R3c` (ensaios), `R4_numerico` (convergência, estabilidade do passo, custo de CPU), `R5` (cada nível de H, D, X e
amplitude, degrau crítico, condição inicial, elasticidades).
`resultados_typhoon.json`: métricas do TyphoonSim nos ensaios (a), (b) e (c), intervalo do tempo crítico, diferença
contra o esquema discreto e contra o RK4, e o σ das ligações alternativas dos integradores (`variantes`).
