# Documentação Técnica: Fecho Automático da Issue (`--close-issue`)

A TUI de Issues cria uma issue e depois fecha-se; o número que recebeu perde-se, e o próximo Pull Request é o primeiro sítio onde poderia ser fechada. O fecho automático de issue é a ponte entre esses dois momentos: um registo local leva o número adiante, e o fluxo de Pull Request oferece uma linha — `close #N` — que faz o forge fechar a issue quando o merge acontece.

Não é um gestor de issues. Não edita, lista, reabre nem etiqueta nada, e nunca fala com o forge por iniciativa própria: nada é registado até que uma issue seja criada pela TUI, e nada é decidido até que uma execução de Pull Request encontre um registo para ler.

---

## 1. Visão Geral

A funcionalidade atua em três superfícies:

1. **Criação.** `gitpr -is` abre a TUI de Issues; `F3` cria a issue no forge, e a mesma resposta é gravada em `.gitpr/conf/github.yml`.
2. **A execução do Pull Request.** O fluxo padrão `gitpr` lê o registo antes de gerar seja o que for, pergunta ao forge se a issue ainda está aberta e — no máximo uma vez — oferece adicionar a linha de fecho à descrição.
3. **Ajuda contextual.** `gitpr -h --close-issue` e `gitpr -h --no-close-issue` descrevem as duas flags e apontam para este documento.

### 1.1 Referência de Comandos

```bash
gitpr -is                      # Cria uma issue; F3 no GitHub regista-a
gitpr                          # O fluxo de PR lê o registo e pode oferecer close #N
gitpr --close-issue            # Aceita a linha sem perguntar (a issue ainda é verificada)
gitpr --no-close-issue         # Ignora a funcionalidade nesta execução
gitpr -h --close-issue         # O mesmo resumo, com ligação a este documento
```

| Comando | Escreve | O que faz |
|---|---|---|
| `gitpr -is` → `F3` | `.gitpr/conf/github.yml`, `.gitignore` | Cria a issue no GitHub e regista número, título, URL, data de criação e branch. `F2` (guardar localmente) não regista nada |
| `gitpr` (padrão) | O corpo do Pull Request, apenas quando a linha é aceite | Lê o registo, verifica a issue, pergunta no máximo uma vez |
| `--close-issue` | O mesmo acima | Aceita a linha sem a pergunta; a issue ainda é verificada |
| `--no-close-issue` | Nada | Nenhum registo é lido e nenhuma chamada ao forge é feita |
| `-h --close-issue` | Nada | Imprime a ajuda contextual |

As duas flags respondem à mesma pergunta, pelo que passar ambas é erro de utilização: a execução informa que não podem ser usadas em conjunto e sai com código `1`. A rejeição acontece antes do prompt de migração do ledger e da criação do ficheiro de projeto, porque um erro de utilização não pode perguntar nada nem escrever ficheiros. `-h` tem precedência sobre o erro, pelo que uma chamada de ajuda que carregue as duas flags ainda mostra as duas entradas.

---

## 2. O Fluxo, de Ponta a Ponta

Seis etapas, pela ordem em que a execução as percorre:

1. **Registo.** `F3` na TUI de Issues chama o forge, recebe a nova issue e entrega o resultado a `register_created_issue` (`src/ui/issue_app.py`). Só o GitHub é registado; uma falha aqui é engolida, porque a issue já existe no forge e a contabilidade local nunca deve transformar uma criação bem-sucedida em erro.
2. **Gate inicial.** `_prepare_close_issue` (`src/main.py`) corre no início do fluxo padrão de Pull Request — **antes** da verificação de ficheiros não commitados, antes da leitura do diff e antes de qualquer chamada de IA. Devolve imediatamente para `--no-close-issue`, para `GITPR_ISSUE_AUTOCLOSE=false` e quando o ficheiro não tem registo nem erro. Só depois desses gates constrói o registo — e construí-lo executa `git rev-parse` — e resolve o provider SCM.
3. **Decisão.** `resolve_close_issue` (`src/issue_autoclose/resolve_close_issue.py`) lê o registo uma vez, pergunta ao forge uma vez e pergunta ao utilizador no máximo uma vez. Os gates estão listados na secção 4.
4. **Montagem.** `insert_close_line` (`src/issue_autoclose/insert_close_line.py`) corre no único ponto em que a descrição é montada — depois do guia do revisor e antes do ficheiro `.md` local e do `pr_data`. O publicador da TUI e o publicador direto de `--no-edit` recebem, por isso, exatamente o mesmo corpo.
5. **Publicação.** A TUI (`PrPublishApp`) ou `_publish_pr_directly` envia o corpo ao forge.
6. **Limpeza.** O registo é removido apenas quando o corpo chegou realmente ao forge: `app.body_published` na TUI, ou `_publish_pr_directly` a devolver `True`. Uma pergunta recusada, `Esc`, uma publicação que falhou ou apenas abrir um Pull Request existente mantêm o registo para a execução seguinte.

