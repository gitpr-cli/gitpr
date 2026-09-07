# Plano — GitPR Suggested Reviewers (skill grill-with-docs sobre a spec `docs/plans/20260904_skill_gitpr_reviewer_suggestion_spec.md`)

## Contexto

A spec pede: ao publicar um PR, sugerir 1..N revisores com base em quem mais tocou (git blame) as linhas adicionadas pelo diff — reaproveitando o motor de blame da arqueologia (`src/blame_engine.py`), com exibição editável no PR Publisher (TUI) e submissão na criação do PR. Esta sessão executou o fluxo grill-with-docs (grilling + domain-modeling) sobre a spec e produziu o plano abaixo, com **7 decisões aprovadas** pelo autor que **divergem da spec** (a exploração do código revelou incompatibilidades: CLI sem subcomando `pr`, sem parser de hunks, `PullRequestRequest.reviewers` morto, config sem YAML, TUI sem seção de metadados, testes sem repo git real).

**Entregáveis após aprovação (regras CLAUDE.md):**
1. Plano salvo em `docs/plans/20260906_skill_gitpr_reviewer_suggestion_plan.md`
2. ADR de desvios: `docs/plans/ADR-002-reviewer-suggestion.md` (formato do ADR-001)
3. Glossário: `docs/plans/glossary-reviewer-suggestion.md` (formato do glossary-scm-multiforge.md)
4. Relatório obrigatório: `docs/claude-code/reports/develop_natan/2026-09-06_reviewer_suggestion.md`
5. Implementação dos passos (a)–(i) **sem nenhum git add/commit/push** (regra CLAUDE.md: mudanças ficam na working tree para revisão do usuário)

## Decisões aprovadas (semearão o ADR-002)

1. **Arquitetura plana** (não `src/domain|application`, não mover `blame_engine.py` p/ `infrastructure/git/`): `blame_engine.py` importa `core.py` → se `core.py` chamasse o use case haveria ciclo. Novos módulos na raiz de `src/`; integração em `main.py` (orquestrador real do fluxo PR), **`core.py` intocado**.
2. **Trigger**: default ON por config; flag opt-out `--no-suggest-reviewers` (padrão `--no-publish`/`--no-edit`/`--no-unstaged-check`). Cálculo **somente no fluxo TUI default** (antes do `PrPublishApp` abrir). `--no-edit` e `--no-publish` não calculam nada. 100% não-bloqueante: falha → warning, fluxo continua.
3. **Transporte**: submissão real de reviewers **somente GitHub** (método novo no provider, pós-criação via `requested_reviewers`). GitLab/Bitbucket/Azure: sugestões exibidas na TUI, nunca submetidas (aviso). Filtro de bot fino (sufixo `[bot]`, e-mails bot conhecidos) — **não** excluir `users.noreply.github.com` (e-mail padrão de usuários reais). Mapeamento e-mail→handle GitHub best-effort nunca-bloqueante: (a) parse do `users.noreply.github.com`, (b) fallback busca `/search/users in:email`. Candidato sem handle aparece na TUI (nome+e-mail) sem prefill.
4. **Granularidade**: blame **só de linhas adicionadas** (new-side), contra a **working tree** (casado com `get_git_full_diff`). Linhas "Not Committed Yet" (`0000…`) puladas.
5. **Config**: dotenv plano `~/.gitpr/.env` (sem YAML, ADR-001): `GITPR_SUGGEST_REVIEWERS` (default true), `GITPR_REVIEWER_SUGGESTION_TOP_N` (3), `GITPR_REVIEWER_SUGGESTION_EXCLUDED` (CSV). Pesos 0.5/0.3/0.2 e meia-vida 90d = **constantes de código**. Chaves novas em `DEFAULT_CONFIG` (`src/config.py:16-51`).
6. **Testes**: fixture de **repo git real** (commits com `git -c user.name=… -c user.email=…`, `tmp_path`, offline) permitida **só** no teste de integração do use case (aceite §8.6). Scoring puro sem git/rede. Resto segue mock de subprocess.
7. **UX TUI**: em `PrPublishApp`, seção `👥 Suggested Reviewers` — `Input` pré-preenchido com handles (CSV) + linha hint read-only com justificativa por candidato. Remover = apagar; adicionar = digitar; aceitar = F3. Falha de attach → warning não-fatal.

## Passos ordenados (cada um revisável isolado; sem commits)

