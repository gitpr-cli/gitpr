## Completion Report — PR Template Skill Artifact

### What was done

- Removed the accidental JSON fragment `".gitpr.commit.md": "gitpr.commit.md",`
  from the required-structure rule of the Brazilian Portuguese PR skill
  template. The sentence now reads `... deve conter as seções: ...`, matching
  the other language variants.
- Added a read-time guard in `get_skill_context` that strips the exact known
  artifact from the PR skill before it becomes a system instruction. The guard
  is scoped to `action_type == "pr"` and never edits the user's skill file, so
  installations that already downloaded the corrupted template are corrected
  without a re-download.
- Added a regression test that scans every shipped template (`templates/*.md`
  and `*.yml`) for embedded skill-file references, preventing this class of
  paste from reaching users again.
- Added two tests proving the guard sanitizes the PR prompt without touching
  the file on disk and without affecting other actions.
- Recorded the survey and execution plan for the session.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `templates/gitpr.pr.pt_br.md` | fix | Removed the embedded artifact from line 14 |
| `src/core.py` | fix | Added `_CORRUPTED_PR_SKILL_ARTIFACT` and the PR-only read guard in `get_skill_context` |
| `tests/test_skill_templates.py` | test | New template-integrity scan for embedded skill references |
| `tests/test_skill_context.py` | test | Guard strips the PR artifact; other actions stay untouched |
| `docs/survey/20261017_pr_template_skill_artifact_surveyfacts.md` | docs | Survey of the root cause and decisions |
| `docs/plans/develop_natan/20261017_pr_template_skill_artifact_plansfacts.md` | docs | Execution plan and verification steps |

### Impact

- **Functionality:** Generated PR bodies no longer receive the stray fragment
  after the "⚠️ Impacto/Avisos" section for pt_br users. New `gitpr --skill`
  downloads get the clean template; existing local copies are cleaned at read
  time. Because the prompt text changes, the MD5 cache key changes and cached
  responses containing the artifact are not reused.
- **Performance:** A single substring search and replace per PR skill load.
  Negligible.
- **Compatibility:** No API or CLI change. No file format change; the user's
  `.gitpr/skill/.gitpr.pr.md` is left intact. The fix reaches new downloads only
  after it lands on `main`, which is the source served by `gitpr --skill`.

### Verification

- `python -m pytest tests/test_skill_context.py tests/test_skill_templates.py tests/test_skill_command.py -q` → **129 passed**.
- `grep -rnE '\.gitpr\.[a-z]+\.(md|yml)"' templates/` → no occurrences.
- The new regex was checked against the old line to confirm it would have caught the artifact before the fix.
- Full suite: **2930 passed, 2 skipped, 10 failed**. The 10 failures are
  pre-existing and unrelated to this change:
  - `tests/badge/test_badge_paths.py` (7): the `--no-edit` publisher path stops
    at "GitHub token expired or invalid" in this environment, so no request is
    captured.
  - `tests/test_i18n.py` (3): translation files are missing 8 recently added
    `__()` keys (`pt_br.json` and peers), the pre-existing i18n parity drift.

### Next steps (if applicable)

- Merge the change to `main` so the corrected template is served by
  `raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`.
- Optional: resolve the pre-existing i18n key parity drift with
  `python tests/sync_i18n.py` and the badge publisher token-dependent test
  environment.
