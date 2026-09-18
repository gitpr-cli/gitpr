# Documentação Técnica: Revisão de Pull Request Remoto (gitpr review-pr)

`gitpr review-pr <number>` revisa um pull request que já está aberto na forge, buscando o diff direto da API. A branch em revisão não precisa existir na sua máquina — você nunca faz checkout dela, nunca a baixa e nunca toca na sua árvore de trabalho. É o modo para quem foi convidado a revisar o pull request de outra pessoa, onde o código a ler está do outro lado da rede.

A revisão em si não é um segundo motor: é o `gitpr -r` com o diff vindo de outro lugar. A mesma chamada de IA, a mesma skill `.gitpr.review.md`, as mesmas regras do linter, o mesmo arquivo de relatório e o mesmo cache — por isso uma revisão remota e uma local do mesmo diff leem de forma idêntica.

---

## 1. Visão Geral

O subcomando é uma adição à CLI, não uma mudança nela: toda opção legada mantém seu significado, e os fluxos locais (`gitpr -r`, `gitpr -f`, `gitpr fix`) não são afetados por ele. Ler é o padrão — sem nenhuma flag, a forge é apenas *lida*, e nada é publicado em lugar algum.

### 1.1 Referência de Comando — `gitpr review-pr`

Todas as opções do subcomando, como mostrado por `gitpr review-pr -h` (ou `--help`):

```bash
gitpr review-pr 123                    # revisa o pull request e grava o .txt
gitpr review-pr 123 --provider deepseek  # revisa com um motor de IA específico
gitpr review-pr 123 --post-comment     # publica também a revisão no pull request
```

| Opção | Descrição |
| --- | --- |
| **`<number>`** | O número do pull request como mostrado na forge (`123`). Obrigatório, e inteiro — um argumento não numérico é erro de uso |
| **`--provider <name>`** | Força o motor de IA desta execução (`gemini`, `deepseek` ou `ollama`). Sem ele, o padrão configurado é usado |
| **`--post-comment`** | Publica a revisão como comentário no pull request. **Sem ele, a forge nunca é escrita** |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | O diff servido pela API da forge para aquele pull request — nunca a sua árvore de trabalho |
| **Forge** | A que o `gitpr --init` configurou (GitHub, GitLab, Bitbucket). O Azure DevOps é recusado — ver §3 |
| **Chamada de IA** | Uma chamada, no modelo avançado do provedor configurado, com cache em `review/` como qualquer outra chamada do GitPR |
| **Arquivos gravados** | `{branch}_{datetime}_PR_REVIEW.txt` na pasta de relatórios (`OUTPUT_FILE_NAME_REVIEW`) |
| **Publicado** | Nada, a menos que `--post-comment` seja informado |
| **Árvore local** | Nunca lida, nunca verificada quanto a arquivos não preparados, nunca modificada — sem checkout, sem fetch, sem troca de branch |
| **Código de saída 1** | Nenhuma forge configurada, forge sem diff revisável, pull request inexistente ou não aberto, diff vazio ou todo filtrado, API inalcançável, nenhuma chave de IA |

---

## 2. O Que É uma Revisão Remota

### 2.1 O Diff Vem da API

A forge é consultada primeiro pelos metadados do pull request, depois pelo seu diff:

| Passo | O que ele estabelece |
| --- | --- |
| `get_pull_request` | Que o número existe, em que estado está e quais branches ele une |
| `get_pull_request_diff` | O diff unificado a revisar |

Resolver o número diretamente é o que torna "não existe" distinguível de "foi mesclado semana passada": listar pull requests abertos devolve apenas os abertos, então um número ausente dessa lista poderia ser qualquer uma das duas coisas. Os metadados também fornecem as duas branches que o relatório precisa nomear.

A consulta de metadados não é enfeite — é o que impede um número obsoleto de gastar tokens (§4.2).

### 2.2 O Diff É Normalizado

Um diff que nunca passou pelo git chega na forma que a forge escolheu enviar. Três coisas são resolvidas antes de a IA vê-lo:

