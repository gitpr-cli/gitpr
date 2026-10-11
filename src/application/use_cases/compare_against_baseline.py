"""Use case: read the findings of one run against the baseline the repository keeps.

The comparison itself is domain work — ``classify_findings`` owns the statuses,
the layers and the precedence between them. What this module is, then, is the
name the application layer calls it by, and the place the "no baseline" rule is
written down: **it is never called without a manifest**. A run with no baseline
does not get a comparison whose answer is "everything is new"; it gets no
comparison at all, which is why the integration points in ``main.py`` ask the
gate before they ask this.

Nothing here writes. §5.9 of the spec is explicit: the file moves only through
``gitpr baseline create``/``update``, never as a side effect of a review.
"""

from typing import Sequence

from src.domain.baseline.baseline_comparator import ComparedFinding, classify_findings
from src.domain.baseline.baseline_types import BaselineManifest
from src.domain.baseline.suppression_policy import Overrides
from src.domain.finding.finding_types import NormalizedFinding


def compare_against_baseline(
    findings: Sequence[NormalizedFinding],
    baseline: BaselineManifest,
    *,
    overrides: Overrides | None = None,
    repo_path: str | None = None,
) -> list[ComparedFinding]:
    """Classifies every finding, in the order it arrived.

    *overrides* is the declarative layer already composed by the caller (the
    repository's ``baseline.overrides.yml`` plus whatever a Policy Pack adds in
    memory), and *repo_path* is the working tree an absolute path is trimmed
    against before it is fingerprinted. One compared finding per input finding:
    no status is ever dropped from the list, so the counts a report shows always
    add up to what the run actually found.
    """
    return classify_findings(
        findings, baseline, overrides=overrides, repo_path=repo_path
    )
