# G01 · Fase 2, Entrega 03 — Instrumentação em malha aberta

Os dois pontos de medida são os níveis dos tanques acoplados. A planta é o
equivalente da Entrega 02. Cada nível alimenta dois caminhos no mesmo modelo:
referência ideal e cadeia piezoresistiva simulada. Nenhuma leitura realimenta a planta.

- [Relatório R1–R6](relatorio/relatorio.pdf) e [figuras](relatorio/figuras/)
- [Modelo TyphoonSim](typhoonsim/modelo.tse), [painel SCADA Standalone](typhoonsim/painel.cus)
  e [instruções de reprodução](typhoonsim/instrucoes.md)
- [Previsões registradas antes dos ensaios](simulacao/previsoes.md) e
  [capturas e métricas](simulacao/dados/)
- [Apresentação em PowerPoint](apresentacao/apresentacao.pptx), com notas para
  os quatro integrantes (7 min + 3 min de perguntas)

O termo *medição real* designa o modelo do instrumento com não idealidades,
executado no solver offline do TyphoonSim 2026.3. Não designa dados de bancada.
Os parâmetros de não idealidade são hipóteses declaradas; as especificações
do transdutor são citadas separadamente no relatório.

Título de PR sugerido: `g01 — Fase 2, Entrega 3: Instrumentação em Malha Aberta`.
