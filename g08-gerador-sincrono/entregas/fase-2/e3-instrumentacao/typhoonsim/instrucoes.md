# Fase 2, Entrega 03 (G08): instrumentação em malha aberta, roteiro de repetibilidade (R6)

A E03 coloca, sobre o equivalente elétrico da E02, a medição da **tensão eficaz** e da **frequência** nos terminais do
gerador: um canal ideal (a planta) e um canal real (TP + AD637 + ADC; pré-filtro + comparador + contador). Tudo em
malha aberta (`malha` = 0). O mesmo modelo serve à E04, que fecha a malha; a cópia em `../../e4-controle/typhoonsim/` é idêntica.

## Versões e arquivos

| Item | Versão |
|---|---|
| Typhoon HIL Control Center | **2026.2**, modo Virtual HIL (VHIL), dispositivo HIL101; modelo só com a biblioteca `core`, sem C function |
| Python da API | `C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe` (abaixo, `$PY`) |
| Python (gabarito e comparação) | 3.12, NumPy, SciPy, pandas, Matplotlib |

Tudo o que é preciso está nesta pasta (`typhoonsim/`):

| Arquivo | Conteúdo |
|---|---|
| `instrumentacao_controle.tse` | modelo (estado padrão: malha aberta, cadeia real, sem degrau temporizado) |
| `painel_e3e4.cus` | painel SCADA |
| `monta_modelo.py`, `monta_painel.py` | regeram o `.tse` (com o Schematic Editor aberto) e o `.cus` (com o HIL SCADA aberto) |
| `roda_vhil.py` | roda os ensaios `e03_*` no VHIL e grava `dados/*.csv` |
| `dados/` | as capturas do VHIL usadas no relatório (CSV) |
| `gabarito/` | gabarito Python: `parametros_e34.py`, `sistema.py` (transcrição do modelo), `controle.py`, `e03.py` (R1–R5 → figuras e `resultados_e03.json`), `ensaios_e34.py` (tabela dos ensaios), `confere_fiacao.py` (executa a fiação do `.tse` bloco a bloco: diferença ≤ 1e-12), `compara_typhoon.py` (VHIL × gabarito → `comparacao_typhoon.json` e a figura 7 do relatório) |

O relatório está em `../relatorio/relatorio.pdf`. O gabarito lê os parâmetros da E02 em
`../../e2-equivalente-eletrico/typhoonsim/gabarito/` (e, por ela, os da E01).
## Topologia e valores

**Planta (igual à E02):** malha série `V_m` → `I_dw` → `L_inercia` (0,66215 H + 1 mH) → `R_amortec` (25·D Ω) →
`C_sincron` (21,822 mF) → `v_nl` → terra, com KV = 2,5 V/pu, KI = 0,1 A/(rad/s), passo de 20 µs.

**Elementos não lineares:**

- resíduo da swing equation: `v_nl = KV·Pmax(t)·sen(δ0 + vC/(KV·Ks)) − vC`, com δ = δ0 + vC/4,5826;
- tensão terminal (fasor): `Vt∠θt = (X′d·V∠0 + Xe·E′∠δ)/X`, com X′d = Xe = 0,30 pu, X = 0,60 pu; módulo por
  `sqrt`, ângulo por `atan2` (bloco `theta_t`); durante a falta na barra de AT, Vt = XT/(X′d + XT)·E′ = 0,30 pu;
- forma de onda no secundário do TP: `v(t) = √2·Vt·Vsec·(1 + eps_tp)·sen(ωs·t + θt) + ruído`.

**Cadeia de medição real (taxa de 100 µs, blocos nativos):** TP (erro `eps_tp` = 0,3 %) → ruído gaussiano
(`sigma` = 5 mV rms) → conversor RMS AD637 (filtro de 1ª ordem, `tau_rms` = 55 ms) → ADC de 12 bits (`nbits`) →
**V medida**. Em paralelo: pré-filtro (passa-baixas Sallen-Key de 150 Hz, ou passa-faixa 60 ± 5 Hz no R5 da E04) →
comparador de cruzamento por zero → contador de período com relógio `fclk` = 1 MHz → média de `n_cic` = 4 ciclos →
**f medida**. A cadeia **ideal** entrega Vt e ω da planta sem atraso nem erro.

