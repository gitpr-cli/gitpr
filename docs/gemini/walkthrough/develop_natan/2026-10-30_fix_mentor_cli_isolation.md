# Walkthrough — Fix `tests/test_mentor_cli.py` Isolation

## Summary of Changes
Fixed test isolation issues in [`tests/test_mentor_cli.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/test_mentor_cli.py) where the mock targeted `src.core.get_git_diff` instead of `src.main.get_git_diff`.

Because `src/main.py` imports `get_git_diff` directly by value (`from src.core import get_git_diff`), `src.main` retained a reference to the unpatched original function, triggering actual Git operations on the local working tree during tests.

Changing the patch target to `src.main.get_git_diff` properly isolated both test cases (`test_review_without_mentor_is_opt_in` and `test_review_with_mentor_flag_invokes_append`).

## Validation Results
Executed `python -m pytest tests/test_mentor_cli.py -v`:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
collected 4 items

tests/test_mentor_cli.py::TestMentorCli::test_review_with_mentor_flag_invokes_append PASSED [ 25%]
tests/test_mentor_cli.py::TestMentorCli::test_review_without_mentor_is_opt_in PASSED [ 50%]
tests/test_mentor_cli.py::TestMentorCli::test_standalone_mentor_command_success PASSED [ 75%]
tests/test_mentor_cli.py::TestMentorCli::test_standalone_mentor_command_with_finding_id PASSED [100%]

============================== 4 passed in 5.52s ==============================
```
- Total tests in file: 4
- Passed: 4
- Failed: 0
- Production code altered: None
