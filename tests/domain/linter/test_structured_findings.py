"""The linter's structured findings — the half of a lint run a baseline can fingerprint.

A rule's alert is built by interpolating the rule's message template and nothing
else, so the string the report is written from names neither the rule that fired
nor the category it belongs to. `TODO marker left in src/app.py (Line 10).` cannot
be turned back into an identity, which is why the engine grew a second, optional
output channel that records the same detection as data.

Two invariants carry this file.

The first is that closing the channel changes nothing. Every alert string, in
every mode, is byte-for-byte what it was before the channel existed — asserted
both by pinning the strings and by running one diff twice, once with the channel
open and once with it shut, comparing the whole result.

The second is that a finding is never re-derived from prose. `rule_id`,
`category` and the digest of the offending line are captured where the detection
happens; the alert and the finding are two renderings of one event, not one
parsed out of the other.

The line numbers are the file's own: the scanner moves its new-side counter over
context lines as well as over additions, so the two added lines below are 10 and
11, which is what `git`, the report and a reader of the file all call them. One
test here pins that directly, because the number a finding carries is half of its
fingerprint and the whole of a `--scope line` suppression.
"""

import unittest
from unittest.mock import patch

from src.diff_parser import parse_added_lines
from src.domain.baseline.baseline_fingerprint import snippet_hash
from src.domain.finding.finding_types import NormalizedFinding
from src.infrastructure.linter.external.base_bridge import ExternalLinterResult
from src.linter_engine import lint_findings, parse_diff_and_lint

# The hunk opens at 9 with one context line before the change, so the two added
# lines are 10 and 11 on the new side.
_HUNK_START = 9
_TODO_LINE = 10
_NUMBER_LINE = 11

_DIFF = f"""diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -{_HUNK_START},2 +{_HUNK_START},4 @@ def main():
     setup()
+TODO: remove this
+MAGIC_NUMBER = 42
     teardown()
"""

_FULL_FILE = """import os

def main():
    TODO: remove this
    MAGIC_NUMBER = 42
"""

_CHECKSTYLE_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<checkstyle version="8.0">
<file name="src/app.py">
<error line="{_TODO_LINE}" severity="error" message="Missing Javadoc comment."/>
<error line="{_NUMBER_LINE}" severity="warning" message="Line is longer than 100 characters."/>
</file>
</checkstyle>"""


def _rule(**overrides):
    """A rule shaped like the ones the linter's YAML carries."""
    rule = {
        "name": "todo-marker",
        "category": "style",
        "regex": r"\bTODO\b",
        "message": "TODO marker left in {file_name} (Line {line_number}).",
        "level": "warning",
        "extensions": ["*"],
    }
    rule.update(overrides)
    return rule


def _number_rule(**overrides):
    """A second rule, this one with no `category` — the default has to show."""
    rule = _rule(
        name="magic-number",
        regex=r"\bMAGIC_NUMBER\b",
        message="Magic number in {file_name} (Line {line_number}).",
        level="error",
    )
    rule.pop("category")
    rule.update(overrides)
    return rule


def _by_source(findings, source):
    return [item for item in findings if item.source == source]


class _FakeBridge:
    """A SAST bridge standing in for a tool that is not installed here."""

    def __init__(self, findings, warnings=(), available=True):
        self._findings = list(findings)
        self._warnings = list(warnings)
        self._available = available

    def is_available(self):
        return self._available

    def run(self, target_files, repo_path=".", diff_only=True, timeout=60):
        return ExternalLinterResult(
            tool_name="gitleaks",
            available=self._available,
            findings=list(self._findings),
            warnings=list(self._warnings),
        )


def _gitleaks_finding(line=_NUMBER_LINE, path="src/app.py", message="Generic API Key"):
    return NormalizedFinding(
        severity="error",
        category="security/secret",
        file_path=path,
        line_start=line,
        line_end=line,
        message=message,
        source="gitleaks",
        rule_id="generic-api-key",
    )


