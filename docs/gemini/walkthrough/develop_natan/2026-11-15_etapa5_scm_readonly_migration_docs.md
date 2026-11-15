# Walkthrough — Etapa 5: Read-Only / Ephemeral `.env` SCM Migration Docs

## Changes Made
1. **`docs/scm-multiforge.*` (5 languages: `.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`)**:
   - Added a `> [!NOTE]` callout immediately below `> [!WARNING]` in `### 3.1` documenting that when `~/.gitpr/.env` is read-only or triggers `OSError`/`PermissionError`, `migrate_legacy_scm_config()` returns `persisted=False`, emits a warning on every command, and falls back to in-memory `os.environ` (recommending removing legacy keys from the image/script or using `GITPR_SCM_TOKEN`).
2. **`docs/adr/0020-per-repo-scm-provisioning-migration.md`**:
   - Updated `## 3. Consequências` (Positivas & Negativas/Riscos) to record `(OSError, PermissionError)` handling, `MigrationResult(..., persisted=False, warning=...)`, `os.environ` materialization/cleanup, and recurring warnings until legacy keys are removed.
3. **`tests/unit/test_scm_multiforge_docs_parity.py`**:
   - Added assertions verifying `persisted=False` and `os.environ` in all 5 `docs/scm-multiforge.*` files, and `persisted=False`, `os.environ`, and `PermissionError` in `ADR-0020`.

## Validation Results
Ran:
```bash
python -m pytest tests/unit/test_scm_multiforge_docs_parity.py tests/unit/test_docs_translation_parity.py tests/scm/test_scm_settings.py -v
```
- **Result:** `34 passed in 1.04s` (0 failures, 0 skipped).
