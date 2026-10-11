"""The gate: the one place a run asks whether there is a baseline.

Two promises are what these tests exist for. The first is structural — a flow
that does not enforce the baseline never reads the file, so every other command
in the CLI keeps behaving exactly as it did before the feature existed. The
second is that a flow which *does* enforce it refuses to run on a file it cannot
apply, instead of classifying every finding as new and calling that a verdict.

The rest is the vocabulary: which status an alert is annotated with, what counts
as blocking, and how a finding that does not count is still shown in the risk
breakdown with zero weight.

The four `GITPR_BASELINE_*` keys are pinned here rather than left to the
environment: a developer whose own `~/.gitpr/.env` turns the feature off would
otherwise see this whole file fail for a reason that has nothing to do with the
code.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from src.application.use_cases import baseline_gate as gate_module
from src.application.use_cases.baseline_gate import (
    alert_for,
    alert_status_index,
    annotate_alerts,
    attach_informational_evidence,
    blocking_errors,
    classify_findings_for_gate,
    informational_evidence,
    load_baseline,
    new_findings,
    status_line,
)
from src.application.use_cases.create_baseline import build_manifest
from src.domain.baseline import (
    BaselineError,
    BaselineStatus,
    compute_fingerprint,
    get_active_baseline,
    set_active_baseline,
    snippet_hash,
)
from src.domain.finding.finding_types import NormalizedFinding
from src.domain.risk.risk_types import (
    FileRisk,
    PullRequestRisk,
    RiskLevel,
    RiskSignal,
)
from src.infrastructure.baseline.local_baseline_repository import write_manifest
from src.linter_engine import external_alert_message

# The documented defaults, pinned so the suite does not depend on the machine.
BASELINE_ENV = {
    "GITPR_BASELINE_ENABLED": "true",
    "GITPR_BASELINE_PATH": "",
    "GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH": "true",
    "GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES": "true",
}

OVERRIDES_BY_RULE = """overrides:
  suppressions:
    - scope: rule
      rule_id: "warning-todo"
      reason: "The rule is too noisy for this legacy tree."
"""


def finding(
    message="AWS access key in source.",
    *,
    file_path="src/app.py",
    line=10,
    severity="error",
    rule_id="sec-aws-key",
    category="security",
    source="linter",
    text="AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'",
):
    """A finding of the shape the linter's side channel produces."""
    return NormalizedFinding(
        severity=severity,
        category=category,
        file_path=file_path,
        line_start=line,
        line_end=line,
        message=message,
        source=source,
        rule_id=rule_id,
        snippet_hash=snippet_hash(text),
    )