class LinterTestCase(unittest.TestCase):
    """Base class wiring the engine to a fixed rule set instead of the real YAML."""

    def _lint(self, diff_text=_DIFF, findings_out=None, rules=None, **kwargs):
        rules = [_rule(), _number_rule()] if rules is None else rules
        with patch("src.linter_engine.load_linter_rules", return_value=rules), \
                patch("src.linter_engine.load_external_linters", return_value=[]), \
                patch("src.linter_engine.load_sast_config", return_value={}):
            return parse_diff_and_lint(diff_text, findings_out=findings_out, **kwargs)

    def _lint_with_external(self, findings_out=None, xml=_CHECKSTYLE_XML,
                            rules=None, full_file=False):
        external = [{"name": "Checkstyle", "extensions": ["py"], "command": "noop"}]
        rules = [_rule()] if rules is None else rules
        if full_file:
            arguments = dict(is_full_file=True, file_path="src/app.py")
        else:
            arguments = {}
        with patch("src.linter_engine.load_linter_rules", return_value=rules), \
                patch("src.linter_engine.load_external_linters", return_value=external), \
                patch("src.linter_engine.load_sast_config", return_value={}), \
                patch("src.linter_engine._run_external_linter", return_value=xml):
            return parse_diff_and_lint(_DIFF, findings_out=findings_out, **arguments)

    def _lint_with_gitleaks(self, findings_out=None, sast_findings=None, rules=(),
                            diff_text=_DIFF):
        bridge = _FakeBridge(
            sast_findings if sast_findings is not None else [_gitleaks_finding()]
        )
        with patch("src.linter_engine.load_linter_rules", return_value=list(rules)), \
                patch("src.linter_engine.load_external_linters", return_value=[]), \
                patch("src.linter_engine.load_sast_config",
                      return_value={"gitleaks": {"enabled": True, "timeout_seconds": 5}}), \
                patch("src.linter_engine.GitleaksBridge", return_value=bridge):
            return parse_diff_and_lint(diff_text, findings_out=findings_out)


class TestRuleFindings(LinterTestCase):
    """A YAML rule's detection, recorded as data alongside its alert."""

    def test_a_finding_names_the_rule_the_alert_cannot(self):
        findings = []
        alerts = self._lint(findings_out=findings)

        todo = next(item for item in findings if item.rule_id == "todo-marker")
        self.assertEqual(todo.source, "linter")
        self.assertEqual(todo.category, "style")
        self.assertEqual(todo.file_path, "src/app.py")
        self.assertEqual(todo.line_start, _TODO_LINE)
        self.assertEqual(todo.line_end, _TODO_LINE)
        # The alert is only the rendered message — the name lives here or nowhere.
        self.assertNotIn("todo-marker", " ".join(alerts["warnings"]))

    def test_the_message_is_exactly_the_alert_string(self):
        """What makes a finding and its alert two views of one event, not two events."""
        findings = []
        alerts = self._lint(findings_out=findings)

        todo = next(item for item in findings if item.rule_id == "todo-marker")
        self.assertEqual(todo.message, alerts["warnings"][0])

    def test_the_line_numbers_are_the_ones_the_file_has(self):
        """Two surfaces number the same diff, and they have to agree.

        The finding's line is half of its fingerprint and the whole of a
        `--scope line` suppression, so the engine and `diff_parser` — the module
        the rest of the CLI counts added lines with — must never disagree about
        where an added line is.
        """
        findings = []
        self._lint(findings_out=findings)

        self.assertEqual(
            sorted(item.line_start for item in findings),
            sorted(parse_added_lines(_DIFF)["src/app.py"]),
        )

    def test_a_missing_category_falls_back_to_lint(self):
        findings = []
        self._lint(findings_out=findings)

        number = next(item for item in findings if item.rule_id == "magic-number")
        self.assertEqual(number.category, "lint")

    def test_severity_follows_the_rule_level(self):
        findings = []
        self._lint(findings_out=findings)

        by_rule = {item.rule_id: item for item in findings}
        self.assertEqual(by_rule["todo-marker"].severity, "warning")
        self.assertEqual(by_rule["magic-number"].severity, "error")

    def test_the_snippet_hash_is_the_digest_of_the_stripped_line(self):
        findings = []
        self._lint(findings_out=findings)

        todo = next(item for item in findings if item.rule_id == "todo-marker")
        self.assertEqual(todo.snippet_hash, snippet_hash("TODO: remove this"))

    def test_every_detection_produces_a_finding(self):
        findings = []
        alerts = self._lint(findings_out=findings)

        self.assertEqual(len(findings), len(alerts["errors"]) + len(alerts["warnings"]))

    def test_the_callers_list_is_extended_never_replaced(self):
        findings = [_gitleaks_finding(line=1, path="src/other.py")]
        self._lint(findings_out=findings)

        self.assertEqual(findings[0].file_path, "src/other.py")
        self.assertGreater(len(findings), 1)

    def test_an_ignored_comment_line_produces_no_finding(self):
        rules = [_rule(ignore_comments=True)]
        diff = _DIFF.replace("+TODO: remove this", "+# TODO: remove this")
        findings = []
        alerts = self._lint(diff, findings_out=findings, rules=rules)

        self.assertEqual(findings, [])
        self.assertEqual(alerts["warnings"], [])

    def test_a_rule_that_does_not_apply_is_silent(self):
        findings = []
        self._lint(findings_out=findings, rules=[_rule(extensions=["rb"])])

        self.assertEqual(findings, [])

    def test_an_invalid_regex_reports_an_alert_and_no_finding(self):
        """The error alert is about the rule itself — it is not a finding."""
        findings = []
        alerts = self._lint(findings_out=findings, rules=[_rule(regex="[unclosed")])

        self.assertEqual(findings, [])
        self.assertTrue(alerts["errors"])

    def test_two_rules_on_one_line_produce_two_findings(self):
        rules = [_rule(), _rule(name="todo-strict", level="error")]
        findings = []
        self._lint(findings_out=findings, rules=rules)

        self.assertEqual([item.rule_id for item in findings], ["todo-marker", "todo-strict"])