A decisão é tomada antes de a descrição existir por um motivo: perguntar uma vez, no início, mantém a pergunta longe do ecrã do publicador e deixa a mesma resposta fluir para o ficheiro, para a TUI e para o publicador direto sem um segundo prompt.

### 2.1 Quanto Custa Cada Etapa

| Etapa | Disco | Rede | IA | Ignorada quando |
|---|---|---|---|---|
| 1. Registo | Escrita do registo, mais uma linha no `.gitignore` na primeira escrita | A chamada `create_issue` que já estava a acontecer | — | Issue criada fora da TUI, gravação local (`F2`) ou forge diferente de GitHub |
| 2. Gate inicial | Uma leitura do registo | `git rev-parse` apenas com a funcionalidade ligada | — | `--no-close-issue`, `GITPR_ISSUE_AUTOCLOSE=false`, nenhum registo |
| 3. Decisão | Uma leitura do registo | Uma `get_issue`; uma segunda chamada para a branch padrão apenas no caminho da pergunta | — | Qualquer um dos gates da secção 4 |
| 4. Montagem | — | — | — | Nenhuma decisão produzida |
| 5. Publicação | Os artefactos usuais do PR | A chamada usual de publicação | A geração usual do PR | — |
| 6. Limpeza | Uma remoção de ficheiro | — | — | Nada foi publicado |

Sem registo, a execução é o fluxo de todas as versões anteriores, byte a byte. O único trabalho extra é uma leitura de ficheiro.

---

## 3. O Ficheiro de Registo

O registo fica em `.gitpr/conf/github.yml`, ancorado na raiz do repositório. É estado local, não conteúdo do projeto: o ficheiro não deve ser commitado, e a primeira escrita acrescenta exatamente uma linha ao `.gitignore` do repositório.

A pasta em si não é ignorada por inteiro. O `gitpr.config.yml` vive no mesmo `.gitpr/conf/` e é versionado de propósito (ADR-015), pelo que a entrada de ignore nomeia especificamente o ficheiro de registo.

O registo guarda **uma issue de cada vez — a última vence.** Um fluxo de Pull Request único não precisa de mais: a issue documentada é a que acabou de ser criada. Criar uma segunda issue substitui a primeira, e não há histórico a consultar. É também por isso que o ficheiro não é uma cache de issues: é um marcador de página.

### 3.1 O Formato

```yaml
schema_version: 1
last_issue:
  repo: owner/name
  number: 42
  title: "Add login rate limit"
  url: https://github.com/owner/name/issues/42
  created_at: '2026-11-03T14:22:07'
  branch: feat/login-rate-limit
```

`schema_version: 1` é a única versão que este módulo lê e a única que escreve. Um ficheiro com qualquer outra versão é reportado como ilegível em vez de ser adivinhado.

`load()` valida cada campo antes de o devolver:

- `repo`, `title`, `url` e `created_at` têm de ser texto não vazio;
- `number` tem de ser um inteiro positivo, e um booleano é rejeitado mesmo que o Python o trate como inteiro;
- `branch` é opcional e pode estar vazio.

Um **ficheiro ausente não é erro** — significa "nenhuma issue registada". Um ficheiro ilegível é erro, devolvido como dado (`RegistryLoad.error`) para que o comando dono do ecrã decida como reportá-lo. O módulo nunca imprime.

