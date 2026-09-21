"""Acceptance 1 — hunks come out exactly as git drew them, and go back the same.

Every diff here is produced by git itself inside a real repository, never
hand-written: the question the parser answers is "what did git emit", and a
fixture string typed by hand would only prove the parser agrees with whoever
typed it.

The round-trip tests are the ones that matter. Parsing can be checked property
by property, but only reapplying the rebuilt patch to a clean tree proves the
parse lost nothing — offsets, counts and the header block all have to be right
at once for that to pass.
"""
import os
import unittest

from src.split.hunk_parser import build_patch, parse_units
from src.split.split_plan import Hunk, OpaqueSection
from tests.split.git_fixture import SplitRepoTestCase, block

#: A section that claims six old lines and supplies two: the counts cannot be
#: reconciled with the body, so no hunk from it can be trusted.
TRUNCATED = (
    "diff --git a/src/app.py b/src/app.py\n"
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,6 +1,6 @@\n"
    " app_01\n"
    "-app_02\n"
    "+app_02_changed\n"
)

#: A well-formed hunk followed by a broken one. The whole section degrades —
#: the first hunk is not rescued, because half of an unparseable section is not
#: something to hand to ``git apply``.
PARTLY_BROKEN = (
    "diff --git a/src/app.py b/src/app.py\n"
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,3 +1,3 @@\n"
    " app_01\n"
    "-app_02\n"
    "+app_02_changed\n"
    " app_03\n"
    "@@ -10,5 +10,5 @@\n"
    " app_10\n"
)

#: A removed line that reads ``--- removed`` and an added line that reads
#: ``+++ added``: at column 0 they are indistinguishable from a file-header
#: pair. Nothing but counting can tell them apart.
HEADER_LOOKALIKE = "a\n-- removed\nb\nc\nd\ne\nf\ng\n"
HEADER_LOOKALIKE_CHANGED = "a\n++ added\nb\nc\nd\ne\nf\ng\n"


class ParsingTest(SplitRepoTestCase):
    """Real git output, parsed into exactly the hunks it describes."""

    def mixed_diff(self):
        """Three concerns: two far-apart edits in one file, one in another.

        Line 3 and line 38 of a 40-line file are far enough apart that ``-U3``
        leaves untouched lines between them, so git reports two hunks and not
        one merged block.
        """
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("src/app.py", 38, "app_38_fixed")
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        return self.diff_now()

    def test_hunks_are_exactly_the_changed_regions(self):
        units = parse_units(self.mixed_diff())

        self.assertEqual(
            [type(unit) for unit in units], [Hunk, Hunk, Hunk]
        )
        self.assertEqual(
            [unit.file_path for unit in units],
            ["src/app.py", "src/app.py", "src/notes.md"],
        )
        self.assertEqual(
            [unit.hunk_header for unit in units],
            ["@@ -1,6 +1,6 @@", "@@ -35,6 +35,6 @@ app_34", "@@ -2,7 +2,7 @@ notes_01"],
        )
        self.assertEqual(
            [(unit.line_start_old, unit.old_count) for unit in units],
            [(1, 6), (35, 6), (2, 7)],
        )
        self.assertEqual(
            [(unit.line_start_new, unit.new_count) for unit in units],
            [(1, 6), (35, 6), (2, 7)],
        )
        self.assertEqual([unit.ordinal for unit in units], [0, 1, 2])

    def test_hunk_content_is_verbatim(self):
        diff = self.mixed_diff()
        first = parse_units(diff)[0]

        self.assertEqual(
            first.content,
            "@@ -1,6 +1,6 @@\n"
            " app_01\n"
            " app_02\n"
            "-app_03\n"
            "+app_03_fixed\n"
            " app_04\n"
            " app_05\n"
            " app_06",
        )
        # The file header is kept whole — 'index', the '---'/'+++' pair and all
        # — so it is compared against the diff's own opening lines rather than
        # against a blob hash this test would have to keep in step by hand.
        self.assertEqual(first.file_header, "\n".join(diff.split("\n")[:4]))
        self.assertIn("index ", first.file_header)

    def test_rebuilt_patch_reproduces_the_working_tree(self):
        """The parse lost nothing — the strongest statement available."""
        diff = self.mixed_diff()
        expected = {name: self.read(name) for name in ("src/app.py", "src/notes.md")}

        rebuilt = build_patch(parse_units(diff))
        self.restore()

        checked = self._git("apply", "--check", "-", check=False)
        self.assertNotEqual(checked.returncode, 0, "stdin was not the patch")

        with open(os.path.join(self.dir, "_rebuilt.patch"), "w",
                  encoding="utf-8", newline="\n") as handle:
            handle.write(rebuilt)
        applied = self._git("apply", "_rebuilt.patch", check=False)
        self.assertEqual(applied.returncode, 0, applied.stderr)

        for name, content in expected.items():
            self.assertEqual(self.read(name), content, name)

    def test_ids_are_deterministic_across_parses(self):
        diff = self.mixed_diff()
        first = [unit.id for unit in parse_units(diff)]
        second = [unit.id for unit in parse_units(diff)]

        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), len(first))

    def test_identical_changes_in_two_files_get_different_ids(self):
        """A vendored copy and its original produce the same hunk, but not the
        same id — the paths are the only thing telling them apart."""
        self.commit("vendor/app_copy.py", block("app", 40), message="chore: seed copy")
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("vendor/app_copy.py", 3, "app_03_fixed")

        units = parse_units(self.diff_now())

        self.assertEqual(len(units), 2)
        self.assertEqual(units[0].hunk_header, units[1].hunk_header)
        self.assertEqual(units[0].content, units[1].content)
        self.assertNotEqual(units[0].id, units[1].id)

    def test_counts_decide_where_a_hunk_ends(self):
        """A removed line reading ``--- x`` is not a file header.

        Scanning for headers instead of counting would split this hunk in two
        at the lookalike pair — and the second half would then be applied as
        though it were a file of its own.
        """
        self.commit("src/prose.txt", HEADER_LOOKALIKE, message="chore: seed prose")
        self.write("src/prose.txt", HEADER_LOOKALIKE_CHANGED)

        units = parse_units(self.diff_now())

        self.assertEqual(len(units), 1)
        self.assertIn("--- removed", units[0].content)
        self.assertIn("+++ added", units[0].content)

        # The declared counts have to match the body actually captured: that is
        # the whole claim of count-driven parsing.
        body = units[0].content.split("\n")[1:]
        old_lines = sum(1 for line in body if line[:1] in (" ", "-"))
        new_lines = sum(1 for line in body if line[:1] in (" ", "+"))
        self.assertEqual((units[0].old_count, units[0].new_count), (old_lines, new_lines))

    def test_missing_newline_marker_stays_in_its_hunk(self):
        self.commit("src/readme.txt", "one\ntwo\nthree", message="chore: seed readme")
        self.write("src/readme.txt", "one\ntwo\nTHREE")

        units = parse_units(self.diff_now())

        self.assertEqual(len(units), 1)
        self.assertEqual(
            units[0].content,
            "@@ -1,3 +1,3 @@\n"
            " one\n"
            " two\n"
            "-three\n"
            "\\ No newline at end of file\n"
            "+THREE\n"
            "\\ No newline at end of file",
        )
        self.assertEqual((units[0].old_count, units[0].new_count), (3, 3))