class TestFullFileFindings(LinterTestCase):
    """`--input` audits a file rather than a diff, and the channel follows it."""

    def test_full_file_mode_collects_findings(self):
        findings = []
        alerts = self._lint(
            _FULL_FILE, findings_out=findings, is_full_file=True, file_path="src/app.py"
        )

        self.assertEqual(len(findings), 2)
        self.assertEqual({item.rule_id for item in findings}, {"todo-marker", "magic-number"})
        self.assertEqual(len(alerts["warnings"]) + len(alerts["errors"]), 2)

    def test_full_file_line_numbers_count_from_the_first_line(self):
        findings = []
        self._lint(_FULL_FILE, findings_out=findings, is_full_file=True, file_path="src/app.py")

        todo = next(item for item in findings if item.rule_id == "todo-marker")
        self.assertEqual(todo.line_start, 4)

    def test_full_file_without_a_path_lints_nothing(self):
        findings = []
        alerts = self._lint(_FULL_FILE, findings_out=findings, is_full_file=True)

        self.assertEqual(findings, [])
        self.assertEqual(alerts, {"errors": [], "warnings": []})

    def test_windows_separators_are_normalized_for_the_digest(self):
        """The digest of a line is the same whichever separator named the file."""
        findings = []
        self._lint(
            _FULL_FILE,
            findings_out=findings,
            is_full_file=True,
            file_path="src\\app.py",
        )

        todo = next(item for item in findings if item.rule_id == "todo-marker")
        self.assertEqual(todo.snippet_hash, snippet_hash("TODO: remove this"))


class TestExternalFindings(LinterTestCase):
    """A Checkstyle bridge reports locations and messages, never a rule name."""

    def test_a_bridge_finding_carries_the_tool_name(self):
        findings = []
        self._lint_with_external(findings_out=findings, rules=[])

        first = findings[0]
        self.assertEqual(first.source, "external")
        self.assertEqual(first.rule_id, "Checkstyle")
        self.assertEqual(first.category, "lint")
        self.assertEqual(first.file_path, "src/app.py")

    def test_the_message_has_no_render_markup(self):
        """The alert is decorated for a terminal; the finding keeps the tool's words."""
        findings = []
        alerts = self._lint_with_external(findings_out=findings, rules=[])

        self.assertEqual(findings[0].message, "Missing Javadoc comment.")
        self.assertTrue(alerts["errors"][0].startswith("🚨 [Checkstyle]"))

    def test_severity_follows_the_report(self):
        findings = []
        self._lint_with_external(findings_out=findings, rules=[])

        self.assertEqual([item.severity for item in findings], ["error", "warning"])

    def test_the_snippet_hash_comes_from_the_line_the_engine_parsed(self):
        """The tool reports a location; the content is the diff's, never the tool's."""
        findings = []
        self._lint_with_external(findings_out=findings, rules=[])

        todo = next(item for item in findings if item.line_start == _TODO_LINE)
        self.assertEqual(todo.snippet_hash, snippet_hash("TODO: remove this"))

    def test_a_file_level_violation_keeps_line_zero(self):
        """Checkstyle's line 0 (file length, missing header) is not bent into line 1."""
        xml = _CHECKSTYLE_XML.replace(f'line="{_TODO_LINE}"', 'line="0"')
        findings = []
        self._lint_with_external(findings_out=findings, xml=xml, rules=[], full_file=True)

        file_level = next(item for item in findings if item.line_start == 0)
        self.assertEqual(file_level.line_end, 0)
        # Nothing was parsed for line 0, so the finding carries no digest rather
        # than a digest of an empty string.
        self.assertIsNone(file_level.snippet_hash)

    def test_a_line_the_diff_did_not_touch_is_not_a_finding(self):
        xml = _CHECKSTYLE_XML.replace(f'line="{_TODO_LINE}"', 'line="900"').replace(
            f'line="{_NUMBER_LINE}"', 'line="901"'
        )
        findings = []
        self._lint_with_external(findings_out=findings, xml=xml, rules=[])

        self.assertEqual(findings, [])

    def test_a_report_about_another_file_is_dropped(self):
        xml = _CHECKSTYLE_XML.replace("src/app.py", "src/elsewhere.py")
        findings = []
        self._lint_with_external(findings_out=findings, xml=xml, rules=[])

        self.assertEqual(findings, [])

    def test_both_channels_describe_the_same_detections(self):
        findings = []
        alerts = self._lint_with_external(findings_out=findings, rules=[])

        self.assertEqual(len(findings), len(alerts["errors"]) + len(alerts["warnings"]))


