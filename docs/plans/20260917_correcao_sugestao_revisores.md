# Correção — sugestão de revisores não chega ao PR no forge

## Context

A feature "Suggested Reviewers" (ADR-002) mostra, no PR Publisher (TUI), um campo editável com os revisores sugeridos — hoje pré-preenchido **apenas** com handles resolvidos por `provider.email_to_handle()`: parse de `users.noreply.github.com` + fallback `GET /search/users?q={email} in:email`, que só encontra quem tem e-mail **público**. Com e-mail corporativo (caso real: `eduardaleal@grafjb.com.br` no repo SIG-Novo) nada resolve: o `Input` nasce **vazio** e o hint mostra só o **nome** — a única identidade que a UI oferece. O usuário digita o nome que a UI mostrou e a CLI o envia **verbatim** como se fosse login.

**Evidência (log da execução do usuário, `~/.gitpr/logs/pr_desc/pr_desc_w7YW-kabx4-8xAg.log`):**

```
[2026-09-16 19:06:08] PR created successfully: .../SIG-Novo/pull/1068, number=1068
[2026-09-16 19:06:10] Reviewers requested on PR #1068: ['Eduarda Leal']
```

A linha só é escrita depois que `_request()` retorna sem levantar, e ele levanta para qualquer status fora de `{201}` → **o GitHub respondeu 201 e não anexou ninguém**. Falha silenciosa: o `final_message` só aparece depois da TUI fechar e o fluxo segue direto ao prompt de merge.

**Fatos de API (pesquisa):** o corpo do 201 traz `requested_reviewers` → dá para verificar sem chamada extra; `GET /repos/{o}/{r}/commits/{sha}` devolve `author.login` (conta ligada ao e-mail do commit) e vem `null`/`{}` quando não há conta ligada; `/search/users in:email` só enxerga e-mail público; login **inexistente** → 201 ignorado (o log), usuário **existente mas inelegível** (autor do PR, não-colaborador) → 422 **tudo-ou-nada**.

**Objetivo:** digitar o que a UI mostra (login, nome ou e-mail) tem que virar revisor efetivamente solicitado — ou um aviso impossível de não ver, dizendo quem não foi e por quê.

## Decisões (grilling, 4 rodadas)

| # | Decisão |
|---|---|
| 1 | O campo aceita **login, nome ou e-mail**; o valor é resolvido para login antes de submeter |
| 2 | Resolução pelo **commit do blame**: `GET /repos/{o}/{r}/commits/{sha}` → `author.login`, com o hash mais recente de cada candidato |
| 3 | Resolver **antes da TUI** (prefill + hint `@handle`) e **validar no attach** só o que o usuário digitou/alterou |
| 4 | Item que não resolve é **pulado e reportado com o motivo** — nunca enviado como veio |
| 5 | **Read-back**: `request_pull_request_reviewers()` devolve os logins realmente anexados (corpo do 201) |
| 6 | Casamento com candidatos **exato e normalizado** (strip + casefold) — sem fuzzy |
| 7 | Autor do PR: **sem** `GET /user` no caminho feliz |
| 8 | Falha parcial → **modal no TUI** que precisa ser fechado (mantendo a linha no `final_message`); sucesso silencioso |
| 9 | Sem login resolvido: hint mostra a pessoa + aviso i18n, e o `Input` continua disponível |
| 10 | Textos novos: chaves nos **6 pacotes** `langs/*.json` + bump de `__lang_version__` |
| 11 | Forges não-GitHub **inalterados** (`submittable=False`, sem Input, nota local-only) |
| 12 | Docs: família `docs/suggested-reviewers.*` (5 cópias), emenda no ADR-002, glossário, relatório |
| 13 | 422 no lote → **reenviar um a um**, anexando os bons e reportando os ruins com a mensagem do GitHub |

**Não-objetivos:** nenhuma chave de config nova (seguem as 3 do ADR-002); nada muda em `--no-edit`/`--no-publish` (nunca calculam sugestão); sem cache da resolução (inputs são por execução; o caminho não passa pelo cache MD5 de IA); `PullRequestRequest.reviewers` continua morto (o GitHub não aceita reviewers no create).

## Desenho

```
blame ──► ReviewerCandidate (+last_commit_hash)
              │
              ▼  resolve_candidates()            [antes da TUI, GitHub-only]
   commits/{sha} ─► author.login ─┐
   email_to_handle (fallback) ────┘──► ResolvedReviewer(name,email,login)
              │
              ▼  _reviewer_suggestion_view()
   view = {handles, lines, submittable, note, candidates}
   Input pré-preenchido · hint "@handle" ou "... no GitHub login found"
              │
              ▼  resolve_typed_reviewers()       [no attach]
   prefill (sem chamada) │ candidato (exato) │ e-mail │ login (GET /users/{login})
              │
              ▼  POST requested_reviewers  ──201──► read-back: attached
              │                            └─422──► reenvia 1 a 1
              ▼  _finish_attach(): avisos → NoticeScreen → só então prompt de merge
```

