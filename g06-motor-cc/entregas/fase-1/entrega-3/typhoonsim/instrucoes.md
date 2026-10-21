# Guia de montagem — cadeia termopar tipo K + amplificador no Typhoon HIL

**Equipe G06 · ECOM060 · Entregas 01, 02 e 03**

Este guia é para quem assistiu ao vídeo da simulação e quer **montar o mesmo circuito do zero**.
Ele está na ordem em que se monta: primeiro a cadeia ideal, depois as três camadas não ideais
e, por fim, os controles do painel SCADA usados no vídeo.
Em cada etapa, os trechos marcados com **⚠ Problema** descrevem erros que a equipe teve
durante a montagem e como evitá-los. A lista completa está na Seção 9.

> Os nomes de menus e campos podem variar na versão 2026.3. Onde isso não foi confirmado, o
> texto avisa. A lógica de cada passo vale mesmo se um nome estiver um pouco diferente.

---

## 1. O que o circuito faz

Um termopar tipo K mede a temperatura (0 a 250 °C). Seu sinal, de milivolts, passa por um
amplificador de instrumentação e uma saturação de 0 a 5 V. O vídeo mostra como cada
imperfeição real muda a saída:

| Camada | O que representa | Efeito na saída |
|---|---|---|
| Ideal | termopar linear, 40,6 µV/°C | referência (`v_ideal`) |
| Dinâmica | junção com constante de tempo τ = 0,5 s | `v_out` atrasa em relação à temperatura |
| Estática | curva real do tipo K + junta fria 10 °C deslocada | pequena curvatura e desvio de zero de −0,196 V |
| Espectral | ruído de modo comum de 573 Hz + ruído de banda larga | oscilação de ±0,10 V na saída |

Ganho total da cadeia ideal: 40,6e-6 × 494,07 ≈ **20,06 mV/°C**.
Com isso, 250 °C dá cerca de 5,0 V (a saturação começa em ~249,3 °C).

---

## 2. Antes de começar

1. Abra o **Typhoon HIL Control Center** (2026.3), depois o **Schematic Editor**.
2. Crie um modelo novo (File ▸ New) e salve como `termopar_g06.tse`.
3. Configure o dispositivo como **Virtual HIL** (não precisa de hardware).
4. Defina o **passo de simulação em 20 µs** (o campo fica nas configurações do modelo).
   Para a cadeia ideal da Entrega 01 bastava 1 ms, mas o ruído de 573 Hz exige 20 µs ou menos.
5. Deixe o **Execution rate** de todos os blocos em `inherit`.

**Dica:** use a barra de busca de blocos. Se não achar um bloco pelo nome, procure por
partes do nome (`Sat`, `Limit`, `Min`, `Max`).

---

## 3. Etapa 1 — Cadeia ideal (Entrega 01)

### 3.1 Blocos

| Bloco | Nome | Parâmetro |
|---|---|---|
| Ramp | `T_sweep` | Slope **25** (°C/s), Start time **1**, Initial output **0** |
| Gain | `Gain_TC` | **40.6e-6** (sensibilidade) |
| Gain | `Gain_stage1` | **494.07** (1 + 2·R2/R1) |
| Gain | `Gain_stage2` | **1** (R4/R3) |
| Min Max (modo MIN) | `Min Sat` | constante **5** na segunda entrada |
| Min Max (modo MAX) | `Max Sat` | constante **0** na segunda entrada |
| Probes | `T`, `v_in`, `v_out` | ver ligações |

Ligação:

```
T_sweep ─┬─► Gain_TC ─┬─► Gain_stage1 ─► Gain_stage2 ─► Min Sat ─► Max Sat ─► Probe v_out
         │            └─► Probe v_in
         └─► Probe T
```

### ⚠ Problema 1 — não existe o bloco "Saturation"

Na biblioteca do Typhoon da equipe não aparece um bloco Saturation com parâmetros
Upper/Lower. O que existe:

- **Rate Limiter** (biblioteca core): **não serve.** Ele limita a *taxa de variação*
  (unidades por segundo), não o valor. Com 5 e 0, a saída só poderia subir a 5 V/s e nunca desceria.
- **Min Max**: é a solução. Dois blocos em série impõem a saturação.

**Como montar a saturação 0–5 V:**

