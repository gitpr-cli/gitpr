"""Pure rules, default weights, and threshold configuration for risk scoring."""

import fnmatch
import os
import re
from dataclasses import dataclass, field
from typing import Any

from src.domain.risk.risk_types import RiskLevel, RiskSignal

DEFAULT_WEIGHTS = {
    RiskSignal.CRITICAL_PATH: 25.0,
    RiskSignal.SECURITY_SENSITIVE: 25.0,
    RiskSignal.DATABASE_MIGRATION: 20.0,
    RiskSignal.INFRASTRUCTURE: 20.0,
    RiskSignal.NO_TEST_CHANGE: 15.0,
    RiskSignal.LARGE_DIFF: 10.0,
    RiskSignal.HISTORICAL_BUGS: 20.0,
    RiskSignal.HISTORICAL_REVERTS: 10.0,
    RiskSignal.HIGH_CHURN: 15.0,
    RiskSignal.HIGH_COUPLING: 15.0,
    RiskSignal.FINDING_BLOCKER: 25.0,
    RiskSignal.FINDING_CRITICAL: 15.0,
    RiskSignal.FINDING_WARNING: 3.0,
    RiskSignal.TEST_PRESENT: -10.0,
    RiskSignal.NEW_FILE: 0.0,
}

DEFAULT_THRESHOLDS = {
    "low_max": 24.0,
    "medium_max": 49.0,
    "high_max": 79.0,
}

DEFAULT_CRITICAL_PATTERNS = {
    RiskSignal.SECURITY_SENSITIVE: [
        "**/security/**",
        "**/crypto/**",
        "**/secret/**",
        "**/token/**",
        "**/session/**",
        "**/auth/**",
        "**/login/**",
    ],
    RiskSignal.DATABASE_MIGRATION: [
        "**/migration/**",
        "**/migrations/**",
        "**/schema/**",
        "database/migrations/**",
    ],
    RiskSignal.INFRASTRUCTURE: [
        ".github/workflows/**",
        ".gitlab-ci.yml",
        "Dockerfile*",
        "docker/**",
        "terraform/**",
        "k8s/**",
        "helm/**",
        "*.tf",
    ],
    RiskSignal.CRITICAL_PATH: [
        "**/payment/**",
        "**/billing/**",
        "**/checkout/**",
        "**/transaction/**",
        "**/policy/**",
        "**/policies/**",
        "**/middleware/**",
        "**/permission/**",
        "**/permissions/**",
    ],
}

# Extra glob patterns that identify a test file, on top of the naming
# conventions is_test_file() recognises by default. Empty here: the built-in
# detection already covers the common shapes (tests/, test_*, *_test.py,
# *.spec.ts, *Test.php), and a project only needs entries when its layout uses
# a convention those rules miss. A policy pack sets them per stack.
DEFAULT_TEST_PATTERNS: list[str] = []

# Non-executable file extensions and patterns that must never trigger NO_TEST_CHANGE
NON_EXECUTABLE_PATTERNS = [
    "*.md",
    "*.txt",
    "*.rst",
    "*.json",
    "*.yml",
    "*.yaml",
    "*.xml",
    "*.csv",
    "*.tsv",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.svg",
    "*.ico",
    "*.lock",
    "*.pdf",
    ".gitignore",
    ".gitattributes",
    ".env*",
    "LICENSE*",
    "CHANGELOG*",
]


@dataclass
class RiskConfig:
    enabled: bool = True
    include_in_review: bool = True
    analysis_version: str = "1.0"
    thresholds: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))
    weights: dict[RiskSignal, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    critical_patterns: dict[RiskSignal, list[str]] = field(
        default_factory=lambda: {k: list(v) for k, v in DEFAULT_CRITICAL_PATTERNS.items()}
    )
    non_executable_patterns: list[str] = field(default_factory=lambda: list(NON_EXECUTABLE_PATTERNS))
    test_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_TEST_PATTERNS))


def resolve_risk_level(score: float, thresholds: dict[str, float] | None = None) -> RiskLevel:
    """Map a numerical score (0.0 to 100.0) to its corresponding RiskLevel."""
    th = thresholds or DEFAULT_THRESHOLDS
    low_max = th.get("low_max", 24.0)
    med_max = th.get("medium_max", 49.0)
    high_max = th.get("high_max", 79.0)

    if score <= low_max:
        return RiskLevel.LOW
    if score <= med_max:
        return RiskLevel.MEDIUM
    if score <= high_max:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


