# Glossário — Sugestão de Revisores (GitPR)

> Vocabulário canônico da feature de sugestão de revisores para PRs.
> Mantido junto da [spec](20260904_skill_gitpr_reviewer_suggestion_spec.md); a
> lista de desvios aprovados vive no [ADR-002](ADR-002-reviewer-suggestion.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **sugestão de revisores** | Cálculo, na publicação de um PR (fluxo TUI default), dos prováveis revisores a partir de quem mais tocou as linhas adicionadas pelo diff na working tree. Habilitada por default; opt-out por `--no-suggest-reviewers` ou `GITPR_SUGGEST_REVIEWERS=false`. |
| **BlameHit** | Um registro de `git blame --line-porcelain` sobre uma faixa de linhas: hash do commit, autor (nome + e-mail), `author-time` e o número da linha new-side. |
| **linha adicionada (added line)** | Linha `+` do diff (new-side). Só linhas adicionadas entram na atribuição de autoria — linhas removidas e contexto são ignorados. |
| **Not Committed Yet (NCY)** | Linha ainda não commitada (trabalho em andamento na working tree): o blame devolve o hash `0000000000000000000000000000000000000000`. Nunca gera candidato — é autoria do próprio autor do PR. |
| **autor do PR (pr author)** | Identidade do usuário publicando (e-mail do git + nome). Excluído do ranking (flag `excluded_pr_author` no resultado) mesmo quando domina o diff. |
| **candidato (ReviewerCandidate)** | Autor agregado com direito a ser sugerido: `author_name`, `author_email` (normalizado), `touched_lines`, `touched_files`, `last_touch_date` (ISO do `author-time` máximo) e `last_commit_hash` (hash do commit **mais recente**, insumo da resolução por commit — vazio quando não há hit utilizável). |
| **ranking (score)** | `0.5·(linhas/total) + 0.3·(arquivos/total) + 0.2·recência`, com recência `1/(1+dias/90)` (half-life de 90 dias). Pesos e half-life são constantes de código. Desempate por `touched_lines`; trunca em `top_n` (default 3). |
| **bot** | Conta não-humana excluída do ranking: sufixo `[bot]` no nome ou na local-part do e-mail, ou e-mail na lista `DEFAULT_BOT_EMAILS` (dependabot, actions, github-actions…). **Nunca** por domínio `users.noreply.github.com` — é o e-mail padrão de usuários reais. |
| **handle** | Login do GitHub (1–39 chars, `[A-Za-z0-9-]`). É o **único** valor que `requested_reviewers` aceita. O campo da TUI aceita login, nome ou e-mail, mas nada é submetido sem antes virar handle: um nome enviado como se fosse login recebe `201` e não anexa ninguém. |
| **identidade (identity)** | Qualquer das três formas de nomear uma pessoa: login, nome de exibição ou e-mail. `normalize_identity(value)` = `strip` + `casefold` — é a normalização usada para casar o que foi digitado com os candidatos (casamento **exato**, sem fuzzy). `identity_key(name, email)` é a chave de agrupamento do candidato (e-mail normalizado; sem e-mail, `name:{nome normalizado}`). |
| **resolução por commit** | Via **primária** de resolução: `GET /repos/{o}/{r}/commits/{sha}` do hit de blame mais recente devolve `author.login` — a conta ligada ao e-mail do commit. É o único caminho que também enxerga e-mails corporativos. Vem `null`/`{}` quando não há conta ligada → cai para o `email_to_handle`; qualquer falha do lookup também cai (as duas vias são tentadas de forma independente). |
| **read-back** | Leitura de volta, no corpo do `201`, dos logins que o forge **realmente anexou** (`requested_reviewers`). É o que distingue "o forge aceitou o pedido" de "o revisor está no PR": login inexistente recebe `201` e não anexa ninguém, então o retorno vazio é o sinal de que o pedido se perdeu. |
| **item descartado (dropped)** | Valor do campo que não resolveu para nenhum handle. Nunca é enviado como veio: entra em `ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e aparece no `NoticeScreen` e no `final_message`. |
| **users.noreply.github.com** | Domínio de e-mail privado do GitHub: `{id}+{login}@users.noreply.github.com` (ou `{login}@` em contas antigas). Parseado em handle sem rede; bots como `dependabot[bot]@…` falham o charset do login → `None`. |
| **email_to_handle** | Mapeamento best-effort nunca-bloqueante no provider GitHub: (a) parse do noreply; (b) fallback `GET /search/users?q={email} in:email` — que só encontra e-mail **público**. É a **segunda** via de resolução (depois do commit) e a última antes do hint "nenhum login encontrado". Candidato sem handle aparece na TUI (nome + e-mail) sem prefill. |
| **requested_reviewers** | Endpoint GitHub pós-criação (`POST /repos/{o}/{r}/pulls/{n}/requested_reviewers`, expected `{201}`, json `{"reviewers": [...]}`). Não existe no create do PR — attach sempre após o PR existir. Forges sem equivalente → `ScmNotSupportedError` (método não-abstrato na base). O método devolve a lista dos logins **realmente anexados** (read-back); lote com usuário inelegível → `422` tudo-ou-nada. |
| **attach** | Submissão dos valores do campo da TUI ao PR recém-criado (ou atualizado), **depois** de resolvidos para handles. GitHub-only; **nunca fatal**: o que não resolve é descartado com motivo e o que o forge não anexou é detectado pelo read-back. Lote recusado com `422` é reenviado **um a um**. Aviso pendente → `NoticeScreen` (modal que precisa ser fechado) **e** linha no `final_message`; o PR permanece criado. |
| **view (reviewer_suggestion)** | Dict repassado por `main.py` à TUI: `{"handles", "lines", "submittable", "note", "resolutions"}`. `handles` = logins resolvidos (prefill do `Input`); `resolutions` = `list[ResolvedReviewer]` (nome/e-mail/login), usado no attach para não refazer rede. `submittable=False` (forges não-GitHub) → sem `Input`, só hint + nota "exibido localmente". |
| **ResolvedReviewer** | Candidato com a identidade resolvida: `name`, `email`, `login` (**pode ser vazio** — é o caso "exibido, não envio"). `key` = `identity_key(name, email)`, a mesma chave do `who_map`. |
| **ResolutionOutcome** | Retorno da resolução do que foi digitado: `logins` (o que será submetido, já deduplicado) + `dropped` (valor, motivo). Contrato "nunca levanta": falha de lookup vira item descartado, não exceção. |
| **NoticeScreen** | Modal novo do PR Publisher para "publicado, com ressalvas": título + mensagem + **um** botão (`Close`), sem Yes/No. Empilhado no caminho de aviso; o callback só continua para o prompt de merge depois de fechado. Não reusa `CommitConfirmScreen` (semântica Yes/No) nem o modal de erro (oferece "Try Again" inexistente). |
| **warning i18n** | Degradação documentada do use case: diff sem linhas adicionadas, arquivo sem histórico de blame (novo/binário), estouro do teto anti-abuso por arquivo (`MAX_RANGES_PER_FILE = 40`). Nunca vira exceção. |

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Significado |
|---|---|
| `GITPR_SUGGEST_REVIEWERS` | Liga/desliga o cálculo (default `true`; valores falsy: `false`, `0`, `no`, `off`, `n`). |
| `GITPR_REVIEWER_SUGGESTION_TOP_N` | Quantos candidatos sugerir (default `3`; inválido/≤0 → 3). |
| `GITPR_REVIEWER_SUGGESTION_EXCLUDED` | CSV opcional de e-mails/nomes a excluir além do autor do PR e dos bots. |

## Notas de fidelidade

- **Blame casa com o diff**: `get_git_full_diff()` compara um ancestral
  (`origin/main`) contra a **working tree** (inclui staged); o blame roda **sem
  revisão** (working tree) e nunca `HEAD` — senão linhas staged/novas virariam
  NCY ou divergiriam do diff.
- **Diff já filtrado**: `parse_added_lines` consome o texto produzido pelo
  diff do GitPR (SMART_EXCLUDES aplicado) — nunca re-roda `git diff` nem
  reaplica exclusões.
- **Caminhos com octais**: nomes de arquivo com caracteres não-ASCII vêm como
  escapes octais **por byte** (`\303\251` = `é` em UTF-8); o parser decodifica
  o bytearray completo uma única vez com `errors="replace"`.
- **Porcelain**: o blame usa `--line-porcelain` (um bloco de metadados por
  linha) — mais estável que o formato padrão para parse; hash com prefixo `^`
  (limite de história) é aceito.
- **Nenhum valor digitado é submetido cru**: o campo da TUI aceita login, nome
  ou e-mail, mas só handles chegam ao `requested_reviewers` — o valor passa
  pela escada prefill → candidato (exato) → e-mail → `GET /users/{login}`, e o
  que não resolve vira item descartado.
- **`201` não é prova de anexo**: um login inexistente é aceito e ignorado sem
  erro; só o read-back do corpo diz quem entrou no PR. O `422`, esse é
  documentado, e derruba o lote inteiro (autor do PR/não-colaborador) — daí o
  reenvio um a um.
- **Ausência ≠ indisponibilidade**: `get_commit_author_login`/`get_user_login`
  devolvem `None` para "não existe" e **levantam** para falha transitória
  (403/timeout); o chamador trata as duas coisas de forma diferente.
- **Charset antes da rede**: `get_user_login` valida o login por regex antes de
  qualquer requisição — `"Eduarda Leal"` (nome com espaço) é recusado localmente.
