# Plano — GitPR Multi-Forge: abstração ScmProvider (GitHub/GitLab/Bitbucket/Azure DevOps)

## Contexto

A spec [docs/plans/2026-09-02_multi_skill_gitpr_multiforge_spec.md](docs/plans/2026-09-02_multi_skill_gitpr_multiforge_spec.md) pede generalizar o acesso a forges por trás de uma interface única (`ScmProvider` + factory), seguindo a ordem da sua §10. A exploração do código revelou que a spec foi escrita contra suposições defasadas; as divergências foram **entrevistadas e aprovadas** pelo usuário (Rodadas 1–3 do grilling) e estão registradas abaixo como decisões vinculantes + desvios a documentar no ADR.

Fatos-chave descobertos (diferem da spec):
- `src/ai_providers.py` **não** tem Strategy Pattern (dispatch funcional) — o ABC será o primeiro do projeto (base hoje: dicts planos, sem dataclasses).
- `src/github_api.py` existe com 4 funções que **engolem exceções** e retornam tuplas `(ok, data, status)`: `create_pull_request` (L22), `check_existing_pr` (L72), `update_pull_request` (L98), `merge_pull_request` (L134). Header `Authorization: token {token}` (não Bearer). Não tem diff/list/comment/test_connection.
- Consumidores reais: **só** `src/main.py` (publish direto L1762/1778) e `src/ui/pr_publish_app.py` (create :1307, check :913, update :1100, merge :1192). `core.py`, MCP server e `action.yml` não tocam `github_api`. Coupling extra: `issue_app.py:109` (POST /issues inline no F3) e `config.validate_github_token` (config.py:408, `/user` hardcoded).
- Config = dotenv plana `~/.gitpr/.env`; **não existe** `.gitpr/config.schema.yml` nem YAML de config. Fernet = `security.encrypt_data`/`decrypt_data`; padrão de chave: raw primeiro, `_ENCRYPTED` depois (config.py:143 `get_api_key`).
- Flags: `--init` **não existe** (wizard é `--install`); `--issue` usa `get_github_repo_info` (issue_engine.py:19) e `-ch` usa display local.
- Testes: **370 funções** em 21 arquivos planos; `unittest.mock.patch` + `monkeypatch`; sem conftest/responses/pytest-mock. i18n: 6 arquivos `langs/*.json`; `test_i18n` **barra** chave faltante/órfã; helper `python tests/sync_i18n.py` reconstrói os 6.

## Decisões vinculantes (aprovadas no grilling)

1. **Passe único** na ordem da §10 com suíte completa como portão por etapa. **Nunca** `git add`/`commit`/`push` — tudo fica no working tree.
2. **ABC estendido**: contrato da §3 + `check_existing_pull_request`, `update_pull_request` e `create_issue` (11 métodos abstratos) — necessário para TUI e fluxo de issues.
3. **Erros**: providers **levantam** `ScmProviderError(provider, http_status, message)` em 4xx/5xx e falha de rede (`http_status=0`); `ScmNotSupportedError` para Azure `create_issue`. Convenção de tuplas morre dentro dos providers; a tradução p/ o comportamento de UI atual fica nos call sites (main/pr_publish_app).
4. **Issues migram também**: `create_issue` em GitHub/GitLab/Bitbucket; Azure levanta not-supported.
5. **Config dotenv plana**: `GITPR_SCM_PROVIDER` (default `github`), `GITPR_SCM_TOKEN` (CI/raw) + `GITPR_SCM_TOKEN_ENCRYPTED` (Fernet, escrita pelo wizard), `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` — em `DEFAULT_CONFIG`/`setup_environment`. `resolve_scm_provider` com provider `github` sem token cai no `GITHUB_TOKEN_ENCRYPTED` existente. Config ausente → github → comportamento atual byte a byte.
6. **Flag nova `--init`** (fluxo da §6f); `--install` intacto.
7. **Azure**: `RepoRef.workspace = "{org}/{project}"` (display apenas; org/project vêm de `extra`); `get_pull_request_diff` = resumo textual dos `changes[]` da última iteration (sem diff unificado — limitação documentada); `create_issue` = `ScmNotSupportedError`.
8. **`github_api.py` vira shim deprecado** (mesmas 4 assinaturas, mesmas tuplas, `DeprecationWarning`), delegando ao GitHubProvider. Código interno deixa de importá-lo.
9. **RepoRef**: workspace = GitHub owner / GitLab namespace completo c/ subgrupos / Bitbucket workspace / Azure display-only. GitLab: `id`=`number`=`iid` (nunca o id global); project path sempre `quote(..., safe="")`. Bitbucket: auth Basic (username + App Password), `username` obrigatório no `__init__` (erro i18n claro, mesmo p/ Azure org/project) — fail-fast.
10. **ADRs/glossário**: PT-BR em `docs/plans/`. Glossário criado na Etapa 1 e atualizado ao longo; ADR-001 na Etapa 9 com a lista de desvios.
11. GitHub byte-parity: caminhos com `provider.name == "github"` reusam chaves i18n existentes verbatim; chaves novas interpolam `{provider}` e, formatadas com "GitHub", reproduzem o texto atual.

