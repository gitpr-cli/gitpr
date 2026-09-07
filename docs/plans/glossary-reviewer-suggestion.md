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
| **candidato (ReviewerCandidate)** | Autor agregado com direito a ser sugerido: `author_name`, `author_email` (normalizado), `touched_lines`, `touched_files`, `last_touch_date` (ISO do `author-time` máximo). |
| **ranking (score)** | `0.5·(linhas/total) + 0.3·(arquivos/total) + 0.2·recência`, com recência `1/(1+dias/90)` (half-life de 90 dias). Pesos e half-life são constantes de código. Desempate por `touched_lines`; trunca em `top_n` (default 3). |
| **bot** | Conta não-humana excluída do ranking: sufixo `[bot]` no nome ou na local-part do e-mail, ou e-mail na lista `DEFAULT_BOT_EMAILS` (dependabot, actions, github-actions…). **Nunca** por domínio `users.noreply.github.com` — é o e-mail padrão de usuários reais. |
| **handle** | Login do GitHub (1–39 chars, `[A-Za-z0-9-]`). É o que a TUI submete (`requested_reviewers` aceita só logins). |
| **users.noreply.github.com** | Domínio de e-mail privado do GitHub: `{id}+{login}@users.noreply.github.com` (ou `{login}@` em contas antigas). Parseado em handle sem rede; bots como `dependabot[bot]@…` falham o charset do login → `None`. |
| **email_to_handle** | Mapeamento best-effort nunca-bloqueante no provider GitHub: (a) parse do noreply; (b) fallback `GET /search/users?q={email} in:email`. Candidato sem handle aparece na TUI (nome + e-mail) sem prefill. |
| **requested_reviewers** | Endpoint GitHub pós-criação (`POST /repos/{o}/{r}/pulls/{n}/requested_reviewers`, expected `{201}`, json `{"reviewers": [...]}`). Não existe no create do PR — attach sempre após o PR existir. Forges sem equivalente → `ScmNotSupportedError` (método não-abstrato na base). |
| **attach** | Submissão dos handles aceitos/editados na TUI ao PR recém-criado (ou atualizado). GitHub-only; falha (ex.: handle digitado inexistente → 422) é **não-fatal**: warning no `final_message`, PR permanece criado. |
| **view (reviewer_suggestion)** | Dict repassado por `main.py` à TUI: `{"handles", "lines", "submittable", "note"}`. `submittable=False` (forges não-GitHub) → sem `Input`, só hint + nota "exibido localmente". |
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