```
sinal ─► MIN (· , 5) ─► MAX (· , 0) ─► saída
```

### ⚠ Problema 2 — constantes do Min/Max trocadas

O primeiro bloco da equipe estava com MIN e constante 0, e o segundo com MAX e constante 5.
O resultado: MIN(sinal, 0) zera tudo que é positivo, e MAX(0, 5) devolve 5. A saída ficaria
**travada em 5 V**, sem rampa.

**Regra:** o bloco no modo **MIN** recebe o **teto** (5). O bloco no modo **MAX** recebe o
**piso** (0). Confira o modo de cada bloco nas propriedades.

### ⚠ Problema 3 — onde ligar o probe `T`

O probe `T` liga na **saída** do `T_sweep`, ao mesmo tempo que o fio segue para o `Gain_TC`.
O Ramp é uma fonte: ele não tem entrada. Para dividir o fio, puxe um segundo fio direto da
saída do bloco (uma saída pode alimentar várias entradas).

### ⚠ Problema 4 — o slope da rampa

O slope é **25** (°C/s), não 250. Com início em t = 1 s, a rampa chega a 250 °C em
250 / 25 = 10 s, ou seja, em t = 11 s. Com 250, a temperatura chegaria a 250 °C em 1 s e o
resultado seria quase um degrau.

---

## 4. Etapa 2 — Camada dinâmica (filtro de 1ª ordem)

Insira o bloco **Transfer Function** (`TF_tau`) depois da saturação de temperatura.

### 4.1 Saturação da temperatura (`Sat_T`)

Monte outro par Min Max, com teto **250** e piso **0**:

```
T_sweep ─► Min (·, 250) ─► Max (·, 0) ─► TF_tau
```

O piso de 0 é redundante (a rampa nunca fica negativa), mas segue o roteiro.

### 4.2 Parâmetros do `TF_tau`

| Campo | Valor |
|---|---|
| Numerador | `[1]` |
| Denominador | `[0.5 1]` |
| Domínio | **contínuo (s)** |

### ⚠ Problema 5 — valores infinitos em `Tj` e `v_in`

O bloco veio no modo **discreto (z)** (ícone `H(z)`). Nesse modo, `[0.5 1]` é lido como
`0,5·z + 1`, que tem polo em z = −2, fora do círculo unitário. O sistema **diverge** e os
sinais viram infinito (o `v_in` fica infinito por consequência).

**Solução:** trocar o domínio para **contínuo (s)**.

Se o bloco não tiver essa opção, use os coeficientes discretos equivalentes (para Ts = 20 µs):

- numerador `[3.99992e-5]`
- denominador `[1 -0.99996000080]`

Esses valores vêm de a = exp(−Ts/τ) = exp(−4e-5). Se mudar o passo, recalcule.
O bloco continua com ícone H(z) mesmo no modo contínuo; confira o domínio nas propriedades.

**Teste:** na rampa, `Tj` deve ficar cerca de **12,5 °C** atrás de `T` (25 °C/s × 0,5 s).

---

## 5. Etapa 3 — Camada estática (C Function)

O bloco **C Function** calcula a f.e.m. real do tipo K (equação NIST ITS-90) e subtrai a
f.e.m. da junta fria deslocada. Isso gera, de uma vez, a não linearidade e o desvio de zero.

### 5.1 Cadastro das portas

| Tipo | Nome | Observação |
|---|---|---|
| Input 1 | `Tj` | °C, vindo do filtro de 1ª ordem |
| Input 2 | `dT_cj` | °C, deriva da junta fria (na Etapa 5 vem de um SCADA Input) |
| Output | `v_s` | f.e.m. em **volts** |

> Na Entrega 02, `dT_cj` pode ser **parâmetro** do bloco (valor `10.0`). No modelo final
> do vídeo ele é **entrada**, para poder ser alterado ao vivo no SCADA.

### 5.2 Código (aba **Output function**)

Cole só este trecho. Não declare `Tj`, `v_s` nem `dT_cj` no código. Não inclua o
bloco de comentário.

