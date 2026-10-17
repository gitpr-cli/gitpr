# Survey — PR template skill artifact

**Date:** 2026-10-17
**Branch:** develop_natan
**Task:** Every generated PR body ends with `(".gitpr.commit.md": "gitpr.commit.md")` right after the "Impacto/Avisos" section. Identify the origin and fix it.

## Task context

A user reported that every generated PR text carries the literal fragment
`(".gitpr.commit.md": "gitpr.commit.md")` at the end, immediately after the
"⚠️ Impacto/Avisos" section and before the closing content/badge.

## Facts gathered

### Root cause

- `templates/gitpr.pr.pt_br.md:14` embedded a JSON-like fragment inside the
  required-structure rule:
  `O texto do PR deve conter ".gitpr.commit.md": "gitpr.commit.md",as seções: ...`
- The fragment entered with commit `a1d6692` ("feat: implementa
  internacionalização com suporte a pt-BR e en-US").
- The English, pt_pt, es_es and fr_fr variants all say only "must contain the
  sections:" / "deve conter as secções:" — no fragment. A repository-wide scan
  found this single occurrence.
- `docs/claude-code/reports/develop_natan/2026-07-13_i18n_multilang_templates_and_workflow_translations.md:34`
  had already noted the artifact and recommended cleaning it; it was never fixed.

### How the fragment reaches the PR body

1. `gitpr --skill` (and the install wizard) downloads the language variant into
   `.gitpr/skill/.gitpr.pr.md` — `src/core.py:1386-1398`, `src/main.py:1014-1019`,
   `src/core.py:1737-1738`.
2. `download_skill_file` never overwrites an existing file — `src/core.py:1288-1311`.
3. `get_skill_context("pr")` returns the file content verbatim as the system
   instruction — `src/core.py:753-821`.
4. `generate_pr_content` feeds it to the model with the schema
   `{"commit_message": "...", "pr_description": "..."}` — `src/core.py:908`,
   `src/core.py:985-997`.
5. The model obeys the instruction and includes the fragment in `pr_description`;
   `src/main.py:1604` writes the body without sanitization.

The local `.gitpr/skill/.gitpr.pr.md` of this repository is a clean, customized
English copy, so the bug does not reproduce here. It affects projects whose
skill was downloaded while the interface language was pt_br.

## Decisions from the grilling round

| Decision | Choice |
|---|---|
| Existing installs that already downloaded the corrupted file | Read-time guard: strip the exact known artifact before sending the skill to the AI; never edit the user's file |
| Regression coverage | A test that scans every `templates/*.md` and `*.yml` for embedded skill-file references |
| Defensive sanitization of the AI output | Not adopted — fixing the prompt (and the guard) removes the source; output regex would be speculative |

## Changed files

| File | Change |
|---|---|
| `templates/gitpr.pr.pt_br.md` | fixed line 14 |
| `src/core.py` | added `_CORRUPTED_PR_SKILL_ARTIFACT` and the PR-only read guard |
| `tests/test_skill_templates.py` | new template-integrity regression test |
| `tests/test_skill_context.py` | guard removes the artifact; other actions untouched |
