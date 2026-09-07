# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add multi-forge SCM abstraction and provider support
```

---

## 🎯 Summary

This PR unifies all Git hosting interactions behind a new multi-forge SCM abstraction. It introduces a common provider contract for GitHub, GitLab, Bitbucket and Azure DevOps, detects the active forge from the repository origin, and migrates PR/issue publishing flows to provider-agnostic code. The legacy GitHub-only API becomes a deprecated shim, and a new `gitpr --init` wizard configures provider credentials interactively. Locale files for Spanish, French and Portuguese variants are synchronized with the new provider-specific messages, and the affected test suites are updated and expanded.

## 🛠️ Technical Changes

- Add `src/infrastructure/scm/` with a unified `ScmProvider` contract, domain models (`PullRequestRequest/Result`, `IssueRequest/Result`, `RepoRef`) and error types (`ScmProviderError`, `ScmNotSupportedError`).
- Implement concrete providers for GitHub, GitLab, Bitbucket and Azure DevOps, covering PR/MR create, update, merge, diff fetch, issue creation, comments, open PR/MR listing and `test_connection`.
- Add a provider factory that resolves the SCM from the `origin` remote URL and supports explicit environment-based configuration via `src/config.py`.
- Add new environment variables `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT` and `GITPR_SCM_USERNAME`, with legacy `GITHUB_TOKEN_*` fallback.
- Add `get_origin_remote_url()`, `describe_repo()` and `run_scm_init_wizard()`, wired to `gitpr --init` in `main.py`.
- Migrate PR publishing and issue creation flows (`main.py`, `src/tui_issue.py`, `src/ui/issue_app.py`, `src/ui/pr_publish_app.py`) from legacy GitHub API return tuples to provider-agnostic `PullRequestResult` and `IssueResult` models.
- Replace hardcoded GitHub labels/messages with `{provider}` placeholders and extract reusable localization keys for setup wizard, external linter, MCP, hooks/editors, PR/issue lifecycle, token validation and batch/Map-Reduce processing.
- Deprecate `src/github_api.py` as a compatibility shim delegating to `GitHubProvider` while preserving `(ok, data, status)` tuples and emitting `DeprecationWarning`.
- Expand locale dictionaries: synchronize Spanish (`es`, `es_es`) and French (`fr`, `fr_fr`), add large Portuguese (`pt_br`, `pt_pt`) translation batches, remove duplicate keys, and add new metrics export sample files (CSV/JSON).
- Add/update tests for provider wire behavior, shared contract, factory, init wizard and `core.py`; replace legacy `tests/test_github_api.py` with provider-level tests.

## ⚠️ Impact/Warnings

- **Environment**: New `GITPR_SCM_*` variables are required for non-GitHub providers. For GitHub, the existing `GITHUB_TOKEN_*` fallback still works.
- **Token storage**: Non-GitHub tokens are persisted in `GITPR_SCM_TOKEN_ENCRYPTED`; GitHub keeps the legacy token store.
- **Deprecation**: Direct imports from `src.github_api` still work but now emit `DeprecationWarning`; new code should use `src.infrastructure.scm`.
- **Behavior**: PR/issue flows are no longer GitHub-hardcoded and will detect the provider from the `origin` remote, which may affect existing workflows on non-GitHub repositories.
- **Localization**: Spanish/French/Portuguese files received extensive key additions and duplicate removal; downstream forks may need to re-review translations.
- **Tests**: `tests/test_github_api.py` was removed and replaced by provider-level tests covering the new contract.
- **Database**: No database migrations are required.


close #153