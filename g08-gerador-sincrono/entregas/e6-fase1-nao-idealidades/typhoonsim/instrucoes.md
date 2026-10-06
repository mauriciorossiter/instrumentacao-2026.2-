# TyphoonSim — Fase 1, Entrega 02 (não idealidades)

Mesma cadeia e mesmo circuito da Entrega 01: Bourns 3590S → buffer OPA333 → XTR115 (4–20 mA) →
laço de 24 V → receptor de 250 Ω. As camadas da Entrega 02 entram **antes** do buffer, sobre o
potenciômetro.

> ⚠️ Os arquivos `modelo.tse` e `modelo_r8_sem_buffer.tse` **ainda não existem**. Eles são gerados
> por script na máquina com o TyphoonSim (passo 1). O que vai dentro deles já foi conferido fora do
> Typhoon (`reprodutibilidade/confere_c.py`): os blocos nativos emulados e o C compilado com gcc
> batem com o gabarito Python em todos os casos.

## Arquivos desta pasta

| Arquivo | Papel |
|---|---|
| **`modelo.tse`** | **o modelo da entrega**: E01 intacta em C function + E02 em blocos nativos |
| `modelo_r8_sem_buffer.tse` | anexo do R8: contrafactual sem buffer (resistores variáveis) |
| `alternativa_c_function/modelo_c_function.tse` | o mesmo modelo com as camadas da E02 em C (ruído com semente; conferência ponto a ponto). Ver o LEIA-ME da pasta |

Os três compilam no Typhoon 2026.3 desta máquina (05/10).

## Os dois modelos

### `modelo.tse`: a entrega

Regra de construção: **o que veio da E01 fica exatamente como era, em C function; tudo o que é da
E02 é bloco nativo.**

| Parte | Onde fica | Blocos |
|---|---|---|
| varredura, potenciômetro (`x = θ/3600`, `v = x·V(VREF)`), receptor | **C function, código da E01 sem alteração** | `referencia`, `potenciometro`, `receptor` |
| R6 folga (backlash 1,0°) | blocos nativos | `folga_b` (Constant), `folga_theta_mais_b` (Sum), `folga_min` / `folga_max` (Min Max), `folga_memoria` (Unit Delay) |
| R6 resolução (0,020 %) | blocos nativos | `res_espiras_por_grau` (Gain), `res_soma_a` (Sum), `res_espira` (Round, floor), `res_soma_fase` (Sum), `res_graus_por_espira` (Gain); chave `res_liga` / `res_desvio` / `res_chave` / `res_saida` |
| R8 ruído de contato 1/f (ENR 100 Ω) | blocos nativos | `ruido_branco` (Random Source, N(0,1)) → `kellet_polo0…5` (Discrete Transfer Function) + `kellet_atraso` + `kellet_direto` → `kellet_soma` (Sum, 8 entradas) → `ruido_K_ENR` (Gain) |
| "cursor em movimento" | blocos nativos | `mov_memoria` (Unit Delay), `mov_desvio` (Sum +−), `mov_abs` (Abs), `mov_cursor_movendo` (Sign) |
| injeção do ruído | blocos nativos | `ruido_x_movimento`, `ruido_chave` (Product), `ruido_x_I_cursor` (Gain, 200 pA), `v_cursor_mais_ruido` (Sum) → buffer |
| R7 ordem zero | — | é o próprio potenciômetro da E01 (`y = K·x`) |
| circuito elétrico | idêntico à E01 | buffer, R0, R_IN, XTR115, laço, R_L |

**Liga/desliga sem mudar a topologia.** As constantes `folga_b` (1° ou 0), `res_liga` (1 ou 0) e
`ruido_liga` (1 ou 0) são ajustadas por `roda_typhoon.py` a cada caso.

**Ruído sem semente.** O Random Source nativo não tem semente, então o ruído do TyphoonSim é outra
realização, com a mesma estatística do gabarito. A análise compara:
- a parte determinística, ponto a ponto, contra o caso equivalente sem ruído;
- o ruído, pela estatística: valor eficaz, pico e inclinação 1/f;
- o filtro 1/f nativo, aplicando o filtro do Python ao branco sorteado (sonda `ruido_branco_N01`).
  Esta comparação sai exata.

**Sondas novas:** `theta_cursor`, `theta_resolucao`, `dRc_ohm`, `ruido_branco_N01`.

### `modelo_r8_sem_buffer.tse`: contrafactual do R8

O potenciômetro vira circuito, com três **Variable Resistors**: `R_trilha_sup`, `R_trilha_inf` e
`R_contato`. O cursor vai **direto** a `R_IN`, sem buffer. As resistências também são calculadas com
blocos nativos:
- `R_inf = min(max(Rp·x, 10 Ω), Rp)`;
- `R_sup = max(Rp − Rp·x, 10 Ω)`;
- `R_c = 110 Ω + ΔRc`.

O efeito de carga (~8,4 % FE) e o ruído (~0,55 % FE) saem do circuito. Hipóteses: contato de base de
110 Ω, para o resistor nunca zerar; pontas de 10 Ω, a resistência mínima absoluta do datasheet.

**Plano B:** se algum bloco nativo falhar, `monta_modelo.py` monta tudo com as camadas em C
(versão conferida bit a bit) e avisa.

## Como executar

