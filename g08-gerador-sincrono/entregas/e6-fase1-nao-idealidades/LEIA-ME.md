# Fase 1 — Entrega 02: não idealidades (G08)

Continuação de `../e5-fase1-cadeia-ideal/`, com a mesma cadeia: Bourns 3590S → OPA333 → XTR115 →
laço 24 V → 250 Ω. **O circuito não muda** (R10). As três camadas agem sobre o potenciômetro.

**Prazo:** 5–7/out/2026, com apresentação de 25 min.
**Especificação:** `../Apresentação_Entrega_1.pdf`. Apesar do nome, é a apresentação do
**professor** sobre a Fase 1 inteira.
- p. 7: requisitos R6–R10.
- p. 8: atribuições.
- p. 10: formato.
- p. 11: dicas.

## Comece por aqui

| Arquivo | Para quê |
|---|---|
| **`EXPLICACAO_E02.md`** | o que foi feito, etapa por etapa: esperado × feito × resultado, hipóteses, pendências e perguntas prováveis |
| **`FUNDAMENTOS_E02.md`** | os conceitos que o relatório assume conhecidos |
| `relatorio/relatorio.pdf` | **entregável: versão curta, 3 páginas** (formato pedido) |
| `relatorio/relatorio_completo.pdf` | versão completa, 7 páginas (deduções e uma figura por requisito) |
| `apresentacao/Equipe_08_F1E02_apresentacao.pdf` | **apresentação em PDF** (13 slides, 25 min) |
| `apresentacao/Equipe_08_F1E02_apresentacao.pptx` | a mesma apresentação, editável (PowerPoint / Google Slides) |
| `apresentacao/roteiro.md` | texto de apoio, slide a slide, e perguntas prováveis |
| `typhoonsim/instrucoes.md` | como rodar no TyphoonSim (máquina do Leonardo) e o que esperar |

## Atribuição do G08 e resultado

| Req. | Camada | Modelo | Desvio máx. contra a E01 |
|---|---|---|---|
| R6 | estática: resolução + histerese do contato | escada de 5000 espiras (0,72°) + folga de 1,0° | 1,36° (0,038 % FE); histerese de 1,44° |
| R7 | dinâmica: ordem zero | y = K·x; polos reais da eletrônica quantificados (τ = 0,88 µs) | 3,2×10⁻⁴° |
| R8 | espectral: ruído de contato 1/f | ΔRc 1/f com pico de 100 Ω (ENR) × corrente no cursor (200 pA) | 2,9×10⁻⁵°; sem buffer: 0,55 % FE de ruído + 8,4 % de carga |
| R10 | as três no circuito da E01 | — | erro total de 0,120 → **0,155 % FE**: **atende** (< 1 %) |

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `reprodutibilidade/` | scripts (tabela abaixo), `gabarito_<caso>.csv`, `resultados_camadas.json` |
| `Fase1_Latex/` | `Equipe_08_F1E02_NaoIdealidades.tex` (curta) + `corpo_curto.tex`; `Equipe_08_F1E02_NaoIdealidades_completo.tex` + `corpo_completo.tex`; `valores_python.tex` (gerado); `valores_typhoon_pendente.tex`; `figs/` |
| `relatorio/` | os dois PDFs e `figuras/` em PNG |
| `apresentacao/` | `.pptx` e roteiro |
| `typhoonsim/` | **`modelo.tse` (entrega: E01 em C + E02 nativa)**, `modelo_r8_sem_buffer.tse` (anexo R8), `alternativa_c_function/` (mesmo modelo com as camadas em C), `instrucoes.md`; `dados/` sai das simulações |

## Scripts (`reprodutibilidade/`)

| Script | Roda com | Faz |
|---|---|---|
| `parametros.py` | — | valores da E01 + bloco "Entrega 02", com as fontes |
| `modelo_camadas.py` | — | **definição única** das camadas, do contrafactual R8 e das métricas |
| `camadas.py` | Python comum | gabarito, figuras 07–11 e 13, `resultados_camadas.json`, `valores_python.tex` |
| `confere_c.py` | Python comum + gcc | emula os blocos nativos da E02 e compila o C da E01 (texto do `.tse`); confere contra o Python (10 casos: **iguais**) |
| `monta_modelo.py` | Python da API do Typhoon | gera `modelo.tse` (**E01 intacta em C function + E02 toda em blocos nativos**; plano B automático em C) e `modelo_r8_sem_buffer.tse` |
| `inspeciona_blocos.py` | Python da API do Typhoon | diagnóstico: nomes reais de propriedades e terminais dos blocos nativos |
| `roda_typhoon.py` | Python da API do Typhoon | 4 casos + 2 do contrafactual → `typhoonsim/dados/` |
| `analisa_typhoon.py` | Python comum | métricas nos CSV, figuras 12 e 14, `valores_typhoon.tex` |
| `gera_slides.py` | Python comum + python-pptx | apresentação (.pptx), com os números do gabarito ou do TyphoonSim; o PDF sai de `soffice --headless --convert-to pdf` |

## Status

- [x] Especificação localizada; datasheets reconferidos (Bourns 3590, catálogo Bourns para o ENR, TI OPA333 e XTR115).
- [x] Modelo das 3 camadas, gabarito Python, figuras e números.
- [x] Modelo do TyphoonSim: E01 intacta em C, E02 toda nativa (inclusive o ruído 1/f), plano B e contrafactual R8, todos **conferidos** e **compilados no Typhoon 2026.3 desta máquina**.
- [x] Análise do TyphoonSim escrita e testada com CSVs sintéticos.
- [x] Relatório em duas versões (3 e 7 páginas); as células do TyphoonSim aparecem como "[pend.]".
- [x] Apresentação (13 slides, .pptx e PDF) e roteiro.
- [x] Os três `.tse` (nativo, alternativa em C e contrafactual R8) montados e **compilados** no Typhoon 2026.3.
- [ ] **Simular:** bloqueado pela licença ("appropriate license is not available" ao iniciar, nas duas versões). Depois de liberar: `roda_typhoon.py` → `analisa_typhoon.py` → `gera_slides.py` → recompilar → zip.
- [ ] Captura de tela (esquemático + Scope em execução) → `typhoonsim/captura-scada.png`.
- [ ] Equipe endossar as hipóteses H1–H7 (`EXPLICACAO_E02.md` §11).

## Como regerar

```bash
cd reprodutibilidade
python camadas.py            # gabarito, figuras, valores_python.tex
python confere_c.py          # (opcional) blocos/C x Python
# na máquina com o Typhoon (ver typhoonsim/instrucoes.md):
#   <python da API> monta_modelo.py ; <python da API> roda_typhoon.py
python analisa_typhoon.py
python gera_slides.py
# compilar os dois .tex de Fase1_Latex/ (pdfLaTeX, 2x) e copiar para relatorio/:
#   Equipe_08_F1E02_NaoIdealidades.pdf          -> relatorio/relatorio.pdf
#   Equipe_08_F1E02_NaoIdealidades_completo.pdf -> relatorio/relatorio_completo.pdf
```
