ECOM060 - Instrumentacao Eletronica - 2026.2
Grupo 08 - Sistema 7: Gerador Sincrono (Swing Equation)
Topico atribuido: LIMIAR
Entrega de 30/08/2026 - versao 1

Equipe: Cleiber de Meireles da Silva Junnior
        Leonardo Lima Barbosa Pereira
        Willian Tcheldon Oliveira Santos

-------------------------------------------------------------------------

  ECOM060_Relatorio_Limiar_Grupo08.pdf      (16 pag.)
      Documento principal. Caracterizacao do limiar do sistema
      instrumentado, em seis ensaios (L1 a L6).

  reprodutibilidade/
      Os dois arquivos citados no Apendice A do relatorio:
        caracterizacao_limiar.py   - script unico, gera tudo
        resultados_limiar.json     - todos os valores citados no texto

-------------------------------------------------------------------------
O QUE O RELATORIO ESTABELECE

  O ponto de partida e' que o LIMIAR NAO ESTA NA PLANTA. O modelo continuo
  da swing equation tem limiar exatamente nulo (Ensaio L1, verificado por
  nove ordens de grandeza). O limiar caracterizado e' o do sistema
  INSTRUMENTADO, construido a partir de tres mecanismos da cadeia de
  medicao: quantizacao do conversor A/D, piso de ruido do canal de delta e
  o criterio de deteccao adotado.

  Definicao adotada: VIM (JCGM 200:2012) item 4.16, limiar de
  discriminacao. A Tabela 1 do relatorio separa limiar de resolucao, zona
  morta e sensibilidade, que sao os topicos vizinhos das demais equipes.

  Resultado principal, referido a' entrada:

    12 bits, sem promediacao efetiva ...... 2,8118e-03 pu  (0,1406 % do FS)
    14 bits, promediacao de 20 s .......... 1,2976e-04 pu  (0,0065 % do FS)
    16 bits, promediacao de 20 s .......... 1,2408e-04 pu  (0,0062 % do FS)

  Especificacao recomendada: conversor de 14 bits sobre FS = 360 graus,
  com promediacao de 20 s. De 12 para 14 bits o limiar melhora 21,67 vezes
  (e' onde o ruido passa a atuar como dither e a promediacao comeca a
  funcionar); de 14 para 16 bits o ganho cai para 1,046 vez.

-------------------------------------------------------------------------
TRES RESULTADOS QUE VALEM A ARGUICAO

  1. O mesmo hardware entrega dois limiares diferentes conforme o instante
     de leitura. Ler no pico do transitorio amplifica o sinal por 1,9313
     (zeta = 0,0227), o que MELHORA o limiar em 1,93x quando ele e'
     limitado por quantizacao, mas o PIORA em 12,68x quando e' limitado
     por ruido - a janela util em torno do pico da' so 2 amostras a 60 Hz,
     contra 1200 em regime. (Secao 5.3)

  2. O limiar depende do ponto de operacao: melhora 11,3x entre
     delta_0 = 10 graus e 85 graus, porque Ps = Pmax*cos(delta_0) amolece.
     E' o mesmo mecanismo do Ensaio 1 do relatorio v2, agora com
     consequencia metrologica. O valor a ESPECIFICAR e' o da maquina
     descarregada, nao o de plena carga. (Secao 5.4)

  3. Ate a simulacao tem limiar. O erro do integrador em relacao a' forma
     fechada cresce de 1,17e-09 % para 4,66e-02 % conforme dPm cai de
     1e-02 para 1e-10 pu: o piso de indeterminacao e' fixo e o sinal
     encolhe. E' o mesmo mecanismo que a cadeia fisica impoe. (Secao 3)

