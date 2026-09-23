ECOM060 - Instrumentacao Eletronica (2026.2)
Grupo 08 - Sistema 7: Gerador Sincrono (Swing Equation)
Capitulo 5 - Subtema atribuido: 5.4.3 - Funcoes de densidade espectral de potencia

RELATORIO DE ANALISE ESPECTRAL DE RUIDO (Cap. 5) -- reaproveita o dataset de
ruido ja entregue no Capitulo 3 (Secao 3.3, caracteristica "Limiar"). Nao
gera nenhum dado novo no TyphoonSim, conforme exigencia 4 da Orientacao do
Capitulo 5.

-------------------------------------------------------------------------
COMECAR POR: DensidadeEspectral_Latex/Equipe_08_DensidadeEspectralPotencia.tex

  Documento principal (\input preambulo e corpo). Teoria (autocorrelacao,
  Wiener-Khinchin, periodograma, Welch, Blackman-Tukey, brancura),
  metodologia, resultados e discussao -- auto-suficiente, sem depender de
  nenhum outro relatorio alem do livro-texto (Aguirre).

DADO DE ENTRADA (nao duplicado aqui -- ja entregue no Capitulo 3):

  ../e3-geracao-dados/dados/Equipe_08_Limiar.csv
  ../e3-geracao-dados/dados/metadados_Equipe_08_Limiar.txt

O QUE ENTREGAR AO PROFESSOR:

  Equipe_08_DensidadeEspectralPotencia.pdf   <- compilar a partir do .tex
                                                 (ver "COMO COMPILAR" abaixo)

-------------------------------------------------------------------------
COMO COMPILAR (Overleaf ou local)

  Overleaf:
    1. Criar um projeto em branco.
    2. Fazer upload de toda a pasta DensidadeEspectral_Latex/ (preserva a
       subpasta figs/ com as 5 figuras em PDF).
    3. Definir Equipe_08_DensidadeEspectralPotencia.tex como documento
       principal (menu Overleaf: "Main document").
    4. Compilar (pdfLaTeX). As figuras ja estao prontas -- nao e'
       necessario rodar nenhum script no Overleaf.
    5. Renomear o PDF final para Equipe_08_DensidadeEspectralPotencia.pdf
       (nome exigido pela Orientacao do Capitulo 5).

  Local (se houver pdflatex/latexmk instalado):
    cd DensidadeEspectral_Latex
    pdflatex Equipe_08_DensidadeEspectralPotencia.tex
    pdflatex Equipe_08_DensidadeEspectralPotencia.tex   (2x, refs/citacoes)

  Este ambiente de trabalho nao tem motor LaTeX instalado, entao o PDF
  final nao foi gerado aqui -- apenas o codigo-fonte e as figuras.

-------------------------------------------------------------------------
REPRODUCAO DA ANALISE (figuras + numeros citados no relatorio)

  cd reprodutibilidade
  python analise_dsp.py

  Requer NumPy, SciPy, Pandas e Matplotlib. Le diretamente o CSV do
  Capitulo 3 (nao gera dados novos) e escreve:

    ../DensidadeEspectral_Latex/figs/*.pdf   <- 5 figuras do relatorio
    resultados_dsp.json                      <- todos os numeros citados

-------------------------------------------------------------------------
RESUMO DO RESULTADO (ver relatorio para a discussao completa)

  Sinal analisado: e[n] = y_instrumento[n] - x_referencia[n] (erro do
  canal de medicao), N=3030 amostras, Fs=60 Hz, mais uma subserie
  complementar de 30 leituras repetidas em repouso (x=0).

  O ruido do canal e' aproximadamente branco (achatamento espectral de
  Welch = 0,966; autocorrelacao da subserie em repouso dentro da banda de
  95% em todos os atrasos testados), com uma contaminacao determinística
  estreita em ~6 Hz no registro completo, atribuivel a' interacao entre o
  quantizador do canal e o protocolo de excitacao em rampa do Capitulo 3
  -- nao ao ruido aleatorio em si. A estimativa de Blackman-Tukey (obtida
  transformando a autocorrelacao amostral) reproduz o mesmo piso e a
  mesma raia encontrados por Welch, verificando numericamente o teorema
  de Wiener-Khinchin.
