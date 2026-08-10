---
name: github-api-shared-module
description: src/github_api.py como módulo compartilhado de chamadas à API REST do GitHub
metadata:
  type: reference
  source: docs/claude-code/reports/develop_natan/2026-08-06_pr_publish_github.md
  date: 2026-08-06
  branch: develop_natan
---

O módulo `src/github_api.py` centraliza todas as chamadas à API REST do GitHub usadas pelo GitPR.
Funções disponíveis:

- `create_pull_request(repo, token, title, body, head, base)` → `POST /repos/{owner}/{repo}/pulls`
- `update_pull_request(repo, token, pr_number, title, body)` → `PATCH /repos/{owner}/{repo}/pulls/{number}`
- `merge_pull_request(repo, token, pr_number, method?)` → `PUT /repos/{owner}/{repo}/pulls/{number}/merge`

Todas as funções retornam `(ok: bool, data: dict, status_code: int)` e usam `requests` com timeout=30s.
Headers incluem `Authorization: token {token}` e `Accept: application/vnd.github.v3+json`.
Erros extraem `response.json().get("message")` com fallback para `response.text`.

**Why:** Antes cada ponto de entrada (TUI, CLI direto) fazia suas próprias chamadas HTTP inline,
duplicando headers, tratamento de erro e parsing de resposta. Centralizar em `github_api.py` permite
reuso consistente e facilita adicionar novas operações (ex: `create_issue`, `list_pull_requests`).

**How to apply:** Sempre que precisar de uma nova chamada à API do GitHub, adicionar a função em
`github_api.py` seguindo o padrão `(ok, data, status)` — NUNCA fazer chamada HTTP inline em TUI
ou CLI. Para autenticação, usar `get_github_token()` de `config.py` que já trata Fernet decrypt
e fallback raw key. Para validação interativa, `validate_or_request_github_token()` em `tui_issue.py`.

Ver também: [[github-token-reauth-flow]]
