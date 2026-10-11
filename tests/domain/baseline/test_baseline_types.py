"""The value contracts: what a status means and what survives a round trip.

These are the shapes every other module reads, so what is pinned here are
invariants rather than behaviour — `new` is never written to the file (an entry
saved as "new" is born stale), a status written by a newer GitPR never stops
this one from running, and a manifest printed and re-read is the same manifest.
"""

import unittest

from src.domain.baseline import (
    PERSISTED_STATUSES,
    SCOPE_PRECEDENCE,
    BaselineEntry,
    BaselineError,
    BaselineManifest,
    BaselineStatus,
    FindingFingerprint,
    SuppressionScope,
)

_FINGERPRINT = "sha256:" + "a" * 64


def entry(**overrides) -> BaselineEntry:
    fields = dict(
        fingerprint=_FINGERPRINT,
        rule_id="sec-aws-key",
        category="security",
        file_path="src/keys.py",
        line_start=10,
        line_end=10,
        severity="error",
        source="linter",
    )
    fields.update(overrides)
    return BaselineEntry(**fields)


class TestStatusVocabulary(unittest.TestCase):
    """The five statuses, and the rule that only four of them are writable."""

    def test_new_is_never_persisted(self):
        self.assertNotIn(BaselineStatus.NEW, PERSISTED_STATUSES)
        self.assertEqual(len(PERSISTED_STATUSES), 4)

    def test_the_four_writable_states_are_the_ones_documented(self):
        self.assertEqual(
            [status.value for status in PERSISTED_STATUSES],
            ["existing", "ignored", "accepted_debt", "resolved"],
        )

    def test_the_specificity_order_is_narrowest_first(self):
        self.assertEqual(
            SCOPE_PRECEDENCE,
            (
                SuppressionScope.FINDING,
                SuppressionScope.LINE,
                SuppressionScope.FILE,
                SuppressionScope.RULE,
            ),
        )


class TestEntryRoundTrip(unittest.TestCase):
    def test_every_field_survives_the_round_trip(self):
        original = entry(
            status=BaselineStatus.ACCEPTED_DEBT,
            low_confidence=True,
            first_seen_commit="a1b2c3d",
            last_seen_commit="d4e5f6a",
            first_seen_date="2026-10-01",
            last_seen_date="2026-10-10",
            suppression_reason="Synthetic secret in a fixture.",
            suppression_scope=SuppressionScope.RULE,
            suppressed_by="alice",
            suppressed_at="2026-10-10",
            accepted_debt_owner="time-backend",
            accepted_debt_due_date="2026-12-31",
            accepted_debt_reason="Planned migration.",
            provenance={"origin": "local", "command": "baseline create"},
        )

        restored = BaselineEntry.from_dict(original.to_dict())

        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_an_unknown_status_reads_as_existing(self):
        """A file from a future GitPR must not block a pipeline on one word."""
        written = entry().to_dict()
        written["status"] = "quarantined"

        self.assertEqual(BaselineEntry.from_dict(written).status, BaselineStatus.EXISTING)

    def test_an_entry_without_a_fingerprint_is_refused(self):
        written = entry().to_dict()
        del written["fingerprint"]

        with self.assertRaises(BaselineError):
            BaselineEntry.from_dict(written)

    def test_identity_falls_back_to_the_category(self):
        self.assertEqual(entry().identity(), "sec-aws-key")
        self.assertEqual(
            entry(rule_id=None, category="security").identity(), "category:security"
        )

    def test_debt_is_recognised_by_status_or_by_owner(self):
        self.assertFalse(entry().is_debt())
        self.assertTrue(entry(status=BaselineStatus.ACCEPTED_DEBT).is_debt())
        self.assertTrue(entry(accepted_debt_owner="time-backend").is_debt())

    def test_a_fingerprint_record_names_its_rule(self):
        record = FindingFingerprint(
            fingerprint=_FINGERPRINT,
            rule_id=None,
            category="Security",
            file_path="src/keys.py",
            line_start=10,
            line_end=10,
            source="ai",
            severity="error",
        )

        self.assertEqual(record.identity(), "category:security")


class TestManifest(unittest.TestCase):
    def test_entries_are_written_ordered_by_fingerprint(self):
        later = entry(fingerprint="sha256:" + "b" * 64)
        earlier = entry(fingerprint="sha256:" + "a" * 64)

        order = [
            item["fingerprint"]
            for item in BaselineManifest(entries=[later, earlier]).to_dict()["entries"]
        ]

        self.assertEqual(order, [earlier.fingerprint, later.fingerprint])

    def test_the_checksum_key_can_be_left_out(self):
        manifest = BaselineManifest(entries=[entry()], checksum="sha256:recorded")

        self.assertNotIn("checksum", manifest.to_dict(include_checksum=False))
        self.assertEqual(manifest.to_dict()["checksum"], "sha256:recorded")

    def test_entry_for_finds_it_by_fingerprint(self):
        manifest = BaselineManifest(entries=[entry()])

        self.assertIsNotNone(manifest.entry_for(_FINGERPRINT))
        self.assertIsNone(manifest.entry_for("sha256:" + "f" * 64))

    def test_a_manifest_without_an_entries_key_is_an_empty_baseline(self):
        manifest = BaselineManifest.from_dict(
            {"schema_version": 1, "fingerprint_version": "1"}
        )

        self.assertEqual(manifest.entries, [])
        self.assertEqual(manifest.fingerprint_version, "1")

    def test_a_document_that_is_not_an_object_is_refused(self):
        with self.assertRaises(BaselineError):
            BaselineManifest.from_dict(["not", "a", "manifest"])

    def test_entries_that_are_not_a_list_are_refused(self):
        with self.assertRaises(BaselineError):
            BaselineManifest.from_dict({"entries": {"fingerprint": _FINGERPRINT}})
