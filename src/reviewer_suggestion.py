"""Pure reviewer suggestion logic: hit aggregation, scoring and ranking.

This module has no git, network or i18n dependency — it consumes blame hits
and produces an ordered list of reviewer candidates. All I/O (blame, diffs)
happens in the orchestration layer (src/suggest_reviewers.py).
"""
from dataclasses import dataclass, field
from datetime import date

# Default scoring weights: how much each signal contributes to the score.
WEIGHTS_DEFAULT = {"lines": 0.5, "files": 0.3, "recency": 0.2}

# Recency half-life in days: a touch N days ago scores 1 / (1 + N / HALFLIFE).
RECENCY_HALFLIFE_DAYS = 90.0

# Well-known bot email addresses (in addition to the [bot] name heuristic).
DEFAULT_BOT_EMAILS = frozenset(
    {
        "dependabot@github.com",
        "github-actions@github.com",
        "actions@github.com",
    }
)

# Fallback identity reported when git config is not available (see cache.py).
_UNKNOWN_IDENTITY = "unknown"


@dataclass
class BlameHit:
    """One diff line attributed to an author via git blame (working tree)."""

    file_path: str
    line_number: int
    author_name: str
    author_email: str
    commit_hash: str
    commit_date: str  # ISO 8601 date (YYYY-MM-DD)


@dataclass
class ReviewerCandidate:
    """An aggregated author with the signals used for scoring."""

    author_name: str
    author_email: str
    touched_lines: int = 0  # diff lines this author "owns" via blame
    touched_files: int = 0  # distinct files of the diff where they appear
    last_touch_date: str = ""  # most recent touch, ISO 8601 date
    score: float = 0.0  # final normalized score (0.0 to 1.0)


@dataclass
class ReviewerSuggestionResult:
    """Ordered reviewer suggestions plus non-fatal warnings."""

    candidates: list = field(default_factory=list)  # list[ReviewerCandidate]
    excluded_pr_author: bool = False
    warnings: list = field(default_factory=list)  # list[str]


def normalize_email(email):
    """Normalize an email for identity comparison (case-insensitive)."""
    return (email or "").strip().lower()


def is_bot(author_name, author_email):
    """True for known bot identities.

    Heuristic: name ending in '[bot]' (GitHub convention), an email local
    part ending in '[bot]', or a well-known bot address. 'users.noreply.
    github.com' addresses are NOT bots — that is the standard private email
    used by real GitHub users.
    """
    name = (author_name or "").strip()
    if name.lower().endswith("[bot]"):
        return True
    email = normalize_email(author_email)
    local_part = email.split("@", 1)[0]
    if local_part.endswith("[bot]"):
        return True
    return email in DEFAULT_BOT_EMAILS


def _identity_key(author_name, author_email):
    """Grouping key: normalized email, falling back to the folded name."""
    email = normalize_email(author_email)
    if email and email != _UNKNOWN_IDENTITY:
        return email
    return f"name:{author_name.strip().lower()}" if author_name else ""


def aggregate_hits(hits):
    """Group BlameHit items per author identity (email is the primary key).

    Returns the aggregated list (not yet scored or filtered). When one
    identity appears with several names, the most recent hit's name wins.
    """
    aggregates = {}
    for hit in hits:
        key = _identity_key(hit.author_name, hit.author_email)
        if not key:
            continue
        agg = aggregates.get(key)
        if agg is None:
            agg = {
                "name": hit.author_name,
                "email": (hit.author_email or "").strip(),
                "files": set(),
                "lines": 0,
                "last": "",
            }
            aggregates[key] = agg
        agg["files"].add(hit.file_path)
        agg["lines"] += 1
        if hit.commit_date and hit.commit_date > agg["last"]:
            agg["last"] = hit.commit_date
            agg["name"] = hit.author_name
            agg["email"] = (hit.author_email or "").strip()
    candidates = []
    for agg in aggregates.values():
        candidates.append(
            ReviewerCandidate(
                author_name=agg["name"],
                author_email=agg["email"],
                touched_lines=agg["lines"],
                touched_files=len(agg["files"]),
                last_touch_date=agg["last"],
            )
        )
    return candidates


def _age_days(last_touch_date, today):
    """Days between the last touch and today; invalid dates age forever."""
    try:
        last = date.fromisoformat(last_touch_date)
    except (TypeError, ValueError):
        return float("inf")
    return (today - last).days


def compute_scores(
    candidates,
    total_lines,
    total_files,
    weights=None,
    halflife_days=RECENCY_HALFLIFE_DAYS,
    today=None,
):
    """Set the score of each candidate and return the same list.

    score = lines_weight * touched_lines/total_lines
          + files_weight * touched_files/total_files
          + recency_weight * 1/(1 + age_days/halflife_days)
    """
    weights = dict(WEIGHTS_DEFAULT if weights is None else weights)
    if today is None:
        today = date.today()
    for candidate in candidates:
        lines = candidate.touched_lines / max(1, total_lines)
        files = candidate.touched_files / max(1, total_files)
        age = _age_days(candidate.last_touch_date, today)
        recency = 0.0 if age == float("inf") else 1.0 / (1.0 + age / halflife_days)
        candidate.score = (
            weights.get("lines", 0.5) * lines
            + weights.get("files", 0.3) * files
            + weights.get("recency", 0.2) * recency
        )
    return candidates


def rank_reviewers(
    hits,
    *,
    pr_author_email="",
    pr_author_name=None,
    excluded_authors=(),
    top_n=3,
    weights=None,
    halflife_days=RECENCY_HALFLIFE_DAYS,
    today=None,
):
    """Rank reviewer candidates from blame hits. Never raises.

    Excludes the PR author and bots/extra excluded identities, scores the
    rest, sorts by score descending and truncates to top_n.
    """
    result = ReviewerSuggestionResult()
    if not hits:
        return result

    candidates = aggregate_hits(hits)
    if not candidates:
        return result

    # Denominator totals come from every hit (pre-exclusion), so lines
    # touched by the author or by bots still count as diff "ownership".
    total_lines = sum(c.touched_lines for c in candidates)
    total_files = len({h.file_path for h in hits})

    author_email = normalize_email(pr_author_email)
    author_name = (pr_author_name or "").strip().lower()
    excluded = [normalize_email(e) for e in (excluded_authors or ())]
    excluded_names = {(e or "").strip().lower() for e in (excluded_authors or ())}
    identity_known = author_email not in ("", _UNKNOWN_IDENTITY) or author_name not in (
        "",
        _UNKNOWN_IDENTITY,
    )

    kept = []
    for candidate in candidates:
        email = normalize_email(candidate.author_email)
        name = (candidate.author_name or "").strip().lower()
        if (
            identity_known
            and (
                (author_email and email == author_email)
                or (author_name and name == author_name)
            )
        ):
            result.excluded_pr_author = True
            continue
        if is_bot(candidate.author_name, candidate.author_email):
            continue
        if email in excluded or (name and name in excluded_names):
            continue
        kept.append(candidate)

    kept = compute_scores(
        kept,
        total_lines,
        total_files,
        weights=weights,
        halflife_days=halflife_days,
        today=today,
    )
    kept.sort(key=lambda c: (c.score, c.touched_lines), reverse=True)
    if top_n and top_n > 0:
        kept = kept[:top_n]
    result.candidates = kept
    return result
