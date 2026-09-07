# Completion Report — Documentation: Suggested Reviewers (suggested-reviewers.md, 5 languages)

This task's plan: [docs/plans/20260907_documentacao_suggested_reviewers.md](../../../plans/20260907_documentacao_suggested_reviewers.md) · Feature sources: [ADR-002-reviewer-suggestion.md](../../../plans/ADR-002-reviewer-suggestion.md) · [glossary-reviewer-suggestion.md](../../../plans/glossary-reviewer-suggestion.md) · [20260906_skill_gitpr_reviewer_suggestion_plan.md](../../../plans/20260906_skill_gitpr_reviewer_suggestion_plan.md) · Feature implementation report: [2026-09-06_reviewer_suggestion.md](2026-09-06_reviewer_suggestion.md)

## What was done

Created the missing user-facing technical documentation family for the **Suggested Reviewers** feature (git-blame-based reviewer suggestion in the default PR publisher flow) in `docs/`, mirroring the conventions of the existing 30 doc families (model: `docs/code-review-ia.md`, structure reference: `docs/scm-multiforge.md`) — English master without suffix plus the four language copies (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) with line-for-line parity (all five files: **107 lines each**, headings at identical line numbers). The family name `suggested-reviewers.md` was fixed by the code, not chosen: `HELP_MAP["no-suggest-reviewers"]` already registers `get_doc_url("suggested-reviewers.md")` (`src/main.py:222`) — a dead link until now. Feature identity was confirmed via grilling round 1 (the "Multi-Forge SCM" name in the request was stale template text; that family was committed today in `ddc8fff`). Dated plan in `docs/plans/` plus this mandatory completion report. No ADR was created (no hard-to-reverse decision) and the existing ADR-002/glossary/plan were left untouched.

- **`docs/suggested-reviewers.md`** (EN master, 107 lines): `# Technical Documentation: Suggested Reviewers for Pull Requests` with numbered sections — 1. How It Works (1.1 Authorship over the Added Lines: diff base vs. working tree incl. staged + smart-excludes, added lines only, "Not Committed Yet" `0000…` skipped, blame without revision, no-history files → warning; 1.2 Ranking and Exclusions: 50% lines / 30% files / 20% recency table with `1/(1+days/90)` half-life, exclusions of PR author and bots — `[bot]` suffix + known list, `users.noreply.github.com` never a bot — plus `GITPR_REVIEWER_SUGGESTION_EXCLUDED`, tie-break by lines, truncation to `top_n`); 2. Configuration (default ON, `--no-suggest-reviewers`, 3-key `GITPR_*` `.env` table with falsy values and invalid-`top_n` fallback); 3. Suggested Reviewers in the PR Publisher (TUI) (3.1 editable `👥` section — CSV input prefilled + read-only hint, empty = no submission; 3.2 Publishing — F3 → PR created → GitHub `requested_reviewers` attach on create and update paths, non-fatal on failure such as HTTP 422; 3.3 Contextual help); 4. Forge Support and Limitations (GitHub submits vs. GitLab/Bitbucket/Azure local-only table, best-effort email→handle mapping via noreply parse + `/search/users in:email` fallback); 5. For Developers and Plugins (flat `src/` modules, `DEFAULT_CONFIG` keys, non-abstract SCM method defaulting to `ScmNotSupportedError`, GitHub-only `email_to_handle()`, view dict, links to ADR-002 and glossary). Closing blockquote cross-links `pull-request-publication.md`.
- **Four translations** (`pt_br`, `pt_pt`, `es_es`, `fr_fr`): faithful per-language prose (PT-PT genuinely European — "por omissão", "secção", "ficheiro", "campo de introdução"; FR with "relecteurs" GitHub vocabulary), headings translated (`# Documentação Técnica: Revisores Sugeridos para Pull Requests` / `# Documentación Técnica: ...` / `# Documentation Technique : Relecteurs Suggérés ...`), technical tokens verbatim (env vars, flags, endpoints, module names), quoted UI strings taken from the real translations in `langs/*.json` (search line, `⚠️ ... could not be requested` warning, `👥` section label — never invented), cross-links kept unsuffixed exactly like the existing translated families.
- **`docs/plans/20260907_documentacao_suggested_reviewers.md`**: dated task plan (PT-BR, sibling-plan style) recording context, grilling decision, deliverables, document outline, steps and verification.
- **This report**.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| docs/suggested-reviewers.md | docs | New EN master — Suggested Reviewers user reference (107 lines) |
| docs/suggested-reviewers.pt_br.md | docs | New PT-BR translation (107 lines, line-parity) |
| docs/suggested-reviewers.pt_pt.md | docs | New PT-PT translation (107 lines, line-parity) |
| docs/suggested-reviewers.es_es.md | docs | New ES translation (107 lines, line-parity) |
| docs/suggested-reviewers.fr_fr.md | docs | New FR translation (107 lines, line-parity) |
| docs/plans/20260907_documentacao_suggested_reviewers.md | docs | Dated task plan (PT-BR) |
| docs/claude-code/reports/develop_natan/2026-09-07_documentacao_suggested_reviewers.md | docs | This report |

### Verification

| Check | Result |
|-------|--------|
| Line parity across the 5 doc files (`wc -l`) | 107 / 107 / 107 / 107 / 107 |
| Heading outline parity (`grep '^#'`, real headings) | Identical line positions in all 5 files (H1 at 1; H2 at 9, 35, 60, 84, 99) |
| Technical tokens preserved | Spot-checked: `GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_*`, `--no-suggest-reviewers`, `requested_reviewers`, `ScmNotSupportedError` intact in all copies |
| Git state | Only the 7 intended new files untracked; nothing staged or committed |

No test suite run — docs-only task, no code touched.

## Impact

- **Functionality:** none — documentation only. Users now have the feature reference that was missing from `docs/`, in the same 5-language family format as every other GitPR technical doc; the contextual help dead link (`gitpr -h --no-suggest-reviewers` → `suggested-reviewers.md`) is resolved for the docs site once it mirrors `docs/`.
- **Performance:** none.
- **Compatibility:** purely additive. Existing ADR-002/glossary/plan and all prior docs are unchanged; no README/CLAUDE.md/ARCHITECTURE registration was performed (convention for doc families); line parity with existing families is preserved (no edits to other docs).

## Next steps

- **User review & commit** of the working tree (nothing was staged or committed per project rule).
- **Optional:** register the new family in the README.md "Technical Documentation" index (and its 4 translated copies) in a later task — deliberately out of scope here.
- **Optional:** if the docs site (gitpr.natanfiuza.dev.br) mirrors `docs/` file families, no action needed — the suffix convention is already the site's language mechanism, and the `HELP_MAP` URL starts working automatically.
