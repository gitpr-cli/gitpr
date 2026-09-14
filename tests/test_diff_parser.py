"""Unit tests for the pure unified-diff parser (parse_added_lines, summarize_patch)."""
import unittest

from src.diff_parser import parse_added_lines, summarize_patch


class TestSimpleHunk(unittest.TestCase):
    def test_added_and_removed_lines(self):
        diff = """diff --git a/src/a.py b/src/a.py
index 1111111..2222222 100644
--- a/src/a.py
+++ b/src/a.py
@@ -1,4 +1,5 @@
 def hello():
-    return 1
+    # new comment
+    return 2
     extra
"""
        result = parse_added_lines(diff)
        # New-side numbering with -U1: hunk starts at new line 1, the context
        # line occupies line 1, so the two additions land at 2 and 3.
        self.assertEqual(result["src/a.py"], [2, 3])

    def test_context_offset_after_removal(self):
        diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -5,3 +4,3 @@
 x
-removed
 y
+added
 z
"""
        # Context 'x' is old 5/new 4; added line lands at new 6.
        self.assertEqual(parse_added_lines(diff)["a.py"], [6])


class TestMultipleHunks(unittest.TestCase):
    def test_several_hunks_accumulate(self):
        diff = """diff --git a/f.py b/f.py
--- a/f.py
+++ b/f.py
@@ -1,2 +1,2 @@
-aa
+a
@@ -10,1 +10,2 @@
 bb
+b
"""
        result = parse_added_lines(diff)["f.py"]
        self.assertEqual(result, [1, 11])

    def test_deletion_only_hunk_adds_nothing(self):
        diff = """diff --git a/f.py b/f.py
--- a/f.py
+++ b/f.py
@@ -3,2 +2,0 @@
-d1
-d2
"""
        result = parse_added_lines(diff)
        self.assertEqual(result.get("f.py"), None)


class TestRenamesAndNewFiles(unittest.TestCase):
    def test_rename_uses_new_side_path(self):
        diff = """diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
index 111..222 100644
--- a/old_name.py
+++ b/new_name.py
@@ -1,1 +1,2 @@
 hello
+world
"""
        result = parse_added_lines(diff)
        self.assertNotIn("old_name.py", result)
        self.assertEqual(result["new_name.py"], [2])

    def test_new_file_from_dev_null(self):
        diff = """diff --git a/new_file.txt b/new_file.txt
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/new_file.txt
@@ -0,0 +1,3 @@
+one
+two
+three
"""
        self.assertEqual(parse_added_lines(diff)["new_file.txt"], [1, 2, 3])

    def test_deleted_file_is_ignored(self):
        diff = """diff --git a/gone.txt b/gone.txt
deleted file mode 100644
index 1111111..0000000
--- a/gone.txt
+++ /dev/null
@@ -1,2 +0,0 @@
-x
-y
"""
        result = parse_added_lines(diff)
        self.assertIsNone(result.get("gone.txt"))


class TestSpecialContent(unittest.TestCase):
    def test_no_newline_marker_does_not_shift(self):
        diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
 old
\\ No newline at end of file
+new
+tail
\\ No newline at end of file
"""
        self.assertEqual(parse_added_lines(diff)["a.py"], [2, 3])

    def test_plus_prefixed_content_inside_hunk_is_an_addition(self):
        diff = """diff --git a/md.md b/md.md
--- a/md.md
+++ b/md.md
@@ -1,0 +1,2 @@
+++ a literal plus heading
++ text
"""
        # Both lines are added content beginning with '++'.
        self.assertEqual(parse_added_lines(diff)["md.md"], [1, 2])

    def test_binary_and_mode_only_changes_have_no_lines(self):
        diff = """diff --git a/img.png b/img.png
index 1111111..2222222 100644
Binary files a/img.png and b/img.png differ
diff --git a/exe b/exe
old mode 100644
new mode 100755
"""
        self.assertEqual(parse_added_lines(diff), {})

    def test_quoted_path_with_spaces(self):
        diff = """diff --git "a/my file.txt" "b/my file.txt"
--- "a/my file.txt"
+++ "b/my file.txt"
@@ -1,1 +1,2 @@
 hello
+world
"""
        self.assertEqual(parse_added_lines(diff)["my file.txt"], [2])

    def test_octal_escaped_non_ascii_path(self):
        diff = """diff --git "a/caf\\303\\251.py" "b/caf\\303\\251.py"
--- "a/caf\\303\\251.py"
+++ "b/caf\\303\\251.py"
@@ -0,0 +1,1 @@
+ol\\303\\241
"""
        result = parse_added_lines(diff)
        # \303\251 is the UTF-8 byte pair for "e-acute" in git's octal quoting.
        self.assertEqual(result["café.py"], [1])


class TestEmptyAndRobustness(unittest.TestCase):
    def test_empty_diff_returns_empty(self):
        self.assertEqual(parse_added_lines(""), {})
        self.assertEqual(parse_added_lines("  \n"), {})

    def test_unrecognized_lines_are_ignored(self):
        diff = """diff --git a/x b/x
weird header line
--- a/x
+++ b/x
@@ -1,1 +1,2 @@
 base
+added
"""
        self.assertEqual(parse_added_lines(diff)["x"], [2])

    def test_multiple_files(self):
        diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,1 +1,2 @@
 x
