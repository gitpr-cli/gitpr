# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive commit TUI for gitpr commit
```

---

## 🎯 Summary

The `gitpr commit` command previously ran as a silent, fire-and-forget pipeline: it validated the working tree, generated a message with the AI provider, and committed immediately — giving the user no opportunity to review, edit, or control which files were included. This was error-prone (accidental commits of unrelated files, no way to reject a poor AI suggestion) and inconsistent with the project's direction of rich terminal UX.

This change replaces that silent flow with a full interactive TUI, so developers stay in control of every step: file staging, message review/editing, and commit execution — all without leaving the terminal.

## 🛠️ Technical Changes

- Add `get_git_staged_diff()` in `src/core.py` — runs `git diff --cached` with the same robustness guards (`-U1 -w -M -B`, `SMART_EXCLUDES`, encoding fallback, quiet-mode error handling) as `get_git_diff()`.
- Add `CommitApp` (`src/ui/commit_app.py`), a Textual application orchestrating the commit flow:
  - Prompts `StageFilesScreen` when unstaged files exist (skippable via flag or env var), with `GITPR_AUTO_STAGE` for non-interactive staging.
  - Prefers the staged diff, falling back to the working-tree diff when nothing is staged.
  - Generates the commit message in a background thread via `generate_pr_content("commit", ...)` while a `CommitProgressScreen` animates.
  - Presents `CommitMessageScreen` for review/editing before committing, then executes `execute_git_commit()` with the co-author trailer appended.
- Rework `src/main.py` commit branch: when invoked from a hook, behavior is unchanged (silent, merge-aware, AI-generated message); otherwise the new `CommitApp` is launched and its terminal state (`no_changes`, `cancelled`, `committed`, `failed`) is surfaced to the user.
- Add `tests/test_commit_app.py` — unit tests for every state transition/callback plus a headless end-to-end flow using Textual's `run_test()` pilot.

## ⚠️ Impact/Warnings

- **Behavior change:** `gitpr commit` without `--hook` is now interactive. Any script or CI job relying on the previous non-interactive commit must pass the skip flag or set `GITPR_SKIP_UNSTAGED_CHECK`.
- **Environment variables introduced:** `GITPR_SKIP_UNSTAGED_CHECK` (bypass the staging prompt) and `GITPR_AUTO_STAGE` (auto-stage all unstaged files). Document these in the user-facing docs.
- **Dependency:** relies on `textual` widgets and screens already present in `src/ui/pr_publish_app.py`; no new third-party packages added.
- **Global state:** `_generate_commit_msg` temporarily reassigns `sys.stdout` during the AI call to suppress provider output — monitor for edge cases with concurrent logging or daemon-thread teardown.
- No database, schema, or network API changes.

close #227

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)