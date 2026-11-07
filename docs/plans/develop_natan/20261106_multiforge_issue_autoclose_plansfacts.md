# Plano de Execução — Fechamento Automático de Issue Multi-Forge

- **Data:** 2026-11-06
- **Branch:** `develop_natan`
- **Tarefa:** `multiforge_issue_autoclose`

---

## 1. Objetivos

1. Implementar `get_issue()`, `get_default_branch()` e `closing_line()` nos providers `GitLabProvider` e `BitbucketProvider`.
2. Implementar `get_default_branch()` no `AzureDevOpsProvider`, mantendo `get_issue()` e `closing_line()` com `ScmNotSupportedError`.
3. Estender `IssueInfo` com `is_open: bool = True` e normalização consistente de estado.
4. Generalizar `IssueRegistry` para usar `.gitpr/conf/issue.yml` com suporte a `provider` e migração/fallback transparente de `.gitpr/conf/github.yml`.
5. Atualizar `register_created_issue.py`, `resolve_close_issue.py` e `src/ui/issue_app.py`, substituindo guardas `provider_is_github` por polimorfismo com `ScmNotSupportedError`.
6. Criar ADR `docs/adr/0010-multiforge-issue-autoclose.md` e atualizar termos no `CONTEXT.md`.
7. Criar e atualizar testes unitários abrangentes cobrindo todos os providers e casos de borda.

---

## 2. Ordem de Execução

### Etapa 1: Atualização de Domínio e Contratos Base
- Modificar `src/infrastructure/scm/base.py`:
  - `IssueInfo`: adicionar `is_open: bool = True`.

### Etapa 2: Implementações nos Providers SCM
- `src/infrastructure/scm/gitlab_provider.py`:
  - `get_issue(repo, number, timeout)`: `GET /projects/:id/issues/:issue_iid`.
  - `get_default_branch(repo, timeout)`: `GET /projects/:id`.
  - `closing_line(number)`: `f"Closes #{number}"`.
- `src/infrastructure/scm/bitbucket_provider.py`:
  - `get_issue(repo, number, timeout)`: `GET /2.0/repositories/{workspace}/{repo_slug}/issues/{number}`.
  - `get_default_branch(repo, timeout)`: `GET /2.0/repositories/{workspace}/{repo_slug}`.
  - `closing_line(number)`: `f"close #{number}"`.
- `src/infrastructure/scm/azure_devops_provider.py`:
  - `get_default_branch(repo, timeout)`: `GET _repo_url(repo)?api-version=7.1` -> `defaultBranch`.

### Etapa 3: Issue Registry e Registro Multi-Forge
- `src/issue_autoclose/issue_registry.py`:
  - Definir `REGISTRY_RELATIVE_PATH = Path(".gitpr") / "conf" / "issue.yml"`.
  - Definir `LEGACY_REGISTRY_RELATIVE_PATH = Path(".gitpr") / "conf" / "github.yml"`.
  - `RegisteredIssue`: adicionar campo `provider: str = "github"`.
  - `load()`: suporte a ler `issue.yml` ou `github.yml`.
  - `record()`: grava `issue.yml`, remove `github.yml` se existir, adiciona `.gitpr/conf/issue.yml` ao `.gitignore`.
  - `clear()`: remove ambos.
- `src/issue_autoclose/register_created_issue.py`:
  - Remover `if not provider_is_github(provider)`.
  - Gravar `provider=provider.name`.

### Etapa 4: Resolução de Fechamento e Integração UI
- `src/issue_autoclose/resolve_close_issue.py`:
  - Remover `if not provider_is_github(provider)`.
  - Capturar `ScmNotSupportedError` ao chamar `provider.get_issue()` ou `provider.closing_line()` -> retornar `skipped_reason="not-supported"`.
  - Avaliar `info.is_open` e `info.state == "open"`.
- `src/ui/issue_app.py`:
  - Habilitar registro para forges suportadas.
  - Telemetria de criação de issue por provider: `command=f"issue:{self.provider.name}_create"`.

### Etapa 5: Testes Unitários
- Testes de `GitLabProvider`: `get_issue` (aberta, fechada, 404, rede), `get_default_branch`, `closing_line`.
- Testes de `BitbucketProvider`: `get_issue` (aberta nos diferentes estados, fechada, 404 tracker, rede), `get_default_branch`, `closing_line`.
- Testes de `AzureDevOpsProvider`: `get_default_branch` e `ScmNotSupportedError` em `get_issue`/`closing_line`.
- Testes de `IssueRegistry`: migração de `github.yml` para `issue.yml`, limpeza dupla, campo `provider`.
- Testes de `resolve_close_issue`: providers suportados e não-suportados, skips e aceitações.

### Etapa 6: Documentação e ADR
- Criar `docs/adr/0010-multiforge-issue-autoclose.md`.
- Atualizar `CONTEXT.md`.
