# G07 - Entrega 3: validação funcional

## Arquivos da entrega

| Arquivo | Conteúdo |
|---|---|
| `typhoonsim/modelo.tse` | Motor BLDC completo e três ensaios simultâneos da cadeia NTC + condicionamento |
| `typhoonsim/instrucoes.md` | Reprodução dos ensaios |
| `relatorio/relatorio.pdf` | Gráficos R11-R12 e síntese R13 |


## Executar e exportar

1. Abra `modelo.tse` no Schematic Editor, na perspectiva **TyphoonSim**.
2. Deixe **Stop time (s) = 60** e clique no **triângulo verde TyphoonSim**, imediatamente à esquerda do botão quadrado de parada. O motor e o inversor completos exigem muitos passos; mesmo com a duração reduzida, a execução pode demorar.
3. Aguarde **Simulation completed successfully**. Abra **Scope1**, que já contém todos os sinais dos três ensaios.
4. Compare **V_media** com **vT_ideal** nos três primeiros painéis. Exporte todos os sinais do Scope1 em CSV, cobrindo de 0 a 60 s, com gravação a cada 10 ms. Preserve `Time`, `G07_D_*`, `G07_CI_*`, `G07_P_*` e `n`.

**Compile model** compila para HIL101. O passo de hardware é **2 µs**, corrigindo a restrição de tempo da configuração anterior de 0,5 µs. O solver TyphoonSim permanece **DAE/BDF, passo máximo 2 µs e tolerâncias absoluta/relativa de 0,001**.

## Painéis

| Scope1 | Sinais |
|---|---|
| 1 | D: referência ideal, saída física, média e extremos observados |
| 2 | CI: referência ideal, saída física, média e extremos observados |
| 3 | P: referência ideal, saída física, média e extremos observados |
| 4 | Temperaturas do motor e do sensor, em °C |
| 5 | Ruído 1/f das três cadeias, em V |
| 6 | Rotação `n`, em rpm |

**Scope_motor** apresenta rotação, torque, correntes de fase, comando, duty cycle e sinais Hall. Para conferir somente a partida, use uma cópia com 0,2 s ou 1 s e gravação de 0,1 ms; depois restaure 60 s e gravação de 10 ms. **V_out gravado a cada 10 ms não resolve a comutação**: use V_media na comparação térmica. Para observar PWM e picos, faça um ensaio separado e curto com gravação de 1 µs.

## Protocolos

| Ensaio | Temperatura do motor | Temperatura inicial do sensor |
|---|---|---|
| D - degrau | 0 → 130 °C em 15 s | 0 °C |
| CI - resposta livre | 0 °C constante | 130 °C |
| P - pulso | 130 °C entre 15 e 20 s; 0 °C fora desse intervalo | 0 °C |

Cada cadeia inclui atraso térmico de primeira ordem (τ = 15 s), curva nominal R/T 8016, divisor, ruído 1/f de 100 µV RMS nominal estimado, cabo e blindagem. O mesmo motor e inversor alimentam os três ramos de interferência. A referência ideal usa a conversão β da Entrega 1.

A média e os extremos são calculados sobre amostras de tensão física a cada **1 µs**, em janelas de **10 ms**, com **10000 leituras por janela**. Como o circuito é resolvido em passos de 2 µs, leituras consecutivas podem repetir o mesmo valor; isso não altera a média nem os extremos. Esses observadores não acrescentam filtro nem realimentação à cadeia. Os extremos são os valores observados nessa amostragem e não garantem capturar todo pico entre amostras.

A duração de 60 s mantém os eventos em 15 e 20 s, sem acelerar artificialmente a dinâmica. O degrau tem 45 s de resposta (3τ), alcançando aproximadamente 95% da mudança térmica; a condição inicial decai por 4τ. O pulso de 5 s é mais breve que τ e deixa uma cauda após o retorno da entrada.

## Partida e verificação

Foi acrescentado à entrada de torque de carga um auxílio de **−1 mNm somente no primeiro 1 ms**. Depois, permanece a carga original. Esse impulso não impõe a velocidade do motor. No teste curto de 0,2 s, a validação passou, a execução terminou com sucesso, a rotação ficou próxima de 4000 rpm e os sinais Hall e correntes de fase comutaram.

As taxas explícitas de processamento são **1, 5, 25 e 50 µs**. Os estados térmicos e do ruído são atualizados a cada 10 ms dentro dos blocos de 50 µs. Foram removidos os pares duplicados de conexões à fase A dos ramos CI e P; permanece uma ligação comum ao motor.

## Origem dos gráficos

A execução nativa anterior de **180 s terminou com sucesso**. O CSV exportado contém **18001 amostras**, de 0 a 180 s, todos os sinais finitos e os três protocolos corretos. O motor partiu e permaneceu próximo de 4000 rpm.

O relatório usa as **6001 amostras do trecho de 0 a 60 s dessa execução**, preservando resultados reais e evitando repetir a execução longa. Nessa aquisição, o observador operava a cada **0,5 µs**, com 20000 amostras por janela de 10 ms. O arquivo entregue foi posteriormente ajustado para 60 s e observação a cada 1 µs. As médias são comparáveis na escala térmica; os extremos podem mudar com o intervalo de observação. A diferença está declarada na legenda do relatório.

Os CSVs, scripts e registros são arquivos internos de preparação e ficam fora do pacote de entrega.

A tentativa de usar 2 µs no observador falhou na compilação HIL: o controle de 5 µs não é múltiplo inteiro dessa taxa. Por isso, a versão final usa **1 µs** no observador (10000 amostras por janela), preservando o controle e o passo de hardware de 2 µs. A taxa do observador e o passo do solver são configurações distintas.

**Verificação final da versão ajustada:** uma cópia de 0,2 s, com circuito e código idênticos ao arquivo entregue e diferença somente no tempo de parada, compilou no HIL101 com **Timing constraints met** (core0: 57,27%) e concluiu a execução nativa no TyphoonSim com **Simulation completed successfully**. A versão de 60 s não foi novamente executada inteira; os gráficos usam o trecho de 60 s da execução anterior completa, como declarado acima.
