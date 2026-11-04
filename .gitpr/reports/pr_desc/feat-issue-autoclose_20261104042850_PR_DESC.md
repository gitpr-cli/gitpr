# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add automatic issue closure to pull request flow
```

---

## 🎯 Summary

Issues created with `gitpr -is` were orphaned: the number existed only inside the issue TUI and was lost as soon as it closed, so every PR had to be linked to its issue by hand. This change records the created issue locally, verifies it is still open on the forge, and offers — or, with `--close-issue`, silently applies — the closing line (`close #N`) in the generated PR description. The goal is that a merge actually closes the tracked issue without the user retyping anything.

## 🛠️ Technical Changes

- New `src/issue_autoclose/` package split by responsibility: `register_created_issue.py` (writes the record after `gitpr -is`), `resolve_close_issue.py` (decides whether the next PR closes it), `insert_close_line.py` (appends the line at the single body assembly point) and `issue_registry.py` (local record at `.gitpr/conf/github.yml`).
- `register_created_issue` only records on GitHub and swallows bookkeeping failures, so a local write problem never turns a successful creation into an error; the first write also adds the record to `.gitignore`.
- `resolve_close_issue` gates cheaply before any disk/network access (flags, config, non-GitHub forge), checks the issue is still open and not a pull request, clears dead records (404, closed, PR number) and asks the user once, warning when the PR targets a branch other than the default one.
- `insert_close_line` is idempotent: it detects any existing closing keyword (`close/closes/closed`, `fix/fixes/fixed`, `resolve/resolves/resolved`, optional `owner/repo#N` prefix, case-insensitive) and never duplicates the line.
- New CLI flags `--close-issue` and `--no-close-issue` (mutually exclusive, rejected before any prompt or file write; `-h` wins over the conflict). Contextual help entries added to `HELP_MAP`.
- PR flow wiring in `src/main.py`: `_prepare_close_issue` runs before the stage TUI and reuses the resolved SCM context; `_publish_pr_directly` now returns whether the forge actually created the PR, so the record is cleared only after a real publication (ADR-007).
- `PrPublishApp.body_published` distinguishes a real create/update from merely opening an existing PR, which also reports `created`.
- New settings `GITPR_ISSUE_AUTOCLOSE` (default `true`, opt-out) and `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` (default `5`, positive int) exposed in the `issue` category of the config TUI.
- One `issue_autoclose` ledger row per decision (`asked`, `accepted`, `skipped_reason`) for telemetry.
- Translations for es/es_es/fr/fr_fr/pt_br/pt_pt, docs and plan/report files, plus version bump to `1.5.0` and language dictionary to `v0.0.38`.
- Test coverage for the wiring, line insertion, registration, decision tree, config getters/schema and `body_published` semantics.

## ⚠️ Impact/Warnings

- **Version bump:** package version goes from `1.4.4` to `1.5.0` (minor feature) and `__lang_version__` to `v0.0.38`; users will be prompted to update language assets.
- **New environment variables:** `GITPR_ISSUE_AUTOCLOSE` and `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`. They are read-only defaults and are deliberately **not** seeded into `~/.gitpr/.env`, so no user file is rewritten.
- **New local state file:** `.gitpr/conf/github.yml` is created on the first `gitpr -is` run and auto-added to `.gitignore`; it never leaves the machine.
- **Extra forge traffic:** at most one `get_issue` call and, only when the user is asked, one default-branch lookup, both bounded by the configurable timeout. Runs without a record keep the previous flow byte-for-byte.
- **Behaviour change:** `_publish_pr_directly` now returns a boolean instead of `None`; any external caller relying on its return value must be aware.
- **Conflict guard:** passing `--close-issue` and `--no-close-issue` together exits with code 1 before any side effect.

close #259

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_1_warning-yellow)](https://gitpr.natanfiuza.dev.br/)