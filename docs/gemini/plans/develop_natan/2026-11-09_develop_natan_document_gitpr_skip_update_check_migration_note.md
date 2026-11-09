# Implementation Plan — Document GITPR_SKIP_UPDATE_CHECK Semantic Change as Migration Note

**Date:** 2026-11-09  
**Branch:** develop_natan  
**Plan:** document_gitpr_skip_update_check_migration_note  

---

## 1. Goal Description

Document the semantic change of `GITPR_SKIP_UPDATE_CHECK` introduced in version 1.4.3 as a formal migration note across technical reference docs (`docs/auto-update.*.md`) and tutorial docs (`docs/tutorial/install-from-source.*.md`) in all 5 supported languages (EN, PT-BR, PT-PT, ES-ES, FR-FR), and sharpen the domain glossary in `CONTEXT.md` by defining the canonical term `Update check switch`.

## 2. User Review Required

> [!NOTE]
> All design choices have been aligned in Round 1 of the grilling interview:
> - Canonical documentation in both `docs/auto-update.*.md` and `docs/tutorial/install-from-source.*.md`.
> - Strict 5-language parity (EN, PT-BR, PT-PT, ES-ES, FR-FR).
> - Domain term formalization in `CONTEXT.md`.
> - Detailed alert explaining the trap where `=false` was formerly treated as truthy but now leaves the update gate active.

## 3. Proposed Changes

### Domain Glossary
#### [MODIFY] `CONTEXT.md`
- Add canonical entry `Update check switch` under the update section.

### Technical Documentation (Auto-Updater)
#### [MODIFY] `docs/auto-update.md` (EN)
#### [MODIFY] `docs/auto-update.pt_br.md` (PT-BR)
#### [MODIFY] `docs/auto-update.pt_pt.md` (PT-PT)
#### [MODIFY] `docs/auto-update.es_es.md` (ES-ES)
#### [MODIFY] `docs/auto-update.fr_fr.md` (FR-FR)
- Add subsection `### Escape Switch for Local Development (GITPR_SKIP_UPDATE_CHECK)` with `> [!WARNING]` migration note explaining strict boolean evaluation and the legacy `=false` trap.

### Tutorial Documentation (Install from Source)
#### [MODIFY] `docs/tutorial/install-from-source.md` (EN)
#### [MODIFY] `docs/tutorial/install-from-source.pt_br.md` (PT-BR)
#### [MODIFY] `docs/tutorial/install-from-source.pt_pt.md` (PT-PT)
#### [MODIFY] `docs/tutorial/install-from-source.es_es.md` (ES-ES)
#### [MODIFY] `docs/tutorial/install-from-source.fr_fr.md` (FR-FR)
- Add `> [!WARNING]` migration note in Section 5 emphasizing that legacy scripts setting `=false` or `=0` will now observe the update check running.

## 4. Verification Plan

### Automated Verification
- Read back all modified files to ensure markdown syntax validity, link integrity, and translation accuracy.
- Ensure no unintended diffs or encoding errors (`errors='replace'`).

### Manual Verification
- Review the rendered markdown callouts and verify consistency across all 5 languages.
