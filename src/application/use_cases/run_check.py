"""Use case: Unified CI check orchestrator (gitpr check).

Executes linter, external bridges, secret scanning, optional AI review,
risk scoring, and baseline classification, returning structured results
with deterministic exit codes (0, 1, 2).
"""

import os
import subprocess
import time
from typing import Any

from src.application.use_cases.calculate_risk import execute_calculate_risk
from src.application.use_cases.compare_against_baseline import compare_against_baseline
from src.application.use_cases.create_baseline import (
    ai_findings_from_record,
    collect_linter_findings,
)
from src.application.use_cases.resolve_effective_policy import resolve_effective_policy
from src.config import get_ai_provider, get_api_key
from src.core import SMART_EXCLUDES
from src.domain.baseline import (
    BaselineError,
    compute_fingerprint,
    normalize_path,
)
from src.domain.check.check_config import CheckConfig
from src.domain.check.check_types import (
    CheckFinding,
    CheckResult,
    CheckSeverity,
    CheckSummary,
    parse_severity,
)
from src.domain.finding.finding_types import NormalizedFinding
from src.domain.policy.policy_types import PolicyError
from src.i18n import __
from src.infrastructure.baseline.local_baseline_repository import (
    baseline_path,
    read_baseline,
)
from src.infrastructure.policy.policy_pack_loader import load_pack_by_reference
from src.review.diff_source import DiffOrigin, DiffSource
from src.updater import __version__


def resolve_diff_base(
    configured_base: str | None = None,
    repo_path: str | None = None,
) -> tuple[str | None, list[str]]:
    """Resolves the diff comparison base according to CI and repository context.

    Precedence:
    1. Explicit configured_base (e.g. from --base)
    2. GITHUB_BASE_REF env var (e.g. origin/${GITHUB_BASE_REF} in PR CI)
    3. origin/main (if remote branch exists)
    4. None (fallback to HEAD / local diff)
    """
    warnings: list[str] = []
    if configured_base:
        return configured_base, warnings

    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        target = f"origin/{github_base.strip()}"
        return target, warnings

    # Check if origin/main exists
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "origin/main"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_path or None,
        )
        if proc.returncode == 0:
            return "origin/main", warnings
    except OSError:
        pass

    return None, warnings


def get_check_diff(
    base_ref: str | None = None,
    repo_path: str | None = None,
) -> str:
    """Retrieves unified git diff against base_ref or HEAD with SMART_EXCLUDES."""
    cmd = ["git", "diff", "-U1", "-w", "-M", "-B"]
    if base_ref:
        cmd.append(base_ref)
    else:
        cmd.append("HEAD")
    cmd.append("--")
    cmd.extend(SMART_EXCLUDES)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_path or None,
        )
        if proc.returncode == 0:
            return proc.stdout or ""
    except OSError:
        pass
    return ""


