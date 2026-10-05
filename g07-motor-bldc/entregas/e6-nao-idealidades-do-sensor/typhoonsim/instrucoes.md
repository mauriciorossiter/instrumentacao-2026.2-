# G07 - Fase 1, Entrega 02

## Arquivos

| Arquivo | Finalidade |
|---|---|
| `relatorio.pdf` | Relatório de 3 páginas, com as seções R6-R10. |
| `modelo_camadas.tse` | Ensaios lentos: curva estática, resposta térmica e ruído 1/f. |
| `modelo_motor.tse` | Ensaio com motor BLDC, comutação e blindagem, com as três camadas em série. |
| `instrucoes.md` | Orientações para executar e visualizar os ensaios. |

As funções C estão incorporadas aos modelos. Não é necessário importar arquivos `.c`, imagens ou dados externos.

## Preparação

1. Abra o `.tse` no Typhoon HIL Control Center/TyphoonSim 2026.3.
2. Use **TyphoonSim Perspective** e inicie pelo **Start Simulation do TyphoonSim**.
3. Ao terminar, abra `Scope1` e selecione os sinais indicados abaixo. Coloque sinais com a mesma unidade no mesmo painel.

## Modelo de camadas - 180 s

Em **Model Initialization**, altere somente `g07_ensaio` para selecionar o ensaio. Execute novamente após cada mudança. Mantenha `g07_dt = 0.01` s e o tempo de simulação em 180 s.

| `g07_ensaio` | Ensaio | Sinais para comparar |
|---|---|---|
| `1` | Varredura estática de 0 a 130 °C e retorno | `G07_vT_ideal`, `G07_V_estatica` e `G07_V_reta`. |
| `0` | Degraus térmicos em 15 s e 105 s | Painel 1: `G07_T_motor` e `G07_T_sensor`. Painel 2: `G07_vT_ideal`, `G07_V_dinamica` e `G07_V_serie`. |
| `2` | Temperatura constante para observar ruído 1/f | Painel 1: `G07_ruido_1f`. Painel 2: `G07_vT_ideal` e `G07_V_espectral`. |

### Como visualizar

- **Estática:** a referência ideal da Entrega 01 já usa o modelo beta do NTC e é curva. A reta verde é a referência linear. A curva nominal e a referência beta devem ficar próximas.
- **Térmica:** mantenha as temperaturas em °C separadas das tensões em V. O atraso é exponencial; o valor esperado de `G07_T_sensor` em 30 s é aproximadamente 82,2 °C.
- **Ruído:** use autoescala vertical no painel de `G07_ruido_1f`. No painel com ideal/espectral, amplie ao redor de aproximadamente 0,1035 V; uma faixa inicial de 0,1030 a 0,1040 V pode ajudar. O ruído tem amplitude pequena e some visualmente na escala geral.

`G07_V_serie` reúne a curva nominal, o atraso e o ruído 1/f antes do cabo. Acrescentá-lo ao ensaio 0 permite mostrar as três camadas juntas, embora o ruído continue pequeno na escala geral.

O modelo lento mantém a fonte de comutação em zero para separar os fenômenos. Para observar a comutação, use o modelo com motor. O limiar de proteção inicial é 1 ms; como o modelo lento atualiza a cada 10 ms, a primeira amostra do sinal aplicado à fonte permanece em zero durante 0-10 ms. No modelo com motor, a proteção dura 200 passos de 5 µs, ou 1 ms.

## Modelo com motor - 0,2 s

Execute `modelo_motor_entrega_2.tse` com os parâmetros atuais. O ensaio começa com sensor em equilíbrio a 65 °C; a entrada térmica aplica um **degrau de 65 para 130 °C em t = 50 ms**. Como a constante térmica é 15 s, a temperatura do sensor varia pouco em 0,2 s, mas a tensão útil apresenta uma pequena deriva.

No Scope:

1. Compare `G07_V_ref` (sem blindagem) e `G07_V_out` (com blindagem). Ambos recebem o mesmo sinal degradado.
2. Acrescente `G07_vT_ideal` e `G07_V_serie` para identificar, respectivamente, a referência instantânea e o sinal com as três camadas antes do acoplamento.
3. Guarde a janela ampla e amplie alguns períodos do PWM, começando por **0,1000-0,1005 s**. Para ver uma borda individual, estreite mais a janela e confira a resolução temporal disponível.
4. Para comparar a camada espectral isolada contra a referência, selecione `G07_vT_ideal` e `G07_V_espectral`. Neste modelo, o ramo espectral usa a curva beta sem atraso, acrescenta ruído 1/f e recebe o mesmo acoplamento da fase A, sem blindagem.
5. Inclua `n` em um painel separado, com unidade rpm, para verificar a partida e a rotação do motor. O alvo é próximo de 4000 rpm; confirme o valor registrado antes de tratá-lo como resultado.

### Picos e preservação do valor útil

O solver conserva o passo máximo de 2 µs da Entrega 1. O transitório estimado do ramo sem blindagem tem constante `(Rth + Rc) Cc ≈ 0,151 µs`, menor que esse passo. Picos exibidos no Scope podem depender da resolução do solver, do registro e da decimação do gráfico. **Zoom não recupera amostras não registradas**. Exporte os resultados com a maior resolução temporal disponível; não altere motor, controle, circuito ou solver para forçar concordância com um pico esperado.

