"""The stable identity of a finding, so a baseline can survive across runs.

A finding is identified by what produced it (rule identity, category, source)
and by where it sits (normalized path, line range, digest of the offending
line). Everything volatile is deliberately left out: the message is prose that
a reworded rule would change, the provider and model belong to whoever ran the
analysis, and the branch belongs to the checkout. Two runs over the same
revision produce the same fingerprint on any machine.

Only the *digest* of the offending line takes part, never the line itself. The
baseline is committed to Git, and GitPR never persists code or a secret — a
finding on a hardcoded key must not put the key in `.gitpr/baseline.json`. The
digest covers the whitespace-collapsed line, so reformatting alone does not
resurrect an old finding.

Line numbers are part of the payload on purpose. An edit above a finding shifts
it down and it reads as new; a false `new` is visible and fixable with
`gitpr baseline update`, while a false `existing` would let a real secret slip
through. The bias is the point.

`FINGERPRINT_VERSION` is the first line of the payload, so bumping it changes
every fingerprint at once and the migration is one recorded decision — the
manifest carries the version it was written with.
"""

from src.domain.finding.finding_types import NormalizedFinding
from src.domain.policy.policy_checksum import checksum_bytes

FINGERPRINT_VERSION = "1"

_SEPARATOR = "\n"
_UNKNOWN_CATEGORY = "unknown"


def normalize_path(file_path: str, repo_path: str | None = None) -> str:
    """Normalizes a path to the repo-relative, forward-slash, lowercase key.

    Where the repository lives on disk must not change a fingerprint, so an
    absolute path is trimmed against *repo_path* when it is given. A path that
    is not under the repository keeps only its suffix, which is the best that a
    pure function can do without the working tree — callers that know the root
    should pass it.
    """
    path = (file_path or "").strip().replace("\\", "/")
    if repo_path:
        root = repo_path.strip().replace("\\", "/").rstrip("/")
        if root and path.lower().startswith(root.lower() + "/"):
            path = path[len(root) + 1:]
    while path.startswith("./"):
        path = path[2:]
    return path.lstrip("/").lower()


def normalize_line_text(text: str) -> str:
    """Collapses every run of whitespace, so reformatting alone is not a change."""
    return " ".join((text or "").split())


def snippet_hash(text: str | None) -> str:
    """Digest of a code line — the line itself never reaches the baseline."""
    if text is None:
        return ""
    return "sha256:" + checksum_bytes(normalize_line_text(text).encode("utf-8"))


def rule_identity(rule_id: str | None, category: str | None = None) -> str:
    """The rule a finding belongs to: its declared id, or the category it fell back to.

    The id is kept as declared, case included, because it *is* the rule's name
    in the linter's YAML — two ids that differ only by case are two rules.
    """
    rule = (rule_id or "").strip()
    if rule:
        return rule
    return "category:" + ((category or "").strip().lower() or _UNKNOWN_CATEGORY)


def is_low_confidence(finding: NormalizedFinding) -> bool:
    """Whether the identity fell back to the category — true for every AI finding."""
    return not (finding.rule_id or "").strip()


def fingerprint_payload(finding: NormalizedFinding, repo_path: str | None = None) -> str:
    """The exact text the digest covers: one field per line, in this order.

    Never in here: message, timestamp, provider or model, branch, absolute path.
    """
    return _SEPARATOR.join([
        FINGERPRINT_VERSION,
        rule_identity(finding.rule_id, finding.category),
        (finding.category or "").strip().lower(),
        normalize_path(finding.file_path, repo_path),
        (finding.source or "").strip().lower(),
        str(finding.line_start),
        str(finding.line_end),
        finding.snippet_hash or "",
    ])


def compute_fingerprint(finding: NormalizedFinding, repo_path: str | None = None) -> str:
    """The finding's stable id, as persisted in `.gitpr/baseline.json`."""
    payload = fingerprint_payload(finding, repo_path)
    return "sha256:" + checksum_bytes(payload.encode("utf-8"))
