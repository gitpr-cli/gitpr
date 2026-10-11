"""The read-only digest: what the record says, in one document.

This is the surface an IDE agent reads instead of a terminal, so the promise it
has to keep is different from `gitpr baseline show`'s. Nothing here may run the
linter or the AI, nothing may write, and an unusable file must come back *as an
answer* — "the record is there and the gate would refuse it" is one of the things
the caller came to find out, and a call that failed instead would leave it
without the difference between a repository with no baseline and a broken one.

The four `GITPR_BASELINE_*` keys are pinned for the same reason the gate tests
pin them: a developer whose own `~/.gitpr/.env` turns the feature off should not
see this file fail for a reason that has nothing to do with the code.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from src.application.use_cases.baseline_summary import TOP_RULES, baseline_summary
from src.application.use_cases.create_baseline import build_manifest
from src.domain.baseline import set_active_baseline, snippet_hash
from src.domain.finding.finding_types import NormalizedFinding
from src.infrastructure.baseline.local_baseline_repository import (
    overrides_path,
    write_manifest,
)

BASELINE_ENV = {
    "GITPR_BASELINE_ENABLED": "true",
    "GITPR_BASELINE_PATH": "",
    "GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH": "true",
    "GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES": "true",
}

# A debt whose deadline has passed, declared in the overrides file rather than on
# the entry: the case that used to be invisible to every overdue check.
PAST_DEBT_OVERRIDES = """overrides:
  suppressions:
    - scope: rule
      rule_id: "warning-todo"
      reason: "Too noisy for this legacy tree."
  accepted_debt:
    - fingerprint: "{fingerprint}"
      owner: "time-backend"
      reason: "Migration planned for the next quarter."
      due_date: "2020-01-31"
"""


def finding(
    *,
    rule_id="sec-aws-key",
    category="security",
    file_path="src/app.py",
    line=10,
    message="AWS access key in source.",
    text="AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'",
):
    """A finding of the shape the linter's side channel produces."""
    return NormalizedFinding(
        severity="error",
        category=category,
        file_path=file_path,
        line_start=line,
        line_end=line,
        message=message,
        source="linter",
        rule_id=rule_id,
        snippet_hash=snippet_hash(text),
    )


