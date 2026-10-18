# Fase 1 — Entrega 03: validação funcional (G08)

Vídeo de 5 a 8 min no TyphoonSim com o painel SCADA, mais um mini relatório de até 2 páginas.
**Prazo: domingo, 18/10/2026, às 12h.** A especificação é o
`ECOM060_Fase1_Entrega03_Orientacao_Video.pdf` (R11–R14).

A cadeia das Entregas 01 e 02 é usada **como está**. Os scripts daqui importam os parâmetros e o
código C de `../e6-fase1-nao-idealidades/reprodutibilidade/` e não alteram nada lá.

## Estado

- [x] **Item 1 — gerador de ensaios** (`monta_modelo_e03.py`): degrau, condição inicial e pulso em
      blocos nativos, em paralelo à varredura da E01. O disparo é ao vivo pelo SCADA ou automático
      (rodada offline).
- [x] **Item 2 — entradas SCADA**: seletor de ensaio, disparo, parâmetros e liga/desliga das três
      camadas (11 SCADA Inputs, listados em `typhoonsim/instrucoes.md`).
- [x] **Item 4 — gabarito Python** (`ensaios.py`): os três ensaios, a tabela por camada (R13) e as
      figuras 15 e 16. Ele reproduz o `gabarito_completa.csv` da E02 em 5×10⁻¹¹ mA.
- [x] Fiação do modelo conferida contra o gabarito com uma API simulada (5×10⁻¹³).
- [ ] **Na máquina com o TyphoonSim:** `monta_modelo_e03.py` → `roda_ensaios.py` →
      `compara_ensaios.py`.
- [ ] Item 3 — painel SCADA (`.cus`): widgets ligados aos SCADA Inputs e Trace Graph
      `theta_ref` × `theta_med`.
- [x] Roteiro do vídeo e rascunho do mini relatório (docs no Claude) e slide de abertura.
- [ ] Gravação, preencher tempos/links do mini relatório.

## Scripts (`reprodutibilidade/`)

| Script | Roda com | Faz |
|---|---|---|
| `parametros_e03.py` | — | importa E01 + E02 sem alteração e define os parâmetros dos ensaios |
| `ensaios.py` | Python comum | gabarito dos 3 ensaios → `gabarito/`; figuras 15–16 → `figuras/` |
| `monta_modelo_e03.py` | Python da API do Typhoon | gera e compila `typhoonsim/modelo_e03.tse` (plano B automático) |
| `roda_ensaios.py` | Python da API do Typhoon | 3 ensaios offline (completa e ideal) → `typhoonsim/dados/` |
| `compara_ensaios.py` | Python comum | TyphoonSim × gabarito → `gabarito/comparacao_typhoon.json`, figura 17 |
| `slide_cadeia.py` | Python comum | slide de abertura do vídeo → `figuras/slide-00-cadeia.png` |
| `inspeciona_blocos_e03.py` | Python da API do Typhoon | diagnóstico dos nomes de propriedade (SCADA Input etc.) |

## Resultado esperado (resumo para o R13)

| Ensaio | Folga (R6) | Resolução (R6) | Ruído 1/f (R8) | Dinâmica (R7) |
|---|---|---|---|---|
| (a) degrau | 0 | 0,18° | 4,7×10⁻⁶° | 0 |
| (b) condição inicial | **1,00°** | 0,18° | 1,2×10⁻⁶° | 0 |
| (c) pulso | **1,00°** | 0,18° | 4,7×10⁻⁶° | 0 |

A camada **estática (folga)** é a que mais afasta a medida, e aparece só quando o eixo volta ou
quando o cursor é deslocado. Os três ensaios dão a mesma forma de resposta (a saída copia a
referência com 2 ms de atraso numérico), como se espera de um sensor de **ordem zero**.
