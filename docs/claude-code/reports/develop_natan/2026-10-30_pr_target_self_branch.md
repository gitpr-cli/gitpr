## Completion Report — PR target branch picker and self-target validator

### What was done

- The **PR Target Base Branch** row of `gitpr config` → Project is now a
  picker over the branches git knows (`KIND_BRANCH`), not a free-text field.
  The options come from `project_config.list_branches()` — local branches plus
  the ones that exist on `origin`, which is where `verify_remote_base()` looks
  — and `origin/HEAD` is dropped because it names a default, not a branch. A
  value the checkout does not have yet stays on screen as an option instead of
  being silently dropped by the widget, and the explicit *(automatic)* entry
  keeps meaning "fall through the precedence chain".
- New validator: **a pull request cannot target the branch it is opened from.**
  `verify_remote_base()` now refuses a target equal to the checked-out branch
  with `CurrentBranchError` (a narrower `BaseBranchError`, so every existing
  `except BaseBranchError` keeps working), before the remote-ref check. New
  `current_branch()` reads `git rev-parse --abbrev-ref HEAD` and returns `""`
  on a detached HEAD.
- **Running:** an interactive publish whose resolved target is the current
  branch opens `BaseBranchPromptApp` — a small screen with only the Project
  branch picker, current branch excluded — before anything is published. The
  choice is written to `.gitpr/conf/gitpr.config.yml` and the target is
  resolved again. The picker is skipped, and the error stands, for `--quiet`,
  a non-interactive stdin (hooks, CI, editors) and an explicit `--base`
  pointing at the current branch: `--base` is a choice for that run, and
  rewriting the project file to satisfy it would leave the repository wrong for
  every later run. A failure to write the file also keeps the original refusal.
- **Configuring:** `gitpr config` never offers the current branch. A file that
  already names it is not an error while only other fields are edited — being
  on the target branch is a normal state of a checkout — but the value is
  labelled **{branch} (current branch)** and an edit that would write it is
  refused at save time. Saving a branch that is no longer valid still warns
  without blocking (unchanged rule).
- Documentation: `docs/config-tui.md` and `docs/pull-request-publication.md`,
  each with the four translations; ADR-015 gained decision 10 (the self-target
  rule, the picker filter and the `--base` exception) and one rejected
  alternative (silent fallback to `origin/HEAD`); `CLAUDE.md` names the check
  and the new screen. Nine new i18n keys, translated in all six `langs/*.json`.
- Technical documentation: `docs/ARCHITECTURE.md` gained section 20
  (*Project-Local PR Target*), the new modules in the project tree and the
  `config-tui.md` entry in the docs index; `CONTEXT.md` gained the domain terms
  **PR target base**, **Diff base**, **Project configuration file** and
  **Self-target**; the config glossary gained **Self-target** and now states
  that the target must differ from the checked-out branch; the validation table
  of `docs/config-tui.md` (+4) lists the refusal as a save rule.
- No commit was made (`CLAUDE.md` rule).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/project_config.py` | feat | `list_branches()`, `current_branch()`, `CurrentBranchError`, self-target check in `verify_remote_base()` |
| `src/config_schema.py` | feat | `KIND_BRANCH`; `PROJECT_BASE_BRANCH` uses it |
| `src/ui/config_app.py` | feat | `current_branch` state, current branch filtered out of the picker, `(current branch)` label for a stored value, save-time refusal of a self-target edit |
| `src/ui/pr_base_app.py` | feat | New `BaseBranchPromptApp` + `prompt_for_base_branch()`: the publish-time modal |
| `src/main.py` | feat | `_resolve_pr_target()` owns the resolution, the modal and the project-file write; the publish path calls it |
| `tests/test_project_config.py` | test | `init_repo` pins the checked-out branch; tests for `current_branch`, the self-target refusal and `CurrentBranchError` as a `BaseBranchError` |
| `tests/test_config_app.py` | test | `current_branch` pinned in `setUp`; current branch absent from the picker; stored current value labelled and replaceable; save-time refusal |
| `tests/test_pr_base_app.py` | test | New suite: the modal headless (options, label, confirm, cancel, no-alternative) and `_resolve_pr_target` (repair, cancel, `--base`, `--quiet`, non-tty, unwritable file) |
| `langs/*.json` (6) | docs | Nine new keys, translated |
| `docs/config-tui.md` +4 | docs | Picker excludes the current branch; stored current value; save-time refusal |
| `docs/pull-request-publication.md` +4 | docs | §9.3: the self-target rule, the modal and when it is skipped |
| `docs/plans/ADR-015-project-local-pr-base.md` | docs | Decision 10 and one rejected alternative |
| `docs/ARCHITECTURE.md` | docs | Section 20 (module, resolver, seeding, verification, modal, stores), project tree and docs index |
| `CONTEXT.md` | docs | Domain terms: PR target base, Diff base, Project configuration file, Self-target |
| `docs/plans/glossary-config-tui.md` | docs | New term **Self-target**; the PR target base now states the checkout rule |
| `CLAUDE.md` | docs | The target must differ from the checked-out branch; the modal lives in `src/ui/pr_base_app.py` |

### Verification

- `tests/test_config_app.py` + `tests/test_project_config.py` +
  `tests/test_project_config_cli.py` + `tests/test_config_schema.py` +
  `tests/test_pr_base_app.py` + `tests/test_mcp_server.py`: **311 passed**
  (176 s).
- `tests/test_config_cli.py` + `tests/test_install_wizard.py` +
  `tests/test_pr_base_app.py`: **24 passed**.
- `tests/test_i18n.py`: **3 failed**, the same three known failures
  (missing keys and orphans reported by that suite before this change) — the
  new keys are present and translated in all six files.
- Full suite: see the run recorded below.

### Impact

- **Functionality:** a project whose base branch is the branch being published
  no longer fails blind — an interactive run offers the fix and records it.
  Non-interactive runs keep a clear error instead of hanging or publishing a
  self-targeted request. The configuration screen cannot produce the invalid
  value.
- **Performance:** `gitpr config` runs one extra `git rev-parse
  --abbrev-ref HEAD` when it opens; the publish path runs the same command as
  part of the existing verification, and only reaches the modal when the target
  is the current branch.
- **Compatibility:** the new exception is a `BaseBranchError` subclass, so the
  MCP server (which maps `BaseBranchError` to a JSON error) and the CLI needed
  no change beyond the modal. A branch name is still accepted from a hand-edited
  file; only the write path refuses the current branch.

### Next steps

- Review the working-tree diff and commit with:
  `feat: validate the PR target against the checked-out branch`