### 3.2 Escritas, Corrupção e `.gitignore`

`record()` escreve num ficheiro temporário irmão e move-o para o lugar com `os.replace`, pelo que uma execução interrompida nunca deixa um registo truncado. Um ficheiro que `load()` reportou como corrompido é simplesmente substituído pelo `record()` seguinte: um marcador quebrado vale menos que um novo.

Antes da primeira escrita, `record()` pergunta `git check-ignore -q .gitpr/conf/github.yml`. Só quando o git ainda não ignora o ficheiro é que acrescenta a entrada ao `.gitignore`, e apenas uma vez. Fora de um repositório git, ou quando o `.gitignore` não pode ser escrito, nada muda e o registo continua válido — o utilizador pode acrescentar a linha à mão.

`clear()` remove o ficheiro e devolve `False` quando não havia o que remover, pelo que o chamador nunca precisa de distinguir "removido" de "não existia". Qualquer falha real de I/O torna-se `IssueRegistryError`; os chamadores que correm dentro do fluxo de Pull Request apanham-na e seguem em frente, porque o estado local não pode quebrar uma publicação.

---

## 4. A Decisão: Gates pela Ordem

A ordem faz parte do contrato. Todos os gates que não custam nada correm antes de qualquer acesso a disco ou rede, e só uma issue ainda aberta chega à pergunta. `skipped_reason` é o vocabulário que a métrica `issue_autoclose` reporta (secção 8).

| # | Gate | `skipped_reason` | Custo | Limpa o registo |
|---:|---|---|---|---|
| 1 | `--no-close-issue` foi passado | `flag-disabled` | Nenhum | Não |
| 2 | `GITPR_ISSUE_AUTOCLOSE=false` | `disabled` | Nenhum — o fluxo de PR devolve antes de chamar o caso de uso; a verificação permanece como defesa em profundidade para chamadores que controlam a chave | Não |
| 3 | O forge não é GitHub | `not-github` | Nenhum | Não |
| 4 | O registo existe mas não pode ser lido | `registry-error` | Uma leitura de ficheiro, um aviso | Não |
| 5 | Não há registo | `no-record` | Uma leitura de ficheiro | Não |
| 6 | O registo pertence a outro repositório | `other-repo` | Uma leitura de ficheiro | Não (ADR-007) |
| 7 | `get_issue` responde 404 | `issue-missing` | Uma chamada HTTP | **Sim** |
| 8 | `get_issue` falha por outro motivo | `verify-failed` | Uma chamada HTTP, um aviso | Não — mantido para a execução seguinte |
| 9 | O número é um Pull Request | `issue-is-pr` | Uma chamada HTTP | **Sim** |
| 10 | A issue não está `open` | `issue-not-open` | Uma chamada HTTP | **Sim** |
| 11 | Não há terminal e `--close-issue` não foi passado | `no-tty` | Uma chamada HTTP | Não |
| 12 | `--close-issue` foi passado | — (uma decisão é tomada) | Uma chamada HTTP, sem pergunta | Não |
| 13 | O utilizador responde à pergunta | `declined` quando a resposta é não | Uma segunda chamada HTTP para a branch padrão, só neste caminho | Não, em caso de recusa |

Dois detalhes importam mais que a tabela:

- **A verificação de Pull Request vem antes da verificação de estado.** O endpoint de issues do GitHub também responde a números de Pull Request, pelo que `is_pull_request` é examinado primeiro. Um número que se revela um Pull Request não é uma issue que foi fechada — é um registo que nunca poderá ser usado, e é esquecido.
- **A comparação de repositório ignora maiúsculas e minúsculas.** Os nomes de owner e repositório no GitHub não distinguem maiúsculas de minúsculas, pelo que `matches_repo()` os compara com `casefold()`. Um registo de outro repositório não é assunto deste fluxo, e é deliberadamente mantido em vez de limpo.

### 4.1 A Pergunta e o Aviso de Branch de Destino

A pergunta é:

```text
Issue #42 – Add login rate limit is open. Add "close #42" to the end of the pull request description?
```