class SummaryTestCase(unittest.TestCase):
    """A repository directory, and the settings pinned."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_baseline_summary_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(self.repo)

        self.env = mock.patch.dict(os.environ, dict(BASELINE_ENV))
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(set_active_baseline, None)

    def write_baseline(self, findings):
        """Writes the file the way `gitpr baseline create` would."""
        manifest = build_manifest(list(findings), repo_path=self.repo)
        write_manifest(manifest, self.repo)
        return manifest

    def fingerprint(self, item):
        """The id `gitpr baseline create` would have written for this finding."""
        from src.domain.baseline import compute_fingerprint

        return compute_fingerprint(item, self.repo)

    def write_overrides(self, text):
        path = overrides_path(self.repo)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        return path

    def summary(self, **kwargs):
        return baseline_summary(self.repo, **kwargs)


class TestTheRecordItself(SummaryTestCase):
    def test_a_repository_with_no_baseline_answers_with_a_zeroed_record(self):
        """Absence is an answer with a shape, not an error and not a raise."""
        summary = self.summary()

        self.assertEqual(summary["status"], "success")
        self.assertFalse(summary["exists"])
        self.assertFalse(summary["usable"])
        self.assertEqual(summary["checksum"], "absent")
        self.assertIsNone(summary["manifest"])
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["problems"], [])
        self.assertEqual(summary["warnings"], [])
        self.assertFalse(summary["enabled"] is None)

    def test_the_counts_read_the_record_through_the_override_layers(self):
        """A decision that lives in the overrides file is a decision here too."""
        key = finding(rule_id="sec-aws-key")
        todo = finding(rule_id="warning-todo", category="lint", line=12)
        other = finding(rule_id="php-tabs", category="style", line=20)
        self.write_baseline([key, todo, other])
        self.write_overrides(PAST_DEBT_OVERRIDES.format(fingerprint=self.fingerprint(key)))

        summary = self.summary()

        self.assertEqual(summary["counts"]["ignored"], 1)
        self.assertEqual(summary["counts"]["accepted_debt"], 1)
        self.assertEqual(summary["counts"]["existing"], 1)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["decisions"]["by_origin"], {"local": 2})
        self.assertEqual(summary["decisions"]["by_scope"]["rule"], 1)
        self.assertEqual(summary["decisions"]["by_scope"]["finding"], 1)

    def test_the_deadline_a_layer_declared_is_what_makes_the_debt_late(self):
        """The owner and the date belong to the layer that won, not to the file."""
        key = finding(rule_id="sec-aws-key")
        self.write_baseline([key])
        self.write_overrides(PAST_DEBT_OVERRIDES.format(fingerprint=self.fingerprint(key)))

        summary = self.summary()

        self.assertEqual(summary["debt"]["total"], 1)
        self.assertEqual(summary["debt"]["undated"], 0)
        self.assertEqual(len(summary["debt"]["overdue"]), 1)
        late = summary["debt"]["overdue"][0]
        self.assertEqual(late["owner"], "time-backend")
        self.assertEqual(late["due_date"], "2020-01-31")
        self.assertEqual(late["origin"], "local")
        self.assertEqual(late["fingerprint"], self.fingerprint(key))

    def test_a_debt_with_no_deadline_is_counted_but_not_late(self):
        """A debt nobody dated is owed — it just cannot be late."""
        key = finding(rule_id="sec-aws-key")
        self.write_baseline([key])
        self.write_overrides(
            "overrides:\n"
            "  accepted_debt:\n"
            '    - fingerprint: "%s"\n'
            '      owner: "platform"\n'
            '      reason: "No date agreed yet."\n' % self.fingerprint(key)
        )

        summary = self.summary()

        self.assertEqual(summary["debt"]["total"], 1)
        self.assertEqual(summary["debt"]["undated"], 1)
        self.assertEqual(summary["debt"]["overdue"], [])

    def test_the_top_rules_put_the_noisiest_first_and_stop_at_ten(self):
        """A digest that listed every rule would be the file again."""
        findings = []
        for index in range(12):
            for occurrence in range(index + 1):
                findings.append(
                    finding(rule_id=f"rule-{index:02d}", line=100 + occurrence)
                )
        self.write_baseline(findings)

        summary = self.summary()

        self.assertEqual(len(summary["rules"]), TOP_RULES)
        self.assertEqual(summary["rules"][0], {"rule_id": "rule-11", "count": 12})
        self.assertEqual(summary["rules"][-1], {"rule_id": "rule-02", "count": 3})

    def test_a_finding_with_no_rule_counts_under_its_category(self):
        """The identity the fingerprint falls back to is the identity shown."""
        self.write_baseline([finding(rule_id=None, category="Security")])

        summary = self.summary()

        self.assertEqual(summary["rules"], [{"rule_id": "category:security", "count": 1}])

    def test_the_master_switch_is_reported_though_the_file_is_still_read(self):
        """The record is readable either way; the flag says whether runs use it."""
        self.write_baseline([finding()])
        with mock.patch.dict(os.environ, {"GITPR_BASELINE_ENABLED": "false"}):
            summary = self.summary()

        self.assertFalse(summary["enabled"])
        self.assertTrue(summary["usable"])
        self.assertEqual(summary["total"], 1)


class TestAFileThatCannotBeApplied(SummaryTestCase):
    def test_a_divergent_checksum_is_reported_with_the_file_left_unapplied(self):
        """The refusal is the answer, and it is not a crash."""
        manifest = self.write_baseline([finding()])
        self._tamper(os.path.join(self.repo, ".gitpr", "baseline.json"), manifest)

        summary = self.summary()

        self.assertEqual(summary["checksum"], "divergent")
        self.assertTrue(summary["exists"])
        self.assertFalse(summary["usable"])
        self.assertEqual(summary["total"], 0)
        self.assertTrue(any("checksum" in problem for problem in summary["problems"]))

    def test_with_the_guard_off_the_file_is_read_and_the_divergence_warned(self):
        """`GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH=false` applies it."""
        manifest = self.write_baseline([finding()])
        self._tamper(os.path.join(self.repo, ".gitpr", "baseline.json"), manifest)

        with mock.patch.dict(
            os.environ, {"GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH": "false"}
        ):
            summary = self.summary()

        self.assertEqual(summary["checksum"], "divergent")
        self.assertTrue(summary["usable"])
        self.assertEqual(summary["total"], 1)
        self.assertTrue(any("checksum" in warning for warning in summary["warnings"]))

    def test_an_unreadable_overrides_file_is_a_warning_not_a_failure(self):
        """A decision a human wrote is never dropped in silence — nor fatal here."""
        self.write_baseline([finding()])
        path = self.write_overrides("overrides:\n  suppressions:\n    - scope: nonsense\n")

        summary = self.summary()

        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["total"], 1)
        self.assertTrue(any(path in warning for warning in summary["warnings"]))

    def _tamper(self, path, manifest):
        """Edits the file the way a hand-editor would: the content moves, the digest does not."""
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        data["entries"][0]["line_start"] = data["entries"][0]["line_start"] + 1
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle)


class TestThePackLayer(SummaryTestCase):
    def test_a_pack_declared_debt_is_counted_and_attributed_to_the_pack(self):
        """The pack's opinion is applied, and it is never written to the file."""
        key = finding(rule_id="sec-aws-key")
        manifest = self.write_baseline([key])
        before = _read(os.path.join(self.repo, ".gitpr", "baseline.json"))
        self.publish_pack(
            suppressions=[
                {
                    "scope": "rule",
                    "rule_id": "warning-todo",
                    "reason": "The team decided this rule is an aid, not a gate.",
                }
            ],
            accepted_debt=[
                {
                    "fingerprint": self.fingerprint(key),
                    "owner": "platform",
                    "reason": "Migration planned for the next quarter.",
                    "due_date": "2020-01-31",
                }
            ],
        )

        summary = self.summary()

        self.assertEqual(len(manifest.entries), 1)
        self.assertEqual(summary["counts"]["accepted_debt"], 1)
        self.assertEqual(
            summary["decisions"]["by_origin"], {"policy:acme/team-policy@1.0.0": 1}
        )
        self.assertEqual(
            summary["debt"]["overdue"][0]["origin"], "policy:acme/team-policy@1.0.0"
        )
        self.assertEqual(summary["debt"]["overdue"][0]["owner"], "platform")
        # The record is the repository's own: the pack's layer is in memory only.
        self.assertEqual(_read(os.path.join(self.repo, ".gitpr", "baseline.json")), before)
        self.assertEqual(summary["warnings"], [])

    def publish_pack(self, *, suppressions=(), accepted_debt=()):
        """Installs an active policy whose manifest carries a `baseline:` block."""
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


class TestReadOnly(SummaryTestCase):
    def test_the_summary_writes_nothing(self):
        """The whole promise of the surface: it opens, counts, and stops."""
        key = finding()
        self.write_baseline([key])
        overrides = self.write_overrides(
            PAST_DEBT_OVERRIDES.format(fingerprint=self.fingerprint(key))
        )
        baseline = os.path.join(self.repo, ".gitpr", "baseline.json")
        before = (_read(baseline), _read(overrides))

        self.summary()

        self.assertEqual((_read(baseline), _read(overrides)), before)
        self.assertFalse(os.path.exists(baseline + ".tmp"))


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()