def matches_pattern(path: str, pattern: str) -> bool:
    """Case-insensitive pattern matcher for file paths using forward slashes."""
    normalized_path = path.replace("\\", "/").strip().lower()
    normalized_pattern = pattern.replace("\\", "/").strip().lower()

    if normalized_pattern.startswith("**/") and normalized_pattern.endswith("/**"):
        token = normalized_pattern[3:-3]
        segments = normalized_path.split("/")[:-1]
        if any(seg == token or seg.startswith(token) for seg in segments):
            return True

    if normalized_pattern.startswith("**/"):
        suffix_pattern = normalized_pattern[3:]
        if fnmatch.fnmatch(normalized_path, suffix_pattern) or fnmatch.fnmatch(
            normalized_path, f"*{suffix_pattern}"
        ):
            return True

    return fnmatch.fnmatch(normalized_path, normalized_pattern)


def is_non_executable_file(path: str, non_exec_patterns: list[str] | None = None) -> bool:
    """Checks whether a file path corresponds to documentation, config, or assets."""
    patterns = non_exec_patterns or NON_EXECUTABLE_PATTERNS
    return any(matches_pattern(path, pat) for pat in patterns)


def is_test_file(path: str, test_patterns: list[str] | None = None) -> bool:
    """Checks whether a path is a test file itself.

    *test_patterns* adds glob patterns on top of the naming conventions below —
    it never narrows them, so a project (or a policy pack) can teach the matcher
    a layout it does not know without losing the conventions it does. Patterns
    are checked first because a declared pattern is an explicit statement about
    this repository, while the conventions are a guess about every repository.
    """
    if test_patterns and any(matches_pattern(path, pat) for pat in test_patterns):
        return True

    normalized = path.replace("\\", "/").lower()
    base = os.path.basename(normalized)
    parts = normalized.split("/")
    if "test" in parts or "tests" in parts or "__tests__" in parts:
        return True
    if ".test." in base or ".spec." in base:
        return True
    if base.startswith("test_") or base.endswith(
        ("_test.py", "test.py", "test.js", "test.ts", "test.tsx", "test.jsx", "test.php")
    ):
        return True
    if base.endswith(
        ("test.go", "spec.js", "spec.ts", "spec.tsx", "spec.jsx", "test.rb")
    ):
        return True
    return False


def load_risk_config(config_path: str | None = None) -> RiskConfig:
    """Load RiskConfig from a yaml file if it exists, otherwise return default config."""
    cfg = RiskConfig()
    candidates = []
    if config_path:
        candidates.append(config_path)
    candidates.extend([
        ".gitpr.risk.yml",
        os.path.join(".gitpr", "skill", "gitpr.risk.yml"),
        os.path.join(os.path.expanduser("~"), ".gitpr", "skill", "gitpr.risk.yml"),
    ])

    found_path = None
    for p in candidates:
        if os.path.isfile(p):
            found_path = p
            break

    if not found_path:
        return cfg

    try:
        import yaml

        with open(found_path, "r", encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f) or {}

        risk_data = data.get("risk", data)
        if not isinstance(risk_data, dict):
            return cfg

        if "enabled" in risk_data:
            cfg.enabled = bool(risk_data["enabled"])
        if "include_in_review" in risk_data:
            cfg.include_in_review = bool(risk_data["include_in_review"])
        if "analysis_version" in risk_data:
            cfg.analysis_version = str(risk_data["analysis_version"])

        if "thresholds" in risk_data and isinstance(risk_data["thresholds"], dict):
            for k, v in risk_data["thresholds"].items():
                if k in cfg.thresholds:
                    cfg.thresholds[k] = float(v)

        if "weights" in risk_data and isinstance(risk_data["weights"], dict):
            for k, v in risk_data["weights"].items():
                try:
                    sig = RiskSignal(k)
                    val = float(v)
                    # Negative weights only allowed for mitigating signals
                    if val < 0 and sig != RiskSignal.TEST_PRESENT:
                        continue
                    cfg.weights[sig] = val
                except (ValueError, KeyError):
                    continue

        if "critical_paths" in risk_data and isinstance(risk_data["critical_paths"], list):
            cfg.critical_patterns[RiskSignal.CRITICAL_PATH] = [
                str(p) for p in risk_data["critical_paths"]
            ]

        if "test_patterns" in risk_data and isinstance(risk_data["test_patterns"], list):
            cfg.test_patterns = [str(p) for p in risk_data["test_patterns"]]
    except Exception:
        # Fall back to default safely
        return RiskConfig()

    return cfg
