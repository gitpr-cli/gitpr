# Implementation Plan — Multi-Forge Issue Autoclose (GitLab, Bitbucket, Azure)

- **Date:** 2026-11-06
- **Branch:** `develop_natan`
- **Plan:** `multiforge_issue_autoclose`

## Goal Description
Expand the automatic issue closure feature (`get_issue`, `get_default_branch`, `closing_line`) from GitHub-only to multi-forge. GitLab and Bitbucket will gain full support for reading back issues and generating forge-specific closing keywords in pull request descriptions. Azure DevOps will implement `get_default_branch` for repository operations while gracefully degrading on issue closure via `ScmNotSupportedError`. The local issue tracking registry will be generalized from `.gitpr/conf/github.yml` to `.gitpr/conf/issue.yml` with seamless backward-compatible migration.

## User Review Required
> [!NOTE]
> All key design decisions were aligned and confirmed across 2 rounds of grilling:
> 1. Azure DevOps supports `get_default_branch` and raises `ScmNotSupportedError` on issue operations.
> 2. Local registry path is `.gitpr/conf/issue.yml` with transparent fallback from `.gitpr/conf/github.yml`.
> 3. Closing keywords: GitLab `Closes #N`, Bitbucket `close #N`, GitHub `close #N`.
> 4. Issue state normalized with `IssueInfo.is_open`.
> 5. Guard `provider_is_github` replaced with polymorphic `ScmNotSupportedError` handling.

## Proposed Changes

### Domain Contracts
#### [MODIFY] `src/infrastructure/scm/base.py`
- Add `is_open: bool = True` to `IssueInfo`.

### SCM Providers
#### [MODIFY] `src/infrastructure/scm/gitlab_provider.py`
- Implement `get_issue(repo, number, timeout)`: `GET /projects/:id/issues/:issue_iid`.
  - Normalizes `state == "opened"` to `is_open = True, state = "open"`.
- Implement `get_default_branch(repo, timeout)`: `GET /projects/:id` -> `default_branch`.
- Implement `closing_line(number)`: returns `f"Closes #{number}"`.

#### [MODIFY] `src/infrastructure/scm/bitbucket_provider.py`
- Implement `get_issue(repo, number, timeout)`: `GET /2.0/repositories/{workspace}/{repo_slug}/issues/{number}`.
  - Normalizes `state in {"new", "open", "on hold"}` to `is_open = True, state = "open"`.
- Implement `get_default_branch(repo, timeout)`: `GET /2.0/repositories/{workspace}/{repo_slug}` -> `mainbranch.name`.
- Implement `closing_line(number)`: returns `f"close #{number}"`.

#### [MODIFY] `src/infrastructure/scm/azure_devops_provider.py`
- Implement `get_default_branch(repo, timeout)`: `GET _repo_url(repo)?api-version=7.1` -> `defaultBranch`.
- Retain `ScmNotSupportedError` on `get_issue` and `closing_line`.

### Issue Autoclose Package
#### [MODIFY] `src/issue_autoclose/issue_registry.py`
- Canonical path changed to `.gitpr/conf/issue.yml`.
- Legacy fallback to `.gitpr/conf/github.yml`.
- Add `provider: str = "github"` to `RegisteredIssue`.
- `record()` writes `issue.yml` and removes legacy `github.yml`.
- `clear()` deletes both if present.

#### [MODIFY] `src/issue_autoclose/register_created_issue.py`
- Remove hardcoded `provider_is_github`.
- Populate `provider=provider.name`.

#### [MODIFY] `src/issue_autoclose/resolve_close_issue.py`
- Remove hardcoded `provider_is_github`.
- Catch `ScmNotSupportedError` -> `skipped_reason="not-supported"`.
- Check `info.is_open` and `info.state == "open"`.

#### [MODIFY] `src/ui/issue_app.py`
- Enable registration on issue creation for any provider.
- Telemetry: `command=f"issue:{self.provider.name}_create"`.

### Documentation & Architecture Decision Records
#### [NEW] `docs/adr/0010-multiforge-issue-autoclose.md`
- Document multi-forge architecture, contract, and migration.

#### [MODIFY] `CONTEXT.md`
- Update "Issue registry" and "Closing line" glossary terms.

## Verification Plan

### Automated Tests
Run full test suite and targeted tests:
- `pytest tests/scm/test_gitlab_provider.py -v`
- `pytest tests/scm/test_bitbucket_provider.py -v`
- `pytest tests/scm/test_azure_devops_provider.py -v`
- `pytest tests/issue_autoclose/ -v`
- `pytest -v`