class TestSastFindings(LinterTestCase):
    """The bridges' findings reach the channel with their digest filled in."""

    def test_a_bridge_finding_is_extended_into_the_list(self):
        findings = []
        alerts = self._lint_with_gitleaks(findings_out=findings)

        self.assertEqual([item.source for item in findings], ["gitleaks"])
        self.assertEqual(len(alerts["errors"]), 1)

    def test_the_digest_is_filled_from_the_diff(self):
        """The tool reports a location; the digest comes from the line the engine parsed."""
        findings = []
        self._lint_with_gitleaks(findings_out=findings)

        self.assertEqual(findings[0].snippet_hash, snippet_hash("MAGIC_NUMBER = 42"))

    def test_an_existing_digest_is_not_overwritten(self):
        """A bridge that already knows the line keeps its own answer."""
        declared = snippet_hash("a different line entirely")
        with_digest = _gitleaks_finding()
        with_digest.snippet_hash = declared
        findings = []
        self._lint_with_gitleaks(findings_out=findings, sast_findings=[with_digest])

        self.assertEqual(findings[0].snippet_hash, declared)

    def test_a_line_outside_the_diff_is_not_a_finding(self):
        findings = []
        self._lint_with_gitleaks(
            findings_out=findings, sast_findings=[_gitleaks_finding(line=900)]
        )

        self.assertEqual(findings, [])

    def test_the_merge_with_a_regex_alert_keeps_the_digest(self):
        """Confirmation by a second tool must not change a finding's identity."""
        rules = [_rule(
            name="sec-hardcoded-value",
            category="security/secret",
            regex=r"\bMAGIC_NUMBER\b",
            message="Possible hardcoded value in {file_name} (Line {line_number}).",
            level="error",
        )]
        findings = []
        alerts = self._lint_with_gitleaks(findings_out=findings, rules=rules)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].source, "gitleaks+regex")
        self.assertEqual(findings[0].snippet_hash, snippet_hash("MAGIC_NUMBER = 42"))
        self.assertEqual(findings[0].rule_id, "generic-api-key")
        # The regex alert was consumed by the merge, and the merged one replaced it.
        self.assertEqual(len(alerts["errors"]), 1)
        self.assertIn("Gitleaks + Static Regex", alerts["errors"][0])

    def test_a_silent_bridge_detects_nothing(self):
        findings = []
        alerts = self._lint_with_gitleaks(findings_out=findings, sast_findings=[])

        self.assertEqual(findings, [])
        self.assertEqual(alerts, {"errors": [], "warnings": []})

    def test_a_file_the_diff_never_showed_keeps_no_digest(self):
        """A bridge may speak about a file the diff did not touch. The engine has no
        text for it, so the finding travels with an empty digest instead of a made-up
        one — the fingerprint then rests on the location alone."""
        findings = []
        self._lint_with_gitleaks(
            findings_out=findings,
            sast_findings=[_gitleaks_finding(line=_NUMBER_LINE, path="src/unseen.py")],
        )

        self.assertEqual(len(findings), 1)
        self.assertIsNone(findings[0].snippet_hash)


