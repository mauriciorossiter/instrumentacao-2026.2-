# Relatório revisado da Equipe 04 — projeto Overleaf

Este projeto documenta a geração e a validação dos dados brutos para análise de
desvio de zero e sensibilidade. Ele incorpora todas as correções obrigatórias do
parecer de 13/09/2026. Os dois CSVs em `dados/` são cópias sem alteração dos
arquivos obtidos no TyphoonSim.

## Como importar no Overleaf

1. No Overleaf, selecione **New Project > Upload Project**.
2. Envie o arquivo ZIP fornecido com esta pasta.
3. Confirme que `main.tex` é o documento principal.
4. Use o compilador **pdfLaTeX** e clique em **Recompile**.

O projeto é autocontido. Os gráficos são produzidos pelo próprio LaTeX com
PGFPlots a partir dos arquivos em `dados_derivados/`. O relatório foi testado
com pdfLaTeX/Tectonic.

## Arquivos da entrega corrigida

- `dados/Equipe_04_DesvioZeroSensibilidade.csv`
- `dados/Equipe_04_DesvioZeroSensibilidade_metadados.csv`
- PDF recompilado do relatório revisado

O modelo e o script em `modelo/` podem ser enviados como evidência adicional de
rastreabilidade. O arquivo `CORRECOES_DO_PARECER.md` mapeia cada diretriz do
professor à correção correspondente. Os arquivos em `dados_derivados/` servem
somente para os gráficos e tabelas do relatório e não substituem os dados
brutos.
