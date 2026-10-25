# Reprodução - Fase 2, Entrega 1: Caracterização da planta

## Ferramenta e ambiente

A simulação usa Python, NumPy, SciPy e Matplotlib, sem depender de TyphoonSim.
Ambiente validado nesta organização: **Python 3.10.11**, **NumPy 2.2.6**,
**SciPy 1.15.3** e **Matplotlib 3.10.9**, com versões registradas em
[requirements.txt](requirements.txt). O relatório informa o ambiente de sua
elaboração; as versões acima são as utilizadas para repetir os cálculos aqui.

Em um ambiente Python isolado, abra um terminal nesta pasta e execute:

```console
python -m pip install -r requirements.txt
python tanques.py
```

O processamento completo pode levar alguns minutos. O script calcula as
[tabelas](resultados.md), exporta as curvas em [dados/](dados/) e gera as
figuras em [relatorio/figuras/](../relatorio/figuras/), com caminhos relativos
ao próprio arquivo. O módulo [complementos.py](complementos.py) é chamado
automaticamente por [tanques.py](tanques.py).

## Modelo e parâmetros

```text
A1*dh1/dt = qi(t) - k1*sqrt(h1)
A2*dh2/dt = k1*sqrt(h1) - k2*sqrt(h2)
```

O escoamento do primeiro tanque alimenta o segundo, com descarga livre.
O bloco `P` no início de `tanques.py` reúne os parâmetros de referência:

| Parâmetro | Valor | Unidade |
|---|---|---|
| A1 e A2 | 0,50 | m² |
| k1 e k2 | 0,010 | m^(5/2)/s |
| qi nominal | 0,010 | m³/s |
| h mínimo operacional | 0,10 | m |
| h máximo | 1,20 | m |
| Equilíbrio nominal h1 e h2 | 1,00 | m |

Integração principal: `solve_ivp`, método RK45, `max_step = 0.1 s`,
`rtol = 1e-8`, `atol = 1e-10`, saída densa e horizonte de `20*max(tau1,tau2)`.
Os gráficos dos ensaios principais mostram até 1200 s; os CSVs mantêm o
horizonte calculado, com amostras a cada 0,5 s.

O modelo linearizado acompanha o não linear como referência. Os tempos
t63, tr (10 a 90%) e ts (banda de ±2% da variação total) usam cruzamentos
calculados com `brentq`. A normalização usa o equilíbrio não linear analítico.

## Como gerar cada figura

Todas as figuras são geradas pelo comando `python tanques.py`:

| Figura | Arquivo em relatorio/figuras/ | Ensaio ou rotina |
|---|---|---|
| 1 | fig-01-diagrama-blocos.png | `diagrama()` em complementos.py; balanços de massa e lei de Torricelli |
| 2 | fig-02-resposta-degrau.png | R3(a): degrau de +5% na vazão, h1(0) = h2(0) = 1 m |
| 3 | fig-03-condicao-inicial.png | R3(b): h1(0) = 1,15 m e h2(0) = 0,60 m, vazão nominal |
| 4 | fig-04-resposta-pulso.png | R3(c): pulso de +20% na vazão por 30 s, partindo do equilíbrio |
| 5 | fig-05-convergencia-rk4.png | RK4 com passos 10; 5; 2,5; 1,25; 0,625 s, comparado com DOP853 em 300 s |
| 6(a) | fig-06a-sensibilidade-k2.png | k2 multiplicado por 0,25; 0,5; 1; 2; 3; 4 |
| 6(b) | fig-06b-sensibilidade-a2.png | A2 multiplicado por 0,25; 0,5; 1; 2; 4 |
| 6(c) | fig-06c-sensibilidade-vazao.png | qi nominal multiplicado por 0,25; 0,5; 0,75; 1; 2; 4 |
| Complemento a R5 | fig-06d-sensibilidade-k1.png | Contraprova: k1 multiplicado por 0,25; 0,5; 1; 2; 3; 4 |
| 7 | fig-07-amplitude-degrau.png | Degraus de -30; -20; -10; -5; +1; +5; +9%, comparando Kef/Kdc e ts/ts,linear |

Em R5, cada caso parte do próprio equilíbrio e recebe degrau de +5%.
Traços contínuos representam casos válidos; traços interrompidos indicam
extrapolações fora do domínio. Os painéis 6(a), 6(b) e 6(c) correspondem aos
três painéis da Figura 6 do relatório; 6(d) é a contraprova adicional de k1.

## CSVs e validação numérica

| Arquivo em dados/ | Conteúdo |
|---|---|
| degrau-01.csv | Degrau de +1%, usado na validação cruzada |
| degrau-05.csv | Degrau de +5% |
| condicao-inicial.csv | Resposta com condições iniciais não nulas |
| pulso.csv | Resposta ao pulso de vazão |

As colunas são `tempo_s`, `h1_nl_m`, `h2_nl_m`, `h1_linear_m` e
`h2_linear_m`, separadas por vírgula, com ponto decimal.

O processamento inclui a ordem do RK4, o balanço integral de massa,
a influência da amplitude do degrau e as elasticidades. O balanço integra
simultaneamente h1, h2 e os volumes de entrada e saída, verificando
`A1*Delta_h1 + A2*Delta_h2 - (Vin - Vout)`.
As elasticidades usam diferenças centrais: ±0,01% no linearizado e ±10% no
parâmetro, com degrau de 1%, no não linear. Esses últimos testes podem
extrapolar o domínio e não representam necessariamente operação física válida.

O script verifica automaticamente o equilíbrio de 1,1025 m, os tempos
aproximados de 221,54; 350,30; 608,90 s do degrau de 5%, a ordem próxima de 4
do RK4, o balanço de massa e a relação `Kef/Kdc = 1 + delta/2`.

### Valores da reexecução

Os resultados desta execução ficam em `resultados.md`. A ordem ajustada do
RK4 foi 4,0486 (aproximadamente 4,05), enquanto o PDF informa 4,06. Na
verificação da bomba de primeira ordem, os aumentos de ts foram 0,1650%,
0,8388% e 1,7144% para constantes de 1, 5 e 10 s; o PDF apresenta 0,17%,
0,88% e 1,8%. O relatório recebido foi preservado, e os valores recalculados
estão explicitamente separados neste registro de reprodução.

## Arquivos da entrega

- [Relatório recebido, preservado](../relatorio/relatorio.pdf).
- [Apresentação em PDF](../apresentacao/apresentacao.pdf), exportada dos slides
  originais da equipe.
- [Gravação fornecida pela equipe](../apresentacao/gravacao.mp4), preservada
  como material complementar aos slides em PDF: 9 min 52,2 s, 1920 × 1080.

O script original foi mantido como base e recebeu ajustes de caminhos e
exportação de CSVs. `complementos.py` reúne as verificações adicionais e as
figuras 1, 5 e 7, que não eram geradas pela pasta inicialmente recebida.
As figuras são reproduções das análises do relatório; a diagramação pode
variar entre versões do Matplotlib.

Mantenha ambientes virtuais fora da pasta da entrega. Não versione caches,
arquivos de compilação, rascunhos, PPTX, DOCX ou fontes LaTeX.