```c
const double c[10] = {
    -0.176004136860e-01,  0.389212049750e-01,  0.185587700320e-04,
    -0.994575928740e-07,  0.318409457190e-09, -0.560728448890e-12,
     0.560750590590e-15, -0.320207200030e-18,  0.971511471520e-22,
    -0.121047212750e-25 };
const double a0 =  0.118597600000e+00;
const double a1 = -0.118343200000e-03;
const double a2 =  0.126968600000e+03;

double t_in[2];
double E_mV[2];
int k, i;

t_in[0] = Tj;        /* juncao de medicao */
t_in[1] = dT_cj;     /* deriva da junta fria */

for (k = 0; k < 2; k++) {
    double t = t_in[k];
    if (t < 0.0) t = 0.0;              /* polinomio valido de 0 a 1372 C */
    double p = c[9];
    for (i = 8; i >= 0; i--) p = p * t + c[i];          /* Horner */
    E_mV[k] = p + a0 * exp(a1 * (t - a2) * (t - a2));
}

v_s = (E_mV[0] - E_mV[1]) * 1.0e-3;   /* nao linearidade + desvio de zero, V */
```

**O que é isso:** `c[]`, `a0`, `a1`, `a2` são constantes tabeladas do NIST (tipo K, 0 a 1372 °C).
O bloco **não as calcula**; a cada passo ele apenas avalia E(t) com elas.
E(10 °C) = 0,3969 mV, e 0,3969 mV × 494,07 = 0,196 V. Esse é o desvio de zero.

### ⚠ Problema 6 — erro de compilação: `'dT_cj' undeclared`

A compilação do Virtual HIL falhou com:

```
sp/usr_sp_function_dev0_0.c: error: 'dT_cj' undeclared (first use in this function)
```

**Causa:** o `dT_cj` não foi cadastrado como parâmetro (ou entrada) do bloco, então o código
gerado não o conhece. `Tj` e `v_s` estavam cadastrados, e só ele faltava.

**Soluções:**

1. Cadastre `dT_cj` com o nome **exatamente igual** ao do código (mesma capitalização),
   na lista correta: parâmetro (Entrega 02) ou segunda entrada (Entrega 03).
2. Alternativa rápida, só para a Entrega 02: declare no código, antes de `t_in[0] = Tj;`,
   a linha `const double dT_cj = 10.0;`. **Nesse caso não cadastre `dT_cj` em nenhuma lista**,
   senão dá erro de redeclaração. Para o ramo da não linearidade, use `0.0`.

### ⚠ Problema 7 — outros erros comuns na C Function

| Erro | Causa | Solução |
|---|---|---|
| `c`, `a0`, `a1`, `a2` undeclared | coeficientes não declarados | copiar o bloco completo da Seção 5.2 |
| `exp` indefinido | falta `math.h` | adicionar `#include <math.h>` na área de includes (ou na 1ª linha) |
| redeclaração de `dT_cj`, `Tj` ou `v_s` | declarados no código **e** na janela do bloco | declarar em um só lugar |
| erro com `double p` após `if` | compilador exige declarações no topo | mover `double p;` para junto de `double t;` |
| `Tj` fica em 0 ou `v_s` em 0 | porta de entrada não ligada ao `TF_tau`, ou nomes diferentes | conferir ligação e nomes |

A aba **Variables** serve apenas para estados que persistem entre passos. Esse bloco é
combinacional e não precisa dela.

---

## 6. Etapa 4 — Camada espectral (ruído)

### 6.1 Blocos

| Bloco | Nome | Parâmetro |
|---|---|---|
| Sine | `n_comm` | Amplitude **2e-3**, Frequency **573**, Phase 0, Offset 0 |
| Random Source | `n_bl` | distribuição normal, média **0**, desvio **1** |
| Gain | `Gain_bl` | **0.2e-3** |
| Sum (`++`) | `Sum_ncm` | `n_comm` + `Gain_bl` (ruído de modo comum n_cm) |
| Gain | `Gain_dm` | **0.1** (10 % do modo comum vira ruído diferencial) |
| Sum (`++`) | `Sum_in` | `v_s` + `Gain_dm` |
| Gain | `Gain_cm` | **494.07e-6** (vazamento pelo CMRR de 120 dB) |
| Sum (`++`) | `Sum_out` | `Gain_stage2` + `Gain_cm` |

### 6.2 Ligações

