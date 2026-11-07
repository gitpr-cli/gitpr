# Survey — Fechamento Automático de Issue Multi-Forge (GitLab, Bitbucket, Azure)

- **Data:** 2026-11-06
- **Branch:** `develop_natan`
- **Tarefa:** `multiforge_issue_autoclose`
- **Contexto:** Expansão da feature de fechamento automático de issue (`get_issue`, `get_default_branch`, `closing_line`) de GitHub-only para multi-forge (GitLab, Bitbucket Cloud e Azure DevOps).

---

## 1. Contexto da Tarefa

A implementação inicial do fechamento automático de issues foi desenhada com escopo restrito ao GitHub (ADR-003, SPEC `docs/specs/issue-autoclose/00-SPEC.md`).
Na classe base `ScmProvider` (`src/infrastructure/scm/base.py`), os métodos `get_issue()`, `get_default_branch()` e `closing_line()` foram implementados como não-abstratos levantando `ScmNotSupportedError`.
Além disso, módulos satélites (`resolve_close_issue.py`, `register_created_issue.py`, `issue_registry.py` e `issue_app.py`) possuíam guardas fixas `provider_is_github()` e persistiam o registro em `.gitpr/conf/github.yml`.

O objetivo desta sessão foi investigar e projetar a cobertura multi-forge:
- **GitLab:** Implementação de `get_issue` (iid, state `opened`), `get_default_branch` e `closing_line` (`Closes #N`).
- **Bitbucket Cloud:** Implementação de `get_issue` (id, estados `new`/`open`/`on hold`), `get_default_branch` (`mainbranch.name`) e `closing_line` (`close #N`).
- **Azure DevOps:** Implementação de `get_default_branch` (`defaultBranch`). Manutenção de `ScmNotSupportedError` para `get_issue` e `closing_line` com explicação sobre Work Items.
- **Registro unificado:** Transição transparente de `.gitpr/conf/github.yml` para `.gitpr/conf/issue.yml`.
- **Contrato polimórfico:** Substituição de `provider_is_github()` por verificação baseada em `ScmNotSupportedError`.

---

## 2. Decisões Confirmadas nas Rodadas de Grill

### Rodada 1

| # | Tema | Decisão |
|---|---|---|
| **Q1** | Azure DevOps | **Opção A**: Implementar `get_default_branch` nativo (Azure Repos). Manter `get_issue` e `closing_line` levantando `ScmNotSupportedError` (Azure Boards Work Items). Degradação elegante. |
| **Q2** | Arquivo de Registro | **Opção A**: Caminho canônico unificado `.gitpr/conf/issue.yml`, campo `provider: str` no schema YAML, leitura com fallback de `github.yml`, e `.gitignore` apontando para `issue.yml`. |
| **Q3** | Sintaxe `closing_line` | **Opção A**: GitHub: `close #{number}`; GitLab: `Closes #{number}`; Bitbucket: `close #{number}`. |
| **Q4** | Normalização de Estado | **Opção A**: `IssueInfo` ganha `is_open: bool` (e normalização nos providers para `state="open"` quando aberta), desacoplando o vocabulário cru das forges de `resolve_close_issue`. |
| **Q5** | Guardas `provider_is_github` | **Opção A**: Remoção de checagens nominais de provider em favor de tratamento polimórfico com `ScmNotSupportedError` (`skipped_reason="not-supported"`). |

### Rodada 2

| # | Tema | Decisão |
|---|---|---|
| **Q6** | Migração do Registro | **Opção A**: `load()` lê de `issue.yml` (fallback para `github.yml`); `record()` grava em `issue.yml` e remove `github.yml` legado; `clear()` limpa ambos se existirem. |
| **Q7** | Bitbucket 404 Tracker | **Opção A**: HTTP 404 limpa o registro com `skipped_reason="issue-missing"`, unificando issue deletada e repositório sem issue tracker. |
| **Q8** | Telemetria de Criação | **Opção A**: Registrar `command=f"issue:{provider.name}_create"` e `provider=provider.name` em `issue_app.py`. |
| **Q9** | Documentação e ADR | **Opção A**: Atualizar termos em `CONTEXT.md` e criar `docs/adr/0010-multiforge-issue-autoclose.md`. |