### (a) `src/blame_engine.py` — função fina, arqueologia intocada
- Nova `get_blame_for_range(file_path, start_line, end_line, repo_path=None) -> list[BlameHit]` (após `execute_git_blame`, ~linha 40): roda `git blame --line-porcelain -L s,e -- <file>` com `cwd=repo_path`, `encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL` (convenção core; **não** corrigir `execute_git_blame` atual), parse por bloco porcelain (`author`, `author-mail`, `author-time`, hash 40 hex com `^` opcional), pula hash `0000…`, `commit_date` = ISO do `author-time`. `except (CalledProcessError, FileNotFoundError, ValueError, OSError): return []` (mesmo contrato do atual). Importa `from src.reviewer_suggestion import BlameHit` (módulo puro do passo b — sem ciclo).
- **Não** refatorar `execute_git_blame`/`run_blame_analysis` (regressão zero da arqueologia).
- Teste novo `tests/test_blame_engine_ranges.py` (mock `subprocess.run`): cmd correto, parsing de bloco, 40-zeros ignorado, erros → `[]`. Verificação: `python -m pytest tests/test_blame_engine_ranges.py tests/test_blame_metrics.py -v`.

### (b) `src/reviewer_suggestion.py` — módulo puro (sem git/rede)
- Dataclasses da spec §3 em inglês: `BlameHit`, `ReviewerCandidate`, `ReviewerSuggestionResult(candidates, excluded_pr_author, warnings)` + `WEIGHTS_DEFAULT = {"lines": 0.5, "files": 0.3, "recency": 0.2}`, `RECENCY_HALFLIFE_DAYS = 90.0`, `DEFAULT_BOT_EMAILS` (dependabot/actions/github-actions).
- Funções: `normalize_email` (lowercase), `is_bot(name, email)` (sufixo `[bot]` no nome ou local-part; e-mail ∈ DEFAULT_BOT_EMAILS; **nunca** por domínio noreply), `aggregate_hits(hits)` (chave = e-mail normalizado, fallback nome casefold; `touched_files`, `last_touch_date` = ISO máxima), `compute_scores(...)`, `rank_reviewers(hits, *, pr_author_email, pr_author_name=None, excluded_authors=None, top_n=3, weights=None, halflife_days=90.0)` → exclui autor do PR (flag `excluded_pr_author`), exclui bots + `excluded_authors` (e-mail ou nome), score = `0.5·lines + 0.3·files + 0.2·recency` (recência `1/(1+dias/90)`; data inválida → 0 sem quebrar), sort desc + desempate por `touched_lines`, trunca `top_n`. Sem hits → resultado vazio, sem exceção.
- Teste novo `tests/test_reviewer_suggestion.py` (puro) cobrindo aceites §8.1–3 + normalização + decaimento + vazio.

### (c) `src/diff_parser.py` — parser puro de hunks
- `parse_added_lines(diff_text) -> dict[str, list[int]]` (nº new-side das linhas `+`): máquina de estados sobre cabeçalhos `diff --git a/.. b/..` (rename: vale o lado `b/`), `+++ b/` vs `+++ /dev/null`, `@@ -a,b +c,d @@` (contador new-side), linhas `+`/`-`/contexto/`\ No newline`, `Binary files`, mode-only. Retorna só arquivos com ≥1 linha adicionada. Consome o texto já produzido por `get_git_full_diff()` — **nunca** re-roda `git diff` nem reaplica SMART_EXCLUDES.
- Teste novo `tests/test_diff_parser.py` (strings literais): hunk `-U1`, múltiplos hunks, `c,0`, rename `-M`, novo arquivo, binário, deletado, `\ No newline`, split de `-B`, linha `+` iniciando com `++`.

### (d) `src/suggest_reviewers.py` — orquestração
- `compute_reviewer_suggestions(diff_text, *, pr_author_email, pr_author_name=None, top_n=3, excluded_authors=(), repo_path=None) -> ReviewerSuggestionResult` — **nunca levanta**: parse → agrupa nºs contíguos (gap 1) → `get_blame_for_range` por intervalo → arquivo sem hits vira warning i18n (`__("File {path}: no blame history found (new or binary file?)", ...)`) e segue → `rank_reviewers` → merge warnings. Teto anti-abuso por arquivo (corte + warning). Imports só de `blame_engine`/`diff_parser`/`reviewer_suggestion`/`i18n` (nada importa `core.py` por este lado; `main.py` orquestra).
- Helpers de apresentação `format_candidate_line(candidate, today=None)` / `format_suggestion_lines(result, today=None)` (tudo via `__()`, testáveis).
- Testes `tests/test_suggest_reviewers.py`: unit com mocks (aceites §8.4–5: arquivo sem histórico → warning não erro; blame incompleto/`diff_text=""` → degrada) + **integração com repo git real** em `tmp_path` (aceite §8.6): `git init -b main`, `commit.gpgsign false` local, commits multi-autor com `-c user.name/-c user.email`, diff com mesmas flags de `get_git_full_diff` sobre a working tree incluindo linhas não-commitadas → assert: autor do PR excluído mesmo dominando, linhas NCY não geram candidato, ranking real, zero rede (sem remote).

