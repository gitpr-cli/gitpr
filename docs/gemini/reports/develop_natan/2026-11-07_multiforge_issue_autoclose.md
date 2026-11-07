## Completion Report — Multi-Forge Issue Autoclose

### What was done
- Extended the automatic issue closing feature (`get_issue`, `get_default_branch`, `closing_line`) from GitHub-only to multi-forge architecture supporting GitLab, Bitbucket Cloud, and Azure DevOps.
- Added `is_open: bool = True` field to [`IssueInfo`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/base.py) for normalized forge-agnostic issue state checking.
- Implemented [`GitLabProvider`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/gitlab_provider.py):
  - `get_issue(repo, number)`: fetches issue via `/projects/:id/issues/:iid` and normalizes `"opened"` to `is_open=True, state="open"`.
  - `get_default_branch(repo)`: retrieves default branch via `/projects/:id` (`default_branch`).
  - `closing_line(number)`: returns `"Closes #{number}"` according to GitLab keyword conventions.
- Implemented [`BitbucketProvider`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/bitbucket_provider.py):
  - `get_issue(repo, number)`: fetches issue via `/repositories/{workspace}/{slug}/issues/{number}`, normalizes states `{"new", "open", "on hold"}` to `is_open=True, state="open"`, and handles 404 cleanly when the issue tracker is disabled.
  - `get_default_branch(repo)`: retrieves default branch via `/repositories/{workspace}/{slug}` (`mainbranch.name`).
  - `closing_line(number)`: returns `"close #{number}"` according to Bitbucket keyword conventions.
- Implemented [`AzureDevOpsProvider`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/azure_devops_provider.py):
  - `get_default_branch(repo)`: queries repository details via REST API 7.1 (`defaultBranch`).
  - Explicitly documents and raises `ScmNotSupportedError` for `get_issue` and `closing_line` (Azure DevOps Git repos do not have native issue tracking; work items belong to Azure Boards).
- Unified issue registration in [`IssueRegistry`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/issue_autoclose/issue_registry.py):
  - Canonical storage path migrated to `.gitpr/conf/issue.yml`.
  - Backward-compatible read fallback for legacy `.gitpr/conf/github.yml`.
  - Added `provider: str = "github"` attribute to `RegisteredIssue`.
  - On `record()`, legacy `github.yml` is cleaned up; on `clear()`, both canonical and legacy files are removed.
- Generalized [`register_created_issue`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/issue_autoclose/register_created_issue.py) and [`resolve_close_issue`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/issue_autoclose/resolve_close_issue.py):
  - Removed GitHub-specific checks (`provider_is_github`).
  - Gracefully catches `ScmNotSupportedError` and records `skipped_reason="not-supported"`.
  - Verifies open issue state using normalized `info.is_open`.
- Updated TUI [`IssueApp`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ui/issue_app.py):
  - Enables issue recording after creation for any configured SCM provider.
  - Emits telemetry with `command=f"issue:{provider_name}_create"`.
- Hardened sandbox resilience in [`src/ledger.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ledger.py), [`src/config.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/config.py), and [`src/main.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py) against `PermissionError` when operating in restricted homedir/sandbox environments.
- Created ADR [`docs/adr/0010-multiforge-issue-autoclose.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/adr/0010-multiforge-issue-autoclose.md) and updated [`CONTEXT.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md).
- Added comprehensive unit tests across `tests/scm/` and `tests/issue_autoclose/`, achieving 100% test pass (459 passed, 0 failed).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/infrastructure/scm/base.py` | feat | Added `is_open: bool = True` to `IssueInfo` dataclass |
| `src/infrastructure/scm/gitlab_provider.py` | feat | Added `get_issue`, `get_default_branch`, `closing_line` ("Closes #N") |
| `src/infrastructure/scm/bitbucket_provider.py` | feat | Added `get_issue`, `get_default_branch`, `closing_line` ("close #N") |
| `src/infrastructure/scm/azure_devops_provider.py` | feat | Added `get_default_branch`, explicit `ScmNotSupportedError` on `get_issue`/`closing_line` |
| `src/issue_autoclose/issue_registry.py` | refactor | Migrated storage to `.gitpr/conf/issue.yml`, legacy fallback, added `provider` field |
| `src/issue_autoclose/register_created_issue.py` | feat | Enabled registration for all forges, passing provider name |
| `src/issue_autoclose/resolve_close_issue.py` | feat | Multi-forge resolution, normalized `is_open` validation, handled `ScmNotSupportedError` |
| `src/ui/issue_app.py` | feat | Registered issues for any provider, updated telemetry to `issue:{provider}_create` |
| `src/config.py` | fix | Made `load_dotenv` resilient to `PermissionError`/`OSError` in sandboxed environments |
| `src/ledger.py` | fix | Handled `PermissionError` in `ledger_exists` and `ensure_ledger` |
| `src/main.py` | fix | Wrapped `ledger.ensure_ledger` call in `try...except (PermissionError, OSError)` |
| `CONTEXT.md` | docs | Updated domain definitions for Issue registry and Closing line |
| `docs/adr/0010-multiforge-issue-autoclose.md` | docs | Documented multi-forge issue autoclose design, forge contract, and migration |
| `tests/scm/test_gitlab_provider.py` | test | Unit tests for GitLab `get_issue`, `get_default_branch`, `closing_line` |
| `tests/scm/test_bitbucket_provider.py` | test | Unit tests for Bitbucket `get_issue`, `get_default_branch`, `closing_line` |
| `tests/scm/test_azure_devops_provider.py` | test | Unit tests for Azure DevOps `get_default_branch` and `ScmNotSupportedError` |
| `tests/issue_autoclose/test_issue_registry.py` | test | Migration, roundtrip, fallback, and validation tests for `issue.yml` |
| `tests/issue_autoclose/test_register_created_issue.py` | test | Registration tests across GitHub, GitLab, and Bitbucket |
| `tests/issue_autoclose/test_resolve_close_issue.py` | test | Multi-forge resolution and `not-supported` handling tests |
| `tests/issue_autoclose/test_close_issue_wiring.py` | test | CLI wiring tests for `--close-issue` and `--no-close-issue` flags |

### Impact
- **Functionality:** Users creating issues via `gitpr -is` on GitLab or Bitbucket will now have them automatically linked and closed on PR merge into default branch using forge-specific keywords (`Closes #N` on GitLab, `close #N` on Bitbucket). On Azure DevOps, the attempt gracefully records `skipped_reason="not-supported"` without breaking the PR flow.
- **Performance:** Issue checking is lightweight (single HTTP GET) and only triggered when an issue record is present in the workspace.
- **Compatibility:** Fully backward-compatible with existing `.gitpr/conf/github.yml` files, which are transparently read and migrated on next write.

### Next steps (if applicable)
- In a future phase, explore Azure Boards Work Item linking via AB# syntax (e.g., `Fixes AB#1234`) once Azure DevOps work item tracking integration is designed.