class TestByteIdentity(LinterTestCase):
    """Opening the channel must not move a single character of the alerts."""

    def test_the_rule_alerts_are_the_strings_they_always_were(self):
        alerts = self._lint()

        self.assertEqual(alerts["warnings"], [
            f"TODO marker left in src/app.py (Line {_TODO_LINE})."
        ])
        self.assertEqual(alerts["errors"], [
            f"Magic number in src/app.py (Line {_NUMBER_LINE})."
        ])

    def test_closing_the_channel_changes_nothing_for_rules(self):
        self.assertEqual(self._lint(), self._lint(findings_out=[]))

    def test_closing_the_channel_changes_nothing_for_the_bridges(self):
        self.assertEqual(
            self._lint_with_external(),
            self._lint_with_external(findings_out=[]),
        )

    def test_closing_the_channel_changes_nothing_for_the_sast_merge(self):
        self.assertEqual(
            self._lint_with_gitleaks(),
            self._lint_with_gitleaks(findings_out=[]),
        )

    def test_an_empty_rule_set_returns_the_empty_result_in_both_modes(self):
        self.assertEqual(self._lint(rules=[]), {"errors": [], "warnings": []})
        self.assertEqual(self._lint(rules=[], findings_out=[]), {"errors": [], "warnings": []})

    def test_a_diff_with_nothing_to_say_returns_the_empty_result(self):
        diff = "diff --git a/src/app.py b/src/app.py\n--- a/src/app.py\n+++ b/src/app.py\n"
        self.assertEqual(self._lint(diff), {"errors": [], "warnings": []})
        self.assertEqual(self._lint(diff, findings_out=[]), {"errors": [], "warnings": []})


class TestLintFindings(LinterTestCase):
    """The public wrapper the baseline calls, instead of the alerts it does not need."""

    def test_it_returns_the_findings_of_one_run(self):
        with patch("src.linter_engine.load_linter_rules",
                   return_value=[_rule(), _number_rule()]), \
                patch("src.linter_engine.load_external_linters", return_value=[]), \
                patch("src.linter_engine.load_sast_config", return_value={}):
            findings = lint_findings(_DIFF)

        self.assertEqual(
            [item.rule_id for item in findings], ["todo-marker", "magic-number"]
        )

    def test_it_passes_its_keywords_through(self):
        with patch("src.linter_engine.load_linter_rules", return_value=[_rule()]), \
                patch("src.linter_engine.load_external_linters", return_value=[]), \
                patch("src.linter_engine.load_sast_config", return_value={}):
            findings = lint_findings(_FULL_FILE, is_full_file=True, file_path="src/app.py")

        self.assertEqual([item.rule_id for item in findings], ["todo-marker"])

    def test_skip_external_never_looks_the_tools_up(self):
        """The remote review passes skip_external: a foreign revision has no local tree."""
        with patch("src.linter_engine.load_linter_rules", return_value=[]), \
                patch("src.linter_engine.load_external_linters") as external_linters, \
                patch("src.linter_engine.load_sast_config") as sast_config:
            findings = lint_findings(_DIFF, skip_external=True)

        self.assertEqual(findings, [])
        external_linters.assert_not_called()
        sast_config.assert_not_called()

    def test_a_clean_run_is_an_empty_list_not_none(self):
        with patch("src.linter_engine.load_linter_rules", return_value=[]), \
                patch("src.linter_engine.load_external_linters", return_value=[]), \
                patch("src.linter_engine.load_sast_config", return_value={}):
            findings = lint_findings(_DIFF)

        self.assertEqual(findings, [])


class TestFindingsAreFingerprintable(unittest.TestCase):
    """The point of the channel: what it records is enough to identify a finding."""

    def _findings(self, rules):
        findings = []
        with patch("src.linter_engine.load_linter_rules", return_value=rules), \
                patch("src.linter_engine.load_external_linters", return_value=[]), \
                patch("src.linter_engine.load_sast_config", return_value={}):
            parse_diff_and_lint(_DIFF, findings_out=findings)
        return findings

    def test_every_field_the_fingerprint_needs_is_present(self):
        from src.domain.baseline.baseline_fingerprint import compute_fingerprint

        fingerprint = compute_fingerprint(self._findings([_rule()])[0])

        self.assertTrue(fingerprint.startswith("sha256:"))
        self.assertEqual(len(fingerprint), len("sha256:") + 64)

    def test_two_runs_over_one_diff_agree(self):
        """Determinism is the whole premise of a committed baseline."""
        from src.domain.baseline.baseline_fingerprint import compute_fingerprint

        rules = [_rule(), _number_rule()]
        first = [compute_fingerprint(item) for item in self._findings(rules)]
        second = [compute_fingerprint(item) for item in self._findings(rules)]

        self.assertEqual(first, second)

    def test_a_finding_without_a_rule_id_is_low_confidence(self):
        """The engine always names its rule; this is the contract the AI channel relies on."""
        from src.domain.baseline.baseline_fingerprint import is_low_confidence

        findings = self._findings([_rule()])

        self.assertFalse(is_low_confidence(findings[0]))


if __name__ == "__main__":
    unittest.main()