## Implementação (ordem de execução)

### 1. Camada SCM
- `src/infrastructure/scm/base.py` (L221-234): manter **não-abstrato** e mantendo `ScmNotSupportedError`; só a assinatura muda para `-> list[str]` (logins efetivamente anexados).
- `src/infrastructure/scm/github_provider.py`:
  - `request_pull_request_reviewers(...) -> list[str]` (L238-258): mesmo endpoint/`{201}`/timeout 15, mas lê `response.json()["requested_reviewers"]` e devolve os logins.
  - **Nova** `get_commit_author_login(repo, sha, timeout=10) -> str | None`: `GET .../commits/{sha}`, esperado `{200}`; 404/422/transporte/`author` nulo → `None` (nunca levanta).
  - **Nova** `get_user_login(login, timeout=10) -> str | None`: valida charset com `_USERNAME_RE` (sem rede para "Eduarda Leal"); `GET {base}/users/{login}` esperado `{200, 404}`; 404 → `None`; demais → `ScmProviderError` (nunca confundir falha transitória com "usuário não existe").
- GitLab/Bitbucket/Azure: **intocados**.

### 2. `src/reviewer_suggestion.py` (puro)
- `ReviewerCandidate` ganha `last_commit_hash: str = ""` (após `last_touch_date`; construções existentes usam kwargs, então não quebram).
- `aggregate_hits()`: guarda `hit.commit_hash` e atualiza no ramo "mais recente vence" (junto de nome/e-mail).
- `normalize_email` → **promover** a chave de agrupamento `_identity_key` para `identity_key(name, email)` (pública) e adicionar `normalize_identity(value)` (strip + casefold) para o casamento do que foi digitado.

### 3. `src/suggest_reviewers.py`
- `format_candidate_line(candidate, who=None, no_login=False)`: quando `no_login`, acrescenta a chave nova de "nenhum login encontrado".
- `format_suggestion_lines(result, who_map=None, no_login=())`: passa a consultar `who_map` por `identity_key(...)` — **corrige o bug secundário** (hoje `main.py` indexa pelo e-mail cru e a consulta usa `normalize_email()`, então e-mail com maiúscula esconde o `@handle`).

### 4. `src/reviewer_resolution.py` (novo, flat, nunca levanta)
- `ResolvedReviewer(name, email, login=None)` + `ResolutionOutcome(logins, dropped=[(valor, motivo_i18n)])`.
- `resolve_candidates(candidates, provider, repo)` — por candidato: `commits/{sha}` → fallback `email_to_handle`; sempre via `getattr(provider, ..., None)` para não quebrar fakes `SimpleNamespace` nem forges sem o método.
- `resolve_typed_reviewers(values, *, resolutions, known_logins, provider, repo)` — escada por valor: prefill (sem chamada) → casamento exato com candidato → e-mail → login (`get_user_login`); o que não resolve entra em `dropped` com motivo.
- `match_candidate(value, resolutions)` — comparação exata contra login/nome/e-mail normalizados.

### 5. `src/main.py`
- `_reviewer_suggestion_view(result, provider, repo=None)` (L2471-2515): resolve candidatos, monta `handles` (dedup), `who_map` por `identity_key`, marca `no_login`, e **acrescenta** `"candidates"` ao view dict (para o attach não refazer rede).
- Chamada em L1539 passa `repo_ref` (já disponível no escopo).

### 6. i18n
- 6 chaves novas (uma literal por linha, sem concatenação — o `sync_i18n.py` é regex e o `test_i18n` exige AST):
  `No GitHub login found for this person — type one below.` · `⚠️ {value}: no GitHub account found.` · `⚠️ {value}: GitHub did not attach this reviewer.` · `⚠️ {value}: {reason}` · `⚠️ Reviewers not requested` · `The pull request was published, but these reviewers were not requested:`
- Adicionar nos 6 pacotes `langs/{es,es_es,fr,fr_fr,pt_br,pt_pt}.json` **com tradução real** (as 3 com `{` são obrigatoriamente traduzidas) e editar à mão (se usar `sync_i18n.py`, conferir `git diff --stat langs/` depois).
- Bump `src/updater.py:11` `__lang_version__` `v0.0.26` → `v0.0.27`.
- Atualizar o placeholder do campo para refletir que aceita nome/e-mail (valor da chave existente).

### 7. `src/ui/pr_publish_app.py`
- `_attach_reviewers(pr_number, values) -> list[str]`: resolve via `resolve_typed_reviewers`, envia, lê de volta e **devolve** as linhas de aviso (motivo do drop · não anexado no read-back), acrescentando-as também ao `final_message`.
- `_request_reviewers(...)`: lote → `201` guarda o read-back; `422` com >1 login → `_request_reviewers_one_by_one` (reusa a mensagem do GitHub como motivo); qualquer outro erro → aviso genérico (chave já existente).
- `_finish_attach(...)` / `_after_attach_continue(...)`: se houver avisos, empilha um **`NoticeScreen(ModalScreen)` novo** (título + mensagem + botão único "Close") e só continua para o merge no callback; sem avisos, segue direto. Não reusar `CommitConfirmScreen` (semântica Yes/No) nem o modal de erro (oferece "Try Again" inexistente).
- **Thread:** `_publish_pr_from_progress` já roda na app thread (`call_from_thread`, L1119) — chamada direta; `_push_and_exit` roda em worker (`_do_push`) — o aviso volta por `call_from_thread` (DOM não é consultável de worker; `call_from_thread` levanta se chamado da própria app thread).
- Os dois call sites do attach (L1241 update, L1490 create) passam a fechar por `_finish_attach`.