**Nesta máquina (Linux, Typhoon 2026.3 em `/opt/typhoon`).** A API exige Python 3.10–3.13, e o
sistema tem o 3.14. Use um ambiente com Python 3.12 e instale o pacote que vem com o Typhoon:
`/opt/typhoon/typhoon_hil_control_center_2026.3/api_install/typhoon_hil_api-1.32.1-py3-none-any.whl`,
mais numpy, scipy, matplotlib, pandas e python-pptx. Exporte
`TYPHOONPATH=/opt/typhoon/typhoon_hil_control_center_2026.3`.
- A **compilação** funciona com a licença importada (testado em 05/10).
- O **início da simulação** pela API foi recusado ("appropriate license is not available"). Teste
  pela interface (Schematic Editor → Start Simulation).

**Na máquina do Leonardo (Windows):** use o Python da API
`C:\Users\Leonardo\Downloads\10.grupo\10.grupo\3.typhoonsim\.venv\Scripts\python.exe`
(`typhoon_hil_api` 1.31.3).

**Abra o TyphoonSim e o Schematic Editor antes.** Sem o Schematic Editor aberto, a simulação pela
API trava em "Simulation ready!" (aconteceu em 22/08 e em 24/09).

```powershell
cd reprodutibilidade
$PY = "C:\Users\Leonardo\Downloads\10.grupo\10.grupo\3.typhoonsim\.venv\Scripts\python.exe"
& $PY monta_modelo.py        # 1. gera modelo.tse (E01 em C + E02 nativo) e modelo_r8_sem_buffer.tse
& $PY roda_typhoon.py        # 2. 4 casos + 2 do contrafactual -> ..\typhoonsim\dados\varredura_<caso>.csv
python analisa_typhoon.py    # 3. métricas, figuras 12 e 14, ..\Fase1_Latex\valores_typhoon.tex
python gera_slides.py        # 4. regera a apresentação com os números do TyphoonSim
```

Depois, recompile os dois relatórios em `Fase1_Latex/` (pdfLaTeX, 2 vezes cada) e copie os PDFs
para `relatorio/`. As células "[pend.]" e as figuras do TyphoonSim entram sozinhas.

### Se algo der errado

| Sintoma | O que fazer |
|---|---|
| `monta_modelo.py` imprime "modo nativo falhou … montando o plano B" | A entrega continua válida: o `modelo.tse` sai com as camadas da E02 em C (versão conferida bit a bit). Para recuperar a versão nativa, rode `& $PY inspeciona_blocos.py > inspecao.txt` e mande o arquivo. Ele lista os nomes reais das propriedades e dos terminais (a documentação pública só mostra os rótulos da interface). |
| "contrafactual R8 … falhou" | O resto da entrega não depende dele. Mande o `inspecao.txt` (o bloco `core/Variable Resistor`). |
| "appropriate license is not available" ao iniciar a simulação | Já tem outra simulação rodando, ou a licença do TyphoonSim não está liberada para simular pela API. Teste pela interface (Start Simulation). |
| "license is not available" | Já tem outra simulação rodando: só uma por vez. |

`roda_typhoon.py completa r8_sem_buffer` roda só esses casos.

### Pela interface (alternativa)

1. Schematic Editor → File → Open → `modelo.tse`.
2. Compile e clique em **Start Simulation** (20 s).
3. No `Scope_cadeia`, confira:
   - `theta_cursor` em escada e deslocado +1° na descida;
   - `theta_med` sobre `theta_ref`;
   - `I_LOOP_mA` de ~4 a ~20 mA.
4. **Captura de tela** (esquemático com os blocos da folga e da resolução + Scope rodando), salva como
   `captura-scada.png` nesta pasta e em `Fase1_Latex/figs/`.

## O que esperar (gabarito Python, grade de 1 ms)

| Grandeza | Python | Tolerância |
|---|---|---|
| ruído (Random Source): eficaz / inclinação | ~27 Ω / ~−1,0 (outra realização) | estatística |
| filtro 1/f nativo × Python (mesmo branco) | ~1e−13 Ω | exato |
| atraso numérico | 2 amostras (2 ms), como na E01 | compensado na análise |
| erro de linearidade terminal (subida) | 0,0100 % FE | < 1 % FE |
| erro total (completa) | 0,155 % FE (ideal: 0,120) | < 1 % FE |
| histerese subida × descida | 1,44° | — |
| zona morta na reversão | 1,44° (amostrada a cada 0,36°) | — |
| \|TyphoonSim − Python\| | ~nA (resíduo do solver; na E01, 0,0015 µA) | — |
| contrafactual: linearidade / pico do ruído | 8,37 % / 0,55 % FE | (não atende, de propósito) |

`analisa_typhoon.py` também confere:
- **`theta_cursor`** contra o gabarito, ponto a ponto. Diferença de 0,72° ou mais indica problema
  nos blocos da folga ou da resolução.
- **`dRc_ohm`** contra o filtro 1/f do Python, aplicado ao `ruido_branco_N01` que o próprio Random
  Source sorteou. Tem que dar ~1e−13 Ω. A comparação com o ruído do gabarito é só estatística
  (eficaz, pico, inclinação), porque o Random Source não tem semente.
- A diferença "Typhoon × Python" de `I_LOOP` nos casos com ruído é medida contra o caso **sem**
  ruído. No contrafactual R8, use a rodada `r8_sem_buffer_sem_ruido` para a parte determinística.

## Atraso numérico

É o mesmo da E01: cada passagem sinal → circuito → sinal soma uma amostra de 1 ms. A 360 °/s,
2 ms equivalem a **0,72°, exatamente um degrau de resolução**, por isso o realinhamento é
obrigatório. As sondas de sinal (`theta_cursor`, `theta_resolucao`, `dRc_ohm`, `ruido_branco_N01`) não têm atraso, e a análise só desloca
as que passam pelo circuito.
