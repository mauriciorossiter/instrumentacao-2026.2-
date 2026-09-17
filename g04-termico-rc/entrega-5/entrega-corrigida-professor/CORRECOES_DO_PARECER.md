# Correções aplicadas após o parecer de 13/09/2026

O parecer foi tratado como fonte de requisitos de revisão. Os CSVs reais foram
preservados sem alteração.

| Diretriz do parecer | Correção aplicada | Evidência no relatório |
| --- | --- | --- |
| Usar as 485 amostras e as duas condições | Toda a análise foi refeita a partir de `dados/Equipe_04_DesvioZeroSensibilidade.csv` | Seções 5.1, 5.4 e 6; Tabelas de cobertura e ajustes |
| Fazer o hash coincidir com os metadados | O relatório cita o prefixo `d5ae377b7e2f` e inclui o hash completo no apêndice | Seções 4.3, 5.4, conclusão e Apêndice A |
| Analisar `condicao_2` ao lado de `condicao_1` | As duas regressões, curvas, resíduos e intervalos são apresentados lado a lado | Seções 6.1 a 6.4 |
| Calcular a incerteza do ajuste | Foram calculados `s(p_hat)`, `s(K_hat)` e intervalos de aproximadamente 95% | Seções 5.2, 5.3 e 6.3 |
| Distinguir estatisticamente os dois efeitos | Foram calculadas as diferenças entre condições e suas incertezas combinadas | Seções 5.3, 6.3 e 7 |
| Confirmar que não houve uso do autoteste sintético | A origem VHIL, o timestamp, a contagem e o hash são explicitados | Seções 4.3, 5.4 e conclusão |

## Valores reproduzidos dos dados reais

- `condicao_1`: 241 amostras, `p_hat = 0,4974 ± 0,0017 V` e
  `K_hat = 1,2007 ± 0,0003`.
- `condicao_2`: 244 amostras, `p_hat = 1,0002 ± 0,0017 V` e
  `K_hat = 0,9002 ± 0,0003`.
- Diferenças: `Delta p = 0,5028 ± 0,0024 V` e
  `Delta K = -0,3005 ± 0,0004`.

As parcelas após o sinal `±` são incertezas padrão calculadas por mínimos
quadrados ordinários. Os arquivos em `dados_derivados/` documentam os cálculos,
mas não substituem o CSV bruto.
