# Completion Report — Resolução do login do revisor: o attach que não chegava ao PR

## What was done

Corrigido o bug relatado — *"quando digito o nome do reviewer sugerido no campo não aparece no pull
request a sugestão no forge (testei com o github)"* — executando o plano
`docs/plans/20260917_correcao_sugestao_revisores.md`, derivado do grill de 4 rodadas registrado em
`docs/survey/20260917_reviewer_login_resolution_surveyfacts.md`.

O sintoma eram **duas falhas silenciosas encadeadas**, não uma:

1. **Prefill vazio.** `_reviewer_suggestion_view()` montava `handles` só com
   `provider.email_to_handle()`, que enxerga apenas e-mails `users.noreply.github.com` ou com
   e-mail **público** no GitHub. Com e-mail corporativo (o caso real: `eduardaleal@grafjb.com.br`)
   nada resolve, o `Input` nasce vazio e o hint mostra apenas o **nome** — a única identidade que a
   UI oferece.
2. **Attach não verificado.** `_attach_reviewers()` repassava os valores do campo **verbatim** para
   `request_pull_request_reviewers()`. O usuário digita o nome que a UI mostrou, a CLI o envia como
   se fosse login, e o GitHub responde **201 sem anexar ninguém**. A linha do log foi escrita porque
   o `_request()` retornou sem levantar — sucesso aparente, revisor ausente, aviso nenhum.

Evidência de origem (log real da execução anterior, `~/.gitpr/logs/pr_desc/pr_desc_w7YW-kabx4-8xAg.log`):

```text
[2026-09-16 19:06:10] Reviewers requested on PR #1068: ['Eduarda Leal']
```

A correção fecha as quatro lacunas do caminho: **resolver** a identidade antes da TUI (commit →
noreply → search), **validar** o que foi digitado no attach, **ler de volta** quem o forge
realmente anexou, e **avisar** de forma impossível de não ver o que não entrou.

### 1. `src/reviewer_resolution.py` — módulo novo (159 linhas)

Módulo plano, sem I/O próprio, **que nunca levanta**: `resolve_candidates()` (antes da TUI) e
`resolve_typed_reviewers()` (no attach). A escada por valor é prefill (sem requisição) → casamento
**exato e normalizado** com um candidato → e-mail → `GET /users/{login}`. O que não resolve sai em
`ResolutionOutcome.dropped` como `(valor, motivo_i18n)` e **nunca é enviado como veio**. O acesso ao
provider é duck-typed por `getattr`, então fakes e forges sem os métodos novos continuam funcionando.

### 2. Camada SCM — o contrato passou a dizer o que aconteceu

| Mudança | Detalhe |
|---|---|
| `request_pull_request_reviewers(...) -> list[str]` | Devolve os logins **realmente anexados**, relidos do corpo do `201` (`requested_reviewers`). Lista vazia = o forge aceitou e ignorou. Segue **não-abstrato** na base (default `ScmNotSupportedError`) |
| `get_commit_author_login(repo, sha)` | `GET /repos/{o}/{r}/commits/{sha}` → `author.login`. `None` para 404/422/transporte/`author` nulo ou `{}`; **nunca levanta** |
| `get_user_login(login)` | `GET /users/{login}`, esperado `{200, 404}`. Valida o charset **antes** de qualquer requisição (`"Eduarda Leal"` não custa rede); 403/timeout **levanta** — ausência não é confundida com indisponibilidade |

GitLab/Bitbucket/Azure intocados.

### 3. `src/reviewer_suggestion.py` e `src/suggest_reviewers.py`

`ReviewerCandidate` ganhou `last_commit_hash` (insumo da via primária); `_identity_key` foi
promovida a pública (`identity_key(name, email)`) e ganhou a companheira `normalize_identity(value)`
(strip + casefold). No hint, `format_candidate_line(..., no_login=True)` acrescenta o aviso de "nenhum
login encontrado" — **bug secundário corrigido de passagem**: o `who_map` era indexado pelo e-mail
cru enquanto a consulta usava `normalize_email()`, então um e-mail com maiúscula escondia o `@handle`.

