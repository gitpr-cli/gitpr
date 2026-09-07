# Plano — GitPR Suggested Reviewers (execução da spec `20260904_skill_gitpr_reviewer_suggestion_spec.md`)

- **Status:** Executado (ver relatório em `docs/claude-code/reports/develop_natan/2026-09-06_reviewer_suggestion.md`)
- **Data:** 2026-09-06
- **Contexto:** spec [20260904_skill_gitpr_reviewer_suggestion_spec.md](20260904_skill_gitpr_reviewer_suggestion_spec.md), grilling + domain-modeling e aprovação do usuário (Rodadas 1–2)
- **ADR de desvios:** [ADR-002-reviewer-suggestion.md](ADR-002-reviewer-suggestion.md)
- **Glossário:** [glossary-reviewer-suggestion.md](glossary-reviewer-suggestion.md)

## Contexto

A spec pede: ao publicar um PR, sugerir 1..N revisores com base em quem mais tocou
(git blame) as linhas adicionadas pelo diff — reaproveitando o motor de blame da
arqueologia (`src/blame_engine.py`), com exibição editável no PR Publisher (TUI) e
submissão na criação do PR. O fluxo grill-with-docs (grilling + domain-modeling)
sobre a spec produziu este plano, com **7 decisões aprovadas** pelo autor que
**divergem da spec** (a exploração do código revelou incompatibilidades: CLI sem
subcomando `pr`, sem parser de hunks, `PullRequestRequest.reviewers` morto, config
sem YAML, TUI sem seção de metadados, testes sem repo git real).

## Decisões aprovadas (semearam o ADR-002)

1. **Arquitetura plana** (não `src/domain|application`, não mover
   `blame_engine.py` para `infrastructure/git/`): `blame_engine.py` importa
   `core.py` → se `core.py` chamasse o use case haveria ciclo. Novos módulos na
   raiz de `src/`; integração em `main.py` (orquestrador real do fluxo PR),
   **`core.py` intocado**.
2. **Trigger**: default ON por config; flag opt-out `--no-suggest-reviewers`
   (padrão `--no-publish`/`--no-edit`/`--no-unstaged-check`). Cálculo **somente
   no fluxo TUI default** (antes de o `PrPublishApp` abrir). `--no-edit` e
   `--no-publish` não calculam nada. 100% não-bloqueante: falha → warning, fluxo
   continua.
3. **Transporte**: submissão real de reviewers **somente GitHub** (método novo
   no provider, pós-criação via `requested_reviewers`). GitLab/Bitbucket/Azure:
   sugestões exibidas na TUI, nunca submetidas (aviso). Filtro de bot fino
   (sufixo `[bot]`, e-mails bot conhecidos) — **não** excluir
   `users.noreply.github.com` (e-mail padrão de usuários reais). Mapeamento
   e-mail→handle GitHub best-effort nunca-bloqueante: (a) parse do
   `users.noreply.github.com`, (b) fallback busca `/search/users in:email`.
   Candidato sem handle aparece na TUI (nome+e-mail) sem prefill.
4. **Granularidade**: blame **só de linhas adicionadas** (new-side), contra a
   **working tree** (casado com `get_git_full_diff`). Linhas "Not Committed
   Yet" (`0000…`) puladas.
5. **Config**: dotenv plano `~/.gitpr/.env` (sem YAML, ADR-001):
   `GITPR_SUGGEST_REVIEWERS` (default true), `GITPR_REVIEWER_SUGGESTION_TOP_N`
   (3), `GITPR_REVIEWER_SUGGESTION_EXCLUDED` (CSV). Pesos 0.5/0.3/0.2 e meia-vida
   90d = **constantes de código**. Chaves novas em `DEFAULT_CONFIG`
   (`src/config.py`).
6. **Testes**: fixture de **repo git real** (commits com
   `git -c user.name=… -c user.email=…`, `tmp_path`, offline) permitida **só**
   no teste de integração do use case (aceite §8.6). Scoring puro sem git/rede.
   Resto segue mock de subprocess.