class GateTestCase(unittest.TestCase):
    """A repository directory, a written baseline, and the settings pinned."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_baseline_gate_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(self.repo)

        self.env = mock.patch.dict(os.environ, dict(BASELINE_ENV))
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(set_active_baseline, None)

    def write_baseline(self, findings=None):
        """Writes the file the way `gitpr baseline create` would."""
        manifest = build_manifest(
            [finding()] if findings is None else findings, repo_path=self.repo
        )
        write_manifest(manifest, self.repo)
        return manifest

    def write_overrides(self, text=OVERRIDES_BY_RULE):
        path = os.path.join(self.repo, ".gitpr", "baseline.overrides.yml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        return path

    def tamper(self, mutate):
        """Edits the written file without recomputing its checksum."""
        path = os.path.join(self.repo, ".gitpr", "baseline.json")
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
        mutate(data)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2)

    def load(self, required=True, **kwargs):
        return load_baseline(required=required, repo_path=self.repo, **kwargs)

    def classified(self, item):
        """The finding, read against a baseline that already records it."""
        self.write_baseline([item])
        gate = self.load()
        return classify_findings_for_gate([item], gate, repo_path=self.repo)[0]


class TestWhatTheGateReads(GateTestCase):
    def test_a_flow_that_does_not_enforce_reads_nothing(self):
        """The "no baseline, no change" promise, held structurally."""
        self.write_baseline()

        with mock.patch.object(gate_module, "read_baseline") as read:
            gate = self.load(required=False)

        read.assert_not_called()
        self.assertFalse(gate.is_active)
        self.assertFalse(gate.snapshot.exists)

    def test_turning_the_feature_off_reads_nothing_even_when_enforced(self):
        self.write_baseline()

        with mock.patch.object(gate_module, "read_baseline") as read:
            with mock.patch.dict(os.environ, {"GITPR_BASELINE_ENABLED": "false"}):
                gate = self.load(required=True)

        read.assert_not_called()
        self.assertFalse(gate.is_active)
        self.assertEqual(gate.warnings, [])

    def test_no_file_is_an_inactive_gate_and_not_an_error(self):
        gate = self.load()

        self.assertFalse(gate.is_active)
        self.assertFalse(gate.is_unusable)
        self.assertTrue(gate.path.endswith(os.path.join(".gitpr", "baseline.json")))
        self.assertEqual(gate.warnings, [])

    def test_the_file_is_applied_and_published_for_the_process(self):
        manifest = self.write_baseline()

        gate = self.load()

        self.assertTrue(gate.is_active)
        self.assertIsNotNone(gate.manifest)
        self.assertEqual(len(gate.manifest.entries), len(manifest.entries))
        self.assertIs(get_active_baseline(), gate.manifest)

    def test_an_inactive_gate_publishes_no_baseline(self):
        gate = self.load(required=False)

        self.assertIsNone(get_active_baseline())
        self.assertFalse(gate.is_active)

    def test_a_tampered_checksum_stops_the_run_and_says_how_to_recover(self):
        self.write_baseline()
        self.tamper(lambda data: data["entries"][0].__setitem__("line_start", 999))

        with self.assertRaises(BaselineError) as caught:
            self.load()

        message = str(caught.exception)
        self.assertIn("baseline.json", message)
        self.assertIn("checksum", message)
        self.assertIn("--recompute", message)
        self.assertIsNone(get_active_baseline())

    def test_the_checksum_guard_can_be_turned_off_and_the_divergence_is_still_reported(self):
        self.write_baseline()
        self.tamper(lambda data: data["entries"][0].__setitem__("line_start", 999))

        with mock.patch.dict(
            os.environ, {"GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH": "false"}
        ):
            gate = self.load()

        self.assertTrue(gate.is_active)
        self.assertEqual(len(gate.warnings), 1)
        self.assertIn("checksum", gate.warnings[0])

    def test_another_fingerprint_version_stops_the_run(self):
        self.write_baseline()
        self.tamper(lambda data: data.__setitem__("fingerprint_version", "99"))

        with self.assertRaises(BaselineError) as caught:
            self.load()

        self.assertIn("fingerprint_version", str(caught.exception))

    def test_a_newer_schema_stops_the_run(self):
        self.write_baseline()
        self.tamper(lambda data: data.__setitem__("schema_version", 99))

        with self.assertRaises(BaselineError) as caught:
            self.load()

        self.assertIn("schema_version", str(caught.exception))

    def test_a_malformed_overrides_file_is_named_rather_than_ignored(self):
        self.write_baseline()
        # A suppression without a reason is exactly the decision §6 refuses.
        self.write_overrides("overrides:\n  suppressions:\n    - scope: rule\n      rule_id: x\n")

        with self.assertRaises(BaselineError) as caught:
            self.load()

        self.assertIn("baseline.overrides.yml", str(caught.exception))

    def test_local_overrides_can_be_refused_with_a_warning(self):
        self.write_baseline()
        self.write_overrides()

        with mock.patch.dict(
            os.environ, {"GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES": "false"}
        ):
            gate = self.load()

        self.assertTrue(gate.is_active)
        self.assertTrue(gate.overrides.is_empty())
        self.assertEqual(len(gate.warnings), 1)
        self.assertIn("GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES", gate.warnings[0])

    def test_the_path_setting_points_the_gate_elsewhere(self):
        elsewhere = os.path.join(self.root, "shared-baseline.json")
        manifest = build_manifest([finding()], repo_path=self.repo)
        write_manifest(manifest, path=elsewhere)

        with mock.patch.dict(os.environ, {"GITPR_BASELINE_PATH": elsewhere}):
            gate = self.load()

        self.assertTrue(gate.is_active)
        self.assertEqual(gate.path, elsewhere)


class TestThePackLayer(GateTestCase):
    """The `baseline:` block of the active pack, as a third layer.

    It reaches the classification from memory — the policy the run already
    resolved — and it is never written into the repository's own file. That is
    the difference between a decision the team made and an opinion the pack
    holds, and it is why `unsuppress` can name where one of them has to be
    edited instead of deleting a line it does not own.
    """

    def publish_pack(self, *, suppressions=(), accepted_debt=()):
        """Publishes a composed policy the way `_resolve_policy_or_die` does.

        Built in memory: the loader/resolver split means composition has no file
        I/O to fake, so a pack is a dataclass carrying the block it declares.
        """
        from src.domain.policy import (
            PackReference,
            PolicySource,
            ResolvedPack,
            set_active_policy,
        )
        from src.domain.policy.policy_resolver import compose_policy
        from src.domain.policy.policy_types import PolicyManifest

        manifest = PolicyManifest(
            name="acme/team-policy",
            version="1.0.0",
            min_gitpr_version=">=1.0.0",
            baseline={
                "suppressions": list(suppressions),
                "accepted_debt": list(accepted_debt),
            },
        )
        policy = compose_policy(
            [
                ResolvedPack(
                    reference=PackReference(
                        name="acme/team-policy",
                        version="1.0.0",
                        source=PolicySource.BUNDLED,
                    ),
                    manifest=manifest,
                )
            ]
        )
        set_active_policy(policy)
        self.addCleanup(set_active_policy, None)
        return policy

    def test_a_pack_that_declares_nothing_leaves_the_layers_alone(self):
        self.write_baseline()
        self.write_overrides()

        gate = self.load()

        self.assertEqual(len(gate.overrides.suppressions), 1)
        self.assertEqual(gate.overrides.suppressions[0].origin, "local")

    def test_a_suppression_from_the_pack_silences_a_finding_with_no_entry(self):
        self.write_baseline([])
        self.publish_pack(
            suppressions=[
                {
                    "scope": "rule",
                    "rule_id": "warning-todo",
                    "reason": "Too noisy for this tree.",
                }
            ]
        )
        gate = self.load()
        item = finding(rule_id="warning-todo", severity="warning")

        compared = classify_findings_for_gate([item], gate, repo_path=self.repo)[0]

        self.assertEqual(compared.baseline_status, BaselineStatus.IGNORED)
        self.assertEqual(compared.applied.origin, "policy:acme/team-policy@1.0.0")
        self.assertEqual(compared.applied.reason, "Too noisy for this tree.")

    def test_the_repository_outranks_the_pack_on_an_equally_specific_scope(self):
        self.write_baseline([])
        self.write_overrides(
            "overrides:\n"
            "  suppressions:\n"
            "    - scope: rule\n"
            "      rule_id: warning-todo\n"
            "      reason: The repository decided this.\n"
        )
        self.publish_pack(
            suppressions=[
                {
                    "scope": "rule",
                    "rule_id": "warning-todo",
                    "reason": "The pack decided this.",
                }
            ]
        )
        gate = self.load()

        compared = classify_findings_for_gate(
            [finding(rule_id="warning-todo")], gate, repo_path=self.repo
        )[0]

        self.assertEqual(compared.applied.origin, "local")
        self.assertEqual(compared.applied.reason, "The repository decided this.")

    def test_turning_local_overrides_off_still_applies_the_packs_layer(self):
        """The switch is about the repository's own file, not about the pack."""
        self.write_baseline([])
        self.write_overrides()
        self.publish_pack(
            suppressions=[
                {
                    "scope": "rule",
                    "rule_id": "warning-todo",
                    "reason": "The pack decided this.",
                }
            ]
        )

        with mock.patch.dict(
            os.environ, {"GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES": "false"}
        ):
            gate = self.load()

        compared = classify_findings_for_gate(
            [finding(rule_id="warning-todo")], gate, repo_path=self.repo
        )[0]
        self.assertEqual(compared.baseline_status, BaselineStatus.IGNORED)
        self.assertEqual(compared.applied.origin, "policy:acme/team-policy@1.0.0")

    def test_debt_from_the_pack_counts_as_accepted_and_owes_nothing_to_the_file(self):
        item = finding()
        self.write_baseline([])
        self.publish_pack(
            accepted_debt=[
                {
                    "fingerprint": compute_fingerprint(item, self.repo),
                    "owner": "platform",
                    "reason": "Migration planned.",
                    "due_date": "2026-12-31",
                }
            ]
        )
        gate = self.load()

        compared = classify_findings_for_gate([item], gate, repo_path=self.repo)[0]

        self.assertEqual(compared.baseline_status, BaselineStatus.ACCEPTED_DEBT)
        self.assertEqual(compared.applied.owner, "platform")
        with open(
            os.path.join(self.repo, ".gitpr", "baseline.json"),
            "r",
            encoding="utf-8",
            errors="replace",
        ) as handle:
            self.assertNotIn("platform", handle.read())


