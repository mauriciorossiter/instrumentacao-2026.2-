# Fase 2 — Entrega Final: como submeter no Git

**Dossiê do Sistema Instrumentado** — entrega em **30/11**

Este documento trata apenas de **onde e como** a entrega é submetida no repositório.
O conteúdo de cada item (dossiê, pacote de repetibilidade, registro das verificações) é
o definido no documento de orientação do professor,
`ECOM060_Fase2_EntregaFinal_Orientacao_v1.pdf`.

---

## Identificação

| Item | Valor |
|---|---|
| Branch | a do grupo: `gXX-<sistema>` |
| Pasta | `gXX-<sistema>/entregas/fase-2/final-dossie/` |
| Título do PR | `gXX — Fase 2, Entrega Final: Dossiê do Sistema Instrumentado` |
| Prazo | PR aberto até o início da aula de **30/11** |

## Estrutura da pasta

```
gXX-<sistema>/entregas/fase-2/final-dossie/
  dossie/
    dossie.pdf                     ← o dossiê
    figuras/
      fig-01-<descricao>.png       ← todas as figuras do dossiê, na ordem do texto
  pacote/                          ← pacote de repetibilidade
    README.md                      ← objetivo, versões das ferramentas, roteiro em passos
                                     numerados e tabela de rastreabilidade
    e1/                            ← arquivos de simulação da Entrega 01, na versão corrigida
    e2/                            ← modelo.tse, painel.cus (e codigo/, se houver) da Entrega 02, corrigidos
    e3/                            ← idem, Entrega 03
    e4/                            ← idem, Entrega 04
    dados/
      fig-01-<descricao>.csv       ← dados de saída de cada figura, com o mesmo nome da figura no dossiê
  verificacao/
    verificacao-por-terceiros.md   ← relato da pessoa de outra equipe que testou o NOSSO pacote
    relato-teste-gYY.md            ← nosso relato testando o pacote da equipe YY
```

### Pacote de repetibilidade (`pacote/`)

- O pacote **é a pasta `pacote/` no repositório**. O "link" do pacote é o endereço dessa
  pasta na `main`.
- Os modelos e painéis entram **copiados** para `pacote/e2/`, `pacote/e3/` e
  `pacote/e4/`, na versão usada no dossiê. As pastas das entregas anteriores não se
  alteram.
- Dentro de cada `pacote/eN/` valem os nomes das entregas: `modelo.tse`, `painel.cus`,
  `codigo/README.md`.
- Na tabela de rastreabilidade do `pacote/README.md`, cada figura e cada tabela do dossiê
  aponta para o caminho do arquivo dentro de `pacote/`, para o ensaio e para o passo do
  roteiro.

### Verificação por terceiros (`verificacao/`)

- `verificacao-por-terceiros.md` registra o teste que outra equipe fez no pacote do grupo.
- `relato-teste-gYY.md` é o relato do grupo testando o pacote da equipe YY. Troque `YY`
  pelo número dela, por exemplo `relato-teste-g03.md`.
- Os dois arquivos ficam **na pasta do próprio grupo**. Não edite nem abra PR na pasta
  da outra equipe. Problemas no pacote dela são registrados no seu relato ou numa issue.
- Para testar o pacote de outra equipe, use a versão que ela deixou na branch dela,
  `gYY-<sistema>`, ou na `main`, e anote no relato o commit testado.

## Como submeter

```bash
git switch gXX-<sistema>
git fetch origin
git merge origin/main
# monte a pasta e depois:
git add gXX-<sistema>/entregas/fase-2/final-dossie
git commit -m "gXX: fase 2, entrega final - dossie do sistema instrumentado"
git push origin gXX-<sistema>
```

Abra um Pull Request da branch do grupo para a `main` com o título da tabela acima.

## Regras

1. **Um PR para esta entrega.** A entrega conta pela **data de abertura do PR**.
2. **"Acessível por link" significa neste repositório.** O dossiê, o pacote e as
   verificações estão no PR. Não use Drive, OneDrive nem anexo no Classroom.
3. **Use exatamente os nomes de pasta e de arquivo acima**, em minúsculas, sem acento e
   sem espaço.
4. **Dossiê somente em PDF.** Não suba `.docx` nem fontes LaTeX.
5. **Dados em CSV.** Não suba dados em planilha (`.xlsx`) nem em formato binário de
   ferramenta.
6. **Não entra no repositório:** rascunhos, versões intermediárias, pastas de
   compilação ou de cache do TyphoonSim, e qualquer coisa fora da pasta do grupo.
7. **README do grupo:** adicione esta entrega à tabela de estado das entregas.

## Antes de abrir o PR, confira

- [ ] A pasta está em `entregas/fase-2/final-dossie/`, na branch do grupo
- [ ] Existem `dossie/dossie.pdf`, `dossie/figuras/`, `pacote/README.md`, `pacote/e1/` a
      `pacote/e4/`, `pacote/dados/`, `verificacao/verificacao-por-terceiros.md` e
      `verificacao/relato-teste-gYY.md`
- [ ] Todo caminho citado na tabela de rastreabilidade existe dentro de `pacote/`
- [ ] Toda figura em `dossie/figuras/` tem um CSV de mesmo nome em `pacote/dados/`
      (exceto diagramas e capturas de tela, que não vêm de dados)
- [ ] Clonando o repositório, só com `pacote/README.md`, é possível reproduzir os
      resultados sem nenhum arquivo de fora
- [ ] Nenhum arquivo fora da pasta do grupo foi alterado