class OpaqueTest(SplitRepoTestCase):
    """Sections with nothing to split: kept whole, labelled, sent nowhere."""

    def only(self, *pathspec):
        units = parse_units(self.diff_now(*pathspec))
        self.assertEqual(len(units), 1, units)
        self.assertIsInstance(units[0], OpaqueSection)
        return units[0]

    def test_binary_change(self):
        path = os.path.join(self.dir, "assets", "logo.bin")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(bytes(range(256)) * 4)
        self._git("add", "--", "assets/logo.bin")
        self._git("commit", "-m", "chore: seed binary")
        with open(path, "wb") as handle:
            handle.write(bytes(range(255, -1, -1)) * 4)

        unit = self.only("--", "assets/logo.bin")

        self.assertEqual(unit.reason, "binary")
        self.assertIn("GIT binary patch", unit.text)
        # Verbatim, 'index' line included: a binary patch names its blobs by it.
        self.assertIn("index ", unit.text)

    def test_pure_rename(self):
        self._git("mv", "src/notes.md", "src/renamed.md")

        unit = self.only()

        self.assertEqual(unit.reason, "rename")
        self.assertEqual(unit.file_path, "src/renamed.md")
        self.assertIn("rename from src/notes.md", unit.text)

    def test_mode_change_only(self):
        self._git("update-index", "--chmod=+x", "--", "src/notes.md")

        unit = self.only("--", "src/notes.md")

        self.assertEqual(unit.reason, "mode")
        self.assertIn("old mode 100644", unit.text)
        self.assertIn("new mode 100755", unit.text)

    def test_new_empty_file(self):
        self.write("src/empty.py", "")
        self._git("add", "--", "src/empty.py")

        unit = self.only()

        self.assertEqual(unit.reason, "empty")
        self.assertIn("new file mode", unit.text)

    def test_truncated_section_degrades_whole(self):
        units = parse_units(TRUNCATED)

        self.assertEqual(len(units), 1)
        self.assertIsInstance(units[0], OpaqueSection)
        self.assertEqual(units[0].reason, "malformed")
        self.assertIn("-app_02", units[0].text)

    def test_one_bad_hunk_costs_the_whole_section(self):
        """The valid hunk before the broken one is not salvaged."""
        units = parse_units(PARTLY_BROKEN)

        self.assertEqual(len(units), 1)
        self.assertIsInstance(units[0], OpaqueSection)
        self.assertEqual(units[0].reason, "malformed")


class BuildPatchTest(SplitRepoTestCase):
    """Rebuilding a patch from a subset — the operation staging depends on."""

    def three_hunks(self):
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("src/app.py", 38, "app_38_fixed")
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        return parse_units(self.diff_now())

    def test_subset_patch_stages_only_those_hunks(self):
        units = self.three_hunks()

        patch = build_patch([units[0]])

        self.assertIn("app_03_fixed", patch)
        self.assertNotIn("app_38_fixed", patch)
        self.assertNotIn("notes_05_documented", patch)

    def test_hunks_are_emitted_in_ordinal_order_whatever_the_caller_passes(self):
        units = self.three_hunks()

        self.assertEqual(build_patch(list(reversed(units))), build_patch(units))

    def test_file_header_is_emitted_once_per_file(self):
        units = self.three_hunks()

        patch = build_patch(units)

        self.assertEqual(patch.count("diff --git a/src/app.py"), 1)
        self.assertEqual(patch.count("diff --git a/src/notes.md"), 1)

    def test_index_line_is_dropped_from_hunk_bearing_headers(self):
        """The index line names a blob the index moves past after the first
        commit; keeping it would make git refuse a patch that matches."""
        patch = build_patch(self.three_hunks())

        self.assertNotIn("index f27c631..ee0bb6b", patch)

    def test_building_nothing_yields_nothing(self):
        self.assertEqual(build_patch([]), "")


if __name__ == "__main__":
    unittest.main()
