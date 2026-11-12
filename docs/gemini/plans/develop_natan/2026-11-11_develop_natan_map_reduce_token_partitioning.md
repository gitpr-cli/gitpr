# Implementation Plan — Map-Reduce Token Partitioning & Per-Provider Part Limits

**Date:** 2026-11-11  
**Branch:** develop_natan  
**Task:** map_reduce_token_partitioning  

## Goal Description
Resolve context window overflow errors (1,048,576 tokens limit) in GitPR Map-Reduce workflows by introducing fine-grained cascade partitioning (File ➔ Hunk ➔ Line) for large diffs and giant individual files, establishing dedicated per-provider token limits for both the trigger threshold (`GITPR_MAP_REDUCE_MAX_TOKENS`, default 90,000) and individual batch part size (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`, default 50,000), integrating them into the `gitpr config` TUI, and updating documentation across all 5 languages.

## User Review Required
> [!IMPORTANT]
> The Map-Reduce pipeline now strictly caps each individual batch to `GITPR_MAP_REDUCE_MAX_PART_TOKENS` (default 50,000 tokens), preventing any single chunk from reaching the AI provider's context limit (such as Gemini's 1,048,576 tokens ceiling). Both trigger threshold and part size can be configured per provider in `gitpr config` or `~/.gitpr/.env`.

## Proposed Changes

### Component 1: Configuration Schema & Resolver
- **Modify**: `src/config_schema.py`
  - Register per-provider fields under `category="ai"`:
    - `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>`
    - `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`
- **Modify**: `src/config.py`
  - Implement `get_map_reduce_thresholds(provider=None)` with hierarchical fallback:
    1. Provider-specific env var (e.g. `GITPR_MAP_REDUCE_MAX_PART_TOKENS_GEMINI`).
    2. Generic env var (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`).
    3. Default value (50,000 for part tokens, 90,000 for trigger tokens).

### Component 2: Core Map-Reduce Cascade Chunking
- **Modify**: `src/core.py`
  - Enhance `split_diff_into_chunks(diff_text, max_tokens=90000, max_part_tokens=50000)`:
    - If diff <= `max_tokens`: return `[diff_text]`.
    - Cascade partitioning:
      - Split by files (`diff --git`).
      - For files exceeding `max_part_tokens`, split by hunks (`@@ -... +... @@`).
      - For hunks exceeding `max_part_tokens`, split by lines (`\n`).
      - Prepend original file header + part marker `[Part X of file Y]` to each sub-block.
    - Fallback: line-based chunking if no git headers found.
  - Update `generate_pr_content()` to query `get_map_reduce_thresholds(provider)`.
  - Add Reduce phase safeguard: if unified partial summaries exceed `max_tokens`, run intermediate reduction.

### Component 3: Engine Integrations
- **Modify**: `src/issue_engine.py` & `src/review/remote_pr.py`
  - Use `get_map_reduce_thresholds(provider)`.

### Component 4: Documentation & ADR
- **Create**: `docs/adr/0022-map-reduce-per-provider-token-partitioning.md`.
- **Modify**: `docs/map-reduce-diff.*.md` (all 5 languages).
- **Modify**: `CONTEXT.md` (record terms: `Map-reduce trigger threshold`, `Map-reduce part size`, `Cascade chunking`).

### Component 5: Test Suite
- **Modify**: `tests/test_core.py`
  - Add tests for cascade chunking (single giant file, giant hunks, non-standard diffs).
- **Modify**: `tests/test_config_schema.py`
  - Add tests for new schema fields and provider resolution.

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/test_core.py -k "chunk" -v
python -m pytest tests/test_config_schema.py -v
python -m pytest tests/unit/ -v
```

### Manual Verification
- Test `gitpr config` TUI navigation to ensure new fields render properly under AI Providers.
