# Roteiro da apresentação: entrega final (G07, motor BLDC)

Feito para quem for apresentar sem ter participado: uma fala por slide, com o item da orientação ao lado. Números iguais aos do relatório.

| Slide | Item |
|---|---|
| 2 | mensagem |
| 3–4 | 1 · Sistema e equivalente |
| 5–6 | 2 · Sensor e localização |
| 7 | 3 · Características |
| 8 | 4 · Malha aberta |
| 9 | 5 · Controle ideal |
| 10–11 | 6 · Controle real |
| 12 | 7 · Ruptura |
| 13–14 | 8 · Compensação |
| 15 | 9 · Síntese |

**Slide 1, capa.** "Vamos mostrar que um controle que funciona com medição ideal piora, e pode falhar, quando a medição é real."

**Slide 2, mensagem.** "O mesmo controlador de corrente deixa o motor 23 mA abaixo da referência quando passa a usar o sensor real. Bastam 1,4 mV de zero ou 15 mV de ruído para ele sair do critério. Com as compensações, o erro cai para 11 mA."

**Slide 3, item 1.** "O sistema é um motor BLDC de 36 V acionando um ventilador, com inversor e sensores Hall de posição. No equivalente, a parte elétrica é a mesma, e a mecânica vira circuito: torque vira tensão (100 V por N·m), velocidade vira corrente (1 A = 1000 rpm), a inércia vira um indutor e o atrito um resistor. A equação é a mesma nos dois domínios."

**Slide 4, item 1.** "Este é o circuito no TyphoonSim: em cima, uma fase do motor com resistência, indutância e força contraeletromotriz; embaixo, a malha mecânica com o indutor da inércia, o resistor do atrito e as fontes de torque."

**Slide 5, item 2.** "Esta é a Figura 1 da orientação com os nossos blocos. Um amperímetro ideal em cada fase dá a corrente verdadeira. Ela segue pelo caminho ideal ou pela cadeia real: sensor, condicionamento e processamento. O seletor, no SCADA, escolhe qual chega ao PI."

**Slide 6, item 2.** "Medimos a corrente de fase, que produz o torque. Usamos o Hall ACS712-20A, mais simples que o shunt: é isolado e já sai em tensão. Ele mede as fases a e b, em série com o enrolamento; a escala é 1:1, porque a parte elétrica não foi transformada. O carregamento é de 1,2 mΩ contra 1,6 Ω, menos de 0,04 %, por isso foi desprezado. A cadeia atende a todos os requisitos da tabela."

**Slide 7, item 3.** "Estas são as características modeladas. Estáticas: zero e sensibilidade. Dinâmica: a resposta de 80 kHz do sensor. Espúrias: temperatura e ruído. Do circuito auxiliar: filtro RC e ADC. Do processamento: a média e o módulo. Cada uma tem um bloco e uma caixa no SCADA."

**Slide 8, item 4.** "Em malha aberta, cada bloco calcula a leitura só com a sua característica. O zero é a única que desloca a média: 75,5 mA. Com a correção calculada, cai para 1,2 mA. A cadeia completa tem 58 mA de erro rms e 60 µs de atraso, dentro da demanda."

**Slide 9, item 5.** "Fechamos a malha de corrente com um PI que cancela o polo elétrico. Com a medição ideal, acomoda em 1,4 ms, com 5 % de sobressinal e 9 mA de erro. Todos os critérios passam."

**Slide 10, item 6.** "Mudando só o seletor, a medida continua em 1,500 A, mas a corrente verdadeira fica em 1,478 A, e a acomodação passa de 1,4 para 4,8 ms: o controle que passava com a medição ideal falha com a real."

**Slide 11, item 6.** "O erro de 23 mA vem do ruído retificado: na fase sem corrente, o módulo do ruído tem média positiva, cerca de 14 mA, mais 5 mA da amostragem do ADC; a medida fica alta e o PI reduz a corrente real. O mesmo viés faz a acomodação falhar. O sobressinal, de 5 para 6 %, e a queda maior vêm do atraso de 60 µs. Zero e ganho não aparecem porque a correção calculada os remove."

**Slide 12, item 7.** "Varremos cada característica em 4 níveis, com previsões feitas antes. O erro falha com 1,4 mV de zero (previsto 1,2), 15 mV de ruído (previsto 19) e filtro RC abaixo de 0,95 kHz (previsto 1,2). O zero tolerável é menor que a deriva térmica do próprio sensor."

**Slide 13, item 8.** "Duas das três rupturas nascem fora do sensor. Para o ruído retificado, insensibilidade inerente: em vez do módulo, usamos a fase em condução indicada pelos sensores Hall de posição, e o processamento deixa de transformar ruído em viés. Para o zero, autocalibração na partida. Para o filtro RC, uma correção calculada pela atenuação na frequência elétrica. O erro na planta caiu de 23 para 11 mA, o limite do ruído subiu de 15 para 78 mV e o do zero de 1,4 para 97 mV."

**Slide 14, item 8.** "As previsões foram registradas antes. A do ruído se confirmou: sem viés, o limite passa a ser o sobressinal, em 17 mV contra 19 previstos. A do filtro RC errou: a correção piorou o resultado em 1 kHz, porque a medida pela posição lê cada fase depois que o filtro já assentou, então não havia atenuação a corrigir. Por isso, para o filtro, a exigência é de projeto: f_c de pelo menos 1,2 kHz."

**Slide 15, item 9.** "O sensor precisa de zero calibrado no sistema e ruído abaixo de 15 a 17 mV. O condicionamento precisa de um filtro acima de 1,2 kHz. O processamento precisa de correção calculada, média por período, autocalibração e da fase escolhida pela posição. Em malha fechada, o instrumento pesa pelo viés, não pela velocidade."
