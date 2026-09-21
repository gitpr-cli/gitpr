# ADR-006 — O split usa captura de diff própria, exige índice limpo e não aplica smart excludes

- **Status:** Aceito
- **Data:** 2026-09-20
- **Contexto:** spec [20260918_skill_gitpr_split_command_spec.md](20260918_skill_gitpr_split_command_spec.md) §2, §4.1 e §5; grill rodadas 1–5
- **Glossário:** [glossary-gitpr-split.md](glossary-gitpr-split.md)

## Contexto

O `gitpr split` promete uma coisa que nenhum outro fluxo do projeto promete: **os
arquivos em disco ao fim são byte a byte idênticos aos arquivos em disco no
início**. Ele redistribui trabalho não commitado entre commits; nunca o altera.

Essa promessa não é um detalhe de qualidade — é uma restrição de projeto que
decide três coisas, e nas três a resposta certa é *diferente* da que todos os
outros fluxos do GitPR dão:

1. **Qual diff capturar.** Todos os fluxos usam `get_git_diff()`, que passa `-w`.
2. **O que fazer com trabalho já estagiado.** A leitura intuitiva é "recusar até
   o índice estar limpo", ou "desestagiar antes de ler".
3. **Se aplicar smart excludes.** Os fluxos de revisão descartam lockfiles,
   gerados e binários antes de mandar o diff à IA; a spec §2 sugeria reusar isso.

As três alternativas são razoáveis fora deste contexto. Aqui as três estão
erradas, e o motivo é o mesmo nas três: elas são compatíveis com um diff que
*descreve aproximadamente* a árvore, e incompatíveis com um patch que precisa
*aplicar exatamente* sobre ela.

## Decisão

### 1. Captura própria: `SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")`

`get_split_diff()` em `core.py`, ao lado de `get_git_diff()`, e não um reuso dele.

- **`-w` é removido, e é a razão principal.** Com `-w`, uma diferença que é
  *apenas* espaço em branco é renderizada como contexto. A linha de contexto
  emitida pode então não bater byte a byte com o arquivo, e o patch construído a
  partir dela ou é recusado pelo `git apply` ou — pior — **aplica conteúdo que
  difere da árvore de trabalho**. O primeiro caso é uma falha barulhenta; o
  segundo quebra a garantia em silêncio, que é a única forma de quebra que este
  comando não pode aceitar.
- **`-U1` é pouco.** Uma linha de contexto deixa o `git apply --check` sem âncora
  suficiente para decidir.
- **`-B` decompõe reescritas** em exclusão mais adição — um hunk aplicável vira
  dois que precisam andar em lockstep.
- **`-M` fica, e é carga útil.** Sem detecção de renomeação, uma renomeação chega
  como exclusão mais adição, e a adição é um arquivo não rastreado — fora de
  escopo. O split commitaria a exclusão pura do caminho antigo enquanto o arquivo
  novo ficava sem rastreio ao lado: lê-se como perda de dados.
- **`--binary`** é inócuo para texto e é a única coisa que torna um binário
  alterado aplicável.

### 2. Capturar primeiro, desestagiar depois

O `--apply` **não** recusa um índice sujo e **não** desestagia antes de ler o diff.

A leitura intuitiva — limpar o índice antes de capturar — destrói o plano. Um
arquivo novo estagiado aparece em `git diff HEAD` **porque o índice o rastreia**;
o mesmo vale para uma renomeação estagiada. Desestagiar antes de capturar
transformaria ambos em arquivos não rastreados, fora de escopo, e o plano
silenciosamente perderia alterações que o usuário tinha.

Então a ordem é fixa: captura contra o índice como ele estiver, desestagia tudo
imediatamente antes do primeiro `git apply --cached`. É sólido porque **todo hunk
de um `git diff HEAD` carrega pré-imagem tirada de HEAD**, qualquer que seja o
estado do índice — e depois da desestagiação o índice *é* HEAD, então essas
mesmas pré-imagens aplicam limpo. Não há re-diff, não há aborto por divergência,
e não há plano que se remodele entre ser mostrado e ser aplicado.

A permissão para descartar esse staging é pedida **uma vez**, pela CLI, antes de
o applier rodar. O `--dry-run` nunca muta, em nenhum estado de índice.

### 3. Sem smart excludes

O split não descarta nada antes de mandar o diff à IA.

A exclusão não é gratuita aqui, ela é **errada**. Um lockfile e o seu manifesto
descrevem *uma* alteração; excluir o lockfile commita o manifesto sozinho e deixa
uma árvore em que os dois discordam — um commit intermediário quebrado, que é
exatamente o que o comando existe para evitar. A revisão pode descartar o
lockfile porque o produto dela é um parecer; o split não pode, porque o produto
dele é um commit.

O ruído é limitado por outros meios: truncagem por unidade dentro do prompt e o
teto `GITPR_SPLIT_MAX_HUNKS` sobre quantas unidades são enviadas.

## Consequências

- **O split não compartilha a captura de diff com o resto do projeto.** É código
  a mais, e é a decisão que mais parece duplicação num primeiro olhar. A resposta
  é que as duas capturas servem a propósitos diferentes: uma descreve a mudança
  para um modelo ler, a outra reconstrói a mudança para o git aplicar.
- **`--apply` descarta trabalho estagiado** depois de pedir permissão uma vez.
  A permissão é explícita e a captura aconteceu antes, então nada do que estava
  estagiado se perde do plano — mas um fluxo de script com `--yes` e
  `GITPR_SPLIT_REQUIRE_CONFIRMATION=false` descarta-o sem perguntar. É o preço
  de `--yes`, e está documentado.
- **Repositórios CRLF são recusados.** A captura com `text=True` mais o
  `rstrip("\r")` do `split_patch_sections` tira os CRs, então `--check` recusa
  esses arquivos e as suas unidades vão para as ungrouped. É falha alta e nunca
  aplicação corrupta — a troca foi aceita de propósito. Só vale revisitar (captura
  em bytes mais um parser que preserve CR, abandonando a regra do parser único) se
  isso morder um usuário real.
- **Um CRLF ou um binário num grupo pode forçar a absorção de arquivos inteiros**
  e, no limite, mandar as unidades para as ungrouped. O laço é limitado e sempre
  termina; nada é descartado e nada é meio-aplicado.
- **A garantia byte a byte é verificável e verificada.** O teste de aceitação
  compara um instantâneo de todos os arquivos (fora `.git`) antes e depois, e
  exige `git status` limpo ao fim.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Reusar `get_git_diff()` | O `-w` quebra a garantia byte a byte. Ver acima. |
| Capturar com `-U3` mas manter smart excludes | Um lockfile excluído ao lado do seu manifesto produz um commit intermediário quebrado, que é o defeito que o comando corrige. |
| Recusar quando o índice não está limpo | Destrói a visibilidade de arquivos novos e renomeações estagiados — eles só existem no diff porque o índice os rastreia. |
| Desestagiar antes de capturar | Mesmo defeito, com o agravante de já ter mutado antes de o usuário confirmar qualquer coisa. |
| Pedir permissão por grupo em vez de uma vez | N confirmações para N commits: o usuário responde a mesma pergunta três, cinco, dez vezes, e a décima vira um `y` reflexo. Uma confirmação que cobre o unstage inteiro é mais honesta do que N que ninguém lê. |
| Fazer rollback automático dos commits já criados numa falha | Os commits são reais e o `git reset` já existe. Desfazê-los automaticamente apagaria o único registro do que aconteceu, que é justamente o que o relatório existe para preservar. |
