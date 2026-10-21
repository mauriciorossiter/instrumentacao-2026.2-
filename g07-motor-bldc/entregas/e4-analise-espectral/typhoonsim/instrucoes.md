# Instruções — modelo TyphoonSim `modelo.tse`

**Disciplina:** Instrumentação Eletrônica (ECOM60) — UFAL, 2026.2
**Sistema 8:** Motor BLDC MOONS' R42BLD30L3 — Equipe 07
**Modelo:** `faixa_e_alcance` (salvo no Typhoon HIL Control Center 2026.2, dispositivo alvo HIL404)

Este documento explica o que o modelo faz, como abri-lo e executá-lo, e como gerar a partir dele o arquivo `dados_ruido_velocidade_bldc.csv` usado no relatório de intervalos de confiança (Seção 5.4.2).

---

## 1. O que o modelo representa

O modelo simula o **canal de leitura de velocidade** do motor BLDC como um instrumento com:

1. **Característica ideal** `y_id = x` (ganho unitário);
2. **Faixa de medição limitada** `[n_min, n_max]` (saturação);
3. **Ruído aleatório aditivo** representando o *jitter* de borda dos sensores Hall causado pela EMI do chaveamento do estator;
4. **Sinal de validade** indicando quando a entrada está dentro da faixa.

### Diagrama de blocos

```
                     ┌──────────────┐     ┌────────────────────┐     ┌──────┐
 Triangular Wave ──► │ Gain "y_id=x"│ ──► │ Limit1 [n_min,n_max]│ ──► │ Sum2 │ ──► y_instrumento
 (0 → x_hi, f_tri)   └──────────────┘     └────────────────────┘     │  +   │
        │                   │                       │                 │  +   │ ◄── Random Source1 (Normal)
        │                   │                       └───────► Sum1 (+)└──────┘
        │                   └───────────────────────────────► Sum1 (−) ──────────► e_dev
        │
        ├──────────────────────────────────────────────────────────────────────► x_referencia
        │
        ├──► Comparator1: x > n_min ──┐
        │                             ├──► AND ──► valid
        └──► Comparator2: n_max > x ──┘
```

### Blocos e parâmetros

| Bloco | Tipo | Parâmetros | Função |
|---|---|---|---|
| `Triangular Wave Source1` | Fonte triangular | min = 0, max = `x_hi`, f = `f_tri`, taxa = 100 µs | Estímulo de velocidade de referência (rampa) |
| `y_id = x` | Ganho | K = 1, taxa = `Ts` | Característica estática ideal |
| `Limit1` | Saturação | inferior = `n_min`, superior = `n_max` | Faixa de medição do instrumento |
| `Random Source1` | Fonte aleatória | Normal, média = −2, desvio = 2, taxa = 100 µs | Ruído/jitter de borda (EMI) |
| `Sum2` | Soma (++) | — | `y_instrumento = Limit(x) + ruído` |
| `Sum1` | Soma (+−) | — | `e_dev = Limit(x) − x` |
| `Constant1`, `Constant2` | Constantes | `n_max`, `n_min` | Limites da faixa |
| `Comparator1`, `Comparator2` | Comparadores | — | `x > n_min` e `n_max > x` |
| `Logical operator2` | AND | 2 entradas | `valid = 1` quando x está dentro da faixa |
| `Scope1` | Osciloscópio | 4 viewports | Exibe `y_instrumento`, `x_referencia`, `e_dev`, `valid` |

### Probes (sinais exportáveis)

| Probe | Significado | Unidade |
|---|---|---|
| `x_referencia` | Velocidade verdadeira (entrada) | rpm |
| `y_instrumento` | Leitura do instrumento (saturada + ruído) | rpm |
| `e_dev` | Desvio por saturação `Limit(x) − x` | rpm |
| `valid` | 1 = dentro da faixa, 0 = fora | — |

---

## 2. Parâmetros de inicialização (`model_init`)

Os parâmetros ficam em **Schematic Settings → Initialization** (código Python executado antes da compilação). Os limites da faixa são **derivados** da cadeia de medição, não digitados:

