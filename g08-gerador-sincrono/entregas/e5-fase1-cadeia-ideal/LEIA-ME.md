# Fase 1 — Entrega 01: cadeia ideal (G08)

Sensor: potenciômetro de precisão Bourns 3590S-2-103L (Cap. 7.1.1/7.1.2).
Circuito: laço de corrente 4–20 mA com transmissor TI XTR115 (Cap. 6.4).
Especificação (família C): faixa 4–20 mA, erro de linearidade < 1 % FE.

## O que tem aqui

| Pasta | Conteúdo | Vai para o PR? |
|---|---|---|
| `relatorio/` | `relatorio.pdf` (final) e `figuras/` em PNG | sim |
| `typhoonsim/` | `modelo.tse`, `instrucoes.md`, `captura-scada.png`, `dados/*.csv` | sim (a pasta `modelo Target files/` é gerada na compilação e não vai) |
| `Fase1_Latex/` | fonte do relatório (`Equipe_08_F1E01_CadeiaIdeal.tex` + `corpo.tex` etc.) e `figs/` em PDF | decidir: o README pede só o PDF, mas o grupo já entregou fonte antes |
| `reprodutibilidade/` | scripts que geram todos os números e figuras | recomendado (o professor já elogiou a rastreabilidade) |
| `apresentacao/` | `Equipe_08_F1E01_apresentacao.pptx` + `gera_slides.js` | decidir (fora da estrutura padrão) |

## Scripts (`reprodutibilidade/`)

| Script | Roda com | Faz |
|---|---|---|
| `parametros.py` | — | todos os valores do projeto, com a fonte ao lado |
| `projeto.py` | Python comum | memória de cálculo numérica, `resultados_projeto.json`, figuras 02 e 03, `gabarito_python.csv` |
| `esquematico.py` | Python comum + `schemdraw` | figura 01 (esquemático) |
| `monta_modelo.py` | Python da API do Typhoon | monta e compila `typhoonsim/modelo.tse` |
| `roda_typhoon.py` | Python da API do Typhoon | roda a simulação offline (cabo de 50 Ω e de 550 Ω) e exporta os CSV |
| `analisa_typhoon.py` | Python comum | verificação R5, `resultados_typhoon.json`, figuras 04–06, `Fase1_Latex/valores_typhoon.tex` |

O Python da API é o `.venv` que o grupo já tinha:
`C:\Users\Leonardo\Downloads\10.grupo\10.grupo\3.typhoonsim\.venv\Scripts\python.exe`
(tem o `typhoon_hil_api` 1.31.3). O TyphoonSim precisa estar aberto.

## Status

- [x] Pesquisa dos datasheets (Bourns 3590, TI XTR115, TI OPA333), com as citações no relatório.
- [x] Memória de cálculo, justificativa (R3b) e figuras de projeto.
- [x] `modelo.tse` montado, compilado e **simulado** no TyphoonSim 2026.2 (24/09): pela
      interface e pela API. Os dados estão em `typhoonsim/dados/` (cabo de 50 Ω e de 550 Ω).
- [x] Verificação R5: **atende**. Linearidade $1{,}1\times10^{-5}$ % FE (piso numérico), erro
      total 0,120 % FE (resistores comerciais), histerese nula, cabo de 550 Ω sem alterar a corrente.
- [x] `relatorio/relatorio.pdf` compilado com os resultados (8 páginas, contando a memória de
      cálculo). `Fase1_Latex.zip` foi atualizado com a mesma versão.
- [x] Slides gerados de novo com os resultados.
- [ ] Opcional: `captura-scada.png` hoje é o esquemático exportado. O README do repositório pede
      "esquemático **e** painel em execução, com valores visíveis". Se quiser seguir à risca,
      troque por um print com a janela do Scope aberta ao lado do esquemático.

## Como regerar tudo

1. Com o TyphoonSim aberto **e o Schematic Editor aberto** (sem ele, a simulação pela API
   trava em "Simulation ready!"; foi o que aconteceu às 18:56 de 24/09):
   `<python da API> reprodutibilidade/roda_typhoon.py`.
2. `python reprodutibilidade/analisa_typhoon.py`: figuras 04–06, números e
   `Fase1_Latex/valores_typhoon.tex`.
3. Se trocar a captura, copie `typhoonsim/captura-scada.png` para `Fase1_Latex/figs/`.
4. Compile `Fase1_Latex/Equipe_08_F1E01_CadeiaIdeal.tex` (Overleaf, pdfLaTeX, 2 vezes) e salve
   como `relatorio/relatorio.pdf`.
5. `node apresentacao/gera_slides.js` (precisa do pacote `pptxgenjs`).

**Atraso numérico.** O TyphoonSim executa os blocos de sinal a cada 1 ms, e cada passagem
sinal → circuito → sinal soma uma amostra. Entre θ_ref e I_LOOP há 2 ms de atraso puro, e as 2
primeiras amostras de I_LOOP saem nulas. `analisa_typhoon.py` estima esse atraso, compensa e
declara no relatório. Na Entrega 03 (degrau e pulso), esse atraso vai aparecer.

## Pontos para a equipe conferir antes de entregar

- A matrícula do Cleiber: o `README.md` do grupo tem `13957115426`, e o relatório anterior (e4)
  usa `20113298`. Usei `20113298`.
- `R_cabo = 50 Ω` é uma hipótese da equipe, declarada como tal no relatório.
- A classificação do Cap. 2 (ativo, por deflexão) segue a convenção de Doebelin, que é a do
  capítulo. O relatório também menciona o nome usado na eletrônica ("passivo").
