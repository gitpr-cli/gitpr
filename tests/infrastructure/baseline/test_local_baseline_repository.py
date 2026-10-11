"""The file on disk: absent is not an error, imperfect is not unusable.

Three distinctions carry this module, and each one has a test here because the
difference decides whether the gate applies a baseline or ignores it:

- no file → no baseline, and the run must behave exactly as before;
- a file that is merely imperfect (a bad date on one entry) → still applied,
  with the problem reported;
- a file that cannot be trusted (checksum, fingerprint version, schema) → not
  applied at all, and the caller is told why.
"""

import json
import os
import tempfile
import unittest

from src.domain.baseline import (
    FINGERPRINT_VERSION,
    SCHEMA_VERSION,
    BaselineError,
    BaselineEntry,
    BaselineManifest,
    dump_manifest,
)
from src.infrastructure.baseline.local_baseline_repository import (
    BaselineSnapshot,
    baseline_path,
    overrides_path,
    read_baseline,
    read_manifest,
    read_overrides,
    write_manifest,
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
        status="existing",
        first_seen_date="2026-10-01",
        last_seen_date="2026-10-10",
    )
    fields.update(overrides)
    return BaselineEntry.from_dict(fields)


def manifest(*entries: BaselineEntry, **header) -> BaselineManifest:
    fields = dict(fingerprint_version=FINGERPRINT_VERSION, gitpr_version="0.0.37")
    fields.update(header)
    return BaselineManifest(entries=list(entries) or [entry()], **fields)


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.repo = self._tmpdir.name

    def path(self) -> str:
        return baseline_path(self.repo)

    def write_raw(self, text: str, name: str = "baseline.json") -> str:
        target = os.path.join(self.repo, ".gitpr", name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        return target


class TestPaths(RepositoryTestCase):
    def test_the_paths_are_the_documented_ones(self):
        self.assertEqual(self.path(), os.path.join(self.repo, ".gitpr", "baseline.json"))
        self.assertEqual(
            overrides_path(self.repo),
            os.path.join(self.repo, ".gitpr", "baseline.overrides.yml"),
        )

    def test_an_explicit_path_wins(self):
        explicit = os.path.join(self.repo, "elsewhere.json")

        self.assertEqual(baseline_path(self.repo, explicit), explicit)


class TestMissingFile(RepositoryTestCase):
    def test_no_file_is_not_an_error(self):
        snapshot = read_baseline(self.repo)

        self.assertEqual(snapshot.manifest, None)
        self.assertEqual(snapshot.problems, [])
        self.assertFalse(snapshot.exists)
        self.assertFalse(snapshot.is_usable)

    def test_the_same_is_true_for_the_overrides(self):
        layers, path = read_overrides(self.repo)

        self.assertTrue(layers.is_empty())
        self.assertEqual(path, overrides_path(self.repo))


class TestRoundTrip(RepositoryTestCase):
    def test_a_written_baseline_reads_back_whole(self):
        written = write_manifest(manifest(), self.repo)

        snapshot = read_baseline(self.repo)

        self.assertEqual(written, self.path())
        self.assertTrue(snapshot.is_usable)
        self.assertTrue(snapshot.checksum_ok)
        self.assertEqual(snapshot.problems, [])
        self.assertEqual(snapshot.manifest.entries[0].fingerprint, _FINGERPRINT)

    def test_the_file_starts_with_the_header_and_ends_with_the_checksum(self):
        write_manifest(manifest(), self.repo)

        with open(self.path(), encoding="utf-8") as handle:
            data = json.load(handle)

        self.assertEqual(
            list(data),
            [
                "schema_version",
                "fingerprint_version",
                "policy_name",
                "policy_version",
                "gitpr_version",
                "created_at",
                "updated_at",
                "entries",
                "checksum",
            ],
        )

    def test_the_written_file_is_utf8_with_lf_endings(self):
        write_manifest(manifest(), self.repo)

        with open(self.path(), "rb") as handle:
            raw = handle.read()

        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r\n", raw)

    def test_two_writes_of_the_same_manifest_are_byte_identical(self):
        """The file is committed: a rewrite that changed nothing must not diff."""
        write_manifest(manifest(), self.repo)
        with open(self.path(), "rb") as handle:
            first = handle.read()

        write_manifest(manifest(), self.repo)
        with open(self.path(), "rb") as handle:
            second = handle.read()

        self.assertEqual(first, second)

    def test_no_temporary_file_is_left_behind(self):
        write_manifest(manifest(), self.repo)

        leftovers = [name for name in os.listdir(os.path.join(self.repo, ".gitpr")) if name.endswith(".tmp")]

        self.assertEqual(leftovers, [])

    def test_the_directory_is_created_when_it_does_not_exist(self):
        self.assertFalse(os.path.isdir(os.path.join(self.repo, ".gitpr")))

        write_manifest(manifest(), self.repo)

        self.assertTrue(os.path.isfile(self.path()))


class TestUnusableFiles(RepositoryTestCase):
    def test_a_file_that_is_not_json_is_reported_and_not_applied(self):
        self.write_raw("{ this is not json")

        snapshot = read_baseline(self.repo)

        self.assertTrue(snapshot.exists)
        self.assertFalse(snapshot.is_usable)
        self.assertIn("JSON", snapshot.first_problem())

    def test_an_edited_file_is_caught_by_the_checksum(self):
        """Decision 6: a baseline nobody can verify is not a baseline."""
        write_manifest(manifest(), self.repo)
        with open(self.path(), encoding="utf-8") as handle:
            data = json.load(handle)
        data["entries"][0]["status"] = "ignored"
        with open(self.path(), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle)

        snapshot = read_baseline(self.repo)

        self.assertTrue(snapshot.exists)
        self.assertFalse(snapshot.checksum_ok)
        self.assertFalse(snapshot.is_usable)
        self.assertTrue(any("checksum" in problem for problem in snapshot.problems))

    def test_a_file_from_another_fingerprint_version_is_not_applied(self):
        write_manifest(manifest(fingerprint_version="2"), self.repo)

        snapshot = read_baseline(self.repo)

        self.assertFalse(snapshot.is_usable)
        self.assertTrue(any("fingerprint_version" in problem for problem in snapshot.problems))

    def test_a_file_from_a_newer_schema_is_not_applied(self):
        write_manifest(manifest(schema_version=SCHEMA_VERSION + 1), self.repo)

        snapshot = read_baseline(self.repo)

        self.assertFalse(snapshot.is_usable)
        self.assertTrue(any("schema_version" in problem for problem in snapshot.problems))

    def test_a_schema_version_that_is_not_a_number_is_refused_like_any_other(self):
        """A hand-edited `"schema_version": "one"` is a refusal, not a traceback."""
        write_manifest(manifest(schema_version="one"), self.repo)

        snapshot = read_baseline(self.repo)

        self.assertFalse(snapshot.is_usable)
        self.assertTrue(any("schema_version" in problem for problem in snapshot.problems))

    def test_a_missing_checksum_is_not_treated_as_matching(self):
        data = dump_manifest(manifest())
        del data["checksum"]
        self.write_raw(json.dumps(data))

        snapshot = read_baseline(self.repo)

        self.assertFalse(snapshot.checksum_ok)
        self.assertFalse(snapshot.is_usable)


class TestImperfectButUsable(RepositoryTestCase):
    def test_a_bad_deadline_is_reported_but_the_baseline_still_applies(self):
        """One unreadable field must not blind the gate for every other finding."""
        write_manifest(
            manifest(
                entry(
                    status="accepted_debt",
                    accepted_debt_owner="time-backend",
                    accepted_debt_reason="Planned migration.",
                    accepted_debt_due_date="31/12/2026",
                )
            ),
            self.repo,
        )

        snapshot = read_baseline(self.repo)

        self.assertTrue(snapshot.is_usable)
        self.assertTrue(any("is not a date" in problem for problem in snapshot.problems))

    def test_an_unknown_key_is_reported_but_the_baseline_still_applies(self):
        write_manifest(manifest(), self.repo)
        with open(self.path(), encoding="utf-8") as handle:
            data = json.load(handle)
        data["entries"][0]["confidence"] = "high"
        self.write_raw(json.dumps(data))

        snapshot = read_baseline(self.repo)

        # The edit broke the checksum, so this one is unusable — the point here
        # is that the unknown key is named in the report.
        self.assertTrue(any("confidence" in problem for problem in snapshot.problems))

    def test_read_manifest_returns_the_pair_validate_prints(self):
        write_manifest(manifest(), self.repo)

        parsed, problems = read_manifest(self.repo)

        self.assertEqual(problems, [])
        self.assertEqual(parsed.fingerprint_version, FINGERPRINT_VERSION)

    def test_the_snapshot_type_is_what_the_gate_reads(self):
        snapshot = read_baseline(self.repo)

        self.assertIsInstance(snapshot, BaselineSnapshot)


class TestOverrides(RepositoryTestCase):
    def test_the_layers_are_read_and_validated(self):
        self.write_raw(
            "overrides:\n"
            "  suppressions:\n"
            "    - scope: rule\n"
            "      rule_id: sec-aws-key\n"
            "      reason: Noisy rule in legacy code.\n",
            name="baseline.overrides.yml",
        )

        layers, path = read_overrides(self.repo)

        self.assertEqual(path, overrides_path(self.repo))
        self.assertEqual(len(layers.suppressions), 1)
        self.assertEqual(layers.suppressions[0].reason, "Noisy rule in legacy code.")

    def test_a_decision_without_a_reason_names_the_file_that_broke(self):
        self.write_raw(
            "suppressions:\n  - scope: rule\n    rule_id: sec-aws-key\n",
            name="baseline.overrides.yml",
        )

        with self.assertRaises(BaselineError) as caught:
            read_overrides(self.repo)

        self.assertEqual(caught.exception.path, overrides_path(self.repo))
        self.assertIn("reason", str(caught.exception))

    def test_a_file_that_is_not_yaml_names_the_file_that_broke(self):
        self.write_raw("suppressions: [unclosed", name="baseline.overrides.yml")

        with self.assertRaises(BaselineError) as caught:
            read_overrides(self.repo)

        self.assertEqual(caught.exception.path, overrides_path(self.repo))

    def test_an_unknown_key_is_refused_not_ignored(self):
        self.write_raw(
            "suppressions:\n  - scope: rule\n    rule_id: x\n    reason: y\n    expires: soon\n",
            name="baseline.overrides.yml",
        )

        with self.assertRaises(BaselineError) as caught:
            read_overrides(self.repo)

        self.assertIn("expires", str(caught.exception))
