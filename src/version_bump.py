"""Pure semantic version decision for the gitpr release flow.

Reads nothing and writes nothing: given the classified commits of the release
range and the previous semver tag, it decides the next version following the
SemVer rules agreed in the spec (section 4.5) and the grill:

- any breaking change -> MAJOR bump;
- no breaking but at least one feature -> MINOR bump;
- otherwise (fixes/refactors/docs/chores only) -> PATCH bump.
"""

import re

from src.changelog_builder import ChangeCategory, ClassifiedCommit

# Accepts "v1.2.3", "1.2", "v2" and semver pre-release/build suffixes; the
# prefix ("v" or "") is preserved when building the suggestion.
_SEMVER_TAG_RE = re.compile(
    r"^(?P<prefix>v)?(?P<major>\d+)"
    r"(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?"
    r"(?P<suffix>[-+][0-9A-Za-z.-]+)?$"
)


def parse_semver_tag(tag):
    """Parses a semver-ish git tag into ``(prefix, major, minor, patch)``.

    Returns ``None`` when the tag is not a version tag (ex.: "release-2026").
    Missing minor/patch segments default to 0 ("v1" -> ("v", 1, 0, 0)).
    """
    if not tag:
        return None
    match = _SEMVER_TAG_RE.match(tag.strip())
    if not match:
        return None
    return (
        match.group("prefix") or "",
        int(match.group("major")),
        int(match.group("minor") or 0),
        int(match.group("patch") or 0),
    )


def format_semver(parsed):
    """Renders a ``(prefix, major, minor, patch)`` tuple back into a tag string."""
    prefix, major, minor, patch = parsed
    return f"{prefix}{major}.{minor}.{patch}"


def _bump_level(commits):
    """Decides major/minor/patch from the classified commits of the range."""
    if any(commit.breaking for commit in commits):
        return "major"
    if any(
        commit.category is ChangeCategory.FEATURE and not commit.breaking
        for commit in commits
    ):
        return "minor"
    return "patch"


def apply_bump(parsed, level):
    """Returns the version string after bumping ``parsed`` by ``level``."""
    prefix, major, minor, patch = parsed
    if level == "major":
        return format_semver((prefix, major + 1, 0, 0))
    if level == "minor":
        return format_semver((prefix, major, minor + 1, 0))
    return format_semver((prefix, major, minor, patch + 1))


def suggest_next_version(commits, previous_tag):
    """Suggests the next version from the classified commits and the last tag.

    Args:
        commits: classified commits of the range (``ClassifiedCommit`` list).
        previous_tag: the previous version tag (ex.: "v1.2.3") or ``None`` on a
            first release with no semver baseline.

    Returns:
        The suggested version string with the previous tag prefix preserved
        (ex.: "v1.3.0"), or ``None`` when there is no parseable previous tag.
    """
    parsed = parse_semver_tag(previous_tag)
    if parsed is None:
        return None
    return apply_bump(parsed, _bump_level(commits))
