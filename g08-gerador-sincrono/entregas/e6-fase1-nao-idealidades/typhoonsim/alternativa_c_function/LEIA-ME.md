# Versão alternativa: camadas da E02 em C function

**O modelo da entrega é `../modelo.tse`.** Nele, o que veio da E01 fica em C function, sem
alteração, e as camadas da E02 são blocos nativos.

Este `modelo_c_function.tse` é **o mesmo modelo** com as três camadas da E02 (folga, resolução e
ruído de contato 1/f) escritas dentro de uma única C function `potenciometro`. O circuito elétrico,
a referência e o receptor são idênticos.

| | `../modelo.tse` (nativo) | `modelo_c_function.tse` (C) |
|---|---|---|
| camadas visíveis no esquemático | sim | não (dentro do código) |
| gerador do ruído 1/f | Random Source nativo, **sem semente** | gerador próprio com **semente fixa** |
| comparação com o gabarito Python | folga e resolução ponto a ponto; ruído pela estatística | **tudo ponto a ponto** (bit a bit, conferido com gcc) |
| contrafactual R8 sem buffer | `../modelo_r8_sem_buffer.tse` | — |

**Para que serve.** Conferência: como o ruído tem a mesma semente do gabarito, a simulação desta
versão tem que coincidir com o Python amostra a amostra, inclusive o ruído.

**Como rodar** (na pasta `reprodutibilidade/`, com o Python da API):
```
G08_MODELO=c <python da API> roda_typhoon.py          # CSV em alternativa_c_function/dados/
```
Regerar o arquivo: `<python da API> -c "import monta_modelo as M; M.monta(modo='c', salvar='<caminho>')"`.
