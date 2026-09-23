# ECOM060 — Instrumentação Eletrônica

Curso de Engenharia de Computação — Universidade Federal de Alagoas
Semestre 2026.2 — Prof. Maurício Beltrão Rossiter

---

## Sobre o projeto

Cada grupo recebe uma planta física distinta e, ao longo do semestre, projeta a
instrumentação capaz de medir, condicionar e monitorar as grandezas relevantes desse
sistema.

Instrumentar exige antes conhecer a planta: saber que grandezas medir, em que faixa
elas variam, com que rapidez, e como reagem a distúrbios. Por isso o projeto começa
pela caracterização do sistema e pela construção de um equivalente elétrico simulável
no TyphoonSim — é esse modelo que serve de bancada para projetar e testar a
instrumentação antes de qualquer implementação física.

O trabalho é entregue em etapas ao longo do semestre. Cada entrega é um relatório
fechado, acompanhado do modelo do TyphoonSim correspondente.

---

## Sistemas e grupos

| Grupo | Sistema | Domínio de origem |
|---|---|---|
| [01](g01-tanques-acoplados/) | Tanques acoplados | hidráulico |
| [02](g02-massa-mola-amortecedor/) | Massa-mola-amortecedor | mecânico translacional |
| [03](g03-pendulo-invertido/) | Pêndulo invertido | mecânico |
| [04](g04-termico-rc/) | Térmico RC (semicondutor) | térmico |
| [05](g05-monotanque/) | Monotanque (nível de líquido) | hidráulico |
| [06](g06-motor-cc/) | Motor CC (escovado) | eletromecânico |
| [07](g07-motor-bldc/) | Motor BLDC (MOONS' R42BLD30L3) | eletromecânico |
| [08](g08-gerador-sincrono/) | Gerador síncrono (swing equation) | eletromecânico |

Nos grupos 06, 07 e 08 o sistema já é parcialmente elétrico: a analogia se aplica à
parte mecânica (J→L, B→R, K→1/C), enquanto o restante já é circuito.

No grupo 04, o domínio térmico não possui análogo de indutância — não existe inércia
de fluxo de calor. O circuito equivalente é RC puro, e isso é esperado, não uma falha
da modelagem.

---

## Como funciona

O **GitHub** é o canal de envio: toda entrega e toda devolutiva é enviada por este
repositório, que substitui os formulários de envio de atividades. O **Classroom** fica
para a comunicação da disciplina — avisos, prazos e dúvidas. Não envie arquivos pelo
Classroom.

### Fluxo resumido

1. Trabalhe na branch do seu grupo, dentro da pasta do seu grupo.
2. Monte a entrega em `entregas/eN-<nome>/`, faça commit e push e abra um PR para a
   `main`.
3. Depois da correção do professor e da integração do PR, sincronize sua branch com a
   `main`.
4. Salve a versão final do relatório, com as correções incorporadas, em
   `devolutiva/eN-<nome>.pdf`; faça commit e push e abra um PR para a `main`.
5. Repita para a entrega seguinte.

### Cada grupo tem a sua branch

A branch é permanente e leva o nome da pasta do grupo: `g01-tanques-acoplados`,
`g02-massa-mola-amortecedor`, ..., `g08-gerador-sincrono`. É nela que o grupo trabalha
o semestre inteiro.

```bash
git clone <url-do-repositorio>
cd <repositorio>
git switch g05-monotanque   # sua branch, já criada
```

**Trabalhe apenas na sua branch e apenas dentro da pasta do seu grupo.**
Não faça commit na `main`. Não edite pasta de outro grupo — nem para "corrigir"
algo que pareça errado. Se encontrar um problema no trabalho de outra equipe, abra
uma issue.

### Cada entrega é uma pasta

Dentro da pasta do seu grupo, crie **uma pasta por entrega**, dentro de `entregas/`:

```
g05-monotanque/
  README.md
  entregas/
    e1-caracterizacao/
      relatorio/
        relatorio.pdf
        figuras/
      typhoonsim/
        modelo.tse
        instrucoes.md
        captura-scada.png
    e2-<nome-da-proxima-entrega>/
      relatorio/
      typhoonsim/
  devolutiva/
    e1-caracterizacao.pdf
    e2-<nome-da-proxima-entrega>.pdf
```

Nomeie as pastas de entrega com prefixo numérico e nome descritivo, em minúsculas e
com hífen: `e1-caracterizacao`, `e2-instrumentacao`, e assim por diante. O número
garante a ordenação; o nome torna a pasta legível meses depois.

Toda entrega tem as duas pastas, `relatorio/` e `typhoonsim/`. Não crie estruturas
próprias — a uniformidade é o que permite corrigir oito projetos diferentes.

Entrega já submetida não se mexe. As correções apontadas pelo professor não são feitas
reescrevendo a entrega: elas entram na versão final do relatório, enviada como
devolutiva (ver [A devolutiva também vira um Pull Request](#a-devolutiva-também-vira-um-pull-request)).

### Cada entrega vira um Pull Request

Quando a entrega estiver pronta:

```bash
git add g05-monotanque/entregas/e1-caracterizacao
git commit -m "g05: entrega 1 - caracterizacao do sistema"
git push origin g05-monotanque
```

Abra um Pull Request da sua branch (`g05-monotanque`) para a `main`, com o título no
formato `g05 — Entrega 1: Caracterização do Sistema`.

**A data de abertura do PR é o que conta como data de entrega.** Não a data do commit.

Depois que o PR for aceito e integrado à `main`, sincronize sua branch antes de
continuar:

```bash
git switch g05-monotanque
git fetch origin
git merge origin/main
```

### A devolutiva também vira um Pull Request

Depois que o professor corrigir a entrega, a equipe incorpora as correções e envia a
**versão final do relatório**, em PDF, na pasta `devolutiva/` do grupo, com o nome da
entrega a que ele se refere:

```
g05-monotanque/
  entregas/
    e1-caracterizacao/
      relatorio/
        relatorio.pdf          ← versão submetida
  devolutiva/
    e1-caracterizacao.pdf      ← versão final (devolutiva)
```

Os dois PDFs ficam no repositório: a versão submetida em `entregas/` não se apaga, não
se renomeia e não se substitui. A devolutiva é o próprio PDF corrigido — não envie
arquivo listando as alterações.

Enquanto nenhuma devolutiva tiver sido enviada, a pasta contém apenas
`sem-devolutiva.md`, um aviso padrão. Apague esse arquivo no mesmo commit da primeira
devolutiva.

```bash
git add g05-monotanque/devolutiva
git commit -m "g05: devolutiva 1 - caracterizacao do sistema"
git push origin g05-monotanque
```

Abra um Pull Request para a `main` com o título no formato
`g05 — Devolutiva 1: Caracterização do Sistema`. Como na entrega, **a data de abertura
do PR é o que conta como data de envio da devolutiva.** Depois da integração,
sincronize a branch com a `main` da mesma forma.

---

## O que cada entrega precisa conter

### `relatorio/`

- `relatorio.pdf` — o relatório da entrega, em PDF
- `figuras/` — as figuras do relatório, também como arquivos de imagem separados

Escreva o relatório na ferramenta que preferir (Word, Google Docs, LaTeX local, o que
for). O repositório recebe apenas o PDF, não os arquivos de edição.

As figuras vão soltas em `figuras/` além de estarem dentro do PDF porque o GitHub
renderiza imagem direto na interface: dá para conferir os gráficos sem baixar e abrir o
relatório. Nomeie na ordem em que aparecem no texto, com nome descritivo —
`fig-01-diagrama-blocos.png`, `fig-02-resposta-degrau.png`, `fig-03-drenagem-livre.png`.
Prefira PNG.

### `typhoonsim/`

- `modelo.tse` — o arquivo para abrir no TyphoonSim
- `instrucoes.md` — topologia do circuito, valores dos elementos, expressão dos
  elementos não lineares, e como executar cada ensaio
- `captura-scada.png` — captura de tela mostrando o esquemático montado **e** o painel
  SCADA em execução, com os valores visíveis nos instrumentos virtuais

A captura deve ser referenciada ao final do `instrucoes.md`:

```markdown
## Captura de tela (esquemático + painel SCADA)

![Esquemático e painel de instrumentação](captura-scada.png)
```

O nome do arquivo no link precisa bater **exatamente** com o nome do arquivo enviado,
incluindo maiúsculas e minúsculas. Windows não diferencia `Captura.PNG` de
`captura.png`, mas o GitHub diferencia — funciona na sua máquina e quebra no
repositório.

---

## O README do seu grupo

Cada pasta de grupo tem um `README.md`. Preencha-o na primeira entrega e mantenha-o
atualizado. Ele deve conter:

- Nome do sistema e número do grupo
- Nome completo e matrícula de todos os integrantes
- Descrição curta da planta e do domínio de origem
- Classificação do sistema: ordem, linearidade, SISO ou MIMO
- Referência de validação adotada (ver seção seguinte)
- Tabela com o estado de cada entrega

---

## Validação do modelo

Antes de instrumentar, é preciso confiar no modelo. Um sensor projetado sobre uma
bancada que não reproduz a física do sistema mede bem uma planta que não existe.

A cadeia de validação tem três estágios, em ordem decrescente de confiança:

1. **Solução algébrica de referência**, quando existe — é o padrão-ouro
2. **Integração numérica** do modelo, comparada contra a solução algébrica
3. **TyphoonSim**, comparado contra a integração numérica

Atenção: **nem todo sistema tem solução analítica fechada.** Cinco das oito plantas não
têm. Se a sua for uma delas, não perca semanas procurando uma integral que não existe —
a referência de validação é outra, e precisa estar declarada no relatório.

| Grupo | Referência de validação |
|---|---|
| 01 | regime permanente analítico + balanço de massa integral |
| 02 | solução fechada, todos os ensaios |
| 03 | autovalores do modelo linearizado (sistema instável em malha aberta) |
| 04 | solução fechada, todos os ensaios |
| 05 | solução fechada apenas na resposta livre |
| 06 | solução fechada, todos os ensaios |
| 07 | regime permanente e balanço de potência |
| 08 | conservação de energia / critério das áreas iguais |

---

## Convenções que evitam dor de cabeça

**PDF e `.tse` são arquivos binários.** O Git não consegue mesclá-los: se duas pessoas
editarem em paralelo, o trabalho de uma delas será perdido. Combinem quem fica com cada
arquivo em cada semana.

**Suba cada PDF uma única vez, já pronto:** a versão submetida em `entregas/` e a versão
final em `devolutiva/`. Cada commit de um arquivo binário guarda uma cópia inteira dele
no histórico. Rascunhos e versões intermediárias devem ficar fora do repositório — subir
o relatório dez vezes até acertar deixa o clone lento para todo mundo.

**Evite acentos e espaços em nomes de arquivo e pasta.** Use `relatorio` e não
`Relatório`, `captura-scada.png` e não `Captura SCADA.png`. Acentos em caminho causam
problemas reais entre Windows, macOS e Linux.

---

## Material compartilhado

A pasta `comum/` contém o material de apoio da disciplina: o relatório-modelo de
referência, que define o padrão de profundidade e organização esperado nas entregas, e
as tabelas de correspondência entre domínios para a analogia força-tensão.

Se precisar alterar algo em `comum/`, abra um PR separado explicando a mudança — o
conteúdo é usado pelos oito grupos."