---

## 3. Relatório de Fatos e Mapeamento Técnico

### 3.1 GitLab Provider (`src/infrastructure/scm/gitlab_provider.py`)
- URL do projeto: `self._project_url(repo)` -> `/api/v4/projects/{quoted_id}`.
- `get_default_branch()`: `GET self._project_url(repo)` -> campo `default_branch` (str).
- `get_issue(repo, number, timeout)`: `GET self._project_url(repo, "issues", number)` -> campo `iid`, `title`, `web_url`, `state`.
  - No GitLab, `state` é `"opened"` ou `"closed"`.
  - Normalização: `is_open = (state == "opened")`. `state = "open" if is_open else "closed"`.
  - `is_pull_request = False` (GitLab separa Issues de Merge Requests).
- `closing_line(number)`: `f"Closes #{number}"`.

### 3.2 Bitbucket Provider (`src/infrastructure/scm/bitbucket_provider.py`)
- URL do repositório: `self._repo_url(repo)` -> `/2.0/repositories/{workspace}/{repo_slug}`.
- `get_default_branch()`: `GET self._repo_url(repo)` -> campo `mainbranch.name` (str).
- `get_issue(repo, number, timeout)`: `GET self._repo_url(repo, "issues", number)` -> campo `id`, `title`, `links.html.href`, `state`.
  - No Bitbucket, estados abertos são `{"new", "open", "on hold"}`. Estados fechados: `{"resolved", "closed", "invalid", "duplicate", "wontfix"}`.
  - Normalização: `is_open = (state in {"new", "open", "on hold"})`. `state = "open" if is_open else "closed"`.
  - `is_pull_request = False` (Bitbucket separa Issues de Pull Requests).
- `closing_line(number)`: `f"close #{number}"`.

### 3.3 Azure DevOps Provider (`src/infrastructure/scm/azure_devops_provider.py`)
- URL do repositório: `self._repo_url(repo)` -> `.../_apis/git/repositories/{name}`.
- `get_default_branch()`: `GET self._repo_url(repo)?api-version=7.1` -> campo `defaultBranch`. Extrai branch curta via `_branch_name("refs/heads/main")` -> `"main"`.
- `get_issue()`: Levanta `ScmNotSupportedError(self.name, "Azure DevOps has no issue API resource.")`.
- `closing_line()`: Levanta `ScmNotSupportedError(self.name, "Azure DevOps has no issue closing keyword.")`.

### 3.4 Issue Registry (`src/issue_autoclose/issue_registry.py`)
- Constante `REGISTRY_RELATIVE_PATH`: alterada para `Path(".gitpr") / "conf" / "issue.yml"`.
- Constante `LEGACY_REGISTRY_RELATIVE_PATH`: `Path(".gitpr") / "conf" / "github.yml"`.
- `GITIGNORE_ENTRY`: `".gitpr/conf/issue.yml"`.
- Dataclass `RegisteredIssue`: adicionado campo `provider: str = "github"`.
- `load()`: tenta carregar `issue.yml`; se não existir, tenta `github.yml`.
- `record()`: grava sempre em `issue.yml` com `provider`; remove `github.yml` legado se existir.
- `clear()`: remove `issue.yml` e `github.yml` se existirem.

### 3.5 Use Cases e UI
- `resolve_close_issue.py`:
  - Remove `provider_is_github`.
  - Trata `ScmNotSupportedError` vindo de `get_issue` ou `closing_line` -> `CloseIssueOutcome(skipped_reason="not-supported")`.
  - Valida se `info.is_open` (ou `info.state == "open"`).
- `register_created_issue.py`:
  - Remove `provider_is_github`.
  - Passa `provider.name` para `RegisteredIssue.provider`.
- `src/ui/issue_app.py`:
  - Habilita registro para qualquer forge que suporte criação de issue.
  - Telemetria de criação por forge: `command=f"issue:{self.provider.name}_create"`.
