# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add local issue registry and SCM issue read-back
```

---

## 🎯 Summary

`gitpr -is` creates an issue, but its number is lost the moment the command ends — and the next pull request is the first place that could close it. This change introduces the persistence and provider groundwork for the automatic issue closure (ADR-001/ADR-003): a small local record of the issue that is still a closure candidate, plus the read-back operations the PR flow needs to decide whether offering to close it even makes sense.

Nothing user-facing changes yet. This is the storage and SCM contract layer that the PR flow will consume next.

## 🛠️ Technical Changes

- **New `IssueRegistry` (`src/issue_autoclose/issue_registry.py`)**: reads and writes `.gitpr/conf/github.yml` with `schema_version: 1` and a single `last_issue` entry (last write wins, matching a single-PR workflow).
- **Atomic writes**: the record is dumped to a sibling temp file and moved into place with `os.replace`, so an interrupted run can never leave a truncated file; a failed replace keeps the previous record intact and cleans up the temp file.
- **Self-ignoring state**: `record()` runs `git check-ignore` before the first write and appends exactly one `.gitpr/conf/github.yml` line to `.gitignore` when the file is not already covered (`.gitpr/conf/` is not ignored wholesale, since `gitpr.config.yml` is versioned on purpose — ADR-015).
- **Corruption is recoverable, not fatal**: `load()` returns a `RegistryLoad` with `error` instead of raising; a missing file simply means "no issue recorded", and the next `record()` overwrites a corrupt file.
- **`matches_repo()`** compares owner/repo case-insensitively, so a record from another repository never drives a wrong closure.
- **New `IssueInfo` dataclass in `ScmProvider`** carrying `state` in the forge's own vocabulary and an `is_pull_request` flag — GitHub's issue endpoint answers PR numbers too, and a caller must not offer to close a pull request as if it were an issue.
- **Three non-abstract defaults on `ScmProvider`** — `get_issue()`, `get_default_branch()` and `closing_line()` — all raising `ScmNotSupportedError`, so the other three forges degrade to "feature inactive" instead of crashing.
- **GitHub implementations**: `GET /repos/{o}/{r}/issues/{n}` (flagging `pull_request` payloads, falling back to the requested number when absent), `GET /repos/{o}/{r}` for `default_branch` (empty string when absent), and the forge-specific `close #N` keyword.
- **Tests**: 263 lines covering round-trip, schema shape, corrupt-file variants, atomic-write failure, `.gitignore` edge cases (missing file, missing final newline, already-ignored by a broader rule, outside a repository) and repository-root anchoring; plus provider contract tests for the not-supported defaults and HTTP 200/401/403/404/500/timeout paths for the new GitHub calls.

## ⚠️ Impact/Warnings

- **Local filesystem**: the first successful `record()` may modify the user's `.gitignore` (one appended line) and creates `.gitpr/conf/github.yml`. Both are local state, never committed.
- **No database, environment variable or dependency changes**: `PyYAML` and `requests` are already in use.
- **Network**: `get_issue()` and `get_default_branch()` default to a deliberately short 5 s timeout so a slow forge cannot delay the PR flow, which only needs one yes/no.
- **Feature scope**: the closure remains GitHub-only by design; other forges inherit the raising defaults and must treat `ScmNotSupportedError` as "feature inactive".
- **Not wired yet**: no command calls the registry or the new provider methods in this change — the integration into the PR flow lands separately.

close #257

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)