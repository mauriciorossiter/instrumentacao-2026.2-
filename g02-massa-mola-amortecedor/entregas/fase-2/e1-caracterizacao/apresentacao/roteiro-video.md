# Roteiro do vídeo — Fase 2, Entrega 01 (apresentação convertida em vídeo)

Formato da orientação: 10 min (7 de exposição + 3 de perguntas). Como é vídeo, a parte de perguntas vira as
"perguntas e se...?" respondidas com previsão e resultado. Gravação de tela com os slides
(`apresentacao/apresentacao.pdf`) e, no R5, o script rodando. **Todos os integrantes participam.**

| Tempo | Quem | Slide | Fala |
|---|---|---|---|
| 0:00–0:20 | Caio | 1 | Grupo, sistema, objetivo: caracterizar a planta antes de instrumentar. |
| 0:20–2:20 | Pedro | 2 | **Modelo e hipóteses (2 min):** diagrama físico, 2ª lei de Newton, estados (x, ẋ) e por que são dois, parâmetros com a fonte de cada um (c ajustado para ζ = 0,3), classificação, hipóteses e domínio de validade (\|x\| ≤ 0,2 m), verificação dimensional. |
| 2:20–4:20 | Thiago | 3 | **Análise algébrica × simulação (2 min):** G(s), polos, ωn, ζ, sobressinal de 37,2 %, Tp de 0,329 s. Os três ensaios com a analítica sobreposta (erro de 1e-14 m). Tabela R4: tudo bate, exceto ts, porque 4/ζωn é o envelope; o valor exato é 1,123 s. |
| 4:20–7:00 | Caio | 4 | **"E se...?" (3 min):** para cada pergunta, dizer a previsão **antes** de mostrar a curva. m×8 → sobressinal de 72 % previsto, 71,5 % obtido; c = 0 → oscilação permanente de 0 a 20 cm; k×8 → 1,25 cm e 3× mais rápido; k/4 → 40 cm, fora da validade. Explicar pelos polos. |
| 7:00–8:00 | Pedro | 5 | **Síntese:** qual parâmetro manda em quê (ganho: k; velocidade: k e m; oscilação: c). |
| 8:00–10:00 | Thiago e Caio | 5 | Perguntas que esperamos ouvir, respondidas em diálogo: "por que c foi ajustado e não medido?" (sem datasheet; numa bancada sairia do decremento logarítmico); "por que não há linearização?" (o modelo já é linear). |

Depois: subir o vídeo, colar o link em `apresentacao/link-video.md` e responder no mural do Classroom (post de 03/11
em que o professor pediu os links).
