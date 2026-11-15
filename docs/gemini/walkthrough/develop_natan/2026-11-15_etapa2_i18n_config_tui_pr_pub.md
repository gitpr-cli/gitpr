# Walkthrough — Etapa 2: Sync `docs/config-tui.*` & `docs/pull-request-publication.*` + ADR-0019 Parity Tests

## Changes Made
1. **`docs/config-tui.{pt_br,pt_pt,es_es,fr_fr}.md` (§1.8)**: Documented `GITPR_SKIP_PROJECT_CONFIG_SEED=true` for CI/CD clean-tree pipelines and monorepos, with localized links to the exact `### 9.4` heading anchor in `pull-request-publication.<lang>.md`.
2. **`docs/pull-request-publication.{pt_br,pt_pt,es_es,fr_fr}.md`**: Synchronized §4, §9.1 (`> [!IMPORTANT]`), §9.4 (complete CI/CD & monorepo migration note), §14 (`GITPR_SKIP_PROJECT_CONFIG_SEED` row), and §15 (Examples 9–10 + Example 11 renumbering), matching the canonical English structural signature (`headings=54`, `table_rows=99`, `bullets=16`, `fences=58`).
3. **`docs/adr/0019-project-configuration-seed-segregation.md`**: Added cross-references to `docs/pull-request-publication.md` (§9.4) and `docs/config-tui.md` (§1.8).
4. **`tests/unit/test_docs_translation_parity.py`**: Removed `"pull-request-publication"` from `_PARITY_EXCEPTIONS`.
5. **`tests/unit/test_project_config_seed_docs.py`**: Added 4 unit tests covering all 5 language variants, `> [!IMPORTANT]`, `#94-...` anchor resolution, ADR-0019 cross-references, and `CONTEXT.md` domain terms.

## Validation Results
Ran:
```bash
python -m pytest tests/unit/test_project_config_seed_docs.py tests/unit/test_docs_translation_parity.py tests/test_doc_links.py -v
```
Result: **18 passed in 18.70s** (0 failures, 0 skipped).