| Variável | Valor | Origem |
|---|---|---|
| `f_clk` | 1,0 MHz | Clock do timer de captura |
| `p` | 4 | Pares de polos do motor |
| `N` | 6·p = 24 | Bordas Hall por revolução |
| `M_max` | 2¹⁶ − 1 = 65 535 | Contador de 16 bits |
| `n_min` | 60·f_clk / (N·M_max) ≈ **38,15 rpm** | Menor velocidade antes do estouro do contador |
| `n_max` | **4000 rpm** | Velocidade nominal |
| `A` | n_max − n_min ≈ **3961,85 rpm** | Alcance (*span*) |
| `Ts` | 100 µs (10 kHz) | Passo de execução |
| `x_hi` | 4200 rpm | Topo da rampa (ultrapassa n_max para testar a saturação) |
| `T_sweep` | 40 s | Período da triangular |
| `f_tri` | 1/T_sweep = 0,025 Hz | Frequência da rampa |

Ao compilar, o console deve mostrar:

```
n_min=38.1476  n_max=4000.0  A=3961.8524
```

> ⚠️ O comentário da linha `x_hi = 4200.0` diz "varre APENAS 0 a 80 rpm", mas isso é resquício de uma versão anterior. Com `x_hi = 4200` a rampa varre de 0 a 4200 rpm. Para investigar só a região próxima de `n_min`, troque para `x_hi = 80.0`.

---

## 3. Como executar a simulação (modo padrão: ensaio de faixa e alcance)

1. Abra o **Typhoon HIL Control Center** e, nele, o **Schematic Editor**.
2. **File → Open** e selecione `modelo.tse`.
3. Confira em **Schematic Settings → Initialization** se o código do item 2 está presente.
4. Em **Schematic Settings → Configuration**:
   - Dispositivo: **HIL404** (ou o disponível / Virtual HIL);
   - Tempo de simulação: **40 s** (um período completo da triangular).
5. Clique em **Compile** (ou `Ctrl+F5`) e verifique o console.
6. Abra o **HIL SCADA**, carregue o modelo e clique em **Start simulation**. Sem HIL físico, marque **Virtual HIL** antes.
7. Acompanhe o `Scope1` (ou adicione as probes ao *Capture/Scope* do SCADA).

### O que deve ser observado

- `x_referencia`: rampa de 0 a 4200 rpm em 20 s e de volta a 0 em mais 20 s.
- `y_instrumento`: acompanha a rampa, mas fica **preso em ≈ 38,15 rpm** abaixo de `n_min` e **preso em 4000 rpm** acima de `n_max`, com ruído sobreposto.
- `e_dev`: zero dentro da faixa; positivo abaixo de `n_min` e negativo acima de `n_max` (erro por saturação).
- `valid`: 1 apenas quando `n_min < x < n_max`.

---

## 4. Como gerar os dados de ruído (`dados_ruido_velocidade_bldc.csv`)

O CSV usado no relatório foi obtido com o motor em **regime permanente a 4000 rpm**, isolando o ruído. O modelo, como está salvo, **não** está nessa configuração. Faça as alterações abaixo em uma cópia (ex.: `modelo_ruido.tse`):

### 4.1 Alterações no modelo

| Item | Configuração salva | Configuração para o ensaio de ruído |
|---|---|---|
| Estímulo | Triangular 0 → 4200 rpm | Substituir por **Constant** com valor `4000` (ou triangular com min = max = 4000) |
| `Random Source1` – média | −2 rpm | **0 rpm** |
| `Random Source1` – desvio padrão | 2 rpm | **≈ 9,05 rpm** |
| Cálculo de `e_dev` | `Limit(x) − x` (sem ruído) | **`y_instrumento − x`** (ruído incluso) |
| Tempo de simulação | 40 s | ≥ **0,5 s** (500 amostras a 1 ms) |

> ⚠️ **Importante sobre `e_dev`:** no modelo salvo, `Sum1` recebe a saída do `Limit1` (antes do ruído) e subtrai `x`. Logo, `e_dev` mostra só o erro de saturação e vale zero dentro da faixa. Para o relatório, em que `e(t) = y(t) − x(t)`, ligue a entrada `+` do `Sum1` na **saída do `Sum2`** (`y_instrumento`) em vez da junção do `Limit1`. Alternativamente, mantenha o modelo e calcule `e = y_instrumento − x_referencia` no pós-processamento.

