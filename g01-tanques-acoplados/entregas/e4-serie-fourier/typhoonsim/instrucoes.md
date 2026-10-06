# TyphoonSim - Série de Fourier

## Arquivo e ambiente

Abra [modelo.tse](modelo.tse) no Schematic Editor do TyphoonSim. O arquivo foi
salvo na versão **2026.3** do software e usa o formato de esquema **4.2**.
O modelo original foi preservado; o nome interno continua sendo `furrier`.
O [relatório](../relatorio/relatorio.pdf) apresenta a dedução da série e as
figuras dos ensaios.

## Topologia

| Caminho | Função |
|---|---|
| `Square Wave Source1` → sonda `Onda Quadrada` | Referência periódica |
| `Clock1` → `C function1` → sonda `Fourrier` | Reconstrução pela série truncada |
| `Scope1` | Exibição dos sinais `Onda Quadrada` e `Fourrier` |

O relógio fornece o tempo em segundos à entrada `in` do bloco C. A saída `out`
é a soma dos termos senoidais de ordem ímpar:

```text
x_N(t) = soma de (4*A/(n*pi)) * sin(n*w0*t)
         para n = 1, 3, 5, ... e n <= N
w0 = 2*pi*60
```

O código usa `pi = 3.14159`, `A = 1.0` e `N = 50`. Não há arquivos C externos
ou bibliotecas externas associados ao bloco: o código está dentro do `.tse`.

## Parâmetros gravados

| Parâmetro | Valor no arquivo |
|---|---|
| Frequência fundamental da fonte e da reconstrução | 60 Hz |
| Período fundamental | Aproximadamente 0,016667 s |
| Nível alto / baixo de `Square Wave Source1` | 1 / 0 |
| Ciclo de trabalho / fase da fonte | 0,5 / 0 |
| Amplitude `A` da reconstrução | 1,0 |
| Ordem máxima `N` | 50; são somados 25 termos ímpares, até n = 49 |
| Taxa de execução de `Clock1` e da fonte | 100 µs |
| Dispositivo configurado | VHIL+ |
| Método de simulação | `exact`; passo automático |
| Solver / integração configurados para TyphoonSim | DAE / BDF |
| Passo máximo / inicial | 100 µs / 1 µs |
| Tempo de simulação | 100 s |
| Tolerância absoluta / relativa | 0,001 / 0,001 |

## Execução e comparação com a referência

1. Abra `modelo.tse` e confira os caminhos e parâmetros acima.
2. A fonte salva gera uma onda **unipolar, de 0 a 1**, enquanto a série
   implementada reconstrói uma onda **bipolar, de -1 a 1**, como definida no
   relatório. Para comparar diretamente a mesma forma de onda, ajuste o nível
   baixo da fonte para `-1`, mantendo o nível alto em `1`, a frequência em
   `60 Hz`, a fase em `0` e o ciclo de trabalho em `0.5`.
3. Inicie a simulação no TyphoonSim. Se executar no ambiente VHIL, compile e
   carregue o modelo nesse ambiente antes de iniciar a execução.
4. Abra `Scope1` e selecione `Onda Quadrada` e `Fourrier`, já configurados no
   arquivo. Use a mesma janela de tempo para os dois sinais; um intervalo de
   aproximadamente 0 a 0,05 s permite observar três períodos.
5. Compare os patamares, as transições e as oscilações próximas às
   descontinuidades. A série converge a zero nos instantes de salto da onda
   bipolar e apresenta o sobressinal do fenômeno de Gibbs nas proximidades.

## Ensaios de truncamento

No código de saída de `C function1`, altere apenas `int N` para cada ensaio,
mantendo `A`, a frequência e a janela de observação iguais. Reinicie a execução
para cada configuração; recompile quando o ambiente exigir compilação.

| Valor de N | Ordens somadas | Quantidade de termos |
|---|---|---|
| 5 | 1, 3 e 5 | 3 |
| 30 | 1, 3, ..., 29 | 15 |
| 50 | 1, 3, ..., 49 | 25 |

No código entregue, `N` é a **ordem máxima permitida**, e não a quantidade de
termos da soma. Essa distinção deve ser considerada ao reproduzir as figuras
rotuladas com 5, 30 e 50 harmônicos no relatório. Compare a aproximação dos
patamares e o estreitamento das oscilações à medida que `N` aumenta.

Se exportar dados dos ensaios, use nomes como `ensaio-n05.csv`, `ensaio-n30.csv`
e `ensaio-n50.csv` dentro desta entrega. Arquivos de compilação, executáveis,
caches e backups ficam fora do versionamento.

As configurações acima foram conferidas no conteúdo de `modelo.tse`. A
simulação não foi executada durante a reorganização das pastas.