class TestClassification(GateTestCase):
    def test_classifying_without_a_baseline_is_refused(self):
        """A gate with no manifest has no answer, and inventing one lies."""
        gate = self.load(required=False)

        with self.assertRaises(BaselineError):
            classify_findings_for_gate([finding()], gate, repo_path=self.repo)

    def test_what_the_file_records_is_existing_and_the_rest_is_new(self):
        self.write_baseline([finding()])
        gate = self.load()

        compared = classify_findings_for_gate(
            [
                finding(),
                finding("A new secret.", line=42, text="OTHER = 'x'"),
                finding("A new warning.", severity="warning", rule_id="warning-todo",
                        text="TODO: fix"),
            ],
            gate,
            repo_path=self.repo,
        )

        self.assertEqual(
            [item.baseline_status for item in compared],
            [BaselineStatus.EXISTING, BaselineStatus.NEW, BaselineStatus.NEW],
        )

    def test_a_rule_scope_override_reaches_findings_with_no_entry_yet(self):
        self.write_baseline([finding()])
        self.write_overrides()
        gate = self.load()

        compared = classify_findings_for_gate(
            [finding("TODO left behind.", severity="warning", rule_id="warning-todo",
                     text="TODO: fix")],
            gate,
            repo_path=self.repo,
        )

        self.assertEqual(compared[0].baseline_status, BaselineStatus.IGNORED)
        self.assertEqual(compared[0].applied.scope.value, "rule")
        self.assertIn("noisy", compared[0].reason)

    def test_only_the_new_findings_are_scored(self):
        self.write_baseline([finding()])
        gate = self.load()
        compared = classify_findings_for_gate(
            [finding(), finding("Fresh.", line=42, text="OTHER = 'x'")],
            gate,
            repo_path=self.repo,
        )

        scored = new_findings(compared)

        self.assertEqual(len(scored), 1)
        self.assertEqual(scored[0].line_start, 42)

    def test_a_new_warning_does_not_block_and_a_new_error_does(self):
        self.write_baseline([finding()])
        gate = self.load()
        compared = classify_findings_for_gate(
            [
                finding("Old.", line=10),
                finding("New error.", line=42, text="OTHER = 'x'"),
                finding("New warning.", severity="warning", line=43, rule_id="warning-todo",
                        text="TODO"),
            ],
            gate,
            repo_path=self.repo,
        )

        blocking = blocking_errors(compared)

        self.assertEqual([item.finding.message for item in blocking], ["New error."])

    def test_an_existing_error_never_blocks(self):
        self.write_baseline([finding()])
        gate = self.load()

        compared = classify_findings_for_gate([finding()], gate, repo_path=self.repo)

        self.assertTrue(compared[0].is_error())
        self.assertFalse(compared[0].is_blocking)
        self.assertEqual(blocking_errors(compared), [])


