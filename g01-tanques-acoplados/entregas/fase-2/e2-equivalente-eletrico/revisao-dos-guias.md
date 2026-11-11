# Revisao dos dois guias recebidos

Os guias `guia_fase2_entrega02.md` e `passo_a_passo_typhoon.md` foram usados
como propostas tecnicas. As exigencias academicas vieram do documento
`ECOM060_Fase2_Entrega02_Orientacao.pdf` e do pedido do usuario.

| Ponto | Avaliacao e ajuste aplicado |
|---|---|
| Analogia e escalas | Corretas: v=10h, i=q, t_original=100t_eletrico; C1=C2=500 uF; G1=G2=0,00316227766017 A/sqrt(V). |
| Acoplamento | Correto usar i12=G1 sqrt(v1). Um resistor entre N1/N2 com lei sqrt(v1-v2) mudaria a planta da Entrega 01. |
| Bloco de raiz | Existe `core/Mathematical function` com `mathematical_fn=sqrt` nesta versao. Foram usados apenas componentes nativos; nenhuma C function foi necessaria. |
| Passo eletrico 50 us | Foi recusado pelo compilador HIL404 nesta configuracao. O modelo salvo usa 1 us, com processamento de sinais a 100 us. |
| Pre-carga com ganho 2 A/V | Sem limite, pediria 20-24 A na partida. Foram acrescentados limitadores de +/-100 mA. Aguardar pelo menos 0,25 s simulados e conferir as tensoes antes do disparo. |
| Reinicio do pulso | O integrador nativo tem reset por nivel em `precarga`. Voltar a pre-carga reinicia o tempo; nao depende de parar todo o simulador. |
| Captura | 20 s eletricos, 1 kHz, disparo crescente em `u_ensaio=0,5`, sem pre-trigger. Com 5% de pre-trigger seria necessario esperar preencher o buffer antes de disparar. |
| Valores do painel | Ao trocar q ou k, atualizar a condicao inicial de equilibrio: Vref1=10(Q_rel/G1_rel)^2 e Vref2=10(Q_rel/G2_rel)^2. Os presets fazem isso. |
| Erro prometido de 0,012 mm | Nao era resultado de Typhoon. Os dados reais mostraram erro maximo de 0,684309 mm na condicao inicial, compativel com o residuo da pre-carga e a amostragem do disparo. Os nove ensaios atenderam a 2 mm e 1%; maior diferenca de metrica 0,3333%. |
| Criterios | 2 mm correspondem a 0,2% do nivel nominal de 1 m; 1% e um limite separado para cada metrica. Nao se equipara automaticamente isso a metade de um orcamento de erro da Fase 1. |
| Compressao temporal | Preserva a dinamica da planta apos reconversao. Um futuro filtro/sensor de 20 Hz tambem precisara de escalonamento temporal para preservar a cadeia completa. |
| TyphoonSim x VHIL | TyphoonSim independente e simulador offline. SCADA Input usa o valor padrao nessa modalidade. O painel Standalone altera os valores antes de cada execucao e chama o solver offline via API. O HIL SCADA regular com Capture/Scope continua sendo uma rota separada para VHIL. |
| Scope offline | Alem da lista de sinais, o Scope precisa de `signals_data`. Salvar e reabrir o modelo inicializa a captura. O valor `0.001` no campo `data_sampling_rate` e o intervalo de amostragem em segundos. |
| Dados reais | CSVs `dados/offline` e figuras `offline-*` foram obtidos do solver nativo. `scada-*.json` registra r3a e os dois ajustes de sensibilidade executados pela interface. A comparacao Python usa as EDOs da E01 como referencia. |

## Referencias tecnicas

- [TyphoonSim](https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/typhoonsim.html).
- [HIL SCADA e Virtual HIL](https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/hil_scada.html).
- [Limites do Standalone HIL SCADA](https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/standalone_scada.html).
- [SCADA Input](https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/References/scada_input.html).
- [Integrator](https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/References/accumulator_integrator.html).
- [Mathematical function](https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/References/mathematical_function.html).
- [API do Schematic Editor](https://www.typhoon-hil.com/documentation/typhoon-hil-api-documentation/schematic_api.html).
- [Propriedades dos widgets SCADA](https://www.typhoon-hil.com/documentation/typhoon-hil-api-documentation/widget_prop.html).

Consultadas em 10/11/2026. O inventario local confirma os nomes usados na API 1.32.1 / aplicativo 2026.3.
