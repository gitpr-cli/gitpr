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

GITPR_LANG pins the suite to English. Without it the language comes from the
developer's own ~/.gitpr/.env (and from the OS locale on a first run), so a
pt-BR machine renders Portuguese while the tests assert the English keys —
22 of them failed that way on 2026-09-21. Pinning it also stops the suite from
writing to the real profile: i18n skips the whole detection branch when the
variable is set, and an English language short-circuits get_translations()
before the OTA download and its set_key(LANG_VERSION).

GITPR_LINTER_SECURITY=false turns off the embedded secret ruleset, which is on
by default. Three suites assert on the rule list the real load_linter_rules()
returns — test_plugins.py (two assertEqual(rules, [])) and the two badge
modules that treat an empty list as "no linter rules configured" — and all
three would see the seven sec-* rules instead. Here as well the pin does double
duty: setup_environment() seeds every missing DEFAULT_CONFIG key into the real
~/.gitpr/.env, so a plain pytest run would otherwise write the two new keys
into the developer's profile, reintroducing exactly the write this suite was
made hermetic about. The new keys' own tests switch the ruleset back on with
monkeypatch.setenv, which wins over the file because every load_dotenv runs
with override=False.
"""

import os

os.environ["GITPR_SHOW_LOGS"] = "false"
os.environ["GITPR_SKIP_UPDATE_CHECK"] = "true"
os.environ["GITPR_LANG"] = "en_us"
os.environ["GITPR_LINTER_SECURITY"] = "false"

# Imported for its version constant, and for the side effect of loading src.i18n
# before the language variables below are added: i18n snapshots os.environ into
# AMBIENT_ENV_KEYS at import time, and the configuration screen flags every key
# in that snapshot as "set in the shell". A real session gets LANG_VERSION from
# the file, not from the shell, so the snapshot has to be taken first.
from src.updater import __lang_version__  # noqa: E402

# With the marker already at the code's version, get_translations() skips the
# download for every language the tests switch to (set_lang("pt_br") in
# test_core.py, for instance), which would otherwise rewrite ~/.gitpr/langs/*.json
# on every __lang_version__ bump.
os.environ["LANG_VERSION"] = __lang_version__
