# TyphoonSim - Caracterização dos tanques acoplados

## Arquivo pendente

Esta entrega contém o [relatório de caracterização](../relatorio/relatorio.pdf),
mas o modelo `.tse` não estava presente nos arquivos recebidos. Para completar a
entrega, adicione o modelo correspondente nesta pasta como `modelo.tse`.
Não é possível executar esta etapa diretamente a partir dos arquivos atuais.

## Modelo e parâmetros descritos no relatório

A entrada `qi` alimenta o tanque 1. A descarga `q1 = k1 * sqrt(h1)` alimenta o
tanque 2, que descarrega `q2 = k2 * sqrt(h2)` para o exterior. Os níveis são os
dois estados do sistema; a saída principal é `h2`.

```text
dh1/dt = (qi - k1 * sqrt(h1)) / A1
dh2/dt = (k1 * sqrt(h1) - k2 * sqrt(h2)) / A2
```

| Parâmetro | Valor |
|---|---|
| A1 e A2 | 0,50 m² |
| k1 e k2 | 0,010 m^(5/2)/s |
| qi nominal | 0,010 m³/s |
| h1 e h2 no equilíbrio nominal | 1,00 m |
| Faixa de validade dos níveis | 0,10 a 1,20 m |

## Verificação ao anexar o modelo

Abra `modelo.tse` no TyphoonSim e confira as equações, as unidades e os
parâmetros acima. Registre as condições iniciais, a configuração do simulador e
o procedimento de cada ensaio realizado. Para a validação em regime permanente,
verifique `qi = k1 * sqrt(h1) = k2 * sqrt(h2)`. No transitório, compare a variação
do volume total `A1*h1 + A2*h2` com a integral de `qi - q2`.
