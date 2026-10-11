"""Use case: orchestrates diff parsing, git history, test matching, and findings into risk scores."""

import os
from typing import Optional

from src.diff_parser import split_patch_sections, summarize_patch
from src.domain.policy import get_active_policy
from src.domain.policy.policy_resolver import risk_config_from_policy
from src.domain.risk.risk_calculator import calculate_file_risk, calculate_pull_request_risk
from src.domain.risk.risk_rules import (
    RiskConfig,
    load_risk_config,
    matches_pattern,
)
from src.domain.risk.risk_types import (
    FileRisk,
    PullRequestRisk,
    RiskEvidence,
    RiskSignal,
)
from src.infrastructure.git.risk_history_reader import read_file_git_history
from src.infrastructure.git.test_matcher import find_related_test_files, requires_tests
from src.domain.finding.finding_types import NormalizedFinding
from src.review.diff_source import DiffOrigin, DiffSource


def execute_calculate_risk(
    diff_source: DiffSource,
    *,
    repo_path: Optional[str] = None,
    config: Optional[RiskConfig] = None,
    target_file: Optional[str] = None,
    findings: Optional[list[NormalizedFinding]] = None,
    include_history: bool = True,
) -> PullRequestRisk:
    """Calculates risk score for all files in diff_source and aggregates them.

    Never raises unhandled exceptions. Degrades gracefully if history or
    findings are not available.

    The active policy pack refines the project's own risk settings — it adds
    critical paths and test patterns, and may raise a weight — so it is applied
    *on top of* what ``load_risk_config()`` produced rather than instead of it.
    With no pack active, ``risk_config_from_policy`` hands back the very object
    ``load_risk_config()`` returned, so this is the line the "no pack, no change"
    property rests on.
    """
    cfg = config or risk_config_from_policy(get_active_policy(), load_risk_config())
    warnings: list[str] = []

    sections = split_patch_sections(diff_source.content or "")
    if not sections:
        return calculate_pull_request_risk(files=[], config=cfg)

    all_changed_files = [s.path for s in sections]

    # Collect findings by file (normalized lowercase with forward slashes)
    findings_by_file: dict[str, list[NormalizedFinding]] = {}
    if findings:
        for f in findings:
            key = f.file_path.replace("\\", "/").lower().lstrip("./")
            findings_by_file.setdefault(key, []).append(f)

    file_risks: list[FileRisk] = []

    for section in sections:
        file_path = section.path
        normalized_path = file_path.replace("\\", "/").lower().lstrip("./")

        # Summarize this file's patch slice
        file_summary = summarize_patch(section.text)
        changed_lines = file_summary.added + file_summary.removed
        changed_hunks = file_summary.hunks

        evidence: list[RiskEvidence] = []
        signals_available: list[RiskSignal] = []
        file_warnings: list[str] = []

        # 1. Critical path / Security / Migration / Infrastructure
        for sig, patterns in cfg.critical_patterns.items():
            if any(matches_pattern(file_path, pat) for pat in patterns):
                points = cfg.weights.get(sig, 20.0)
                evidence.append(
                    RiskEvidence(
                        signal=sig,
                        points=points,
                        summary=f"Path matches critical pattern for {sig.value}",
                        details={"file": file_path, "signal": sig.value},
                        confidence="high",
                    )
                )
                signals_available.append(sig)

        # 2. Diff size
        large_diff_weight = cfg.weights.get(RiskSignal.LARGE_DIFF, 10.0)
        if changed_lines >= 300:
            evidence.append(
                RiskEvidence(
                    signal=RiskSignal.LARGE_DIFF,
                    points=min(20.0, large_diff_weight * 1.5),
                    summary=f"Very large diff ({changed_lines} lines changed)",
                    details={"changed_lines": changed_lines},
                    confidence="high",
                )
            )
            signals_available.append(RiskSignal.LARGE_DIFF)
        elif changed_lines >= 100:
            evidence.append(
                RiskEvidence(
                    signal=RiskSignal.LARGE_DIFF,
                    points=large_diff_weight,
                    summary=f"Large diff ({changed_lines} lines changed)",
                    details={"changed_lines": changed_lines},
                    confidence="high",
                )
            )
            signals_available.append(RiskSignal.LARGE_DIFF)
        elif changed_lines >= 50:
            evidence.append(
                RiskEvidence(
                    signal=RiskSignal.LARGE_DIFF,
                    points=round(large_diff_weight * 0.5, 1),
                    summary=f"Moderate diff ({changed_lines} lines changed)",
                    details={"changed_lines": changed_lines},
                    confidence="high",
                )
            )
            signals_available.append(RiskSignal.LARGE_DIFF)

        # 3. Test matching
        related_tests = find_related_test_files(
            file_path, all_changed_files, repo_path, cfg.test_patterns
        )
        if related_tests:
            pts = cfg.weights.get(RiskSignal.TEST_PRESENT, -10.0)
            evidence.append(
                RiskEvidence(
                    signal=RiskSignal.TEST_PRESENT,
                    points=pts,
                    summary=f"Related test modified: {os.path.basename(related_tests[0])}",
                    details={"related_test_files": related_tests},
                    confidence="high",
                )
            )
            signals_available.append(RiskSignal.TEST_PRESENT)
        elif requires_tests(file_path, cfg.test_patterns):
            pts = cfg.weights.get(RiskSignal.NO_TEST_CHANGE, 15.0)
            evidence.append(
                RiskEvidence(
                    signal=RiskSignal.NO_TEST_CHANGE,
                    points=pts,
                    summary="Executable production code without detected test changes in diff",
                    details={"file": file_path},
                    confidence="medium",
                )
            )
            signals_available.append(RiskSignal.NO_TEST_CHANGE)

        # 4. Git history signals
        if include_history and diff_source.origin == DiffOrigin.LOCAL:
            history = read_file_git_history(file_path, repo_path=repo_path)
            if not history.available:
                evidence.append(
                    RiskEvidence(
                        signal=RiskSignal.SIGNAL_UNAVAILABLE,
                        points=0.0,
                        summary=f"Git history unavailable for {file_path}",
                        confidence="low",
                    )
                )
                file_warnings.extend(history.warnings)
            elif history.is_new_file:
                evidence.append(
                    RiskEvidence(
                        signal=RiskSignal.NEW_FILE,
                        points=0.0,
                        summary="New file with no prior commit history",
                        confidence="high",
                    )
                )
                signals_available.append(RiskSignal.NEW_FILE)
            else:
                if history.revert_commits > 0:
                    pts = cfg.weights.get(RiskSignal.HISTORICAL_REVERTS, 10.0)
                    evidence.append(
                        RiskEvidence(
                            signal=RiskSignal.HISTORICAL_REVERTS,
                            points=pts,
                            summary=f"{history.revert_commits} historical revert(s) touching this file",
                            details={"revert_commits": history.revert_commits},
                            confidence="high",
                        )
                    )
                    signals_available.append(RiskSignal.HISTORICAL_REVERTS)

                if history.bug_commits > 0:
                    pts = cfg.weights.get(RiskSignal.HISTORICAL_BUGS, 20.0)
                    # Scale points if few bugs
                    points_allocated = pts if history.bug_commits >= 3 else round(pts * 0.5, 1)
                    evidence.append(
                        RiskEvidence(
                            signal=RiskSignal.HISTORICAL_BUGS,
                            points=points_allocated,
                            summary=f"{history.bug_commits} bug fix commit(s) in recent history",
                            details={"bug_commits": history.bug_commits},
                            confidence="high",
                        )
                    )
                    signals_available.append(RiskSignal.HISTORICAL_BUGS)

                if history.total_commits >= 20:
                    pts = cfg.weights.get(RiskSignal.HIGH_CHURN, 15.0)
                    evidence.append(
                        RiskEvidence(
                            signal=RiskSignal.HIGH_CHURN,
                            points=pts,
                            summary=f"High churn: {history.total_commits} commits in recent window",
                            details={"total_commits": history.total_commits},
                            confidence="medium",
                        )
                    )
                    signals_available.append(RiskSignal.HIGH_CHURN)
        elif diff_source.origin == DiffOrigin.REMOTE_PR:
            # Remote PR without full local checkout
            signals_available.append(RiskSignal.SIGNAL_UNAVAILABLE)

        # 5. Local Findings
        file_findings = findings_by_file.get(normalized_path, [])
        for f in file_findings:
            sev = (f.severity or "").lower()
            cat = (f.category or "").lower()
            msg = (f.message or "").lower()

            if sev == "error" and ("secret" in cat or "security" in cat or "blocker" in msg or "cve" in msg):
                pts = cfg.weights.get(RiskSignal.FINDING_BLOCKER, 25.0)
                evidence.append(
                    RiskEvidence(
                        signal=RiskSignal.FINDING_BLOCKER,
                        points=pts,
                        summary=f"Blocker finding: {f.message[:80]}",
                        details={"rule_id": f.rule_id, "source": f.source},
                        confidence="high",
                    )
                )
                signals_available.append(RiskSignal.FINDING_BLOCKER)
            elif sev == "error":
                pts = cfg.weights.get(RiskSignal.FINDING_CRITICAL, 15.0)
                evidence.append(
                    RiskEvidence(
                        signal=RiskSignal.FINDING_CRITICAL,
                        points=pts,
                        summary=f"Critical finding: {f.message[:80]}",
                        details={"rule_id": f.rule_id, "source": f.source},
                        confidence="high",
                    )
                )
                signals_available.append(RiskSignal.FINDING_CRITICAL)
            elif sev == "warning":
                pts = cfg.weights.get(RiskSignal.FINDING_WARNING, 3.0)
                evidence.append(
                    RiskEvidence(
                        signal=RiskSignal.FINDING_WARNING,
                        points=pts,
                        summary=f"Warning finding: {f.message[:80]}",
                        details={"rule_id": f.rule_id, "source": f.source},
                        confidence="medium",
                    )
                )
                signals_available.append(RiskSignal.FINDING_WARNING)

        file_risk = calculate_file_risk(
            file_path=file_path,
            changed_lines=changed_lines,
            changed_hunks=changed_hunks,
            evidence=evidence,
            related_test_files=related_tests,
            signals_available=signals_available,
            warnings=file_warnings,
            config=cfg,
        )
        file_risks.append(file_risk)

    pr_risk = calculate_pull_request_risk(file_risks, config=cfg, extra_warnings=warnings)

    # If target_file filter was requested:
    if target_file:
        norm_target = target_file.replace("\\", "/").lower().lstrip("./")
        matched_files = [
            f for f in file_risks
            if f.file_path.replace("\\", "/").lower().lstrip("./") == norm_target
            or f.file_path.lower().endswith(norm_target)
        ]
        if matched_files:
            return calculate_pull_request_risk(matched_files, config=cfg, extra_warnings=warnings)
        else:
            # File not in diff
            empty_file_risk = FileRisk(
                file_path=target_file,
                score=0.0,
                level=pr_risk.level,
                changed_lines=0,
                changed_hunks=0,
                evidence=[],
                warnings=[f"File '{target_file}' is not modified in the current diff."],
            )
            return calculate_pull_request_risk([empty_file_risk], config=cfg, extra_warnings=warnings)

    return pr_risk

