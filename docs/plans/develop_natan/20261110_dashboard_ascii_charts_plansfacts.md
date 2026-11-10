# Plan Facts — Dashboard ASCII Charts & Tabbed Navigation

**Date:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `dashboard_ascii_charts`  

## Objective
Implement dedicated 2D ASCII charts (vertical latency histogram and continuous token time-series) in the GitPR Metrics Dashboard TUI (`gitpr metrics dashboard`), organized under a responsive tabbed interface (`TabbedContent`).

## Architectural Blueprint

### 1. New Module: `src/ascii_chart.py`
A dependency-free, pure Python module for generating terminal 2D ASCII graphs:
- `render_vertical_histogram(latency_data, width=64, height=8)`:
  - Takes dictionary from `latency_report()`.
  - Computes max frequency across buckets.
  - Generates Y-axis with scaled tick marks (`|`, `┼`).
  - Plots vertical columns using block elements (`█`, `▄`).
  - Draws X-axis baseline (`└─────┴─────┘`) with centered bucket labels (`<1s`, `1–5s`, `5–15s`, `15–30s`, `≥30s`).
  - Attaches summary stats (Timed runs, Avg, Median P50, P95).
  - Returns empty state if `latency_data["count"] == 0`.
- `render_token_timeseries(trend_data, width=64, height=8)`:
  - Takes dictionary from `token_trend_report()`.
  - Generates Y-axis scaled from 0 to peak tokens with formatted labels (e.g. `20k`, `10k`, `0`).
  - Draws horizontal dotted gridlines (`┼┈┈┈┤` / `┼───┤`).
  - Plots daily values as vertical columns or area chart points.
  - Draws X-axis baseline with dates formatted as `MM-DD`.
  - Attaches summary stats (Total tokens, Peak, Daily Avg).
  - Returns empty state if `trend_data["total_tokens"] == 0` or days empty.

### 2. Dashboard Refactoring: `src/ui/metrics_app.py`
- Import `TabbedContent`, `TabPane` from `textual.widgets`.
- Add tab bindings:
  - `Binding("1", "switch_tab('tab_events')", __("Events"), priority=True)`
  - `Binding("2", "switch_tab('tab_charts')", __("Charts"), priority=True)`
- Restructure `compose()`:
  - Header & Repo Label remain persistent at the top.
  - Wrap content inside `TabbedContent(id="main_tabs")`:
    - `TabPane(__("Events"), id="tab_events")`:
      - `#summary` Static.
      - `#sections` VerticalScroll.
      - `#table_container` Vertical (`DataTable`).
    - `TabPane(__("Charts"), id="tab_charts")`:
      - `VerticalScroll(id="charts_container")`:
        - `#latency_chart_panel` Static inside a styled container with title and border.
        - `#token_chart_panel` Static inside a styled container with title and border.
  - `#status_bar` and `Footer()` remain persistent at the bottom.
- In `_render_sections()`:
  - In addition to rendering the text sections, query `#latency_chart_panel` and `#token_chart_panel` and update them with the 2D ASCII charts generated from `latency_report` and `token_trend_report`.
- Add action `action_switch_tab(tab_id: str)` to support direct numeric key switching.

### 3. Unit Tests: `tests/test_ascii_chart.py`
- Test `render_vertical_histogram` with populated data, various scales, and empty data.
- Test `render_token_timeseries` with continuous series, zero-gap days, and empty data.
- Verify exact string output format, axis alignment, and presence of statistical labels.

### 4. Integration Tests & Parity: `tests/test_metrics.py`
- Add dashboard test ensuring `#tab_charts`, `#latency_chart_panel`, and `#token_chart_panel` are populated properly on mount.
- Ensure existing CLI parity tests continue passing without regression.

### 5. Documentation and ADR
- Update `CONTEXT.md` with terms: `Dashboard chart pane`, `Vertical latency histogram`, `Token time-series chart`.
- Create ADR `docs/adr/0018-dashboard-ascii-charts-and-tabbed-navigation.md`.
