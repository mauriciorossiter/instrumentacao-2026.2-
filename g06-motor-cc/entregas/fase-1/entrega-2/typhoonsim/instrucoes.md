# Guia de simulação — Entrega 02 (G06) no Typhoon HIL

Cadeia termopar tipo K + amplificador de instrumentação com as camadas não ideais
(dinâmica, estática e espectral). Domínio **Signal Processing**, **Virtual HIL**.

> Nomes de menus e campos podem variar na 2026.3. Onde não foi confirmado, o texto avisa.

---

## 1. Visão geral

```
T_sweep ─► Sat_T ─┬─► Probe T*
                  └─► TF_tau ─┬─► Probe Tj
                              └─► CF_estatica (v_s) ─► Sum_in ─┬─► Probe v_in
                                                               └─► Gain_stage1 ─► Gain_stage2 ─► Sum_out ─► Sat ─► Probe v_out

n_comm ─┐
        ├─► Sum_ncm (n_cm) ─┬─► Gain_dm ─► Sum_in (2ª entrada)
n_bl ─► Gain_bl ┘           └─► Gain_cm ─► Sum_out (2ª entrada)
```

\* No esquemático da equipe o probe `T` está na saída do `T_sweep` (antes do `Sat_T`),
então ele passa de 250 °C. Para ver o patamar em 250 °C, ligue o probe na saída do Max do `Sat_T`.

---

## 2. Configuração do modelo

| Item | Valor |
|---|---|
| Arquivo | `entrega02_g06_termopar.tse` |
| Dispositivo | Virtual HIL (VHIL) |
| Passo de simulação (Ts) | **20 µs** ou menor |
| Execution rate dos blocos | `inherit` |

Por que 20 µs: o ruído de comutação está em 573 Hz (período ≈ 1,75 ms, ≈ 87 pontos por ciclo).

---

## 3. Blocos da cadeia completa (R10)

### 3.1 Saturações (Min + Max)

A biblioteca não tem bloco Saturation. Monte cada saturação com **Min Max** em série:

| Saturação | Bloco 1 (modo MIN) | Bloco 2 (modo MAX) |
|---|---|---|
| `Sat_T` [0; 250] | Min com Constant **250** | Max com Constant **0** |
| `Sat` [0; 5] | Min com Constant **5** | Max com Constant **0** |

Ordem: sinal → MIN (teto) → MAX (piso). Constantes trocadas travam a saída.

### 3.2 Parâmetros

| # | Bloco | Nome | Parâmetros |
|---|---|---|---|
| 1 | Ramp | `T_sweep` | Slope **25**, Start time **1**, Initial output **0** |
| 2 | Min + Max | `Sat_T` | teto 250, piso 0 |
| 3 | Transfer Function | `TF_tau` | num `[1]`, den `[0.5 1]`, **domínio contínuo (s)** |
| 4 | C Function | `CF_estatica` | ver seção 4 |
| 5 | Sine | `n_comm` | Amplitude **2e-3**, Frequency **573** (Hz), Phase 0, Offset 0 |
| 6 | Random Source | `n_bl` | normal, média **0**, desvio **1** |
| 7 | Gain | `Gain_bl` | **0.2e-3** |
| 8 | Sum | `Sum_ncm` | `++` |
| 9 | Gain | `Gain_dm` | **0.1** |
| 10 | Sum | `Sum_in` | `++` |
| 11 | Gain | `Gain_stage1` | **494.07** |
| 12 | Gain | `Gain_stage2` | **1** |
| 13 | Gain | `Gain_cm` | **494.07e-6** |
| 14 | Sum | `Sum_out` | `++` |
| 15 | Min + Max | `Sat` | teto 5, piso 0 |

Observações importantes:

- **Slope = 25** (°C/s). Com início em t = 1 s, a rampa chega a 250 °C em t = 11 s.
- **TF_tau:** se o ícone mostrar `H(z)` e houver um seletor de domínio, escolha **contínuo (s)**.
  No modo discreto, `[0.5 1]` é lido como `0,5·z + 1` (polo em z = −2), que é instável e gera
  **valores infinitos** em `Tj` e `v_in`.
  Alternativa discreta, só se o modo contínuo não existir (Ts = 20 µs):
  `num = [3.99992e-5]`, `den = [1 -0.99996000080]`.
- **Sine:** confirme se a frequência é em Hz ou rad/s. Se for rad/s, use `2*pi*573`.
- Os blocos 13 e 14 (vazamento do CMRR) dão ~1 µV e podem ser omitidos.

---

