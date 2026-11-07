# Walkthrough — Multi-Forge Issue Autoclose

## Overview
This walkthrough demonstrates the multi-forge extension of automatic issue closing in GitPR across GitHub, GitLab, Bitbucket Cloud, and Azure DevOps.

## Architecture

```
                    ┌─────────────────────────┐
                    │      Issue Creation     │
                    │      (gitpr -is TUI)    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   RegisterCreatedIssue  │
                    │   (.gitpr/conf/issue.yml)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    PR Preparation Flow  │
                    │    (gitpr default flow) │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   [GitLabProvider]      [BitbucketProvider]    [AzureDevOpsProvider]
   get_issue() -> open   get_issue() -> open    get_issue() -> raises
   closing_line():       closing_line():        ScmNotSupportedError
   "Closes #<iid>"       "close #<id>"          (skipped_reason="not-supported")
```

## Changes Implemented

### 1. Unified SCM Provider Contract
In [`src/infrastructure/scm/base.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/base.py), `IssueInfo` gained `is_open: bool = True`:
```python
@dataclass(frozen=True)
class IssueInfo:
    number: int
    title: str
    state: str
    is_pull_request: bool = False
    is_open: bool = True
```

### 2. GitLab Provider Support
In [`src/infrastructure/scm/gitlab_provider.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/gitlab_provider.py):
- `get_issue(repo, number)`: Normalizes GitLab state `"opened"` to `is_open=True, state="open"`.
- `get_default_branch(repo)`: Queries project info from GitLab REST API v4 `/projects/:id`.
- `closing_line(number)`: Generates `"Closes #{number}"`.

### 3. Bitbucket Cloud Provider Support
In [`src/infrastructure/scm/bitbucket_provider.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/bitbucket_provider.py):
- `get_issue(repo, number)`: Normalizes Bitbucket states (`"new"`, `"open"`, `"on hold"`) to `is_open=True, state="open"`. If the Issue Tracker feature is disabled (returns 404), raises `ScmProviderError(http_status=404)`.
- `get_default_branch(repo)`: Queries repository details from Bitbucket REST API 2.0 `/repositories/{workspace}/{repo_slug}` (`mainbranch.name`).
- `closing_line(number)`: Generates `"close #{number}"`.

### 4. Azure DevOps Handling
In [`src/infrastructure/scm/azure_devops_provider.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/azure_devops_provider.py):
- `get_default_branch(repo)`: Queries repository details from Azure DevOps REST API 7.1 (`defaultBranch`).
- `get_issue` and `closing_line` explicitly raise `ScmNotSupportedError` as Azure DevOps Git repositories do not host native issues (work items live in Azure Boards).

### 5. Registry Migration
In [`src/issue_autoclose/issue_registry.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/issue_autoclose/issue_registry.py):
- The canonical path is `.gitpr/conf/issue.yml`.
- Existing `.gitpr/conf/github.yml` files are automatically read as fallback and purged upon next write or clear.
- `RegisteredIssue` stores the `provider` name (`"github"`, `"gitlab"`, `"bitbucket"`, etc.).

## Verification Results

Full test suite execution:
```
============================== test session starts ==============================
collected 461 items

tests/issue_autoclose/... PASSED
tests/scm/... PASSED

====== 459 passed, 2 skipped, 12 warnings, 74 subtests passed in 11.37s =======
```
All unit test suites run cleanly with zero failures and zero regressions.