7. **UX TUI**: em `PrPublishApp`, seção `👥 Suggested Reviewers` — `Input`
   pré-preenchido com handles (CSV) + linha hint read-only com justificativa por
   candidato. Remover = apagar; adicionar = digitar; aceitar = F3. Falha de
   attach → warning não-fatal.

## Passos ordenados (cada um revisável isolado; sem commits)

### (a) `src/blame_engine.py` — função fina, arqueologia intocada
Nova `get_blame_for_range(file_path, start_line, end_line, repo_path=None)
-> list[BlameHit]`: roda `git blame --line-porcelain -L s,e -- <file>` com
`cwd=repo_path`, `encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL`,
parse por bloco porcelain (`author`, `author-mail`, `author-time`, hash 40 hex
com `^` opcional), pula hash `0000…`, `commit_date` = ISO do `author-time`;
erros → `[]` (mesmo contrato da função atual). **Não** refatora
`execute_git_blame`/`run_blame_analysis`.

### (b) `src/reviewer_suggestion.py` — módulo puro (sem git/rede)
Dataclasses da spec §3 em inglês (`BlameHit`, `ReviewerCandidate`,
`ReviewerSuggestionResult`) + `WEIGHTS_DEFAULT`, `RECENCY_HALFLIFE_DAYS`,
`DEFAULT_BOT_EMAILS`. Funções: `normalize_email`, `is_bot`,
`aggregate_hits`, `compute_scores`, `rank_reviewers` (exclui autor do PR com
flag `excluded_pr_author`, exclui bots + `excluded_authors`, score
`0.5·lines + 0.3·files + 0.2·recency`, recência `1/(1+dias/90)`, sort desc +
desempate por `touched_lines`, trunca `top_n`; sem hits → vazio, sem exceção).

### (c) `src/diff_parser.py` — parser puro de hunks
`parse_added_lines(diff_text) -> dict[str, list[int]]` (nº new-side das linhas
`+`): máquina de estados sobre `diff --git` (rename vale o lado `b/`),
`+++ b/` vs `+++ /dev/null`, `@@ -a,b +c,d @@`, linhas `+`/`-`/contexto/
`\ No newline`, `Binary files`, mode-only. Consome o texto já produzido por
`get_git_full_diff()` — **nunca** re-roda `git diff` nem reaplica
SMART_EXCLUDES.

### (d) `src/suggest_reviewers.py` — orquestração
`compute_reviewer_suggestions(diff_text, *, pr_author_email, pr_author_name=None,
top_n=3, excluded_authors=(), repo_path=None) -> ReviewerSuggestionResult` —
**nunca levanta**: parse → agrupa nºs contíguos (gap 1) →
`get_blame_for_range` por intervalo → arquivo sem hits vira warning i18n e
segue → `rank_reviewers` → merge warnings. Teto anti-abuso por arquivo (corte +
warning). Helpers de apresentação `format_candidate_line` /
`format_suggestion_lines` (tudo via `__()`).

### (e) `src/config.py` — 3 chaves
`DEFAULT_CONFIG` += `GITPR_SUGGEST_REVIEWERS: "true"`,
`GITPR_REVIEWER_SUGGESTION_TOP_N: "3"`, `GITPR_REVIEWER_SUGGESTION_EXCLUDED:
""`. `suggest_reviewers_enabled()` (parse bool espelhando `coauthor_enabled`),
`get_reviewer_suggestion_settings()` (`top_n` inválido → 3; `excluded` CSV →
lista limpa).

### (f) `src/main.py` — flag + integração no fluxo default
Flag `--no-suggest-reviewers` (decorators, assinatura `cli()`, `HELP_MAP`,
`HELP_PRIORITY`). Bloco novo entre o `return` do `--no-edit` e o
`# ── Default: Open TUI ──`: se habilitado → identidade via
`get_git_user_info()` → `compute_reviewer_suggestions(diff_text, ...)` com
top_n/excluded do config; falha → warning e segue com `None`. Após
`validate_or_request_scm_token`: `_reviewer_suggestion_view(result, provider)`
→ dict `{"handles", "lines", "submittable", "note"}` (resolução de handle
best-effort por candidato; não-GitHub → `submittable=False` + nota i18n).
Passar `reviewer_suggestion=view` ao `PrPublishApp`.