```
n_comm ─► Sum_ncm (entrada 1)
n_bl ─► Gain_bl ─► Sum_ncm (entrada 2)
Sum_ncm ─┬─► Gain_dm ─► Sum_in (entrada 2)
         └─► Gain_cm ─► Sum_out (entrada 2)

CF_estatica (v_s) ─► Sum_in (entrada 1) ─┬─► Probe v_in
                                         └─► Gain_stage1 ─► Gain_stage2 ─► Sum_out (entrada 1)
Sum_out ─► Min (·, 5) ─► Max (·, 0) ─► Probe v_out
```

A saída do `Random Source` vai **só** ao `Gain_bl`.
Os blocos `Gain_cm` e `Sum_out` dão ~1 µV na saída e podem ser omitidos sem mudar o gráfico.
Se omitir, ligue `Gain_stage2` direto no Min.

### ⚠ Problema 8 — probe `v_in` no lugar errado

O probe `v_in` estava ligado **depois** do `Gain_stage1`. Ele media volts (494× maior),
e não os milivolts esperados.

**Correto:** `v_in` na saída do `Sum_in`, no trecho entre `Sum_in` e `Gain_stage1`.

### ⚠ Problema 9 — frequência do `Sine` em Hz ou rad/s

Alguns blocos de senoide do Typhoon pedem a frequência em **Hz** e outros em **rad/s**.
Confira a descrição do campo. Se for rad/s, use `2*pi*573` ≈ `3600.1`.
**Teste:** o ruído deve ter período de ~1,75 ms (573 ciclos por segundo).

### ⚠ Problema 10 — ruído aleatório maior que o previsto

Nos dados capturados, a oscilação em 573 Hz estava certa (pico espectral em 573,4 Hz), mas a
parte aleatória parecia cerca de **3 vezes** maior que a prevista (σ ≈ 0,06 mV em `v_in`, contra 0,02 mV).
Confira:

- `Gain_bl = 0.2e-3` (e não 0.6e-3 ou 2e-3);
- `n_bl` com **desvio padrão 1** (alguns blocos pedem variância ou outra escala).

Se estiverem certos, pode ser só flutuação de um trecho curto.

---

## 7. Etapa 5 — Controles do SCADA (modelo do vídeo)

No vídeo, tudo é alterado **ao vivo no painel**, sem recompilar. Por isso os números fixos
da referência viram **SCADA Inputs** (bloco `SC`, biblioteca Signal Processing).
Salve uma cópia antes: `termopar_g06_video.tse`.

### 7.1 SCADA Inputs

| Nome | Valor inicial | Para que serve |
|---|---|---|
| `SI_T0` | 25 | temperatura de repouso (°C) |
| `SI_dT` | 225 | tamanho do salto (25 → 250 °C) |
| `SI_pulso` | 0 | 0 = degrau, 1 = pulso (desce de novo em t = 1,5 s) |
| `SI_Tj0` | 25 | temperatura inicial da junção (°C) |
| `SI_dTcj` | 10 | deriva da junta fria (°C), o controle da previsão |
| `SI_esp` | 1 | liga/desliga o ruído |

### 7.2 Nova referência de temperatura (substitui o `T_sweep`)

Use dois blocos **Step** (Initial 0, Final 1): `Step_A` com Step time **1** e `Step_B` com Step time **1.5**.

| Bloco | Operação |
|---|---|
| `Prod_p` (Product) | `SI_pulso` × `Step_B` |
| `Sum_s` (Sum `+ −`) | `Step_A` − `Prod_p` |
| `Prod_dT` (Product) | `SI_dT` × `Sum_s` |
| `Sum_ref` (Sum `++`) | `SI_T0` + `Prod_dT` |

Resultado: **T_ref = T0 + dT · (Step_A − pulso · Step_B)**. A saída do `Sum_ref` vai ao probe
`T` e ao par Min/Max do `Sat_T`.

### 7.3 Condição inicial da junção

O filtro de 1ª ordem começa com estado zero. Para a junção partir de `Tj0`, trabalhe em
"desvio" e some `Tj0` de volta:

```
Max Sat ─► Sum_dev (+ −) ─► TF_tau ─► Sum_back (+ +) ─┬─► Probe Tj
               ▲  (− : SI_Tj0)           ▲ (+ : SI_Tj0) └─► CF_estatica (Tj)
```

- `Sum_dev` = T_ref saturada − `SI_Tj0`.
- `Sum_back` = saída do filtro + `SI_Tj0`.

