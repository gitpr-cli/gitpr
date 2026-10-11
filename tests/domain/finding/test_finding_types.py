"""Unit tests for the canonical finding model and its legacy import path."""

from src.domain.finding.finding_types import NormalizedFinding
from src.infrastructure.linter.external.base_bridge import (
    NormalizedFinding as LegacyNormalizedFinding,
)


def test_positional_construction_with_seven_args():
    """The historical seven positional arguments must keep working unchanged."""
    finding = NormalizedFinding(
        "error",
        "security/secret",
        "src/config.py",
        42,
        42,
        "AWS Access Key detected [AKIA****]",
        "gitleaks",
    )

    assert finding.rule_id is None
    assert finding.snippet_hash is None
    assert finding.rule_version is None


def test_optional_fields_are_carried():
    finding = NormalizedFinding(
        severity="error",
        category="security",
        file_path="src/keys.py",
        line_start=10,
        line_end=10,
        message="Hardcoded secret",
        source="linter",
        rule_id="sec-aws-key",
        snippet_hash="sha256:abc",
        rule_version="2",
    )

    assert finding.rule_id == "sec-aws-key"
    assert finding.snippet_hash == "sha256:abc"
    assert finding.rule_version == "2"


def test_legacy_import_path_returns_the_same_class():
    """`base_bridge` re-exports the canonical model, it does not redefine it."""
    assert LegacyNormalizedFinding is NormalizedFinding
