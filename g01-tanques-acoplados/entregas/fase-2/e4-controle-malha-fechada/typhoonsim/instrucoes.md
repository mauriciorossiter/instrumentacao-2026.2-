# Roteiro de reprodução

1. Use TyphoonSim 2026.3 com licença ativa e mantenha as pastas da
   Entrega 2, 3 e 4 no mesmo diretório da Fase 2. O gerador desta entrega
   reutiliza os blocos de instrumentação e os parâmetros da Entrega 3,
   que carrega a planta nativa da Entrega 2.
2. Abra `modelo.tse` no TyphoonSim, execute e abra o Scope **Captura**.
   O modelo salvo corresponde ao degrau de 1,00 para 1,08 m com medição real
   nominal. `ref_m`, `med_m` e `h2_m` são, respectivamente, referência,
   leitura realimentada e nível físico de T2 em metros. `h1_m` registra
   o nível de T1. `bomba_ls` e `entrada_ls` estão em L/s.
3. No Standalone HIL SCADA, abra `painel.cus` e acione **Start simulation**
   para habilitar macros. Se solicitado, preencha **Pasta dos scripts**
   com o caminho absoluto da pasta `typhoonsim` da Entrega 4 e confirme
   com Enter. Escolha um preset e clique **Executar no TyphoonSim**.
   O resultado e a pasta da captura aparecem ao lado do gráfico.
4. Compare `subida-ideal`, `subida-real` e `subida-calibrado`. No segundo,
   a leitura deve chegar ao setpoint de 1,08 m enquanto T2 fica em cerca
   de 1,068 m. No terceiro, T2 deve ficar em cerca de 1,0795 m.
   Use esses dois últimos presets para a demonstração em sala.
5. Repita com `disturbio-ideal`, `disturbio-real` e `disturbio-calibrado`
   (referência 1 m, acrescentar 0,50 L/s após a bomba) e os presets
   `descida-*` (referência de 0,92 m). Os nove CSVs principais e as
   métricas estão em `../simulacao/dados/`.
6. Para isolar efeitos, selecione `zero-mm-6`, `tau-s-60` ou `ruido-mm-40`.
   No primeiro e no segundo os demais efeitos estão em bypass.
   O terceiro conserva o RC a 0,2 Hz. Os presets com prefixo `d-`
   repetem a variação durante a rejeição de perturbação. Edite o campo
   correspondente, confirme com Enter e execute. A grade completa e
   a primeira falha de cada métrica estão em `../simulacao/mapa.json`.

## API e execução em lote

Na pasta da Entrega 4, use Python com a API Typhoon 1.32.1, NumPy e Matplotlib.
O código Python monta os blocos nativos, inicia o solver, exporta os dados e
faz as figuras. O controlador e a instrumentação rodam no circuito nativo.

```powershell
$env:TYPHOONPATH = 'C:\Program Files\TyphoonSim 2026.3'
python -m pip install -r typhoonsim/requirements.txt
python typhoonsim/rodar.py --grupo todos --saida "$env:TEMP/g01-e4"
python simulacao/graficos.py --capturas "$env:TEMP/g01-e4"
```

Escolha também `--ensaio NOME`, `--grupo principais`, `--grupo grade`
(subida) ou `--grupo grade-disturbio`. Para recriar o modelo nominal,
adicione `--salvar-modelo typhoonsim/modelo.tse` ao preset `subida-real`.
Para recriar o painel, execute `python typhoonsim/gerar_painel.py`.
O PI usa Gain, Sum, Product, Integrator e Limit. A correção adiciona
Gain e Sum à leitura antes do comparador.

Pré-carga de 0,25 s elétrico. Simulação total de 25,25 s elétricos.
O tempo físico após o disparo é `100·(t_elétrico − 0,25)`.
O passo de processamento é 100 µs elétricos e o Scope amostra a cada
1 ms elétrico (0,1 s físico). As métricas usam amostras com disparo ativo.
O erro estacionário é a média assinada dos últimos 100 s físicos.
A acomodação é a entrada sustentada na banda de ±4 mm até o fim da captura.
Na comparação com o limite de 4 mm, aplica-se 0,001 mm de tolerância numérica.
