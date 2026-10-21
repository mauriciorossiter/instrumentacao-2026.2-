# TyphoonSim - Sensibilidade estática

## Arquivo pendente

O [relatório](../relatorio/relatorio.pdf) descreve uma bancada TyphoonSim/VHIL,
mas o modelo `.tse` não estava presente nos arquivos recebidos. Adicione nesta
pasta o modelo usado no relatório com o nome `modelo.tse`. O roteiro abaixo
registra o ensaio descrito no PDF; sua execução depende desse arquivo.

## Topologia e parâmetros do relatório

A fonte `Ramp2` alimenta o canal ideal diretamente e dois canais com ganhos
modificados. Os blocos `Sum1` e `Sum2` subtraem a saída ideal das saídas
modificadas. As sondas monitoram a entrada, a referência ideal, as duas saídas e
os dois resíduos em `Scope1`.

| Elemento ou sinal | Configuração |
|---|---|
| Ramp2 | Rampa de 0 a 10 V em 1 s; taxa de 10 V/s |
| Referência ideal | `y_id = x`; ganho 1,00 V/V |
| Gain1 | `y1 = 1.50 * x` |
| Gain2 | `y2 = 0.60 * x` |
| Sum1 | `e1 = y1 - y_id = 0.50 * x` |
| Sum2 | `e2 = y2 - y_id = -0.40 * x` |

## Ensaio ao anexar o modelo

1. Abra `modelo.tse` e confira os blocos, os ganhos e o sinal de cada subtrator.
2. Execute a bancada no ambiente TyphoonSim/VHIL utilizado pela equipe e
   observe o intervalo de 0 a 1 s em `Scope1`.
3. Registre os canais quando a entrada atingir 0, 2, 4, 6, 8 e 10 V, conforme
   a tabela de resultados do relatório.
4. Em `x = 10 V`, compare com `y_id = 10 V`, `y1 = 15 V`, `y2 = 6 V`,
   `e1 = 5 V` e `e2 = -4 V`.
5. Calcule `K_exp = (y_final - y_inicial) / (x_final - x_inicial)` e verifique
   os ganhos 1,50 e 0,60 V/V e os interceptos nulos.

Ao anexar o modelo, registre aqui a versão do software e as configurações de
execução efetivamente utilizadas.