## Arquitetura alvo

```
src/infrastructure/scm/            NOVO
├── __init__.py                    # re-exports públicos
├── base.py                        # ScmProvider ABC + dataclasses + erros
├── github_provider.py             # extraído de github_api.py (raise)
├── gitlab_provider.py / bitbucket_provider.py / azure_devops_provider.py
└── factory.py                     # _REGISTRY + resolve_scm_provider + detect_provider_from_remote
src/github_api.py                  # REESCRITO: shim deprecado (tuplas + DeprecationWarning)
src/config.py                      # + DEFAULT_CONFIG GITPR_SCM_*, get_scm_settings(), get_scm_token()
src/core.py                        # + get_origin_remote_url(), describe_repo(), run_scm_init_wizard()
src/main.py                        # + --init; publish e issue flows resolvem provider/repo_ref
src/ui/pr_publish_app.py           # plumbing provider (create/check/update/merge)
src/ui/issue_app.py                # F3 → provider.create_issue
src/tui_issue.py                   # validate_or_request_github_token → validate_or_request_scm_token
src/issue_engine.py                # intocado (fluxo -ch não migra)
tests/scm/__init__.py + tests/scm/test_{contract,github_provider,github_api_shim,gitlab_provider,azure_devops_provider,bitbucket_provider,factory,init_wizard}.py   # NOVOS
tests/test_github_api.py           # DELETADO (30 testes migram p/ tests/scm/test_github_provider.py)
tests/test_pr_publish_linter_modal.py  # 1 patch retarget
langs/*.json                       # sync + traduções (6 arquivos)
docs/plans/ADR-001-…md, glossary-…md    # NOVOS (PT-BR)
CLAUDE.md, docs/ARCHITECTURE.md, CHANGELOG.md, .claude/memory/github-api-shared-module.md  # atualizados
docs/claude-code/reports/develop_natan/2026-09-04_scm_multiforge_providers.md  # relatório final obrigatório
```

## Contrato final — `src/infrastructure/scm/base.py`

Dataclasses da §3 (`PullRequestRequest` c/ `title, description, source_branch, target_branch, draft=False, labels=[], reviewers=[]`; `PullRequestResult(id, url, number, state, source_branch, target_branch, provider)`; `RepoRef(raw, workspace, name, provider)`) **+** `IssueRequest(title, description)` e `IssueResult(id, url, number, provider)`. `ScmProviderError(Exception)` com `.provider/.http_status/.message`; `ScmNotSupportedError(ScmProviderError)`.

`ScmProvider(ABC)`: `name: str`; `__init__(token, base_url=None, **kwargs)` com fail-fast por provider (Azure sem org/project, Bitbucket sem username → `ScmProviderError` i18n nomeando a env var); métodos abstratos: `default_base_url`, `parse_repo_ref`, `create_pull_request`, `get_pull_request_diff`, `list_open_pull_requests`, `add_comment`, `merge_pull_request`, `test_connection` (spec §4) **+** `check_existing_pull_request(repo, source_branch) -> Optional[PullRequestResult]` (PR aberto do branch ou None; levanta como qualquer método), `update_pull_request(repo, pr_id, title=None, description=None) -> PullRequestResult` (envia só campos fornecidos), `create_issue(repo, req) -> IssueResult`. Helper concreto `with_token(token)` (reauth). Timeouts espelhando o atual: create 30, demais 15, test_connection 10. `parse_repo_ref` levanta `ValueError` (mensagem estática EN, não-i18n) quando não parseia.

