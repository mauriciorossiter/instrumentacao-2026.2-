# Fase 2 — Entrega 01: como submeter no Git

**Caracterização da Planta no Domínio de Origem** — entrega em **21/10**

Este documento trata apenas de **onde e como** a entrega é submetida no repositório.
O conteúdo de cada item (relatório, simulação, slides) é o definido no documento de
orientação do professor, `ECOM060_Fase2_Entrega01_Orientacao.pdf`.

---

## Identificação

| Item | Valor |
|---|---|
| Branch | a do grupo: `gXX-<sistema>` |
| Pasta | `gXX-<sistema>/entregas/fase-2/e1-caracterizacao/` |
| Título do PR | `gXX — Fase 2, Entrega 1: Caracterização da Planta` |
| Prazo | PR aberto até o início da aula de **21/10** |

## Estrutura da pasta

```
gXX-<sistema>/entregas/fase-2/e1-caracterizacao/
  relatorio/
    relatorio.pdf              ← relatório
    figuras/
      fig-01-<descricao>.png   ← todas as figuras do relatório, na ordem do texto
  simulacao/
    instrucoes.md              ← ferramenta e versão, valores dos parâmetros e passos para gerar cada figura
    <arquivos da simulação>    ← .py, .m, .slx, .xlsx, .tse... (ferramenta à escolha da equipe)
  apresentacao/
    apresentacao.pdf           ← slides
```

Nesta entrega a ferramenta de simulação é livre. Por isso a pasta se chama `simulacao/`
e não `typhoonsim/`.

## Como submeter

```bash
git switch gXX-<sistema>
git fetch origin
git merge origin/main
# monte a pasta e depois:
git add gXX-<sistema>/entregas/fase-2/e1-caracterizacao
git commit -m "gXX: fase 2, entrega 1 - caracterizacao da planta"
git push origin gXX-<sistema>
```

Abra um Pull Request da branch do grupo para a `main` com o título da tabela acima.

## Regras

1. **Um PR para esta entrega.** A entrega conta pela **data de abertura do PR**.
2. **"Acessível por link" significa neste repositório.** O link da entrega é o PR. Não
   use Drive, OneDrive nem anexo no Classroom.
3. **Use exatamente os nomes de pasta e de arquivo acima**, em minúsculas, sem acento e
   sem espaço.
4. **Relatório e slides somente em PDF.** Não suba `.pptx`, `.docx` nem fontes LaTeX.
5. **Não entra no repositório:** rascunhos, versões intermediárias, arquivos de build
   ou de cache, e qualquer coisa fora da pasta do grupo.
6. **Depois de submetida, a entrega não se altera.** As correções apontadas no aval
   entram na entrega seguinte.
7. **README do grupo:** adicione esta entrega à tabela de estado das entregas.

## Antes de abrir o PR, confira

- [ ] A pasta está em `entregas/fase-2/e1-caracterizacao/`, na branch do grupo
- [ ] Existem `relatorio/relatorio.pdf`, `relatorio/figuras/`, `simulacao/instrucoes.md`
      e `apresentacao/apresentacao.pdf`
- [ ] Os arquivos de `simulacao/` bastam para refazer cada figura seguindo o `instrucoes.md`
- [ ] Nenhum arquivo fora da pasta do grupo foi alterado
