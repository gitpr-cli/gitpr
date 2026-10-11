"""Recording a decision about a finding, and taking it back.

`suppress` and `unsuppress` are the only commands that write a human's decision
into the record, so what these tests are about is the two ways that record could
become a lie:

- a decision written where the classification does not look for it. A `rule`
  scope stored on one entry would silence one finding while claiming to silence
  a rule — the entry is not what a wider scope is matched against;
- a decision removed by a command that had no right to remove it. A `file`
  suppression is a statement about every finding in that file, and `unsuppress`
  names one finding.

The path is real throughout: the file is written to a temporary directory and
read back, because "the decision lands in the file the gate reads" is the
property under test and a stubbed writer would prove nothing about it. Only git
and the configuration are stubbed, and only where the module asks for them.
"""

import os
import shutil
import tempfile
import unittest
from datetime import date
from unittest import mock

from src.application.use_cases import suppress_finding as module
from src.application.use_cases.suppress_finding import (
    suppress_finding,
    unsuppress_finding,
)
from src.domain.baseline import (
    FINGERPRINT_VERSION,
    AcceptedDebt,
    BaselineEntry,
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    Overrides,
    Suppression,
    SuppressionScope,
    overdue_debt,
    status_of_entry,
)
from src.infrastructure.baseline.local_baseline_repository import (
    OVERRIDES_NAME,
    baseline_path,
    overrides_path,
    read_manifest,
    read_overrides,
    write_manifest,
    write_overrides,
)

TODAY = date(2026, 10, 10)
RULE = "legacy-no-eval"
LEGACY_FILE = "app/legacy.py"


def fingerprint(char: str) -> str:
    """A well-formed digest, so the tests do not depend on the fingerprint itself."""
    return "sha256:" + char * 64


def entry(
    char="a",
    *,
    rule_id: str | None = RULE,
    category="security",
    file_path=LEGACY_FILE,
    line=3,
    status=BaselineStatus.EXISTING,
):
    """One acknowledged finding, as `baseline create` would have written it."""
    return BaselineEntry(
        fingerprint=fingerprint(char),
        rule_id=rule_id,
        category=category,
        file_path=file_path,
        line_start=line,
        line_end=line,
        severity="error",
        source="linter",
        status=status,
        first_seen_date="2026-10-01",
        last_seen_date="2026-10-01",
    )