**Controle (só na E04, `malha` = 1):** campo T′d0·dE′/dt = Efd − E′ (T′d0 = 6 s); AVR PI com Kp/Ki = T′d0 (o zero cancela
o polo do campo); PSS (lavagem + dois avanço-atraso) com ganho `Kpss` = 20, alimentado pela frequência (ideal ou medida).
Os valores numéricos estão em `gabarito/parametros_e34.py` e são gravados nos blocos por `monta_modelo.py`.
## Painel SCADA (`painel_e3e4.cus`)

| Botão | O que faz | Botão | O que faz |
|---|---|---|---|
| `Pm ON` / `Pm OFF` | degrau de Pm (+0,1 pu) | `Vref ON` / `VrefOFF` | degrau de Vref (+0,02 pu) |
| `FaltaON` / `FaltOFF` | falta na barra de AT | `FECHAR` / `ABRIR` | malha fechada / aberta |
| `FB REAL` / `FBIDEAL` | realimentação com a medição real / ideal | `PSS ON` / `PSS OFF` | liga / desliga o PSS |
| `PF  R5` / `PB 150` | pré-filtro passa-faixa (ação do R5) / passa-baixas 150 Hz | `IDEAL` / `REAL` | zera / restaura as seis características |

Caixas de texto (0 desliga a característica): `eps_tp` [%], `tau_rms` [s], `nbits`, `sigma` [V rms], `n_cic` [ciclos],
`fclk` [Hz] e `Kpss`. **A caixa começa vazia e não mostra o valor em uso:** o mostrador `em uso` ao lado de cada uma mostra
o valor que o modelo está usando. A linha `estado_*` (embaixo) mostra malha, realimentação, PSS, pré-filtro, degraus e falta
(0/1). Os botões enviam o valor no clique (não são chaves): confira o efeito pela linha de estado. Mostradores: V medida,
V real da planta, f medida e Efd; gráficos de tensão, frequência, Efd/PSS e δ.

## Abrir e rodar (passos 1 e 2, comuns)

1. Abra o Control Center e o **Schematic Editor**. Feche abas antigas (compilar uma aba velha sobrescreve o modelo).
   File → Open → `instrumentacao_controle.tse` → **Compile**.
2. Abra o **HIL SCADA** → **Load Model** → `instrumentacao_controle Target files/instrumentacao_controle.cpd` (criada pela
   compilação) → **Load Model to Virtual HIL (VHIL)**. **Panel → Open Panel** → `painel_e3e4.cus` → **Start**.
   *Esperado (malha aberta, cadeia real):* V real da planta = 1,0770 pu, V medida = 1,0800 pu (+0,3 %, erro do TP),
   f medida = 60,000 Hz, linha de estado `0 1 1 0 0 0 0`.

## Ensaios da E03 pela interface

3. **Ensaio (a), degrau de Pm.** Clique em `Pm ON`.
   *Esperado:* V real 1,0770 → 1º afundamento de 1,0635 pu cerca de 0,38 s depois → 1,0706 pu em regime. V medida
   1,0800 → 1,0670 pu (atraso de ~50 ms) → 1,0737 pu. f real com 1º pico de 60,038 Hz; f medida com 60,036 Hz, ~60 ms depois.
   Depois, `Pm OFF` e espere acomodar (~20 s, ζ = 2,3 %).
