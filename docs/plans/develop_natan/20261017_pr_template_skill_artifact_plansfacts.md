# Plan facts — PR template skill artifact

**Date:** 2026-10-17
**Branch:** develop_natan
**Source survey:** `docs/survey/20261017_pr_template_skill_artifact_surveyfacts.md`

## Objective

Stop the fragment `".gitpr.commit.md": "gitpr.commit.md"` from appearing in
generated PR bodies, both for new skill downloads and for installations that
already carry the corrupted pt_br template.

## Execution plan

1. **Fix the source template**
   - `templates/gitpr.pr.pt_br.md` line 14 → `O texto do PR deve conter as seções: ...`
   - Scope limited to this line; the other language variants are already clean.

2. **Read-time guard**
   - `src/core.py`: module constant
     `_CORRUPTED_PR_SKILL_ARTIFACT = '".gitpr.commit.md": "gitpr.commit.md",'`
     next to `_SKILL_BASE_URL`.
   - In `get_skill_context`, after reading the skill file and only for
     `action_type == "pr"`, remove the exact artifact from `conteudo` before
     appending the policy context.
   - Silent on purpose: the user's file is not modified, and a warning would
     print on every PR run. Changing the prompt also changes the MD5 cache key,
     so cached responses containing the artifact are not reused.

3. **Tests**
   - New `tests/test_skill_templates.py`: scans every `templates/*.md` and
     `*.yml` for `\.gitpr\.[a-z_]+\.(md|yml)"\s*:` and reports offending
     file/line. Intentional JSON schema examples do not match.
   - `tests/test_skill_context.py`: the PR skill is sanitized on read, the file
     on disk is untouched, and the guard does not apply to other actions.

4. **Session documentation**
   - This file, the survey, and the completion report under
     `docs/claude-code/reports/develop_natan/`.

## Verification

```text
python -m pytest tests/test_skill_context.py tests/test_skill_templates.py tests/test_skill_command.py -q
python -m pytest tests/ -q
grep -rnE '\.gitpr\.[a-z]+\.(md|yml)"' templates/
```

Expected: targeted tests green; template scan empty; full suite unchanged
relative to its pre-existing failures (badge publisher auth-dependent tests and
i18n key parity, unrelated to this change).

## Constraints

- No commits, no pushes (project rule).
- Template fixes reach new downloads only after the change lands on `main`;
  existing installs are covered by the read guard.
