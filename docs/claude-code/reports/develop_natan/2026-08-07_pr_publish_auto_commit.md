## Completion Report — PR Publication Interface Update + Auto-Commit

### What was done

Implemented the development plan `docs/plans/20260807_altera_interface_pullrequest_auto.md` which redefines the PR publication UX: publishing via TUI is now the default behavior, `--no-publish` skips the TUI, and `--no-edit` provides a fully automated flow with auto-commit (lint + AI commit message) and direct GitHub publication.

1. **Inverted the publication flag semantics**: removed `--publish` references; TUI opens by default when running `gitpr`. Added `--no-publish` (save locally, skip TUI) and `--no-edit` (auto-commit + direct publish) flags.
2. **Implemented auto-commit flow** for both CLI (`--no-edit` mode) and TUI (F3 key). The flow checks for uncommitted changes, runs the static linter, generates an AI commit message, confirms with the user, and executes `git commit` before publishing.
3. **Added two new environment variables**: `GITPR_AUTO_COMMIT` (skip commit confirmation) and `GITPR_SKIP_LINT` (skip lint validation).
4. **Updated all documentation and i18n**: 5 doc files rewritten, 4 i18n files updated with 30+ new keys each, 5 README files updated.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat | Added `has_uncommitted_changes()` and `execute_git_commit()` helpers |
| `src/config.py` | feat | Added `GITPR_AUTO_COMMIT` and `GITPR_SKIP_LINT` to `DEFAULT_CONFIG` |
| `src/main.py` | feat | Added `--no-publish` and `--no-edit` Click flags; implemented `_run_auto_commit_cli()` and `_publish_pr_directly()` functions; restructured PR publisher dispatch logic; updated banner and HELP_MAP |
| `src/ui/pr_publish_app.py` | feat | Added `CommitConfirmScreen`, `CommitMessageScreen`, `LinterErrorScreen` modal dialogs; refactored `action_publish_pr` with auto-commit chain (`_start_auto_commit_flow` → `_run_linter_and_commit` → `_generate_commit_and_show` → `_do_publish_pr`) |
| `src/ui/pr_publish_help.py` | update | Updated F3 description to mention auto-commit |
| `langs/pt_br.json` | feat | Added 30+ new i18n keys for auto-commit flow, flag help text, and TUI dialogs; updated banner and F3 help text |
| `langs/pt_pt.json` | feat | Same — European Portuguese translations |
| `langs/es_es.json` | feat | Same — Spanish translations |
| `langs/fr_fr.json` | feat | Same — French translations |
| `docs/pull-request-publication.md` | rewrite | Complete rewrite: inverted flag semantics, auto-commit section, linter flowchart, new env vars, updated examples |
| `docs/pull-request-publication.pt_br.md` | rewrite | Same — Brazilian Portuguese |
| `docs/pull-request-publication.pt_pt.md` | rewrite | Same — European Portuguese |
| `docs/pull-request-publication.es_es.md` | rewrite | Same — Spanish |
| `docs/pull-request-publication.fr_fr.md` | rewrite | Same — French |
| `README.md` | update | Replaced `--publish` bullet with new default-publisher description |
| `README.pt_br.md` | update | Same |
| `README.pt_pt.md` | update | Same |
| `README.es_es.md` | update | Same |
| `README.fr_fr.md` | update | Same |

### Impact

- **Functionality:**
  - `gitpr` (default): unchanged — generates PR + opens TUI
  - `gitpr --no-publish`: NEW — generates PR + saves .md + exits (no TUI)
  - `gitpr --no-edit`: NEW — generates PR + auto-commits pending changes (lint → AI commit msg → confirmation → git commit) + publishes directly to GitHub
  - TUI F3: ENHANCED — now triggers auto-commit flow before PR publication if uncommitted changes exist
- **Performance:** AI call added for commit message generation in auto-commit flow (~1-3s depending on provider). Linter runs locally (~instant).
- **Compatibility:** Backward-compatible. Default `gitpr` behavior unchanged. The `--publish` flag (which was already removed from the working tree Click decorator) is fully replaced by `--no-publish`. Existing `PR_DEFAULT_BASE` and `GITHUB_TOKEN_ENCRYPTED` env vars unchanged.

### Verification

- 130/131 tests pass (1 pre-existing failure unrelated to changes — PT-BR locale mismatch in `test_api_exception`)
- `main.py` and `pr_publish_app.py` import cleanly
- GitPR linter passes with no violations
- Banner displays new flags: `--no-publish | --no-edit`
- README references updated; zero `--publish` references remain in README files

### Post-implementation fixes

- **Round 1 — `OSError: [Errno 9] Bad file descriptor`**: `get_git_diff()` was called without `quiet=True` inside the Textual TUI, causing `click.secho()` to fail because Textual replaces `sys.stdout` with a `_PrintCapture` object without a valid Windows file descriptor.
- **Round 2 — Deeper `click` calls**: `generate_pr_content()` → `get_skill_context()` also calls `click.secho()`. Added `_with_real_stdout()` wrapper that temporarily restores `sys.stdout` during backend calls. All `core.py` calls inside `pr_publish_app.py` now use this wrapper.
- **Round 3 — UI improvements** (plan `20260807_apromaramento_interface_commit-prdesc.md`):
  - `CommitConfirmScreen`: CSS updated to 70% height with centered layout
  - New `FileStageScreen`: modal with toggleable file list for selective `git add` before commit
  - New `CommitProgressScreen`: terminal-like `RichLog` modal isolating commit logs from the main TUI
  - `CommitMessageScreen`: replaced `Static` with `Input` for editable messages; added "Regenerate" button
  - New env vars: `GITPR_AUTO_STAGE` (skip file selection), `GITPR_SHOW_LOGS` (control log display)
  - New flow: confirm → file stage (if unstaged) → progress/log modal → editable message → commit → publish
  - `_get_unstaged_files()` helper parses `git status --porcelain` for `??` and ` M` files

### Changed files (cumulative)

| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat | `has_uncommitted_changes()`, `execute_git_commit()` helpers |
| `src/config.py` | feat | Added `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS` |
| `src/main.py` | feat | `--no-publish`/`--no-edit` flags, `_run_auto_commit_cli()`, `_publish_pr_directly()` |
| `src/ui/pr_publish_app.py` | feat+refactor | `_with_real_stdout()`, `FileStageScreen`, `CommitProgressScreen`, updated `CommitConfirmScreen`/`CommitMessageScreen`, `LinterErrorScreen`; `_get_unstaged_files()`; restructured F3 flow |
| `src/ui/pr_publish_help.py` | update | F3 description updated |
| `langs/pt_br.json` | feat | 40+ new i18n keys |
| `langs/pt_pt.json` | feat | Same — PT-PT |
| `langs/es_es.json` | feat | Same — ES |
| `langs/fr_fr.json` | feat | Same — FR |
| `docs/pull-request-publication*.md` (5) | rewrite | Complete doc refresh |
| `README*.md` (5) | update | Replaced `--publish` references |

### Next steps

- Test end-to-end with real GitHub API: `gitpr --no-edit` against a test repository
- Consider adding `git push` step after auto-commit (currently commits locally only)
- Add unit tests for `has_uncommitted_changes()`, `execute_git_commit()`, and `_get_unstaged_files()`
