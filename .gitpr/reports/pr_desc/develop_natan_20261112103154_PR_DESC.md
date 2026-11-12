# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add per-provider map-reduce token partitioning
```

---

## 🎯 Summary

Large diffs were previously chunked with a single hardcoded 90,000-token threshold shared by every AI provider, forcing identical behavior regardless of each provider's actual context window and cost profile. This change introduces a hierarchical, per-provider Map-Reduce configuration so Gemini, DeepSeek, and Ollama can trigger chunking and size their batches independently, and it hardens the chunker so a single oversized file or hunk can no longer break the split. The goal is to reduce wasted tokens, avoid oversized requests that degrade summary quality, and give operators explicit control over cost/quality trade-offs.

## 🛠️ Technical Changes

- Added `get_map_reduce_thresholds(provider)` in `src/config.py` with a three-level resolution hierarchy: provider-specific env (`GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`) → generic env (`GITPR_MAP_REDUCE_MAX_TOKENS` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS`) → baseline defaults (90,000 trigger / 50,000 part).
- Added `_positive_int_from_raw` to safely reject invalid, non-numeric, or non-positive values with fallback, and guaranteed the invariant `max_part_tokens <= max_tokens`.
- Extended `split_diff_into_chunks` with a `max_part_tokens` parameter and a cascade chunker: `_split_giant_file` splits oversized files at hunk boundaries, and `_split_line_chunk` splits monolithic hunks at line/character boundaries, always re-attaching the file header and a `[file - part N]` marker.
- Hardened the file-header regex to tolerate additional diff prefixes when parsing file boundaries.
- Added an intermediate reduction pass in `generate_pr_content`: when the consolidated summary set still exceeds `max_tokens`, partial summaries are batched to `max_part_tokens` and re-consolidated via `call_ai_model`, aggregating telemetry metadata.
- Registered per-provider config fields in `src/config_schema.py` (Gemini, DeepSeek, Ollama) with `show_if` gating on `DEFAULT_AI_PROVIDER`.
- Updated `src/issue_engine.py` and `src/review/remote_pr.py::_chunk_count` to resolve thresholds through the new function.
- Added translations (es, es_es, fr, fr_fr, pt_br, pt_pt) for the new UI strings and messages, and sorted/normalized several existing keys.
- Added `tests/test_map_reduce_chunking.py` covering threshold resolution, env precedence, capping, invalid input handling, and all cascade chunking levels.

## ⚠️ Impact/Warnings

- **Environment variables:** introduces `GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS`, and provider-suffixed variants (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`). Defaults preserve prior behavior (90,000 trigger), but the new 50,000 part size changes how large diffs are batched by default.
- **Behavioral change:** chunk boundaries and part sizes may differ from previous runs, so summary/cost output for large diffs will vary. The new intermediate reduction pass adds extra AI calls when summary sets remain large, increasing token usage and latency in those cases.
- **No database changes.** No new third-party dependencies.
- **Config UI:** new fields are visible in the AI settings panel and filtered by the active provider; translation files must stay in sync with the new keys.

close #317

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)