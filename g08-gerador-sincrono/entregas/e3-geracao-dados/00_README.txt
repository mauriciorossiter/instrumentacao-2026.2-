ECOM060 - Instrumentacao Eletronica (2026.2)
Grupo 08 - Sistema 7: Gerador Sincrono (Swing Equation)
Topico atribuido: LIMIAR

GERACAO DE DADOS BRUTOS (Secao 3.3) -- protocolo "Limiar" da Orientacao
recebida do professor ("Geracao de dados - Caracteristicas estaticas").

-------------------------------------------------------------------------
COMECAR POR: RELATORIO_geracao_dados_limiar.md

  Explica o protocolo aplicado (pequenos incrementos crescentes de x, a
  partir de um ponto de repouso constante), a metodologia de geracao
  (reuso da funcao de caracteristica estatica ja validada no relatorio
  principal, quantizacao de 12 bits + ruido do canal de delta), e como
  o dataset atende as duas exigencias obrigatorias da Orientacao (ruido
  incluido deliberadamente; nenhum pre-processamento).

O QUE ENTREGAR (se este pacote for repassado ao professor):

  dados/Equipe_08_Limiar.csv               <- dataset bruto
  dados/metadados_Equipe_08_Limiar.txt     <- metadados exigidos

O QUE NAO PRECISA SER REPASSADO (material de trabalho da equipe):

  gerar_dados_limiar.py    - contem os parametros internos da funcao
                             geradora (gabarito); a Orientacao diz que
                             nao e' necessario revela-los
  figs/                    - figura de apoio a este relatorio
  RELATORIO_geracao_dados_limiar.md
  Latex/                   - versao em LaTeX deste mesmo relatorio

-------------------------------------------------------------------------
REPRODUCAO

  python gerar_dados_limiar.py

  Requer NumPy, Pandas e Matplotlib. Semente fixa (20260903): dataset e
  figura reprodutiveis byte a byte.

-------------------------------------------------------------------------
VERSAO EM LATEX

  Latex/GeracaoDados_Limiar_v1.tex   documento principal (\input preambulo
                                     e corpo)
  Latex/preambulo.tex                mesmo preambulo do relatorio principal
                                     (../../Latex/), reaproveitado
  Latex/corpo.tex                    conteudo (mesmas secoes deste .md)
  Latex/referencias.tex              bibliografia desta nota
  Latex/figuras_relatorio.py         gera Latex/figs/*.pdf a partir do CSV
                                     ja entregue (nao gera dados novos)

  Compilar com pdflatex/latexmk (nao ha' motor LaTeX neste ambiente de
  trabalho, entao o PDF nao foi gerado aqui -- so' o codigo-fonte):

    cd Latex
    python figuras_relatorio.py
    pdflatex GeracaoDados_Limiar_v1.tex
    pdflatex GeracaoDados_Limiar_v1.tex   (2x, para acertar referencias)