Endpoints por provider: **tabelas da §4 da spec são autoritativas** — implementar conforme elas; cada provider só anota desvios:
- GitHub: manter `Authorization: token` (não Bearer da §4.1 — desvio nº 3 do ADR); payload de create com 4 chaves exatas (draft só quando True); check com params `head=owner:branch, state=open`; merge com `json={}` se strategy=="merge".
- GitLab: `quote(f"{workspace}/{name}", safe="")`; MR create 201 → id/number/url = `iid`/`web_url`; draft vira prefixo `"Draft: "` no título; diff = join de `changes[].diff`; check via `?state=opened` + filtro `source_branch`.
- Bitbucket: `auth=(username, token)`; create com body aninhado `source.branch.name`/`destination.branch.name`; diff texto plano; list em `values[]` com `state=OPEN`; comentário `{"content": {"raw": ...}}`; merge `{"merge_strategy": strategy}`; **issue requer Issue Tracker habilitado no repo (documentar)**.
- Azure: `auth=("", token)`; `api-version=7.1` em toda URL; `{base}/{org}/{project}/_apis/git/repositories/{quote(name)}`; refs `refs/heads/...`; diff = resumo `"{path} (+{additions} -{deletions})"` da última iteration com changes; check por `searchCriteria.status=active` + `sourceRefName`; comentário `{"comments": [{"content": ..., "commentType": 1}], "status": 1}`; merge PATCH `{"status": "completed", "completionOptions": {"mergeStrategy": strategy}}`; test_connection em `{base}/{org}/_apis/projects/{project}`; create_issue → `ScmNotSupportedError`.

`factory.py`: `_REGISTRY` (registro incremental nas Etapas 2/3/6/7); `resolve_scm_provider(config)` — provider default `"github"`, token GitHub cai em `config.get_github_token()` (import lazy p/ evitar ciclo), repassa extras; provider inválido → `ValueError` i18n listando válidos. `detect_provider_from_remote`: substring case-insensitive `gitlab`→gitlab, `bitbucket`→bitbucket, `dev.azure.com`/`visualstudio.com`→azure_devops, senão github.

## Convenções críticas (barram cada etapa)

1. **i18n é portão**: toda `__("literal")` nova exige `python tests/sync_i18n.py` (raiz do repo) + tradução nas **6** `langs/*.json` antes da suíte. Chave com `{braces}` igual ao próprio valor falha teste; chave órfã também (swap do label `"Create on GitHub"` → `"Create Issue"` no F3 cria órfã — sync na Etapa 5).
2. Chaves novas interpolam `{provider}` ("GitLab"/"Bitbucket"/"Azure DevOps"); para github reusar chaves existentes verbatim (byte-parity). Mensagens de rede/validação do GitHub reusam as chaves atuais de github_api.py/validate_github_token.
3. Testes rodam sob **pytest e unittest discover** — `tests/scm/__init__.py` obrigatório. Novos arquivos: estilo `unittest.TestCase` + `mock.patch` (convenção dominante); `monkeypatch` aceito.
4. Threads da TUI (pr_publish_app) trocam stdout — providers/logs novos **nunca** dão `print`/`click.*` em thread; só `self._log`. Ctors de PrPublishApp/IssueApp **não fazem I/O** (senão os 30 testes headless `run_test` fazem rede).
5. Nunca `set_key` com token cru — só `GITPR_SCM_TOKEN_ENCRYPTED` via `encrypt_data` (CI usa `GITPR_SCM_TOKEN` raw).

## Etapas (ordem da §10, sem commits)

**Etapa 1 — `base.py` + esqueleto + contrato.** Cria `src/infrastructure/{__init__,scm/{__init__,base}}.py`, `tests/scm/{__init__,test_contract}.py` (harness parametrizado registrando providers conforme entram nas Etapas 2–7; asserts: herda ABC, 11 métodos overridden, `name`, `default_base_url()`, instanciação mínima, fail-fast Azure/Bitbucket, `with_token`). Cria **glossário** `docs/plans/glossary-scm-multiforge.md` (PT-BR; termos: forge, RepoRef/workspace por forge, PR/MR, iid vs id, App Password vs PAT, api-version, env keys SCM). **Gate**: suíte completa (370) verde.

**Etapa 2 — GitHubProvider + shim + migração de testes** (maior etapa). `github_provider.py` (~250 linhas): helpers `_extract_error_message` (algoritmo 1:1) e wrapper `_request` que converte qualquer exceção → `ScmProviderError(status=0)` e status inesperado → raise com mensagem; métodos da §2 do contrato; reusar chaves i18n de rede do github_api atual. `github_api.py` reescrito como shim (4 funções, assinaturas/tuplas idênticas, `warnings.warn` DeprecationWarning stacklevel=2; mapeia `repo_info` string → `RepoRef`; converte `ScmProviderError` de volta p/ tuplas). **Migra** os 30 testes: deleta `tests/test_github_api.py`, cria `tests/scm/test_github_provider.py` — patch string `src.github_api.requests.<verb>` → `src.infrastructure.scm.github_provider.requests.<verb>`; cenários de erro passam a `assertRaises(ScmProviderError)` com `e.http_status`; sucesso idêntico (URL/headers/json/timeouts). Novos testes: `create_issue`, `test_connection`, `parse_repo_ref` (https/ssh/.git), `with_token`. Novo `tests/scm/test_github_api_shim.py` (~6: delegação mantém tuplas, DeprecationWarning, `_extract_error_message`). Gate: suíte cheia.

