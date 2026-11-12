## Completion Report — Map-Reduce Token Partitioning & Per-Provider Part Limits

### What was done
- Resolved the 1,048,576 tokens context window overflow error by introducing cascade intra-file diff partitioning (File ➔ Hunk ➔ Lines).
- Separated the Map-Reduce trigger threshold (`GITPR_MAP_REDUCE_MAX_TOKENS`, default 90,000) from the individual batch part ceiling (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`, default 50,000).
- Implemented per-provider configuration (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) in `src/config.py` (`get_map_reduce_thresholds`) and `src/config_schema.py` under the `ai` category with `show_if` filters.
- Added hierarchical reduction safeguard during the Reduce phase in `src/core.py`.
- Formalized architecture in ADR-0022: [`docs/adr/0022-map-reduce-per-provider-token-partitioning.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/adr/0022-map-reduce-per-provider-token-partitioning.md).
- Updated reference documentation [`docs/map-reduce-diff.*.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/map-reduce-diff.md) across all 5 official languages.
- Added 10 automated unit tests in `tests/test_map_reduce_chunking.py` and synchronized i18n dictionaries (100% test pass).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat / refactor | Cascade chunking (file ➔ hunk ➔ line) and intermediate reduce |
| `src/config.py` | feat | `get_map_reduce_thresholds()` with hierarchical provider fallback |
| `src/config_schema.py` | feat | Added per-provider fields for trigger and part size |
| `src/issue_engine.py` | refactor | Consumed `get_map_reduce_thresholds(provider)` |
| `src/review/remote_pr.py` | refactor | Consumed `get_map_reduce_thresholds()` in `_chunk_count` |
| `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` | docs | Created ADR-0022 |
| `docs/map-reduce-diff.md` | docs | Updated technical explanation and per-provider config (EN) |
| `docs/map-reduce-diff.pt_br.md` | docs | Updated technical explanation and per-provider config (PT-BR) |
| `docs/map-reduce-diff.pt_pt.md` | docs | Updated technical explanation and per-provider config (PT-PT) |
| `docs/map-reduce-diff.es_es.md` | docs | Updated technical explanation and per-provider config (ES-ES) |
| `docs/map-reduce-diff.fr_fr.md` | docs | Updated technical explanation and per-provider config (FR-FR) |
| `CONTEXT.md` | docs | Registered domain terms for trigger, part size, and cascade chunking |
| `langs/*.json` | i18n | Synchronized and translated new config labels and messages |
| `tests/test_map_reduce_chunking.py` | test | Created 10 unit tests for cascade chunker and threshold resolution |
| `docs/survey/20261111_map_reduce_token_partitioning_surveyfacts.md` | docs | Grill session survey facts and decisions |
| `docs/plans/develop_natan/20261111_map_reduce_token_partitioning_plansfacts.md` | docs | Plan facts file per grill-with-docs |
| `docs/gemini/plans/develop_natan/2026-11-11_develop_natan_map_reduce_token_partitioning.md` | docs | Implementation plan per GEMINI.md |
| `docs/gemini/walkthrough/develop_natan/2026-11-11_map_reduce_token_partitioning.md` | docs | Walkthrough artifact per GEMINI.md |

### Impact
- **Functionality:** Eliminates 400 token limit overflow errors when analyzing diffs with massive individual files or large accumulated diffs. Guarantees that every chunk sent to the AI remains strictly within the configured part limit (50,000 tokens by default).
- **Performance:** Small diffs remain unaffected (single call). Diffs with giant files are safely divided and processed deterministically.
- **Compatibility:** Backward compatible. Default trigger limit of 90,000 tokens is preserved.

### Next steps (if applicable)
- None. The feature is complete, fully tested, and documented.