+a1
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1,1 +1,2 @@
 y
+b1
"""
        result = parse_added_lines(diff)
        self.assertEqual(result["a.py"], [2])
        self.assertEqual(result["b.py"], [2])


class TestSummarizePatch(unittest.TestCase):
    def test_counts_files_hunks_and_lines(self):
        diff = """diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,4 +1,5 @@
 def hello():
-    return 1
+    # new comment
+    return 2
     extra
"""
        summary = summarize_patch(diff)
        self.assertEqual(summary.files, ("src/a.py",))
        self.assertEqual(summary.hunks, 1)
        self.assertEqual(summary.added, 2)
        self.assertEqual(summary.removed, 1)
        # The removed text is kept verbatim (sans the '-' marker) so a caller
        # can tell a deleted function call from a deleted blank line.
        self.assertEqual(summary.removed_lines, ("    return 1",))

    def test_headers_are_not_counted_as_changes(self):
        # '--- a/x' looks like a removal and '+++ b/x' like an addition; both
        # sit outside a hunk and must stay out of the counts.
        diff = """diff --git a/x b/x
--- a/x
+++ b/x
@@ -1,1 +1,1 @@
-old
+new
"""
        summary = summarize_patch(diff)
        self.assertEqual((summary.added, summary.removed), (1, 1))

    def test_multiple_hunks_and_files_keep_order(self):
        diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,2 @@
-aa
+a
@@ -10,1 +10,2 @@
 bb
+b
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1,1 +1,1 @@
-c
+d
"""
        summary = summarize_patch(diff)
        self.assertEqual(summary.files, ("a.py", "b.py"))
        self.assertEqual(summary.hunks, 3)
        self.assertEqual(summary.added, 3)
        self.assertEqual(summary.removed, 2)

    def test_no_newline_marker_is_ignored(self):
        diff = """diff --git a/x b/x
--- a/x
+++ b/x
@@ -1,1 +1,1 @@
-old
+new
\\ No newline at end of file
"""
        summary = summarize_patch(diff)
        self.assertEqual((summary.added, summary.removed), (1, 1))
        self.assertEqual(summary.removed_lines, ("old",))

    def test_deletion_keeps_the_file_name(self):
        # A full deletion prints '+++ /dev/null', so the only place its name
        # appears is the 'diff --git' line.
        diff = """diff --git a/gone.py b/gone.py
deleted file mode 100644
--- a/gone.py
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
"""
        summary = summarize_patch(diff)
        self.assertEqual(summary.files, ("gone.py",))
        self.assertEqual((summary.added, summary.removed), (0, 2))

    def test_ai_style_diff_without_git_header(self):
        # An AI commonly returns hunks with no 'diff --git' line at all.
        diff = """--- a/mod.py
+++ b/mod.py
@@ -1,1 +1,2 @@
 keep
+added
"""
        summary = summarize_patch(diff)
        self.assertEqual(summary.files, ("mod.py",))
        self.assertEqual(summary.hunks, 1)
        self.assertEqual(summary.added, 1)

    def test_quoted_path_with_space_is_decoded(self):
        diff = """diff --git "a/my file.txt" "b/my file.txt"
--- "a/my file.txt"
+++ "b/my file.txt"
@@ -1,1 +1,2 @@
 hello
+world
"""
        self.assertEqual(summarize_patch(diff).files, ("my file.txt",))


class TestSummarizePatchRobustness(unittest.TestCase):
    def test_text_without_a_diff_is_empty(self):
        for text in ("", "  \n", "just prose, no diff here", "```python\nx = 1\n```"):
            with self.subTest(text=text):
                summary = summarize_patch(text)
                self.assertEqual(summary.files, ())
                self.assertEqual(summary.hunks, 0)
                self.assertEqual((summary.added, summary.removed), (0, 0))
                self.assertEqual(summary.removed_lines, ())

    def test_mode_only_change_has_no_hunks(self):
        diff = """diff --git a/script.sh b/script.sh
old mode 100644
new mode 100755
"""
        summary = summarize_patch(diff)
        self.assertEqual(summary.files, ("script.sh",))
        self.assertEqual(summary.hunks, 0)

    def test_malformed_hunk_header_is_not_counted(self):
        # A hunk whose header does not parse leaves the reader outside any
        # hunk, so the '+not counted' line is skipped rather than miscounted.
        diff = """diff --git a/x b/x
--- a/x
+++ b/x
@@ broken @@
+not counted
"""
        summary = summarize_patch(diff)
        self.assertEqual(summary.hunks, 0)
        self.assertEqual(summary.added, 0)

    def test_a_file_is_listed_once(self):
        diff = """diff --git a/x b/x
--- a/x
+++ b/x
@@ -1,1 +1,1 @@
-a
+b
@@ -9,1 +9,1 @@
-c
+d
"""
        self.assertEqual(summarize_patch(diff).files, ("x",))


if __name__ == "__main__":
    unittest.main()
