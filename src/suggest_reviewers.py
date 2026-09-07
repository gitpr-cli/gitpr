"""Use case: from a unified diff text to ranked reviewer suggestions.

This is the only layer of the feature that touches git: it maps the added
lines parsed from the diff text onto working-tree blame hits and hands those
to the pure ranking logic (src/reviewer_suggestion.py). It never raises —
every failure path degrades into a warning — and it never runs ``git diff``
itself: the diff text comes from core.get_git_full_diff, which already
applied SMART_EXCLUDES and the -U1 -w -M -B flags.
"""
from src.blame_engine import get_blame_for_range
from src.diff_parser import parse_added_lines
from src.i18n import __
from src.reviewer_suggestion import (
    ReviewerSuggestionResult,
    normalize_email,
    rank_reviewers,
)

# Anti-abuse: per file, at most this many contiguous added-line segments are
# blamed (each segment is one `git blame` subprocess).
MAX_RANGES_PER_FILE = 40


def _group_line_ranges(line_numbers):
    """Split sorted new-side line numbers into [start, end] runs (gap <= 1)."""
    ranges = []
    start = prev = None
    for num in sorted(line_numbers):
        if start is None:
            start = prev = num
        elif num <= prev + 1:
            prev = num
        else:
            ranges.append((start, prev))
            start = prev = num
    if start is not None:
        ranges.append((start, prev))
    return ranges


def compute_reviewer_suggestions(
    diff_text,
    *,
    pr_author_email,
    pr_author_name=None,
    top_n=3,
    excluded_authors=(),
    repo_path=None,
):
    """Rank reviewer candidates from the added lines of a unified diff.

    Never raises. Files whose blame comes back empty (new, binary, shallow or
    untracked) produce a warning and are skipped; pathological diffs have
    their per-file segment count capped (MAX_RANGES_PER_FILE). An empty diff
    yields an empty result with a warning.
    """
    result = ReviewerSuggestionResult()
    added_lines = parse_added_lines(diff_text or "")
    if not added_lines:
        result.warnings.append(
            __("No added lines to attribute — skipping reviewer suggestion.")
        )
        return result

    hits = []
    for file_path, line_numbers in sorted(added_lines.items()):
        ranges = _group_line_ranges(line_numbers)
        if len(ranges) > MAX_RANGES_PER_FILE:
            result.warnings.append(
                __(
                    "File {path}: too many added segments ({count}), analyzed only the first {limit}.",
                    path=file_path,
                    count=len(ranges),
                    limit=MAX_RANGES_PER_FILE,
                )
            )
            ranges = ranges[:MAX_RANGES_PER_FILE]
        file_hits = []
        for start, end in ranges:
            file_hits.extend(
                get_blame_for_range(file_path, start, end, repo_path=repo_path)
            )
        if not file_hits:
            result.warnings.append(
                __("File {path}: no blame history found (new or binary file?)", path=file_path)
            )
        else:
            hits.extend(file_hits)

    if not hits:
        return result

    ranked = rank_reviewers(
        hits,
        pr_author_email=pr_author_email,
        pr_author_name=pr_author_name,
        excluded_authors=excluded_authors,
        top_n=top_n,
    )
    return ReviewerSuggestionResult(
        candidates=ranked.candidates,
        excluded_pr_author=ranked.excluded_pr_author,
        warnings=result.warnings,
    )


def format_candidate_line(candidate, who=None):
    """One hint line justifying a suggested reviewer.

    ``who`` is the display label (GitHub handle when resolved, otherwise the
    author name); when omitted the author name is used, falling back to the
    email address.
    """
    if who is None:
        who = candidate.author_name or candidate.author_email or "?"
    date_label = candidate.last_touch_date or __("Unknown")
    return __(
        "Suggested {who}: {lines} added line(s) in {files} file(s), last touched {date}.",
        who=who,
        lines=candidate.touched_lines,
        files=candidate.touched_files,
        date=date_label,
    )


def format_suggestion_lines(result, who_map=None):
    """Hint lines for every candidate, in ranking order.

    ``who_map`` optionally maps a normalized email address to the display
    label to use (e.g. the resolved GitHub handle); authors not present in
    the map fall back to format_candidate_line's default.
    """
    lines = []
    for candidate in result.candidates:
        who = None
        if who_map:
            who = who_map.get(normalize_email(candidate.author_email))
        lines.append(format_candidate_line(candidate, who=who))
    return lines
