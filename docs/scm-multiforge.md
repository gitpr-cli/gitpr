# Technical Documentation: Multi-Forge SCM (ScmProvider)

GitPR publishes Pull Requests and issues through a single abstraction, the `ScmProvider`, which supports four Git hosting forges: GitHub, GitLab, Bitbucket Cloud and Azure DevOps. Every publication flow — the interactive PR publisher (default mode), the direct publish (`--no-edit`) and the issues TUI (`-is`) — resolves the provider **of the repository it runs in** and calls the forge API through it.

The forge belongs to the repository, not to the machine: GitPR detects it from the `origin` remote (or reads an explicit override committed with the project), and keeps **one encrypted token per forge** in `~/.gitpr/.env`. One machine can therefore work with a GitLab repository and a GitHub repository at the same time, each with its own credential.

Without SCM configuration, GitPR keeps the legacy GitHub-only behavior — zero migration and byte-identical output.

---

## 1. Supported Forges

| Forge | Provider key | Default API base | Authentication |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Username + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Which Forge a Repository Uses

The forge is resolved per repository, in this order:

1. **Project override** — `scm.provider` in `.gitpr/conf/gitpr.config.yml`, versioned with the repository. It always wins, which is how you correct a self-managed host whose domain does not name its forge.
2. **Origin remote detection** — a case-insensitive substring match on the `origin` URL.
3. **`github`** — the historical default.

| Remote URL contains | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` or `visualstudio.com` | `azure_devops` |
| anything else (default) | `github` |

```yaml
# .gitpr/conf/gitpr.config.yml — commit it to share the forge with the team
scm:
  provider: gitlab
