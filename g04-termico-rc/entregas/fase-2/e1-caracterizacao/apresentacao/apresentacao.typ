#let primary = rgb("#163e69")
#let accent = rgb("#c84c35")
#let green = rgb("#237647")
#let bg = rgb("#f8f9fa")

#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: bg)
#set text(font: "Carlito", size: 20pt)
#set par(justify: true, leading: 0.62em)

#let dc(n) = text(str(n).replace(".", ","))

#let header(title) = block(
  width: 100%,
  height: 2.4cm,
  fill: primary,
  inset: (x: 1.5cm, y: 0.5cm),
  align(horizon)[
    #text(fill: white, size: 26pt, weight: "bold", title)
    #h(1fr)
    #text(fill: white, size: 13pt, "G04 • Fase 2 / Entrega 01")
  ],
)

#let footer(n) = place(
  bottom + left,
  dy: -0.55cm,
  block(width: 100%, inset: (x: 1.5cm))[
    #line(length: 100%, stroke: 0.6pt + primary)
    #v(0.15cm)
    #text(size: 11pt, fill: primary)[Caracterização da Planta #h(1fr) #n / 8]
  ],
)

#let slide(title, number, body) = page[
  #header(title)
  #block(inset: (x: 1.5cm, y: 0.9cm), width: 100%, height: 15.2cm)[
    #body
  ]
  #footer(number)
]

#slide("Planta térmica RC do IGBT IKD04N60RF", 1)[
  #align(center)[
    #text(size: 17pt, accent, weight: "bold")[Caracterização no domínio térmico — Equipe G04]
    #v(0.7cm)
  ]
  #grid(
    columns: (1.1fr, 1fr),
    gutter: 1.6cm,
    align(horizon)[
      - *Representação:* aquecimento da junção de um semicondutor.
      - *Entrada:* potência dissipada $P$ [W].
      - *Saída:* temperatura da junção $T_j$ [K].
      - *Referência:* cápsula fixa a $T_c =$ #dc("298.15") K (25 °C).
      - *Objetivo:* prever o quanto e quão rápido a junção aquece, antes de instrumentar o sistema.
      - *Modelo base:* quatro ramos Foster publicados pelo fabricante (Fig. 21 do datasheet).
    ],
    align(center + horizon)[
      #image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-01-impedancias-reducao.png", width: 95%)
      #text(size: 11pt, fill: gray)[Impedância térmica: 4 ramos vs. redução de 2 ramos]
    ]
  )
]

#slide("Modelo Foster de quatro ramos", 2)[
  #align(center)[
    $C_i (d theta_i)/(d t) = P - theta_i / R_i$ \
    $T_j = T_c + sum_i theta_i$
  ]
  #v(0.4cm)
  #grid(
    columns: (1.2fr, 1fr),
    gutter: 1.4cm,
    [
      - Os quatro ramos RC são *modos de ajuste* do modelo Foster; não representam camadas físicas identificadas do IGBT.
      - Resistências $R_i$ e constantes de tempo $tau_i$ vêm da Fig. 21 do datasheet Infineon IKD04N60RF.
      - Capacidades térmicas são derivadas: $C_i = tau_i / R_i$.
      - Sistema LTI de 4ª ordem, com polos reais negativos: sem oscilação nem sobressinal.
    ],
    align(center + horizon)[
      #table(
        columns: (1fr, 1fr, 1fr),
        inset: 7pt,
        stroke: 0.5pt + primary,
        align: center,
        table.header[*Ramo*][*$R_i$ [K/W]*][*$tau_i$ [s]*],
        [1], [#dc("0.492466")], [#dc("0.00020")],
        [2], [#dc("0.884411")], [#dc("0.00054")],
        [3], [#dc("0.589157")], [#dc("0.00210")],
        [4], [#dc("0.073673")], [#dc("0.03166")],
      )
      #v(0.3cm)
      #text(size: 11pt, fill: gray)[Fonte: Infineon IKD04N60RF, datasheet v2.6]
    ]
  )
]

#slide("Validação: RK4 concorda com a solução fechada", 3)[
  #grid(
    columns: (1fr, 1.1fr),
    gutter: 1.2cm,
    [
      - *Ganho estático:* $sum R_i =$ #dc("2.039707") K/W.
      - *Equilíbrio (10 W):* $T_j =$ #dc("318.547") K ($approx$ #dc("45.4") °C acima da cápsula).
      - *Polos:* #text[-5000; −1851,85; −476,19; −31,59] s⁻¹.
      - *Sobressinal:* 0 %.
      - *Integração:* RK4 explícito, $h = 2$ µs, registro a 10 µs.
      - *Erro máximo:* $< 3 times 10^(-4)$ K em relação à solução analítica.
      #v(0.3cm)
      #text(size: 11pt, fill: gray)[A concordância verifica a implementação matemática, não um componente real.]
    ],
    align(center + horizon)[
      #image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-05-validacao-typhoon.png", width: 100%)
    ]
  )
]