| Passo | Por quê |
| --- | --- |
| **Fins de linha unificados em LF** | GitLab e Bitbucket servem CRLF em branches escritas no Windows, e o chunker divide em `^diff --git a/`, que um `\r` perdido desalinha |
| **O conteúdo é confirmado como diff** | Um provedor que declara servir diffs mas responde com prosa para aqui, em vez de ser revisado como se fosse código |
| **Smart excludes aplicados** | Os lockfiles e assets minificados são filtrados do diff *revisado*, não de um diff local (§2.3) |

### 2.3 O Smart Excludes Roda em Python Aqui

Todo diff local recebe o smart-excludes aplicado pelo próprio git, como pathspecs `:(exclude)`. Um diff que chega pela API nunca passa pelo git, então os mesmos padrões são aplicados em Python, seção por arquivo, e os arquivos descartados são nomeados em um aviso:

```text
⚠️  3 file(s) skipped by the smart excludes: package-lock.json, poetry.lock, dist/app.min.js
```

A lista de padrões é a mesma que os fluxos locais usam (`~/.gitpr/conf/gitpr.smart-excludes.json`), e o `GITPR_SKIP_SMART_EXCLUDES` também a desativa aqui. Um pull request em que todos os arquivos são lockfile não tem nada restante para revisar, e o comando diz isso em vez de enviar um diff vazio ao modelo.

### 2.4 O Cache É Separado do da Revisão Local

A chave do cache MD5 é construída a partir do prompt, e um prompt é construído a partir do diff — então uma revisão remota de uma branch que por acaso está em checkout local produziria um prompt byte a byte idêntico e seria respondida pela revisão local em cache. Por isso o fluxo remoto acrescenta um escopo à chave de cache:

```text
::diff-source::pr-123
```

O escopo é acrescentado **somente** à chave de cache — nunca ao texto enviado à IA. A consequência para quem já usa o GitPR é zero: os fluxos locais passam um escopo vazio, então suas chaves continuam byte a byte iguais às de sempre, e nenhuma entrada de cache existente é invalidada.

### 2.5 O Diff Revisado É Registrado

A revisão é guardada no cache junto do diff que a produziu, e é isso que permite ao `gitpr fix` corrigir a revisão que foi de fato revisada, em vez de recalcular um diff da sua árvore. Numa revisão remota isso não é uma conveniência, mas a única fonte correta: a branch pode não existir localmente. Veja a [documentação do Comando de Correção](fix-command.pt_br.md) para o que o lê de volta.

O registro é arquivado sob o repositório e a branch em que **você está** — os mesmos campos que toda revisão em cache carrega, porque é o que o `gitpr fix` resolve para encontrá-la. As branches do próprio pull request são registradas dentro da entrada (como o `{branch}` do nome do relatório e na origem do diff), mas não a endereçam: revisar o PR #123 estando em `develop` arquiva a revisão sob `develop`.

---

## 3. Quais Forges Podem Ser Revisadas

Uma revisão precisa de um diff unificado, e nem toda forge serve um.

| Forge | Revisão remota | Por quê |
| --- | --- | --- |
| **GitHub** | Sim | `GET /repos/{owner}/{repo}/pulls/{n}/files` com `Accept: application/vnd.github.diff` |
| **GitLab** | Sim | `changes[].diff` por arquivo, com os cabeçalhos de arquivo sintetizados (§3.1) |
| **Bitbucket** | Sim | `GET .../pullrequests/{n}/diff` |
| **Azure DevOps** | **Não** | Sua API devolve uma lista de arquivos alterados com contagem de linhas, não um diff unificado. Recusado antes de qualquer chamada de rede, com mensagem apontando para a revisão local |

A capacidade é declarada pelo próprio provedor (`supports_reviewable_diff` na `ScmProvider`), então uma forge adicionada depois declara sua própria resposta em vez de ser adivinhada. Atrás dessa flag há uma segunda rede, mais barata: o conteúdo buscado é verificado quanto a estrutura real de diff, então um provedor que declara a capacidade e depois responde com um resumo de arquivos é pego de qualquer forma (§2.2).

### 3.1 GitLab: Os Cabeçalhos de Arquivo São Sintetizados

