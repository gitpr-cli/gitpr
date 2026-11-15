# Implementation Plan — Etapa 2 (`docs/config-tui.*`, `docs/pull-request-publication.*`, ADR-0019)

- **Date:** 2026-11-15
- **Branch:** `develop_natan`
- **Source:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L74–L99)

## Scope
1. Update `docs/config-tui.{pt_br,pt_pt,es_es,fr_fr}.md` (§1.8) with `GITPR_SKIP_PROJECT_CONFIG_SEED=true` and localized `#94-...` anchor links to `pull-request-publication.<lang>.md`.
2. Sync `docs/pull-request-publication.{pt_br,pt_pt,es_es,fr_fr}.md` (§4, §9.1 `[!IMPORTANT]`, §9.4, §14, §15 Ex. 9–10 + Ex. 11 renumbering) to match `docs/pull-request-publication.md` structural signature (`headings=54`, `table_rows=99`, `bullets=16`, `fences=58`).
3. Add cross-references in `docs/adr/0019-project-configuration-seed-segregation.md` to `docs/pull-request-publication.md` (§9.4) and `docs/config-tui.md` (§1.8).
4. Remove `"pull-request-publication"` from `_PARITY_EXCEPTIONS` in `tests/unit/test_docs_translation_parity.py`.
5. Create `tests/unit/test_project_config_seed_docs.py` covering all 5 languages, `> [!IMPORTANT]`, `#94-...` anchors, ADR-0019 cross-references, and `CONTEXT.md` domain terms.

## Verification
- `python -m pytest tests/unit/test_project_config_seed_docs.py tests/unit/test_docs_translation_parity.py -v`
- `python -m pytest tests/test_doc_links.py -v`
