# Survey Facts — ASCII/Unicode Charts in Metrics Dashboard (`metrics_ascii_charts`)

- **Date:** 2026-11-05
- **Branch:** `develop_natan`
- **Task:** Gráficos em ASCII/Textual no Dashboard: Histogramas de tempo e tendências de tokens na TUI de métricas.

## 1. Task Context & Codebase Facts Discovered

1. **Single-Renderer Architecture (`src/metrics.py` & `src/ui/metrics_app.py`)**:
   - Every metric section in GitPR is computed once by a reader in `src/metrics.py` and rendered once into `(style, text)` tuples (`TITLE`, `PLAIN`, `WARN`).
   - `src/main.py` (`_echo_sections` / `_metrics_summary_lines`) maps those styles to Click colors for `gitpr metrics`, while `src/ui/metrics_app.py` (`MetricsApp._markup`) maps them to Textual markup for `gitpr metrics dashboard`.
   - `src/mcp_server.py` (`get_usage_metrics`) exposes the structured dictionaries returned by the readers to MCP clients.
2. **Execution Source Filter (`_execution_rows`)**:
   - Analytical readers (`cost_report`, `quality_report`, `module_debt`, `provider_breakdown`) query `source = 'execution'` only, excluding `cache_backfill` rows because the AI cache keys by `md5(prompt)` and therefore counts distinct prompts rather than executions (R10.1).
   - While `telemetry.db` is absent (bridge mode before migration), ledger-backed sections stay hidden and `#sections_notice` prompts the user to run `gitpr metrics migrate`.
3. **Duration Recording Across 34 Call Sites**:
   - AI-powered commands (`commit`, `review`, `fullreview`, `filereview`, `issue`, `blame`), static linter runs (`linter`), and MCP check/publish tools measure elapsed milliseconds (`duration_ms > 0`) or pass `meta={"duration_ms": ...}`.
   - Instantaneous state/lifecycle events (`hook:post-checkout`, `hook:pre-push`, `hook:post-merge`, `issue_autoclose`, `skill`, `update`, `install`, `pr:publish`) log rows with `duration_ms = 0`.
   - `src/ledger.py:_row_from_payload` previously read `payload.pop("duration_ms", 0) or 0` without falling back to `meta.get("duration_ms", 0)`.

## 2. Grill Rounds & Decisions

### Round 1
- **Q1 — Surface Scope (`gitpr metrics dashboard` vs `gitpr metrics` CLI & MCP)**:
  - **Decision:** Keep full parity across surfaces. Implement `token_trend_report` / `token_trend_lines` and `latency_report` / `latency_lines` in `src/metrics.py`, render in both TUI (`MetricsApp`) and CLI (`gitpr metrics`), and expose structured data in `get_usage_metrics` (MCP).
- **Q2 — Latency Histogram Semantics**:
  - **Decision:** Group timed executions into fixed duration buckets (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) with horizontal proportional bars, counts, percentages, and summary statistics (Mean, Median/P50, P95).
- **Q3 — Token Trend Semantics**:
  - **Decision:** Continuous daily series (`day` column `YYYY-MM-DD`) filling zero-consumption days with `0` within the window so temporal spacing is preserved.
- **Q4 — TUI Visual Primitives**:
  - **Decision:** Render Unicode block characters (`█`, `░` for horizontal bars and `▁▂▃▄▅▆▇█` / `·` for sparklines) inside `Static` section widgets using `SECTION_IDS` and `_markup()`.
- **Q5 — Data Source**:
  - **Decision:** Strictly `_execution_rows()` (`source = 'execution'`) from the SQLite ledger; hidden in bridge mode when the ledger does not exist.

### Round 2
- **Q6 — Timed Execution Filter (`duration_ms > 0`) & Latency Buckets**:
  - **Decision:** Filter `duration_ms > 0` (with fallback to `meta.duration_ms` in `src/ledger.py`) so untimed hook/state rows do not skew mean/median/P95 or inflate `< 1s`. Use 5 fixed buckets (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) with max 20-block bars (`█`/`░`). Hide section when no timed runs exist.
- **Q7 — Token Trend Window Cap & Layout**:
  - **Decision:** Continuous daily series of up to 14 days anchored on `until` or the most recent active day in the window. Render a top summary line with vertical sparkline (`▁▂▃▄▅▆▇█`, `·` for 0), peak, and daily average, followed by per-day horizontal bars (`YYYY-MM-DD  ████████░░  12,450`). Hide section when total tokens in window is 0.
- **Q8 — Section Ordering & TUI Layout**:
  - **Decision:** Order `SECTION_IDS` as `section_cost`, `section_token_trend`, `section_quality`, `section_latency`, `section_modules`, `section_providers`, `section_cycle`, and increase `#sections` `max-height` in `MetricsApp` CSS from `20` to `24`.
- **Q9 — Domain Modeling (`CONTEXT.md` & ADR)**:
  - **Decision:** Add **Latency histogram** and **Token trend** to `CONTEXT.md`. Skip creating a new ADR since the design follows the established single-renderer telemetry architecture.
