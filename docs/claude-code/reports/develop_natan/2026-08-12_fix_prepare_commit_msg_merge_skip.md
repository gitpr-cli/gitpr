## Completion Report — Skip AI Commit Message on Merge Sources (`git pull`)

### What was done
- Fixed `prepare-commit-msg` hooks to skip AI commit-message generation for git-generated sources (`merge`, `squash`, `commit` — previously only `message` was skipped), so `git pull`/`git merge` no longer corrupt `.git/MERGE_MSG` with an AI message
- Added a belt-and-braces `.git/MERGE_HEAD` file check to all 5 language variants of the template
- Added `is_merge_in_progress()` in `src/core.py` (checks `git rev-parse -q --verify MERGE_HEAD`) as defense-in-depth against stale hooks that call the CLI during a merge
- Added a silent hook-mode guard in `src/main.py` commit flow: merge in progress → exit 0 without AI
- Bumped `__scripts_version__` to `v0.0.2` so installed hooks auto-sync on the next plain `gitpr` run
- Added `TestIsMergeInProgress` unit tests (3 cases) in `tests/test_core.py`
- Documented the new skip behavior in `docs/git-hooks-locais.md` and the 4 localized copies (pt_br, pt_pt, es_es, fr_fr)
- Metrics side unchanged: `git pull` events were already recorded via the `post-merge` hook (`hook:post-merge`)

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| scripts/prepare-commit-msg-template.sh | fix | Guard replaced by POSIX `case` skipping `message\|merge\|squash\|commit` + `.git/MERGE_HEAD` belt-and-braces check |
| scripts/prepare-commit-msg-template.pt_br.sh | fix | Same fix with localized comments |
| scripts/prepare-commit-msg-template.pt_pt.sh | fix | Same fix with localized comments |
| scripts/prepare-commit-msg-template.fr.sh | fix | Same fix with localized comments |
| scripts/prepare-commit-msg-template.es.sh | fix | Same fix with localized comments |
| src/core.py | feat | New `is_merge_in_progress()` helper (silent, worktree-safe, returns False on git failure) |
| src/main.py | fix | Hook-mode commit guard: `if hook and is_merge_in_progress(): return` before diff/AI |
| src/updater.py | chore | `__scripts_version__` bumped `v0.0.1` → `v0.0.2` (triggers hook auto-sync) |
| tests/test_core.py | test | New `TestIsMergeInProgress` class with 3 unit tests |
| docs/git-hooks-locais.md | docs | "Preserving Manual Flow" now documents merge/squash/amend skip |
| docs/git-hooks-locais.pt_br.md | docs | Same, translated |
| docs/git-hooks-locais.pt_pt.md | docs | Same, translated |
| docs/git-hooks-locais.es_es.md | docs | Same, translated |
| docs/git-hooks-locais.fr_fr.md | docs | Same, translated |
| docs/plans/2026-08-12_fix_prepare_commit_msg_merge.md | docs | Development plan (PT-BR) |

### Impact
- **Functionality:** `git pull`/`git merge` no longer triggers AI commit suggestions — the merge message stays git's own (`Merge branch '...'`). `git commit --amend`, `-c`/`-C` and `git merge --squash` now also preserve the git-supplied message. Normal `git commit` (no `-m`) still generates AI messages; `git commit -m` unchanged. Pull events keep being recorded in metrics via the `post-merge` hook.
- **Performance:** Positive — merges skip a full AI call (no diff, no API request). One extra local `git rev-parse` only in `--commit --hook` mode.
- **Compatibility:** No breaking changes. Behavior change: amend/squash/merge commits no longer receive AI messages (intended). Hook auto-sync will overwrite the 5 hook scripts in repos on next plain `gitpr` run (documented mechanism). Templates must reach GitHub `main` before releasing the CLI with `v0.0.2` so auto-sync installs the fixed templates.

### Next steps (if applicable)
- Merge templates to GitHub `main` before shipping the `__scripts_version__` bump (ordering constraint of the auto-sync)
- Pre-existing flaky test observed: `tests/test_metrics.py::TestMetricsDashboardF5::test_refresh_does_not_duplicate_columns` failed once in the full run but passes in isolation (Textual timing) — worth a stabilization pass
- Test-suite hygiene: running the metrics tests writes real export files to the project-local `.gitpr/metrics/export/` (today's pair was generated at 13:25 by the full pytest run) — tests should use a temp dir instead
