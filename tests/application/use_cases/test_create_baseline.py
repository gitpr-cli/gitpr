"""Writing the baseline, and moving it forward without losing what a human decided.

`create` records a state; `update` is the one that has to be careful. What it
must never do, in order of how much it would cost to get wrong:

- drop a suppression or an accepted debt that was written by hand;
- call a finding gone when the diff never mentioned its file — a narrow diff is
  no evidence about a file it does not touch;
- re-identify a finding behind the reader's back. A fingerprint *is* the
  identity, and only `--recompute` — the command a version bump points at — may
  move an entry to a new one, carrying the decision with it.

The git side and the AI review are stubbed below, so every test here is about
the manifest. The real end-to-end run over a repository is
`tests/integration/test_baseline_effect_on_review_linter_risk.py`.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import date
from unittest import mock

from src.application.use_cases import create_baseline as module
from src.application.use_cases.create_baseline import (
    ai_findings_from_record,
    build_manifest,
    create_baseline,
    update_baseline,
)
from src.domain.baseline import (
    FINGERPRINT_VERSION,
    BaselineError,
    BaselineStatus,
    SuppressionScope,
    compute_fingerprint,
    snippet_hash,
    status_of_entry,
)
from src.domain.finding.finding_types import NormalizedFinding
from src.infrastructure.baseline.local_baseline_repository import (
    baseline_path,
    read_baseline,
    read_manifest,
    write_manifest,
)

TODAY = date(2026, 10, 10)
LATER = date(2026, 11, 1)

DIFF = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
+KEY = "AKIAIOSFODNN7EXAMPLE"
 context
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
        snippet_hash=snippet_hash("KEY = 'x'"),
    )


class BaselineUseCaseTestCase(unittest.TestCase):
    """A repository directory, a stubbed diff, a stubbed linter, a stubbed review."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_create_baseline_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(self.repo)

    def stubs(self, findings=None, diff=DIFF, ai=()):
        """The diff, the linter and the AI half, with answers this test chose.

        The review is always stubbed, never left to the real reader: the cache
        it would consult belongs to whoever is running the suite, and a test
        whose result depends on that is a test that fails on someone else's
        machine for no reason at all.
        """
        patches = [
            mock.patch.object(module, "current_diff", return_value=diff),
            mock.patch.object(
                module,
                "collect_linter_findings",
                side_effect=lambda text, path=None: list(
                    [finding()] if findings is None else findings
                ),
            ),
            mock.patch.object(
                module, "_ai_review_findings", return_value=(list(ai), [])
            ),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def create(self, **kwargs):
        return create_baseline(repo_path=self.repo, today=TODAY, **kwargs)

    def update(self, **kwargs):
        return update_baseline(
            repo_path=self.repo, today=kwargs.pop("today", LATER), **kwargs
        )

    def read(self):
        """The manifest on disk, asserting it is one this build can apply."""
        manifest, problems = read_manifest(self.repo)
        self.assertEqual(problems, [])
        return manifest

    def entry_for(self, item):
        manifest = self.read()
        entry = manifest.entry_for(compute_fingerprint(item, self.repo))
        self.assertIsNotNone(entry, "the entry should be in the baseline")
        return entry

    def decide_on(self, item, decide):
        """Records a decision on an entry the way `baseline suppress` would."""
        manifest = self.read()
        entry = manifest.entry_for(compute_fingerprint(item, self.repo))
        self.assertIsNotNone(entry, "the entry should be in the baseline")
        decide(entry)
        write_manifest(manifest, self.repo)
        return entry

    def stale_every_fingerprint(self):
        """What a `FINGERPRINT_VERSION` bump leaves behind: digests this build cannot make."""
        manifest = self.read()
        for entry in manifest.entries:
            entry.fingerprint = "sha256:" + "0" * 64
        manifest.fingerprint_version = "99"
        write_manifest(manifest, self.repo)

    def tamper(self, mutate):
        """Edits the written file without recomputing its checksum."""
        path = baseline_path(self.repo)
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
        mutate(data)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2)

    def raw(self):
        with open(baseline_path(self.repo), "rb") as handle:
            return handle.read()

    def suppress(self, entry):
        entry.suppressed = True
        entry.suppression_reason = "Synthetic secret in a fixture."
        entry.suppression_scope = SuppressionScope.FINDING
        entry.suppressed_by = "alice"


