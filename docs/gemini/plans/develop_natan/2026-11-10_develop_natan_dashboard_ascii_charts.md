# Implementation Plan — Dashboard ASCII Charts & Tabbed Navigation

**Date:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `dashboard_ascii_charts`  

## 1. Goal Description
The objective of this task is to enhance the GitPR Metrics Dashboard TUI (`gitpr metrics dashboard`) with rich 2D ASCII charts (vertical latency histogram and daily token time-series) structured in a dedicated tabbed interface (`TabbedContent`).

## 2. User Review Required
> [!IMPORTANT]
> - The CLI `gitpr metrics` will continue to render compact 1-line horizontal bars to keep terminal command output clean and concise.
> - The Dashboard TUI (`gitpr metrics dashboard`) receives full-width 2D visual ASCII charts under a new `[📊 Charts]` tab.
> - Both CLI and TUI consume the exact same underlying analytics functions (`latency_report()` and `token_trend_report()` from `src/metrics.py`) preserving strict data parity.

## 3. Proposed Changes

### Component 1: 2D ASCII Chart Generator (`src/ascii_chart.py`) [NEW]
Create a pure Python module `src/ascii_chart.py` that formats 2D charts:
- `render_vertical_histogram(latency_dict, width=64, height=8) -> str`
- `render_token_timeseries(trend_dict, width=64, height=8) -> str`
- Formatting helpers for numbers, axes, and Unicode block characters.

### Component 2: Dashboard TUI Refactoring (`src/ui/metrics_app.py`) [MODIFY]
- Introduce `TabbedContent` and `TabPane` in `MetricsApp.compose()`.
- Add tab switching bindings (`1` for Events, `2` for Charts).
- Implement `action_switch_tab(tab_id)`.
- Render 2D charts into `#latency_chart_panel` and `#token_chart_panel` in `_render_sections()`.
- Style chart cards in `CSS` with background, border, padding, and accent colors.

### Component 3: Domain Model & Documentation [MODIFY]
- Update `CONTEXT.md` with:
  - `Dashboard chart pane`
  - `Vertical latency histogram`
  - `Token time-series chart`
- Create ADR `docs/adr/0018-dashboard-ascii-charts-and-tabbed-navigation.md`.

### Component 4: Test Suite [NEW & MODIFY]
- Create `tests/test_ascii_chart.py` for comprehensive unit tests of 2D rendering.
- Update `tests/test_metrics.py` to verify dashboard tab and chart widgets rendering.

## 4. Verification Plan

### Automated Tests
```bash
pytest tests/test_ascii_chart.py -v
pytest tests/test_metrics.py -k "TestTokenTrendReport or TestLatencyReport or TestDashboardChartsParity" -v -o addopts=""
```

### Manual Verification
- Run `gitpr metrics` to verify CLI output remains compact and intact.
- Run `gitpr metrics dashboard` (or simulate TUI mount) to verify tab navigation and 2D charts rendering.
