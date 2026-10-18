# TyphoonSim — Fase 1, Entrega 03 (validação funcional, vídeo)

A cadeia é a mesma das Entregas 01 e 02, sem alteração: Bourns 3590S → buffer OPA333 → XTR115
(4–20 mA) → laço de 24 V → receptor de 250 Ω, com as camadas da E02 sobre o potenciômetro.

Esta entrega acrescenta dois elementos:
- um **gerador de ensaios**, em blocos nativos, para os três ensaios-padrão do R11;
- as **entradas do painel SCADA**, que permitem disparar os ensaios e ligar ou desligar cada
  camada ao vivo.

> ⚠️ O `modelo_e03.tse` é **gerado por script** na máquina com o TyphoonSim (passo 1). A fiação
> já foi conferida fora do Typhoon. O script foi rodado com uma API simulada e o grafo de blocos
> resultante foi executado amostra a amostra. Ele bate com o gabarito Python (`ensaios.py`) em
> 5×10⁻¹³, nos 4 ensaios e com 4 combinações de camadas.

## O que mudou em relação ao modelo da E02

| Parte | Como ficou |
|---|---|
| C functions da E01 (`referencia`, `potenciometro`, `receptor`) e o circuito | **iguais à E01**. A varredura da E01 passou a ser o ensaio 0 do seletor. |
| Camadas da E02 (folga, resolução, ruído 1/f) | **mesmos blocos nativos**. Os três liga/desliga viraram SCADA Inputs: `folga_liga` alimenta o Gain `folga_b` (1,0° × folga_liga); `res_liga` e `ruido_liga` mantêm os mesmos nomes. |
| **Gerador de ensaios** (novo, blocos `ens_*`) | θ_ref = e₀·varredura + e₁·(base + A·d) + e₂·θ₀ + e₃·(base + A·p). Usa só tipos de bloco que já compilaram na E02 (Constant, Sum, Gain, Product, Unit Delay, Min Max, Abs, Sign, Clock), mais o SCADA Input. |
| **Condição inicial** (novo, blocos `ci_*`) | Na borda do disparo do ensaio (b), o estado da folga (`folga_memoria`) recebe θ_ref + δ₀ durante **uma** amostra. Fora desse instante, o bloco repassa exatamente θ_c. A referência não muda. |
| Sondas novas | `theta_ref` (a referência selecionada, que vai para a cadeia e para o receptor), `theta_ref_E01` (a varredura), `ens_disparo_sinal`, `ens_pulso_sinal` |
| Tempo de simulação | 600 s, para dar tempo de operar o painel. A varredura da E01 só acontece nos primeiros 20 s. |

## Entradas SCADA (o painel do item 3 liga um widget a cada uma)

| SCADA Input | Inicial | Faixa | Widget sugerido | Para quê |
|---|---|---|---|---|
| `ens_ensaio` | 1 | 0–3 | Combo box (0 varredura E01, 1 degrau, 2 cond. inicial, 3 pulso) | escolhe o ensaio |
| `ens_disparo` | 0 | 0/1 | **Chave (toggle)** | 0 → 1 dispara; no degrau, 1 → 0 volta ao repouso |
| `ens_amplitude` | 1800 | ±3600 | campo numérico [graus] | amplitude do degrau e do pulso (1800° = 12 mA) |
| `ens_theta_base` | 0 | 0–3600 | campo numérico [graus] | repouso dos ensaios (a) e (c) |
| `ens_theta0` | 1800 | 0–3600 | campo numérico [graus] | referência fixa do ensaio (b) |
| `ens_delta0` | 5 | ±20 | campo numérico [graus] | deslocamento do cursor imposto como condição inicial |
| `ens_largura_s` | 0,5 | 0,001–10 | campo numérico [s] | duração do pulso |
| `ens_t_auto` | 1e9 | — | **não precisa de widget** | disparo automático, usado só na rodada offline |
| `folga_liga` | 1 | 0/1 | checkbox | R6 folga de 1,0° |
| `res_liga` | 1 | 0/1 | checkbox | R6 resolução de 0,72° |
| `ruido_liga` | 1 | 0/1 | checkbox | R8 ruído de contato 1/f |

**Gráfico do R12:** um Trace Graph com as sondas `theta_ref` e `theta_med` sobrepostas.
**Mostradores:** `I_LOOP_mA` com 4 casas decimais (o efeito da folga é de 3,2 µA), `theta_med` e
`theta_cursor`.

## Como gerar o modelo

Use o mesmo ambiente da E02: Python da API, `TYPHOONPATH` exportado e TyphoonSim **com o
Schematic Editor aberto**. A pasta `../../e6-fase1-nao-idealidades/reprodutibilidade/` precisa
estar no lugar, porque os scripts importam dela os parâmetros e o código C da E01/E02.