class TestBuildManifest(BaselineUseCaseTestCase):
    def test_every_recorded_finding_is_stored_as_existing(self):
        manifest = build_manifest([finding()], repo_path=self.repo, today=TODAY)

        self.assertEqual(len(manifest.entries), 1)
        entry = manifest.entries[0]
        self.assertEqual(entry.status, BaselineStatus.EXISTING)
        self.assertEqual(entry.first_seen_date, "2026-10-10")
        self.assertEqual(entry.rule_id, "sec-aws-key")
        self.assertFalse(entry.low_confidence)

    def test_the_header_names_the_build_that_wrote_it(self):
        from src.updater import __version__

        manifest = build_manifest([finding()], repo_path=self.repo, today=TODAY)

        self.assertEqual(manifest.fingerprint_version, FINGERPRINT_VERSION)
        self.assertEqual(manifest.schema_version, 1)
        self.assertEqual(manifest.gitpr_version, __version__)
        self.assertEqual(manifest.created_at, manifest.updated_at)
        self.assertIsNone(manifest.policy_name)

    def test_a_finding_with_no_rule_id_is_marked_low_confidence(self):
        manifest = build_manifest(
            [finding(source="ai", rule_id=None, category="review")],
            repo_path=self.repo,
            today=TODAY,
        )

        self.assertTrue(manifest.entries[0].low_confidence)

    def test_the_provenance_names_the_command_that_wrote_the_entry(self):
        manifest = build_manifest([finding()], repo_path=self.repo, today=TODAY)

        self.assertEqual(
            manifest.entries[0].provenance,
            {"origin": "local", "command": "baseline create", "policy": None},
        )


class TestCreate(BaselineUseCaseTestCase):
    def test_the_file_is_written_and_every_finding_reads_new(self):
        """On a fresh repository, "new" is the team accepting what is there."""
        self.stubs()

        run = self.create()

        self.assertTrue(run.created)
        self.assertEqual(run.counts["new"], 1)
        self.assertTrue(os.path.isfile(baseline_path(self.repo)))
        self.assertEqual(len(self.read().entries), 1)

    def test_the_file_it_writes_is_usable_as_written(self):
        self.stubs()

        self.create()

        snapshot = read_baseline(self.repo)
        self.assertTrue(snapshot.is_usable)
        self.assertEqual(snapshot.problems, [])

    def test_an_empty_diff_is_refused_rather_than_recorded(self):
        self.stubs(diff="   \n")

        with self.assertRaises(BaselineError) as caught:
            self.create()

        self.assertIn("--base", str(caught.exception))
        self.assertFalse(os.path.exists(baseline_path(self.repo)))

    def test_replacing_a_baseline_reports_the_decisions_it_drops(self):
        self.stubs()
        self.create()
        self.decide_on(finding(), self.suppress)

        run = self.create()

        self.assertFalse(run.created)
        self.assertTrue(
            any("suppression" in warning for warning in run.warnings), run.warnings
        )
        self.assertFalse(self.entry_for(finding()).suppressed)

    def test_the_date_the_baseline_was_first_written_survives_a_recreate(self):
        self.stubs()
        first = self.create()

        second = self.create()

        self.assertEqual(second.manifest.created_at, first.manifest.created_at)

    def test_the_findings_of_a_review_are_recorded_alongside_the_linter_ai_ones(self):
        self.stubs(
            ai=[finding("Deep coupling.", rule_id=None, source="ai", category="review")]
        )

        run = self.create()

        self.assertEqual(run.ai_findings, 1)
        self.assertEqual(len(self.read().entries), 2)


