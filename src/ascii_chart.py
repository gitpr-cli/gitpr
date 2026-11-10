"""
ASCII / Unicode 2D Chart Rendering Engine for GitPR Metrics.

Provides pure functions to render 2D terminal charts (vertical histograms,
time-series charts) without external dependencies or UI framework coupling.
"""

import math
from typing import Any, Dict, List, Optional


def _fmt_tokens(val: float) -> str:
    """Format token count in human-readable compact form (e.g. 1.2M, 45.0k, 500)."""
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}k"
    return str(int(round(val)))


def _duration_ms_label(ms: Optional[float]) -> str:
    """Format duration in milliseconds into ms, s, or min."""
    if ms is None:
        return "0 ms"
    if ms < 1000:
        return f"{ms:.0f} ms"
    seconds = ms / 1000.0
    if seconds < 60:
        return f"{seconds:.1f} s"
    return f"{seconds / 60.0:.1f} min"


def render_empty_card(title: str, message: str, width: int = 60) -> str:
    """Render a framed empty-state banner with informative text."""
    w = max(40, width)
    inner_w = w - 4
    top_border = f"┌{'─' * (w - 2)}┐"
    bottom_border = f"└{'─' * (w - 2)}┘"
    empty_line = f"│ {' ' * inner_w} │"

    title_line = f"│ [bold cyan]{title:<{inner_w}}[/bold cyan] │"
    msg_line = f"│ [yellow]{message:<{inner_w}}[/yellow] │"

    return "\n".join([top_border, title_line, empty_line, msg_line, bottom_border])


def render_vertical_histogram(
    latency: Optional[Dict[str, Any]],
    height: int = 7,
    col_width: int = 7,
) -> str:
    """Render a 2D vertical ASCII histogram for latency distributions.

    Args:
        latency: Dict from latency_report() containing 'count', 'average_ms',
                 'median_ms', 'p95_ms', and 'buckets'.
        height: Height in lines for the plotting area.
        col_width: Character width of each column bar.

    Returns:
        Formatted multi-line string containing the 2D chart.
    """
    if not latency or not latency.get("count") or not latency.get("buckets"):
        return render_empty_card(
            "📊 Latency Distribution",
            "No timed executions recorded in the selected window.",
        )

    buckets: List[Dict[str, Any]] = latency["buckets"]
    counts = [b["count"] for b in buckets]
    max_count = max(counts) if counts else 0
    if max_count <= 0:
        max_count = 1

    count_total = latency.get("count", 0)
    avg_lbl = _duration_ms_label(latency.get("average_ms"))
    med_lbl = _duration_ms_label(latency.get("median_ms"))
    p95_lbl = _duration_ms_label(latency.get("p95_ms"))

    lines: List[str] = []

    # Title & Summary header
    lines.append("[bold cyan]📊 Latency Histogram[/bold cyan]")
    lines.append(
        f"  Timed runs: [bold]{count_total}[/bold]  │  "
        f"Average: [cyan]{avg_lbl}[/cyan]  │  "
        f"Median (P50): [green]{med_lbl}[/green]  │  "
        f"P95: [yellow]{p95_lbl}[/yellow]"
    )
    lines.append("")

    # Y-axis label formatting width
    y_label_width = max(len(str(max_count)), 3)

    # Plot rows from top (height) down to 1
    for r in range(height, 0, -1):
        # Y-axis tick mark and label
        ratio = r / height
        level_val = round(ratio * max_count)
        if r == height:
            y_tick = f"{max_count:>{y_label_width}} ┤"
        elif r == math.ceil(height / 2):
            half_val = round(max_count / 2)
            y_tick = f"{half_val:>{y_label_width}} ┤"
        else:
            y_tick = f"{' ' * y_label_width} │"

        # Build column cells
        cells = []
        for b_count in counts:
            # Thresholds for full block and half block
            val_ratio = b_count / max_count
            if val_ratio >= (r / height):
                # Full block
                bar_chars = "█" * col_width
            elif val_ratio >= ((r - 0.5) / height):
                # Half block
                bar_chars = "▄" * col_width
            else:
                bar_chars = " " * col_width

            cells.append(bar_chars)

        row_content = "   ".join(cells)
        lines.append(f"  {y_tick}  {row_content}")

    # X-axis Baseline
    base_col = "─" * col_width
    x_axis_line = "───".join([base_col] * len(buckets))
    lines.append(f"  {0:>{y_label_width}} ┴─{x_axis_line}─")

    # Bucket Labels
    label_cells = []
    for b in buckets:
        lbl = b.get("label", "")
        label_cells.append(f"{lbl:^{col_width}}")
    lines.append(f"  {' ' * y_label_width}    " + "   ".join(label_cells))

    # Counts and percentages below labels
    stat_cells = []
    for b in buckets:
        c = b.get("count", 0)
        rate = b.get("rate", 0.0)
        txt = f"{c} ({rate:.0%})"
        stat_cells.append(f"{txt:^{col_width}}")
    lines.append(f"  {' ' * y_label_width}    " + "   ".join(stat_cells))

    return "\n".join(lines)


