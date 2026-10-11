"""Classification: what this run found, read against what the baseline knew.

The matrix is the contract. Every finding lands on exactly one status, nothing
falls out of the count, and `new` is the only status that blocks — a `new`
warning stays a warning and an `existing` error stops blocking, because the
gate answers for what the change introduced, not for what the tree already had.

The comparison is read-only. §5.9 of the spec is blunt about it: the file moves
only through `baseline create`/`update`, never as a side effect of a review, so
one of these tests checks that the manifest comes back untouched.
"""

import unittest

from src.domain.baseline import (
    BaselineEntry,
    BaselineManifest,
    BaselineStatus,
    ComparedFinding,
    classify_findings,
    compute_fingerprint,
    entries_resolved_by,
    parse_overrides,
    snippet_hash,
    status_counts,
)
from src.domain.finding.finding_types import NormalizedFinding

_LINE = '    key = "AKIA****"'


def finding(**overrides) -> NormalizedFinding:
    fields = dict(
        severity="error",
        category="security/secret",
        file_path="src/config.py",
        line_start=42,
        line_end=42,
        message="AWS Access Key detected",
        source="gitleaks",
        rule_id="aws-access-key",
        snippet_hash=snippet_hash(_LINE),
    )
    fields.update(overrides)
    return NormalizedFinding(**fields)


def entry_for(item: NormalizedFinding, **overrides) -> BaselineEntry:
    fields = dict(
        fingerprint=compute_fingerprint(item),
        rule_id=item.rule_id,
        category=item.category,
        file_path=item.file_path,
        line_start=item.line_start,
        line_end=item.line_end,
        severity=item.severity,
        source=item.source,
        status=BaselineStatus.EXISTING,
        first_seen_date="2026-10-01",
    )
    fields.update(overrides)
    return BaselineEntry.from_dict(fields)


def manifest_of(*entries: BaselineEntry) -> BaselineManifest:
    return BaselineManifest(entries=list(entries), fingerprint_version="1")


def only(compared) -> ComparedFinding:
    assert len(compared) == 1
    return compared[0]


class TestStatusMatrix(unittest.TestCase):
    def test_a_finding_the_baseline_does_not_know_is_new(self):
        compared = only(classify_findings([finding()], manifest_of()))

        self.assertEqual(compared.baseline_status, BaselineStatus.NEW)
        self.assertTrue(compared.is_blocking)
        self.assertIsNone(compared.entry)

    def test_a_finding_the_baseline_knows_is_existing(self):
        item = finding()
        compared = only(classify_findings([item], manifest_of(entry_for(item))))

        self.assertEqual(compared.baseline_status, BaselineStatus.EXISTING)
        self.assertFalse(compared.is_blocking)
        self.assertIn("2026-10-01", compared.reason)

    def test_an_ignored_entry_stays_ignored_and_shows_the_reason(self):
        item = finding()
        entry = entry_for(
            item,
            status=BaselineStatus.IGNORED,
            suppressed=True,
            suppression_reason="Synthetic secret in a fixture.",
        )

        compared = only(classify_findings([item], manifest_of(entry)))

        self.assertEqual(compared.baseline_status, BaselineStatus.IGNORED)
        self.assertFalse(compared.is_blocking)
        self.assertEqual(compared.reason, "Synthetic secret in a fixture.")

    def test_accepted_debt_carries_the_owner_and_the_deadline(self):
        item = finding()
        entry = entry_for(
            item,
            status=BaselineStatus.ACCEPTED_DEBT,
            accepted_debt_owner="time-backend",
            accepted_debt_reason="Planned migration.",
            accepted_debt_due_date="2026-12-31",
        )

        compared = only(classify_findings([item], manifest_of(entry)))

        self.assertEqual(compared.baseline_status, BaselineStatus.ACCEPTED_DEBT)
        self.assertFalse(compared.is_blocking)
        self.assertEqual(compared.applied.owner, "time-backend")
        self.assertEqual(compared.applied.due_date, "2026-12-31")

    def test_a_resolved_entry_that_came_back_is_new(self):
        """The code returned; calling it `existing` would hide a regression."""
        item = finding()
        entry = entry_for(
            item, status=BaselineStatus.RESOLVED, resolved_at="2026-10-05"
        )

        compared = only(classify_findings([item], manifest_of(entry)))

        self.assertEqual(compared.baseline_status, BaselineStatus.NEW)
        self.assertTrue(compared.is_blocking)
        self.assertIn("2026-10-05", compared.reason)

    def test_without_a_baseline_every_finding_is_new(self):
        compared = classify_findings([finding(), finding(line_start=7, line_end=7)], None)

        self.assertEqual([item.baseline_status for item in compared], [BaselineStatus.NEW] * 2)

    def test_a_line_that_moved_is_new_again(self):
        """The documented limit of a content-hash fingerprint."""
        moved = finding(line_start=60, line_end=60)

        compared = only(classify_findings([moved], manifest_of(entry_for(finding()))))

        self.assertEqual(compared.baseline_status, BaselineStatus.NEW)


