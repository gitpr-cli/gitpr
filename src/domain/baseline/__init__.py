"""Domain package for the technical baseline and its auditable suppressions.

Modules:

- ``baseline_fingerprint`` — the stable identity of a finding;
- ``baseline_types`` — the value contracts (status, scope, entry, manifest);
- ``baseline_manifest`` — reading, validating and checksumming
  ``.gitpr/baseline.json``;
- ``baseline_comparator`` — what this run found, read against the baseline;
- ``suppression_policy`` — auditable suppressions, accepted debt and the layers
  they arrive in.

See docs/plans/glossary-baseline.md for the vocabulary and
docs/plans/ADR-012-baseline-suppressions.md for the decisions behind the shape.
"""

from src.domain.baseline.baseline_comparator import (
    ComparedFinding,
    classify_findings,
    entries_resolved_by,
    status_counts,
)
from src.domain.baseline.baseline_fingerprint import (
    FINGERPRINT_VERSION,
    compute_fingerprint,
    fingerprint_payload,
    is_low_confidence,
    normalize_line_text,
    normalize_path,
    rule_identity,
    snippet_hash,
)
from src.domain.baseline.baseline_manifest import (
    SCHEMA_VERSION,
    canonical_json,
    checksum_matches,
    dump_manifest,
    manifest_checksum,
    parse_manifest,
    resolve_fingerprint_prefix,
    validate_manifest_dict,
)
from src.domain.baseline.baseline_types import (
    PERSISTED_STATUSES,
    SCOPE_PRECEDENCE,
    BaselineEntry,
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    FindingFingerprint,
    SuppressionScope,
)
from src.domain.baseline.suppression_policy import (
    ORIGIN_ENTRY,
    ORIGIN_LOCAL,
    AcceptedDebt,
    AppliedSuppression,
    Overrides,
    Suppression,
    apply_overrides,
    entry_debt,
    entry_suppression,
    match_debt,
    match_suppression,
    overdue_debt,
    overdue_decisions,
    parse_overrides,
    status_of_entry,
    validate_debt,
    validate_suppression,
)

# The baseline the current process resolved, published the same way the active
# policy is: read once at startup, consulted by the review/linter/risk
# integration points, and rebindable so a test can install one without a disk.
ACTIVE_BASELINE: BaselineManifest | None = None


def set_active_baseline(manifest: BaselineManifest | None) -> None:
    """Publishes *manifest* as the process-wide baseline.

    Passing None means "this run has no baseline", which every consumer reads as
    "behave exactly as before": no file, no comparison, no extra output.
    """
    global ACTIVE_BASELINE
    ACTIVE_BASELINE = manifest


def get_active_baseline() -> BaselineManifest | None:
    """The baseline the current process runs against, or None."""
    return ACTIVE_BASELINE


__all__ = [
    "ACTIVE_BASELINE",
    "FINGERPRINT_VERSION",
    "ORIGIN_ENTRY",
    "ORIGIN_LOCAL",
    "PERSISTED_STATUSES",
    "SCOPE_PRECEDENCE",
    "SCHEMA_VERSION",
    "AcceptedDebt",
    "AppliedSuppression",
    "BaselineEntry",
    "BaselineError",
    "BaselineManifest",
    "BaselineStatus",
    "ComparedFinding",
    "FindingFingerprint",
    "Overrides",
    "Suppression",
    "SuppressionScope",
    "apply_overrides",
    "canonical_json",
    "checksum_matches",
    "classify_findings",
    "compute_fingerprint",
    "dump_manifest",
    "entries_resolved_by",
    "entry_debt",
    "entry_suppression",
    "fingerprint_payload",
    "get_active_baseline",
    "is_low_confidence",
    "manifest_checksum",
    "match_debt",
    "match_suppression",
    "normalize_line_text",
    "normalize_path",
    "overdue_debt",
    "overdue_decisions",
    "parse_manifest",
    "parse_overrides",
    "resolve_fingerprint_prefix",
    "rule_identity",
    "set_active_baseline",
    "snippet_hash",
    "status_counts",
    "status_of_entry",
    "validate_debt",
    "validate_manifest_dict",
    "validate_suppression",
]
