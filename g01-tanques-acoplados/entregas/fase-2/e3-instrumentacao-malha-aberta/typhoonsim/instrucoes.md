# Reprodução no TyphoonSim 2026.3

## Modelo e painel

1. Use o TyphoonSim 2026.3 com licença ativa. Mantenha esta pasta da E03 e
   `e2-equivalente-eletrico` como pastas irmãs. O gerador carrega a planta
   `../e2-equivalente-eletrico/typhoonsim/modelo-offline.tse` (caminho relativo
   à pasta da entrega E03). O `modelo.tse` nominal já contém toda a planta
   instrumentada e pode ser aberto sozinho.
2. No TyphoonSim, abra `modelo.tse`, clique em **Run** e abra o Scope
   **Captura**. Os sinais `h1_m` e `h2_m` são as referências amostradas, as
   colunas `ideal_h1/2` são os caminhos unitários e `real_h1/2` as leituras
   do instrumento simulado. V1/V2 são tensões da planta; divida-as por 10
   para obter metros. Reconverta o tempo por `100(t_elétrico − 0,25)`.
3. Abra **Standalone HIL SCADA**, carregue `painel.cus` e clique
   **Start simulation** na barra para ativar as macros. Se o painel não
   localizar os scripts automaticamente, informe o caminho absoluto da
   pasta `typhoonsim` da E03 no campo **Pasta dos scripts** e confirme com Enter.
   O botão **Executar no TyphoonSim** prepara e roda um novo ensaio offline.
   Os ajustes mudam **entre** rodadas. Nenhum dispositivo HIL é necessário.
4. Selecione um preset. Os campos recebem seus valores; depois de qualquer
   ajuste manual, confirme com Enter. Ao executar, o gráfico e o estado são
   substituídos pela nova captura. O estado indica a pasta temporária do CSV,
   do JSON e do gráfico daquela rodada.
5. Para repetir a demonstração, clique `zero-6mm` e execute. Comente o
   deslocamento de 6 mm em relação ao ideal. Em seguida mude apenas
   **Erro de zero** para 60, confirme com Enter e execute novamente. Os
   patamares físicos continuam em 1,1025 m, e as leituras terminam cerca de
   60 mm acima deles. A planta não recebe a leitura como entrada.

## Presets de referência

| Preset | Condição da planta | Perfil da cadeia |
|---|---|---|
| degrau | Equilíbrio 1 m / 1 m; +5% na vazão | Cadeia nominal |
| inicial | h1 = 1,15 m; h2 = 0,60 m; vazão nominal | Cadeia nominal |
| pulso | Equilíbrio 1 m / 1 m; +20% por 30 s | Cadeia nominal |
| referencia | Degrau +5% | Bypass de todos os efeitos |
| so-ganho / so-curvatura | Degrau +5% | +0,3% de ganho / 3 mm de curvatura |
| so-adc / so-filtro | Degrau +5% | Quantizador de 12 bits / RC de 0,2 Hz |
| so-interferencia | Degrau +5% | Seno ±2 mm a 0,8 Hz, sem RC |
| zero-6mm / zero-20mm / zero-60mm | Degrau +5% | Apenas desvio de zero |
| tau-0p2s / tau-10s / tau-60s | Degrau +5% | Apenas dinâmica da tomada |
| ruido-2mm / ruido-10mm / ruido-40mm | Degrau +5% | Seno com RC de 0,2 Hz |
| zero-corrigido | Degrau +5% | Cadeia nominal, subtraindo 6 mm |

Cadeia nominal: erro de zero +6 mm, ganho +0,3%, curvatura de pico 3 mm,
constante da tomada 0,2 s, interferência de pico 2 mm, corte RC de 0,2 Hz,
ADC de 12 bits, correção de zero de 0 mm. O zero desliga o efeito; no caso
de `tau_s`, `fc_hz` e `adc_bits`, zero desvia o bloco correspondente.
Nos presets de seno com RC, subtraia a rodada `so-filtro` para isolar a
interferência. As previsões e os resultados estão no relatório.

## Execução em lote

A partir da pasta desta entrega:

```powershell
$env:TYPHOONPATH = 'C:\Program Files\TyphoonSim 2026.3'
python -m pip install -r typhoonsim/requirements.txt
python typhoonsim/executar.py --ensaio degrau --saida "$env:TEMP/g01-e3"
python typhoonsim/executar.py --todos --saida "$env:TEMP/g01-e3"
python simulacao/graficos.py --capturas "$env:TEMP/g01-e3"
```

Pode-se regenerar `modelo.tse` adicionando
`--salvar-modelo typhoonsim/modelo.tse` ao ensaio degrau e o SCADA com
`python typhoonsim/gerar_painel.py`. O gerador usa somente blocos nativos:
`Gain`, `Constant`, `Sum`, `Product`, `Low-Pass Filter`,
`Trigonometric function`, `Limit`, `Round` e `Probe`, além da planta da E02.
Os filtros recebem a frequência na escala elétrica (100 vezes Hz físicos).
A pré-carga estabelece as condições iniciais; a tomada é inicializada no
nível de partida, sem interpretar a rampa artificial de pré-carga como
um evento hidráulico. Os CSVs principais estão junto aos JSONs; as
capturas completas das variações podem ser refeitas com `--todos`.
