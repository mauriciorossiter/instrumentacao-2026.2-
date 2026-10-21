# Geração de Dados — Equipe 8 (Resolução) — Guia TyphoonSim

**Disciplina:** ECOM060 — Instrumentação Eletrônica — UFAL — 2026.2
**Equipe:** Abraão · Mayara · Paulo — **Característica: Resolução**
**Instrumento:** amperímetro digital de 12 bits, FS = 4,095 mA, **∆c = 1 µA** (coerente com o relatório oficial revisado).

> Guia completo para montaem da parte do **TyphoonSim**. Cobre: (1) o **bloco do instrumento** com 1 entrada e 1 saída, (2) o **rig de geração de dados** com ruído e pontos fixos, e (3) o **formato de entrega**.
> Os dois esquemáticos devem ser commitados junto com este arquivo para as figuras aparecerem no GitHub.

---

##  **O que já está montado (para conferência):**





- **Bloco `Amperímetro Digital`** (subsystem) — 1 entrada `i`, 1 saída `i_read`. Interior (todos com *execution rate* `1e-4`):
  `i → Gain_in (1e6) → Round1 (floor) → Gain_out (1e-6) → Limit1 [inferior 0 ; superior 4.095e-3] → i_read`
- **Esquemático de simulação** (Root do modelo `.tse`), já ligado:
  - `Constant1` (o **ponto fixo** de corrente, em ampères) → entrada `+` do `Sum1`
  - `Random Source1` (Distribution = **Normal**, **Mean = 0**, **Standard deviation = 1**, rate `100e-6`) → `Gain1` (`0.3e-6`, rate `100e-6`) → outra entrada `+` do `Sum1`
    *(o `Gain1` reduz o ruído unitário para σ = 0,3 µA; o campo do Random não aceitava `0.3e-6` direto)*
  - `Sum1` (Constant1 + ruído) → entrada `i` do bloco
  - Probe **`i_read`** na saída do bloco → é o `y_instrumento`
  - Probe **`i_in`** no sinal que entra no bloco ⚠️ *neste modelo o `i_in` está **depois** do `Sum1`, então ele **inclui ruído**. Por isso o `x_referencia` da entrega **não** é o `i_in`, e sim o **valor do `Constant1`** do ponto (ver [Seção 6.1](#61-o-que-me-enviar)).*

![Bloco Amperímetro Digital](bloco_amperimetro.png)

![Esquemático de simulação — Equipe 8 (Resolução)](esquematico_simulacao.png)


> **Parâmetros do instrumento:** 12 bits · FS = 4,095 mA · Δc = 1 µA. No Typhoon, decimal é **com ponto** (`1.00050e-3`); vírgula só separa itens de lista.

---

## Índice

- [ STATUS ATUAL: blocos prontos — falta só simular e exportar](#-status-atual-blocos-prontos--falta-só-simular-e-exportar)
- [1. O que a Equipe 8 precisa produzir](#1-o-que-a-equipe-8-precisa-produzir)
- [2. Esquemático completo dos blocos](#2-esquemático-completo-dos-blocos)
- [3. O bloco do instrumento no TyphoonSim](#3-o-bloco-do-instrumento-no-typhoonsim)
  - [3.1 Por que a probe N é desnecessária](#31-por-que-a-probe-n-é-desnecessária)
  - [3.2 Como criar o bloco passo a passo](#32-como-criar-o-bloco-passo-a-passo)
  - [3.3 Como usar o bloco na geração de dados](#33-como-usar-o-bloco-na-geração-de-dados)
- [4. Modificações no esquemático passo a passo](#4-modificações-no-esquemático-passo-a-passo)
- [5. Parâmetros da campanha de dados](#5-parâmetros-da-campanha-de-dados)
- [6. Execução e captura](#6-execução-e-captura)
  - [6.1 O que me enviar](#61-o-que-me-enviar)
  - [6.2 Erros comuns](#62-erros-comuns)
- [7. O que NÃO fazer](#7-o-que-não-fazer)
- [8. Formato final de entrega](#8-formato-final-de-entrega)
- [9. Checklist antes de enviar](#9-checklist-antes-de-enviar)
- [10. O que enviar de volta](#10-o-que-enviar-de-volta)

---

## 1. O que a Equipe 8 precisa produzir

O protocolo da nossa equipe (Resolução) é **pontos fixos de x, com muitas repetições no mesmo valor**, mais as duas exigências comuns a todas as equipes: **ruído de medição obrigatório** e **dados brutos** (sem pré-processar).

| Exigência do PDF de orientação | Como se traduz para nós |
|---|---|
| Sinal: **pontos fixos de x, com múltiplas repetições no mesmo valor** | Manter x **constante** em alguns valores e coletar **≥ 50 amostras** em cada (usaremos **100**). |
| O que precisa aparecer: **muitas repetições no mesmo x (mín. 50)** | Cada ponto fixo vira dezenas de leituras repetidas do **mesmo** x verdadeiro. |
| **Ruído de medição obrigatório** (o efeito "só existe em relação a um piso de ruído") | Injetar **ruído gaussiano** na cadeia, **antes** do quantizador. Sem ruído, todas as repetições seriam idênticas e a análise estatística fica impossível. |
| **Não pré-processar** | Exportar exatamente como lido: sem média, sem filtro, sem suavização. |
| Colunas obrigatórias do PDF: `tempo`, `x_referencia`, `y_instrumento`, `repeticao` | `x_referencia` = **valor do `Constant1`** do ponto (mensurando aplicado, sem distorção); `y_instrumento` = **`i_read`** (leitura quantizada, com ruído); `repeticao` = 1..100. Capturar `i_read` (e `i_in` para conferência); as colunas finais são montadas depois. |
| Metadados (equipe, característica, unidades, faixa nominal) | Montados no arquivo final de entrega. |

**Ideia física central da resolução:** ao repetir a medida de um **mesmo** x, a leitura cai numa **grade discreta de 1 µA** (os patamares do A/D). O ruído faz a leitura, de vez em quando, "pular" para o nível vizinho — e é essa dispersão sobre níveis discretos que revela a resolução. Por isso escolhemos pontos fixos em posições diferentes dentro do patamar (uns no meio, outros perto da borda).

---

## 2. Esquemático completo dos blocos

Visão geral do que será montado no TyphoonSim. A fonte de **pontos fixos** e o **ruído** (fora do bloco) alimentam o **bloco do instrumento**; capturamos `i_in` (x limpo) e `i_read` (leitura quantizada).

![Esquemático de geração de dados — Equipe 8 (Resolução)](esquematico_geracao_dados_equipe08.svg)

Cadeia interna do instrumento (mesma do relatório oficial):

```
i  →  Gain_in (×1e6 = 1/∆c)  →  Floor (Round, floor)  →  Gain_out (×1e-6 = ∆c)  →  Sat [0; 4,095 mA]  →  i_read
```

Pontos-chave do desenho:
- **`i_in`** é probado **direto na fonte de x**, **antes** do ruído → é o `x_referencia` limpo.
- O **ruído** entra **só** no ramo do quantizador (via `Sum`), **fora** do bloco do instrumento.
- **`i_read`** é a saída do bloco (após a saturação) → é o `y_instrumento`.
- **Não há probe `N`** — ver Seção 3.1.

---

## 3. O bloco do instrumento no TyphoonSim

> ✅ **JÁ CONCLUÍDO.** O bloco `Amperímetro Digital` já está criado e validado (ver STATUS no topo). Esta seção fica como **referência** de como ele foi feito — quem só vai gerar os dados pode pular para a [Seção 6](#6-execução-e-captura).

O professor pediu um **bloco do nosso instrumento com exatamente 1 entrada e 1 saída**. O instrumento é a função **corrente medida → leitura**:

- **Entrada:** `i` (corrente medida)
- **Saída:** `i_read` = `î = N·∆c` (leitura reconstruída)

![Bloco do instrumento — símbolo mascarado e vista interna](bloco_instrumento_equipe08.svg)

### 3.1 Por que a probe N é desnecessária

O código digital **`N`** é a saída do bloco `Floor` — uma **variável intermediária interna** do quantizador (vem *antes* do `Gain_out`). **`N` não é a leitura do instrumento**; é apenas um sinal de depuração/conferência.

- O instrumento tem **1 entrada (`i`) e 1 saída (`i_read`)** — `N` não deve ser uma porta de saída.
- A entrega exige apenas `x_referencia` e `y_instrumento` (= `i_read`); `N` não é usado.

**Conclusão: a probe `N` foi removida do bloco.** Se quiser conferir o código durante os testes, pode ligar um probe `N` **temporário e interno**, mas ele **não** faz parte do bloco nem vira porta de saída.

### 3.2 Como criar o bloco passo a passo

**Pré-requisito:** ter a cadeia `Gain_in → Floor → Gain_out → Sat` montada no canvas (a mesma do relatório).

**Método rápido — agrupar o que já existe:**
1. No **Schematic Editor**, selecione os 4 blocos `Gain_in`, `Floor`, `Gain_out`, `Sat` (segure **Ctrl** para marcar vários, ou arraste um retângulo de seleção em volta deles).
2. **Botão direito → Create Subsystem** (em algumas versões: *Create Subsystem from selection*). O editor cria **um único bloco Subsystem** e gera automaticamente as **portas** nos fios que cruzam a fronteira.
3. **Duplo-clique** no Subsystem para entrar. Já existirão uma **Port de entrada** e uma **Port de saída**.
4. **Renomeie as portas:** duplo-clique em cada uma → entrada = **`i`**, saída = **`i_read`**. (Se faltar alguma, arraste um **Port** da biblioteca *Ports & Subsystems* e conecte.)
5. Volte ao nível de cima (botão **Up** / breadcrumb). O bloco agora tem **1 entrada (`i`)** e **1 saída (`i_read`)**.

**Método do zero — bloco vazio:**
1. Arraste um **Subsystem** vazio da biblioteca *Ports & Subsystems* para o canvas.
2. Duplo-clique para entrar; adicione uma **Port In** e uma **Port Out**.
3. Monte lá dentro `Gain_in → Floor → Gain_out → Sat`, ligando **Port In → Gain_in** e **Sat → Port Out**.
4. Renomeie as portas para `i` e `i_read`.

**Dar nome, ícone e parâmetros (opcional, recomendado — "mask"):**
1. Botão direito no Subsystem → **Mask / Create Mask** (ou *Edit Mask*).
2. Em **Parameters**, crie: `n_bits` (= 12), `FS` (= 4.095e-3), `delta_c` (= 1e-6).
3. Nos blocos internos, use os parâmetros nas expressões: `Gain_in = 1/delta_c`, `Gain_out = delta_c`, limites do `Sat = [0, FS]`. Assim, mudar a resolução vira **só trocar um parâmetro**.
4. Em **Icon/Appearance**, dê o nome **"Amperímetro Digital"** e, se quiser, um desenho.
5. **Salvar como componente reutilizável:** botão direito → **Save as…** e/ou adicione à sua **User Library** para reaproveitar em outros modelos.

> **Observação de versão:** os nomes de menu podem variar levemente entre versões do Typhoon HIL (*Create Subsystem* / *Create Component* / *Mask Editor*). Se algum nome não bater exatamente, procure o equivalente no menu de **botão-direito** do bloco selecionado.

### 3.3 Como usar o bloco na geração de dados

Com o bloco pronto, o rig fica exatamente como o esquemático da Seção 2:
- **`Constant` (x fixo)** → derivação:
  - direto para o **Probe `i_in`** (`x_referencia`) — sinal **limpo**;
  - para o **`Sum`**, onde soma o **White Noise**;
- **`Sum` → entrada `i`** do bloco;
- **saída `i_read`** do bloco → **Probe `i_read`** (`y_instrumento`).

O **ruído fica FORA do bloco** (é condição de teste da geração de dados, não faz parte do instrumento). O bloco em si continua sendo só o quantizador — a característica de resolução —, **idêntico ao do relatório oficial**.

> **Alternativa válida:** se preferir modelar o ruído como *piso de ruído do próprio instrumento*, dá para colocá-lo **dentro** do bloco; nesse caso a entrada `i` seria o x limpo. Recomendamos manter **fora** para o bloco ficar igual ao do relatório.

---

## 4. Modificações no esquemático passo a passo

> ✅ **JÁ CONCLUÍDO.** O esquemático de simulação já está montado (Constant1 + Random Source1 → Gain1 → Sum1 → bloco, com probes `i_in` e `i_read`). Esta seção fica como **referência**. **Diferença em relação ao texto abaixo:** o ruído foi feito com **`Random Source1` (Normal, média 0, desvio 1) → `Gain1` (×`0.3e-6`)** — e não com um bloco "White Noise" com σ direto, porque o campo do Random recusa valores tão pequenos. O resultado é o mesmo: σ = 0,3 µA.

### 4.1 Entrada = ponto fixo (`x_referencia` limpo)
- **Remova/desative** a fonte `Ramp1` (ou ponha inclinação 0). Vamos **fixar**, não varrer.
- Deixe uma `Constant` cujo valor será o **ponto fixo de x** (editado entre capturas — ver Seção 5). Comece em `1.0005e-3` (1,0005 mA).
- Ligue um **Probe `i_in`** direto nessa `Constant`, **antes de qualquer ruído**. Esse probe é o `x_referencia`.

> ⚠️ O ruído **não** pode entrar no `i_in` — ele tem que ser o valor limpo aplicado. O ruído entra só no ramo que vai para o bloco do instrumento.

### 4.2 Injeção de ruído — **obrigatória**
- Na biblioteca **Signal Processing → Sources**, pegue o bloco de **ruído gaussiano/branco** (nome típico: *White Noise* ou *Gaussian Noise*; varia com a versão).
- Some o ruído ao x fixo, **antes** da entrada `i` do bloco:

```
Constant (x fixo) ──┐
                    Sum ── [ Bloco do Instrumento ] ── i_read
White Noise ────────┘
```

**Parâmetros do ruído (recomendados):**
- **Desvio-padrão σ ≈ 0,3 µA** (`3e-7` A). Se o bloco pedir **variância**, use `σ² = 9e-14`. Se pedir **PSD/potência**, ajuste até o scope mostrar desvio ~0,3 µA.
- **Média = 0**.
- **Sample time = passo de execução do subsistema SP** (o mesmo da captura). **Crítico:** se o ruído atualizar mais devagar que a captura, você grava o mesmo valor repetido e as "repetições" ficam **falsas** — cada amostra precisa ser um sorteio novo.
- **Seed (semente) fixa** (ex.: 1234) para reprodutibilidade.

> **Por que σ ≈ 0,3 µA (≈ 0,3 LSB)?** É "pequena amplitude" (só ~0,007 % do fundo de escala de 4,095 mA), mas comparável a uma fração do degrau de 1 µA — suficiente para provocar saltos de nível perto das bordas e quase nenhum salto no meio do patamar. Ajuste entre **0,2 e 0,4 µA** se quiser mais/menos dispersão.

### 4.3 Cadeia de quantização
É o **interior do bloco do instrumento** (Seção 3): `Gain_in ×1e6 → Floor → Gain_out ×1e-6 → Sat [0; 4,095 mA]`, **idêntica** ao relatório. Não mude o ∆c.

### 4.4 Probes a capturar
- `i_in` → x limpo (vira `x_referencia`).
- `i_read` → leitura quantizada, já com ruído (vira `y_instrumento`).
- ~~`N`~~ → **não capturar** (interno ao bloco; ver Seção 3.1).

---

## 5. Parâmetros da campanha de dados

Rode **5 pontos fixos**, **100 repetições cada** (bem acima do mínimo de 50). Os pontos varrem da região "estável" (meio do patamar) à "instável" (sobre a transição). O patamar N=1000 cobre x ∈ [1,000 ; 1,001) mA; as transições ficam nos múltiplos inteiros de 1 µA.

| Ponto | x fixo (`Constant`) | Posição no patamar | Dispersão esperada |
|:---:|:---:|---|---|
| P1 | `1.00050e-3` | centro do patamar (0,5 µA de cada borda) | quase nula — leitura ≈ 1,000 mA |
| P2 | `1.00080e-3` | 0,2 µA abaixo da transição em 1,001 | moderada — alguns saltos p/ 1,001 mA |
| P3 | `1.00095e-3` | 0,05 µA abaixo da transição | alta — maioria salta p/ 1,001 mA |
| P4 | `1.00100e-3` | **exatamente sobre a transição** | máxima — ~50/50 entre 1,000 e 1,001 mA |
| P5 | `1.00300e-3` | centro de outro patamar (contraste) | quase nula — leitura ≈ 1,003 mA |

**Configuração de captura por ponto:** 100 amostras, **sem decimação** (decimação = 1, para cada amostra ser um sorteio de ruído independente), no mesmo passo de execução do bloco de ruído.

---

## 6. Execução e captura

**Passo a passo da simulação (TyphoonSim 2026.3).**

> 👤 **Para a pessoa que vai gerar os dados.** Você **não precisa** montar nada — está tudo pronto. Siga os passos abaixo, um ponto de cada vez, e salve **um arquivo CSV por ponto**. No fim, mande os arquivos para o Paulo (ver [Seção 6.1](#61-o-que-me-enviar)).
>
> Os nomes de menu podem variar levemente na sua instalação; quando isso acontecer, procure a opção pela **função** descrita (o caminho mais provável está indicado). Decimais **com ponto**.

### Passo 1 — Abrir o modelo
1. Abra o **Typhoon HIL Control Center 2026.3**.
2. **File → Open** e abra o arquivo do modelo de simulação (o `.tse` que o Paulo enviou — é o que tem o `Constant1`, o `Random Source1` e o bloco `Amperímetro Digital`). Ele abre no **Schematic Editor**.

### Passo 2 — (opcional, 30 s) conferir se está tudo certo
Duplo-clique nos blocos e confira: `Gain_in = 1e6`, `Gain_out = 1e-6`, `Round1 = floor`, `Limit1 = [0 ; 4.095e-3]`, `Random Source1` (Normal, média 0, desvio 1), `Gain1 = 0.3e-6`. Se estiver assim, **não mexa em mais nada** além do `Constant1` (Passo 3).

### Passo 3 — Definir o ponto fixo (só o `Constant1` muda entre capturas)
1. **Duplo-clique no `Constant1`**.
2. No campo de valor, apague e digite o valor do ponto (em **ampères, com ponto**). Comece pelo **P1 = `1.00050e-3`**.
3. **OK**. (A lista completa dos 5 pontos está na [Seção 5](#5-parâmetros-da-campanha-de-dados) e é repetida no Passo 7.)

### Passo 4 — Compilar
1. Clique no botão **Compile** da barra de ferramentas (ícone de compilar; ou menu **Model → Compile**).
2. Espere aparecer a mensagem de sucesso no painel de saída (algo como *"compiled successfully"*).
3. **Se aparecer erro:** anote/print e veja a [Seção 6.2 — Erros comuns](#62-erros-comuns). Não adianta seguir sem compilar.

### Passo 5 — Carregar em Virtual HIL e abrir o HIL SCADA
1. Após compilar, abra o **HIL SCADA** (botão/atalho do SCADA na barra, ou o app **Standalone HIL SCADA V2026.3**).
2. No SCADA, **carregue o modelo compilado** e selecione o dispositivo **Virtual HIL** (é a simulação em tempo real no PC, não precisa de hardware). Caminho típico: **botão de carregar/Load → escolher Virtual HIL → Load**.
3. **Inicie a simulação** (botão de **Start/Run** no SCADA). A partir daí a simulação está rodando em tempo real.

### Passo 6 — Capturar os sinais `i_in` e `i_read`
1. Adicione (ou abra) um widget de **Capture** (também chamado *Signal Capture* / *Capture/Scope*). Caminho típico: menu de **widgets** do SCADA → **Capture**.
2. Nos sinais do Capture, selecione **`i_in`** e **`i_read`** (são os nomes dos probes do modelo).
3. Configure a captura:
   - **Número de amostras: `100`** (é o nº de repetições do ponto — bem acima do mínimo 50 do PDF).
   - **Decimação: `1`** ⚠️ **importante:** decimação 1 faz **cada amostra** ser um **sorteio novo de ruído** = uma repetição de verdade. Se você decimar/mediar, as repetições ficam falsas.
   - **Trigger:** manual/imediato (dispara na hora).
4. Deixe a simulação estabilizar **~1 s** e **dispare a captura**. Espere encher as 100 amostras.

### Passo 7 — Exportar para CSV (um arquivo por ponto)
1. No Capture, use **Export / Save data → CSV** (salvar os dados capturados).
2. Salve com um nome que identifique o ponto, por exemplo **`ponto1_1p00050mA.csv`**.
3. **Repita os Passos 3 a 7 para cada ponto**, mudando **só o valor do `Constant1`** e o **nome do arquivo**:

   | Ponto | Valor do `Constant1` | Nome do CSV |
   |:---:|:---:|:---|
   | P1 | `1.00050e-3` | `ponto1_1p00050mA.csv` |
   | P2 | `1.00080e-3` | `ponto2_1p00080mA.csv` |
   | P3 | `1.00095e-3` | `ponto3_1p00095mA.csv` |
   | P4 | `1.00100e-3` | `ponto4_1p00100mA.csv` |
   | P5 | `1.00300e-3` | `ponto5_1p00300mA.csv` |

   > Ao trocar o valor do `Constant1` você precisa **compilar de novo** (Passo 4) e recarregar/rodar (Passo 5) antes de capturar. Se o SCADA permitir editar o `Constant1` como um *slider/input* ao vivo, pode mudar por lá sem recompilar — mas o caminho garantido é recompilar.

**Resultado esperado:** **5 arquivos CSV**, cada um com uma coluna de **tempo**, os valores de **`i_in`** e os de **`i_read`** (100 linhas de dados por arquivo).




> **Alternativa (avançada): script Python (API do Typhoon).** Dá para automatizar tudo num loop com `typhoon.api.hil` (setar o valor do `Constant1`, rodar, capturar e exportar). A assinatura varia com a versão — se preferir esse caminho, peça ao Paulo o script já ajustado. O método manual acima já resolve.


---

## 8. Formato final de entrega

- **Nome:** `Equipe_08_Resolucao.csv` (ou `.xlsx`) — padrão do PDF `Equipe_0X_[Caracteristica]`.
- **Colunas obrigatórias (PDF):**
  - `tempo` — coluna de tempo (ou índice de amostra) do CSV capturado.
  - `x_referencia` — **valor do `Constant1`** daquele ponto (mensurando aplicado, **sem distorção**), repetido nas 100 linhas do ponto. *(Não usar a coluna `i_in`, que neste modelo já vem com ruído.)*
  - `y_instrumento` — a coluna **`i_read`** (leitura após a característica, com ruído).
  - `repeticao` — índice da repetição no mesmo ponto (1..100). **Obrigatória para a Equipe 8** (PDF).
- **Metadados (arquivo/aba à parte, PDF):** nome da equipe, característica = **Resolução**, **unidades de x e y** (A), **faixa nominal = [0 ; 4,095 mA]**. Não é preciso revelar parâmetros internos da função geradora.

---

## 9. Checklist

**Montagem (já concluída — só conferir se quiser):**
- [x] Bloco `Amperímetro Digital` com **1 entrada (`i`)** e **1 saída (`i_read`)**; **sem** porta `N`.
- [x] Ruído montado como `Random Source1` (Normal, média 0, desvio 1) → `Gain1` (`0.3e-6`) → `Sum1`, resultando em σ = 0,3 µA **antes** do quantizador.
- [x] Probe `i_read` na **saída** do bloco. (O probe `i_in` está após o `Sum1`, então inclui ruído — o `x_referencia` vem do valor do `Constant1`, não do `i_in`.)

**Execução (o que a pessoa faz — conferir antes de mandar):**
- [x] 5 pontos fixos capturados (P1–P5), **1000 amostras cada**, **decimação 1**.
- [x] Anotado qual **valor de `Constant1`** corresponde a cada CSV (vira o `x_referencia`).
- [x] Há **dispersão** nas repetições dos pontos de borda (P3/P4) e **pouca/nenhuma** nos do meio (P1/P5). Se P3/P4 não dispersarem, avise o Paulo (dá para aumentar σ trocando o `Gain1` para `0.35e-6`).
- [x] CSVs **brutos** salvos (sem média, filtro ou edição manual dos valores).


---

<sub>ECOM060 — Instrumentação Eletrônica · UFAL 2026.2 · Equipe 8 (Resolução) — Guia de geração de dados no TyphoonSim.</sub>
