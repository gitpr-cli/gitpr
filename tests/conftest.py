"""Shared pytest configuration.

GitPR records every command in ~/.gitpr/logs — the user's real usage log. No
test isolates HOME, and several modules drive the CLI (test_config_cli.py,
test_main_suggest_reviewers.py, test_release_cli.py), so without this guard a
single `pytest` run would bury the genuine usage history under hundreds of test
invocations and make the log worthless.

Setting the variable here, before any project module is imported, is enough:
every load_dotenv() in the codebase runs with override=False, so it never
overwrites a variable that is already in the environment.

The same trick mutes the mandatory update gate: every `cli()` invocation would
otherwise query PyPI, and the three CLI suites above are unittest.TestCase
classes — pytest autouse fixtures never reach those, so an env switch set here
is the only way to keep them offline-safe. tests/test_updater.py clears it
explicitly to exercise the gate itself.
"""

import os

os.environ["GITPR_SHOW_LOGS"] = "false"
os.environ["GITPR_SKIP_UPDATE_CHECK"] = "true"
