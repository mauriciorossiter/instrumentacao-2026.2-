# Fase 2 - Entrega 02: equivalente elétrico

O circuito nativo reproduz a cascata da Entrega 01: v=10h, i=q e
t_original=100t_elétrico. Os **nove ensaios foram executados no TyphoonSim
2026.3**. O erro máximo de nível foi **0,684309 mm** (limite de 2 mm) e a
maior diferença relativa de métrica foi **0,3333%** (limite de 1%).

- [Relatório](relatorio/relatorio.pdf), [circuito](relatorio/figuras/circuito-equivalente.png) e [slides](apresentacao/apresentacao.pdf).
- [Modelo para TyphoonSim independente](typhoonsim/modelo-offline.tse),
  [painel Standalone](typhoonsim/painel-offline.cus) e [roteiro](typhoonsim/instrucoes.md).
- [Capturas reais](simulacao/dados/offline/) e [tabelas de comparação](simulacao/resultados-offline.md).
- [Revisão dos guias](revisao-dos-guias.md) e [registro de validação](simulacao/estado-validacao.json).

Os slides registram a etapa de validação em Python. O relatório e as tabelas
de comparação registram os resultados finais obtidos no TyphoonSim.

Para abrir a interface sem Control Center, executar `python iniciar_painel_offline.py`
na pasta `typhoonsim`. Selecionar um preset e clicar **Executar ensaio no
TyphoonSim**. O painel ajusta os parâmetros antes da execução, aciona o solver
nativo e mostra o gráfico da captura concluída. Pela interface foram
confirmados r3a, k2×2 e q0×0,5. A variação dos parâmetros ocorre entre execuções.

O procedimento usa **TyphoonSim offline + SCADA Standalone**. O enunciado
menciona o fluxo VHIL/SCADA; não houve execução em Virtual HIL ou no HIL SCADA
regular. Para esse outro ambiente, o pacote preserva [modelo.tse](typhoonsim/modelo.tse),
[painel.cus](typhoonsim/painel.cus) e [executar_vhil.py](typhoonsim/executar_vhil.py).

Título do PR: `g01 — Fase 2, Entrega 2: Equivalente Elétrico dos Tanques`.
