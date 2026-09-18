"""Where a review diff came from — the value contract for both review flows.

Pure data, no I/O, no imports from the review engine. The engine
(``core.generate_pr_content``) never sees this type: it takes the diff as a
plain string and has always been origin-agnostic, so threading a DiffSource
through it would add a layer without buying anything. What the type is for is
the *caller* — it carries the provenance the engine cannot express (which PR,
which branches) and decides the cache scope that keeps a remote review from
answering a local one.

See docs/plans/ADR-005-review-pr-subcommand.md for why this stayed a contract
instead of becoming an engine parameter.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.infrastructure.scm.base import RepoRef


class DiffOrigin(str, Enum):
    """Which side of the tool produced a review diff."""

    LOCAL = "local"
    REMOTE_PR = "remote_pr"


@dataclass(frozen=True)
class DiffSource:
    """A normalized diff plus the provenance of the review that consumes it.

    ``content`` is a unified diff ready for the engine — already filtered by the
    smart excludes when it came from a forge, since those exclusions are a git
    pathspec and a remote diff never passes through git. ``identifier`` names
    the revision the review is about ("head" for the local tree, "pr-123" for a
    pull request) and is what the cache scope is built from.

    ``pr_number``, ``repo_ref``, ``base_branch`` and ``head_branch`` are filled
    only for REMOTE_PR; the local flow leaves them None because the working tree
    has no PR behind it.
    """

    origin: DiffOrigin
    content: str
    identifier: str
    pr_number: Optional[int] = None
    repo_ref: Optional[RepoRef] = None
    base_branch: Optional[str] = None
    head_branch: Optional[str] = None

    @property
    def cache_scope(self) -> str:
        """Suffix appended to the cache key so origins never collide.

        Empty for LOCAL on purpose: concatenating nothing leaves the MD5 of
        every existing local review byte-for-byte identical, so the switch to
        DiffSource invalidates nobody's cache. A remote review is scoped by
        identifier, so reviewing PR 42 and reviewing the local tree can never
        return each other's answer even when the diff text matches.
        """
        if self.origin == DiffOrigin.LOCAL:
            return ""
        return f"::diff-source::{self.identifier}"

    @property
    def is_remote(self) -> bool:
        """True when the diff came from a forge rather than the working tree."""
        return self.origin == DiffOrigin.REMOTE_PR
