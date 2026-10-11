"""Tests for the finding fingerprint — the golden values are the tripwire.

The digest below is hardcoded on purpose. Changing it means every baseline in
the wild stops matching, so it has to be a deliberate `FINGERPRINT_VERSION`
bump and never a side effect of a refactor.
"""

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
from src.domain.finding.finding_types import NormalizedFinding

_GOLDEN_LINE = '    key = "AKIA****"  '
_GOLDEN_SNIPPET = "sha256:b63cce4bc668c5ba47049f5e37e3923ef1639325015fe5ce3ad58b0788476410"
_GOLDEN_PAYLOAD = (
    "1\naws-access-key\nsecurity/secret\nsrc/config.py\ngitleaks\n42\n42\n" + _GOLDEN_SNIPPET
)
_GOLDEN_DIGEST = "sha256:b37f7666093a90c00c555dbda6c65ad7ee9136d46a517cbc529273e1521f1869"
_AI_DIGEST = "sha256:2140017bce39616cda28a7a2f0945d9f0930386bf4293352f6173b85d55d2ae9"


def _finding(**overrides) -> NormalizedFinding:
    fields = dict(
        severity="error",
        category="security/secret",
        file_path="src/config.py",
        line_start=42,
        line_end=42,
        message="AWS Access Key detected [AKIA****]",
        source="gitleaks",
        rule_id="aws-access-key",
        snippet_hash=snippet_hash(_GOLDEN_LINE),
    )
    fields.update(overrides)
    return NormalizedFinding(**fields)


def test_payload_and_digest_are_golden():
    finding = _finding()

    assert fingerprint_payload(finding) == _GOLDEN_PAYLOAD
    assert compute_fingerprint(finding) == _GOLDEN_DIGEST


def test_version_is_the_first_line_of_the_payload():
    """A bump must change every fingerprint at once, so it comes first."""
    assert FINGERPRINT_VERSION == "1"
    assert fingerprint_payload(_finding()).split("\n")[0] == FINGERPRINT_VERSION


def test_message_and_severity_do_not_take_part():
    """Prose is reworded and a rule's severity is retuned — neither is identity."""
    rewritten = _finding(
        message="Hardcoded credential found",
        severity="warning",
    )

    assert compute_fingerprint(rewritten) == _GOLDEN_DIGEST


def test_the_offending_line_never_reaches_the_payload():
    finding = _finding(snippet_hash=snippet_hash("SECRET_TOKEN = 'ghp_0123456789'"))

    payload = fingerprint_payload(finding)

    assert "ghp_0123456789" not in payload
    assert "SECRET_TOKEN" not in payload
    assert compute_fingerprint(finding) != _GOLDEN_DIGEST


def test_a_shifted_line_is_a_different_finding():
    assert compute_fingerprint(_finding(line_start=43, line_end=43)) != _GOLDEN_DIGEST


def test_edited_line_content_is_a_different_finding():
    edited = _finding(snippet_hash=snippet_hash('key = "AKIAOTHER"'))

    assert compute_fingerprint(edited) != _GOLDEN_DIGEST


def test_whitespace_alone_does_not_change_the_digest():
    assert normalize_line_text(_GOLDEN_LINE) == 'key = "AKIA****"'
    assert snippet_hash(_GOLDEN_LINE) == snippet_hash('key = "AKIA****"')
    assert snippet_hash("key\t=\n\t\"AKIA****\"") == _GOLDEN_SNIPPET
    assert compute_fingerprint(_finding(snippet_hash=snippet_hash('key = "AKIA****"'))) == _GOLDEN_DIGEST


def test_an_unknown_line_is_not_an_empty_line():
    """`None` means "no content evidence"; an empty line is still evidence."""
    assert snippet_hash(None) == ""
    assert snippet_hash("") != ""


def test_paths_are_repo_relative_forward_slash_lowercase():
    assert normalize_path("src\\Config\\A.py") == "src/config/a.py"
    assert normalize_path("./src/a.py") == "src/a.py"
    assert normalize_path("C:\\Repo\\src\\A.py", repo_path="c:/repo") == "src/a.py"
    assert normalize_path("/abs/repo/src/a.py", repo_path="/abs/repo/") == "src/a.py"


def test_the_repository_location_does_not_change_the_digest():
    """The same revision cloned elsewhere is the same baseline."""
    portability = _finding(file_path="C:\\Work\\Repo\\src\\config.py")

    assert compute_fingerprint(portability, repo_path="C:\\Work\\Repo") == _GOLDEN_DIGEST


def test_rule_identity_falls_back_to_the_category():
    assert rule_identity("aws-access-key", "security") == "aws-access-key"
    assert rule_identity(None, "Security") == "category:security"
    assert rule_identity("  ", None) == "category:unknown"


def test_a_finding_without_a_rule_is_low_confidence():
    """The AI reports prose, not rule ids, so its findings are marked as weaker."""
    ai_finding = NormalizedFinding(
        severity="error",
        category="security",
        file_path="src/a.py",
        line_start=10,
        line_end=12,
        message="Looks like a hardcoded token.",
        source="ai",
    )

    assert is_low_confidence(ai_finding) is True
    assert is_low_confidence(_finding()) is False
    assert fingerprint_payload(ai_finding).split("\n")[1] == "category:security"
    assert compute_fingerprint(ai_finding) == _AI_DIGEST