```

An unknown value in the project file is ignored with a warning (a malformed file must never stop every command), and the detection decides instead.

```bash
git remote get-url origin
# git@github.com:gitpr-cli/gitpr.git               -> github (default)
# https://gitlab.com/acme/platform/web-app.git     -> gitlab
# https://bitbucket.org/acme/web-app               -> bitbucket
# https://dev.azure.com/acme/project/_git/web-app  -> azure_devops
```

The repository is addressed through `RepoRef`, parsed from the remote URL. The **workspace** is the GitHub owner, the GitLab namespace (subgroups included), the Bitbucket workspace, or — on Azure DevOps — a display-only `{org}/{project}` label, because API calls use the `organization` and `project` from the configuration instead.

---

## 2. First-Time Setup — `gitpr --init`

The interactive wizard detects the forge, validates the access token and persists the configuration:

```bash
gitpr --init
```

| Step | What happens |
| --- | --- |
| 1. Forge detection | Detects the forge from the `origin` remote and asks for confirmation (you can choose another forge; a host that names no forge is asked, never assumed) |
| 2. Provider extras | Azure DevOps asks for `organization` and `project`; Bitbucket asks for the `username`, which is part of the credential |
| 3. API base URL | Custom base URL for every forge except GitHub; the value already stored for that forge is offered as the default |
| 4. Token | Asks for the PAT — or the App Password on Bitbucket |
| 5. Validation | `test_connection()` — up to 3 attempts; HTTP 401 (expired token) re-prompts in yellow, other failures abort in red |
| 6. Persistence | Only on success: writes the Fernet-encrypted token into its forge's slot (`GITLAB_TOKEN_ENCRYPTED`, …) plus the base URL and extras, and records `scm.provider` in the project file **only when the chosen forge differs from the detected one** |

Nothing is written when validation fails. Re-run `gitpr --init` in each repository to switch forges or renew an expired token; the tokens of the other forges are left untouched. Values from older versions (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) are migrated automatically on the first command after upgrading.

---

## 3. Manual Configuration (.env)

Alternative to the wizard: edit `~/.gitpr/.env` directly. See the [GitHub PAT integration guide](github-pat-integration.md) for how GitPR protects tokens at rest.

| Variable | Forge | Description |
| --- | --- | --- |
| `GITPR_SCM_TOKEN` | all | Raw token, for CI/CD environments only — single and global, tried before any stored token |
| `GITHUB_TOKEN_ENCRYPTED` | `github` | Fernet-encrypted token of the GitHub forge |
| `GITLAB_TOKEN_ENCRYPTED` | `gitlab` | Fernet-encrypted token of the GitLab forge |
| `BITBUCKET_TOKEN_ENCRYPTED` | `bitbucket` | Fernet-encrypted token of the Bitbucket forge |
| `AZURE_DEVOPS_TOKEN_ENCRYPTED` | `azure_devops` | Fernet-encrypted token of the Azure DevOps forge |
| `GITHUB_BASE_URL` / `GITLAB_BASE_URL` / `BITBUCKET_BASE_URL` / `AZURE_DEVOPS_BASE_URL` | own forge | Custom API base URL (self-managed/enterprise); empty = public SaaS |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Organization name — mandatory (fail-fast error names the missing variable) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Project name — mandatory |
| `GITPR_SCM_USERNAME` | `bitbucket` | Bitbucket username — mandatory (App Password uses HTTP Basic) |

Each forge reads only its own slot: a GitLab token never answers for a GitHub repository. GitHub without SCM configuration keeps using `GITHUB_TOKEN_ENCRYPTED` — zero migration.

### 3.1 Migration Note: Automated Provisioning & Per-Forge Slots

> [!WARNING]
> **Migration Note for Infrastructure & Provisioning Scripts:**  
> The legacy machine-wide configuration keys `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, and `GITPR_SCM_BASE_URL` have been permanently retired. The automatic runtime migration removes these lines from `~/.gitpr/.env` on the first execution.  
> 
> Automated machine provisioning scripts (Ansible, Docker, devcontainers, dotfiles, or VM bootstrapping) must now populate the dedicated per-forge slots directly:
> - GitHub: `GITHUB_TOKEN_ENCRYPTED` (and optionally `GITHUB_BASE_URL`)
> - GitLab: `GITLAB_TOKEN_ENCRYPTED` (and optionally `GITLAB_BASE_URL`)
> - Bitbucket: `BITBUCKET_TOKEN_ENCRYPTED` (and `GITPR_SCM_USERNAME`)
> - Azure DevOps: `AZURE_DEVOPS_TOKEN_ENCRYPTED` (and `GITPR_SCM_ORGANIZATION` + `GITPR_SCM_PROJECT`)
> 
> For self-managed hosts with custom domains, configure the project override in `.gitpr/conf/gitpr.config.yml` (`scm.provider: <forge>`) instead of attempting to define a global provider in `.env`. Ephemeral CI environments should continue using the single unencrypted `GITPR_SCM_TOKEN`. For architectural details, see [ADR-0020](adr/0020-per-repo-scm-provisioning-migration.md) and [ADR-016](plans/ADR-016-per-provider-scm-settings.md).

---

## 4. Using GitPR with the Configured Forge

### 4.1 Pull Request Publication

```bash
gitpr                # Interactive publisher (TUI) — review and confirm the PR
gitpr --no-edit      # Publish directly, with auto-commit (skips the TUI)
gitpr --no-publish   # Generate only the PR description file (.md), no TUI
```

The publisher resolves the provider from the `origin` remote, parses the repository into a `RepoRef` and creates the pull request through `provider.create_pull_request()`. The PR number, URL and state returned by the forge are shown in the TUI and saved in the output file.

### 4.2 Issues

```bash
gitpr -is            # Issue flow: AI draft -> TUI -> F3 creates the issue on the forge
```

