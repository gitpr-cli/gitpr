# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add ASCII charts and tabbed navigation to metrics dashboard
```

---

## 🎯 Summary

The metrics dashboard only surfaced latency and token consumption as textual sections, making distribution and day-over-day trends hard to read at a glance. This change introduces a dependency-free 2D chart rendering engine and reorganizes the TUI into tabs so operators can visually inspect latency distributions and token trends without leaving the terminal.

The rendering logic is kept as pure functions, decoupled from Textual, so it can be reused by other front-ends and unit-tested in isolation.

## 🛠️ Technical Changes

- Add `src/ascii_chart.py`, a pure-function rendering engine providing:
  - `render_vertical_histogram` for latency bucket distributions (Y-axis ticks, full/half block bars, counts and percentages per bucket).
  - `render_token_timeseries` for daily token consumption (date labels, compact token labels, optional sparkline summary).
  - `render_empty_card` for framed empty states.
  - Internal formatters `_fmt_tokens` (compact `1.2M` / `45.0k`) and `_duration_ms_label` (`ms` / `s` / `min`).
- Restructure `MetricsApp` into a `TabbedContent` with an `Events` tab and a new `Charts & Trends` tab housing the latency and token chart panels.
- Add `Binding` shortcuts `1` and `2` plus `action_switch_tab` to jump between tabs.
- Change `_load_sections` to return `(rendered_sections, chart_data)`, capturing the raw `latency` and `token_trend` payloads while rendering the existing text sections in a single pass (avoids duplicate reader calls).
- Propagate `chart_data` through `_finish_scan` into `_render_sections`, with a fallback that re-queries the reports when data is missing.
- Render an instructive empty state in the charts tab when the ledger is unavailable, pointing users to `gitpr metrics migrate`.
- Add `tests/test_ascii_chart.py` covering formatters, empty states, populated histogram/timeseries output, tab composition and tab switching.
- Update CONTEXT, ADR 0018, and plan/report/walkthrough docs to reflect the chart and navigation design.

## ⚠️ Impact/Warnings

- **Database:** No schema or migration changes. The new charts read the same ledger reports already used by the metrics pipeline.
- **Environment variables:** None added or modified.
- **Dependencies:** None added — the renderer relies only on the standard library, and Textual widgets used (`TabbedContent`, `TabPane`) ship with the existing Textual dependency.
- **Behavioral change:** `_load_sections` now returns a tuple instead of a list; any external caller must be updated accordingly.
- **Robustness note:** chart rendering in `_render_sections` is wrapped in a broad `try/except`, which intentionally degrades to text-only output but may mask real rendering errors during development.
- **Compatibility:** Charts use Unicode block/box-drawing characters, so terminals must support UTF-8 box drawing for correct alignment.

close #306

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)