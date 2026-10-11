"""The baseline file: the checksum has to catch an edit and never cover itself.

Two properties carry the whole feature here. The checksum is what makes an
unreviewed hand edit visible, so it has to be recomputed from the content and
must not include its own value — otherwise writing the file would invalidate it.
And the serialization has to be canonical, because the file is committed: the
same findings on two machines have to produce the same bytes.

Validation reports the whole list instead of raising on the first problem, so
these tests check that a document with three mistakes yields three lines.
"""

import unittest

from src.domain.baseline import (
    SCHEMA_VERSION,
    BaselineEntry,
    BaselineError,
    BaselineManifest,
    checksum_matches,
    dump_manifest,
    manifest_checksum,
    parse_manifest,
    resolve_fingerprint_prefix,
    validate_manifest_dict,
)

_FINGERPRINT_A = "sha256:" + "a" * 64
_FINGERPRINT_B = "sha256:" + "b" * 64


def entry(fingerprint: str = _FINGERPRINT_A, **overrides) -> BaselineEntry:
    fields = dict(
        fingerprint=fingerprint,
        rule_id="sec-aws-key",
        category="security",
        file_path="src/keys.py",
        line_start=10,
        line_end=10,
        severity="error",
        source="linter",
        status="existing",
        first_seen_date="2026-10-01",
        last_seen_date="2026-10-10",
    )
    fields.update(overrides)
    return BaselineEntry.from_dict(fields)


def document(entries=None, **header) -> dict:
    """A checksummed baseline document, the way `baseline create` writes one."""
    manifest = BaselineManifest(
        entries=entries if entries is not None else [entry()],
        fingerprint_version="1",
        gitpr_version="0.0.37",
        created_at="2026-10-10T09:00:00",
        updated_at="2026-10-10T09:00:00",
        **header,
    )
    return dump_manifest(manifest)


class TestChecksum(unittest.TestCase):
    def test_a_written_baseline_matches_its_own_checksum(self):
        data = document()

        self.assertTrue(checksum_matches(data))
        self.assertEqual(data["checksum"], manifest_checksum(data))

    def test_the_checksum_does_not_cover_itself(self):
        data = document()

        rewritten = dict(data, checksum="sha256:" + "0" * 64)

        self.assertEqual(manifest_checksum(rewritten), data["checksum"])

    def test_editing_an_entry_breaks_the_checksum(self):
        """The tampering this exists to catch: a status flipped by hand."""
        data = document()
        data["entries"][0]["status"] = "ignored"

        self.assertFalse(checksum_matches(data))
        self.assertTrue(
            any("checksum" in problem for problem in validate_manifest_dict(data))
        )

    def test_two_orders_produce_the_same_bytes(self):
        """The file is committed, so insertion order must not reach the disk."""
        first = document(entries=[entry(_FINGERPRINT_B), entry(_FINGERPRINT_A)])
        second = document(entries=[entry(_FINGERPRINT_A), entry(_FINGERPRINT_B)])

        self.assertEqual(first, second)

    def test_a_missing_checksum_is_reported(self):
        data = document()
        del data["checksum"]

        self.assertFalse(checksum_matches(data))
        self.assertTrue(
            any("checksum" in problem for problem in validate_manifest_dict(data))
        )