-------------------------------------------------------------------------
VALIDACAO NO CIRCUITO EQUIVALENTE DO TYPHOONSIM (Secao 6)

  O circuito de [2] foi estendido com a cadeia de medicao que produz o
  limiar -- um quantizador de 12 bits no ramo de SINAL, a jusante do
  integrador, sem tocar na topologia eletrica ja validada:

    delta -> Sum(+delta,-delta0) -> Gain(1/q) -> Round(floor) -> Gain(q)

  Tres modelos .tse (0,40x / 0,60x / 1,20x o limiar de 12 bits), mesmo
  solucionador de [2] (DAE, BDF, passo maximo 1e-3 s, tolerancias 1e-9).

    dPm         excursao    erro TS x Python    erro/excursao   codigos A/D
    0,40x       0,0679 deg  2,038e-04 deg       0,3001 %        {0}     = {0}
    0,60x       0,1019 deg  3,056e-04 deg       0,3000 %        {0,1}   = {0,1}
    1,20x       0,2038 deg  6,104e-04 deg       0,2995 %        {0,1,2} = {0,1,2}

  O circuito reproduz o LIMIAR, nao so a dinamica: os codigos assumidos
  pelo conversor sao identicos aos do gabarito Python nos tres ensaios --
  inclusive no caso sutil de 0,60x, em que a variacao esta abaixo do
  limiar em regime permanente mas o sobressinal de 1,9313 cruza uma
  transicao de codigo.

  CORRECAO DE LEITURA SOBRE [2] -- vale citar na arguicao:
  A validacao do v2 reporta erros ABSOLUTOS de 0,0106 a 1,0906 grau. E'
  tentador ler o menor deles como "o piso do TyphoonSim" e concluir que
  ele nao mediria um limiar de milesimos de grau. A leitura e' errada:
  normalizando pela excursao, os cinco ensaios do v2 caem entre 0,12 % e
  1,09 % -- o erro e' PROPORCIONAL a' excursao (deriva de fase do passo
  do solucionador), nao um piso aditivo. Os tres ensaios desta entrega
  confirmam com 0,3001 %, 0,3000 % e 0,2995 %.
  Consequencia: num ensaio de pequenos sinais o erro cai junto. O maior
  observado foi 6,104e-04 grau, contra o limiar especificado de
  4,056e-03 grau -- margem de 6,6 vezes.

  Arquivos em reprodutibilidade/typhoonsim/:
    INSTRUCOES.txt             COMECAR POR AQUI -- como abrir, como rodar
                               e os valores esperados de cada ensaio para
                               conferencia direta, sem precisar de Python
    L_quant12_*.tse            os tres modelos
    comparacao_limiar_typhoonsim.json   numeros do confronto TS x Python

  Os modelos vao prontos: nao e' preciso rodar nada em Python para
  conferi-los. Os scripts que os geraram e executaram (monta_circuito_
  limiar.py e roda_limiar.py) ficam no pacote de projeto da equipe, como
  na entrega v2, e estao a' disposicao se o professor quiser.

-------------------------------------------------------------------------
DEBITO TECNICO DECLARADO (um so, Secao 7 do relatorio)

  Limiar do lado da ENTRADA nao foi caracterizado. Atrito seco na valvula
  do regulador de velocidade produziria um limiar anterior a' planta,
  provavelmente dominante em instalacao real e de natureza diferente
  (zona morta bilateral, nao limiar unilateral). Caracteriza-lo exigiria
  parametros de atuador que a equipe nao possui; arbitra-los daria uma
  tabela de numeros sem lastro.

  Este e' o unico efeito de natureza DINAMICA entre os quatro levantados,
  e portanto o unico para o qual o TyphoonSim voltaria a ser a ferramenta
  adequada - faltam os parametros, nao a ferramenta.

-------------------------------------------------------------------------
RESSALVAS DE PARAMETRO (Secao 7)

  sigma_delta = 0,020 graus e' representativo, nao medido. Ancorado por
  ordem de grandeza no limite de 1 % de TVE da IEEE Std C37.118.1
  (equivalente a 0,573 grau de erro angular). Os limiares por ruido
  escalam linearmente com ele; os por quantizacao nao dependem dele. A
  conclusao estrutural - existe um ponto de saturacao em que comprar mais
  bits deixa de ajudar - e' robusta: o que muda e' ONDE esse ponto cai.

  Fundo de escala de 360 graus e' escolha, nao dado. Decorre de supor
  medicao de angulo por sincrofasor. Um canal de faixa reduzida daria
  quantum menor para o mesmo numero de bits - caminho alternativo ao
  aumento de resolucao, nao explorado aqui.

-------------------------------------------------------------------------
REPRODUCAO

  python3 caracterizacao_limiar.py

  Requer NumPy, SciPy e Matplotlib. Gera as tres figuras do relatorio e
  reescreve resultados_limiar.json. Integracoes deterministicas; o Monte
  Carlo da Secao 5.2 usa semente fixa (20260830). Mesmas tolerancias do
  relatorio v2: rtol = 1e-10, atol = 1e-12.
