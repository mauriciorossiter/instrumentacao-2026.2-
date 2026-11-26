# Fase 2, Entrega Final (G08): instrumentação não ideal e seus efeitos no controle

**Sistema:** gerador síncrono de 100 MVA ligado a barramento infinito (swing equation), com equivalente elétrico RLC no
TyphoonSim. **Pergunta da entrega:** o que o instrumento entrega ao controlador difere do que a planta faz; quais
características causam isso, em que intensidade o controle falha e o que se pode fazer a respeito.

**Resposta curta.** O TP lê a tensão 0,3 % acima da real, o conversor RMS e o frequencímetro atrasam a leitura (≈ 50 e
64 ms) e o ruído do secundário vira ruído de frequência. O mesmo AVR + PSS que atende os 7 critérios com medição ideal,
com a medição real, deixa a planta 0,31 % abaixo da referência sem que nenhum mostrador perceba e reprova no esforço
(σ(Efd) = 0,120 > 0,10 pu). Pontos de ruptura (simulado / previsto antes): erro do TP 0,49 / 0,50 %; τ do AD637
109 / 98 ms; média N 7,4 / 7,1 ciclos; ruído 4,1 / 4,0 mV. Um passa-faixa de 60 ± 5 Hz no frequencímetro (filtragem,
Cap. 2) leva o ponto de ruptura do ruído a 12,4 mV e faz os 7 critérios passarem.

Equipe: Cleiber de Meireles da Silva Junnior (20113298), Leonardo Lima Barbosa Pereira (22110875),
Willian Tcheldon Oliveira Santos (17212878).

## Versões

| Item | Versão |
|---|---|
| Simulador | **Typhoon HIL Control Center 2026.2** (Schematic Editor + HIL SCADA), modo **Virtual HIL** (VHIL), dispositivo HIL101; modelo só com a biblioteca `core`, sem C function |
| Python da API do Typhoon | `C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe` (abaixo, `$PY`) |
| Python do gabarito | 3.12 com NumPy, SciPy, pandas e Matplotlib |

A simulação offline do TyphoonSim exige licença que o grupo não tem: tudo roda no VHIL.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `relatorio/relatorio.pdf` | **relatório**, organizado pelos 9 itens do Quadro 1 (a primeira página tem o mapa item → seção) |
| `relatorio/apresentacao.pdf` | slides da apresentação (20 min) |
| `relatorio/roteiro-apresentacao.md` | roteiro falado slide a slide, a demonstração no SCADA, o plano B e perguntas prováveis |
| `relatorio/figuras/` | as figuras do relatório em PNG (`fig-01` a `fig-14`) e prints do SCADA (`scada/`) |
| `typhoonsim/instrumentacao_controle.tse` | **o modelo** (planta da E02 + caminho ideal + caminho real + controle + seletor) |
| `typhoonsim/painel_e3e4.cus` | o painel SCADA (botões e caixas de cada característica) |
| `typhoonsim/instrucoes.md` | topologia, valores, painel e o roteiro completo de cada ensaio no SCADA |
| `typhoonsim/monta_modelo.py`, `monta_painel.py` | regeneram o `.tse` e o `.cus` pela API |
| `typhoonsim/roda_vhil.py` | roda no VHIL os ensaios do gabarito e grava `dados/<ensaio>.csv` |
| `typhoonsim/dados/` | as 16 capturas do VHIL das E03 e E04 (`e03_*`, `e04_*`) |
| `typhoonsim/gabarito/final.py` | **gera os itens 3 a 8**: figuras 4, 5, 7, 8, 11 e 13 e `resultados_final.json` |
| `typhoonsim/gabarito/compara_typhoon.py` | VHIL × gabarito: figuras 6 e 10 e `comparacao_typhoon.json` |
| `typhoonsim/gabarito/sistema.py`, `controle.py`, `parametros_e34.py` | o gabarito: o mesmo modelo do `.tse`, bloco a bloco (`confere_fiacao.py` confere a fiação com diferença ≤ 1e-12) |
| `typhoonsim/gabarito/e03.py`, `e04.py`, `ensaios_e34.py` | métricas e ensaios das E03/E04, usados pelos scripts acima |

O gabarito lê os parâmetros da planta das pastas irmãs `../e2-equivalente-eletrico/` e `../e1-caracterizacao/`, que
já estão no repositório: clone a pasta `entregas/fase-2/` inteira.

## Abrir o modelo (comum a todos os itens)

1. Abra o Control Center e o **Schematic Editor**. Feche abas antigas (compilar uma aba velha sobrescreve o modelo).
   File → Open → `typhoonsim/instrumentacao_controle.tse` → **Compile**.
2. Abra o **HIL SCADA** → **Load Model** → `instrumentacao_controle Target files/instrumentacao_controle.cpd` →
   **Load Model to Virtual HIL**. **Panel → Open Panel** → `painel_e3e4.cus` → **Start**.
3. *Esperado (malha aberta, cadeia real):* `mostrador_V_ideal` = 1,0770 (tensão **real da planta**),
   `mostrador_V_real` = 1,0800 (tensão **medida** pelo instrumento real, +0,3 % do TP), `mostrador_f_real` = 60,000 Hz.

Atenção a três detalhes do painel: (a) `V_ideal` é a grandeza real da planta e `V_real` é a leitura do instrumento
real; (b) as caixas de texto começam vazias e não mostram o valor em uso: confira nos mostradores `em_uso_*`; (c) o VHIL
roda 8 a 13 vezes mais devagar que o tempo real, então um degrau leva ≈ 30 s para acomodar na tela.

## Item 4: efeito em malha aberta, uma característica por vez

