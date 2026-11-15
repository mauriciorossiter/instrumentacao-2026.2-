# Gerador síncrono (swing equation) — Grupo 08

**Sistema:** gerador síncrono ligado a um barramento infinito, descrito pela equação de oscilação do rotor
(swing equation): (2H/ωs)·δ̈ = Pm − Pmax·sen δ − D·δ̇.
**Domínio de origem:** eletromecânico (a parte mecânica do rotor vira circuito pela analogia força-tensão: J→L, B→R, K→1/C).
**Classificação:** 2ª ordem, não linear (termo Pmax·sen δ), SISO (entrada Pm, saída δ). Na Fase 2 a planta ganha a
tensão terminal e o campo (E′), e a medição e o controle a tornam MIMO (entradas Pm e Vref; saídas V e f).
**Referência de validação:** conservação de energia / critério das áreas iguais (sem solução fechada). Na Fase 2, o
modelo no Typhoon (Virtual HIL) é comparado com a integração numérica da E01 e com o gabarito Python de cada entrega.

## Equipe

| Nome completo | Matrícula |
|---|---|
| Cleiber de Meireles da Silva Junnior | 20113298 |
| Leonardo Lima Barbosa Pereira | 22110875 |
| Willian Tcheldon Oliveira Santos | 17212878 |

## Entregas

### Fase 1

| Entrega | Pasta | Estado |
|---|---|---|
| E1 — Caracterização | `entregas/e1-caracterização/` | entregue |
| E2 — Estáticas | `entregas/e2-estaticas/` | entregue |
| E3 — Geração de dados | `entregas/e3-geracao-dados/` | entregue |
| E4 — Densidade espectral | `entregas/e4-densidade-espectral/` | entregue |
| E5 — Cadeia ideal | `entregas/e5-fase1-cadeia-ideal/` | entregue |
| E6 — Não idealidades | `entregas/e6-fase1-nao-idealidades/` | entregue |
| E7 — Validação funcional | `entregas/e7-fase1-validacao-funcional/` | entregue |

### Fase 2

| Entrega | Pasta | Estado |
|---|---|---|
| E01 — Caracterização do sistema | `entregas/fase-2/e1-caracterizacao/` | entregue |
| E02 — Equivalente elétrico | `entregas/fase-2/e2-equivalente-eletrico/` | entregue (validado no VHIL, 14 ensaios) |
| E03 — Instrumentação (malha aberta) | `entregas/fase-2/e3-instrumentacao/` | entregue (validado no VHIL, 5 ensaios) |
| E04 — Controle (malha fechada) | `entregas/fase-2/e4-controle/` | entregue (validado no VHIL, 11 ensaios) |

E02, E03 e E04 foram apresentadas juntas (slides em `entregas/fase-2/e4-controle/relatorio/apresentacao-e02-e03-e04.pdf`).

## Observações

- Ferramenta: Typhoon HIL Control Center 2026.2 em modo Virtual HIL (a simulação offline do TyphoonSim exige licença).
  Cada `typhoonsim/instrucoes.md` traz a topologia, os valores, as expressões não lineares e o roteiro de cada ensaio.
- O modelo da E03 e da E04 é o mesmo (`instrumentacao_controle.tse`); cada pasta tem a sua cópia para a entrega ficar completa.