```powershell
cd reprodutibilidade
$PY = "C:\Users\Leonardo\Downloads\10.grupo\10.grupo\3.typhoonsim\.venv\Scripts\python.exe"
& $PY monta_modelo_e03.py      # 1. gera e compila ..\typhoonsim\modelo_e03.tse; lista os SCADA Inputs
& $PY roda_ensaios.py          # 2. (conferência) 3 ensaios offline -> ..\typhoonsim\dados\ensaio_<a|b|c>_<caso>.csv
python compara_ensaios.py      # 3. TyphoonSim x gabarito -> ..\gabarito\comparacao_typhoon.json, fig-17
```

O `roda_ensaios.py` sempre termina devolvendo o `.tse` aos valores do painel (disparo manual e
600 s).

### Se algo der errado

| Sintoma | O que fazer |
|---|---|
| `(aviso) SCADA Input …: propriedade min/max/signal_type não aplicada` | Não impede nada: só o `def_value` é obrigatório. Ajuste a faixa no widget do painel. |
| Erro em `def_value` ou em `core/SCADA Input` | Rode `& $PY inspeciona_blocos_e03.py > inspecao_e03.txt` e mande o arquivo. Ele mostra os nomes reais das propriedades nesta versão. |
| "modo nativo falhou … plano B" | O modelo sai com as camadas na C function da E02 e o gerador nativo. Nesse modo as camadas ficam fixas e o ensaio (b) não tem a injeção. Mande o `inspecao_e03.txt`. |
| A simulação trava em "Simulation ready!" | Abra o Schematic Editor antes (mesmo problema da E01/E02). |
| "appropriate license is not available" | Teste pela interface (Start Simulation). É o bloqueio de licença que apareceu na E02. |

## Como operar cada ensaio pelo SCADA (vídeo)

Antes de cada ensaio: deixe `ens_disparo` = 0 e espere o gráfico estabilizar.

| Ensaio | Ajuste | Ação ao vivo | O que deve aparecer |
|---|---|---|---|
| (a) degrau | `ens_ensaio` = 1, base 0, A = 1800 | chave 0 → 1 | `theta_med` sobe de uma vez de ≈ 0° para ≈ 1801,6° (12,007 mA), com 2 ms de atraso numérico e sem sobressinal. A folga não age, porque a calibração é na subida. |
| (b) condição inicial | `ens_ensaio` = 2 (a referência vai para 1800°: é a preparação), δ₀ = 5° | chave 0 → 1 (não muda a referência) | O cursor não fica a 5°, porque a folga só admite até 1°. Na amostra seguinte, `theta_cursor` vai para θ + 1° e **fica**. `theta_med` sobe um degrau de resolução: 1801,63° → 1802,35° (12,0072 → 12,0104 mA). Com `folga_liga` = 0, **nada acontece**: ordem zero não guarda estado. |
| (c) pulso | `ens_ensaio` = 3, base 0, A = 1800, 0,5 s | chave 0 → 1 (o pulso volta sozinho) | Sobe e desce junto com a referência. Depois do retorno, fica **+0,72° acima** do valor de antes (3,9944 → 3,9976 mA): é a histerese da folga, vista através da resolução. |

**Previsão e teste (sugestão):** antes de rodar, digam que, com `folga_liga` = 0, o resíduo depois
do pulso (c) e o salto do ensaio (b) **desaparecem**, e que com `res_liga` = 0 o resíduo passa de
0,72° para 1,00° (a folga inteira). Depois rodem e comparem.

## O que esperar (gabarito Python, grade de 1 ms, disparo em t = 1 s)

| Grandeza | (a) degrau | (b) cond. inicial | (c) pulso |
|---|---|---|---|
| θ_med final (completa) | 1801,63° | 1802,35° | −0,54° |
| θ_med final (ideal da E01) | 1801,45° | 1801,45° | −1,44° |
| I_LOOP final | 12,0072 mA | 12,0104 mA | 3,9976 mA |
| desvio da folga (R6) | 0 | 1,00° | 1,00° |
| desvio da resolução (R6) | 0,18° | 0,18° | 0,18° |
| desvio do ruído 1/f (R8) | 4,7×10⁻⁶° | 1,2×10⁻⁶° | 4,7×10⁻⁶° |
| desvio da dinâmica (R7, ordem zero) | 0 | 0 | 0 |

Os desvios de camada são medidos contra a cadeia ideal da E01, nas mesmas amostras. Os ±1,44°
entre θ_med e θ_ref vêm dos resistores comerciais da E01 (erro de 0,04 % FE), não das camadas.

**Atraso numérico:** é o mesmo da E01 e da E02. `I_LOOP` e `theta_med` saem 2 amostras (2 ms)
atrasados e começam nulos. No degrau e no pulso isso aparece como um atraso puro de 2 ms: é
efeito da amostragem do simulador, não dinâmica do sensor.
