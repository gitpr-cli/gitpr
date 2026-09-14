"""Tests for the applied-patch record (.gitpr/fix_history.json).

The load/save/append behaviour is tested against a plain temporary directory —
the module deliberately knows nothing about git, which is what keeps these
tests fast. The end-to-end behaviour on a real repository lives in
test_apply_fix.py and test_rollback_fix.py.
"""
import json
import os
import shutil
import tempfile
import unittest

from src.fix.fix_history import (
    HISTORY_DIR,
    HISTORY_FILENAME,
    FixHistoryError,
    append_entry,
    find_entry,
    history_path,
    load_history,
    make_entry,
    mark_rolled_back,
    save_history,
)
from src.fix.patch_provenance import FindingRef, PatchProvenance, PatchSafety

FINDING = FindingRef(
    id="FIX-001",
    file_path="src/app.py",
    line_start=2,
    line_end=2,
    severity="minor",
    category="style",
    message="use a clear return",
)
PROVENANCE = PatchProvenance(
    finding_id="FIX-001",
    ai_provider="gemini",
    ai_model="gemini-pro-latest",
    prompt_version="1",
    generated_at="2026-09-13 12:00:00",
    gitpr_version="0.0.37",
)
DIFF = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1,1 +1,1 @@\n-a\n+b\n"


class HistoryTestCase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_fix_history_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def entry(self, patch_id="FIX-001-1a2b3c4d", branch=None):
        return make_entry(
            patch_id=patch_id,
            finding=FINDING,
            diff=DIFF,
            provenance=PROVENANCE,
            files_changed=("src/app.py",),
            safety=PatchSafety.SAFE,
            branch=branch,
        )


class TestHistoryPath(HistoryTestCase):
    def test_path_sits_under_the_given_root(self):
        expected = os.path.join(self.root, HISTORY_DIR, HISTORY_FILENAME)
        self.assertEqual(history_path(self.root), expected)

    def test_path_falls_back_to_the_working_directory(self):
        self.assertEqual(history_path(), os.path.join(os.getcwd(), HISTORY_DIR, HISTORY_FILENAME))


class TestLoadAndSave(HistoryTestCase):
    def test_a_missing_file_is_an_empty_history(self):
        self.assertEqual(load_history(self.root), [])
        self.assertFalse(os.path.exists(history_path(self.root)))

    def test_saving_creates_the_directory(self):
        save_history([self.entry()], self.root)
        self.assertTrue(os.path.exists(history_path(self.root)))

    def test_what_was_saved_is_what_loads_back(self):
        entry = self.entry()
        save_history([entry], self.root)
        self.assertEqual(load_history(self.root), [entry])

    def test_the_file_is_readable_utf8_json(self):
        save_history([self.entry()], self.root)
        with open(history_path(self.root), "r", encoding="utf-8") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith("\n"))
        self.assertEqual(json.loads(raw)[0]["patch_id"], "FIX-001-1a2b3c4d")

    def test_non_ascii_is_kept_readable(self):
        entry = self.entry()
        entry["file_path"] = "src/ação.py"
        save_history([entry], self.root)
        with open(history_path(self.root), "r", encoding="utf-8") as handle:
            self.assertIn("ação", handle.read())

    def test_a_corrupt_file_raises_instead_of_reporting_an_empty_history(self):
        os.makedirs(os.path.dirname(history_path(self.root)), exist_ok=True)
        with open(history_path(self.root), "w", encoding="utf-8") as handle:
            handle.write("{not json at all")
        with self.assertRaises(FixHistoryError):
            load_history(self.root)

    def test_a_json_document_that_is_not_a_list_raises(self):
        save_history({"patch_id": "x"}, self.root)
        with self.assertRaises(FixHistoryError):
            load_history(self.root)

    def test_saving_leaves_no_temporary_file_behind(self):
        save_history([self.entry()], self.root)
        leftovers = [n for n in os.listdir(os.path.dirname(history_path(self.root))) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])


class TestAppendAndFind(HistoryTestCase):
    def test_appending_accumulates(self):
        append_entry(self.entry("FIX-001-aaaaaaaa"), self.root)
        append_entry(self.entry("FIX-002-bbbbbbbb"), self.root)
        self.assertEqual(
            [e["patch_id"] for e in load_history(self.root)],
            ["FIX-001-aaaaaaaa", "FIX-002-bbbbbbbb"],
        )

    def test_an_unrecorded_patch_is_not_found(self):
        append_entry(self.entry(), self.root)
        self.assertIsNone(find_entry("FIX-999-ffffffff", self.root))

    def test_finding_returns_the_newest_record_of_a_repeated_patch(self):
        first = self.entry()
        first["applied_at"] = "2026-09-13 10:00:00"
        second = self.entry()
        second["applied_at"] = "2026-09-13 11:00:00"
        save_history([first, second], self.root)
        self.assertEqual(find_entry("FIX-001-1a2b3c4d", self.root)["applied_at"], "2026-09-13 11:00:00")


class TestMarkRolledBack(HistoryTestCase):
    def test_stamping_records_the_moment(self):
        append_entry(self.entry(), self.root)
        self.assertTrue(mark_rolled_back("FIX-001-1a2b3c4d", self.root))
        entry = find_entry("FIX-001-1a2b3c4d", self.root)
        self.assertRegex(entry["rolled_back_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_stamping_survives_a_reload(self):
        append_entry(self.entry(), self.root)
        mark_rolled_back("FIX-001-1a2b3c4d", self.root)
        self.assertIsNotNone(find_entry("FIX-001-1a2b3c4d", self.root)["rolled_back_at"])

    def test_stamping_an_unknown_patch_reports_false(self):
        append_entry(self.entry(), self.root)
        self.assertFalse(mark_rolled_back("FIX-999-ffffffff", self.root))
        self.assertIsNone(find_entry("FIX-001-1a2b3c4d", self.root)["rolled_back_at"])


class TestMakeEntry(HistoryTestCase):
    def test_every_documented_field_is_present(self):
        entry = self.entry(branch="fix/gitpr-20260913120000")
        self.assertEqual(
            sorted(entry),
            [
                "applied_at", "branch", "diff", "file_path", "files_changed",
                "finding_id", "patch_id", "provenance", "rolled_back_at", "safety",
            ],
        )
        self.assertEqual(entry["safety"], "safe")
        self.assertEqual(entry["files_changed"], ["src/app.py"])
        self.assertIsNone(entry["rolled_back_at"])
        self.assertEqual(entry["diff"], DIFF)

    def test_the_diff_is_stored_verbatim(self):
        # Rollback replays this text, so it may not be reformatted or trimmed.
        entry = self.entry()
        self.assertEqual(entry["diff"], DIFF)
        self.assertTrue(entry["diff"].endswith("\n"))

    def test_provenance_is_stored_as_plain_json(self):
        entry = self.entry()
        self.assertEqual(entry["provenance"]["ai_provider"], "gemini")
        self.assertEqual(entry["provenance"]["gitpr_version"], "0.0.37")
        json.dumps(entry)  # would raise if a dataclass had leaked through

    def test_the_safety_enum_is_stored_by_value(self):
        entry = make_entry(
            patch_id="FIX-002-bbbbbbbb",
            finding=FINDING,
            diff=DIFF,
            provenance=PROVENANCE,
            safety=PatchSafety.REVIEW_REQUIRED,
        )
        self.assertEqual(entry["safety"], "review_required")

    def test_the_timestamp_uses_the_project_format(self):
        self.assertRegex(self.entry()["applied_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


if __name__ == "__main__":
    unittest.main()
