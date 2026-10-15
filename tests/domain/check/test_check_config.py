"""Tests for check_config loading and precedence."""

from src.domain.check.check_config import (
    DEFAULT_FAIL_ON,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TIMEOUT_SECONDS,
    CheckConfig,
    load_check_config,
)
from src.domain.check.check_types import CheckOutputFormat, CheckSeverity


def test_load_check_config_defaults():
    cfg = load_check_config({}, environ={})
    assert cfg.base_ref is None
    assert cfg.output_format == DEFAULT_OUTPUT_FORMAT
    assert cfg.output_path is None
    assert cfg.fail_on == DEFAULT_FAIL_ON
    assert cfg.no_ia is False
    assert cfg.ia_only_high_risk is False
    assert cfg.baseline_path is None
    assert cfg.policy is None
    assert cfg.timeout_seconds == DEFAULT_TIMEOUT_SECONDS


def test_load_check_config_from_environ():
    env = {
        "GITPR_CHECK_BASE": "origin/develop",
        "GITPR_CHECK_FORMAT": "junit",
        "GITPR_CHECK_OUTPUT": "results.xml",
        "GITPR_CHECK_FAIL_ON": "warning",
        "GITPR_CHECK_NO_IA": "true",
        "GITPR_CHECK_IA_ONLY_HIGH_RISK": "1",
        "GITPR_CHECK_BASELINE_PATH": ".gitpr/custom-baseline.json",
        "GITPR_CHECK_POLICY": "strict@1.0.0",
        "GITPR_CHECK_TIMEOUT_SECONDS": "180",
    }
    cfg = load_check_config({}, environ=env)
    assert cfg.base_ref == "origin/develop"
    assert cfg.output_format == CheckOutputFormat.JUNIT
    assert cfg.output_path == "results.xml"
    assert cfg.fail_on == CheckSeverity.WARNING
    assert cfg.no_ia is True
    assert cfg.ia_only_high_risk is True
    assert cfg.baseline_path == ".gitpr/custom-baseline.json"
    assert cfg.policy == "strict@1.0.0"
    assert cfg.timeout_seconds == 180


def test_load_check_config_cli_overrides_environ():
    env = {
        "GITPR_CHECK_BASE": "origin/develop",
        "GITPR_CHECK_FORMAT": "junit",
        "GITPR_CHECK_FAIL_ON": "warning",
        "GITPR_CHECK_NO_IA": "false",
        "GITPR_CHECK_TIMEOUT_SECONDS": "180",
    }
    cli = {
        "base": "origin/main",
        "format": "sarif",
        "fail_on": "critical",  # alias for error
        "no_ia": True,
        "timeout_seconds": 60,
    }
    cfg = load_check_config(cli, environ=env)
    assert cfg.base_ref == "origin/main"
    assert cfg.output_format == CheckOutputFormat.SARIF
    assert cfg.fail_on == CheckSeverity.ERROR
    assert cfg.no_ia is True
    assert cfg.timeout_seconds == 60