class SuppressUseCaseTestCase(unittest.TestCase):
    """A repository directory with a baseline on disk, and a pinned identity."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_suppress_finding_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(self.repo)

    def write_baseline(self, *entries, path=None):
        """Puts a manifest on disk and returns the entries as they were written."""
        manifest = BaselineManifest(
            entries=list(entries),
            fingerprint_version=FINGERPRINT_VERSION,
            gitpr_version="0.0.37",
            created_at="2026-10-01T00:00:00",
            updated_at="2026-10-01T00:00:00",
        )
        write_manifest(manifest, self.repo, path)
        return manifest.entries

    def suppress(self, identifier, **kwargs):
        kwargs.setdefault("by", "alice")
        kwargs.setdefault("today", TODAY)
        return suppress_finding(identifier, repo_path=self.repo, **kwargs)

    def unsuppress(self, identifier):
        return unsuppress_finding(identifier, repo_path=self.repo)

    def stored(self):
        """The manifest as it is on disk, asserting this build can still apply it."""
        manifest, problems = read_manifest(self.repo)
        self.assertEqual(problems, [])
        return manifest

    def entry_for(self, char="a"):
        found = self.stored().entry_for(fingerprint(char))
        self.assertIsNotNone(found, "the entry should still be in the baseline")
        return found

    def overrides(self):
        """The overrides file as it is on disk, plus its path."""
        stored, path = read_overrides(self.repo)
        return stored, path

    def raw_baseline(self):
        with open(baseline_path(self.repo), "rb") as handle:
            return handle.read()

    def allow_local_overrides(self, allowed):
        """Pins what `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` reads as."""
        settings = {"allow_local_overrides": allowed}
        patcher = mock.patch(
            "src.config.get_baseline_settings", return_value=settings
        )
        patcher.start()
        self.addCleanup(patcher.stop)


class TestRecordingASuppression(SuppressUseCaseTestCase):
    def test_a_finding_scope_is_recorded_on_the_entry_the_gate_reads(self):
        """The decision has to sit where the classification looks, or it is prose."""
        self.write_baseline(entry())

        result = self.suppress(
            fingerprint("a"), reason="Synthetic eval in a boot fixture."
        )

        self.assertIsNone(result.override, "a finding scope is not an override")
        self.assertIsNotNone(result.entry)
        self.assertEqual(result.path.replace("\\", "/"), baseline_path(self.repo).replace("\\", "/"))
        stored = self.entry_for()
        self.assertTrue(stored.suppressed)
        self.assertEqual(stored.suppression_reason, "Synthetic eval in a boot fixture.")
        self.assertEqual(stored.suppression_scope, SuppressionScope.FINDING)
        self.assertEqual(stored.suppressed_by, "alice")
        self.assertEqual(stored.suppressed_at, "2026-10-10")
        applied = status_of_entry(stored)
        self.assertEqual(applied.status, BaselineStatus.IGNORED)
        self.assertEqual(applied.reason, "Synthetic eval in a boot fixture.")

    def test_a_short_id_is_enough_to_name_a_finding(self):
        self.write_baseline(entry())

        result = self.suppress("sha256:aaa", reason="Fixture.")

        self.assertEqual(result.entry.fingerprint, fingerprint("a"))

    def test_the_provenance_names_the_command_that_wrote_it(self):
        self.write_baseline(entry())

        self.suppress(fingerprint("a"), reason="Fixture.")

        provenance = self.entry_for().provenance
        self.assertEqual(provenance["command"], "baseline suppress")
        self.assertEqual(provenance["origin"], "local")

    def test_the_decision_replaces_the_one_the_entry_already_carried(self):
        """An entry states one decision. Two of them is a file nobody can read."""
        self.write_baseline(entry())
        self.suppress(
            fingerprint("a"), reason="Migration planned.", debt=True, owner="backend"
        )

        self.suppress(fingerprint("a"), reason="Synthetic eval in a boot fixture.")

        stored = self.entry_for()
        self.assertFalse(stored.is_debt())
        self.assertIsNone(stored.accepted_debt_owner)
        self.assertIsNone(stored.accepted_debt_reason)

    def test_the_git_identity_is_used_when_no_author_is_given(self):
        self.write_baseline(entry())
        patcher = mock.patch("src.cache.get_git_user_info", return_value=("bob", "b@x"))
        patcher.start()
        self.addCleanup(patcher.stop)

        suppress_finding(
            fingerprint("a"), reason="Fixture.", repo_path=self.repo, today=TODAY
        )

        self.assertEqual(self.entry_for().suppressed_by, "bob")

    def test_a_reason_is_required(self):
        self.write_baseline(entry())

        with self.assertRaises(BaselineError) as caught:
            self.suppress(fingerprint("a"), reason="   ")

        self.assertIn("reason", str(caught.exception).lower())
        self.assertFalse(self.entry_for().suppressed)

    def test_the_decision_lands_in_the_file_the_repository_reads(self):
        """`GITPR_BASELINE_PATH` names the file; a command that wrote another
        one would record a decision nobody is judged against."""
        elsewhere = os.path.join(self.repo, "audit", "baseline.json")
        self.write_baseline(entry(), path=elsewhere)

        result = suppress_finding(
            fingerprint("a"),
            reason="Fixture.",
            repo_path=self.repo,
            configured_path=elsewhere,
            by="alice",
            today=TODAY,
        )

        self.assertEqual(result.path, elsewhere)
        self.assertTrue(os.path.isfile(elsewhere))
        self.assertFalse(os.path.exists(baseline_path(self.repo)))
        manifest, problems = read_manifest(self.repo, elsewhere)
        self.assertEqual(problems, [])
        self.assertTrue(manifest.entry_for(fingerprint("a")).suppressed)


class TestAcceptedDebt(SuppressUseCaseTestCase):
    def test_debt_is_recorded_on_the_entry_with_its_owner_and_its_promise(self):
        self.write_baseline(entry())

        result = self.suppress(
            fingerprint("a"),
            reason="Rewrite in progress.",
            debt=True,
            owner="backend",
            due_date="2026-12-31",
        )

        self.assertTrue(result.is_debt)
        stored = self.entry_for()
        self.assertEqual(stored.status, BaselineStatus.ACCEPTED_DEBT)
        self.assertEqual(stored.accepted_debt_owner, "backend")
        self.assertEqual(stored.accepted_debt_reason, "Rewrite in progress.")
        self.assertEqual(stored.accepted_debt_due_date, "2026-12-31")
        applied = status_of_entry(stored)
        self.assertEqual(applied.status, BaselineStatus.ACCEPTED_DEBT)
        self.assertEqual(applied.owner, "backend")
        self.assertEqual(applied.due_date, "2026-12-31")

    def test_debt_without_an_owner_is_refused(self):
        """A debt nobody owns is not accepted — it is an unsuppression with a story."""
        self.write_baseline(entry())

        with self.assertRaises(BaselineError) as caught:
            self.suppress(fingerprint("a"), reason="Later.", debt=True)

        self.assertIn("owner", str(caught.exception).lower())
        self.assertIsNone(self.entry_for().accepted_debt_owner)

    def test_debt_cannot_be_assigned_to_a_rule(self):
        self.write_baseline(entry())

        with self.assertRaises(BaselineError) as caught:
            self.suppress(
                fingerprint("a"),
                reason="Later.",
                scope=SuppressionScope.RULE,
                debt=True,
                owner="backend",
            )

        self.assertIn("--debt", str(caught.exception))

    def test_a_deadline_that_has_passed_is_recorded_and_read_back_as_overdue(self):
        """The past is a warning the readers raise, never a write this refuses."""
        self.write_baseline(entry())

        self.suppress(
            fingerprint("a"),
            reason="Migration planned.",
            debt=True,
            owner="backend",
            due_date="2026-09-01",
        )

        stored = self.entry_for()
        self.assertEqual(stored.accepted_debt_due_date, "2026-09-01")
        self.assertEqual(overdue_debt([stored], TODAY), [stored])

    def test_the_deadline_is_optional(self):
        self.write_baseline(entry())

        self.suppress(
            fingerprint("a"), reason="Migration planned.", debt=True, owner="backend"
        )

        self.assertIsNone(self.entry_for().accepted_debt_due_date)


class TestWiderScopes(SuppressUseCaseTestCase):
    def test_a_rule_scope_is_written_to_the_overrides_file_and_not_the_entry(self):
        self.write_baseline(entry())

        result = self.suppress(
            fingerprint("a"),
            reason="Noisy rule in legacy code.",
            scope=SuppressionScope.RULE,
        )

        self.assertIsNotNone(result.override)
        self.assertIsNone(result.entry)
        stored = self.entry_for()
        self.assertFalse(stored.suppressed, "the entry must not claim a rule decision")
        self.assertEqual(stored.status, BaselineStatus.EXISTING)
        overrides, path = self.overrides()
        self.assertEqual(path.replace("\\", "/").endswith(OVERRIDES_NAME), True)
        self.assertEqual(len(overrides.suppressions), 1)
        self.assertEqual(overrides.suppressions[0].rule_id, RULE)
        applied = status_of_entry(stored, overrides)
        self.assertEqual(applied.status, BaselineStatus.IGNORED)
        self.assertEqual(applied.scope, SuppressionScope.RULE)

    def test_a_rule_scope_covers_every_finding_of_that_rule(self):
        """The point of writing it to the overrides file: it reaches past today's entries."""
        self.write_baseline(entry("a", line=3), entry("b", line=9))

        self.suppress(
            fingerprint("a"),
            reason="Noisy rule in legacy code.",
            scope=SuppressionScope.RULE,
        )

        overrides, _ = self.overrides()
        for char in ("a", "b"):
            applied = status_of_entry(self.entry_for(char), overrides)
            self.assertEqual(applied.status, BaselineStatus.IGNORED, char)

    def test_a_line_scope_covers_a_range_and_stops_at_its_edge(self):
        self.write_baseline(entry("a", line=3), entry("b", line=40))

        self.suppress(
            fingerprint("a"),
            reason="Block under migration.",
            scope=SuppressionScope.LINE,
        )

        overrides, _ = self.overrides()
        inside = status_of_entry(self.entry_for("a"), overrides)
        outside = status_of_entry(self.entry_for("b"), overrides)
        self.assertEqual(inside.status, BaselineStatus.IGNORED)
        self.assertIsNone(outside, "a range does not reach the next finding's line")

    def test_a_file_scope_carries_the_file_and_a_line_scope_the_range(self):
        self.write_baseline(entry())
        self.suppress(
            fingerprint("a"),
            reason="Generated file.",
            scope=SuppressionScope.FILE,
        )

        overrides, _ = self.overrides()
        written = overrides.suppressions[0]
        self.assertEqual(written.scope, SuppressionScope.FILE)
        self.assertEqual(written.file_path, LEGACY_FILE)
        self.assertEqual(written.rule_id, RULE)
        self.assertIsNone(written.line_start)

    def test_an_ai_finding_is_silenced_by_its_category(self):
        """A finding with no rule id is fingerprinted under its category, so a
        wider scope has to name that same identity or it matches nothing."""
        self.write_baseline(entry(rule_id=None, category="review"))

        result = self.suppress(
            fingerprint("a"),
            reason="Known and accepted.",
            scope=SuppressionScope.RULE,
        )

        self.assertEqual(result.override.rule_id, "category:review")
        overrides, _ = self.overrides()
        applied = status_of_entry(self.entry_for(), overrides)
        self.assertEqual(applied.status, BaselineStatus.IGNORED)

    def test_a_wider_scope_is_refused_when_the_repository_does_not_read_the_file(self):
        """Writing a decision into a file the run drops would look like it worked."""
        self.write_baseline(entry())
        self.allow_local_overrides(False)

        with self.assertRaises(BaselineError) as caught:
            self.suppress(
                fingerprint("a"),
                reason="Noisy rule.",
                scope=SuppressionScope.RULE,
            )

        self.assertIn("ALLOW_LOCAL_OVERRIDES", str(caught.exception))
        self.assertFalse(os.path.exists(overrides_path(self.repo)))


