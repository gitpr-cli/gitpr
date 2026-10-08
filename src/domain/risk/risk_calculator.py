"""Pure calculator for file risk and aggregated pull request risk."""

from src.domain.risk.risk_rules import RiskConfig, resolve_risk_level
from src.domain.risk.risk_types import (
    FileRisk,
    PullRequestRisk,
    RiskEvidence,
    RiskLevel,
    RiskSignal,
)


def calculate_file_risk(
    file_path: str,
    changed_lines: int,
    changed_hunks: int,
    evidence: list[RiskEvidence],
    related_test_files: list[str] | None = None,
    signals_available: list[RiskSignal] | None = None,
    warnings: list[str] | None = None,
    config: RiskConfig | None = None,
) -> FileRisk:
    """Calculates pure deterministic risk score for a single file."""
    cfg = config or RiskConfig()
    total_points = sum(e.points for e in evidence)

    # Clamping between 0.0 and 100.0
    clamped_score = max(0.0, min(100.0, total_points))
    level = resolve_risk_level(clamped_score, cfg.thresholds)

    # Sort evidence by points descending
    sorted_evidence = sorted(evidence, key=lambda e: abs(e.points), reverse=True)

    return FileRisk(
        file_path=file_path,
        score=round(clamped_score, 1),
        level=level,
        changed_lines=max(0, changed_lines),
        changed_hunks=max(0, changed_hunks),
        evidence=sorted_evidence,
        related_test_files=list(related_test_files or []),
        signals_available=list(signals_available or []),
        warnings=list(warnings or []),
    )


def calculate_pull_request_risk(
    files: list[FileRisk],
    config: RiskConfig | None = None,
    extra_warnings: list[str] | None = None,
) -> PullRequestRisk:
    """Aggregates individual file risks into PullRequestRisk using the 50/30/20 formula."""
    cfg = config or RiskConfig()
    all_warnings = list(extra_warnings or [])

    if not files:
        return PullRequestRisk(
            score=0.0,
            level=RiskLevel.LOW,
            files=[],
            evidence=[],
            total_changed_files=0,
            total_changed_lines=0,
            tests_changed=False,
            critical_files=[],
            analysis_version=cfg.analysis_version,
            warnings=all_warnings,
        )

    total_changed_files = len(files)
    total_changed_lines = sum(f.changed_lines for f in files)

    # Check whether any test file was changed
    tests_changed = any(f.related_test_files for f in files) or any(
        "test" in f.file_path.lower() for f in files
    )

    # Component 1: Highest risk among files (50%)
    max_file_score = max(f.score for f in files)

    # Component 2: Weighted average by changed lines (30%)
    if total_changed_lines > 0:
        weighted_avg = sum(f.score * f.changed_lines for f in files) / total_changed_lines
    else:
        weighted_avg = sum(f.score for f in files) / total_changed_files

    # Component 3: Aggregated critical evidence (20%)
    all_evidence: list[RiskEvidence] = []
    seen_evidence_keys = set()
    has_blocker = False

    for f in files:
        all_warnings.extend(f.warnings)
        for ev in f.evidence:
            if ev.signal == RiskSignal.FINDING_BLOCKER:
                has_blocker = True
            key = (ev.signal, ev.summary)
            if key not in seen_evidence_keys:
                seen_evidence_keys.add(key)
                all_evidence.append(ev)

    # Score from critical evidences (signals >= 15 pts)
    critical_signals_points = sum(
        ev.points for ev in all_evidence if ev.points >= 15.0
    )
    critical_ev_score = min(100.0, max(0.0, critical_signals_points))

    # Aggregated calculation: 50% max + 30% weighted avg + 20% critical evidence
    raw_aggregated = (0.50 * max_file_score) + (0.30 * weighted_avg) + (0.20 * critical_ev_score)
    aggregated_score = max(0.0, min(100.0, raw_aggregated))

    resolved_level = resolve_risk_level(aggregated_score, cfg.thresholds)

    # Mandatory Rule 5: If any file has score >= 80, PR cannot be below HIGH
    if any(f.score >= 80.0 for f in files) and resolved_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
        resolved_level = RiskLevel.HIGH

    # Mandatory Rule 6: If there is a blocker or any file has score >= 90, PR is CRITICAL
    if has_blocker or any(f.score >= 90.0 for f in files):
        resolved_level = RiskLevel.CRITICAL

    critical_files = [f.file_path for f in files if f.score >= 50.0]

    # Deduplicate and sort aggregate evidence
    sorted_aggregate_evidence = sorted(
        all_evidence, key=lambda e: abs(e.points), reverse=True
    )

    # Deduplicate warnings
    unique_warnings = list(dict.fromkeys(all_warnings))

    return PullRequestRisk(
        score=round(aggregated_score, 1),
        level=resolved_level,
        files=sorted(files, key=lambda f: f.score, reverse=True),
        evidence=sorted_aggregate_evidence[:10],
        total_changed_files=total_changed_files,
        total_changed_lines=total_changed_lines,
        tests_changed=tests_changed,
        critical_files=critical_files,
        analysis_version=cfg.analysis_version,
        warnings=unique_warnings,
    )