### (g) SCM — `requested_reviewers` + mapeamento de handle (GitHub)
`src/infrastructure/scm/base.py`: método **não-abstrato**
`request_pull_request_reviewers(self, repo, pr_id, reviewers) -> None` com
default `raise ScmNotSupportedError(...)` — não quebra o `test_contract.py`
nem força os 4 providers. `PullRequestRequest.reviewers` (morto) permanece
intocado. `github_provider.py`: `request_pull_request_reviewers` →
`POST …/pulls/{n}/requested_reviewers` json `{"reviewers": [...]}` expected
`{201}` via `_request`; `email_to_handle(email) -> str|None` **nunca levanta**
(helper `_handle_from_noreply` + fallback `/search/users` → `items[0].login`).

### (h) `src/ui/pr_publish_app.py` — seção editável + attach
Parâmetro novo `reviewer_suggestion=None` no `__init__`; `compose()` com a
seção (Label, `Input` pré-preenchido CSV com placeholder, `Static` hint com
justificativas + nota) quando a view existe; regra CSS `#reviewers_hint`.
`_parsed_reviewers()` (split/strip/dedupe preservando ordem, guardas → `[]`).
Create path (`_publish_pr_from_progress`, após `log_command_metric`, antes de
auto-merge): se GitHub e `pr_number` → `request_pull_request_reviewers` em
try/except → aviso i18n não-fatal no `final_message` (PR permanece criado);
não-GitHub → sem Input/sem attach. Update path (`_push_and_exit`): leitura dos
reviewers na app thread (o push roda em worker) + attach após
`update_pull_request`. i18n: chaves novas nos 6 `langs/*.json` via sync +
tradução (chaves com `{...}` diferem do EN).

### (i) Documentos
Plano (este), `ADR-002-reviewer-suggestion.md`, `glossary-reviewer-suggestion.md`
e o relatório obrigatório em `docs/claude-code/reports/develop_natan/`.

## Armadilhas críticas

- SMART_EXCLUDES: parser consome só o texto do diff já filtrado; nunca re-filtra
  nem re-roda diff.
- `-U1 -w -M -B` vs parse ingênuo: parser por estados com testes para
  rename/`-B`/`+++ /dev/null`/`\ No newline`/binário.
- Blame **sem revisão** (working tree) casa com o diff `<ancestor>` vs working
  tree (inclui staged) — nunca `HEAD`.
- NCY `0000…` nunca gera candidato (trabalho não-commitado do autor).
- Shallow/binário/novo/sem histórico → `[]` + warning, nunca exceção.
- UTF-8 `errors="replace"` + `stdin=subprocess.DEVNULL` em todo subprocess novo
  (CLAUDE.md).
- Todo texto visível via `__()`; chaves nos 6 arquivos langs.
- Sem ciclo de imports: `core.py` intocado; `blame_engine →
  reviewer_suggestion` (puro); `suggest_reviewers → {diff_parser,
  blame_engine, reviewer_suggestion}`.
- Handle inexistente digitado → GitHub 422 → `ScmProviderError` → warning; PR
  continua criado.
- Fixture real sem vazar identidade global (commits com `-c user.*`, `gpgsign
  false` local, `-b main`, sem remote).

## Verificação final

- Suíte: `python -m pytest tests/ -v` — mínimo verde obrigatório: arqueologia
  (`test_blame_metrics.py`), i18n (`test_i18n.py`), contrato SCM (`tests/scm/`)
  e todos os arquivos novos/alterados.
- Manual (repo multi-autor GitHub): `gitpr` → mensagem "Searching for suggested
  reviewers…", hint com justificativas, Input pré-preenchido → editar → F3 → PR
  criado com reviewers (campo Reviewers no GitHub); `GITPR_SUGGEST_REVIEWERS=false`
  ou falha → TUI abre sem sugestões (só aviso); `--no-edit`/`--no-publish` →
  nenhuma menção; `gitpr -h --no-suggest-reviewers` → help contextual; repo
  não-GitHub → nota "shown locally only"; `-c`/`-r`/`-f`/`-is`/`-b` inalterados.
