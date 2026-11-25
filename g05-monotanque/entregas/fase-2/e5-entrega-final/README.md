# Entrega final (Fase 2) — Instrumentação não ideal e seus efeitos no controle

**G05 — Monotanque (nível de líquido)** · ECOM060 Instrumentação Eletrônica · UFAL 2026.2

O nível que o sensor entrega ao controlador difere do nível que o tanque realmente tem. Este material mostra
quais características do instrumento causam isso, a partir de que intensidade o controle de nível falha e o que
fazer a respeito. Tudo roda em **um modelo** e **um painel SCADA**, em laço contínuo.

## Arquivos

| Arquivo | O que é |
|---|---|
| `relatorio/relatorio.pdf` | relatório final, itens 1 a 9 do Quadro 1 |
| `typhoonsim/monotanque_final.tse` | modelo: planta (equivalente elétrico) + caminho ideal + caminho real (sensor, condicionamento, processamento) + PI |
| `typhoonsim/painel_final.cus` | painel HIL SCADA com 8 cenários prontos |
| `apresentacao/apresentacao.pdf` | slides da apresentação |

## Versão e requisitos

- **Typhoon HIL Control Center 2026.2** (licença acadêmica), dispositivo **Virtual HIL** (não precisa de hardware).
- Passo de simulação 20 µs; escalas 1 V = 10 cm, 1 A = 1 L/s, 1 s de circuito = 100 s de tanque. Os tempos abaixo
  já estão na escala do tanque (o gráfico do SCADA mostra segundos de circuito: 1,5 s no gráfico = 150 s no tanque).

## Preparar (uma vez)

1. Abra `typhoonsim/monotanque_final.tse` no **Schematic Editor**.
2. Confira em *Model → Model settings*: dispositivo **Virtual HIL**, passo 2e-5 s.
3. Compile pelo menu suspenso **Compile and (re)load model in SCADA VHIL MODE** (a primeira carga leva alguns minutos).
4. No **HIL SCADA**, abra `typhoonsim/painel_final.cus`, clique em **Lock** (cadeado) e em **Start simulation**.
5. O painel começa no padrão: malha fechada, realimentação REAL, sensor nos valores do datasheet. O quadro
   **ESTADO ATUAL** mostra o que está valendo; o botão **RESTAURAR PADRÃO** volta a esse ponto.

Cada cenário (coluna 1 do painel) aplica todos os valores e dispara o ensaio. O evento acontece em t = 150 s
(1,5 s no gráfico); espere ~6 s de gráfico para ver o regime.

## Repetir o item 4 (malha aberta, ideal × real)

1. Clique em **CENÁRIO 1 — MALHA ABERTA**. A bomba leva o nível a 0,5 m e sobe 20 % em t = 150 s.
2. Esperado: nível real 0,720 m; nível medido ≈ 0,735 m (**erro ≈ 14,7 mm**, display
   "Medido − real").
3. Contribuição de cada característica: clique em **DESLIGAR TUDO** (medido = real) e digite **uma** característica
   no seu valor do datasheet; clique em DISPARAR. Esperado no fim do degrau: dT_ar_C = 5 → 8,1 mm;
   e0_mm = 5 → 5,0 mm; tau_filtro_s = 1 → atraso de 1,03 s; ruído, 60 Hz e ADC < 1 mm.
4. Correções: comp_termica = 1 e cal_zero_mm = 5 → erro ≈ 2,2 mm.

## Repetir os itens 5 e 6 (mesmo PI, instrumento ideal × real)

1. **CENÁRIO 2 — instrumento IDEAL** (degrau de referência 0,5 → 0,6 m). Esperado: nível real em 0,600 m,
   tₛ ≈ 77 s, Mₚ ≈ 0,20 %, bomba ≤ 8,5 L/s → todos os critérios atendidos.
2. **CENÁRIO 3 — instrumento REAL** (mesmo PI). Esperado: nível **medido** em 0,600 m e nível **real** em
   ≈ 0,585 m (**15,4 mm abaixo**: falha o critério de 5 mm).
3. **CENÁRIO 4 — REAL + correções**: erro real cai para ≈ 1,5 mm.
4. Perturbação: no campo Ensaio escolha **2 Degrau de consumo**. Esperado: pico ≈ 26,3 mm (ideal) e
   ≈ 30,3 mm (real), volta à faixa em ~60 s.

## Repetir o item 7 (ponto de ruptura)

As previsões foram registradas antes de simular (relatório, item 7).

| Característica | Onde mudar | Valores a testar | Esperado (VHIL) |
|---|---|---|---|
| latência | `t_lat_s` (ou CENÁRIO 5 = 12 s) | 0,14 · 8 · 9 · 10 · 12 | ok até 7 s; falha (tₛ/Mₚ) em 8 s; oscilação a partir de 12 s (previsto MF = 0 em 12,0 s) |
| gradiente térmico | `dT_ar_C`, com `e0_mm` = 0 | 0 · 1 · 2 · 3 · 4 · 5 | ok até 2 °C; falha em 3 °C (previsto 2,7 °C) |
| laço de terra | `R_terra_mOhm`, com comp_termica = 1, cal_zero_mm = 5 (CENÁRIOS 6 e 7) | 0 · 0,4 · 1 · 5 · 8 · 10 | erro > 5 mm a partir de 0,6 mΩ (previsto 0,41); instável em 10 mΩ (previsto 10,4 mΩ) |

Com 1 mΩ o nível real fica ≈ 13,9 mm **acima** da referência; com 10 mΩ oscila (bomba batendo em 0 e 20 L/s).

## Repetir o item 8 (compensação)

1. **CENÁRIO 7** (laço de 10 mΩ, entrada simples): a malha oscila.
2. **CENÁRIO 8** (mesmo laço, **entrada DIFERENCIAL**, CMRR 60 dB): a oscilação some e o erro volta a
   ≈ 1,4 mm. A ruptura do erro passa de ~0,6 mΩ para ~1000 mΩ.

## Equipe

Carlos Vinicius de Souza Cassimiro · Nelson Alves Sousa Moreira · Pedro Henrique Santos Resende