class TestUpdate(BaselineUseCaseTestCase):
    def test_a_finding_seen_again_keeps_the_date_it_was_first_seen(self):
        self.stubs()
        self.create()
        first = self.entry_for(finding()).first_seen_date

        self.update()

        entry = self.entry_for(finding())
        self.assertEqual(entry.first_seen_date, first)
        self.assertEqual(entry.last_seen_date, "2026-11-01")
        self.assertEqual(entry.status, BaselineStatus.EXISTING)

    def test_a_finding_whose_file_the_diff_touched_and_is_gone_is_resolved(self):
        self.stubs()
        self.create()
        self.stubs(findings=[])  # the same file, with the finding no longer there

        self.update()

        entry = self.entry_for(finding())
        self.assertEqual(entry.status, BaselineStatus.RESOLVED)
        self.assertEqual(entry.resolved_at, "2026-11-01")

    def test_a_finding_in_a_file_the_diff_never_touched_keeps_its_status(self):
        """A narrow diff is not evidence about a file it does not mention."""
        self.stubs()
        self.create()
        self.stubs(findings=[], diff=DIFF.replace("src/app.py", "src/other.py"))

        self.update()

        entry = self.entry_for(finding())
        self.assertEqual(entry.status, BaselineStatus.EXISTING)
        self.assertIsNone(entry.resolved_at)

    def test_a_finding_that_comes_back_is_live_again(self):
        self.stubs()
        self.create()
        self.stubs(findings=[])
        self.update()
        self.assertEqual(self.entry_for(finding()).status, BaselineStatus.RESOLVED)

        self.stubs()
        self.update()

        entry = self.entry_for(finding())
        self.assertEqual(entry.status, BaselineStatus.EXISTING)
        self.assertIsNone(entry.resolved_at)

    def test_a_resolution_date_is_stamped_once_and_never_moves(self):
        self.stubs()
        self.create()
        self.stubs(findings=[])
        self.update()
        resolved_at = self.entry_for(finding()).resolved_at

        self.update(today=date(2026, 12, 25))

        self.assertEqual(self.entry_for(finding()).resolved_at, resolved_at)

    def test_an_empty_diff_writes_nothing_at_all(self):
        self.stubs()
        self.create()
        before = self.raw()
        self.stubs(diff="")

        run = self.update()

        self.assertFalse(run.written)
        self.assertEqual(self.raw(), before)
        self.assertTrue(any("no diff" in warning for warning in run.warnings))

    def test_an_unwritten_update_still_reports_the_manifest_in_force(self):
        self.stubs()
        self.create()
        self.stubs(diff="")

        run = self.update()

        self.assertEqual(len(run.manifest.entries), 1)

    def test_a_file_that_cannot_be_applied_stops_a_plain_update(self):
        self.stubs()
        self.create()
        self.tamper(lambda data: data.__setitem__("fingerprint_version", "99"))

        with self.assertRaises(BaselineError) as caught:
            self.update()

        self.assertIn("--recompute", str(caught.exception))

    def test_recompute_reads_the_file_a_plain_update_refuses(self):
        self.stubs()
        self.create()
        self.tamper(lambda data: data.__setitem__("fingerprint_version", "99"))

        run = self.update(recompute=True)

        self.assertTrue(run.warnings, "the repair path reports what it read")
        self.assertEqual(len(self.read().entries), 1)

    def test_recompute_carries_a_suppression_onto_the_new_fingerprint(self):
        """The version bump case: same finding, new identity, same decision."""
        self.stubs()
        self.create()
        self.decide_on(finding(), self.suppress)
        self.stale_every_fingerprint()

        run = self.update(recompute=True)

        self.assertEqual(run.warnings, [])
        self.assertEqual(self.read().fingerprint_version, FINGERPRINT_VERSION)
        entry = self.entry_for(finding())
        self.assertTrue(entry.suppressed)
        self.assertEqual(entry.suppression_reason, "Synthetic secret in a fixture.")
        self.assertEqual(entry.suppressed_by, "alice")
        self.assertEqual(status_of_entry(entry).status, BaselineStatus.IGNORED)

    def test_recompute_does_not_carry_a_resolution_onto_a_new_fingerprint(self):
        """The location index keeps a decision alive; it does not resurrect a closed one."""
        self.stubs()
        self.create()
        self.stubs(findings=[])
        self.update()
        self.stale_every_fingerprint()

        self.stubs()
        self.update(recompute=True)

        fresh = self.entry_for(finding())
        self.assertEqual(fresh.status, BaselineStatus.EXISTING)
        self.assertIsNone(fresh.resolved_at)