### 7.4 ΔTcj e ruído ao vivo

- `SI_dTcj` liga na segunda entrada (`dT_cj`) do `CF_estatica`. O código não muda.
- Coloque um **Product** entre `Gain_dm` e `Sum_in`, multiplicando por `SI_esp`.

### 7.5 Ramo `v_ideal`

Ramo **separado, em paralelo**, saindo da saída do `Max Sat` (a mesma que alimenta o `Sum_dev`):

```
Max Sat ─► Gain 40.6e-6 ─► Gain 494.07 ─► Gain 1 ─► Min (·, 5) ─► Max (·, 0) ─► Probe v_ideal
```

Sem dinâmica, sem não linearidade, sem desvio de zero e sem ruído. Use constantes 5 e 0 próprias
(copie o par Min/Max e as constantes). Em 25 °C ele dá 0,50 V; em 250 °C, 5,00 V.

### ⚠ Problema 11 — montagem do modelo do vídeo

| Sintoma | Causa | Solução |
|---|---|---|
| `v_out` parte de 0 V e não de ~0,30 V | `SI_Tj0` não está ligado nas duas somas | conferir `Sum_dev` e `Sum_back` |
| a saída não cai com ΔTcj = 20 | `dT_cj` ainda é parâmetro, não entrada | refazer o item 7.4 |
| resultado errado sem aviso de erro | entradas do `CF_estatica` invertidas | a 1ª deve ser `Tj` e a 2ª `dT_cj` |
| `Tj` com valores absurdos | `TF_tau` em modo discreto | Problema 5 |
| scope sem `v_ideal` | ramo ideal não montado | Seção 7.5 |
| mudar o campo não muda nada | widget ligado ao SCADA Input errado, ou simulação não reiniciada | conferir o vínculo; parar e iniciar |

Depois de montar tudo, **compile e confira**. Essa deve ser a última compilação antes de gravar.

---

## 8. Scope e painel SCADA

### 8.1 Painel

1. Carregue o modelo em Virtual HIL e abra o HIL SCADA.
2. Crie um campo numérico por SCADA Input, com rótulos claros: "Repouso (°C)", "Salto (°C)",
   "Pulso 0/1", "Tj inicial (°C)", "ΔTcj (°C)", "Ruído 0/1".
3. Crie um Scope com `v_out` e `v_ideal` no mesmo gráfico, janela de ~5 s, eixo y de 0 a 5,5 V,
   cores bem diferentes e legenda visível. Opcional: um 2º gráfico com `T` e `Tj`.
4. Salve o painel e guarde o arquivo.

### 8.2 Configuração de captura

| Campo | Valor | Motivo |
|---|---|---|
| Time interval | 5 s para os ensaios do vídeo; **15 s** (mín. 14 s) para a rampa longa da Entrega 02 | a dinâmica converge ~2,5 s depois da subida |
| Sample rate | **10 KSPS** ou mais | ruído de 573 Hz |
| Gatilho | subida de T_ref, nível ~100 °C, pré-gatilho 20 % | alinhar o degrau |
| Ensaio (b) | captura forçada (sem gatilho) | a resposta começa em t = 0 |

### ⚠ Problema 12 — sample rate baixo cria um sinal falso

Com **1 KSPS** (que servia na Entrega 01), o ruído de 573 Hz fica acima do limite de 500 Hz do
Scope e vira um sinal lento falso (alias). **Use 10 KSPS ou mais.** Para medir a senoide em detalhe,
faça uma captura curta (~0,1 s) a 50 KSPS.

### ⚠ Problema 13 — onde ajustar o tempo da simulação

O Typhoon não tem campo de "tempo final" no esquemático. A simulação roda até você parar.
Quem define a janela é a **captura do Scope** (Time interval). Como a rampa continua depois
da janela, isso não atrapalha.

### ⚠ Problema 14 — a curva não parte de 0 °C (atraso de disparo)

Nos primeiros dados da Entrega 01, a temperatura já aparecia em ~12 °C em t = 0, e na Entrega 02
a rampa aparecia em t ≈ 0,645 s em vez de 1 s. É o **atraso entre o start da simulação e o disparo
da captura** (~0,3 a 0,5 s). Todos os instantes ficam deslocados igualmente; não é erro de modelo.