class TestRefusals(SuppressUseCaseTestCase):
    def test_without_a_baseline_there_is_nothing_to_decide_about(self):
        with self.assertRaises(BaselineError) as caught:
            self.suppress(fingerprint("a"), reason="Fixture.")

        self.assertIn("baseline create", str(caught.exception))

    def test_a_baseline_that_cannot_be_applied_is_refused_rather_than_edited(self):
        """Rewriting it would launder whatever made it unusable into a fresh checksum."""
        self.write_baseline(entry())
        target = baseline_path(self.repo)
        with open(target, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text.replace(FINGERPRINT_VERSION, "99", 1))

        with self.assertRaises(BaselineError) as caught:
            self.suppress(fingerprint("a"), reason="Fixture.")

        self.assertIn("--recompute", str(caught.exception))
        with open(target, "r", encoding="utf-8", errors="replace") as handle:
            self.assertIn("99", handle.read(), "the file is left as it was found")

    def test_an_id_that_matches_two_findings_is_refused(self):
        """Guessing would silence a finding nobody meant to silence."""
        self.write_baseline(
            entry(),
            BaselineEntry(
                fingerprint="sha256:" + "a" + "b" * 63,
                rule_id="other-rule",
                category="security",
                file_path="app/other.py",
                line_start=1,
                line_end=1,
                severity="warning",
                source="linter",
            ),
        )

        with self.assertRaises(BaselineError) as caught:
            self.suppress("a", reason="Fixture.")

        self.assertIn("matches 2 findings", str(caught.exception))

    def test_an_id_that_matches_nothing_is_refused(self):
        self.write_baseline(entry())

        with self.assertRaises(BaselineError) as caught:
            self.suppress("sha256:ffff", reason="Fixture.")

        self.assertIn("No finding in the baseline matches", str(caught.exception))

    def test_a_finding_that_was_resolved_has_nothing_to_decide_about(self):
        self.write_baseline(entry(status=BaselineStatus.RESOLVED))

        with self.assertRaises(BaselineError) as caught:
            self.suppress(fingerprint("a"), reason="Fixture.")

        self.assertIn("resolved", str(caught.exception))


