# TyphoonSim - Projeto da cadeia ideal

## Arquivos e ambiente

Abra [modelo.tse](modelo.tse) no Schematic Editor do TyphoonSim. O arquivo foi
salvo na versão **2026.3**, no formato de esquema **4.2**, com dispositivo
configurado como **VHIL+**. O nome interno do modelo é `G01_Cadeia_Ideal`.
O [relatório](../relatorio/relatorio.pdf) contém a especificação da Família A,
o dimensionamento do condicionador e os resultados apresentados pela equipe.

## Topologia e parâmetros

A cadeia é formada por uma excitação de deslocamento, um sensor ideal com
saída em tensão e um condicionador não inversor:

```text
Excitacao_Deslocamento -> Sensor_LVDT -> Condicionador_NaoInversor
                             |                    |
                         Vin_sensor        Vout_condicionada
```

As duas sondas são exibidas em `Scope1`. O sensor e o condicionador são
representados por blocos de ganho ideal.

| Bloco | Parâmetro gravado | Interpretação |
|---|---|---|
| Excitacao_Deslocamento (`core/Ramp`) | `initial_output = 0.0`; `slope = 10.0`; `start_time = 0.0` | Deslocamento de 0 a 10 mm entre 0 e 1 s |
| Sensor_LVDT (`core/Gain`) | `gain = 0.1` | Sensibilidade de 0,10 V/mm; saída de 0 a 1 V |
| Condicionador_NaoInversor (`core/Gain`) | `gain = 5.0` | Ganho de 5 V/V; saída de 0 a 5 V |
| Scope1 | `Vin_sensor` e `Vout_condicionada` | Observação da tensão nativa e da tensão condicionada |

As expressões da cadeia no intervalo de ensaio são:

```text
x(t) = 10*t                 [mm], 0 <= t <= 1 s
Vin(t) = 0.10*x(t)          [V]
Vout(t) = 5.00*Vin(t)       [V]
Av = 1 + Rf/Rin = 5.00
```

O relatório dimensiona `Rin = 10 kΩ` e `Rf = 40 kΩ`. Esses resistores justificam
o ganho do condicionador; no arquivo `.tse`, a função é implementada pelo bloco
`Gain`, sem uma rede de resistores ou um amplificador operacional explícito.
A rampa não tem limitador; mantenha o ensaio em 1 s para respeitar a faixa de
0 a 10 mm.

## Configuração gravada de simulação

| Configuração | Valor |
|---|---|
| Tempo de simulação | 1,0 s |
| Método de simulação | `exact`; passo automático |
| Solver / integração | DAE / BDF |
| Passo máximo / inicial | 100 µs / 1 µs |
| Taxa de execução da rampa | 100 µs |
| Tolerância absoluta / relativa | 0,001 / 0,001 |
| Taxa de amostragem (`data_sampling_rate`) | 0, conforme gravado no arquivo |

## Ensaio de origem e fundo de escala

1. Abra `modelo.tse` e confira a rampa e os dois ganhos na tabela acima.
2. Execute por **1 s** no TyphoonSim. Se usar VHIL, compile e carregue o
   modelo nesse ambiente antes de iniciar a execução.
3. Abra `Scope1` com os sinais `Vin_sensor` e `Vout_condicionada`, já
   selecionados no arquivo, e observe o intervalo de 0 a 1 s.
4. Verifique a origem: em `t = 0 s`, ambas as tensões devem ser 0 V.
5. Verifique o fundo de escala: em `t = 1 s`, o deslocamento é 10 mm,
   `Vin = 1 V` e `Vout = 5 V`.
6. Calcule `erro_FS = abs(Vout(1 s) - 5 V)` e
   `erro_percentual_FS = 100 * erro_FS / 5 V`. O critério da Família A é
   `erro_FS <= 0.10 V`, equivalente a 2% do fundo de escala. A janela de
   aceitação no ponto final é de 4,90 a 5,10 V.

| Tempo (s) | Deslocamento esperado (mm) | Vin esperado (V) | Vout esperado (V) |
|---|---|---|---|
| 0,0 | 0,0 | 0,0 | 0,0 |
| 0,2 | 2,0 | 0,2 | 1,0 |
| 0,4 | 4,0 | 0,4 | 2,0 |
| 0,6 | 6,0 | 0,6 | 3,0 |
| 0,8 | 8,0 | 0,8 | 4,0 |
| 1,0 | 10,0 | 1,0 | 5,0 |

Esses valores são referências calculadas pelas expressões dos blocos. Ao
exportar o ensaio, salve os dados em um CSV dentro desta entrega, por exemplo
`ensaio-cadeia-ideal.csv`. Não versione arquivos de compilação, executáveis,
caches ou backups.

## Conferência com o relatório

A seção R5 do PDF informa passo de 100 ns e coleta de 2000 amostras. O modelo
recebido registra os passos e a taxa de execução da tabela acima e não contém
uma configuração explícita de coleta de 2000 amostras. Para reproduzir essa
aquisição específica, confirme e registre as configurações do ensaio original.

O PDF e o modelo foram preservados durante a organização da entrega. Os
parâmetros deste roteiro foram conferidos no `.tse`; a simulação não foi
executada durante essa organização.