**Etapa 3 — GitLabProvider.** `gitlab_provider.py` + `tests/scm/test_gitlab_provider.py` (~26: sucesso/erro por método, assert de urlencode `group%2Fsubgroup%2Fproj`, mapeamento iid, parse de subgrupos, self-managed base_url). Gate: suíte cheia.

**Etapa 4 — `factory.py`** (github+gitlab registrados), re-exports no `__init__.py`, `tests/scm/test_factory.py` (registry, ValueError com lista, fallback github-token via `config.get_github_token` mockado, tabela de detecção: gitlab.com, git@gitlab.com, self-managed, bitbucket.org, dev.azure.com, *.visualstudio.com, github.com, junk→github). Gate: suíte cheia.

**Etapa 5 — Integração main/core/TUI** (a cirúrgica; sub-gate no meio: `pytest tests/test_pr_publish_app.py tests/test_pr_publish_linter_modal.py`).
- 5.1 `config.py`: 7 chaves em `DEFAULT_CONFIG`; `get_scm_token()` (raw → decrypt, espelhando `get_api_key`); `get_scm_settings() -> dict`; `get_scm_provider()` conveniência.
- 5.2 `core.py`: `get_origin_remote_url()` (git remote get-url origin, `errors="replace"`, nunca imprime) e `describe_repo(repo_ref)` (display `workspace/name` — para GitHub idêntico a `get_repo_name()`). `get_repo_name`/`get_base_branch`/`run_install_wizard` intactos (metrics/cache/MCP dependem).
- 5.3 `tui_issue.py`: `validate_or_request_scm_token(provider, repo_display) -> (token, provider)` — loop com `provider.test_connection()`, 401 → reauth, rede → mensagens; instruções de auth: github = corpo atual, outros = genérico; salva em `GITPR_SCM_TOKEN_ENCRYPTED` (github legado sem config SCM continua salvando `GITHUB_TOKEN_ENCRYPTED`). Deletar `validate_or_request_github_token` após migrar os 3 imports de main.py (L928/1457/1746).
- 5.4 `pr_publish_app.py`: remove import L24; ctor ganha `provider=None, repo_ref=None` com fallback legado lazy (GitHubProvider+RepoRef de `repo_info.partition("/")`) — 30 testes TUI existentes continuam construindo com os mesmos args; **seam** module-level `_check_existing_pull_request(provider, repo_ref, head_branch)` (engole `ScmProviderError` → None, comportamento do check antigo) — alvo do patch do teste L128; 4 call sites viram try/except mapeando p/ os locals `(ok, data, status)`/`up_ok...` e **corpos `if ok / elif status == 401 / else` intactos**; sucesso de create monta `data = {"url": result.url, "number": result.number}`; merge: sucesso → `_on_merge_success`, raise → `_on_merge_failure(..., e.message, e.http_status)` (modal 405 intacto); log de progresso do create vira chave `{provider}`; auto-merge `GITPR_AUTO_MERGE` intacto.
- 5.5 `test_pr_publish_linter_modal.py:128`: retarget p/ `src.ui.pr_publish_app._check_existing_pull_request` retornando `PullRequestResult` fake. `test_pr_publish_app.py` sem mudanças.
- 5.6 `main.py` publish flow (L1411-1516 + `_publish_pr_directly` L1757): resolve `raw_remote → detect (se provider vazio) → resolve_scm_provider → parse_repo_ref` com `ValueError` → `⚠️ Configuration error` vermelho + return; `--no-edit` e TUI usam `validate_or_request_scm_token`/`provider.with_token` por iteração do reauth; `_publish_pr_directly` recebe provider/repo_ref e faz boundary mapping (401 → chave existente github / nova `{provider}`).
- 5.7 `issue_app.py`: ctor `provider=None, repo_ref=None` (fallback legado); F3 remove o POST inline e o `import requests`; usa `provider.create_issue` → created/reauth (401)/erro/`ScmNotSupportedError` → mensagem "salve localmente (F2)"; binding F3 label → `"Create Issue"`.
- 5.8 i18n: sync + traduzir chaves novas (tabela §7 da spec do agente; ~30 chaves) nas 6 línguas.
- 5.9 Testes: `get_origin_remote_url` em test_core.py; verificação manual `gitpr --no-publish`/`-c` num repo GitHub sem config SCM (byte-parity).
**Gate**: suíte cheia + 34 testes TUI verdes.

