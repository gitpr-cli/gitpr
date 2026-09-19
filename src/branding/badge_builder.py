"""Builds the badge markdown and appends it to a pull request body.

The URL is constructed and never fetched: a badge that needs the network to be
written would fail exactly where the product cannot afford to — the moment a
pull request is published. shields.io renders it in the reader's browser.

The text is fixed English on purpose. The badge is a public artefact that ends
up inside someone else's repository, next to the PR body the AI wrote, so it
follows the same rule: English, whatever the interface language is.
"""

from urllib.parse import quote

from src.branding.badge_data import collect_linter_counts
from src.config import badge_enabled

# Where the badge points, and where shields.io renders it from.
BRAND_URL = "https://gitpr.natanfiuza.dev.br/"
SHIELDS_BASE = "https://img.shields.io/badge/"

BADGE_LABEL = "GitPR"
README_MESSAGE = "quality-checked"
README_COLOR = "blue"

# The styles shields.io ships. The PR badge is always the default one.
VALID_STYLES = ("flat", "flat-square", "for-the-badge")
DEFAULT_STYLE = "flat"

# Identifies a badge GitPR already put in a body, so appending twice is a no-op.
_BADGE_MARKER = "img.shields.io/badge/GitPR"


def _escape(text):
    """Encode a badge segment the way shields.io reads it.

    Its own escaping comes first — a literal dash and underscore are doubled so
    a single one still means separator — and the percent-encoding after it
    covers what is left, so the URL stays pure ASCII (the separator between the
    counts is a middle dot).
    """
    escaped = text.replace("-", "--").replace("_", "__").replace(" ", "_")
    return quote(escaped, safe="")


def _counted(number, noun):
    """``1 error`` / ``2 errors`` — each count pluralises on its own."""
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def _message(counts):
    """What the badge says: the two counts, or a clean bill of health."""
    if not counts.errors and not counts.warnings:
        return "no issues"

    return f"{_counted(counts.errors, 'error')} · {_counted(counts.warnings, 'warning')}"


def _color(counts):
    """Red for a blocking finding, yellow for advice, green for a clean diff."""
    if counts.errors:
        return "red"

    return "yellow" if counts.warnings else "brightgreen"


def _snippet(message, color, style, style_in_url):
    """The linked image, in the shape GitHub and the forges render."""
    url = f"{SHIELDS_BASE}{_escape(BADGE_LABEL)}-{_escape(message)}-{color}"
    if style_in_url:
        url += f"?style={style}"

    return f"[![{BADGE_LABEL}]({url})]({BRAND_URL})"


def normalize_style(style):
    """The requested style if shields.io has it, the default otherwise."""
    return style if style in VALID_STYLES else DEFAULT_STYLE


def build_pr_badge(counts):
    """The badge for a published PR body.

    Empty when there is nothing to report: ``BadgeCounts`` with both lists
    empty is still a real measurement and says ``no issues``, but ``None`` —
    no rules configured — means the badge would be claiming a check nobody ran.
    """
    if counts is None:
        return ""

    return _snippet(_message(counts), _color(counts), DEFAULT_STYLE, style_in_url=False)


def build_readme_badge(style=DEFAULT_STYLE):
    """The static adoption badge, for a project's own README."""
    return _snippet(
        README_MESSAGE, README_COLOR, normalize_style(style), style_in_url=True
    )


def has_badge(body):
    """Whether this body already carries the GitPR badge."""
    return _BADGE_MARKER in (body or "")


def append_badge(body, badge):
    """Put ``badge`` at the end of a PR body, after a rule, exactly once.

    A republish sends the whole body again — including one the user may have
    edited — so an existing badge is left where it is instead of stacking.
    """
    if not badge or has_badge(body):
        return body

    body = (body or "").rstrip()
    if not body:
        return badge

    return f"{body}\n\n---\n\n{badge}"


def attach_pr_badge(pr_data, diff_text):
    """Put the badge on a pull request body that is about to be published.

    Called once, where ``pr_data`` is complete: both publishers — the TUI and
    ``--no-edit`` — read the body from it, so the badge reaches the screen where
    the user can delete it and the request that goes out, from a single place.
    The local ``.md`` written by ``--no-publish`` is composed from the AI payload
    and never passes here.

    Nothing is attached when the user opted out with ``GITPR_BADGE=false``, and
    nothing is attached when the linter had no rules to run — a green badge over
    an unchecked diff would be a claim GitPR cannot back.
    """
    if not badge_enabled():
        return

    badge = build_pr_badge(collect_linter_counts(diff_text))
    if badge:
        pr_data["pr_description"] = append_badge(pr_data["pr_description"], badge)