Tem "sim" como padrão. `ask` é chamado fora de todos os blocos `try`: o `Abort` do `click` é um `RuntimeError`, e `Ctrl+C` tem de deixar o fluxo exatamente como qualquer outro prompt, em vez de ser engolido como funcionalidade ignorada.

No caminho da pergunta — e só nele — o fluxo também procura a branch padrão do repositório. Quando o destino configurado difere da padrão, a pergunta transporta uma linha extra:

> Warning: the pull request targets `"develop"` but the default branch is `"main"`. GitHub only closes the issue when the merge lands on the default branch.

Uma procura de branch padrão que falha ou volta vazia degrada em silêncio. O forge só diz "desconhecido", e um aviso que o chamador não consegue formular corretamente é pior que nenhum aviso.

### 4.2 O Que o Resultado Transporta

`CloseIssueOutcome` tem cinco campos, e todos podem ser ignorados em segurança:

| Campo | Significado |
|---|---|
| `decision` | O número, o título e a linha exata a inserir — `None` quando nada foi oferecido ou o utilizador recusou |
| `warning` | Uma mensagem de uma linha para imprimir; nunca definida quando uma pergunta foi feita |
| `skipped_reason` | O gate que encerrou a decisão; vazio quando uma decisão foi tomada |
| `asked` | Se o utilizador viu realmente uma pergunta |
| `accepted` | Se a linha será inserida |

Uma decisão nunca limpa o registo — limpar é tarefa do chamador, depois de o Pull Request existir (ADR-007), porque uma publicação que falhou precisa de manter o registo para a execução seguinte. `target_branch_warning` é repetido na decisão apenas para que o chamador o mantenha junto da linha; já fez parte da pergunta e não deve ser impresso de novo.

---

## 5. Inserção e Idempotência

O corpo é montado uma única vez. `insert_close_line` é chamado desse ponto e de nenhum outro, pelo que nenhum publicador pode receber um corpo sem a linha ou com a linha adicionada duas vezes.

Uma decisão `None` devolve o corpo inalterado. Caso contrário, a linha é acrescentada como parágrafo próprio:

```text

close #42
```

A função é idempotente entre as grafias das palavras-chave. O GitHub aceita `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` e `resolved`, sem distinguir maiúsculas de minúsculas, e a mesma issue pode ser nomeada como `owner/repo#42`. Se o corpo já menciona **o mesmo número de issue** em qualquer dessas formas, nada é acrescentado — o forge fechará a issue de qualquer maneira, e uma segunda referência seria apenas ruído.

O selo é anexado depois e sempre no fim do corpo, pelo que acrescentar aqui é o que deixa a linha de fecho imediatamente antes dele. Este módulo nunca precisa de procurar um selo.

---

## 6. O Contrato SCM e os Outros Forges

Três métodos de `ScmProvider` existem para esta funcionalidade:

| Método | GitHub | Classe base |
|---|---|---|
| `get_issue(repo, number, timeout=5)` | `GET /repos/{owner}/{repo}/issues/{n}` | Levanta `ScmNotSupportedError` |
| `get_default_branch(repo, timeout=5)` | `GET /repos/{owner}/{repo}` → `default_branch` | Levanta `ScmNotSupportedError` |
| `closing_line(number)` | `close #N` | Levanta `ScmNotSupportedError` |

Nenhum dos três é abstrato. É deliberado: GitLab, Bitbucket e Azure DevOps continuam a compilar e continuam a funcionar em todas as outras funcionalidades, e o fecho automático é exclusivo do GitHub (ADR-003). O chamador lê `ScmNotSupportedError` como "funcionalidade inativa", nunca como falha.

`closing_line` é sintaxe do forge, não uma string genérica. O GitHub lê `close #N`; uma linha construída em qualquer outro sítio poderia estar escrita corretamente e ainda assim não significar nada para o forge. O timeout curto de cinco segundos também faz parte do contrato: a resposta só decide se uma pergunta será feita, e um forge lento não pode segurar o fluxo de Pull Request.

`provider_is_github()` é verificado antes de tudo isto, pelo que os outros forges ignoram a funcionalidade sem leitura de disco e sem aviso.

---

## 7. Configuração

