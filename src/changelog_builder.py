"""Data contracts and pure Markdown assembly for the gitpr release flow.

This module holds the canonical data shapes of the feature (spec section 3,
ADR-003): ``ChangeCategory``, ``ClassifiedCommit`` and ``ReleaseNotesResult``.
It performs no I/O: classification and version bumping live in their own pure
modules (``commit_classifier.py``, ``version_bump.py``) and only import the
contracts from here.

The Markdown helpers build a single changelog version section:
``## [x.y.z] - date`` + localized category sections + contributors footer.
Heading labels go through the ``__()`` engine, so the artifact language
follows the interface language (grill Q1).
"""

from dataclasses import dataclass, field
from enum import Enum

from src.i18n import __


class ChangeCategory(str, Enum):
    """User-facing categories a classified commit can belong to."""

    FEATURE = "feature"
    FIX = "fix"
    BREAKING = "breaking"
    PERFORMANCE = "performance"
    DOCS = "docs"
    REFACTOR = "refactor"
    CHORE = "chore"
    OTHER = "other"


@dataclass
class ClassifiedCommit:
    """A single commit parsed by Conventional Commits rules."""

    hash: str
    short_hash: str
    author_name: str
    author_email: str
    date: str  # ISO 8601
    subject: str
    body: str
    category: ChangeCategory
    scope: str | None  # ex.: "linter", "mcp", "pr" (from the Conventional Commit)
    breaking: bool
    pr_number: int | None  # extracted from a squash-merge subject, ex.: "(#123)"
    raw_type: str  # the original prefix ("feat", "fix", ...), "" when not Conventional Commits


@dataclass
class ReleaseNotesResult:
    """Everything the release flow produced for one version."""

    version: str  # target version, ex.: "1.2.0"
    previous_tag: str | None  # origin tag, None on the first release
    generated_at: str  # ISO 8601
    summary: str  # natural-language AI summary ("" when degraded)
    sections: dict[ChangeCategory, list[ClassifiedCommit]]
    breaking_changes: list[ClassifiedCommit]
    contributors: list[str]  # unique normalized author names
    markdown: str  # formatted changelog section, ready to be written/prepended
    warnings: list[str] = field(default_factory=list)


# ── Markdown rendering metadata ──────────────────────────────────────────────
# Labels are the FULL heading including the emoji, passed through __() so EN is
# the fallback and langs/*.json translate them (grill Q1: artifact language
# follows the interface language).
_SECTION_ORDER = (
    ChangeCategory.FEATURE,
    ChangeCategory.FIX,
    ChangeCategory.PERFORMANCE,
    ChangeCategory.DOCS,
    ChangeCategory.REFACTOR,
    ChangeCategory.CHORE,
    ChangeCategory.OTHER,
)


def organize_commits(commits):
    """Splits classified commits into per-category sections and a breaking list.

    Breaking commits are rendered only under the Breaking Changes section (not
    duplicated inside their own category section). Non-breaking commits keep
    their original relative order (newest first as collected from git log).
    """
    sections = {}
    breaking_changes = []
    for commit in commits:
        if commit.breaking:
            breaking_changes.append(commit)
        else:
            sections.setdefault(commit.category, []).append(commit)
    return sections, breaking_changes


def normalize_contributors(commits):
    """Returns unique contributor display names, deduplicated by e-mail.

    The first seen ``author_name`` wins for each e-mail; names are sorted
    alphabetically for a stable footer.
    """
    by_email = {}
    for commit in commits:
        key = (commit.author_email or "").lower()
        if key and key not in by_email:
            by_email[key] = commit.author_name or commit.author_email
    return sorted(
        (name for name in by_email.values() if name), key=lambda n: n.casefold()
    )


def _commit_line(commit):
    """Renders one bullet of a category section."""
    if commit.scope:
        return "- {subject} ({short_hash}) — {scope}".format(
            subject=commit.subject, short_hash=commit.short_hash, scope=commit.scope
        )
    return "- {subject} ({short_hash})".format(
        subject=commit.subject, short_hash=commit.short_hash
    )


def _category_heading(category):
    """Localized heading for a category block, resolved at render time.

    The labels are full strings passed through literal __() calls so the i18n
    test extractor sees every heading as a live key; runtime resolution keeps
    the section headings following the current interface language.
    """
    headings = {
        ChangeCategory.FEATURE: __("✨ Features"),
        ChangeCategory.FIX: __("🐛 Fixes"),
        ChangeCategory.PERFORMANCE: __("⚡ Performance"),
        ChangeCategory.DOCS: __("📚 Docs"),
        ChangeCategory.REFACTOR: __("♻️ Refactoring"),
        ChangeCategory.CHORE: __("🔧 Chores"),
        ChangeCategory.OTHER: __("📦 Other Changes"),
    }
    return headings[category]


def _render_category_block(category, commits):
    """Renders a full category subsection, or "" when there are no commits."""
    if not commits:
        return ""
    heading = _category_heading(category)
    lines = [f"### {heading}"] + [_commit_line(c) for c in commits]
    return "\n".join(lines)


def build_release_section(
    version, generated_at, summary, sections, breaking_changes, contributors
):
    """Builds the Markdown of one changelog version section (no I/O).

    Args:
        version: target version as displayed (ex.: "1.2.0").
        generated_at: ISO 8601 timestamp; only its date is displayed.
        summary: AI executive summary; empty means no Summary subsection.
        sections: mapping category -> non-breaking commits (see organize_commits).
        breaking_changes: commits rendered under the Breaking Changes heading.
        contributors: unique author names for the footer (see normalize_contributors).

    Returns:
        The section as a Markdown string, ready to be prepended to a changelog.
    """
    date_part = (generated_at or "")[:10]
    blocks = [f"## [{version}] - {date_part}"]

    if summary and str(summary).strip():
        blocks.append(f"### {__('Summary')}\n{summary.strip()}")

    if breaking_changes:
        lines = [f"### {__('⚠️ Breaking Changes')}"] + [
            _commit_line(c) for c in breaking_changes
        ]
        blocks.append("\n".join(lines))

    for category in _SECTION_ORDER:
        rendered = _render_category_block(category, sections.get(category) or [])
        if rendered:
            blocks.append(rendered)

    if contributors:
        blocks.append("**{label}:** {names}".format(
            label=__("Contributors"), names=", ".join(contributors)
        ))

    return "\n\n".join(blocks) + "\n"


def release_body(markdown):
    """Strips the ``## [version] - date`` heading for use as a forge release body."""
    if markdown.startswith("## ["):
        return markdown.split("\n", 1)[1].strip("\n")
    return markdown
