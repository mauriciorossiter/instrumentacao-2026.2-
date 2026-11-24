# G07 · Fase 2 · Entrega final

Motor BLDC MOONS' R42BLD30L3 acionando um ventilador: como a instrumentação não ideal da corrente de fase (sensor Hall ACS712-20A) muda o controle de corrente simulado no Typhoon HIL.

A entrega reúne as quatro entregas da Fase 2, que continuam nas pastas vizinhas: `e1-caracterizacao` (modelo e parâmetros do motor, base do item 1 e da demanda de medição), `e2-equivalente-eletrico`, `e3-instrumentacao` e `e4-malha-fechada`.

## O que há em cada pasta

| Pasta | Conteúdo |
|---|---|
| `relatorio/` | `relatorio.pdf` (entregável, um capítulo por item do Quadro 1 da orientação) e o fonte `relatorio.tex`, com `figuras/`, `tabelas/` e as figuras em TikZ (`fig1.tex` = Figura 1 da orientação preenchida; `fig_sistema.tex` = sistema original). Compilar com `xelatex relatorio.tex` duas vezes. |
| `apresentacao/` | `apresentacao.pdf` (15 slides), o fonte `apresentacao.tex` (usa as figuras de `../relatorio/figuras/`) e `roteiro.md`, com uma fala por slide para quem for apresentar. |
| `simulacao/` | `modelo_final.tse` (modelo único dos itens 4 a 8), `painel_final.cus` (HIL SCADA), `README.md` (versão do Typhoon, blocos de inicialização, caixas, presets e resultado esperado de cada captura), `codigo_c_functions.md` (código das C functions, para leitura) e `dados-vhil/` (todas as capturas em CSV). |

## Onde está cada item da orientação

| Item | Relatório | Slides | Dados |
|---|---|---|---|
| 1 · Sistema e equivalente | Seção 1 | 3–4 | — |
| 2 · Sensor e localização | Seção 2 (Fig. 2 = Figura 1 preenchida) | 5–6 | — |
| 3 · Características | Seção 3, Tab. 3 | 7 | — |
| 4 · Malha aberta | Seção 4 | 8 | `e3_a`, `e3_b`, `e3_c` |
| 5 · Controle ideal | Seção 5 | 9 | `e4_r3_ideal` |
| 6 · Controle real | Seção 6 | 10–11 | `e4_r3_real` |
| 7 · Ruptura | Seção 7 | 12 | `e4_r4_zero`, `e4_r4_rc`, `e4_r4_ruido` |
| 8 · Compensação | Seção 8 | 13–14 | `e4_r5_autocal`, `final_r3`, `final_ruido_hall`, `final_rc_hall`, `final_rc_hall_comp` |
| 9 · Síntese e reprodução | Seção 9 + `simulacao/README.md` | 15 | — |

## Observações

- Os arquivos `.svc` em `simulacao/dados-vhil/`, se aparecerem, são criados pelo Capture do HIL SCADA junto com cada CSV (guardam as configurações da captura). Não são usados pelo relatório e podem ser apagados.
- A pasta `simulacao/modelo_final Target files/` e os `.bak` são gerados pelo Typhoon ao compilar e salvar; não fazem parte da entrega.
- Os CSV `e3_*` e `e4_*` vêm das Entregas 03 e 04; o `modelo_final.tse` contém aqueles modelos sem alteração nesses caminhos, então os mesmos blocos de inicialização reproduzem os mesmos resultados.