Duas variáveis em `~/.gitpr/.env`, também editáveis em `gitpr config` na secção **Issue**. Nenhuma delas é escrita automaticamente.

| Chave | Padrão | Efeito |
|---|---|---|
| `GITPR_ISSUE_AUTOCLOSE` | `true` | Apenas `false`, `0`, `no`, `off` ou `n` desligam a funcionalidade; qualquer outro valor — incluindo um que não possa ser interpretado — mantém-na ligada |
| `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` | `5` | Segundos de espera pelo forge ao ler a issue. Zero, número negativo ou valor não inteiro voltam para `5` |

A precedência é:

```text
--no-close-issue  >  GITPR_ISSUE_AUTOCLOSE=false  >  --close-issue
```

`--close-issue` **não sobrepõe** `GITPR_ISSUE_AUTOCLOSE=false`. A chave é a decisão do utilizador sobre a máquina, e uma flag por execução que a revertesse em silêncio tornaria a configuração indigna de confiança. Não existe configuração por repositório para esta funcionalidade.

---

## 8. Métricas

Todas as decisões que o caso de uso alcança são reportadas uma vez ao ledger local (`gitpr metrics`) como uma linha `issue_autoclose`:

| Campo do payload | Valor |
|---|---|
| `command` | `issue_autoclose` |
| `asked` | Se a pergunta foi mostrada |
| `accepted` | Se a linha será inserida |
| `skipped_reason` | O gate da secção 4, ou vazio quando uma decisão foi tomada |

Os curto-circuitos do próprio helper — flag desligada, configuração desligada, nenhum registo, nenhum provider — nunca engajaram a funcionalidade e ficam fora do ledger. Não são decisões; são execuções em que não havia nada a decidir.

Os campos viajam no payload JSON. A exportação CSV transporta as colunas que o ledger define para todos os comandos, não um formato por funcionalidade.

---

## 9. Limites, Ditos com Clareza

- **Uma issue de cada vez.** Criar uma segunda issue substitui o primeiro registo; a primeira já não pode ser fechada por esta funcionalidade.
- **O registo só acontece na TUI.** Uma issue criada com `gh`, pela API ou por qualquer outro caminho é invisível para a funcionalidade.
- **Apenas GitHub.** Os outros forges ignoram a funcionalidade em silêncio, sem aviso e sem registo.
- **O registo é por clone.** É estado local e não é commitado, pelo que o clone de um colega não o herda, e um clone novo começa sem nada a fechar.
- **Apagar a linha no editor não mantém o registo.** Se o corpo foi publicado, o registo é limpo porque a publicação transportou o corpo — mesmo que a linha tenha sido editada para fora antes do envio.
- **Atualizar um Pull Request existente também limpa o registo.** A TUI reporta "created" para esse caminho também; o que decide a limpeza é o corpo ter chegado ao forge.
- **As palavras-chave são só em inglês.** `close`, `fix` e `resolve` e as suas flexões são o que o GitHub lê; um corpo que diga `fecha #42` não é uma referência de fecho, e a linha será acrescentada ao lado dele.
- **A verificação de estado confia no forge.** Uma issue fechada entre a leitura e o merge não pode ser detetada aqui; a linha de fecho simplesmente já não tem o que fechar.

---

## 10. Leitura Relacionada

- `docs/issue-tui-help.md` — a TUI de Issues, `F2`/`F3` e o resumo curto desta funcionalidade para o utilizador.
- `docs/config-tui.md` — o ecrã de configuração, incluindo a secção **Issue**.
- `docs/metricas-telemetria.md` — o ledger local e a métrica `issue_autoclose`.
- `docs/scm-multiforge.md` — a abstração de providers e por que só o GitHub implementa o fecho.
- `docs/github-pat-integration.md` — o token de que `F3` precisa para criar a issue.
- `docs/pull-request-publication.md` — o publicador que recebe o corpo montado.
- `docs/specs/issue-autoclose/adrs/ADR-001` a `ADR-007` — as decisões por trás do registo, dos gates, da inserção e da limpeza.
- `CONTEXT.md` — os termos do glossário *Issue registry*, *Closing line* e *Close issue decision*.