A API do GitLab devolve o campo `diff` de cada arquivo alterado como um hunk puro, com a identidade do arquivo em campos separados `old_path` / `new_path`. Lido como está, a revisão receberia hunks anônimos — a IA não poderia dizer a que arquivo uma alteração pertence, e nem o filtro de smart-excludes nem o chunker funcionariam, já que ambos se apoiam na linha `diff --git a/…`. O provedor reconstrói esse cabeçalho antes de cada hunk:

```diff
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,2 @@
```

O GitLab também sinaliza quando truncou um diff por exceder o limite de tamanho da API (`overflow: true`). Um diff truncado não é um diff, então ele é recusado de imediato com uma mensagem dizendo ao revisor para revisar aquele merge request localmente, em vez de ser revisado pela metade e o resultado publicado como se fosse inteiro.

---

## 4. O Relatório, os Avisos e as Falhas

### 4.1 O Relatório

A saída é o mesmo arquivo que a revisão local grava, pelo mesmo código de renderização — bloco do linter em cima, revisão da IA embaixo — com uma diferença no nome: o espaço `{branch}` carrega a branch de **origem** do pull request, sanitizada para o sistema de arquivos (`feature/login` vira `feature-login`), porque o relatório pertence à revisão que está sendo revisada e não à branch que por acaso está em checkout. Um pull request sem nome de branch cai em `pr-123`.

```text
✅ Code Review successfully generated: 'feature-login_20260917143210_PR_REVIEW.txt'
```

Nada mais é impresso: a revisão nunca é ecoada no terminal, exatamente como nos fluxos locais. O caminho do relatório é configurado por `OUTPUT_FILE_NAME_REVIEW`, a mesma variável que a revisão local usa — o modo remoto não introduz configuração nova.

### 4.2 Recusas Que Não Custam Nada

Tudo o que o usuário pode resolver é recusado **antes** de a IA ser chamada, então um número errado, um pull request fechado ou uma forge com o token errado não custam token algum:

| Situação | Mensagem |
| --- | --- |
| A forge não serve um diff revisável | `{provider} does not serve a reviewable diff: … Review this pull request locally, or use a forge that serves diffs.` |
| O número não existe | `Pull request #123 was not found in {repo}.` |
| O token não consegue lê-lo (401/403) | `No permission to read pull request #123 in {repo}. Check the token configured for {provider} (gitpr --init).` |
| Está fechado ou mesclado | `Pull request #123 is not open (state: closed). Only open pull requests can be reviewed.` |
| O diff voltou vazio | `Pull request #123 has no diff to review.` |
| Voltou como resumo de arquivos | `{provider} returned a file summary instead of a diff for pull request #123. It cannot be reviewed.` |
| Todos os arquivos casaram com o smart excludes | `Every file of pull request #123 matches the smart excludes — nothing left to review.` |
| O modelo não devolveu nada utilizável | `The AI returned no review for pull request #123.` |

Os quatro estados abertos entre as forges suportadas — GitHub `open`, GitLab `opened`, Azure `active`, Bitbucket `OPEN` — são comparados sem diferenciar maiúsculas, então uma única verificação cobre todos. Um provedor que não reporta estado algum é deixado passar, em vez de recusado por um campo que nunca prometeu.

### 4.3 Avisos

Avisos são coisas que o usuário deve saber e que não interromperam a execução. Eles são impressos antes do relatório e, com `--post-comment`, publicados dentro do comentário — quem lê no pull request merece saber que a revisão pulou três lockfiles.

| Aviso | Quando |
| --- | --- |
| `{count} file(s) skipped by the smart excludes: {files}` | O filtro descartou ao menos um arquivo |
| `Large diff: processed in {count} batches (map-reduce).` | O diff é grande o bastante para o motor dividi-lo |

A contagem de lotes é perguntada ao chunker, e não observada na linha de terminal do motor, porque a tool MCP não tem terminal de onde lê-la. Um chunker que falha ao responder não é uma falha: o aviso é uma cortesia e nunca o motivo de uma execução morrer.

### 4.4 Uma Execução Que Falha Não Grava Nada