def render_token_timeseries(
    trend: Optional[Dict[str, Any]],
    height: int = 7,
    col_width: int = 5,
) -> str:
    """Render a 2D continuous ASCII time-series chart for daily token trends.

    Args:
        trend: Dict from token_trend_report() containing 'days', 'total_tokens',
               'peak_tokens', 'average_tokens', and 'sparkline'.
        height: Height in lines for the plotting area.
        col_width: Character width allocated per day column.

    Returns:
        Formatted multi-line string containing the 2D chart.
    """
    if not trend or not trend.get("days") or not trend.get("total_tokens"):
        return render_empty_card(
            "📈 Token Trend & Consumption",
            "No token consumption recorded in the selected window.",
        )

    days: List[Dict[str, Any]] = trend["days"]
    peak_tokens = trend.get("peak_tokens", 0)
    total_tokens = trend.get("total_tokens", 0)
    avg_tokens = trend.get("average_tokens", 0.0)
    sparkline = trend.get("sparkline", "")

    if peak_tokens <= 0:
        peak_tokens = 1

    lines: List[str] = []

    # Title & Summary header
    lines.append("[bold cyan]📈 Token Consumption Trend[/bold cyan]")
    lines.append(
        f"  Total: [bold]{total_tokens:,}[/bold]  │  "
        f"Peak: [yellow]{peak_tokens:,}[/yellow]  │  "
        f"Daily Avg: [green]{avg_tokens:,.0f}[/green]  │  "
        f"Sparkline: {sparkline}"
    )
    lines.append("")

    y_label_top = _fmt_tokens(peak_tokens)
    y_label_mid = _fmt_tokens(peak_tokens / 2)
    y_label_width = max(len(y_label_top), len(y_label_mid), 4)

    # Plot matrix from top down
    for r in range(height, 0, -1):
        if r == height:
            y_tick = f"{y_label_top:>{y_label_width}} ┼"
            grid_char = "┈"
        elif r == math.ceil(height / 2):
            y_tick = f"{y_label_mid:>{y_label_width}} ┼"
            grid_char = "┈"
        else:
            y_tick = f"{' ' * y_label_width} │"
            grid_char = " "

        day_cells = []
        for d in days:
            tokens = d.get("tokens", 0)
            ratio = tokens / peak_tokens
            if ratio >= (r / height):
                cell_str = "█" * col_width
            elif ratio >= ((r - 0.5) / height):
                cell_str = "▄" * col_width
            elif grid_char != " ":
                cell_str = grid_char * col_width
            else:
                cell_str = " " * col_width
            day_cells.append(cell_str)

        lines.append(f"  {y_tick} " + " ".join(day_cells))

    # X-axis Baseline
    base_col = "─" * col_width
    x_axis_line = "─".join([base_col] * len(days))
    lines.append(f"  {'0':>{y_label_width}} ┴─{x_axis_line}─")

    # Date labels (MM-DD)
    date_cells = []
    for d in days:
        raw_day = d.get("day", "")
        # Format YYYY-MM-DD -> MM-DD
        short_date = raw_day[5:] if len(raw_day) >= 10 else raw_day
        date_cells.append(f"{short_date:^{col_width}}")
    lines.append(f"  {' ' * y_label_width}   " + " ".join(date_cells))

    # Compact token labels below dates
    tok_cells = []
    for d in days:
        t = d.get("tokens", 0)
        tok_str = _fmt_tokens(t) if t > 0 else "·"
        tok_cells.append(f"{tok_str:^{col_width}}")
    lines.append(f"  {' ' * y_label_width}   " + " ".join(tok_cells))

    return "\n".join(lines)
