"""Pure Conventional Commits parsing for the gitpr release flow.

Every function here is deterministic and performs no I/O, so the classification
rules can be unit-tested without fixtures (spec section 8.1 and 8.3). A commit
that does not follow the Conventional Commits shape is never an error: it is
classified as ``ChangeCategory.OTHER`` and keeps ``raw_type == ""`` so the
engine can count how many commits fell outside the standard.

Recognized signals, per the Conventional Commits spec:
- header ``type(scope)!: subject`` (also ``type!: subject``);
- ``!`` right after the type/scope;
- a ``BREAKING CHANGE:`` (or ``BREAKING-CHANGE:``) line in the body;
- a GitHub-style squash subject tail ``(#123)`` for ``pr_number``.

A forge that merges through a merge commit instead of a squash leaves the PR
number in the *merge* message, which never reaches this module through the
engine's commit range — ``pr_number_from_merge()`` reads that message, and the
engine calls it from its own ``git log --merges`` pass.
"""

import re

from src.changelog_builder import ChangeCategory, ClassifiedCommit


# Canonical Conventional Commits types mapped to change categories. Prefixes
# not listed here (ex.: "test", "build") still parse as Conventional Commits
# headers but land in OTHER — they keep their ``raw_type`` for the record.
_TYPE_TO_CATEGORY = {
    "feat": ChangeCategory.FEATURE,
    "fix": ChangeCategory.FIX,
    "perf": ChangeCategory.PERFORMANCE,
    "docs": ChangeCategory.DOCS,
    "refactor": ChangeCategory.REFACTOR,
    "chore": ChangeCategory.CHORE,
}

# type(scope)!: subject — multiline subjects are not Conventional Commits.
_HEADER_RE = re.compile(
    r"^(?P<type>[A-Za-z][A-Za-z0-9-]*)(?:\((?P<scope>[^()\n]*)\))?"
    r"(?P<breaking>!)?:\s*(?P<subject>.+?)\s*$"
)

# BREAKING CHANGE: / BREAKING-CHANGE: anywhere in the body (own line or inline).
_BREAKING_BODY_RE = re.compile(r"BREAKING[ -]CHANGE\s*:", re.IGNORECASE)

# Squash-merge PR reference at the very end of the subject, ex. "fix: x (#42)".
_PR_NUMBER_RE = re.compile(r"\(#(?P<number>\d+)\)\s*$")

# Merge-commit PR references, one per forge and in the shape each one writes
# the merge subject: GitHub "Merge pull request #193 from o:b", Bitbucket
# "Merged in b (pull request #193)", Azure DevOps "Merged PR 193: title".
# GitLab writes a neutral subject and puts the reference in the body instead
# ("Merge branch 'b' into 'main'" + "See merge request group/project!193"),
# which _MERGE_BODY_RE reads. A merge that names no request — a branch
# synchronization such as "Merge branch 'main' into develop" — matches none of
# them, which is the point: it must never lend its PR number to a commit.
_MERGE_SUBJECT_RES = (
    re.compile(r"^Merge pull request #(?P<number>\d+)\b"),
    re.compile(r"^Merged in .*\(pull request #(?P<number>\d+)\)"),
    re.compile(r"^Merged PR (?P<number>\d+):"),
)
_MERGE_BODY_RE = re.compile(
    r"^See merge request [^\s!]+!(?P<number>\d+)", re.MULTILINE
)


def classify_commit(
    commit_hash,
    short_hash,
    author_name,
    author_email,
    date,
    subject,
    body,
):
    """Classifies one raw commit into a ``ClassifiedCommit`` (never raises).

    Args:
        commit_hash: full git hash.
        short_hash: abbreviated hash displayed in the changelog.
        author_name / author_email: commit author metadata.
        date: ISO 8601 commit date.
        subject: first line of the commit message.
        body: remaining lines of the commit message (may be "").
    """
    subject = subject.strip() if subject else ""
    body = body.strip() if body else ""

    match = _HEADER_RE.match(subject)
    if not match:
        return ClassifiedCommit(
            hash=commit_hash,
            short_hash=short_hash,
            author_name=author_name,
            author_email=author_email,
            date=date,
            subject=subject,
            body=body,
            category=ChangeCategory.OTHER,
            scope=None,
            breaking=bool(_BREAKING_BODY_RE.search(body)),
            pr_number=_extract_pr_number(subject),
            raw_type="",
        )

    raw_type = match.group("type")
    pr_match = _PR_NUMBER_RE.search(match.group("subject"))
    return ClassifiedCommit(
        hash=commit_hash,
        short_hash=short_hash,
        author_name=author_name,
        author_email=author_email,
        date=date,
        subject=match.group("subject"),
        body=body,
        category=_TYPE_TO_CATEGORY.get(raw_type.lower(), ChangeCategory.OTHER),
        scope=match.group("scope") or None,
        breaking=bool(match.group("breaking")) or bool(_BREAKING_BODY_RE.search(body)),
        pr_number=int(pr_match.group("number")) if pr_match else None,
        raw_type=raw_type,
    )


def classify_commits(raw_commits):
    """Classifies a list of raw commit mappings produced by the engine.

    Args:
        raw_commits: iterable of dicts with the keys ``hash``, ``short_hash``,
            ``author_name``, ``author_email``, ``date``, ``subject``, ``body``
            (the shape emitted by ``release_engine`` git log parsing).

    Returns:
        The list of ``ClassifiedCommit``, preserving the input order.
    """
    return [
        classify_commit(
            commit_hash=raw.get("hash", ""),
            short_hash=raw.get("short_hash", ""),
            author_name=raw.get("author_name", ""),
            author_email=raw.get("author_email", ""),
            date=raw.get("date", ""),
            subject=raw.get("subject", ""),
            body=raw.get("body", ""),
        )
        for raw in raw_commits
    ]


def pr_number_from_merge(subject, body=""):
    """Extracts the PR number a merge commit names, or ``None``.

    Only merge messages are read here: the number a merge names belongs to the
    merge, not to any commit it brings in (that attribution is the engine's
    ancestry walk). A merge subject with no recognizable reference — the usual
    branch synchronization — returns ``None`` rather than a guess.

    Args:
        subject: first line of the merge commit message.
        body: remaining lines, where GitLab writes its reference.
    """
    subject = subject.strip() if subject else ""
    for pattern in _MERGE_SUBJECT_RES:
        match = pattern.match(subject)
        if match:
            return int(match.group("number"))
    body_match = _MERGE_BODY_RE.search(body or "")
    if body_match:
        return int(body_match.group("number"))
    return None


def _extract_pr_number(subject):
    """Extracts the PR number from a squash-merge subject tail, if present."""
    pr_match = _PR_NUMBER_RE.search(subject)
    if pr_match:
        return int(pr_match.group("number"))
    return None
