## Completion Report — Etapa 2: Sync `docs/config-tui.*` & `docs/pull-request-publication.*` + ADR-0019 Parity Tests

### What was done
- Synchronized `docs/config-tui.{pt_br,pt_pt,es_es,fr_fr}.md` (§1.8) with `GITPR_SKIP_PROJECT_CONFIG_SEED=true` and localized `#94-...` anchor links pointing to `pull-request-publication.<lang>.md`.
- Synchronized `docs/pull-request-publication.{pt_br,pt_pt,es_es,fr_fr}.md` with `docs/pull-request-publication.md` across §4 (command table, `--no-unstaged-check`, `--status`, updated §4.1 flowchart, §4.2 combined codes), §9.1 (`> [!IMPORTANT]` callout), §9.4 (full Migration & Workflow Note for CI/CD & monorepos), §14 (`GITPR_SKIP_PROJECT_CONFIG_SEED` row), and §15 (Examples 9–10 + renumbered Example 11).
- Added cross-references to `docs/pull-request-publication.md` (§9.4) and `docs/config-tui.md` (§1.8) in `docs/adr/0019-project-configuration-seed-segregation.md`.
- Removed `"pull-request-publication"` from `_PARITY_EXCEPTIONS` in `tests/unit/test_docs_translation_parity.py`.
- Created `tests/unit/test_project_config_seed_docs.py` validating all 5 language variants of both guides, `> [!IMPORTANT]`, exact `#94-...` anchors, ADR-0019 cross-references, and `CONTEXT.md` domain terms.
- Verified with `python -m pytest tests/unit/test_project_config_seed_docs.py tests/unit/test_docs_translation_parity.py tests/test_doc_links.py -v` (18 passed).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/config-tui.pt_br.md` | docs | Added `GITPR_SKIP_PROJECT_CONFIG_SEED=true` and localized `#94-...` link in §1.8 |
| `docs/config-tui.pt_pt.md` | docs | Added `GITPR_SKIP_PROJECT_CONFIG_SEED=true` and localized `#94-...` link in §1.8 |
| `docs/config-tui.es_es.md` | docs | Added `GITPR_SKIP_PROJECT_CONFIG_SEED=true` and localized `#94-...` link in §1.8 |
| `docs/config-tui.fr_fr.md` | docs | Added `GITPR_SKIP_PROJECT_CONFIG_SEED=true` and localized `#94-...` link in §1.8 |
| `docs/pull-request-publication.pt_br.md` | docs | Synced §4, §9.1, §9.4, §14, §15 with English canonical doc |
| `docs/pull-request-publication.pt_pt.md` | docs | Synced §4, §9.1, §9.4, §14, §15 with English canonical doc |
| `docs/pull-request-publication.es_es.md` | docs | Synced §4, §9.1, §9.4, §14, §15 with English canonical doc |
| `docs/pull-request-publication.fr_fr.md` | docs | Synced §4, §9.1, §9.4, §14, §15 with English canonical doc |
| `docs/adr/0019-project-configuration-seed-segregation.md` | docs | Added cross-references to `pull-request-publication.md` and `config-tui.md` |
| `tests/unit/test_docs_translation_parity.py` | test | Removed `"pull-request-publication"` from `_PARITY_EXCEPTIONS` |
| `tests/unit/test_project_config_seed_docs.py` | test | Added 5-language contract & anchor tests for ADR-0019 docs |

### Impact
- **Functionality:** Documentation-only and test-only changes; no CLI/runtime behavior altered.
- **Performance:** Negligible (adds 4 fast file-reading unit tests).
- **Compatibility:** Eliminates `"pull-request-publication"` structural parity debt across all 5 languages.

### Next steps (if applicable)
- Proceed to Etapa 3 in `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` when ready.