**Etapa 6 — AzureDevOpsProvider** + testes (~26: fail-fast org/project com nome da env, api-version em toda URL, auth `("", token)`, resumo de diff da última iteration, refs/heads, threads, merge PATCH, create_issue not-supported). Registra no factory. Gate: suíte cheia.

**Etapa 7 — BitbucketProvider** + testes (~26: auth kwarg, body aninhado, values[], diff texto). Registra no factory (registry completo → contrato cobre 4 classes). Gate: suíte cheia. E2E manual: GitHub novamente + GitLab/Bitbucket/Azure só com mocks (sem token/repo reais disponíveis — anotar no relatório).

**Etapa 8 — `--init`.** `core.run_scm_init_wizard()` (após `run_install_wizard`, mesmo tom): banner → `get_origin_remote_url()` (None → msg vermelha) → `detect_provider_from_remote` → confirma → prompts (base_url p/ não-github; org/project se azure; username se bitbucket; token `hide_input=True`; instruções github reusam as atuais via import lazy) → instancia provider → `test_connection()` (3 tentativas) → **persiste só no sucesso** via `set_key` (`GITPR_SCM_PROVIDER`; `GITPR_SCM_TOKEN_ENCRYPTED = encrypt_data(raw)`; campos extras quando presentes). `main.py`: opção Click `--init` + dispatch ao lado do bloco `--install`. Testes `tests/scm/test_init_wizard.py` (~8, mocks de remote/test_connection/set_key/click — nada persiste em falha). Gate: suíte cheia.

**Etapa 9 — Docs + i18n final.** Não criar `.gitpr/config.schema.yml` (não existe; desvio registrado). sync_i18n final + traduções completas. Escrever `docs/plans/ADR-001-…md` (PT-BR) com a decisão, alternativas (flags por forge; camadas HTTP duplicadas) e os **10 desvios aprovados**: (1) ABC estendido (3 métodos), (2) raise em vez de tuplas, (3) header `token` não Bearer, (4) dotenv plano no lugar do YAML da §2/§6, (5) workspace Azure display-only, (6) diff Azure = resumo estruturado, (7) issues Bitbucket exigem Issue Tracker, (8) create_issue Azure not-supported, (9) shim github_api mantido, (10) `labels`/`reviewers` reservados não consumidos. Atualizar CLAUDE.md (árvore `infrastructure/`, env vars SCM, github_api → shim deprecado), `docs/ARCHITECTURE.md`, `CHANGELOG.md` (`## [Unreleased]`), `.claude/memory/github-api-shared-module.md`. Gate: suíte cheia.

**Etapa 10 — Portão final + relatório.** `python -m pytest tests/ -q` (370 antigos + ~160 novos ≈ 530) e `python -m unittest discover tests -q`; sanity CLI `gitpr --no-publish` / `gitpr -c` / `gitpr --status`; escrever `docs/claude-code/reports/develop_natan/2026-09-04_scm_multiforge_providers.md` (template CLAUDE.md, contagens por etapa, notas de verificação manual).

## Fora de escopo (confirmado)

OAuth2 interativo; Bitbucket Server/DC; GitHub Enterprise Server; webhooks de entrada; UI/TUI nova; fluxo `-ch` (chat) e MCP `get_git_context`; `validate_github_token` (config.py) fica para estabilidade de API sem callers internos; `issue_engine.get_github_repo_info` fica.

## Riscos principais

1. **i18n como portão absoluto** — sync+tradução (6 arquivos, 5 línguas) em toda etapa que toca string de usuário.
2. **Byte-parity GitHub** — payload/headers/timeouts exatos assertados pelos testes migrados; chaves github existentes não podem mudar de texto.
3. **Testes TUI headless** (30+4) — ctor sem I/O + único retarget de patch (seam); não quebrar `run_test` async.
4. **Threads com stdout trocado** — nada de `print`/`click` dentro de providers.
5. **`tests/scm/__init__.py`** obrigatório para unittest discover; rodar os dois runners.
6. **GitLab iid vs id** e **Azure repositoryId com espaços** (`quote`) — erros silenciosos de alvo se esquecidos.