class TestAiFindingsFromRecord(unittest.TestCase):
    def test_a_review_without_a_findings_array_yields_nothing_and_says_nothing(self):
        findings, warnings = ai_findings_from_record({"response": {"review": "prose"}})

        self.assertEqual(findings, [])
        self.assertEqual(warnings, [])

    def test_a_findings_key_that_is_not_a_list_is_reported(self):
        findings, warnings = ai_findings_from_record({"response": {"findings": "nope"}})

        self.assertEqual(findings, [])
        self.assertEqual(len(warnings), 1)

    def test_a_well_formed_entry_becomes_a_finding(self):
        findings, warnings = ai_findings_from_record(
            {
                "response": {
                    "findings": [
                        {
                            "file_path": "src/app.py",
                            "line_start": 10,
                            "line_end": 12,
                            "severity": "error",
                            "category": "security",
                            "message": "The token is logged.",
                        }
                    ]
                }
            }
        )

        self.assertEqual(warnings, [])
        self.assertEqual(len(findings), 1)
        item = findings[0]
        self.assertEqual(item.source, "ai")
        self.assertIsNone(item.rule_id)
        self.assertIsNone(
            item.snippet_hash,
            "the review has no parsed line index, so any digest here would be fiction",
        )
        self.assertEqual((item.line_start, item.line_end), (10, 12))
        self.assertEqual(item.severity, "error")

    def test_a_malformed_entry_is_dropped_with_its_index_and_the_rest_survives(self):
        findings, warnings = ai_findings_from_record(
            {
                "response": {
                    "findings": [
                        {"line_start": 3, "message": "no file"},
                        {"file_path": "src/app.py", "message": "no line"},
                        {"file_path": "src/app.py", "line_start": 1, "message": ""},
                        {"file_path": "src/app.py", "line_start": 1, "message": "fine"},
                    ]
                }
            }
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(len(warnings), 3)
        self.assertIn("#1", warnings[0])
        self.assertIn("#2", warnings[1])
        self.assertIn("#3", warnings[2])

    def test_a_missing_category_falls_back_to_the_one_the_identity_uses(self):
        findings, _ = ai_findings_from_record(
            {
                "response": {
                    "findings": [{"file_path": "a.py", "line_start": 1, "message": "m"}]
                }
            }
        )

        self.assertEqual(findings[0].category, "review")
        self.assertEqual(findings[0].severity, "warning")


class TestTheCachedReview(BaselineUseCaseTestCase):
    def test_a_cached_review_of_another_diff_is_not_used(self):
        record = {"diff": "some other diff", "response": {"findings": []}}
        with mock.patch.object(module, "_last_review_record", return_value=record):
            findings, warnings = module._ai_review_findings(DIFF, False, self.repo)

        self.assertEqual(findings, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("--refresh", warnings[0])

    def test_a_cached_review_of_this_very_diff_is_used(self):
        record = {
            "diff": DIFF,
            "response": {
                "findings": [{"file_path": "a.py", "line_start": 1, "message": "m"}]
            },
        }
        with mock.patch.object(module, "_last_review_record", return_value=record):
            findings, warnings = module._ai_review_findings(DIFF, False, self.repo)

        self.assertEqual(len(findings), 1)
        self.assertEqual(warnings, [])

    def test_refresh_reviews_the_current_diff_instead(self):
        seen = {}

        def fake_review(action, action_type, diff_text, provider, **kwargs):
            seen["diff"] = diff_text
            return {"review": "prose", "findings": []}

        with mock.patch("src.core.generate_pr_content", side_effect=fake_review):
            findings, warnings = module._ai_review_findings(DIFF, True, self.repo)

        self.assertEqual(seen["diff"], DIFF)
        self.assertEqual(findings, [])
        self.assertEqual(len(warnings), 1)

    def test_a_review_that_returns_nothing_is_reported(self):
        with mock.patch("src.core.generate_pr_content", return_value=None):
            findings, warnings = module._ai_review_findings(DIFF, True, self.repo)

        self.assertEqual(findings, [])
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
