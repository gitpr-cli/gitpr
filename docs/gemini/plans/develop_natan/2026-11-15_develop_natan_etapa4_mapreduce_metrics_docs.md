# Implementation Plan — Etapa 4: Map-Reduce Cost and Latency Documentation

- **Date:** 2026-11-15
- **Branch:** `develop_natan`
- **Reference:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L128–L146)

## Goal Description

Document in `docs/metricas-telemetria.*` (all 5 languages) and `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` how Map-Reduce partitioning multiplies AI calls and token consumption (`N` Map batches + optional intermediate pre-reduce + `1` Reduce call), how to interpret `map_reduce`, `chunks_count`, and `duration_ms` in telemetry reports and CSV/JSON exports, and how to tune `GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS`, and per-provider `<PROVIDER>` overrides to balance latency and cost.

## Proposed Changes

### Metrics & Telemetry Documentation (5 languages)

#### [MODIFY] docs/metricas-telemetria.md
Insert `### Map-Reduce Cost and Latency` right after `### Cost and Rates` (around line 140, before `### The Cycle Metric`), containing:
- Concise explanation of call/token multiplication (`N` Map calls + optional intermediate pre-reduce + `1` final Reduce call, 1s rate-limit pause between calls, and aggregated `duration_ms`).
- Bullets explaining how to read `map_reduce`, `chunks_count`, and `duration_ms` in the ledger, CSV/JSON exports, and the `🧪 Quality` / `📊 Latency` sections.
- Compact comparison table using exact `DEFAULT_MODEL_PRICES` from `src/config.py`:
  - `gemini-2.5-flash-lite`: USD 0.10 / 0.40 per 1M tokens
  - `gemini-2.5-pro`: USD 1.25 / 10.00 per 1M tokens
  - `deepseek-v4-flash`: USD 0.14 / 0.28 per 1M tokens
  - `deepseek-v4-pro`: USD 0.435 / 0.87 per 1M tokens
  - `ollama` / `local`: USD 0.00 / 0.00 (zero by definition)
- `ini` configuration snippet showing `GITPR_MAP_REDUCE_MAX_TOKENS` (default `90000`), `GITPR_MAP_REDUCE_MAX_PART_TOKENS` (default `50000`), and per-provider overrides (`GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`).

#### [MODIFY] docs/metricas-telemetria.pt_br.md
#### [MODIFY] docs/metricas-telemetria.pt_pt.md
#### [MODIFY] docs/metricas-telemetria.es_es.md
#### [MODIFY] docs/metricas-telemetria.fr_fr.md
Translate the new `### Map-Reduce Cost and Latency` subsection right after `### Custo e Tarifas` / `### Coste y Tarifas` / `### Coût et Tarifs` in each language (keeping `pt_br` and `pt_pt` distinct), preserving exact structural parity (headings, table rows, bullets, and code fences) with `docs/metricas-telemetria.md`.

---

### Architecture Decision Record

#### [MODIFY] docs/adr/0022-map-reduce-per-provider-token-partitioning.md
- Add cross-reference link to `../metricas-telemetria.md` in `Relacionados`.
- Add a concise observability note under `## 3. Consequências` linking to the new cost and latency section in `docs/metricas-telemetria.md`.

## Verification Plan

### Automated Tests
Run:
```bash
python -m pytest tests/unit/test_docs_translation_parity.py tests/test_metrics.py -v
```
Verify all structural parity checks across the 5 languages and all metrics tests pass without errors or skips.