class TestStatusLine(GateTestCase):
    def test_nothing_to_say_is_an_empty_line(self):
        self.assertEqual(status_line({}), "")
        self.assertEqual(status_line({"new": 0, "existing": 0}), "")

    def test_the_line_leads_with_what_the_change_added(self):
        line = status_line(
            {"new": 3, "existing": 120, "resolved": 2, "ignored": 0, "accepted_debt": 0}
        )

        self.assertEqual(line, "Baseline: 3 new, 120 existing, 2 resolved")

    def test_the_counts_of_a_classification_can_be_printed_directly(self):
        self.write_baseline([finding()])
        gate = self.load()
        compared = classify_findings_for_gate(
            [finding(), finding("Fresh.", line=42, text="OTHER = 'x'")],
            gate,
            repo_path=self.repo,
        )

        self.assertEqual(status_line(compared), "Baseline: 1 new, 1 existing")


class TestAlerts(GateTestCase):
    def test_a_linter_finding_renders_as_its_own_message(self):
        item = finding("Rule text.")

        self.assertEqual(alert_for(item), "Rule text.")

    def test_a_bridge_finding_renders_the_line_the_linter_rendered(self):
        item = finding("Semicolon required", source="external", rule_id="checkstyle")

        self.assertEqual(
            alert_for(item),
            external_alert_message("checkstyle", "Semicolon required", "src/app.py", 10),
        )

    def test_a_sast_finding_renders_through_the_shared_formatter(self):
        item = finding("Hardcoded key", source="gitleaks", rule_id="aws-key")

        self.assertEqual(
            alert_for(item), "🚨 [Gitleaks:aws-key] Hardcoded key (src/app.py, Line 10)"
        )

    def test_the_status_is_written_in_front_of_the_alert_it_belongs_to(self):
        self.write_baseline([finding()])
        gate = self.load()
        compared = classify_findings_for_gate(
            [finding(), finding("Fresh.", line=42, text="OTHER = 'x'")],
            gate,
            repo_path=self.repo,
        )

        annotated = annotate_alerts(
            {"errors": ["Fresh.", "AWS access key in source."], "warnings": []},
            alert_status_index(compared),
        )

        self.assertEqual(
            annotated["errors"],
            ["[new] Fresh.", "[existing] AWS access key in source."],
        )

    def test_a_line_the_index_does_not_know_is_left_exactly_as_it_was(self):
        compared = []
        alerts = {"errors": [], "warnings": ["⚠️ [semgrep] enabled but not in PATH."]}

        annotated = annotate_alerts(alerts, alert_status_index(compared))

        self.assertEqual(annotated["warnings"], alerts["warnings"])
        self.assertEqual(annotated["errors"], [])

    def test_the_annotation_is_a_copy_and_leaves_the_alerts_alone(self):
        alerts = {"errors": ["Fresh."], "warnings": []}

        annotate_alerts(alerts, {"Fresh.": BaselineStatus.NEW})

        self.assertEqual(alerts["errors"], ["Fresh."])

    def test_a_new_status_wins_when_two_findings_render_the_same_line(self):
        """Hiding a new alert behind an older one loses what a reviewer needed."""
        self.write_baseline([finding()])
        gate = self.load()
        compared = classify_findings_for_gate(
            [finding(), finding("Fresh.", line=42, text="OTHER = 'x'")],
            gate,
            repo_path=self.repo,
        )
        # Both findings collapse onto one rendered line, as a rule whose message
        # carries no line number does.
        for item in compared:
            item.finding.message = "Same line"
        index = alert_status_index(compared)

        self.assertEqual(index, {"Same line": BaselineStatus.NEW})