F3 calls `provider.create_issue()` on the configured forge. Azure DevOps has no issue API resource (Work Items depend on the project's process template), so GitPR tells you to save the draft locally with F2. Bitbucket requires the repository's **Issue Tracker** to be enabled, otherwise the API answers 404.

### 4.3 Token Expiry and Reauthentication (HTTP 401)

When the token is rejected (HTTP 401), GitPR removes the expired token from the slot of **that** forge and asks for a new one — up to 3 attempts. Prefer the interactive flows (`gitpr`, `gitpr -is`) to re-authenticate: `--no-edit` publishes directly and cannot re-prompt.

A non-interactive run (git hooks, the MCP server, CI) never asks and never deletes the stored credential: it stops with a message telling you to run `gitpr --init` in that repository.

---

## 5. Per-Forge Notes and Limitations

### 5.1 GitHub

- Existing installations keep exact behavior (byte-parity): payload, `Authorization: token` header and the legacy `GITHUB_TOKEN_ENCRYPTED` store are unchanged.
- Reviewer suggestions are native (`requested_reviewers`); disable them with `--no-suggest-reviewers`.

### 5.2 GitLab

- Merge requests: the API identifier is the MR `iid` — never the global project-scoped id.
- Drafts: GitLab has no draft flag when creating an MR, so GitPR prefixes the title with `"Draft: "`.
- Repository paths (groups and subgroups) are always URL-quoted.
- The merge strategy parameter is ignored — GitLab merges with its native merge action.

### 5.3 Bitbucket Cloud

- Credentials are HTTP Basic: username + App Password. The username is mandatory (`GITPR_SCM_USERNAME`) and is part of the credential.
- Issues require the repository's Issue Tracker to be enabled.
- Merge strategies: `merge` -> `merge_commit`, `squash` and `fast_forward`.

### 5.4 Azure DevOps

- `organization` and `project` are mandatory — the fail-fast error names the missing env vars.
- Every REST call carries `api-version=7.1`.
- Branch refs use the `refs/heads/` prefix.
- No unified PR diff over REST: `get_pull_request_diff()` returns a per-file textual summary (`path (+adds −dels)`) of the last iteration.
- Issues are not supported (`ScmNotSupportedError`) — save the draft locally with F2.
- Legacy `*.visualstudio.com` remotes are accepted by the detector.

---

## 6. For Developers and Plugins

The abstraction lives in `src/infrastructure/scm/`: the `ScmProvider` contract in `base.py`, one concrete provider per forge and the registry in `factory.py`. Internal code resolves providers only through `resolve_scm_provider()` and never imports concrete classes directly. Provider methods raise `ScmProviderError(provider, http_status, message)` — `http_status` is `0` on network failures — or `ScmNotSupportedError` when the forge has no equivalent operation. They never return the legacy `(ok, data, status)` tuples.

`src/github_api.py` is a **deprecated shim**: it still exposes the four legacy functions with their tuple returns for third-party integrations, but every call raises a `DeprecationWarning`. New code and plugins must use `resolve_scm_provider()` instead.

### 6.1 Contract for Third-Party Providers (breaking change since v1.2.0)

`ScmProvider.request_pull_request_reviewers()` used to return `None`. Since **v1.2.0** it returns `list[str]`: the logins the forge **actually attached**, read back from the response body. An empty list means "accepted but ignored" — that is how GitPR detects a reviewer the forge silently dropped.

| | Up to v1.1.x | Since v1.2.0 |
| --- | --- | --- |
| Return type | `None` | `list[str]` (attached logins) |
| `[]` | — | Request accepted, nobody attached |
| Default in the base class | `ScmNotSupportedError` | `ScmNotSupportedError` (unchanged) |

**Who is affected:** only subclasses that **override** the method. Code that merely calls it is unaffected. A subclass that does not override it keeps raising `ScmNotSupportedError`, as before.

**How to migrate:** return what the forge attached. If the forge returns no body, return the list you were asked to attach — optimistic, and it turns off the "not attached" warning for that forge.

```python
class MyForgeProvider(ScmProvider):
    def request_pull_request_reviewers(self, repo, pr_id, reviewers) -> list[str]:
        body = self._post_reviewers(repo, pr_id, reviewers)
        return [r["login"] for r in body.get("requested_reviewers", [])]
        # No body from the forge? `return list(reviewers)` instead.
```

A legacy override that still returns `None` keeps working: the caller reads it as "cannot verify" and skips the "not attached" warning. It is tolerated, not recommended. Decision record: [ADR-0009](adr/0009-reviewer-attach-returns-read-back.md).

Architecture decision record and canonical vocabulary: [ADR-001 SCM abstraction](plans/ADR-001-scm-abstraction.md) and [SCM Multi-Forge glossary](plans/glossary-scm-multiforge.md).

> **Note:** See also the [GitHub PAT integration documentation](github-pat-integration.md) for creating tokens and understanding GitPR's encryption (Fernet).