### 4. `src/ui/pr_publish_app.py` — attach verificado + `NoticeScreen`

`_attach_reviewers()` resolve, envia e **lê de volta**; lote recusado com `422` (tudo-ou-nada, caso
do autor do PR) é reenviado **um a um**, para que um handle ruim não derrube os bons. Qualquer item
que não terminou no PR vira aviso em duas camadas: a linha no `final_message` e um **`NoticeScreen`**
novo (título + mensagem + botão único `Close`) empilhado **antes** do prompt de merge — nos dois
caminhos, create (app thread) e update (`_do_push`, worker → `call_from_thread`).

### 5. i18n — 7 chaves nos 6 pacotes + bump

A chave genérica de placeholder foi trocada por `GitHub login, name or email, comma separated` e as 7
chaves novas têm tradução real em `es`, `es_es`, `fr`, `fr_fr`, `pt_br` e `pt_pt`;
`src/updater.py`: `__lang_version__` v0.0.26 → **v0.0.27**.

### 6. Documentação

Família `docs/suggested-reviewers.*` (5 cópias, **126 linhas cada**, paridade verificada), emenda
datada no ADR-002, glossário com 4 termos novos + 6 linhas atualizadas, survey do grill e este
relatório.

## Changed files

### Novos

| File | Change type | Description |
|------|-------------|-------------|
| `src/reviewer_resolution.py` | feat | Identidade → login: `ResolvedReviewer`, `ResolutionOutcome`, `resolve_candidates()`, `resolve_typed_reviewers()`, `match_candidate()`; nunca levanta |
| `tests/test_reviewer_resolution.py` | test | 18 testes (+5 subtests), incluindo a **regressão do bug relatado** (nome digitado nunca submetido) |
| `docs/survey/20260917_reviewer_login_resolution_surveyfacts.md` | docs | Levantamento do grill: log de origem, fatos de API, Q1–Q15 |
| `docs/plans/20260917_correcao_sugestao_revisores.md` | docs | O plano aprovado (renomeado para a convenção `.md` do projeto) |

### Alterados

| File | Change type | Description |
|------|-------------|-------------|
| `src/ui/pr_publish_app.py` | fix | `_attach_reviewers` resolve/verifica, `NoticeScreen`, `_unattached_warnings`, `_request_reviewers_one_by_one`, `_after_attach_continue` [+222/−38] |
| `src/main.py` | fix | `_reviewer_suggestion_view` resolve candidatos, monta `who_map` por `identity_key`, marca `no_login` e entrega `resolutions` [+21/−17] |
| `src/infrastructure/scm/github_provider.py` | feat | Read-back do `201` + `get_commit_author_login()` + `get_user_login()` [+59/−4] |
| `src/suggest_reviewers.py` | fix | Sufixo `no_login` no hint; `who_map` consultado por `identity_key` (bug secundário) [+19/−12] |
| `src/reviewer_suggestion.py` | feat | `last_commit_hash`, `identity_key()` pública, `normalize_identity()` [+19/−3] |
| `src/infrastructure/scm/base.py` | fix | Contrato devolve `list[str]` (logins anexados) — método segue não-abstrato [+5/−1] |
| `langs/*.json` (6 arquivos) | feat | 7 chaves novas com tradução real; placeholder substituído (8 linhas por arquivo) |
| `src/updater.py` | chore | `__lang_version__` v0.0.26 → v0.0.27 (OTA das traduções) |
| `tests/test_pr_publish_app.py` | test | `_Recorder` devolve os anexados; 3 testes novos (nome exibido nunca submetido, 201 sem anexo avisa e bloqueia o merge, 422 reenvia um a um) [+146/−5] |
| `tests/scm/test_github_provider.py` | test | Read-back (201 com corpo vazio, corpo ilegível) + 9 testes dos dois métodos novos [+110/−2] |
| `tests/test_main_suggest_reviewers.py` | test | Fake com `get_commit_author_login`; `resolutions` no view [+40/−4] |
| `tests/test_suggest_reviewers.py` | test | Sufixo `no_login` e casamento por `identity_key` [+32/−1] |
| `tests/test_reviewer_suggestion.py` | test | `last_commit_hash` do hit mais recente [+23] |
| `docs/suggested-reviewers.md` + `.pt_br/.pt_pt/.es_es/.fr_fr` | docs | §3.1 (campo/hint), §3.2 (read-back + modal), §4 (como o login é resolvido), §5 (módulo novo, retorno do método) |
| `docs/plans/ADR-002-reviewer-suggestion.md` | docs | Emenda datada: o defeito, as 15 decisões, os achados de API e o que não mudou [+74] |
| `docs/plans/glossary-reviewer-suggestion.md` | docs | +`resolução por commit`, `read-back`, `item descartado`, `identidade`, `ResolvedReviewer`, `ResolutionOutcome`, `NoticeScreen`; 6 linhas refinadas e 4 notas de fidelidade [+26/−6] |