- Dispare a captura logo depois de iniciar.
- Para o vídeo, use gatilho na subida de `T_ref`, que alinha o degrau.
- Para a Entrega 01, uma alternativa é Start time = 2 na rampa.

### ⚠ Problema 15 — legenda e escalas

- A **legenda cobria o trecho final** do gráfico, justamente onde aparece a saturação. Mova ou oculte a legenda.
- `T` (centenas), `v_in` (milivolts) e `v_out` (volts) têm escalas muito diferentes. Use **painéis ou eixos separados**,
  senão `v_in` fica achatado.

### ⚠ Problema 16 — o arquivo `.svc` não tem dados

O primeiro arquivo exportado (`.svc`) era só a **configuração de visualização do Scope** (cores, escala,
legenda). Não continha amostras. Os dados numéricos vêm da exportação em **CSV** da captura.

### ⚠ Problema 17 — o probe `T` e o patamar de 250 °C

O probe `T` está na saída da referência, **antes** do `Sat_T`, e por isso passa de 250 °C
(nos dados chegou a 358 °C). O `Tj`, depois da saturação, trava em 250. Se quiser ver o
patamar no `T`, ligue o probe na saída do `Max Sat`.

---

## 9. Ensaios do vídeo e valores esperados

Em cada ensaio: **parar → mudar os campos → iniciar → esperar ~5 s → comentar**.
Reiniciar zera o tempo: o degrau cai sempre em t = 1 s e a junção parte do `Tj` inicial.