## 4. C Function `CF_estatica`

Cadastre na janela do bloco:

| Tipo | Nome | Valor |
|---|---|---|
| Input | `Tj` | (°C, vindo do `TF_tau`) |
| Output | `v_s` | (V) |
| Parameter | `dT_cj` | `10.0` (°C) |

Cole na aba **Output function**. Não declare `Tj`, `v_s` nem `dT_cj` no código e
não inclua o bloco de comentário. Se o compilador acusar `exp` indefinido, adicione
`#include <math.h>` na área de includes (se existir) ou na primeira linha.

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

Se houver erro de declaração no meio do código (`double p` após `if`), mova `double p;`
para junto de `double t;` no topo do laço.

Significado: `c[]` e `a0..a2` são constantes tabeladas do NIST ITS-90 (tipo K, 0–1372 °C).
O bloco não as calcula; ele só avalia E(t) a cada passo.

---

## 5. Ligações (fio a fio)

| De (saída) | Para (entrada) |
|---|---|
| `T_sweep` | `Sat_T` (Min) e Probe `T` |
| `Sat_T` (saída do Max) | `TF_tau` |
| `TF_tau` | `CF_estatica` (`Tj`) e Probe `Tj` |
| `CF_estatica` (`v_s`) | `Sum_in`, entrada 1 |
| `n_comm` | `Sum_ncm`, entrada 1 |
| `n_bl` | `Gain_bl` |
| `Gain_bl` | `Sum_ncm`, entrada 2 |
| `Sum_ncm` | `Gain_dm` **e** `Gain_cm` |
| `Gain_dm` | `Sum_in`, entrada 2 |
| `Sum_in` | `Gain_stage1` **e** Probe `v_in` |
| `Gain_stage1` | `Gain_stage2` |
| `Gain_stage2` | `Sum_out`, entrada 1 |
| `Gain_cm` | `Sum_out`, entrada 2 |
| `Sum_out` | Min do `Sat` |
| Max do `Sat` | Probe `v_out` |

Erro comum: o probe `v_in` deve sair do fio entre `Sum_in` e `Gain_stage1`.
Se sair depois do `Gain_stage1`, ele mede volts (494× maior) em vez de milivolts.

---

## 6. Uma camada por vez (R9)

Cada ramo termina em: `Gain 494.07 → Gain 1 → Min 5 → Max 0 → Probe`.
Monte esse final uma vez, selecione e copie com Ctrl+C / Ctrl+V.

| Ramo | Origem | Blocos | Probe |
|---|---|---|---|
| Ideal (E01) | saída de `Sat_T` | Gain **40.6e-6** | `vo_ideal` |
| Só não linearidade | saída de `Sat_T` | cópia do `CF_estatica` com `dT_cj = 0` | `vo_nl` |
| Só desvio de zero | saída de `Sat_T` | Gain **40.6e-6** → Sum com Constant **−0.3969e-3** | `vo_zero` |
| Só dinâmica | saída de `TF_tau` | Gain **40.6e-6** | `vo_din` |
| Só espectral | saída de `Sat_T` | Gain **40.6e-6** → Sum com saída do `Gain_dm` | `vo_esp` |

O roteiro agrupa `vo_nl` e `vo_zero` como `vo_est`. Manter dois probes permite conferir cada efeito.
O `Gain_dm` pode alimentar a cadeia completa e o ramo espectral ao mesmo tempo.

---

## 7. Configuração do Scope

| Campo | Valor | Motivo |
|---|---|---|
| Time interval | **15 s** (mínimo 14 s) | rampa termina em t = 11 s; dinâmica converge ~2,5 s depois |
| Sample rate | **10 KSPS** ou mais | o ruído de 573 Hz sofre alias com 1 KSPS |

Passo a passo:

1. No Schematic Editor, compile e carregue o modelo (Load model to HIL / Start simulation).
2. No SCADA, adicione o Scope e associe os sinais: `T`, `Tj`, `v_in`, `v_out` (e os `vo_*` dos ramos).
3. Coloque cada grandeza em painel/eixo separado: `v_in` está em mV e fica invisível junto de `T`.
4. Defina Time interval = 15 e Sample rate = 10 KSPS.
5. Inicie a simulação e dispare a captura logo em seguida.
6. **Recompile e recarregue o modelo depois de qualquer alteração**, senão o Scope mostra o modelo antigo.
7. Exporte a captura em CSV para análise.

Atraso do disparo: se a captura começar ~0,3 s depois do start, a rampa aparece em t ≈ 0,65 s no gráfico
em vez de 1 s. Isso não é erro; todos os instantes ficam deslocados igualmente.

