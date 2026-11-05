# Implementation Plan — ASCII/Unicode Charts in Metrics Dashboard (Token Trend & Latency Histogram)

## Goal Description

Add two new visual analytics sections to GitPR's telemetry system:
1. **Token Trend (`📈 Token Trend`)**: A continuous daily time series of token consumption (up to 14 days anchored at the window's end or latest active day, preserving zero-token days) rendered with a compact Unicode vertical block sparkline (`▁▂▃▄▅▆▇█` and `·` for 0) plus per-day horizontal bar charts (`█` / `░`), peak, and daily average.
2. **Latency Histogram (`📊 Latency`)**: A distribution of timed command executions (`duration_ms > 0`) across 5 fixed latency buckets (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`), rendered with proportional horizontal bars (`█` / `░`), execution counts, percentages, and summary statistics (Mean, Median/P50, and P95).

Both metrics are computed once and rendered into `(style, text)` pairs in `src/metrics.py`, shared identically between `src/ui/metrics_app.py` (TUI) and `src/main.py` (CLI), and exposed in `src/mcp_server.py` (`get_usage_metrics`).

## Proposed Changes

- `CONTEXT.md`: Add `Latency histogram` and `Token trend` glossary definitions.
- `src/ledger.py`: Enrich `duration_ms` from `meta.get("duration_ms", 0)` when top-level `duration_ms` is not provided.
- `src/metrics.py`: Add `_bar`, `_sparkline`, `_duration_ms_label`, `_percentile`, `token_trend_report`, `token_trend_lines`, `latency_report`, and `latency_lines`.
- `src/ui/metrics_app.py`: Add `section_token_trend` and `section_latency` to `SECTION_IDS` and `_load_sections()`, and adjust `#sections` `max-height` to `24`.
- `src/main.py`: Render `token_trend_lines` and `latency_lines` in `_metrics_summary_lines()`.
- `src/mcp_server.py`: Include `token_trend` and `latency` in `get_usage_metrics()`.
- `langs/*.json` & `docs/metricas-telemetria.md`: Add i18n keys and documentation.
- `tests/test_metrics.py`: Add unit and headless TUI tests for token trend and latency histogram.
