"""The data contract of ``gitpr fix`` — the shapes every other module shares.

Nothing here touches the filesystem, the network or git: these are the values
that travel between the AI call, the safety classifier, the applier and the
history file. The other half of the contract, ``PatchSummary``, is owned by the
pure diff parser in ``src/diff_parser.py`` — import it from there.
"""
import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PatchSafety(str, Enum):
    """How much a patch may be trusted without a human reading it first.

    ``SAFE`` is the only class ``--all-safe`` will touch; ``REVIEW_REQUIRED``
    applies but needs a decision; ``EXPERIMENTAL`` never applies in a batch —
    only through an explicit ``--apply --force`` on that single patch.
    """
    SAFE = "safe"
    REVIEW_REQUIRED = "review_required"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class FindingRef:
    """One issue the review reported, as the normalizing AI call restated it.

    ``id`` is assigned by gitpr (``FIX-001``, ``FIX-002``, ...) in the order the
    findings come back, never by the model — the same review and the same
    working tree therefore yield the same ids, which is what makes
    ``gitpr fix FIX-001`` addressable.
    """
    id: str
    file_path: str
    line_start: int
    line_end: int
    severity: str
    category: str
    message: str


@dataclass(frozen=True)
class PatchProvenance:
    """Where a patch came from — the record kept for every applied patch."""
    finding_id: str
    ai_provider: str
    ai_model: str
    prompt_version: str
    generated_at: str
    gitpr_version: str


@dataclass(frozen=True)
class PatchCandidate:
    """A finding plus the patch that would fix it, already classified.

    ``diff_unified`` is a real unified diff — it parsed as one and passed
    ``git apply --check`` (or was marked ``EXPERIMENTAL`` for failing to).
    ``safety_reason`` is a code from ``patch_safety_classifier``, not a
    sentence: the display layer turns it into translated text.
    """
    finding: FindingRef
    diff_unified: str
    suggested_test: str
    confidence: str
    safety: PatchSafety
    safety_reason: str
    provenance: PatchProvenance

    @property
    def patch_id(self):
        """``FIX-001-1a2b3c4d`` — stable for a given finding and patch text.

        Derived rather than stored so a patch and its id can never disagree;
        the history file records it to make ``--rollback`` addressable.
        """
        digest = hashlib.md5(self.diff_unified.encode("utf-8")).hexdigest()
        return f"{self.finding.id}-{digest[:8]}"


@dataclass(frozen=True)
class ApplyFixResult:
    """What actually happened — returned by both the dry run and the real run.

    ``applied`` is False for a dry run, so callers can print one result shape
    for both. ``branch_created`` is the branch name when one was made (None
    otherwise) and ``dry_run_diff`` always carries the diff, applied or not.
    """
    applied: bool
    patch_id: str
    files_changed: tuple
    dry_run_diff: str
    warnings: tuple
    branch_created: Optional[str] = None
