"""
Unit tests for the 2D ASCII Chart Rendering Engine (src/ascii_chart.py).
"""

import pytest
from src.ascii_chart import (
    _duration_ms_label,
    _fmt_tokens,
    render_empty_card,
    render_token_timeseries,
    render_vertical_histogram,
)


class TestAsciiChartHelpers:
    """Helper formatting tests."""

    def test_fmt_tokens_compact_representation(self):
        assert _fmt_tokens(500) == "500"
        assert _fmt_tokens(1_000) == "1.0k"
        assert _fmt_tokens(15_400) == "15.4k"
        assert _fmt_tokens(1_200_000) == "1.2M"

    def test_duration_ms_label(self):
        assert _duration_ms_label(None) == "0 ms"
        assert _duration_ms_label(500) == "500 ms"
        assert _duration_ms_label(1800) == "1.8 s"
        assert _duration_ms_label(120_000) == "2.0 min"

    def test_render_empty_card(self):
        output = render_empty_card("Test Title", "No data here", width=50)
        assert "Test Title" in output
        assert "No data here" in output
        assert "┌" in output and "┐" in output
        assert "└" in output and "┘" in output


class TestRenderVerticalHistogram:
    """Tests for 2D Vertical Latency Histogram."""

    def test_empty_or_zero_count_renders_empty_state(self):
        empty_data = {"count": 0, "buckets": []}
        res1 = render_vertical_histogram(empty_data)
        assert "No timed executions recorded" in res1

        res2 = render_vertical_histogram(None)
        assert "No timed executions recorded" in res2

    def test_populated_histogram_renders_axes_and_stats(self):
        latency_data = {
            "count": 25,
            "average_ms": 2500,
            "median_ms": 1800,
            "p95_ms": 12000,
            "buckets": [
                {"label": "< 1s", "count": 10, "rate": 0.40},
                {"label": "1–5s", "count": 8, "rate": 0.32},
                {"label": "5–15s", "count": 4, "rate": 0.16},
                {"label": "15–30s", "count": 2, "rate": 0.08},
                {"label": "≥ 30s", "count": 1, "rate": 0.04},
            ],
        }

        output = render_vertical_histogram(latency_data, height=6)

        # Header assertions
        assert "Latency Histogram" in output
        assert "Timed runs: 25" or "Timed runs: [bold]25[/bold]" in output
        assert "2.5 s" in output  # Average
        assert "1.8 s" in output  # Median
        assert "12.0 s" in output  # P95

        # Buckets and block characters assertions
        assert "< 1s" in output
        assert "1–5s" in output
        assert "5–15s" in output
        assert "15–30s" in output
        assert "≥ 30s" in output
        assert "█" in output

        # Counts and percentages below labels
        assert "10 (40%)" in output
        assert "8 (32%)" in output
        assert "4 (16%)" in output


class TestRenderTokenTimeseries:
    """Tests for 2D Token Time-Series Chart."""

    def test_empty_or_zero_tokens_renders_empty_state(self):
        empty_data = {"days": [], "total_tokens": 0}
        res1 = render_token_timeseries(empty_data)
        assert "No token consumption recorded" in res1

        res2 = render_token_timeseries(None)
        assert "No token consumption recorded" in res2

    def test_populated_timeseries_renders_axes_dates_and_stats(self):
        trend_data = {
            "total_tokens": 45000,
            "peak_tokens": 20000,
            "average_tokens": 15000.0,
            "sparkline": " ▅█",
            "days": [
                {"day": "2026-11-01", "tokens": 5000, "executions": 2},
                {"day": "2026-11-02", "tokens": 20000, "executions": 4},
                {"day": "2026-11-03", "tokens": 0, "executions": 0},
                {"day": "2026-11-04", "tokens": 20000, "executions": 3},
            ],
        }

        output = render_token_timeseries(trend_data, height=6)

        # Header assertions
        assert "Token Consumption Trend" in output
        assert "45,000" in output
        assert "20,000" in output
        assert "15,000" in output

        # Formatted dates (MM-DD)
        assert "11-01" in output
        assert "11-02" in output
        assert "11-03" in output
        assert "11-04" in output

        # Gridlines and block characters
        assert "┼" in output or "┴" in output
        assert "█" in output


class TestDashboardAsciiCharts:
    """Tests for 2D charts and tab navigation in MetricsApp."""

    def test_dashboard_composition_and_tabs(self):
        from src.ui.metrics_app import MetricsApp
        from textual.widgets import TabbedContent, TabPane, Static

        app = MetricsApp()
        with app._context():
            app._compose_stacks.append([])
            app._composed.append([])
            try:
                widgets = list(app.compose())
                # Verify Header and persistent widgets
                widget_types = [type(w) for w in widgets]
                assert Static in widget_types

                # Verify TabbedContent is part of the composition context
                tabbed_containers = [
                    w for w in app._composed[0] if isinstance(w, TabbedContent)
                ]
                assert len(tabbed_containers) == 1
                tabs_widget = tabbed_containers[0]
                assert tabs_widget.id == "main_tabs"
            finally:
                app._compose_stacks.pop()
                app._composed.pop()

    def test_action_switch_tab(self):
        from src.ui.metrics_app import MetricsApp

        app = MetricsApp()
        # Switching tab does not raise
        app.action_switch_tab("tab_charts")
        app.action_switch_tab("tab_events")

