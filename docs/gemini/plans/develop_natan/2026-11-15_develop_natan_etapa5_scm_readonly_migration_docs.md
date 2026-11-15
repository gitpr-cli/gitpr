# Implementation Plan — Etapa 5: Document Read-Only / Ephemeral `.env` SCM Migration (`persisted=False`)

- **Date:** 2026-11-15
- **Branch:** `develop_natan`
- **Source Spec:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (Etapa 5, L149–L167)

## Goal Description

Document the resilient runtime behavior of `migrate_legacy_scm_config()` (`src/scm_settings.py`) when `~/.gitpr/.env` is read-only (e.g., `:ro` mounted volumes or ephemeral CI/CD containers). Currently, `docs/scm-multiforge.*` (5 languages) and `docs/adr/0020-per-repo-scm-provisioning-migration.md` describe the automatic migration and legacy key removal, but do not explain that `(OSError, PermissionError)` returns `persisted=False`, emits a warning on every command, and safely degrades to in-memory `os.environ`.

## Proposed Changes

### Documentation (`docs/scm-multiforge.*` — 5 languages)

#### [MODIFY] [docs/scm-multiforge.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.md)
#### [MODIFY] [docs/scm-multiforge.pt_br.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.pt_br.md)
#### [MODIFY] [docs/scm-multiforge.pt_pt.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.pt_pt.md)
#### [MODIFY] [docs/scm-multiforge.es_es.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.es_es.md)
#### [MODIFY] [docs/scm-multiforge.fr_fr.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/scm-multiforge.fr_fr.md)

Add a `> [!NOTE]` callout immediately after the `> [!WARNING]` block in `### 3.1` (before `---`, around line 124) in all 5 files, preserving identical structural counts (0 headings, 0 table rows, 0 bullets, 0 fences).

English (`docs/scm-multiforge.md`) content:
```markdown
> [!NOTE]
> **Read-only or ephemeral `~/.gitpr/.env`:**  
> If `~/.gitpr/.env` is mounted read-only (for example, `:ro` container volumes) or cannot be modified (`OSError`/`PermissionError`), `migrate_legacy_scm_config()` does not abort execution: it returns `persisted=False`, emits a warning on every command, and safely falls back to in-memory `os.environ` (materializing the per-forge slots and removing the legacy keys for the current process). To avoid repeated warnings in ephemeral runners, remove the legacy keys from the base image/script or use `GITPR_SCM_TOKEN`.
```
Localized equivalents will be written in natural `pt-BR`, `pt-PT`, `es-ES`, and `fr-FR`, preserving `persisted=False`, `os.environ`, and `GITPR_SCM_TOKEN`.

---

### Architecture Decision Record (`docs/adr/`)

#### [MODIFY] [docs/adr/0020-per-repo-scm-provisioning-migration.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/adr/0020-per-repo-scm-provisioning-migration.md)

Update `## 3. Consequências` to document the resilient read-only `.env` behavior implemented in `src/scm_settings.py`:
- Captures `(OSError, PermissionError)` during `save_config_values()` / `_remove_legacy_lines()`.
- Returns `MigrationResult(..., persisted=False, warning=...)`.
- Materializes migrated per-forge keys into `os.environ` and pops `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, and `GITPR_SCM_BASE_URL` from `os.environ` for the active process.
- Emits a warning on each run until the `.env` file or provisioning script is updated.

---

### Parity Tests (`tests/unit/`)

#### [MODIFY] [tests/unit/test_scm_multiforge_docs_parity.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/unit/test_scm_multiforge_docs_parity.py)

1. In `test_scm_multiforge_files_exist_and_have_migration_note_section()`: assert `"persisted=False"` and `"os.environ"` are present in all 5 `docs/scm-multiforge.*` files.
2. In `test_adr_0020_exists_and_references_docs_and_adr_016()`: assert `"persisted=False"`, `"os.environ"`, and `"PermissionError"` are present in `ADR-0020`.

## Verification Plan

### Automated Tests
Run:
```bash
python -m pytest tests/unit/test_scm_multiforge_docs_parity.py tests/unit/test_docs_translation_parity.py tests/scm/test_scm_settings.py -v
```
All tests must pass with zero failures or skipped parity checks.
