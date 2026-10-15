"""Tests for run_check use case."""

from unittest.mock import MagicMock, patch
import pytest

from src.application.use_cases.run_check import execute_check, resolve_diff_base
from src.domain.baseline.baseline_types import (
    BaselineEntry,
    BaselineManifest,
    BaselineStatus,
)
from src.domain.check.check_config import CheckConfig
from src.domain.check.check_types import (
    CheckOutputFormat,
    CheckSeverity,
)
from src.domain.finding.finding_types import NormalizedFinding
from src.infrastructure.baseline.local_baseline_repository import BaselineSnapshot


def test_resolve_diff_base_precedence():
    # 1. Configured base wins
    base, _ = resolve_diff_base("feature/branch", repo_path=".")
    assert base == "feature/branch"

    # 2. GITHUB_BASE_REF environment variable
    with patch.dict("os.environ", {"GITHUB_BASE_REF": "main"}):
        base, _ = resolve_diff_base(None, repo_path=".")
        assert base == "origin/main"


def test_execute_check_clean_diff():
    config = CheckConfig(no_ia=True)
    with patch("src.application.use_cases.run_check.get_check_diff", return_value=""):
        result = execute_check(config, repo_path=".")
        assert result.exit_code == 0
        assert len(result.findings) == 0
        assert result.incomplete is False


def test_execute_check_no_baseline_blocking_finding():
    config = CheckConfig(no_ia=True, fail_on=CheckSeverity.ERROR)
    finding_err = NormalizedFinding(
        severity="error",
        category="security",
        file_path="app.py",
        line_start=10,
        line_end=10,
        message="Hardcoded API key",
        source="linter",
        rule_id="SEC-01",
    )

    with patch("src.application.use_cases.run_check.get_check_diff", return_value="diff --git a/app.py"):
        with patch("src.application.use_cases.run_check.collect_linter_findings", return_value=[finding_err]):
            with patch("src.application.use_cases.run_check.read_baseline", return_value=BaselineSnapshot(path=".gitpr/baseline.json", exists=False)):
                result = execute_check(config, repo_path=".")
                assert result.exit_code == 1
                assert len(result.findings) == 1
                assert result.findings[0].is_countable is True
                assert result.findings[0].baseline_status is None


def test_execute_check_no_baseline_warning_passes_error_threshold():
    config = CheckConfig(no_ia=True, fail_on=CheckSeverity.ERROR)
    finding_warn = NormalizedFinding(
        severity="warning",
        category="style",
        file_path="app.py",
        line_start=10,
        line_end=10,
        message="Line too long",
        source="linter",
        rule_id="STYLE-01",
    )

    with patch("src.application.use_cases.run_check.get_check_diff", return_value="diff --git a/app.py"):
        with patch("src.application.use_cases.run_check.collect_linter_findings", return_value=[finding_warn]):
            with patch("src.application.use_cases.run_check.read_baseline", return_value=BaselineSnapshot(path=".gitpr/baseline.json", exists=False)):
                result = execute_check(config, repo_path=".")
                assert result.exit_code == 0
                assert len(result.findings) == 1


def test_execute_check_with_baseline_existing_finding_does_not_fail():
    config = CheckConfig(no_ia=True, fail_on=CheckSeverity.ERROR)
    finding_err = NormalizedFinding(
        severity="error",
        category="security",
        file_path="app.py",
        line_start=10,
        line_end=10,
        message="Hardcoded API key",
        source="linter",
        rule_id="SEC-01",
    )

    manifest = BaselineManifest(
        schema_version="1",
        fingerprint_version="1",
        policy_name=None,
        policy_version=None,
        gitpr_version="1.0.0",
        created_at="2026-10-01",
        updated_at="2026-10-01",
        checksum="abc",
        entries=[
            BaselineEntry(
                fingerprint="sha256:dummy",
                rule_id="SEC-01",
                category="security",
                file_path="app.py",
                line_start=10,
                line_end=10,
                severity="error",
                source="linter",
                status=BaselineStatus.EXISTING,
                low_confidence=False,
                first_seen_commit="abc",
                last_seen_commit="abc",
                first_seen_date="2026-10-01",
                last_seen_date="2026-10-01",
            )
        ],
    )

    from src.domain.baseline.baseline_comparator import ComparedFinding

    mock_compared = [
        ComparedFinding(
            fingerprint="sha256:dummy",
            identity="SEC-01",
            current_severity="error",
            baseline_status=BaselineStatus.EXISTING,
            is_blocking=False,
            reason="Already in baseline",
            finding=finding_err,
        )
    ]

    with patch("src.application.use_cases.run_check.get_check_diff", return_value="diff --git a/app.py"):
        with patch("src.application.use_cases.run_check.collect_linter_findings", return_value=[finding_err]):
            with patch("src.application.use_cases.run_check.read_baseline", return_value=BaselineSnapshot(path=".gitpr/baseline.json", exists=True, manifest=manifest)):
                with patch("src.application.use_cases.run_check.compare_against_baseline", return_value=mock_compared):
                    result = execute_check(config, repo_path=".")
                    # Finding exists in baseline -> not countable -> exit 0!
                    assert result.exit_code == 0
                    assert len(result.findings) == 1
                    assert result.findings[0].is_countable is False
                    assert result.findings[0].baseline_status == "existing"


def test_execute_check_corrupted_baseline_exits_2():
    config = CheckConfig(no_ia=True)
    # exists=True but manifest=None represents corrupted/checksum mismatch baseline
    bad_snapshot = BaselineSnapshot(
        path=".gitpr/baseline.json",
        exists=True,
        manifest=None,
        checksum_ok=False,
    )

    with patch("src.application.use_cases.run_check.get_check_diff", return_value="diff --git a/app.py"):
        with patch("src.application.use_cases.run_check.collect_linter_findings", return_value=[]):
            with patch("src.application.use_cases.run_check.read_baseline", return_value=bad_snapshot):
                result = execute_check(config, repo_path=".")
                assert result.exit_code == 2
                assert result.incomplete is True


def test_execute_check_invalid_policy_exits_2():
    config = CheckConfig(policy="non-existent@9.9.9")
    with patch("src.application.use_cases.run_check.load_pack_by_reference", side_effect=Exception("Pack not found")):
        result = execute_check(config, repo_path=".")
        assert result.exit_code == 2
        assert result.incomplete is True
        assert "non-existent@9.9.9" in result.warnings[0]


def test_execute_check_ai_failure_mid_run_exits_2():
    config = CheckConfig(no_ia=False)
    with patch("src.application.use_cases.run_check.get_check_diff", return_value="diff --git a/app.py"):
        with patch("src.application.use_cases.run_check.collect_linter_findings", return_value=[]):
            with patch("src.application.use_cases.run_check.get_api_key", return_value="test-api-key"):
                with patch("src.core.generate_pr_content", side_effect=RuntimeError("AI network timeout")):
                    result = execute_check(config, repo_path=".")
                    assert result.exit_code == 2
                    assert result.incomplete is True
                    assert "AI review failed" in result.warnings[0]
