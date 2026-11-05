# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add token trend and latency histogram to metrics
```

---

## 🎯 Summary

The metrics surface only exposed aggregated cost and quality numbers, so users could not see whether token consumption was spiking on specific days or whether executions were getting slower over time. This change adds two new visual reports — a continuous daily **Token Trend** (sparkline + per-day horizontal bars) and a **Latency Histogram** (bucket distribution with average, median and P95) — and exposes them consistently across the CLI (`metrics`), the TUI dashboard and the MCP `get_usage_metrics` tool. It also fixes a data gap where `duration_ms` sent only inside an event's `meta` payload was silently dropped, which would have left the latency report under-counted.

## 🛠️ Technical Changes

- **`src/metrics.py`**
  - Added `token_trend_report()`: aggregates daily tokens over the active window, preserves zero-consumption days as `tokens = 0` so gaps remain visible, caps the series at `TOKEN_TREND_MAX_DAYS` (14) and returns an empty `days` list when no tokens exist so callers can hide the section.
  - Added `latency_report()`: computes count, average, median and nearest-rank P95 plus fixed bucket distribution (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`), ignoring rows with `duration_ms <= 0` and backfill sources.
  - Added rendering helpers `_bar()`, `_sparkline()`, `_percentile()`, `_duration_ms_label()` and the section builders `token_trend_lines()` / `latency_lines()`.
- **`src/ledger.py`** — `duration_ms` now falls back to `meta.get("duration_ms")` before defaulting to `0`, so timed events that only carry duration in metadata are persisted and measurable.
- **`src/main.py`** — `_metrics_summary_lines()` and the `metrics` command accept and render `token_trend` and `latency` sections.
- **`src/mcp_server.py`** — `get_usage_metrics()` returns `token_trend` and `latency` objects in its JSON payload.
- **`src/ui/metrics_app.py`** — registered `section_token_trend` and `section_latency` sections, wired their reports and line renderers, and raised the card `max-height` from 20 to 24 to fit the new charts.
- **`langs/{pt_br,pt_pt,es_es,fr_fr}.json`** — added translations for `Token Trend`, `Peak`, `Daily avg`, `Latency` and `Timed runs`.
- **`tests/test_metrics.py`** — new `TestTokenTrendReport`, `TestLatencyReport` and `TestDashboardChartsParity` suites covering zero-day gaps, empty windows, backfill exclusion, the 14-day cap, bucket/percentile classification, and TUI/CLI/MCP parity.
- **Docs** — added survey, plan, telemetry documentation and metrics chart references.

## ⚠️ Impact/Warnings

- **Data behavior change:** events that previously stored duration only under `meta.duration_ms` were recorded as `0` and excluded from timing stats; new writes will now be counted, which can shift average/median/P95 values for fresh data. Historical rows are not backfilled.
- **No database schema changes** and no migrations required.
- **No new dependencies** added (`math`, `statistics`, `datetime` are stdlib).
- **No environment variables** introduced or changed.
- **Output contracts:** `get_usage_metrics` JSON gains two new keys (`token_trend`, `latency`) — additive only, but consumers with strict schema validation should be reviewed.
- **Missing trailing newline** at the end of the modified `langs/*.json` files (pre-existing condition, unchanged here).
- Latency buckets and the 14-day token trend cap are hard-coded constants; changing them alters rendered charts and should be treated as a UI-contract adjustment.

close #275

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)