### (e) `src/config.py` — 3 chaves
- `DEFAULT_CONFIG` += `GITPR_SUGGEST_REVIEWERS: "true"`, `GITPR_REVIEWER_SUGGESTION_TOP_N: "3"`, `GITPR_REVIEWER_SUGGESTION_EXCLUDED: ""` (gravação automática via `setup_environment`).
- `suggest_reviewers_enabled()` (parse bool espelhando `coauthor_enabled` ~137-150), `get_reviewer_suggestion_settings() -> {"enabled", "top_n", "excluded"}` (`top_n` inválido → 3; `excluded` CSV → lista limpa). Testes novos espelhando os de `coauthor_enabled`.

### (f) `src/main.py` — flag + integração no fluxo default
- Flag `--no-suggest-reviewers` na pilha de decorators (~450-454, antes de `--linter-setup`); parâmetro na assinatura `cli()` (~499-502); entradas em `HELP_MAP` (~208) e `HELP_PRIORITY` (~247); import topo: `suggest_reviewers_enabled`, `get_reviewer_suggestion_settings`.
- **Bloco novo entre o `return` do `--no-edit` (linha 1468) e o comentário `# ── Default: Open TUI ──` (1470)** (lá só o fluxo default chega): se `not no_suggest_reviewers and suggest_reviewers_enabled()` → identidade via `get_git_user_info()` (`src/cache.py:20`) → `compute_reviewer_suggestions(diff_text, ...)` com top_n/excluded do config; todo o try/except geral → secho amarelo e segue com `None`. Mensagens via `__()` ("🔍 Searching for suggested reviewers...", warnings).
- Após `validate_or_request_scm_token` (1474-1479): montar view `_reviewer_suggestion_view(result, provider)` (helper novo perto de `_resolve_scm_context` ~1764): dict `{"handles": [...], "lines": [...], "submittable": bool, "note": str|None}` — resolve `provider.email_to_handle(email)` (passo g) por candidato em try/except silencioso; não-GitHub → `submittable=False` + nota i18n ("shown locally only"). Passar `reviewer_suggestion=view` ao `PrPublishApp` (1483-1491).

### (g) SCM — `requested_reviewers` + mapeamento de handle (GitHub)
- `src/infrastructure/scm/base.py`: método **não-abstrato** `request_pull_request_reviewers(self, repo, pr_id, reviewers) -> None` no ABC (~após `update_pull_request`, 188-196) com default `raise ScmNotSupportedError(...)` — **não** abstrato para não quebrar `tests/scm/test_contract.py:69-76` nem forçar os 4 providers. `PullRequestRequest.reviewers` (morto, base.py:34) **permanece intocado**.
- `src/infrastructure/scm/github_provider.py`: `request_pull_request_reviewers(repo, pr_id, reviewers, timeout=15)` → `POST _repo_url(repo, "pulls", pr_id, "requested_reviewers")` json `{"reviewers": [...]}`, expected `{201}`, via `_request` (99-123). `email_to_handle(email) -> str|None` **nunca levanta**: helper `_handle_from_noreply(email)` (domínio `users.noreply.github.com`; local-part após último `+`; valida regex username `^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?$`) → fallback `GET {base}/search/users` `params={"q": f"{email} in:email"}` → `items[0].login`; qualquer `ScmProviderError` → `None`.
- Testes em `tests/scm/test_github_provider.py` (padrão `_response`/mock requests): sucesso 201, erro 422 → `ScmProviderError`, rede → `http_status=0`; `email_to_handle` com `1234+ana@users.noreply.github.com`→`ana`, `ana@users.noreply.github.com`→`ana`, `dependabot[bot]@…`→None (regex), e-mail comum → search, 403/vazio → None. Caso opcional em `test_contract.py` p/ provider não-GitHub (GitLab) → `ScmNotSupportedError`.

