## Completion Report — Etapa 5: Documentação de Migração SCM em `.env` Somente Leitura / Efêmero (`persisted=False`)

### What was done
- Expanded section `### 3.1` across all 5 language variants of `docs/scm-multiforge.*` with a dedicated `> [!NOTE]` callout explaining that when `~/.gitpr/.env` is mounted read-only (e.g., `:ro` container volumes) or cannot be modified (`OSError`/`PermissionError`), `migrate_legacy_scm_config()` does not abort execution: it returns `persisted=False`, emits a warning on every command, and safely falls back to in-memory `os.environ` (recommending removing legacy keys from the base image/script or using `GITPR_SCM_TOKEN`).
- Updated `## 3. Consequências` in `docs/adr/0020-per-repo-scm-provisioning-migration.md` to record the `(OSError, PermissionError)` capture, `MigrationResult(..., persisted=False, warning=...)`, in-memory `os.environ` materialization/cleanup, and recurring warning behavior.
- Expanded `tests/unit/test_scm_multiforge_docs_parity.py` to assert the presence of `persisted=False` and `os.environ` in all 5 `docs/scm-multiforge.*` files and `persisted=False`, `os.environ`, and `PermissionError` in `ADR-0020`.
- Verified all 34 tests across `tests/unit/test_scm_multiforge_docs_parity.py`, `tests/unit/test_docs_translation_parity.py`, and `tests/scm/test_scm_settings.py` pass.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/scm-multiforge.md` | docs | Added `> [!NOTE]` in `### 3.1` documenting `persisted=False` and `os.environ` fallback |
| `docs/scm-multiforge.pt_br.md` | docs | Added `pt-BR` translation of the `> [!NOTE]` in `### 3.1` |
| `docs/scm-multiforge.pt_pt.md` | docs | Added `pt-PT` translation of the `> [!NOTE]` in `### 3.1` |
| `docs/scm-multiforge.es_es.md` | docs | Added `es-ES` translation of the `> [!NOTE]` in `### 3.1` |
| `docs/scm-multiforge.fr_fr.md` | docs | Added `fr-FR` translation of the `> [!NOTE]` in `### 3.1` |
| `docs/adr/0020-per-repo-scm-provisioning-migration.md` | docs | Recorded read-only `.env` fallback (`(OSError, PermissionError)`, `persisted=False`, `os.environ`) in Consequences |
| `tests/unit/test_scm_multiforge_docs_parity.py` | test | Added assertions for `persisted=False`, `os.environ`, and `PermissionError` |

### Impact
- **Functionality:** Documentation and parity tests now accurately reflect the existing resilient behavior of `migrate_legacy_scm_config()` in `src/scm_settings.py`. No runtime code changes.
- **Performance:** None.
- **Compatibility:** Preserves 100% structural parity across all 5 languages in `docs/scm-multiforge.*`.

### Next steps (if applicable)
- Review working tree changes and proceed to Etapa 6 when ready.
