# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: scope SCM forge and credentials per repository
```

---

## Summary

GitPR stored the SCM forge (`GITPR_SCM_PROVIDER`), the token (`GITPR_SCM_TOKEN_ENCRYPTED`) and the base URL as machine-global settings in `~/.gitpr/.env`. That made a single machine unable to serve more than one forge at a time, sent the wrong credential to the wrong host when a repository's remote changed, and silently mapped any unrecognised self-hosted host to GitHub. This change makes the forge and its credential a property of the **repository** (ADR-016): each repository resolves its own forge from the project override, then from the `origin` remote, then falls back to GitHub — and each forge has its own credential and base-URL slot.

## ️Technical Changes

- New `src/scm_settings.py` is the single resolver for "which forge, which token, which base URL does this repository use?"; `get_scm_token` / `get_scm_settings` / `get_scm_provider` are removed from `src/config.py`, which stays a machine-wide dotenv layer with no repository dependency.
- Per-forge credential slots in `~/.gitpr/.env`: `GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED`, each with a matching `*_BASE_URL`. A token never answers on behalf of another forge; the raw `GITPR_SCM_TOKEN` stays the single CI/CD override, tried first for every forge.
- Resolution order: project override → `origin` remote detection → `github`. An unknown forge key in the project file is ignored with a warning instead of aborting the command.
- `src/project_config.py` gains an `scm.provider` section (read/write), reads both sections independently, and refuses to overwrite a non-mapping `scm` block.
- `detect_provider_from_remote` accepts `default=None`, so the wizard can distinguish "recognised as GitHub" from "not recognised" and ask instead of silently configuring the wrong host.
- One-shot, idempotent migration of the legacy `GITPR_SCM_PROVIDER` / `GITPR_SCM_TOKEN_ENCRYPTED` / `GITPR_SCM_BASE_URL` keys into their per-forge slot: it never overwrites an existing value, keeps working when `~/.gitpr/.env` is read-only, and reports unmatched cases (token without a provider, unknown provider) with an actionable warning.
- `gitpr --init` now writes the token into its own forge slot and records a project override only when the chosen forge is not the one the remote implies; the stored `*_BASE_URL` is offered as the prompt default and clearing it back to the cloud value removes the override.
- Configuration screen: editable `PROJECT_SCM_PROVIDER` row plus a read-only `PROJECT_EFFECTIVE_PROVIDER` row that shows the forge in use and its source; every forge token and base-URL row is always listed; token probing validates against the host the slot belongs to; a new `gitlab` group is introduced.
- `src/tui_issue.py` gained `allow_prompt=False` for hooks, MCP and CI: a missing or rejected token returns a clean "run `gitpr --init`" message, prompts nothing and never deletes the stored credential; a token that is validated but cannot be persisted still works for the current run.
- `src/main.py`, `src/metrics.py`, `src/release_engine.py` and `src/mcp_server.py` now resolve through `src.scm_settings` and surface the resolver warnings; the MCP path answers an unauthenticated forge with the command that fixes it, since a tool call cannot stop and ask.
- Test infrastructure: root-level autouse fixtures `english_interface` and `no_hook_script_sync` stop the developer's own profile (language, linter flags, hook auto-sync) from leaking between CLI tests; new `tests/scm/test_scm_settings.py` and `tests/test_tui_issue_token.py`, plus expanded coverage of the wizard, project config and config schema.
- i18n entries added for `es`, `es_es`, `fr`, `fr_fr`, `pt_br` and `pt_pt`.

##  Impact/Warnings

- **Environment variables:** new keys `GITHUB_TOKEN_ENCRYPTED`, `GITLAB_TOKEN_ENCRYPTED`, `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED` and their `*_BASE_URL` counterparts. `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` and `GITPR_SCM_BASE_URL` are deprecated and removed from `~/.gitpr/.env` by the migration.
- **Project configuration format:** `.gitpr/conf/gitpr.config.yml` may now contain an `scm.provider` section. Repositories whose `origin` remote does not name the forge (custom domains) must run `gitpr --init` once to record the override.
- **Behavioural change:** an unrecognised `origin` remote asks the user in the wizard instead of silently becoming GitHub; non-interactive callers get a message pointing at `gitpr --init` rather than an interactive prompt.
- **Precedence change:** the `origin` remote now decides the default forge. A self-hosted GitLab/GitHub on a domain that does not contain "gitlab"/"github" falls back to GitHub unless an override is recorded.
- **Migration is automatic and best-effort:** a legacy token without a recorded provider is deliberately left in place rather than guessed, and a write failure is reported without breaking the command.
- **No database change and no new dependency.**

close #288

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_6_warnings-yellow)](https://gitpr.natanfiuza.dev.br/)