> Observação: com x = 4000 rpm exatamente igual a `n_max`, o `Limit1` não satura, mas `valid` pode indicar 0 (comparação estrita). Isso não afeta a análise de ruído.

### 4.2 Captura e exportação

1. No HIL SCADA, abra **Capture/Scope**.
2. Selecione as probes `x_referencia`, `y_instrumento` e `e_dev`.
3. Configure a captura com **taxa de 1 kHz** (1 ms entre amostras) e **500 amostras** — ou capture a 10 kHz e decime por 10 no pós-processamento.
4. Inicie a simulação, aguarde o fim da captura e exporte em **CSV**.
5. Renomeie/organize as colunas no formato:

```
Amostra,Tempo_s,x_referencia_rpm,e_dev_rpm,y_instrumento_rpm
1,0.0,4000.0,4.5876,4004.5876
2,0.001,4000.0,-1.2552,3998.7448
...
```

### 4.3 Conferência rápida (Python)

```python
import pandas as pd

d = pd.read_csv("dados_ruido_velocidade_bldc.csv")
e = d["y_instrumento_rpm"] - d["x_referencia_rpm"]
print("N =", len(e))
print("média =", e.mean())        # esperado ≈ 0,08 rpm
print("s     =", e.std(ddof=1))   # esperado ≈ 9,03 rpm
print("s²    =", e.var(ddof=1))   # esperado ≈ 81,5 rpm²
```

Valores obtidos com o CSV atual (N = 500): média = 0,08 rpm, s = 9,03 rpm, s² = 81,52 rpm².

---

## 5. Pós-processamento: intervalos de confiança

```python
import numpy as np
import pandas as pd
from scipy import stats

e = pd.read_csv("dados_ruido_velocidade_bldc.csv")["e_dev_rpm"].to_numpy()
alpha = 0.05

for N in (10, 50, 500):
    x = e[:N]
    m, s = x.mean(), x.std(ddof=1)
    # IC da média (t de Student; para N >= 30, t ≈ Z = 1,96)
    t = stats.t.ppf(1 - alpha/2, N - 1)
    ic_mu = (m - t*s/np.sqrt(N), m + t*s/np.sqrt(N))
    # IC da variância (qui-quadrado)
    chi_hi = stats.chi2.ppf(1 - alpha/2, N - 1)
    chi_lo = stats.chi2.ppf(alpha/2, N - 1)
    ic_var = ((N-1)*s**2/chi_hi, (N-1)*s**2/chi_lo)
    print(f"N={N:3d}  x̄={m:6.2f}  s={s:5.2f}  "
          f"IC(µ)=[{ic_mu[0]:.2f}; {ic_mu[1]:.2f}]  "
          f"IC(σ²)=[{ic_var[0]:.2f}; {ic_var[1]:.2f}]")
```

> Este script usa as **primeiras** N amostras do arquivo. Se os cenários A e B do relatório foram tirados de outro trecho, ajuste o fatiamento (`e[i0:i0+N]`) e registre no relatório qual trecho foi usado.

---

## 6. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Erro "name 'n_min' is not defined" | Código de inicialização ausente | Colar o bloco `model_init` em Schematic Settings → Initialization |
| `e_dev` sempre zero a 4000 rpm | `Sum1` ligado antes do ruído | Ver item 4.1 (religar ao `Sum2`) |
| Média do ruído ≈ −2 rpm | `Random Source1` com média −2 | Ajustar média para 0 |
| Desvio do ruído ≈ 2 rpm | `Random Source1` com desvio 2 | Ajustar desvio para ≈ 9,05 |
| Simulação lenta | 40 s a passo de 100 µs | Reduzir tempo de simulação para o ensaio de ruído (0,5–1 s) |
| `valid` = 0 a 4000 rpm | Comparação estrita com `n_max` | Esperado; usar x ligeiramente menor (ex.: 3999) se precisar de `valid = 1` |

---

## 7. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `modelo.tse` | Modelo TyphoonSim (ensaio de faixa e alcance) |
| `dados_ruido_velocidade_bldc.csv` | 500 amostras do ruído a 4000 rpm (1 ms) |
| `relatorio.pdf` | Relatório da Equipe 07 — intervalos de confiança |
| `instrucoes.md` | Este documento |
