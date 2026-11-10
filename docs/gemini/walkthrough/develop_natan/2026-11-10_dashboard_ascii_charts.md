# Walkthrough — Dashboard ASCII Charts & Tabbed Navigation

## Overview
This walkthrough demonstrates the new 2D ASCII charts (vertical latency histogram and daily token consumption time-series) and the tabbed navigation system in the GitPR Metrics Dashboard (`gitpr metrics dashboard`).

---

## 1. Visual Design & Architecture

### Tab 1: [1: 📋 Events]
Preserves the classic operational dashboard:
- Repository and ledger summary banner.
- Compact single-line sections (Cost, Quality, Modules, Providers, Cycle).
- Detailed interactive `DataTable` listing raw events, timestamps, commands, providers, and tokens.

### Tab 2: [2: 📊 Charts & Trends]
Full-width dedicated visual analytics pane (`VerticalScroll`):
1. **Vertical Latency Histogram (`#latency_chart_panel`)**:
   - Cartesian 2D grid with discrete latency buckets (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) on the X-axis.
   - Column bars built with block characters (`█`, `▄`) scaled to maximum frequency.
   - Real-time statistics card showing Timed Runs, Average Latency, Median (P50), and P95.
2. **Token Consumption Time-Series (`#token_chart_panel`)**:
   - Cartesian 2D grid with date intervals (`MM-DD`) on the X-axis and auto-scaled token volume (`10k`, `25k`, etc.) on the Y-axis.
   - Dotted horizontal gridlines (`┼───┤`).
   - Real-time statistics card showing Total Tokens, Peak Consumption, Daily Average, and compact Sparkline.

---

## 2. Keyboard Navigation
- Press `1`: Instantly activates Tab 1 (`Events`).
- Press `2`: Instantly activates Tab 2 (`Charts & Trends`).
- Press `F5`: Reloads and refreshes telemetry from the ledger across both tabs.
- Press `Esc`: Exits the dashboard.
- Mouse clicks on the tab header buttons work seamlessly.

---

## 3. Automated Verification Results
```bash
# Unit tests for the 2D chart engine (src/ascii_chart.py)
$env:GITPR_LANG="en_us"; pytest tests/test_ascii_chart.py -v -o addopts=""
# Result: 9 passed in 1.13s

# Telemetry report suite (tests/test_metrics.py)
$env:GITPR_LANG="en_us"; pytest tests/test_metrics.py -k "TestTokenTrendReport or TestLatencyReport" -v -o addopts=""
# Result: 8 passed in 5.60s
```
