"""
Equipe 8 (Resolução) - ECOM060
Script para:
  1) Adicionar a coluna 'repeticao' (1..100) em cada um dos 5 CSVs capturados.
  2) Montar o arquivo final Equipe_08_Resolucao.csv com as colunas exigidas
     pelo PDF: tempo, x_referencia, y_instrumento, repeticao.

x_referencia é o valor FIXO do Constant1 daquele ponto (NÃO a coluna i_in,
que neste modelo já vem com ruído, pois o probe está depois do Sum1).

Como usar:
  1. Coloque este script na mesma pasta dos 5 CSVs exportados do Typhoon.
  2. Ajuste, se necessário, os nomes dos arquivos e os valores de x_referencia
     na lista PONTOS abaixo (já vêm preenchidos com os valores do guia).
  3. Ajuste os nomes das colunas de tempo e leitura conforme o CSV exportado
     pelo TyphoonSim (COL_TEMPO, COL_I_READ) -- confira o cabeçalho real do
     seu arquivo antes de rodar.
  4. Rode: python montar_equipe08.py
"""

import pandas as pd
import glob

# ---------------------------------------------------------------
# 1) CONFIGURAÇÃO -- ajuste conforme seus arquivos reais
# ---------------------------------------------------------------

# Nome do arquivo CSV de cada ponto e o valor correspondente de x_referencia
# (valor do Constant1, em ampères), conforme a Seção 5 do guia.
PONTOS = [
    {"arquivo": "ponto1_1p00050mA.csv", "x_referencia": 1.00050e-3},
    {"arquivo": "ponto2_1p00080mA.csv", "x_referencia": 1.00080e-3},
    {"arquivo": "ponto3_1p00095mA.csv", "x_referencia": 1.00095e-3},
    {"arquivo": "ponto4_1p00100mA.csv", "x_referencia": 1.00100e-3},
    {"arquivo": "ponto5_1p00300mA.csv", "x_referencia": 1.00300e-3},
]
# Time,Subsystem1.i_in,Subsystem1.i_read
# Nomes das colunas como elas aparecem no CSV exportado pelo Typhoon.
# CONFIRA o cabeçalho do seu arquivo e ajuste se for diferente.
COL_TEMPO = "time"        # ex.: "time", "Time (s)", "tempo" ...
COL_I_READ = "i_read"     # ex.: "i_read", "Subsystem1.i_read" ...

# Nome do arquivo final de saída
SAIDA_FINAL = "Equipe_08_Resolucao.csv"

# ---------------------------------------------------------------
# 2) PROCESSAMENTO
# ---------------------------------------------------------------

dfs_finais = []

for ponto in PONTOS:
    caminho = ponto["arquivo"]
    x_ref = ponto["x_referencia"]

    df = pd.read_csv(caminho)

    # Verifica se as colunas esperadas existem
    if COL_TEMPO not in df.columns or COL_I_READ not in df.columns:
        print(f"[AVISO] Colunas encontradas em {caminho}: {list(df.columns)}")
        print(f"        Ajuste COL_TEMPO/COL_I_READ no script conforme o cabeçalho acima.")
        raise SystemExit(1)

    n = len(df)

    # Monta o dataframe no formato exigido pelo PDF
    df_saida = pd.DataFrame({
        "tempo": df[COL_TEMPO],
        "x_referencia": x_ref,               # mesmo valor repetido nas n linhas
        "y_instrumento": df[COL_I_READ],
        "repeticao": range(1, n + 1),        # 1, 2, 3, ..., n (reinicia por ponto)
    })

    # Salva também uma cópia individual do ponto já com a coluna repeticao
    nome_individual = caminho.replace(".csv", "_com_repeticao.csv")
    df_saida.to_csv(nome_individual, index=False)
    print(f"[OK] {caminho}: {n} linhas -> {nome_individual}")

    dfs_finais.append(df_saida)

# ---------------------------------------------------------------
# 3) ARQUIVO FINAL CONSOLIDADO (todos os pontos juntos)
# ---------------------------------------------------------------

df_final = pd.concat(dfs_finais, ignore_index=True)
df_final.to_csv(SAIDA_FINAL, index=False)

print(f"\n[OK] Arquivo final consolidado salvo em: {SAIDA_FINAL}")
print(f"     Total de linhas: {len(df_final)}  (esperado: {len(PONTOS)} x 100 = {len(PONTOS)*100})")
print(df_final.head(10))