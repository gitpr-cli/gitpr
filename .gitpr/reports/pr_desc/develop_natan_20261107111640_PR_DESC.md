# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: support multi-forge issue auto-close
```

---

## 🎯 Summary

The automatic issue-closure flow was previously locked to GitHub only, which meant `gitpr -is` and `--close-issue` silently did nothing on GitLab, Bitbucket, and Azure DevOps. This change generalizes the closure workflow across supported forges (ADR-010) by introducing a provider-agnostic issue read-back contract (`get_issue`, `get_default_branch`, `closing_line`) and removing the hardcoded GitHub gate. It also renames the local issue record to a provider-neutral path and adds a transparent migration path so existing users keep working without manual intervention.

## 🛠️ Technical Changes

- **Provider contract:** added `get_issue`, `get_default_branch`, and `closing_line` to GitLab, Bitbucket, and Azure DevOps providers. GitLab normalizes `opened` → `open` and emits `Closes #N`; Bitbucket normalizes `new`/`open`/`on hold` → `open` and emits `close #N`; Azure DevOps raises `ScmNotSupportedError` (work items are not issues).
- **Model:** extended `IssueInfo` with an explicit `is_open` flag to remove brittle string-state comparisons at the decision layer.
- **Resolution logic:** `resolve_close_issue` no longer short-circuits on non-GitHub forges; unsupported forges degrade to `skipped_reason="not-supported"` instead of being ignored, and the decision path prefers `is_open` when present.
- **Registration:** `register_created_issue` now records issues from any supported provider, persisting the `provider` name; the GitHub-only `not-github` outcome was replaced with `no-provider`.
- **Registry storage:** renamed the record from `.gitpr/conf/github.yml` to `.gitpr/conf/issue.yml`, added a `provider` field (`github` default), and introduced legacy fallback: `github.yml` is read transparently when the new file is absent and deleted on the next write/clear.
- **Robustness:** wrapped `load_dotenv`, `ledger_exists`, and `ensure_ledger` in `PermissionError`/`OSError` guards so read-only or restricted environments no longer abort the CLI.
- **UI/telemetry:** issue-creation metrics now derive `issue:<provider>_create` dynamically instead of being hardcoded to GitHub.
- **Cleanup:** removed redundant blank lines and a manual provider check in `main.py`/`issue_app.py`.
- **Tests:** added coverage for GitLab/Bitbucket/Azure DevOps read-back and closing-line behavior, registry migration (legacy read, migration on write, dual clear), and provider-agnostic registration/metrics.

## ⚠️ Impact/Warnings

- **Behavioral change:** the local issue record moved from `.gitpr/conf/github.yml` to `.gitpr/conf/issue.yml`. Existing `github.yml` files are read automatically and migrated on the next write, but users who inspect or version this file should expect the new name. `.gitignore` was updated accordingly.
- **Public API surface:** `register_created_issue` now returns `no-provider` (previously `not-github`) and records non-GitHub issues — any consumer keying off the old outcome string must be updated.
- **Forge limitations:** Azure DevOps will always report `not-supported` for issue closure (work items only); GitLab/Bitbucket issue trackers that are disabled return `ScmProviderError` (404) and are treated as skips.
- **No dependency or environment-variable changes.**
- **Error swallowing:** filesystem permission failures in `.env` loading, ledger access, and legacy cleanup are now suppressed by design; check logs if unexpected silent failures are suspected.

close #286

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)