Qualquer falha sai com código 1, imprime o motivo em stderr e **não grava relatório** — um `.txt` em disco significa que uma revisão existe, e "a revisão falhou" nunca pode parecer "a revisão não encontrou nada". O comando também nunca tenta de novo: o pipeline levanta antes do motor, então não há uma segunda chamada a pagar.

---

## 5. Publicação — `--post-comment`

Com `--post-comment`, a revisão é publicada como comentário no próprio pull request. É um comentário, criado depois que a revisão teve sucesso e o linter rodou, e é **sempre um comentário novo** — uma revisão anterior da mesma ferramenta fica onde está, porque sobrescrever um comentário ao qual alguém pode ter respondido não é uma decisão deste comando.

O corpo é o corpo do relatório mais um rodapé:

```markdown
## 🚨 Local Static Analysis Alerts (YAML Rules)

- 🚨 console.log usage detected in app.js (Line 42)

---

## 🤖 AI Code Review

…

---

*Automated review by GitPR 1.1.0 — AI provider: Gemini. AI-generated content: verify before acting on it.*
```

O rodapé existe porque o comentário cai no pull request de **outra pessoa**: quem nunca rodou o comando não tem outra forma de saber que um modelo o escreveu. Os alertas são compostos pela mesma função que compõe o `.txt`, então o arquivo e o comentário nunca podem ler de formas diferentes.

Nenhum SHA de commit aparece nele. O resultado da forge não carrega nenhum, e inventar um em um comentário público seria pior do que omiti-lo.

Se a revisão falha, nada é publicado — o comentário só existe depois de uma revisão que produziu algo. Se o *comentário* falha (um token que lê mas não escreve), o erro surge como erro de forge e a execução sai com código 1: a revisão foi produzida, mas não foi publicada.

---

## 6. Template de Skill — `.gitpr.review.md`

A revisão remota usa a mesma instrução de sistema que a local: `.gitpr.review.md` (persona e foco da revisão), baixada por `gitpr --skill` — ciente do idioma e sem sobrescrever um arquivo existente. Não há um tipo de skill específico do remoto; uma revisão que lesse diferente dependendo de onde o diff veio anularia o propósito de compartilhar o motor.

---

## 7. Integração MCP

`review_remote_pr` é a 14ª tool MCP e é **somente leitura**: ela revisa um pull request aberto e devolve a revisão e os alertas do linter, e não tem como publicar nada. Não existe argumento `post_comment`, de propósito — uma tool que um agente chama por conta própria não pode ser capaz de escrever no pull request de alguém.

```json
{"status": "success", "pr_number": 123, "pr_url": "…", "head_branch": "feature/login",
 "base_branch": "main", "origin": "remote_pr", "linter": {…}, "warnings": [], "review": "…"}
```

Diferente da CLI, ela não grava `.txt` — tools MCP não gravam artefatos — e resolve a forge por conta própria, então um repositório sem forge configurada responde com um erro JSON apontando o `gitpr --init` em vez de uma mensagem de terminal. O status é `error` com um `message` para cada recusa da §4.2. Veja a [documentação de Integração MCP](mcp-integration.pt_br.md).

---

## 8. Variáveis de Ambiente

A revisão remota **não introduz configuração nova**. Ela lê o que a revisão local já lê:

| Variável | Propósito |
| --- | --- |
| `GITPR_SCM_PROVIDER` / `GITPR_SCM_TOKEN` / `GITPR_SCM_TOKEN_ENCRYPTED` | A forge e seu token, configurados pelo `gitpr --init` |
| `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` | Extras da forge (GitLab auto-hospedado, Azure, Bitbucket) |
| `OUTPUT_FILE_NAME_REVIEW` | Nome do relatório (padrão `{branch}_{datetime}_PR_REVIEW.txt`) |
| `DEFAULT_AI_PROVIDER` | Motor de IA usado quando `--provider` não é informado |
| `GITPR_SKIP_SMART_EXCLUDES` | Desativa o filtro de smart excludes, local ou remoto |

> **Nota:** Veja também a [documentação de Revisão de Código por IA](code-review-ia.pt_br.md) para os modos de revisão e a [documentação do Comando de Correção](fix-command.pt_br.md) para o que consome o diff registrado.
