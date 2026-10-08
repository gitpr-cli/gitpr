# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add junior mentor mode for pedagogical code review guidance
```

---

## 🎯 Summary

Code reviews tell a developer *what* is wrong, but rarely *why it matters* or *what to learn from it*. This change introduces **Junior Mentor Mode**, which enriches review findings with pedagogical explanations (what is happening, why it matters, an everyday analogy, and concepts to study) aimed at junior engineers.

The feature is opt-in and works in two ways: automatically appended to normal reviews via `gitpr -r`/`-f --mentor` (or always, if enabled by config), and on demand against the last review through the new standalone `gitpr mentor` command. All user-facing strings were added to the es, es_es, fr, fr_fr, pt_br and pt_pt dictionaries, and a minor typo (`quando` → `cuando`) was fixed in the Spanish locale.

## 🛠️ Technical Changes

- Add `src/domain/mentor/` package with a pure, I/O-free `MentorExplanation` builder/parser that converts AI payloads into validated explanations, enforces epistemic honesty (falls back to an "insufficient evidence" message), strips hallucinated URLs from "learn more" pointers, rejects unknown finding IDs and preserves the strict order of the original findings.
- Add the `generate_mentor_explanation` use case orchestrating candidate collection (`collect_candidates`), batching AI calls (max 10 findings per run, severity-ordered), reusing the MD5 response cache, and assembling the final Markdown section.
- Add the `gitpr mentor [--finding <id>] [--provider <name>]` CLI command plus the `--mentor` flag on `-r`/`-f`, with a warning when `--mentor` is used with unsupported actions.
- Register the new `mentor` skill file (`.gitpr.mentor.md`) across `src/core.py` and `src/mcp_server.py`, and register `tests`, `explain` and `mentor` skill labels in `config_schema.py`.
- Add config keys `GITPR_REVIEW_MENTOR_MODE` (default `false`) and `GITPR_MENTOR_INCLUDE_ANALOGY` (default `true`) with helpers `mentor_mode_enabled()` and `mentor_include_analogy()`, surfaced in the interactive config UI.
- Add i18n entries for the Mentor surface in all five language dictionaries and bump `__lang_version__` to `v0.0.33`.
- Add unit tests for the domain builder/parser, the use case (success, missing API key, cache hit, severity cap/ordering, single-finding helper) and CLI integration tests for the opt-in behavior of `--mentor` and the `mentor` command.
- Include documentation for Mentor Mode (multi-language docs, ADR/glossary, plans, mentor skill templates) as part of this change set.

## ⚠️ Impact/Warnings

- **Environment/config:** two new variables are introduced — `GITPR_REVIEW_MENTOR_MODE` (off by default) and `GITPR_MENTOR_INCLUDE_ANALOGY` (on by default). Existing users are unaffected unless they opt in.
- **Dependency:** Mentor Mode requires the `.gitpr.mentor.md` skill file; run `gitpr --install` to generate it, otherwise the built-in fallback system instruction is used.
- **External calls/cost:** enabling `--mentor` or the mentor command triggers additional AI provider calls (capped at 10 findings per run, cached by prompt hash, so repeated runs on unchanged reviews cost nothing).
- **No database, no breaking API changes.** The `mentor` command relies on the persisted last review (`resolve_review`), so it must be run after a `-r`/`-f` review.


close #197

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)