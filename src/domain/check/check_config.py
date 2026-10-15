"""Configuration loader and settings model for gitpr check."""

import os
from dataclasses import dataclass
from typing import Any, Mapping

from src.domain.check.check_types import (
    CheckOutputFormat,
    CheckSeverity,
    parse_output_format,
    parse_severity,
)

DEFAULT_OUTPUT_FORMAT = CheckOutputFormat.SARIF
DEFAULT_FAIL_ON = CheckSeverity.ERROR
DEFAULT_TIMEOUT_SECONDS = 300


@dataclass
class CheckConfig:
    """Consolidated configuration for a check run."""

    base_ref: str | None = None
    output_format: CheckOutputFormat = DEFAULT_OUTPUT_FORMAT
    output_path: str | None = None
    fail_on: CheckSeverity = DEFAULT_FAIL_ON
    no_ia: bool = False
    ia_only_high_risk: bool = False
    baseline_path: str | None = None
    policy: str | None = None
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def load_check_config(
    cli_args: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> CheckConfig:
    """Builds a CheckConfig with precedence: CLI flags > environment variables > defaults."""
    env = environ if environ is not None else os.environ
    args = cli_args or {}

    # 1. Base ref
    base_ref = args.get("base") or args.get("base_ref")
    if not base_ref:
        base_ref = env.get("GITPR_CHECK_BASE") or None

    # 2. Output format
    raw_format = args.get("format") or args.get("output_format")
    if not raw_format:
        raw_format = env.get("GITPR_CHECK_FORMAT")
    output_format = (
        parse_output_format(raw_format) if raw_format else DEFAULT_OUTPUT_FORMAT
    )

    # 3. Output path
    output_path = args.get("output") or args.get("output_path")
    if not output_path:
        output_path = env.get("GITPR_CHECK_OUTPUT") or None

    # 4. Fail on severity
    raw_fail_on = args.get("fail_on")
    if not raw_fail_on:
        raw_fail_on = env.get("GITPR_CHECK_FAIL_ON")
    fail_on = parse_severity(raw_fail_on) if raw_fail_on else DEFAULT_FAIL_ON

    # 5. No IA
    no_ia_arg = args.get("no_ia")
    if no_ia_arg is not None:
        no_ia = bool(no_ia_arg)
    else:
        no_ia = _parse_bool(env.get("GITPR_CHECK_NO_IA", "false"))

    # 6. IA only high risk
    ia_high_risk_arg = args.get("ia_only_high_risk")
    if ia_high_risk_arg is not None:
        ia_only_high_risk = bool(ia_high_risk_arg)
    else:
        ia_only_high_risk = _parse_bool(
            env.get("GITPR_CHECK_IA_ONLY_HIGH_RISK", "false")
        )

    # 7. Baseline path
    baseline_path = args.get("baseline") or args.get("baseline_path")
    if not baseline_path:
        baseline_path = env.get("GITPR_CHECK_BASELINE_PATH") or None

    # 8. Policy
    policy = args.get("policy")
    if not policy:
        policy = env.get("GITPR_CHECK_POLICY") or None

    # 9. Timeout
    timeout_raw = args.get("timeout_seconds")
    if timeout_raw is None:
        timeout_raw = env.get("GITPR_CHECK_TIMEOUT_SECONDS")
    if timeout_raw is not None:
        try:
            timeout_seconds = int(timeout_raw)
        except (ValueError, TypeError):
            timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    else:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    return CheckConfig(
        base_ref=base_ref,
        output_format=output_format,
        output_path=output_path,
        fail_on=fail_on,
        no_ia=no_ia,
        ia_only_high_risk=ia_only_high_risk,
        baseline_path=baseline_path,
        policy=policy,
        timeout_seconds=timeout_seconds,
    )
