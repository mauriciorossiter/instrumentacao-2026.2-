# Equipe 04 — caracterização do sistema térmico RC

Pacote revisado em 25/09/2026 a partir da captura VHIL fornecida pela equipe.
O relatório final tem cinco páginas, inclui os resultados medidos no
TyphoonSim e foi compilado e inspecionado. Os arquivos originais em Downloads
não foram alterados.

## Arquivos principais

- `Relatorio_Equipe04_TermicoRC_revisado.pdf`: PDF final revisado.
- `main.tex`: fonte do relatório para Overleaf. Compilar com **pdfLaTeX**.
- `figuras/`: dois gráficos gerados dos CSVs, incluídos no relatório.
- `resultados_vhil/`: tabela LaTeX, resumo JSON e curvas VHIL comparadas com
  a solução analítica, na posição esperada pelo `main.tex`.
- `capturas/captura_20260925_094319/`: CSV bruto, metadados originais e
  resultados da análise, mantidos para rastreabilidade.
- `Equipe04_TermicoRC_IGBT.tse`: esquemático executado.
- `evidencias_compilacao/`: `.cpd` e log de compilação bem-sucedida.
- `parametros_e_referencia.py`, `capturar_vhil.py`, `analisar_captura.py`,
  `gerar_figuras.py`: scripts que permitem reproduzir as etapas.
- `referencia_analitica/`: dados e métricas calculados fora do TyphoonSim.

## Conferências realizadas

- 30.000 linhas de amostras, seis probes e três pulsos de reinício;
- passo-base de simulação de 0,2 µs; Capture com decimação 50 e passo
  uniforme de 10 µs;
- hashes SHA-256 do CSV, `.tse` e `.cpd` conferem com os metadados;
- compilação THCC 2026.2 concluída com restrições de tempo atendidas;
- maior erro VHIL versus solução analítica: 1,9074 µK no degrau,
  1,8947 µK na relaxação e 1,9062 µK no pulso;
- pico do degrau: 45,3970718384 °C; equilíbrio do modelo: 45,39707 °C;
- critério de erro de 0,15 K satisfeito.

Essa concordância verifica a execução da implementação matemática, não a
física de um IGBT real. Não houve ensaio em hardware físico.

## Overleaf e envio

Importe o ZIP completo em um projeto novo do Overleaf, marque `main.tex` como
arquivo principal e selecione **pdfLaTeX**. A estrutura das pastas deve ser
preservada: `figuras/` e `resultados_vhil/` precisam ficar ao lado de
`main.tex`. Confira se os dois gráficos aparecem e se a tabela mostra erros
na ordem de 10⁻⁶ K.

Para a entrega, envie o PDF revisado e, se o professor pedir os artefatos de
reprodução, este pacote: `.tse`, CSV bruto, JSON de metadados, resumo da
análise, scripts e referências. O `.cpd` é específico da versão/configuração
do Typhoon; anexe-o quando for solicitado. Não é necessário um painel `.cus`
para reproduzir a captura programática.
