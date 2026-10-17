## Implementation Plan — PR Template Skill Artifact

**Date:** 2026-10-17
**Branch:** develop_natan
**Task:** remove the fragment `(".gitpr.commit.md": "gitpr.commit.md")` that appears at the end of every generated PR body, right after the "Impacto/Avisos" section.

## Root cause

`templates/gitpr.pr.pt_br.md:14` embeds an accidental JSON-like fragment inside the required-structure rule. The template is downloaded by `gitpr --skill` into `.gitpr/skill/.gitpr.pr.md` and injected verbatim as a system instruction by `get_skill_context("pr")`; the model treats the fragment as required content and echoes it into `pr_description`. Downloads never overwrite an existing skill file, so fixing the template alone does not repair existing installations.

## Steps

1. **Template fix** — `templates/gitpr.pr.pt_br.md` line 14:
   `O texto do PR deve conter ".gitpr.commit.md": "gitpr.commit.md",as seções: ...`
   → `O texto do PR deve conter as seções: ...`
   Other language variants are already clean.

2. **Read-time guard** — `src/core.py`:
   - Add `_CORRUPTED_PR_SKILL_ARTIFACT = '".gitpr.commit.md": "gitpr.commit.md",'`
     next to `_SKILL_BASE_URL`.
   - In `get_skill_context`, after reading the skill file, for
     `action_type == "pr"` only, remove the exact artifact from `conteudo`
     before appending the policy context. The file on disk is untouched.
   - Side effect: the changed prompt invalidates the MD5 cache, so cached
     responses containing the artifact are not reused.

3. **Tests**
   - New `tests/test_skill_templates.py`: scans every `templates/*.md` and
     `*.yml` for `\.gitpr\.[a-z_]+\.(md|yml)"\s*:` and reports file/line.
   - `tests/test_skill_context.py`: PR skill is sanitized; disk file is
     untouched; other actions are not sanitized.

4. **Documentation** — survey, plan facts and completion report as required by
   the project workflow.

## Verification

```text
python -m pytest tests/test_skill_context.py tests/test_skill_templates.py tests/test_skill_command.py -q
python -m pytest tests/ -q
grep -rnE '\.gitpr\.[a-z]+\.(md|yml)"' templates/
```

Targeted suite passed (129 tests). Full suite: 2930 passed, 10 pre-existing
failures unrelated to this change (7 badge publisher tests blocked by token
validation, 3 i18n key-parity tests).

## Constraints

- No commits or pushes.
- The corrected template reaches new downloads only after landing on `main`;
  existing installs are covered by the read guard.