def execute_check(
    config: CheckConfig,
    repo_path: str | None = None,
    ai_provider: Any = None,
) -> CheckResult:
    """Executes the unified CI check pipeline."""
    start_time = time.monotonic()
    warnings: list[str] = []

    def deadline_exceeded() -> bool:
        return (time.monotonic() - start_time) > config.timeout_seconds

    # 1. Policy resolution
    if config.policy:
        try:
            # Pinned policy requested explicitly
            load_pack_by_reference(config.policy, repo_path=repo_path)
        except (PolicyError, Exception) as exc:
            msg = f"Requested policy '{config.policy}' is invalid or could not be loaded: {exc}"
            return CheckResult(
                findings=[],
                exit_code=2,
                fail_on=config.fail_on,
                output_format=config.output_format,
                output_path=config.output_path,
                analysis_version=__version__,
                warnings=[msg],
                incomplete=True,
            )
    else:
        # Load active policy if configured
        try:
            resolve_effective_policy(repo_path=repo_path, strict=True, publish=True)
        except PolicyError as err:
            return CheckResult(
                findings=[],
                exit_code=2,
                fail_on=config.fail_on,
                output_format=config.output_format,
                output_path=config.output_path,
                analysis_version=__version__,
                warnings=[str(err.message)],
                incomplete=True,
            )

    # 2. Diff extraction
    base_ref, base_warnings = resolve_diff_base(config.base_ref, repo_path=repo_path)
    warnings.extend(base_warnings)
    diff_text = get_check_diff(base_ref, repo_path=repo_path)

    if not diff_text.strip():
        # Clean repository / no changes
        return CheckResult(
            findings=[],
            exit_code=0,
            fail_on=config.fail_on,
            output_format=config.output_format,
            output_path=config.output_path,
            analysis_version=__version__,
            warnings=warnings,
            incomplete=False,
            summary=CheckSummary(),
        )

    # 3. Linter, Secret Scanning & External Bridges
    raw_findings: list[NormalizedFinding] = []
    try:
        raw_findings.extend(collect_linter_findings(diff_text, repo_path=repo_path))
    except Exception as exc:
        warnings.append(f"Linter execution encountered an error: {exc}")

    if deadline_exceeded():
        return _build_timed_out_result(
            raw_findings, config, warnings, repo_path=repo_path
        )

    # 4. Preliminary Risk Scoring (to identify high-risk files)
    diff_source = DiffSource(
        content=diff_text,
        origin=DiffOrigin.LOCAL,
        identifier="check",
    )
    preliminary_risk = None
    try:
        preliminary_risk = execute_calculate_risk(
            diff_source,
            repo_path=repo_path,
            findings=raw_findings,
            include_history=False,
        )
    except Exception as exc:
        warnings.append(f"Risk calculation failed: {exc}")

    high_risk_files: set[str] = set()
    if preliminary_risk:
        for f in preliminary_risk.files:
            if getattr(f, "level", None) in ("high", "critical"):
                high_risk_files.add(f.path.replace("\\", "/").lower())

    # 5. Optional AI Review
    should_run_ai = not config.no_ia
    if should_run_ai and config.ia_only_high_risk and not high_risk_files:
        should_run_ai = False

    if should_run_ai:
        provider = ai_provider or get_ai_provider()
        api_key = get_api_key(provider)
        if not api_key and provider != "ollama":
            warnings.append(
                __(
                    "No API key configured for {provider} — skipping AI code review.",
                    provider=provider,
                )
            )
        else:
            try:
                from src.core import generate_pr_content

                ai_response = generate_pr_content(
                    "review", "review", diff_text, provider, store_diff=True
                )
                if ai_response:
                    ai_findings, ai_warnings = ai_findings_from_record(
                        {"response": ai_response}
                    )
                    warnings.extend(ai_warnings)
                    if config.ia_only_high_risk:
                        # Filter AI findings only to high risk files
                        ai_findings = [
                            f
                            for f in ai_findings
                            if f.file_path.replace("\\", "/").lower() in high_risk_files
                        ]
                    raw_findings.extend(ai_findings)
            except Exception as exc:
                # Per ADR-013 Decision 5: AI provider failure mid-run -> exit 2
                return CheckResult(
                    findings=[],
                    exit_code=2,
                    fail_on=config.fail_on,
                    output_format=config.output_format,
                    output_path=config.output_path,
                    analysis_version=__version__,
                    warnings=[f"AI review failed during execution: {exc}"],
                    incomplete=True,
                )

    if deadline_exceeded():
        return _build_timed_out_result(
            raw_findings, config, warnings, repo_path=repo_path
        )

    # 6. Baseline Resolution & Classification
    b_path = config.baseline_path or baseline_path(repo_path)
    snapshot = read_baseline(repo_path, b_path, require_checksum=True)

    if snapshot.exists and snapshot.manifest is None:
        # Corrupted / tampered baseline -> exit 2 per ADR-013 Decision 3
        return CheckResult(
            findings=[],
            exit_code=2,
            fail_on=config.fail_on,
            output_format=config.output_format,
            output_path=config.output_path,
            analysis_version=__version__,
            warnings=[
                __(
                    "The baseline at {path} could not be loaded (checksum mismatch or corrupt).",
                    path=snapshot.path,
                )
            ],
            incomplete=True,
        )

    check_findings: list[CheckFinding] = []
    file_risk_map: dict[str, float] = {}
    if preliminary_risk:
        for fr in preliminary_risk.files:
            file_risk_map[fr.path.replace("\\", "/").lower()] = fr.score

    if snapshot.manifest is not None:
        # Classify findings against baseline
        try:
            compared = compare_against_baseline(
                raw_findings, snapshot.manifest, repo_path=repo_path
            )
            for c in compared:
                norm_path = normalize_path(c.finding.file_path, repo_path)
                risk_val = file_risk_map.get(norm_path.lower())
                try:
                    sev = parse_severity(c.finding.severity)
                except ValueError:
                    sev = CheckSeverity.WARNING

                check_findings.append(
                    CheckFinding(
                        fingerprint=c.fingerprint,
                        rule_id=c.finding.rule_id or f"CATEGORY-{c.finding.category.upper()}",
                        category=c.finding.category,
                        file_path=norm_path,
                        line_start=c.finding.line_start,
                        line_end=c.finding.line_end,
                        severity=sev,
                        source=c.finding.source,
                        message=c.finding.message,
                        baseline_status=c.baseline_status.value if hasattr(c.baseline_status, "value") else str(c.baseline_status),
                        risk_score=risk_val,
                        provenance={"source": c.finding.source},
                    )
                )
        except BaselineError as b_err:
            return CheckResult(
                findings=[],
                exit_code=2,
                fail_on=config.fail_on,
                output_format=config.output_format,
                output_path=config.output_path,
                analysis_version=__version__,
                warnings=[str(b_err)],
                incomplete=True,
            )
    else:
        # No baseline -> baseline_status = None, every finding is countable
        for f in raw_findings:
            norm_path = normalize_path(f.file_path, repo_path)
            risk_val = file_risk_map.get(norm_path.lower())
            fp = compute_fingerprint(f, repo_path)
            try:
                sev = parse_severity(f.severity)
            except ValueError:
                sev = CheckSeverity.WARNING

            check_findings.append(
                CheckFinding(
                    fingerprint=fp,
                    rule_id=f.rule_id or f"CATEGORY-{f.category.upper()}",
                    category=f.category,
                    file_path=norm_path,
                    line_start=f.line_start,
                    line_end=f.line_end,
                    severity=sev,
                    source=f.source,
                    message=f.message,
                    baseline_status=None,
                    risk_score=risk_val,
                    provenance={"source": f.source},
                )
            )

    # 7. Final Risk Summary
    risk_summary_dict = None
    if preliminary_risk:
        level_val = (
            preliminary_risk.level.value
            if hasattr(preliminary_risk.level, "value")
            else str(preliminary_risk.level)
        )
        risk_summary_dict = {
            "score": round(preliminary_risk.score, 1),
            "level": level_val,
            "files_count": len(preliminary_risk.files),
        }

    # 8. Evaluate Failure Threshold
    summary = CheckSummary.from_findings(check_findings)
    blocking_findings = [
        cf
        for cf in check_findings
        if cf.is_countable and cf.severity.meets_threshold(config.fail_on)
    ]

    exit_code = 1 if blocking_findings else 0

    return CheckResult(
        findings=check_findings,
        exit_code=exit_code,
        fail_on=config.fail_on,
        output_format=config.output_format,
        output_path=config.output_path,
        analysis_version=__version__,
        warnings=warnings,
        incomplete=False,
        risk_summary=risk_summary_dict,
        summary=summary,
    )


def _build_timed_out_result(
    findings: list[NormalizedFinding],
    config: CheckConfig,
    warnings: list[str],
    repo_path: str | None = None,
) -> CheckResult:
    warnings.append(
        __(
            "Execution exceeded deadline of {timeout}s.",
            timeout=config.timeout_seconds,
        )
    )
    converted: list[CheckFinding] = []
    for f in findings:
        fp = compute_fingerprint(f, repo_path)
        try:
            sev = parse_severity(f.severity)
        except ValueError:
            sev = CheckSeverity.WARNING
        converted.append(
            CheckFinding(
                fingerprint=fp,
                rule_id=f.rule_id or f"CATEGORY-{f.category.upper()}",
                category=f.category,
                file_path=normalize_path(f.file_path, repo_path),
                line_start=f.line_start,
                line_end=f.line_end,
                severity=sev,
                source=f.source,
                message=f.message,
                baseline_status=None,
            )
        )
    return CheckResult(
        findings=converted,
        exit_code=2,
        fail_on=config.fail_on,
        output_format=config.output_format,
        output_path=config.output_path,
        analysis_version=__version__,
        warnings=warnings,
        incomplete=True,
    )