class TestInformationalEvidence(GateTestCase):
    def test_a_known_finding_carries_no_weight_and_names_its_status(self):
        item = self.classified(finding())

        evidence = informational_evidence(item)

        self.assertEqual(evidence.signal, RiskSignal.BASELINE_FINDING)
        self.assertEqual(evidence.points, 0.0)
        self.assertEqual(evidence.details["status"], "existing")
        self.assertEqual(evidence.details["rule_id"], "sec-aws-key")
        self.assertEqual(evidence.confidence, "high")
        self.assertIn("[existing]", evidence.summary)

    def test_the_decision_behind_it_travels_with_the_evidence(self):
        """Accepted debt is not hidden — it is shown with its owner and deadline."""
        self.write_baseline([])
        item = finding()
        self.write_overrides(
            "overrides:\n"
            "  accepted_debt:\n"
            f"    - fingerprint: {compute_fingerprint(item, self.repo)}\n"
            '      owner: "time-backend"\n'
            '      reason: "Migration is planned for the next quarter."\n'
            '      due_date: "2026-12-31"\n'
        )
        gate = self.load()
        compared = classify_findings_for_gate([item], gate, repo_path=self.repo)[0]

        evidence = informational_evidence(compared)

        self.assertEqual(evidence.details["status"], "accepted_debt")
        self.assertEqual(evidence.details["owner"], "time-backend")
        self.assertEqual(evidence.details["due_date"], "2026-12-31")
        self.assertEqual(
            evidence.details["reason"], "Migration is planned for the next quarter."
        )

    def test_an_ai_finding_is_low_confidence(self):
        """Nothing about an AI finding is as stable as a rule's name."""
        item = finding(source="ai", rule_id=None, category="review")

        evidence = informational_evidence(self.classified(item))

        self.assertEqual(evidence.confidence, "low")
        self.assertIsNone(evidence.details["rule_id"])