4. **Ensaio (c), falta.** `FaltaON` e logo depois `FaltOFF`. À mão, a duração passa do tempo crítico (288 ms) e o gerador
   perde o sincronismo: para voltar, Stop e Start. A falta de exatamente 200 ms sai do passo 7.
   *Esperado:* V real cai para 0,300 pu; a V medida leva ~0,1 s para chegar a 90 % do afundamento; a f medida dá um
   pico no início e no fim da falta (salto de fase).
5. **Cadeia ideal × real.** `IDEAL` zera as seis características (V medida = V real, f medida = f real); `REAL` restaura
   o padrão. Uma por vez: `eps_tp` = 0 tira o desvio de +0,3 %; `tau_rms` = 0 tira o atraso da V; `n_cic` = 0 faz a
   f medida igual à ideal; `sigma` = 0 tira o ruído. Confira cada valor no mostrador `em uso`.
6. **Exacerbação (R5).** `tau_rms` = 1 (a leitura quase não acompanha a falta); `n_cic` = 16 (f medida com 45 % da
   amplitude em 1,32 Hz); `fclk` = 2000 (saltos de ~1,8 Hz por ciclo); `sigma` = 1 (viés de +10 % na V medida e disparos
   falsos do comparador). Volte com `REAL`.
7. **Valores exatos (estados iniciais e degraus temporizados): por script.** Feche o SCADA, deixe o Schematic Editor
   aberto e rode, na pasta `typhoonsim`:

   ```powershell
   $PY = "C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe"
   & $PY roda_vhil.py                      # e03_a, e03_b, e03_b_N16, e03_c, e03_c_tau1 (~25 min)
   python gabarito\compara_typhoon.py      # Python comum
   ```

   O script remonta o modelo em cada ensaio (tensão inicial de `C_sincron`: 0 no (a), 2,913 V no (b), δ(0) = 60°; degrau
   de Pm em 1,0 s; falta de 1,0 a 1,2 s) e termina recompilando o estado padrão.
   *Esperado (VHIL × gabarito):* atraso da V medida de 50,1 ms (gabarito 50,8); da f medida, 64,2 ms (64,4); erro
   máximo da V de 0,0065 pu (0,0067); V ideal igual ao gabarito a 1e-5 pu; δ a 0,005°.

## Por script

```powershell
# na pasta typhoonsim
& $PY monta_modelo.py                 # regera o .tse (depois: Open + Compile)
& $PY monta_painel.py                 # regera o .cus (com o HIL SCADA aberto)
& $PY roda_vhil.py                    # capturas da E03 -> dados/e03_*.csv
python gabarito/e03.py                # gabarito, figuras 1-6 e 8, resultados_e03.json (~1 min)
python gabarito/confere_fiacao.py     # fiação do .tse x gabarito
python gabarito/compara_typhoon.py    # VHIL x gabarito -> figura 7
```

## Observações sobre o Typhoon HIL 2026.2 (já corrigidas em `monta_modelo.py`)

- *Signal switch*: `in` = entrada 1, `in1` = entrada 2, `in2` = controle.
- *atan2*: calcula `atan2(in, in1)`, então `in` = parte imaginária e `in1` = parte real; θt(0) = 0,2247 rad (12,88°).
- *Clock*: reinicia quando o estado ≥ `reset_at`; com 10 000 passos de 1e-4 o acumulado fica em 0,99999999999991,
  então o reinício é em 1 − Ts/2 (sem isso o passa-faixa dava um pulso a cada 1 s).
- A fonte `V_m` é *Signal Controlled Voltage Source* (a *Voltage Source* com entrada por sinal compilou como 0 V).
- A SCADA API não tem `set_widget_value` (as caixas começam vazias) nem caixa de seleção (por isso, pares de botões).
- O VHIL roda de 8 a 13 vezes mais devagar que o tempo real. A simulação offline (`roda_typhoon.py`) exige licença.
- O `Random Source` não tem semente: nos canais com ruído a comparação com o gabarito é pelo desvio-padrão.

## Captura de tela (esquemático + painel SCADA)

![Esquemático e painel de instrumentação](captura-scada.png)
