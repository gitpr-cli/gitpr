# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add explain my PR reviewer guide generation
```

---

## 🎯 Summary

Reviewers often have to reverse-engineer intent from a raw diff, which slows down review and hides risk. This change introduces an "Explain my PR" capability that produces a reviewer-centric guide — what changes, why it changes, where to focus, and the regression risk — so reviewers can understand intent and target their attention without reading every line.

The feature is exposed both as a standalone `gitpr explain` command and as an optional `--explain` flag that appends the guide to generated PR descriptions.

## 🛠️ Technical Changes

- Add `src/domain/pr/explain_section_builder.py` with `PrExplanation` / `ReviewerFocusPoint` dataclasses, a `build_explain_markdown` renderer, and a `parse_explain_payload` parser that tolerates malformed or non-JSON AI output and detects `[FILL]`/`[TODO]` placeholders to flag insufficient evidence.
- Add `src/application/use_cases/generate_pr_explanation.py` orchestrating provider resolution, API key validation, skill context loading (`explain`), prompt construction, AI invocation, and parsing into the domain model.
- Register a new `explain` skill file mapping (`.gitpr.explain.md`) in `src/config.py` and expose `explain_enabled_by_default()` controlled by `GITPR_EXPLAIN_BY_DEFAULT`.
- Add the `GITPR_EXPLAIN_BY_DEFAULT` boolean field to `src/config_schema.py` under the `pr` category so it is configurable through the config UI.
- Add the `gitpr explain` CLI command with `--provider` override, diff detection with a clear error when there is no diff, and a colorized reviewer guide output.
- Add the `--explain` flag to the main CLI to append the generated guide to the PR description body and to the emitted JSON payload, merging it into a single reused `pr_desc_body` variable.
- Add help entries for the new `explain` topic in `HELP_MAP`/`HELP_PRIORITY` and new localized explanation templates.
- Add unit tests for the domain builder (markdown rendering, valid JSON parsing, placeholder detection, empty payload) and for the use case and CLI (success, missing API key, empty diff).

## ⚠️ Impact/Warnings

- Environment variable change: new optional `GITPR_EXPLAIN_BY_DEFAULT` (default `false`). When set to `true`, the Reviewer Guide section is automatically appended to every generated PR description, which adds an extra AI call and increases token usage/cost per PR.
- No database migrations or dependency changes.
- The feature depends on a configured API key for the active AI provider; when missing, generation degrades gracefully and reports it instead of failing the surrounding PR flow.
- AI output is treated as untrusted: parsing failures fall back to raw text and mark the result as insufficient evidence rather than raising.


close #189

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)