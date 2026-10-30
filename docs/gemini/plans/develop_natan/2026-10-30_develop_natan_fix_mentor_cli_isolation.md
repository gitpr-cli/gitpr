# Implementation Plan — Fix `tests/test_mentor_cli.py` Isolation

## Goal Description
Fix the two oldest failing tests in `tests/test_mentor_cli.py` (`test_review_without_mentor_is_opt_in` and `test_review_with_mentor_flag_invokes_append`).
Currently, both tests patch `src.core.get_git_diff`. However, `src/main.py` imports `get_git_diff` by value (`from src.core import get_git_diff`), creating a module-level binding in `src.main`.
When `cli` runs during test execution, it invokes `src.main.get_git_diff` (which remains unmocked), causing real Git operations against the working directory and breaking test isolation.
Changing the patch target to `src.main.get_git_diff` restores complete test isolation without altering any production code.

## User Review Required
> [!NOTE]
> Following Python's standard `unittest.mock` rule ("patch where an object is looked up, not where it is defined"), the fix is applied exclusively to `tests/test_mentor_cli.py`. Production code (`src/main.py`) remains untouched.

## Proposed Changes

### Tests
#### [MODIFY] `tests/test_mentor_cli.py`
- In `test_review_without_mentor_is_opt_in` (line 32):
  Change `@patch("src.core.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")`
  to `@patch("src.main.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")`
- In `test_review_with_mentor_flag_invokes_append` (line 50):
  Change `@patch("src.core.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")`
  to `@patch("src.main.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")`

```diff
--- a/tests/test_mentor_cli.py
+++ b/tests/test_mentor_cli.py
@@ -29,7 +29,7 @@ class TestMentorCli(unittest.TestCase):
     @patch("src.main.render_review_result")
     @patch("src.main.parse_diff_and_lint", return_value={"errors": [], "warnings": []})
     @patch("src.main.generate_pr_content")
-    @patch("src.core.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")
+    @patch("src.main.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")
     @patch("src.main._append_mentor_section")
     def test_review_without_mentor_is_opt_in(
         self, mock_append, mock_diff, mock_gen_pr, mock_linter, mock_render
@@ -47,7 +47,7 @@ class TestMentorCli(unittest.TestCase):
     @patch("src.main.render_review_result")
     @patch("src.main.parse_diff_and_lint", return_value={"errors": [], "warnings": []})
     @patch("src.main.generate_pr_content")
-    @patch("src.core.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")
+    @patch("src.main.get_git_diff", return_value="diff --git a/a.py b/a.py\n+new line")
     @patch("src.main._append_mentor_section")
     def test_review_with_mentor_flag_invokes_append(
```

## Verification Plan

### Automated Tests
Run pytest specifically for `tests/test_mentor_cli.py`:
```bash
python -m pytest tests/test_mentor_cli.py -v
```
All 4 test cases (`test_review_without_mentor_is_opt_in`, `test_review_with_mentor_flag_invokes_append`, `test_standalone_mentor_command_success`, `test_standalone_mentor_command_with_finding_id`) must pass with 0 failures.

### Manual Verification
Ensure that no files in `src/` are modified (`git status -s` shows only `tests/test_mentor_cli.py` modified).