### 8. Docs
- `docs/suggested-reviewers.md` + `.pt_br/.pt_pt/.es_es/.fr_fr` (paridade linha a linha, 5 cópias): §3.1 (campo/hint), §3.2 (read-back + modal), §4 (como o login é resolvido: commit → noreply → search; não resolvido = exibido, não enviado), §5 (módulo `reviewer_resolution.py`, view dict com `candidates`, retorno do `request_pull_request_reviewers`).
- Emenda datada em `docs/plans/ADR-002-reviewer-suggestion.md` (Q1-Q13, achado do 422, `reviewers` ainda morto).
- `docs/plans/glossary-reviewer-suggestion.md`: atualizar linhas (`candidato`, `handle`, `email_to_handle`, `requested_reviewers`, `attach`, `view`) e acrescentar `resolução por commit`, `read-back`, `item descartado`.
- `docs/claude-code/reports/develop_natan/2026-09-17_reviewer_login_resolution.md` (template obrigatório do CLAUDE.md).
- `docs/survey/20260917_reviewer_login_resolution_surveyfacts.md` — levantamento da sessão de grill (contexto, decisões das 4 rodadas, fatos), no formato dos surveys existentes.

## Testes

**Ajustar:** `tests/test_main_suggest_reviewers.py` (fake ganha `get_commit_author_login`; view com `candidates`), `tests/test_pr_publish_app.py` (`_suggestion_view` com `candidates`; `_Recorder.request_pull_request_reviewers` passa a **devolver** a lista), `tests/scm/test_github_provider.py` (fixture 201 com `requested_reviewers`), `tests/scm/test_contract.py` (contrato de retorno; método segue não-abstrato).

**Novos:**
- `tests/test_reviewer_resolution.py` — **regressão do bug reportado**: candidato "Eduarda Leal" sem login + usuário digita "Eduarda Leal" → `logins == []`, um drop com motivo, e `get_user_login` **não** chamado; "Eduarda" não casa com "Eduarda Leal"; prefill não faz chamada; ladders de resolução e de validação.
- `tests/test_reviewer_suggestion.py` — `last_commit_hash` do hit mais recente.
- `tests/test_suggest_reviewers.py` — sufixo `no_login` e quem_map por `identity_key`.
- `tests/test_pr_publish_app.py` — **regressão**: nome digitado nunca vira login enviado; 201 com `requested_reviewers: []` → aviso no `final_message` **e** `NoticeScreen` ativo, com `_prompt_merge` só depois do "Close"; sem avisos, merge imediato; 422 no lote → reenvio um a um mantém os bons.
- `tests/scm/test_github_provider.py` — `get_commit_author_login` (200/`author: null`/`{}`/404/transporte), `get_user_login` (200, 404 sem levantar, charset inválido sem request, 403 levanta).

## Verificação

```bash
GITPR_LANG=en_us python -m pytest tests/ -q        # baseline atual: 1277 passed, 2 skipped, 4 failed
```
Os 4 `failed` do baseline são pré-existentes e **não** são deste escopo (`tests/test_net_timeouts.py` e variantes de locale) — confirmar que seguem sendo exatamente os mesmos, sem nenhum novo. Sem `GITPR_LANG=en_us` dois testes de hint falham por tradução (locale pt_BR da máquina), não por código.

Depois, prova de ponta a ponta no caso real: no checkout `/c/Users/nataniel/projetos/gjb/SIG-Novo`, rodar `gitpr`, publicar um PR e conferir (a) o `Input` pré-preenchido com `@login` quando o commit tem conta ligada; (b) o hint marcando quem não tem login; (c) digitando o nome de quem **tem** login, o revisor aparece em `Reviewers` no PR do GitHub; (d) um `NoticeScreen` aparecendo quando algum item não for anexado; (e) a linha `Reviewers requested on PR #N: [...] -> attached [...]` no log `~/.gitpr/logs/pr_desc/`.

## Riscos

- **Latência antes da TUI:** até 2 chamadas por candidato (top_n=3 → ≤6), timeout 10 s nas duas leituras novas.
- **Commit local não enviado:** `commits/{sha}` → 404 → cai no `email_to_handle` → hint "nenhum login encontrado" (nunca erro).
- **Rate limit secundário:** o reenvio um a um só dispara no caminho de 422.
- Nada é commitado: as mudanças ficam na árvore de trabalho para revisão.