**Captura do ruído (separada):** para medir ±0,10 V e σ ≈ 0,01 V, faça uma captura curta
(≈ 0,1 s a 50 KSPS) em regime, depois de t ≈ 14 s, ou use zoom no gráfico longo.

---

## 8. Valores esperados — cadeia completa

Médias, sem o ruído. Tempos na escala da simulação (rampa começando em t = 1 s).

| t (s) | T (°C) | Tj (°C) | v_in (mV) | v_out (V) |
|---|---|---|---|---|
| 0 a 1 | 0 | 0 | −0,397 | 0 |
| 2 | 25 | 14,19 | 0,168 | 0,083 |
| 3 | 50 | 37,73 | 1,122 | 0,554 |
| 6 | 125 | 112,50 | 4,215 | 2,083 |
| 9 | 200 | 187,50 | 7,242 | 3,578 |
| 11 | 250 | 237,50 | 9,249 | 4,570 |
| 12 | 250 | 248,31 | 9,688 | 4,786 |
| 13,5 | 250 | 249,92 | 9,753 | 4,819 |
| 15 | 250 | 250,00 | 9,756 | 4,820 |

Ruído sobreposto: `v_in` ≈ ±0,2 mV (573 Hz) + σ ≈ 0,02 mV; `v_out` ≈ ±0,10 V + σ ≈ 0,01 V.

Verificações rápidas:

- `Tj` fica ≈ **12,5 °C** abaixo de `T` durante a rampa.
- `v_out / v_in` = **494,07**.
- Antes da rampa, `v_out` fica em 0 V (desvio de zero); só sai de 0 acima de ~10 °C.

### Camadas isoladas

| Camada | Esperado |
|---|---|
| Não linearidade (`dT_cj = 0`) | ≈ **+25 mV** (0,50 % FS) em ~135 °C |
| Desvio de zero | **−0,196 V** (−3,9 % FS) em toda a faixa; 0 V abaixo de ~10 °C; **4,82 V** em 250 °C |
| Dinâmica | ≈ 0,25 V abaixo do ideal na rampa; converge ~2,5 s após t = 11 s |
| Espectral | ±0,10 V em 573 Hz + σ ≈ 0,01 V |
| Cadeia completa | ≈ −3,7 % FS em regime; ≈ −8,6 % FS durante a rampa |

---

## 9. Solução de problemas

| Sintoma | Causa provável | Ação |
|---|---|---|
| `Tj` e `v_in` infinitos | `TF_tau` em modo discreto (z) | Trocar para contínuo (s) ou usar os coeficientes discretos da seção 3.2 |
| `v_in` em ~494× o esperado | probe depois do `Gain_stage1` | Mover o probe para a saída do `Sum_in` |
| `v_in` e `v_out` em 0, `T` sobe | `Tj` ou `v_s` em 0 | Probe em `Tj`, `v_s` e `Gain_dm` e seguir a cadeia; ver cadastro de `Tj`/`v_s` no C Function |
| `v_out` travado em 5 V | constantes do Min/Max trocadas | Min com 5, Max com 0 |
| Erro de compilação em `exp` | falta `math.h` | Adicionar `#include <math.h>` |
| Erro de redeclaração | `dT_cj`, `Tj` ou `v_s` declarados no código e no bloco | Declarar só na janela do bloco |
| Ruído em frequência errada | sample rate baixo (alias) | Usar ≥ 10 KSPS |
| Scope não muda após editar | modelo antigo carregado | Recompilar e recarregar |
| Ruído aleatório maior que o previsto | `Gain_bl` ou desvio do `n_bl` fora do especificado | Conferir `Gain_bl = 0.2e-3` e `n_bl` com desvio 1 |

---

## 10. Checklist final

- [ ] Ts = 20 µs, Virtual HIL
- [ ] `T_sweep`: slope 25, start 1, initial 0
- [ ] `Sat_T` e `Sat` com Min (teto) → Max (piso)
- [ ] `TF_tau` em modo contínuo
- [ ] `CF_estatica` compila, com `Tj`, `v_s`, `dT_cj = 10.0`
- [ ] Probes: `T`, `Tj`, `v_in` (saída do `Sum_in`), `v_out`
- [ ] Ramos R9 com probes `vo_ideal`, `vo_nl`, `vo_zero`, `vo_din`, `vo_esp`
- [ ] Scope: 15 s, ≥ 10 KSPS
- [ ] Valores conferidos com a seção 8
- [ ] CSV exportado
