# Implementation Plan — Formalize and Verify GITPR_SKIP_UPDATE_CHECK Migration Note

**Date:** 2026-11-11  
**Branch:** develop_natan  
**Task:** document_gitpr_skip_update_check_migration_note  

## Goal Description
Document and formalize the semantic breaking change of `GITPR_SKIP_UPDATE_CHECK` introduced by the strict boolean parser (`_SKIP_TRUTHY_VALUES`), ensuring full architectural governance via ADR-0021, updating technical reference documentation across all 5 official languages, and introducing an automated unit test suite (`tests/unit/test_auto_update_docs_parity.py`) to prevent documentation drift.

## User Review Required
> [!IMPORTANT]
> The migration note addresses legacy scripts or CI environments setting `GITPR_SKIP_UPDATE_CHECK=false` or `=0`. In GitPR >= 1.4.3, falsey strings no longer mute the update gate, causing the gate to execute and potentially block unexempted commands if a newer version exists on PyPI.

## Proposed Changes

### Component 1: Architectural Decision Record (ADR)
- **Create**: `docs/adr/0021-strict-boolean-update-check-migration.md`
  - Document status, date, context, problem statement (string truthiness vs boolean evaluation), architectural decision, and remediation for legacy automation.

### Component 2: Documentation Cross-References
- **Modify**:
  - `docs/auto-update.md` (EN)
  - `docs/auto-update.pt_br.md` (PT-BR)
  - `docs/auto-update.pt_pt.md` (PT-PT)
  - `docs/auto-update.es_es.md` (ES-ES)
  - `docs/auto-update.fr_fr.md` (FR-FR)
  - `docs/tutorial/install-from-source.md` (EN)
  - `docs/tutorial/install-from-source.pt_br.md` (PT-BR)
  - `docs/tutorial/install-from-source.pt_pt.md` (PT-PT)
  - `docs/tutorial/install-from-source.es_es.md` (ES-ES)
  - `docs/tutorial/install-from-source.fr_fr.md` (FR-FR)
  - Inject explicit cross-references to ADR-0021 in all migration warning blocks.

### Component 3: Automated Parity and Quality Test
- **Create**: `tests/unit/test_auto_update_docs_parity.py`
  - Enforce existence of all 10 documentation files.
  - Assert presence of `> [!WARNING]` migration blocks.
  - Assert inclusion of `GITPR_SKIP_UPDATE_CHECK`, falsey examples (`false`, `0`), truthy requirements (`1`, `true`), and links to `0021-strict-boolean-update-check-migration.md`.
  - Assert existence and content of ADR-0021.
  - Assert definition of `Update check switch` in `CONTEXT.md`.

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/unit/test_auto_update_docs_parity.py -v
python -m pytest tests/test_updater.py -v
```

### Manual Verification
- Verify link resolution and markdown formatting across all edited files.