| Ensaio | Repouso | Salto | Pulso | Tj inicial | ΔTcj | Gatilho |
|---|---|---|---|---|---|---|
| (a) degrau | 25 | 225 | 0 | 25 | 10 | subida de T_ref |
| (b) cond. inicial | 25 | 0 | 0 | 250 | 10 | forçado |
| (c) pulso | 25 | 225 | 1 | 25 | 10 | subida de T_ref |
| (a') previsão | 25 | 225 | 0 | 25 | 20 | subida de T_ref |

| Ensaio | O que deve aparecer |
|---|---|
| (a) | `v_ideal` salta de 0,50 para 5,00 V em t = 1 s. `v_out` parte de ~0,30 V, passa por ~3,18 V em t = 1,5 s e assenta em ~4,82 V, com faixa de ±0,10 V |
| (b) | `v_ideal` reto em 0,50 V. `v_out` parte de ~4,82 V, passa por ~1,99 V em t = 0,5 s e chega a ~0,30 V em ~2,5 s |
| (c) | `v_ideal` é um retângulo de 0,50 → 5,00 → 0,50 V entre 1 e 1,5 s. `v_out` sobe até ~3,17 V e desce devagar (~2 s) até ~0,30 V |
| (a') | mesma forma do degrau, regime em ~4,62 V e partida em ~0,10 V |

### Valores da rampa longa (Entrega 02), cadeia completa

Referência: rampa de 25 °C/s com início em t = 1 s. Valores médios, sem o ruído.

| t (s) | T (°C) | Tj (°C) | v_in (mV) | v_out (V) |
|---|---|---|---|---|
| 0 a 1 | 0 | 0 | −0,397 | 0 |
| 2 | 25 | 14,19 | 0,168 | 0,083 |
| 6 | 125 | 112,50 | 4,215 | 2,083 |
| 9 | 200 | 187,50 | 7,242 | 3,578 |
| 11 | 250 | 237,50 | 9,249 | 4,570 |
| 13,5 | 250 | 249,92 | 9,753 | 4,819 |
| 15 | 250 | 250,00 | 9,756 | 4,820 |

Verificações rápidas: `Tj` fica ~12,5 °C abaixo de `T` na rampa; `v_out / v_in` = **494,07**;
antes da rampa, `v_out` fica em 0 V (o desvio de zero só deixa a saída sair de 0 V acima de ~10 °C).

### Camadas isoladas

| Camada | Esperado |
|---|---|
| Não linearidade (`dT_cj = 0`) | ≈ **+25 mV** (0,50 % FS) em ~135 °C |
| Desvio de zero | **−0,196 V** (−3,9 % FS); saída em 0 V abaixo de ~10 °C; **4,82 V** em 250 °C |
| Dinâmica | ≈ 0,25 V abaixo do ideal na rampa; converge ~2,5 s após t = 11 s |
| Espectral | ±0,10 V em 573 Hz + σ ≈ 0,01 V |

### ⚠ Problema 18 — correção de um valor citado antes

Foi dito inicialmente que `v_in` chegaria a "cerca de 9,8 mV no final da rampa". O correto é
**9,25 mV em t = 11 s**, porque a dinâmica ainda não convergiu. Os 9,756 mV só aparecem
em t ≈ 13,5 a 15 s.

---

## 10. Lista resumida dos problemas encontrados

| # | Problema | Onde ocorre | Solução em uma linha |
|---|---|---|---|
| 1 | Não há bloco Saturation; Rate Limiter não serve | Cadeia ideal | Usar Min + Max em série |
| 2 | Constantes do Min/Max trocadas (saída presa em 5 V) | Cadeia ideal | MIN com teto 5, MAX com piso 0 |
| 3 | Dúvida sobre onde ligar o probe `T` | Cadeia ideal | Saída do Ramp, com fio dividido |
| 4 | Slope 25 ou 250 | Rampa | 25 °C/s, com início em t = 1 s |
| 5 | `Tj` e `v_in` infinitos | `TF_tau` | Trocar H(z) discreto por contínuo (s) |
| 6 | `'dT_cj' undeclared` na compilação | C Function | Cadastrar `dT_cj` como parâmetro/entrada, ou declarar no código |
| 7 | Coeficientes, `math.h`, redeclaração, `double p` | C Function | Seção 5.2 e tabela do Problema 7 |
| 8 | `v_in` medido depois do ganho | Probe | Ligar na saída do `Sum_in` |
| 9 | Frequência do `Sine` em Hz ou rad/s | Ruído | Conferir a unidade do campo |
| 10 | Ruído aleatório maior que o previsto | Ruído | Conferir `Gain_bl` e o desvio do `n_bl` |
| 11 | `v_out` em 0 V, regime errado, `v_ideal` ausente | Modelo do vídeo | Conferir `SI_Tj0` nas duas somas, `dT_cj` como entrada, ramo ideal |
| 12 | Sample rate de 1 KSPS causa alias do ruído | Scope | Usar 10 KSPS ou mais |
| 13 | Onde ajustar o tempo da simulação | Scope | Time interval da captura |
| 14 | Curva não parte de 0 °C | Scope | Atraso de disparo; gatilho em T_ref |
| 15 | Legenda cobre o fim da curva; escalas muito diferentes | Scope | Mover a legenda e usar painéis separados |
| 16 | Arquivo `.svc` sem dados | Exportação | Exportar o CSV da captura |
| 17 | `T` passa de 250 °C | Probe | Probe depois do `Max Sat` mostra o patamar |
| 18 | Valor errado de `v_in` em t = 11 s | Conferência | Usar 9,25 mV (e 9,756 mV em regime) |

Dois cuidados gerais, que evitam vários dos problemas acima:

- **Depois de qualquer alteração, recompile e recarregue o modelo no HIL.** Senão o Scope mostra o modelo antigo.
- **Não compile durante a gravação.** Toda mudança durante o vídeo deve ser só em campos do SCADA.

---

## 11. Checklist final

- [ ] Virtual HIL, passo de 20 µs, Execution rate `inherit`
- [ ] Saturações com Min (teto) → Max (piso); constantes conferidas
- [ ] `TF_tau` em domínio contínuo, num `[1]`, den `[0.5 1]`
- [ ] `CF_estatica` compila; entradas `Tj` (1ª) e `dT_cj` (2ª); saída `v_s`
- [ ] `Sine` com unidade de frequência confirmada; `Gain_bl = 0.2e-3`; `n_bl` com desvio 1
- [ ] `SI_Tj0` nas duas somas (`Sum_dev` e `Sum_back`)
- [ ] `SI_dTcj` na 2ª entrada do `CF_estatica`; `SI_esp` no Product do ruído
- [ ] Probe `v_in` na saída do `Sum_in`; ramo `v_ideal` montado em paralelo
- [ ] Scope: 10 KSPS ou mais, legenda visível, painéis separados
- [ ] Ensaios (a), (b), (c) e (a') conferidos com a Seção 9
- [ ] Painel SCADA salvo e CSV exportado
