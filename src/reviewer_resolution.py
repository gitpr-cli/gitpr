"""Resolve reviewer identities (name, email or login) to forge logins.

The reviewer field of the PR publisher shows people that came out of ``git
blame`` — names and emails, not necessarily forge handles. This module turns
those into logins the forge will actually attach, and it does so in two
moments:

  - resolve_candidates: before the TUI opens, so the field can be prefilled
    with handles and the hint can flag the people that have no account.
  - resolve_typed_reviewers: at attach time, for whatever the user typed or
    edited the field into.

The heavy lifting is delegated to the provider (duck-typed through getattr, so
fakes and forges without the reviewer API keep working). Nothing here raises:
an identity that cannot be resolved becomes an entry in ``dropped`` with the
reason, and is never submitted as-is.
"""
from dataclasses import dataclass, field

from src.i18n import __
from src.reviewer_suggestion import identity_key, normalize_identity


@dataclass
class ResolvedReviewer:
    """A suggested author mapped to a forge account (login may be empty)."""

    name: str
    email: str
    login: str = ""

    @property
    def key(self) -> str:
        """Identity key of the underlying candidate (see identity_key)."""
        return identity_key(self.name, self.email)


@dataclass
class ResolutionOutcome:
    """Logins to submit, plus the values that could not be resolved."""

    logins: list = field(default_factory=list)  # list[str], ready to submit
    dropped: list = field(default_factory=list)  # list[tuple[str, str]] value, warning


def _candidate_login(candidate, provider, repo) -> str:
    """Login for one candidate: the commit author first, the email second.

    The commit lookup is the reliable path — it works for corporate addresses
    that the user search API cannot see. The email fallback covers commits the
    forge does not know (never pushed, shallow clone) and any failure of the
    first lookup, so one bad step never costs the other.
    """
    get_commit_author_login = getattr(provider, "get_commit_author_login", None)
    sha = getattr(candidate, "last_commit_hash", "")
    if get_commit_author_login and sha:
        try:
            login = get_commit_author_login(repo, sha)
        except Exception:
            login = None
        if login:
            return login
    email_to_handle = getattr(provider, "email_to_handle", None)
    if email_to_handle:
        try:
            login = email_to_handle(candidate.author_email)
        except Exception:
            login = None
        if login:
            return login
    return ""


def resolve_candidates(candidates, provider, repo) -> list:
    """Resolve the login of every candidate. Never raises.

    Returns a list of ResolvedReviewer in the same order; ``login`` is empty
    for the people the forge could not map to an account.
    """
    resolutions = []
    for candidate in candidates or ():
        try:
            login = _candidate_login(candidate, provider, repo)
        except Exception:
            login = ""
        resolutions.append(
            ResolvedReviewer(
                name=candidate.author_name,
                email=candidate.author_email,
                login=login,
            )
        )
    return resolutions


def match_candidate(value, resolutions):
    """The resolved candidate whose login, name or email equals ``value``.

    Exact match after normalization (strip + casefold) — a partial name never
    matches, which is what keeps "Eduarda" from being taken for "Eduarda Leal".
    """
    target = normalize_identity(value)
    if not target:
        return None
    for resolution in resolutions or ():
        for identity in (resolution.login, resolution.name, resolution.email):
            if identity and normalize_identity(identity) == target:
                return resolution
    return None


def resolve_typed_reviewers(
    values, *, resolutions=(), known_logins=(), provider=None, repo=None
) -> ResolutionOutcome:
    """Turn the values of the reviewer field into submittable logins.

    Ladder per value: an already-resolved handle (no request), an exact match
    on a suggested person, an email address, or a login looked up on the
    forge. A value that resolves to nothing is dropped with a warning instead
    of being sent verbatim — the forge answers 201 to a nonexistent login and
    attaches nobody, so sending it would fail silently.
    """
    outcome = ResolutionOutcome()
    known = {normalize_identity(login): login for login in (known_logins or ()) if login}
    seen = set()

    for raw in values or ():
        value = (raw or "").strip()
        if not value:
            continue
        normalized = normalize_identity(value)

        login = known.get(normalized)
        if not login:
            matched = match_candidate(value, resolutions)
            if matched is not None:
                login = matched.login
        if not login and "@" in value:
            email_to_handle = getattr(provider, "email_to_handle", None)
            login = email_to_handle(value) if email_to_handle else ""
        if not login:
            get_user_login = getattr(provider, "get_user_login", None)
            if get_user_login:
                try:
                    login = get_user_login(value) or ""
                except Exception:
                    login = ""

        if not login:
            outcome.dropped.append(
                (value, __("⚠️ {value}: no GitHub account found.", value=value))
            )
            continue
        if normalize_identity(login) in seen:
            continue
        seen.add(normalize_identity(login))
        outcome.logins.append(login)

    return outcome
