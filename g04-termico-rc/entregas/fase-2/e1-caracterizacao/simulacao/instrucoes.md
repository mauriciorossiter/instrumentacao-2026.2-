# Instruções de reprodução — Simulação térmica RC (G04)

Ferramentas e versões usadas na geração dos resultados:

- Python 3.12 (biblioteca padrão para integração; NumPy/Matplotlib para pós-processamento)
- Typhoon HIL Control Center 2026.3 (simulação nativa da rede térmica Foster)

## Parâmetros da planta

Sistema térmico RC de quatro ramos, equivalente Foster do IGBT IKD04N60RF (datasheet v2.6, Fig. 21):

| Ramo i | Rᵢ [K/W] | τᵢ [s] | Cᵢ = τᵢ/Rᵢ [J/K] |
|---|---|---|---|
| 1 | 0,492466 | 2,0 × 10⁻⁴ | 4,0612 × 10⁻⁴ |
| 2 | 0,884411 | 5,4 × 10⁻⁴ | 6,1058 × 10⁻⁴ |
| 3 | 0,589157 | 2,1 × 10⁻³ | 3,5644 × 10⁻³ |
| 4 | 0,073673 | 3,1658 × 10⁻² | 4,2971 × 10⁻¹ |

Cápsula fixa: Tc = 298,15 K. Potência nominal: 10 W (exceto extrapolação de 100 W).

## Arquivos incluídos

- `modelo.py`: definição dos parâmetros, cenários e solução fechada de referência.
- `simular_rk4.py`: integração RK4 explícito com passo h = 2 µs e registro a 10 µs.
- `gerar_figuras_tabelas.py`: pós-processamento dos CSVs para reproduzir as figuras.
- `parametros.json`: configuração de todos os cenários.
- `modelos/`: arquivos `.tse` e `.json` dos 16 casos para o Typhoon HIL.
- `resultados_rk4/`: CSVs e `resumo.json` já gerados.
- `resultados_typhoon/`: resultados da execução nativa, quando aplicável.

## Passos para reproduzir as figuras do relatório

### 1. Figuras 1 a 6 via Python

Requer Python 3.12 com NumPy e Matplotlib instalados:

```bash
cd g04-termico-rc/entregas/fase-2/e1-caracterizacao/simulacao
python simular_rk4.py          # gera resultados_rk4/*.csv e resumo.json
python gerar_figuras_tabelas.py # gera as figuras em PNG
```

As figuras são escritas no caminho padrão do script (`../../Overleaf/figuras/` a partir de `simulacao/`). Para gerar diretamente no relatório, ajuste a variável `FIG` no início de `gerar_figuras_tabelas.py` para apontar para `../relatorio/figuras/`.

Mapeamento das figuras do relatório:

| Figura | Arquivo gerado | Descrição |
|---|---|---|
| Figura 1 | `reducao.png` | Impedância térmica e erro da redução de 2 estados |
| Figura 2 | `degrau.png` | Resposta ao degrau de 10 W |
| Figura 3 | `livre.png` | Resposta livre a partir de IC não nula |
| Figura 4 | `pulso.png` | Resposta ao pulso de 10 W |
| Figura 5 | `validacao_typhoon.png` | Desvios TyphoonSim contra solução fechada |
| Figura 6 | `sensibilidade.png` | Variação de R₁, C₁ e R₄ |

### 2. Execução nativa no Typhoon HIL 2026.3

Abra o Control Center, certifique-se de que não há outra sessão de API em execução, e rode:

```bash
typhoon-python typhoon_modelo.py --caso degrau_4r
typhoon-python executar_typhoon.py --caso degrau_4r
```

Casos disponíveis: `degrau_4r`, `livre_4r`, `pulso_4r`, `degrau_2r`, `livre_2r`, `pulso_2r`, e todos os casos de sensibilidade (`R1_x0.2`, `R1_x5`, `C1_x0.2`, etc.). Use `--caso todos` para executar em sequência.

Para visualização direta no Schematic Editor, abra `modelos/G04_degrau_4r.tse` e pressione **Run TyphoonSim**. Após a simulação, abra o Scope `Resultados`. O eixo horizontal está em segundos; `T_j_K` é a temperatura da junção em kelvin.

### 3. Reprodutibilidade independente do Typhoon

A integração RK4 em `simular_rk4.py` usa apenas a biblioteca padrão do Python e reproduz todos os gráficos principais sem depender do Typhoon HIL. Os valores característicos (ganho, tempos de subida e acomodação, polos) estão documentados em `resultados_rk4/resumo.json`.

## Observações

- A extrapolação de 100 W é apenas numérica; não representa operação física segura do componente.
- O adaptador elétrico de 1 V/K no Typhoon serve apenas para observação; ele não carrega a planta térmica.
- Todos os arquivos `.tse` usam um único bloco nativo *Thermal network (Foster)*, sem C function.