class TestAttachingTheEvidence(GateTestCase):
    """The zero-point evidence has to land on the file it belongs to, or nowhere.

    A risk report is read per file, so evidence attached to nothing would be a
    finding quietly dropped from the breakdown — the one outcome the whole
    feature exists to prevent. The other mistake is attaching it to a finding
    that *did* count: a 0-point copy beside a scored one reads as a
    contradiction, and a reviewer who cannot tell which is which stops
    believing the score.
    """

    def risk_for(self, *paths):
        """The risk result the calculator would return for these files."""
        risk = PullRequestRisk(score=0.0, level=RiskLevel.LOW)
        for path in paths:
            risk.files.append(
                FileRisk(
                    file_path=path,
                    score=0.0,
                    level=RiskLevel.LOW,
                    changed_lines=1,
                    changed_hunks=1,
                )
            )
        return risk

    def test_a_finding_the_baseline_knew_lands_on_its_own_file(self):
        item = self.classified(finding(file_path="src/app.py"))
        risk = self.risk_for("src/app.py")

        attached = attach_informational_evidence(risk, [item])

        self.assertEqual(attached, 1)
        evidence = risk.files[0].evidence[0]
        self.assertEqual(evidence.signal, RiskSignal.BASELINE_FINDING)
        self.assertEqual(evidence.points, 0.0)
        self.assertEqual(evidence.details["status"], "existing")

    def test_the_match_ignores_case_and_separators(self):
        """A path is matched the way the risk calculator matches it."""
        item = self.classified(finding(file_path="src/app.py"))
        risk = self.risk_for("src\\App.py")

        self.assertEqual(attach_informational_evidence(risk, [item]), 1)

    def test_a_new_finding_is_left_alone(self):
        """It already scored; a 0-point copy beside it would contradict it."""
        self.write_baseline([])
        item = finding()
        gate = self.load()
        compared = classify_findings_for_gate([item], gate, repo_path=self.repo)
        risk = self.risk_for("src/app.py")

        attached = attach_informational_evidence(risk, compared)

        self.assertEqual(attached, 0)
        self.assertEqual(risk.files[0].evidence, [])

    def test_a_finding_of_a_file_the_risk_does_not_carry_attaches_nothing(self):
        item = self.classified(finding(file_path="src/app.py"))
        risk = self.risk_for("src/other.py")

        self.assertEqual(attach_informational_evidence(risk, [item]), 0)
        self.assertEqual(risk.files[0].evidence, [])


if __name__ == "__main__":
    unittest.main()
