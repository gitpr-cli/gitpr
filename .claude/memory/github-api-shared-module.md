---
name: github-api-shared-module
description: src/github_api.py agora é shim deprecado; chamadas de PR/issue vivem nos providers ScmProvider (src/infrastructure/scm/)
metadata:
  type: reference
  source: docs/plans/ADR-001-scm-abstraction.md
  date: 2026-09-05
  branch: develop_natan
---

Originalmente (2026-08-06) `src/github_api.py` centralizava as chamadas REST do
GitHub com o padrão de tuplas `(ok, data, status)` que **engole exceções**.
Desde a abstração Multi-Forge (2026-09-05) ele é um **shim deprecado**: mesmas
4 assinaturas (`create_pull_request`, `check_existing_pr`,
`update_pull_request`, `merge_pull_request`), mesmas tuplas e
`DeprecationWarning` (stacklevel=2), delegando ao `GitHubProvider`.

O caminho canônico agora é `src/infrastructure/scm/`:

- `base.py` — ABC `ScmProvider` (11 métodos) + dataclasses + `ScmProviderError`
  (`.provider`, `.http_status` — 0 = rede) e `ScmNotSupportedError`.
- Um provider por forge (`github_provider.py`, `gitlab_provider.py`,
  `bitbucket_provider.py`, `azure_devops_provider.py`) — todos **levantam**
  exceções; nenhum print/click em thread.
- `factory.py` — `resolve_scm_provider(config)` (chave `GITPR_SCM_PROVIDER`,
  default `github` com fallback no `GITHUB_TOKEN_ENCRYPTED` legado) e
  `detect_provider_from_remote(url)`.
- Consumidores (main.py, TUI, MCP) devem importar apenas o pacote
  `src.infrastructure.scm` — **nunca** os módulos de provider diretamente.
  Código novo nunca importa `src.github_api.py`.

**Why:** o padrão de tuplas apagava o motivo do erro (reauth 401, rede, 4xx)
e impedia suportar GitLab/Bitbucket/Azure sem duplicar camadas HTTP. A
conversão de exceção → comportamento de UI (tuplas locais, reauth) mora nos
call sites; no shim, `ScmProviderError` é convertido de volta para tuplas.

**How to apply:** para adicionar operação de PR/issue, estenda o ABC e todos
os providers + o contrato de testes (`tests/scm/test_contract.py`); rode
`python -m pytest tests/` e `python -m unittest discover tests -q` (os dois
runners são portão). Para token interativo use
`validate_or_request_scm_token()` em `tui_issue.py` (não a função antiga
`validate_or_request_github_token`, removida). Config via `gitpr --init` →
`core.run_scm_init_wizard()` — persiste só no sucesso
(`GITPR_SCM_TOKEN_ENCRYPTED`, nunca token cru com `set_key`).

Ver também: [[github-token-reauth-flow]], [[claude-md-desatualizado-vs-architecture]]
