# Survey Facts — Dashboard ASCII Charts & Tabbed Navigation

**Date:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `dashboard_ascii_charts`  

## 1. Context and Problem Statement
GitPR maintains an offline SQLite usage ledger (`~/.gitpr/metrics/telemetry.db`).
Both the CLI (`gitpr metrics`) and the TUI dashboard (`gitpr metrics dashboard`, class `MetricsApp` in `src/ui/metrics_app.py`) present metrics including latency distributions and token trends.

Currently:
- The latency histogram and token trend are rendered only as single-line horizontal bars (`_bar()` using block characters `█` and `░`) and a 1-line sparkline (`▁▂▃▄▅▆▇█`).
- In the dashboard TUI, these are placed sequentially inside a `VerticalScroll` container with `max-height: 24` along with 5 other text sections, followed immediately by the `DataTable` for events.
- There is no 2D visualization of distributions (frequency on Y-axis, latency ranges on X-axis) or time-series (token consumption volume on Y-axis with horizontal gridlines, dates on X-axis).
- The vertical space in the existing layout is too constrained to accommodate informative 2D charts without pushing the events table out of comfortable view.

## 2. Grilling Rounds & Design Decisions

### Round 1: Core Rendering, Parity, and Layout
- **Q1: Rendering Engine:** Hybrid Textual + ASCII (Option C). The charts are rendered using high-density 2D ASCII/Unicode matrices (`█`, `▄`, `│`, `┼`, `─`) with clean border styling and colors provided by Textual's theme (`$primary`, `$accent`, `$surface`).
- **Q2: Parity Contract:** Data Parity with Surface Specialization (Option B). The CLI (`gitpr metrics`) continues to output compact single-line bars suitable for fast terminal scrolling. The TUI dashboard gains rich 2D graphs. Both surfaces strictly consume the identical underlying reports (`latency_report()` and `token_trend_report()` from `src/metrics.py`) so one ledger is never counted two ways.
- **Q3: Dashboard Layout Structure:** Tabbed Interface (Option A). `MetricsApp` is upgraded to use `TabbedContent` with two primary tabs: `[📋 Events]` (Summary, Sections, DataTable) and `[📊 Charts & Trends]` (full-width dedicated charts view).
- **Q4: Chart Specifications:**
  - **Latency:** 2D vertical histogram with buckets (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) on the X-axis, proportional column heights (`█`), count labels, and header summary card displaying P50 (median), P95, and average latency.
  - **Token Trend:** 2D continuous time-series chart with dates (`MM-DD`) on the X-axis, token volume on the Y-axis with formatted scales (`10k`, `25k`, etc.) and subtle horizontal gridlines (`┼───┤`), plus peak and daily average indicators.

### Round 2: Modularity, Dimensions, and Empty States
- **Q5: Modularity & Location:** Pure agnostic Python module `src/ascii_chart.py` (Option A). The 2D rendering algorithms (matrix calculation, scaling, axis drawing, label alignment) are implemented as pure functions without Textual dependencies, making them 100% unit-testable synchronously and deterministically. The Textual UI simply embeds the generated strings.
- **Q6: Chart Tab Arrangement:** Vertical Stack with Scroll (Option A). The charts tab presents the Latency Histogram panel and Token Trend panel stacked vertically in a `VerticalScroll` container, each with explicit borders and metric cards.
- **Q7: Empty State Behavior:** Explicit Informative Empty State Banner (Option A). When no timed executions or token data exist in the selected window, a dedicated styled message explains the absence of data rather than drawing confusing empty axes with zero values.

### Round 3: Navigation & Keybindings
- **Q8: Keyboard Navigation:** Dedicated numeric hotkeys (`1` for Events tab, `2` for Charts tab) visible in the `Footer` alongside `F5` (Refresh) and `Esc` (Exit), supporting both keyboard-only power users and mouse clicks.

## 3. Facts Verified in Codebase
- Textual version is 8.2.8, fully supporting `TabbedContent` and `TabPane`.
- `latency_report` and `token_trend_report` in `src/metrics.py` return well-structured dictionaries with buckets, counts, percentiles, days, peak, and average.
- Existing tests in `tests/test_metrics.py` enforce that `latency_lines` and `token_trend_lines` maintain parity and handle window filtering and empty states.
