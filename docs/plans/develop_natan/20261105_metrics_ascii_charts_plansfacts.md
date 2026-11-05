# Plan Facts — ASCII/Unicode Charts in Metrics Dashboard (`metrics_ascii_charts`)

- **Date:** 2026-11-05
- **Branch:** `develop_natan`

## 1. Goal

Add two ASCII/Unicode visual analytics sections to the GitPR telemetry system (`gitpr metrics dashboard` TUI, `gitpr metrics` CLI summary, and `get_usage_metrics` MCP tool):
- **Token Trend (`📈 Token Trend`)**: Continuous daily token consumption series (up to 14 days, preserving zero-token days) with a Unicode sparkline (`▁▂▃▄▅▆▇█` / `·`), peak, daily average, and daily horizontal bar chart (`█` / `░`).
- **Latency Histogram (`📊 Latency`)**: Distribution of timed executions (`duration_ms > 0`) across 5 fixed buckets (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) with horizontal proportional bars (`█` / `░`), counts, percentages, and Mean / Median (P50) / P95 latency.

## 2. Execution Steps

1. **Domain Glossary (`CONTEXT.md`)**:
   - Define **Latency histogram** and **Token trend**.
2. **Ledger Duration Fallback (`src/ledger.py`)**:
   - In `_row_from_payload()`, fallback `row["duration_ms"]` to `meta.get("duration_ms", 0)` when top-level `duration_ms` is absent or `0`.
3. **Telemetry Readers & Renderers (`src/metrics.py`)**:
   - Implement chart helpers: `_bar(value, maximum, width=20)`, `_sparkline(values)`, `_duration_ms_label(ms)`, `_percentile(sorted_values, q)`.
   - Implement `token_trend_report(repo_filter=None, since=None, until=None, max_days=14)` and `token_trend_lines(trend, bar_width=20)`.
   - Implement `latency_report(repo_filter=None, since=None, until=None)` and `latency_lines(latency, bar_width=20)`.
4. **TUI Dashboard (`src/ui/metrics_app.py`)**:
   - Add `section_token_trend` and `section_latency` to `SECTION_IDS`.
   - Wire `token_trend_report` / `token_trend_lines` and `latency_report` / `latency_lines` in `_load_sections()`.
   - Increase `#sections` `max-height` from `20` to `24`.
5. **CLI Summary (`src/main.py`) & MCP Server (`src/mcp_server.py`)**:
   - Wire `token_trend` and `latency` into `_metrics_summary_lines()` and `metrics_group()`.
   - Include `token_trend` and `latency` in `get_usage_metrics()`.
6. **Translations (`langs/*.json`) & Documentation (`docs/metricas-telemetria.md`)**:
   - Add translations for `"Token Trend"`, `"Peak"`, `"Daily avg"`, `"Latency"`, `"Timed runs"`.
   - Document the new sections in `docs/metricas-telemetria.md`.
7. **Verification (`tests/test_metrics.py`)**:
   - Add unit and TUI integration tests for `token_trend_report`, `token_trend_lines`, `latency_report`, `latency_lines`, TUI rendering, and CLI/MCP parity.