#slide("Três ensaios caracterizam a dinâmica", 4)[
  #align(center)[
    #grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 0.5cm,
      image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-02-degrau.png", width: 100%),
      image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-03-livre.png", width: 100%),
      image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-04-pulso.png", width: 100%),
    )
  ]
  #v(0.25cm)
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 0.6cm,
    align(center)[
      *Degrau* #linebreak() 0 → 10 W em 2 ms #linebreak()
      #text(size: 11pt)[subida, ganho e acomodação]
    ],
    align(center)[
      *Livre* #linebreak() P = 0; IC não nula #linebreak()
      #text(size: 11pt)[decaimento dos estados e polos]
    ],
    align(center)[
      *Pulso* #linebreak() 10 W de 2 a 12 ms #linebreak()
      #text(size: 11pt)[aquecimento e resfriamento]
    ],
  )
]

#slide("Aumentar R₁ eleva o ganho e muda a acomodação", 5)[
  #grid(
    columns: (1fr, 1.1fr),
    gutter: 1.2cm,
    [
      - Com C₁ fixo, aumentar R₁ eleva o ganho DC e a constante de tempo τ₁.
      - *Fatores testados:* 0,2×; 1×; 5× o valor nominal.
      - *Ganho:* #dc("2.040") → #dc("4.010") K/W.
      - *Acomodação a 2 %:* #dc("18.773") → #dc("7.157") ms.
      - Aparentemente mais rápida porque a banda de 2 % cresce com o valor final.
      #v(0.3cm)
      #text(size: 11pt, fill: gray)[Não há oscilação nem instabilidade para R₁ > 0.]
    ],
    align(center + horizon)[
      #image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-061-sensibilidade-r1.png", width: 100%)
    ]
  )
]

#slide("C₁ altera o transitório, mas não o ganho", 6)[
  #grid(
    columns: (1fr, 1.1fr),
    gutter: 1.2cm,
    [
      - Com R₁ fixo, variar C₁ muda a taxa inicial de aquecimento e o polo do ramo 1.
      - *Ganho estático:* permanece #dc("2.039707") K/W.
      - *Temperatura final:* inalterada (o equilíbrio depende só das resistências).
      - *Acomodação a 2 %:* $approx$ #dc("18.773") ms — a cauda do ramo 4 ainda domina.
      #v(0.3cm)
      #text(size: 11pt, fill: gray)[A mudança aparece na curva; a métrica percentual não a destaca sozinha.]
    ],
    align(center + horizon)[
      #image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-062-sensibilidade-c1.png", width: 100%)
    ]
  )
]

#slide("R₄ governa a cauda lenta", 7)[
  #grid(
    columns: (1fr, 1.1fr),
    gutter: 1.2cm,
    [
      - O ramo 4 tem a menor resistência, mas a maior constante de tempo.
      - Aumentar R₄ eleva o ganho e alonga a cauda da resposta.
      - *Constante de tempo:* τ₄: #dc("31.658") → #dc("158.29") ms.
      - *Acomodação a 2 %:* $approx$ #dc("326.962") ms (janela estendida a > 1 s).
      #v(0.3cm)
      - *Síntese:* $R$ altera ganho e velocidade; $C$ altera apenas velocidade.
      - *Extrapolação:* 100 W → 228,97 °C, acima do limite de 175 °C do componente.
    ],
    align(center + horizon)[
      #image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-063-sensibilidade-r4.png", width: 100%)
    ]
  )
]

#slide("Limites do modelo e respostas às perguntas", 8)[
  #grid(
    columns: (1.2fr, 1fr),
    gutter: 1.2cm,
    [
      - *Hipóteses:* cápsula a $T_c =$ #dc("298.15") K; faixa nominal 0–10 W.
      - *O que não está no modelo:* aquecimento da cápsula, dissipador e realimentação eletrotérmica.
      - *Redução anterior:* 2 estados aproximam os 4 ramos com erro máx. de 2,679 % em $Z_"th"$.
      - *Extrapolação 100 W:* resultado numérico de 228,97 °C; não é recomendação de ensaio físico.
      #v(0.3cm)
      #text(size: 11pt, fill: gray)[Fontes: Infineon IKD04N60RF datasheet v2.6 e Infineon AN2015-10.]
    ],
    align(center + horizon)[
      #image("/g04-termico-rc/entregas/fase-2/e1-caracterizacao/relatorio/figuras/fig-01-impedancias-reducao.png", width: 95%)
    ]
  )
]