### (h) `src/ui/pr_publish_app.py` — seção editável + attach
- `__init__` (632-682): parâmetro novo `reviewer_suggestion=None` antes de `**kwargs`; guarda `self.reviewer_suggestion`.
- `compose()` (684-691): quando view existe, entre o corpo e o Footer: `Label(__("👥 Suggested Reviewers"))`, `Input(value=", ".join(handles), id="reviewers_input", placeholder=…)`, `Static(hint_lines + note, id="reviewers_hint")`. CSS (619-623): regra `#reviewers_hint { height: auto; text-style: dim; }` (verificar token de cor no tema; fallback `opacity`).
- `_parsed_reviewers()`: lê `#reviewers_input`, split `,`, strip, dedupe preservando ordem.
- Create path `_publish_pr_from_progress` (sucesso 1385-1419, após `log_command_metric` ~1392, **antes** de auto-merge/`_prompt_merge`): se handles e `provider_is_github(self.provider)` (helper já importado no arquivo, 1395) e `pr_number` → `request_pull_request_reviewers` em try/except `ScmProviderError` → `final_message` += aviso i18n (não-fatal, PR permanece criado); provider não-GitHub → log skip.
- Update path `_push_and_exit` (~1152-1154, após `update_pull_request` do PR existente): mesmo attach + try/except.
- i18n: rodar `python tests/sync_i18n.py` e traduzir chaves novas nos 6 arquivos `langs/*.json` (chaves com `{...}` não podem ficar idênticas ao EN — `test_identity_keys_with_braces_allowlist`).
- Testes em `tests/test_pr_publish_app.py`: sem view → sem `#reviewers_input` (regressão); com view → prefill + hint; `_parsed_reviewers` com lixo; publish GitHub → attach chamado **depois** de `create_pull_request`; falha do attach → `final_action` continua `created` + aviso; provider não-GitHub → attach nunca chamado.

### (i) Documentos
1. `docs/plans/20260906_skill_gitpr_reviewer_suggestion_plan.md` (este plano, espelhando o nome da spec)
2. `docs/plans/ADR-002-reviewer-suggestion.md` — formato ADR-001 (metadados Status/Data/Contexto/Glossário + Contexto + Decisão numerada + tabela "Desvios aprovados (vs. spec)" com os 7 itens e porquês + alternativas consideradas curtas)
3. `docs/plans/glossary-reviewer-suggestion.md` — formato glossary-scm-multiforge.md: termos de domínio (BlameHit, candidate, handle, requested_reviewers, NCY, half-life/recência, users.noreply.github.com) + tabela das 3 chaves + notas de fidelidade de API
4. `docs/claude-code/reports/develop_natan/2026-09-06_reviewer_suggestion.md` — relatório obrigatório `## Completion Report — …` (What was done / Changed files / Impact / Next steps), PT-BR

## Armadilhas críticas
- SMART_EXCLUDES: parser consome só o texto do diff já filtrado; nunca re-filtra nem re-roda diff.
- `-U1 -w -M -B` vs parse ingênuo: parser por estados com testes p/ rename/`-B`/`+++ /dev/null`/`\ No newline`/binário.
- Blame **sem revisão** (working tree) casa com o diff `<ancestor>` vs working tree (inclui staged) — nunca `HEAD`.
- NCY `0000…` nunca gera candidato (trabalho não-commitado do autor).
- Shallow/binário/novo/sem histórico → `[]` + warning, nunca exceção.
- UTF-8 `errors="replace"` + `stdin=subprocess.DEVNULL` em todo subprocess novo (CLAUDE.md).
- Todo texto visível via `__()`; chaves nos 6 arquivos langs via `sync_i18n.py`.
- Sem ciclo de imports: `core.py` intocado; `blame_engine → reviewer_suggestion` (puro); `suggest_reviewers → {diff_parser, blame_engine, reviewer_suggestion}`.
- Handle inexistente digitado → GitHub 422 → `ScmProviderError` → warning; PR continua criado.
- Fixture real sem vazar identidade global (commits com `-c user.*`, `gpgsign false` local, `-b main`, sem remote).

## Verificação final
- Suíte: `python -m pytest tests/ -v` — mínimo verde obrigatório: arqueologia (`test_blame_metrics.py`), i18n (`test_i18n.py`), contrato SCM (`tests/scm/`) e todos os arquivos novos/alterados.
- Manual (repo multi-autor GitHub): `gitpr` → mensagem "Searching for suggested reviewers…", hint com justificativas, Input pré-preenchido → editar → F3 → PR criado com reviewers (checar campo Reviewers no GitHub); `GITPR_SUGGEST_REVIEWERS=false` ou falha → TUI abre sem sugestões (só aviso); `--no-edit`/`--no-publish` → nenhuma menção; `gitpr -h --no-suggest-reviewers` → help contextual; repo não-GitHub → nota "shown locally only"; `-c`/`-r`/`-f`/`-is`/`-b` inalterados.
- Mapa de aceite §8: 1→test_reviewer_suggestion; 2→exclusão do autor; 3→bots default+config; 4→warning de arquivo sem histórico; 5→degradação/blame incompleto; 6→fixture real (d); 7→arqueologia intocada + suíte verde.