**Ao vivo.** Malha aberta (estado padrão). Clique em **IDEAL** (zera as seis características): V medida = V real.
Depois digite um valor numa única caixa e Enter:

| Caixa | Valor | Esperado |
|---|---|---|
| `eps_tp` | 0.3 | V medida 1,0802 contra 1,0770 da planta (+0,3 %, constante) |
| `tau_rms` | 0.055 | com **Pm ON**, a V medida acompanha a real ≈ 50 ms atrasada |
| `n_cic` | 4 | com **Pm ON**, a f medida acompanha a real ≈ 64 ms atrasada |
| `sigma` + `n_cic` | 0.005 e 1 | f medida oscila ≈ 4 mHz em torno de 60 Hz |

Volte com **REAL** (restaura as seis).

**Por script** (Python comum, na pasta da entrega):

```powershell
python typhoonsim/gabarito/final.py           # ≈ 12 min: itens 3 a 8; o item 4 e' a figura 5 e item4 no json
& $PY typhoonsim/roda_vhil.py fin_a_so_eps_tp fin_a_so_tau_rms fin_a_so_nbits fin_a_so_sigma fin_a_so_n_cic fin_a_so_fclk
python typhoonsim/gabarito/compara_typhoon.py # (opcional) compara as capturas fin_a_so_* com o gabarito
```

*Esperado (ensaio a, erro RMS da leitura):* tensão: todas 3,39 mpu; só TP 3,21; só AD637 0,75 (atraso 52 ms); só ADC
0,14; só ruído 0. Frequência: todas 5,10 mHz; só média N = 4 5,02 (atraso 64 ms); só ruído (N = 1) 4,39; só relógio
(N = 1) 2,14; referência N = 1 sozinho 1,55.

## Item 6: controle com instrumento real (e o item 5, com o ideal)

**Ao vivo.** **FBIDEAL** e **FECHAR**; espere acomodar (linha de estado `1 0 1 0 0 0 0`). **Vref ON**: a tensão vai
de 1,077 a 1,097 pu com sobressinal ≈ 4 % (item 5). **Vref OFF**. Agora **FB REAL**: a medida volta a 1,0770 e a
**planta desce para ≈ 1,0737 (−0,31 %)**; Efd fica ruidoso. **Vref ON**: medida 1,097, planta 1,094, sobressinal ≈ 10 %.

**Por script.** `final.py` (acima) gera as figuras 7 e 8 e as métricas `item5`/`item6` do `resultados_final.json`.
No VHIL (≈ 45 min, Schematic Editor aberto e HIL SCADA fechado):

```powershell
& $PY typhoonsim/roda_vhil.py e04_ideal_r e04_ideal_p e04_ideal_regime e04_real_r e04_real_p e04_real_regime
python typhoonsim/gabarito/compara_typhoon.py
```

*Esperado (planta, gabarito / VHIL):* ideal M_p 4,08 / 4,08 %, ζ 0,148 / 0,148; real erro −0,31 / −0,32 %,
σ(Efd) 0,120 / 0,118 pu, ζ 0,199 / 0,195.

## Item 7: ponto de ruptura

**Ao vivo** (malha fechada, **FB REAL**; volte com **REAL** entre um e outro):

| Caixa | Valor | Ação | Esperado | Ruptura (simulada) |
|---|---|---|---|---|
| `eps_tp` | 0.6 | — | planta 0,61 % abaixo da medida: reprova o erro de 0,5 % | 0,49 % |
| `tau_rms` | 0.25 | Vref ON | sobressinal ≈ 26 % (> 15 %) | 109 ms |
| `n_cic` | 16 | Pm ON | o rotor oscila sem amortecer (ζ ≈ 0,02 < 0,10) | 7,4 ciclos |
| `sigma` | 0.01 | — | Efd mais ruidoso, σ(Efd) ≈ 0,23 pu | 4,1 mV |

**Por script.** `final.py` grava primeiro as previsões (`item7_previsao`, com o horário) e só depois roda os níveis e a
bisseção (`item7`); a figura 11 mostra previsão × simulação.

## Item 8 (compensação)

**Ao vivo:** com **FB REAL**, clique em **PF R5** (pré-filtro passa-faixa 60 ± 5 Hz): o ruído do Efd cai à metade
(σ 0,120 → 0,064 pu); com **Pm ON** o rotor continua amortecido (ζ 0,159). **PB 150** volta ao passa-baixas.
**Por script:** figura 13 e `item8` do `resultados_final.json`; no VHIL, `roda_vhil.py e04_R5_r e04_R5_p e04_R5_regime`.

## Onde cada item do Quadro 1 está

| Item | Relatório | Arquivos |
|---|---|---|
| 1 Sistema e equivalente | §1, Fig. 1–2, Tab. 1 | `.tse` (planta), E02 |
| 2 Sensor e localização | §2, Fig. 3 (Figura 1 preenchida), Tab. 2–3 | `.tse`, `painel_e3e4.cus` |
| 3 Características | §3, Tab. 4, Fig. 4 | `final.py` (item 3) |
| 4 Malha aberta | §4, Fig. 5–6, Tab. 5 | `final.py`, `dados/e03_*` |
| 5 Controle ideal | §5, Tab. 6, Fig. 7 | `final.py`, `dados/e04_ideal_*` |
| 6 Controle real | §6, Fig. 8–10, Tab. 7–8 | `final.py`, `dados/e04_real_*` |
| 7 Ponto de ruptura | §7, Tab. 9, Fig. 11 | `final.py` (item 7) |
| 8 Compensação | §8, Tab. 10–11, Fig. 12–13 | `final.py`, `dados/e04_R5_*` |
| 9 Síntese e reprodução | §9, Fig. 14, este README | — |
