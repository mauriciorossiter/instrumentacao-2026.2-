# Tanques acoplados — Grupo 01

**Domínio de origem:** hidráulico
**Ordem:** 2ª
**Linearidade:** não linear (√h)
**Entrada e saída:** SISO (vazão de entrada e nível do segundo tanque); SIMO ao observar os dois níveis
**Solução algébrica de referência:** regime permanente + balanço integral

A planta tem dois reservatórios em série. A vazão de entrada alimenta o primeiro
tanque, cuja descarga alimenta o segundo; ambos escoam por gravidade segundo a lei
de Torricelli.

## Equipe

| Nome completo | Matrícula |
|---|---|
| Pablo Munih Silva de Carvalho | 22210730 |
| Pedro Henrique Balbino Rocha | 22210705 |
| Rafael José Amaral Saleme | 21111340 |
| Raniel Ferreira Athayde | 22210703 |

## Entregas

| Entrega | Relatório submetido | TyphoonSim | Devolutiva |
|---|---|---|---|
| e1-caracterizacao | [relatorio.pdf](entregas/e1-caracterizacao/relatorio/relatorio.pdf) | [Instruções](entregas/e1-caracterizacao/typhoonsim/instrucoes.md); modelo pendente | — |
| e2-sensibilidade | [relatorio.pdf](entregas/e2-sensibilidade/relatorio/relatorio.pdf) | [Instruções](entregas/e2-sensibilidade/typhoonsim/instrucoes.md); modelo pendente | — |
| e3-correcoes-calculadas | Versão submetida não disponível nesta pasta | Modelo não disponível nesta pasta | [e3-correcoes-calculadas.pdf](devolutiva/e3-correcoes-calculadas.pdf) |
| e4-serie-fourier | [relatorio.pdf](entregas/e4-serie-fourier/relatorio/relatorio.pdf) | [modelo.tse](entregas/e4-serie-fourier/typhoonsim/modelo.tse) e [instruções](entregas/e4-serie-fourier/typhoonsim/instrucoes.md) | — |
| e5-cadeia-ideal | [relatorio.pdf](entregas/e5-cadeia-ideal/relatorio/relatorio.pdf) | [modelo.tse](entregas/e5-cadeia-ideal/typhoonsim/modelo.tse) e [instruções](entregas/e5-cadeia-ideal/typhoonsim/instrucoes.md) | — |
| e6-dinamica-modulacao-am | [relatorio.pdf](entregas/e6-dinamica-modulacao-am/relatorio/relatorio.pdf) | [modelo.tse](entregas/e6-dinamica-modulacao-am/typhoonsim/modelo.tse) e [instruções](entregas/e6-dinamica-modulacao-am/typhoonsim/instrucoes.md) | — |

Na reorganização, a numeração adotada é caracterização (1), sensibilidade (2),
correções calculadas (3), série de Fourier (4), projeto da cadeia ideal (5) e
dinâmica, modulação AM e condicionamento (6).
O PDF de correções calculadas é
armazenado como devolutiva, conforme a orientação recebida.

Os PDFs e os modelos foram apenas movidos e renomeados, preservando seu conteúdo.
Os modelos de caracterização e sensibilidade precisam ser adicionados como
`typhoonsim/modelo.tse` nas respectivas entregas. As instruções dessas duas etapas
registram os parâmetros dos relatórios e a ausência do arquivo de modelo.

## Fase 2

| Entrega | Relatório | Simulação | Apresentação | Estado |
|---|---|---|---|---|
| e1-caracterizacao | [relatorio.pdf](entregas/fase-2/e1-caracterizacao/relatorio/relatorio.pdf) e [figuras](entregas/fase-2/e1-caracterizacao/relatorio/figuras/) | [instrucoes.md](entregas/fase-2/e1-caracterizacao/simulacao/instrucoes.md), scripts, [resultados](entregas/fase-2/e1-caracterizacao/simulacao/resultados.md) e [CSVs](entregas/fase-2/e1-caracterizacao/simulacao/dados/) | [apresentacao.pdf](entregas/fase-2/e1-caracterizacao/apresentacao/apresentacao.pdf) e [gravação](entregas/fase-2/e1-caracterizacao/apresentacao/gravacao.mp4) | Organizada para submissão |

A Fase 2 usa a estrutura específica solicitada em `e1-caracterizacao-git.pdf`:

```text
entregas/fase-2/e1-caracterizacao/
  relatorio/relatorio.pdf
  relatorio/figuras/fig-01-diagrama-blocos.png
  simulacao/instrucoes.md
  simulacao/tanques.py
  simulacao/complementos.py
  simulacao/requirements.txt
  simulacao/resultados.md
  simulacao/dados/
  apresentacao/apresentacao.pdf
  apresentacao/gravacao.mp4
```

O relatório fornecido foi preservado. As instruções permitem reproduzir os
ensaios em Python, as figuras e os CSVs. A gravação é material complementar.
O título do PR desta etapa é
`g01 — Fase 2, Entrega 1: Caracterização da Planta`.

## Organização e próximos PRs

Cada entrega usa esta estrutura, com nomes em minúsculas, sem acentos ou espaços:

```text
entregas/eN-nome/
  relatorio/relatorio.pdf
  typhoonsim/modelo.tse
  typhoonsim/instrucoes.md
devolutiva/eN-nome.pdf
```

Scripts auxiliares e CSVs de ensaio, quando necessários, ficam dentro da pasta da
respectiva entrega. Compilações, executáveis, caches, backups e configurações de
editor ficam fora do versionamento; o `.gitignore` do grupo cobre esses arquivos.

Nas próximas entregas, abra um PR por entrega, da branch `g01-tanques-acoplados`
para `main`, com o título `g01 — Entrega N: Nome da Entrega`. Para uma devolutiva,
use `g01 — Devolutiva N: Nome da Entrega` e preserve o relatório submetido em
`entregas/`.

Para a entrega da cadeia ideal, use o título
`g01 — Entrega 5: Projeto da Cadeia Ideal`.

Para a entrega de dinâmica e AM, use o título
`g01 — Entrega 6: Dinâmica de primeira ordem, modulação AM e condicionamento`.
O [circuito equivalente](entregas/e6-dinamica-modulacao-am/relatorio/figuras/circuito-equivalente.png)
fica junto ao relatório, com uma versão SVG na mesma pasta de figuras.

## Observações

Sem solução fechada geral: o acoplamento 2×2 destrói a separabilidade. Valide por regime permanente ($q_i = k_1\sqrt{h_1} = k_2\sqrt{h_2}$) e conservação de massa.
