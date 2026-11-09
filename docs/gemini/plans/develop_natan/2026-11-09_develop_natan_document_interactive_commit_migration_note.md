# Implementation Plan — Document Interactive Commit Migration Note

**Date:** 2026-11-09  
**Branch:** develop_natan  
**Task:** document_interactive_commit_migration_note  

## Goal Description
Document the behavioral breaking change of `gitpr -c` / `gitpr --commit` as an explicit migration note across the technical documentation (`docs/commit-message-ia.*.md`) in all 5 supported languages and refine the domain model in `CONTEXT.md`. Prior to v1.4.4, `gitpr -c` was a silent console command that merely printed the AI-generated commit message without staging files or committing; starting in v1.4.4, an interactive run launches a 4-step Textual TUI that performs `git commit`. The documentation must explicitly advise that legacy invocations were silent, and that CI and headless automation should use `--hook <file>` (or run in non-interactive/headless environments).

## User Review Required
> [!NOTE]
> All decisions from Round 1 of Grilling were approved (Opção A para Q1, Q2, Q3 e Q4).
> The migration note will be placed as a GitHub alert (`> [!WARNING]`) in Section 1 and supplemented in Section 3 of `commit-message-ia.*.md` across all 5 languages, and `CONTEXT.md` will refine the `Commit flow` glossary entry.

## Proposed Changes

### Domain Modeling
#### [MODIFY] `CONTEXT.md`
- Clarify in the `Commit flow` glossary entry that actual commit creation only happens in an `Interactive run`, whereas non-interactive runs fall back to console output or hook injection.

---

### Technical Documentation (5 Languages)
#### [MODIFY] `docs/commit-message-ia.md` (EN)
- Add Migration Note callout in Section 1 and update Section 3 with CI & headless guidelines.

#### [MODIFY] `docs/commit-message-ia.pt_br.md` (PT-BR)
- Add Migration Note callout in Section 1 and update Section 3 with CI & headless guidelines.

#### [MODIFY] `docs/commit-message-ia.pt_pt.md` (PT-PT)
- Add Migration Note callout in Section 1 and update Section 3 with CI & headless guidelines.

#### [MODIFY] `docs/commit-message-ia.es_es.md` (ES-ES)
- Add Migration Note callout in Section 1 and update Section 3 with CI & headless guidelines.

#### [MODIFY] `docs/commit-message-ia.fr_fr.md` (FR-FR)
- Add Migration Note callout in Section 1 and update Section 3 with CI & headless guidelines.

---

## Verification Plan
### Automated Tests
- `pytest tests/test_doc_links.py`
- `pytest tests/test_commit_app.py`