Os 33,6 V sem blindagem e 1,71 V de excursão blindada da Entrega 1 são estimativas para uma borda ideal de 36 V. Não os apresente como picos medidos na nova simulação. Se o CSV continuar mostrando valores menores, registre a discrepância e deixe a causa como hipótese, sem afirmar que o pico foi completamente resolvido.

Para avaliar a leitura útil, compare **a média de `G07_V_out` com a média de `G07_V_serie` na mesma janela**, excluindo a proteção de partida. A janela 0,010-0,040 s antecede o degrau térmico e tem referência próxima de 1,0343 V. Uma janela posterior, como 0,100-0,200 s, já contém pequena deriva; não use 1,0343 V como valor fixo esperado. Se os tempos do CSV forem irregulares, calcule a média ponderada no tempo (integral dividida pela duração da janela).

O equivalente de Thévenin é mantido fixo em 1409 Ω, pior caso da referência beta a 0 °C. A 65 °C seria cerca de 862 Ω com a curva nominal, ou 857 Ω com beta. Essa simplificação conserva a comparação com a Entrega 1; não significa que a resistência real do divisor seja constante.

## Registro e interpretação

Salve capturas com legenda e eixos visíveis: tempo em s, temperatura em °C ou tensão em V. Se converter tensões para µV, multiplique os valores em V por 10^6; mudar apenas a legenda não converte os dados.

O foco do trabalho é **ruído 1/f + comutação**: a blindagem reduz a interferência rápida acoplada pelo cabo, enquanto a flutuação lenta gerada no sensor permanece. As camadas estática e dinâmica são os requisitos de apoio.

O gráfico temporal do ruído não comprova sozinho uma lei 1/f. O relatório compara a PSD estimada do CSV pelo método de Welch com a PSD teórica do gerador. Os 100 µV RMS nominais são uma estimativa didática declarada. O ensaio de 0,2 s não caracteriza a banda de ruído de 0,01-1 Hz; por isso são usados dois modelos com escalas de tempo distintas.

A ampliação do CSV do motor mostra a redução das excursões registradas com blindagem. Essa comparação não garante a resolução dos picos contínuos nem caracteriza uma resposta em frequência do circuito.

## Verificação dos CSVs fornecidos

O relatório foi atualizado com `curva_estatica.csv`, `resposta_termica.csv` e `ruido.csv`, exportados do TyphoonSim. Cada arquivo contém 18001 amostras em 180 s, com intervalo de 10 ms.

- **Estática:** não linearidade de 9,08% do alcance e diferença máxima de 8,63 mV entre a curva nominal e a referência beta.
- **Térmica:** ajuste exponencial com constante de tempo de aproximadamente 15 s; temperatura registrada de 82,14 °C em 30 s. Temperatura e tensão aparecem em painéis separados no relatório.
- **Ruído:** no intervalo 0,1-180 s, RMS em relação a zero de 105,4 µV, desvio padrão de 99,1 µV e amplitude de 0,781 mV pico a pico. A PSD foi estimada pelo método de Welch, além da curva teórica; o registro finito não confirma com precisão o limite inferior de 0,01 Hz.

O CSV térmico fornecido não contém `G07_V_serie`. Para registrar diretamente as três camadas juntas, inclua esse sinal em uma nova exportação do ensaio 0.

O arquivo `modelo_motor.csv` contém 413379 amostras de `G07_V_ref` e `G07_V_out`, de 0 a aproximadamente 0,2 s. Os tempos são irregulares, com intervalo típico de 0,5 µs e máximo de 1 µs. A Figura 5 foi refeita com esse CSV, preservando os extremos na vista ampla e mostrando uma ampliação de cinco períodos do PWM.

- **Média antes do degrau (0,010-0,040 s):** `G07_V_out` = 1,03444 V, ponderada no tempo; a referência nominal calculada a 65 °C é 1,03434 V. A diferença de aproximadamente 0,103 mV reúne os efeitos presentes no registro, sem atribuição isolada a uma camada.
- **Média após o degrau (0,100-0,200 s):** `G07_V_out` = 1,04315 V, ponderada no tempo. A variação é coerente com a pequena deriva térmica; a referência inicial não deve ser usada como valor esperado fixo nessa janela.
- **Extremos em 0,100-0,200 s:** sem blindagem, -1,372 a 3,704 V; com blindagem, 0,918 a 1,180 V. Os extremos durante a partida são diferentes e estão incluídos na vista ampla.
- **Ampliação em 0,1000-0,1005 s:** 5,068 V pico a pico sem blindagem e 0,254 V com blindagem, cerca de 20 vezes de redução da excursão registrada. Isso não é uma medida de atenuação senoidal nem uma garantia dos picos contínuos.

O CSV confirma picos inferiores aos relatados na Entrega 1. Como a diferença está nos dados exportados, não pode ser atribuída apenas à decimação visual do Scope. A resolução do solver/registro permanece uma hipótese: o intervalo típico de 0,5 µs é maior que a constante estimada de 0,151 µs. Não se altera o circuito ou o solver conservados da Entrega 1 para forçar concordância.

O arquivo não inclui `G07_V_serie`, `G07_vT_ideal` ou `n`. Portanto, o relatório não afirma ter medido a rotação nem comparado diretamente a média da saída com o sinal antes do cabo. Para complementar essas verificações, inclua os três sinais em uma nova exportação, com a maior resolução temporal disponível.