## Impact

- **Functionality:** digitar login, nome ou e-mail agora **funciona** — o valor é resolvido para um
  handle antes de ser submetido. O que não resolve é **descartado com motivo**, e o que o forge não
  anexou é **detectado pelo read-back**. Falha parcial passa a ser visível: modal que precisa ser
  fechado + linha no `final_message`. Sucesso continua silencioso (nenhum diálogo novo no caminho feliz).
- **Performance:** até 2 requisições por candidato (top_n=3 → ≤6) **antes** da TUI abrir, com timeout
  de 10 s nas duas leituras novas; o commit resolve primeiro e o e-mail só é tentado se ele falhar.
  No attach, requisição extra apenas no caminho de `422` (reenvio um a um).
- **Compatibility:** API pública inalterada para os demais forges (métodos novos são exclusivos do
  GitHub, e a base segue não-abstrata). `ReviewerCandidate` ganhou campo **com default** — construções
  por kwargs não quebram. O retorno de `request_pull_request_reviewers()` muda de `None` para
  `list[str]`: quem ignorava o retorno não é afetado, e é o único ponto de contato alterado.
  `__lang_version__` v0.0.27 faz o OTA baixar as traduções novas na próxima execução.

## Desvios do plano (aprovados)

1. **`resolutions`, não `candidates`** — a chave acrescentada ao view dict carrega `ResolvedReviewer`
   (nome/e-mail/login), não candidatos de blame; o nome do plano descrevia mal o conteúdo.
2. **7 chaves i18n, não 6** — a chave do placeholder do campo foi **substituída** (não convivem duas
   com o mesmo propósito) além das 6 novas.
3. **`⚠️ {value}: {reason}` virou `⚠️ {value}: GitHub rejected this reviewer — {reason}`** — uma chave
   só de placeholders é idêntica ao próprio valor e o `test_identity_keys_with_braces_allowlist` a
   rejeita (o `__()` usa a frase em inglês como chave).
4. **`_candidate_login()` envolve cada chamada do provider em `try/except` próprio** — no plano havia
   só o `try` externo do `resolve_candidates`, e um teste mostrou que ele engolia a via do e-mail
   quando o lookup do commit levantava.
5. **A asserção da regressão virou `provider.calls == [("user", "Eduarda Leal")]`** — o teste esperava
   que nenhuma consulta fosse tentada; quem recusa o nome com espaço é o **provider**, antes de
   qualquer requisição (`tests/scm/test_github_provider.py`), e é lá que essa garantia está provada.
6. **`test_attach_failure_keeps_pr_created_with_warning` passou de 422 para 500** — o `422` deixou de
   ser o "erro genérico" do attach: virou o **caminho de reenvio um a um**, com teste próprio.

## Verificação

Suíte completa na árvore de trabalho (`GITPR_LANG=en_us`, para as asserções de texto inglês):

```
3 failed, 1318 passed, 2 skipped
```

As 3 falhas são **pré-existentes e de ambiente**, sem relação com este trabalho:

| Falha | Causa | Evidência |
|---|---|---|
| `test_net_timeouts.py::TestTimeoutConfig::test_ai_timeout_defaults_to_600` e `::test_invalid_ai_timeout_falls_back_to_default` | `GITPR_AI_TIMEOUT=180` no `~/.gitpr/.env` contra o teste que espera 600 | `AssertionError: 180.0 != 600.0`, arquivo de outra árvore no traceback |
| `test_core.py::TestHooksLanguage::test_the_language_chosen_with_the_lang_flag_is_honoured` | o teste asserta o idioma da máquina (`pt_br`) e a suíte roda forçada em `en_us` | `AssertionError: 'en_us' != 'pt_br'` — é o espelho da escolha de rodar em inglês |

Suítes da feature, isoladas: **86 passed** (`tests/test_reviewer_resolution.py` +
`tests/scm/test_github_provider.py`), **45 passed** (`tests/test_pr_publish_app.py`), **63 passed**
(`tests/test_reviewer_suggestion.py` + `tests/test_suggest_reviewers.py` +
`tests/test_main_suggest_reviewers.py` + `tests/test_i18n.py`).

### Baseline: `HEAD` pristino × árvore de trabalho

Mesmo comando e mesmo ambiente numa cópia de `git archive HEAD` (`PYTHONPATH` apontando para a cópia —
confirmado que `src` resolve para lá e que `src.reviewer_resolution` **não** é importável, ou seja, o
baseline é `HEAD` de verdade e não a árvore de trabalho):

| | `HEAD` pristino | Árvore de trabalho |
|---|---|---|
| Resultado | **4 failed, 1277 passed, 2 skipped** (537 s) | **3 failed, 1318 passed, 2 skipped** |
| `test_net_timeouts::TestTimeoutConfig` (2) | FAIL | FAIL |
| `test_core::TestHooksLanguage::test_the_language_chosen_with_the_lang_flag_is_honoured` | FAIL | FAIL |
| `test_config_app::TestSave::test_template_without_datetime_blocks_the_save` | FAIL | **passa** |

**Nenhuma falha nova em nenhum dos dois lados, e nenhuma delas é da feature.** Os +41 passes são os
testes desta entrega. A única diferença entre as duas colunas é um teste **instável sob carga**:
`test_template_without_datetime_blocks_the_save` conduz um app Textual com `pilot.pause()` e uma
gravação real de arquivo — passa **isolado nos dois lados** (verificado, 2 s cada) e passou na execução
completa da árvore de trabalho; falhou apenas na execução completa do baseline, que rodou com a máquina
carregada. Não é código desta entrega (o teste é do fluxo `config`, intocado) e não é regressão.


### O que só a sua execução real prova

A verificação de ponta a ponta depende do GitHub e do repo corporativo: no checkout do **SIG-Novo**,
rodar `gitpr`, publicar um PR e conferir (a) o `Input` pré-preenchido com `@login` quando o commit tem
conta ligada; (b) o hint marcando quem não tem login; (c) digitando o nome de quem **tem** login, o
revisor aparecendo em *Reviewers* no PR; (d) o `NoticeScreen` no caso parcial; (e) a linha
`Reviewers requested on PR #N: [...] -> attached [...]` em `~/.gitpr/logs/pr_desc/`.

## Next steps

- **Conteúdo OTA:** o bump de `__lang_version__` só passa a casar com o que o GitHub serve depois do
  push para `main` (as 7 chaves viajam no commit). Até lá, uma instalação na v0.0.26 baixa os pacotes
  antigos e as chaves novas caem no texto inglês — que **é** a chave, então a degradação é silenciosa.
- **`.gitpr/metrics/export/gitpr_metrics_2026-09-17.{csv,json}`** estão não rastreados na árvore
  (uma exportação sua de hoje, seguindo a série diária de arquivos já commitados) — não toquei neles.
- Fora do escopo, como o ADR-002 já registra: `PullRequestRequest.reviewers` continua morto (o GitHub
  não aceita reviewers no create), submissão nos forges sem endpoint equivalente e sugestão por
  CODEOWNERS/times ficam para trabalho futuro.
