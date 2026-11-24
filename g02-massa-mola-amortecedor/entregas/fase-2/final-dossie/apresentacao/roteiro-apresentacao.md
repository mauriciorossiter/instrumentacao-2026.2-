# Roteiro da apresentação — Entrega Final (20 min)

G02 · massa-mola-amortecedor · slides em `apresentacao-final.pdf` (27 páginas) ·
demonstração com `../pacote/e4/modelo.tse` + `painel.cus`

Slides de seção (fundo branco, título grande: 4, 6, 9, 11, 13, 15, 18, 20, 23) são só transição: passar direto,
anunciando o tema enquanto troca.

## Antes de começar (checklist)

- [ ] `apresentacao-final.pdf` aberto em tela cheia (testar que a barra de progresso aparece embaixo).
- [ ] `modelo.tse` compilado e carregado no VHIL; `painel.cus` aberto; simulação rodando.
- [ ] Testar uma vez cada botão de cenário (1 a 4) e o campo `fc_Hz`.
- [ ] Gráfico 1 do painel com janela de 8 s; tela do SCADA ao lado dos slides (ou alternar com Alt+Tab).
- [ ] Cronômetro visível. Ensaiar: o total previsto é de 19 min.

## Falas e demonstrações

| Tempo | Slide | Quem | O que dizer / fazer |
|---|---|---|---|
| 0:00 | 1–2 | Caio | Capa. No slide 2 (destaque azul), a pergunta: um controle que funciona com medição ideal continua funcionando com o nosso sensor real? Spoiler: não. |
| 0:40 | 3 | Caio | Roteiro. Tudo vai ser mostrado ao vivo: o seletor troca a leitura que chega ao **mesmo** controlador. |
| 1:10 | 4–5 | Pedro | Sistema e RLC. Destacar v_C = kx: tensão = força na mola = deslocamento em cm. |
| 2:00 | 6–8 | Pedro | Slide 7: Figura 1 preenchida (apontar os nomes dos blocos). Slide 8: por que o piezo (rígido, sem carregamento, mas não mede força estática → chopagem + lock-in). G passou de 25 para 5 por causa da faixa de 20 N. |
| 4:00 | 9–10 | Thiago | As características: estática (S de −38 a +71 %), dinâmicas (passa-alta do piezo e Butterworth do lock-in), espúrias. Duas nascem no condicionamento. |
| 6:00 | 11–12 | Thiago | Malha aberta, cada uma isolada. O lock-in só atrasa; S dá erro de ganho; a chopagem resolve o resto. "Parece utilizável". |
| 8:00 | 13–14 | Caio | **DEMO 1:** botão **1) Instrumento IDEAL**. Ler no painel: acomoda em ≈ 0,45 s, sobressinal de 2,4 %. Mostrar a tabela de critérios. |
| 10:00 | 15–16 | Caio | **DEMO 2:** botão **2) Instrumento REAL**. Apontar `x_real` oscilando e `y_med` "quase certo": o controlador corrige uma leitura atrasada. |
| 11:30 | 17 | Pedro | Tabela de decomposição: tirar o ruído não muda nada; tirar o erro de S **piora** (paradoxo: o ganho baixo mascarava o atraso); trocar fc para 10 Hz estabiliza. |
| 13:00 | 18–19 | Thiago | Previsões registradas antes de simular (mostrar o JSON com a data). **DEMO 3:** seletor real, características desligadas; **dizer a previsão em voz alta** e digitar `fc_Hz` = 5 (oscila), 7 (no limite) e 10 (atende). |
| 16:00 | 20–21 | Pedro | Compensação por correções calculadas: calibração + inversa do filtro. **DEMO 4:** botão **3)** (só calibração: instável) e **4)** (atende). |
| 17:30 | 22 | Pedro | Ganho sobre o item 7 e custo. **DEMO 5 (se der tempo):** no cenário 4, `fc_Hz` = 0,9 → volta a oscilar (a correção depende do modelo do filtro). |
| 18:30 | 23–25 | Thiago | Slide 24: síntese, o que exigir de sensor, condicionamento e processamento. Slide 25 (destaque azul): a lição, aprovado em malha aberta ≠ aprovado em malha fechada. Deixar a frase na tela um instante. |
| 19:20 | 26–27 | Caio | Reprodução: tudo no GitHub (`pacote/README.md`). Slide 27: perguntas. |

## Perguntas prováveis (respostas curtas)

- **"Por que não usar só um filtro mais rápido?"** Funciona: fc entre 7 e 15 Hz atende (slide 19). A correção
  calculada é a saída quando o hardware não pode mudar, e o resultado é equivalente a uma banda de 10 Hz.
- **"Como se chopa uma força?"** No modelo, a portadora multiplica a força antes do sensor (como na Fase 1). Numa
  bancada, o equivalente é excitar o sensor com a portadora (ponte excitada em AC) ou modular mecanicamente.
- **"De onde vêm os valores?"** d33 e Ct dos catálogos APC e Murata; offset do TL072; deriva, 60 Hz, limiar e
  resolução são estimativas declaradas (slide 10).
- **"As curvas vieram do TyphoonSim?"** As figuras vêm do gêmeo numérico, que executa o mesmo código C dos blocos
  (conferido com gcc: 0,02 cm de diferença, slide 26). A demonstração é no VHIL.
- **"Por que tirar o erro de S piora?"** O ganho de malha cai para 0,615; com menos ganho, o atraso do filtro
  desestabiliza menos. Calibrar devolve o ganho e expõe o problema dinâmico (slide 17).