class TestValidation(unittest.TestCase):
    def test_a_clean_baseline_has_nothing_to_report(self):
        self.assertEqual(validate_manifest_dict(document()), [])

    def test_a_document_that_is_not_an_object_is_reported(self):
        problems = validate_manifest_dict(["not", "a", "manifest"])

        self.assertEqual(len(problems), 1)

    def test_a_wrong_schema_version_is_reported(self):
        data = document()
        data["schema_version"] = SCHEMA_VERSION + 1

        self.assertTrue(
            any("schema_version" in problem for problem in validate_manifest_dict(data))
        )

    def test_a_fingerprint_version_mismatch_is_reported_when_the_caller_knows_it(self):
        data = document()

        silent = validate_manifest_dict(data)
        loud = validate_manifest_dict(data, fingerprint_version="2")

        self.assertEqual(silent, [])
        self.assertTrue(any("fingerprint_version" in problem for problem in loud))

    def test_a_missing_fingerprint_version_is_reported(self):
        data = document()
        data["fingerprint_version"] = ""

        self.assertTrue(
            any(
                "fingerprint_version" in problem
                for problem in validate_manifest_dict(data)
            )
        )

    def test_a_status_that_cannot_be_stored_is_reported(self):
        """`new` is a comparison result; a file claiming it is a file edited wrong."""
        data = document(entries=[entry(status="new")])

        self.assertTrue(
            any("status 'new'" in problem for problem in validate_manifest_dict(data))
        )

    def test_a_duplicated_fingerprint_is_reported(self):
        data = document(entries=[entry(), entry()])

        self.assertTrue(
            any("appears 2 times" in problem for problem in validate_manifest_dict(data))
        )

    def test_an_unknown_key_is_reported_at_both_levels(self):
        data = document()
        data["linter_rules"] = []
        data["entries"][0]["confidence"] = "high"

        problems = validate_manifest_dict(data)

        self.assertTrue(any("linter_rules" in problem for problem in problems))
        self.assertTrue(any("confidence" in problem for problem in problems))

    def test_a_suppression_without_a_reason_is_reported(self):
        data = document(entries=[entry(suppressed=True)])

        self.assertTrue(
            any("without a reason" in problem for problem in validate_manifest_dict(data))
        )

    def test_debt_without_an_owner_or_a_reason_is_reported(self):
        data = document(entries=[entry(status="accepted_debt")])

        problems = validate_manifest_dict(data)

        self.assertTrue(any("without an owner" in problem for problem in problems))
        self.assertTrue(any("without a reason" in problem for problem in problems))

    def test_a_deadline_that_is_not_a_date_is_reported(self):
        data = document(
            entries=[
                entry(
                    status="accepted_debt",
                    accepted_debt_owner="time-backend",
                    accepted_debt_reason="Planned migration.",
                    accepted_debt_due_date="31/12/2026",
                )
            ]
        )

        self.assertTrue(
            any("is not a date" in problem for problem in validate_manifest_dict(data))
        )

    def test_an_impossible_line_range_is_reported(self):
        data = document(entries=[entry(line_start=40, line_end=10)])

        self.assertTrue(
            any("line range" in problem for problem in validate_manifest_dict(data))
        )

    def test_a_resolution_date_without_the_status_is_reported(self):
        data = document(entries=[entry(resolved_at="2026-10-05")])

        self.assertTrue(
            any("resolution date" in problem for problem in validate_manifest_dict(data))
        )

    def test_every_problem_is_reported_not_only_the_first(self):
        data = document()
        data["unknown_one"] = 1
        data["entries"][0]["line_start"] = 0

        self.assertGreaterEqual(len(validate_manifest_dict(data)), 2)

    def test_parsing_refuses_a_document_that_is_not_a_manifest(self):
        with self.assertRaises(BaselineError):
            parse_manifest("baseline.json")

    def test_parsing_returns_the_manifest_the_document_describes(self):
        manifest = parse_manifest(document(entries=[entry(_FINGERPRINT_B)]))

        self.assertEqual(manifest.fingerprint_version, "1")
        self.assertEqual(manifest.entries[0].fingerprint, _FINGERPRINT_B)


class TestFingerprintPrefix(unittest.TestCase):
    """Ids are typed by hand, so a prefix has to be unambiguous or refused."""

    def test_a_unique_prefix_resolves(self):
        resolved = resolve_fingerprint_prefix("sha256:aaaa", [_FINGERPRINT_A, _FINGERPRINT_B])

        self.assertEqual(resolved, _FINGERPRINT_A)

    def test_the_prefix_may_omit_the_algorithm(self):
        self.assertEqual(
            resolve_fingerprint_prefix("BBBB", [_FINGERPRINT_A, _FINGERPRINT_B]),
            _FINGERPRINT_B,
        )

    def test_an_ambiguous_prefix_is_refused(self):
        with self.assertRaises(BaselineError) as caught:
            resolve_fingerprint_prefix("sha256:", [_FINGERPRINT_A, _FINGERPRINT_B])

        self.assertIn("2", str(caught.exception))

    def test_an_unknown_prefix_is_refused(self):
        with self.assertRaises(BaselineError):
            resolve_fingerprint_prefix("sha256:ffff", [_FINGERPRINT_A])

    def test_an_empty_prefix_is_refused(self):
        with self.assertRaises(BaselineError):
            resolve_fingerprint_prefix("   ", [_FINGERPRINT_A])