class TestBlocking(unittest.TestCase):
    def test_blocking_is_read_from_the_status_never_from_the_severity(self):
        new_warning = finding(severity="warning", line_start=7, line_end=7)
        known_error = finding()

        compared = classify_findings(
            [new_warning, known_error],
            manifest_of(entry_for(known_error)),
        )
        statuses = {item.current_severity: item for item in compared}

        self.assertTrue(statuses["warning"].is_blocking)
        self.assertFalse(statuses["error"].is_blocking)
        # The severity is still there for the caller to combine with the status.
        self.assertTrue(statuses["error"].is_error())
        self.assertFalse(statuses["warning"].is_error())


class TestCounts(unittest.TestCase):
    def test_the_counts_add_up_to_the_findings(self):
        known = finding()
        ignored = finding(line_start=2, line_end=2)
        unknown = finding(line_start=3, line_end=3)
        entries = [
            entry_for(known),
            entry_for(
                ignored,
                status=BaselineStatus.IGNORED,
                suppressed=True,
                suppression_reason="Fixture.",
            ),
        ]

        compared = classify_findings([known, ignored, unknown], manifest_of(*entries))
        counts = status_counts(compared)

        self.assertEqual(sum(counts.values()), 3)
        self.assertEqual(counts["existing"], 1)
        self.assertEqual(counts["ignored"], 1)
        self.assertEqual(counts["new"], 1)

    def test_every_status_has_a_row_even_when_empty(self):
        counts = status_counts(classify_findings([finding()], None))

        self.assertEqual(
            sorted(counts), ["accepted_debt", "existing", "ignored", "new", "resolved"]
        )
        self.assertEqual(counts["accepted_debt"], 0)

    def test_an_empty_run_counts_nothing(self):
        self.assertEqual(sum(status_counts(classify_findings([], None)).values()), 0)


class TestLayers(unittest.TestCase):
    def test_an_override_silences_a_finding_that_has_no_entry_yet(self):
        overrides = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "aws-access-key", "reason": "Synthetic."}]}
        )

        compared = only(classify_findings([finding()], None, overrides))

        self.assertEqual(compared.baseline_status, BaselineStatus.IGNORED)
        self.assertEqual(compared.reason, "Synthetic.")
        self.assertEqual(compared.applied.origin, "local")

    def test_the_most_specific_scope_supplies_the_reason_shown(self):
        overrides = parse_overrides(
            {
                "suppressions": [
                    {"scope": "rule", "rule_id": "aws-access-key", "reason": "Noisy rule."},
                    {
                        "scope": "line",
                        "rule_id": "aws-access-key",
                        "file_path": "src/config.py",
                        "line_start": 1,
                        "line_end": 100,
                        "reason": "Legacy block.",
                    },
                ]
            }
        )

        compared = only(classify_findings([finding()], None, overrides))

        self.assertEqual(compared.reason, "Legacy block.")

    def test_debt_declared_in_the_overrides_is_applied(self):
        item = finding()
        overrides = parse_overrides(
            {
                "accepted_debt": [
                    {
                        "fingerprint": compute_fingerprint(item),
                        "owner": "time-backend",
                        "reason": "Planned migration.",
                        "due_date": "2026-12-31",
                    }
                ]
            }
        )

        compared = only(classify_findings([item], None, overrides))

        self.assertEqual(compared.baseline_status, BaselineStatus.ACCEPTED_DEBT)
        self.assertEqual(compared.applied.owner, "time-backend")

    def test_an_override_can_silence_an_entry_the_file_calls_existing(self):
        item = finding()
        overrides = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "aws-access-key", "reason": "Noisy."}]}
        )

        compared = only(classify_findings([item], manifest_of(entry_for(item)), overrides))

        self.assertEqual(compared.baseline_status, BaselineStatus.IGNORED)


class TestReadOnly(unittest.TestCase):
    def test_classification_never_touches_the_manifest(self):
        item = finding()
        manifest = manifest_of(entry_for(item))
        before = manifest.to_dict()

        classify_findings([item, finding(line_start=9, line_end=9)], manifest)

        self.assertEqual(manifest.to_dict(), before)


class TestResolvedEntries(unittest.TestCase):
    def test_an_entry_the_diff_proves_gone_is_resolved(self):
        entry = entry_for(finding())

        resolved = entries_resolved_by([entry], ["src/config.py"], seen_fingerprints=[])

        self.assertEqual(resolved, [entry])

    def test_an_entry_outside_the_diff_is_left_alone(self):
        entry = entry_for(finding())

        self.assertEqual(entries_resolved_by([entry], ["src/other.py"], []), [])

    def test_an_entry_still_present_is_not_resolved(self):
        entry = entry_for(finding())

        self.assertEqual(
            entries_resolved_by([entry], ["src/config.py"], [entry.fingerprint]), []
        )

    def test_paths_are_compared_normalized(self):
        entry = entry_for(finding(file_path="src/config.py"))

        resolved = entries_resolved_by([entry], ["SRC\\Config.py"], [])

        self.assertEqual(resolved, [entry])

    def test_a_glob_does_not_count_as_touching_the_file(self):
        """Only a diff that names the file is evidence about that file."""
        entry = entry_for(finding())

        self.assertEqual(entries_resolved_by([entry], ["src/*"], []), [])
