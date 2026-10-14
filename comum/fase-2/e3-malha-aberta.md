# Fase 2 — Entrega 03: como submeter no Git

**Instrumentação em Malha Aberta: Medição Ideal e Medição Real** — entrega em **11/11**

Este documento trata apenas de **onde e como** a entrega é submetida no repositório.
O conteúdo de cada item (relatório, roteiro de repetibilidade, modelo, painel, slides) é
o definido no documento de orientação do professor,
`ECOM060_Fase2_Entrega03_Orientacao.pdf`.

---

## Identificação

| Item | Valor |
|---|---|
| Branch | a do grupo: `gXX-<sistema>` |
| Pasta | `gXX-<sistema>/entregas/fase-2/e3-malha-aberta/` |
| Título do PR | `gXX — Fase 2, Entrega 3: Instrumentação em Malha Aberta` |
| Prazo | PR aberto até o início da aula de **11/11** |

## Estrutura da pasta

```
gXX-<sistema>/entregas/fase-2/e3-malha-aberta/
  relatorio/
    relatorio.pdf              ← relatório, incluindo o roteiro de repetibilidade
    figuras/
      fig-01-<descricao>.png   ← todas as figuras do relatório, na ordem do texto
  typhoonsim/
    modelo.tse                 ← modelo do TyphoonSim (planta + caminhos de medição ideal e real)
    painel.cus                 ← painel SCADA
    instrucoes.md              ← roteiro de repetibilidade em passos numerados (o mesmo do relatório)
    captura-scada.png          ← esquemático + SCADA em execução, referenciada no fim do instrucoes.md
    codigo/                    ← SOMENTE se houver código externo (C-function etc.)
      README.md                ← descrição do código
  apresentacao/
    apresentacao.pdf           ← slides
```

Se for preciso mais de um modelo ou painel, use `modelo-<descricao>.tse` e
`painel-<descricao>.cus` e diga no `instrucoes.md` qual arquivo usar em cada ensaio.

## Como submeter

```bash
git switch gXX-<sistema>
git fetch origin
git merge origin/main
# monte a pasta e depois:
git add gXX-<sistema>/entregas/fase-2/e3-malha-aberta
git commit -m "gXX: fase 2, entrega 3 - instrumentacao em malha aberta"
git push origin gXX-<sistema>
```

Abra um Pull Request da branch do grupo para a `main` com o título da tabela acima.

## Regras

1. **Um PR para esta entrega.** A entrega conta pela **data de abertura do PR**.
2. **"Acessível por link" significa neste repositório.** O link do modelo e do painel é
   o PR. Não use Drive, OneDrive nem anexo no Classroom.
3. **Use exatamente os nomes de pasta e de arquivo acima**, em minúsculas, sem acento e
   sem espaço.
4. **Relatório e slides somente em PDF.** Não suba `.pptx`, `.docx` nem fontes LaTeX.
5. **Não entra no repositório:** rascunhos, versões intermediárias, pastas de
   compilação ou de cache do TyphoonSim, e qualquer coisa fora da pasta do grupo.
6. **Datasheets e referências citadas não são enviados.** Eles aparecem nas referências
   do relatório.
7. **Depois de submetida, a entrega não se altera.** As correções apontadas no aval
   entram na entrega seguinte.
8. **README do grupo:** adicione esta entrega à tabela de estado das entregas.

## Antes de abrir o PR, confira

- [ ] A pasta está em `entregas/fase-2/e3-malha-aberta/`, na branch do grupo
- [ ] Existem `relatorio/relatorio.pdf`, `relatorio/figuras/`, `typhoonsim/modelo.tse`,
      `typhoonsim/painel.cus`, `typhoonsim/instrucoes.md`, `typhoonsim/captura-scada.png`
      e `apresentacao/apresentacao.pdf`
- [ ] Se houver código externo, ele está em `typhoonsim/codigo/`, junto com o `README.md`
- [ ] Clonando o repositório, é possível abrir o modelo, carregar o painel e executar o
      roteiro do `instrucoes.md` sem nenhum arquivo de fora
- [ ] Nenhum arquivo fora da pasta do grupo foi alterado