class TestTakingItBack(SuppressUseCaseTestCase):
    def test_unsuppress_clears_the_decision_on_the_entry(self):
        self.write_baseline(entry())
        self.suppress(fingerprint("a"), reason="Synthetic eval in a boot fixture.")

        result = self.unsuppress(fingerprint("a"))

        self.assertEqual(result.removed, ["entry"])
        stored = self.entry_for()
        self.assertFalse(stored.suppressed)
        self.assertIsNone(stored.suppression_reason)
        self.assertIsNone(stored.suppression_scope)
        self.assertIsNone(stored.suppressed_by)
        self.assertIsNone(status_of_entry(stored))
        self.assertEqual(stored.status, BaselineStatus.EXISTING)
        self.assertEqual(stored.fingerprint, fingerprint("a"))
        self.assertEqual(stored.provenance["command"], "baseline unsuppress")

    def test_unsuppress_removes_the_override_bound_to_that_fingerprint(self):
        self.write_baseline(entry())
        write_overrides(
            Overrides(
                suppressions=[
                    Suppression(
                        scope=SuppressionScope.FINDING,
                        reason="Synthetic secret in a fixture.",
                        fingerprint=fingerprint("a"),
                    )
                ]
            ),
            self.repo,
        )

        result = self.unsuppress(fingerprint("a"))

        self.assertEqual(result.removed, ["finding"])
        overrides, _ = self.overrides()
        self.assertEqual(overrides.suppressions, [])

    def test_unsuppress_removes_debt_bound_to_that_fingerprint(self):
        self.write_baseline(entry())
        write_overrides(
            Overrides(
                accepted_debt=[
                    AcceptedDebt(
                        fingerprint=fingerprint("a"),
                        owner="backend",
                        reason="Migration planned.",
                    )
                ]
            ),
            self.repo,
        )

        result = self.unsuppress(fingerprint("a"))

        self.assertEqual(result.removed, ["accepted_debt"])
        overrides, _ = self.overrides()
        self.assertEqual(overrides.accepted_debt, [])

    def test_unsuppress_reports_a_wider_suppression_instead_of_removing_it(self):
        """A rule decision belongs to the file that states it, not to this command."""
        self.write_baseline(entry())
        self.suppress(
            fingerprint("a"),
            reason="Noisy rule in legacy code.",
            scope=SuppressionScope.RULE,
        )

        with self.assertRaises(BaselineError) as caught:
            self.unsuppress(fingerprint("a"))

        message = str(caught.exception)
        self.assertIn("'rule' suppression", message)
        self.assertIn(RULE, message)
        self.assertIn(OVERRIDES_NAME, message)
        overrides, _ = self.overrides()
        self.assertEqual(len(overrides.suppressions), 1, "the decision is still there")

    def test_unsuppress_warns_about_a_wider_suppression_it_leaves_behind(self):
        """The entry decision was taken back; the rule decision never was this
        command's to take, and saying nothing would report a silence that is gone."""
        self.write_baseline(entry())
        self.suppress(fingerprint("a"), reason="Synthetic eval in a boot fixture.")
        self.suppress(
            fingerprint("a"),
            reason="Noisy rule in legacy code.",
            scope=SuppressionScope.RULE,
        )

        result = self.unsuppress(fingerprint("a"))

        self.assertEqual(result.removed, ["entry"])
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("'rule' suppression", result.warnings[0])
        self.assertEqual(len(self.overrides()[0].suppressions), 1)
        self.assertEqual(
            status_of_entry(self.entry_for(), self.overrides()[0]).scope,
            SuppressionScope.RULE,
        )

    def test_unsuppress_says_so_when_no_decision_covers_the_finding(self):
        self.write_baseline(entry())

        with self.assertRaises(BaselineError) as caught:
            self.unsuppress(fingerprint("a"))

        self.assertIn("no decision to take back", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
