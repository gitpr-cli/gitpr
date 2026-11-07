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

GITPR_SKIP_PROJECT_CONFIG_SEED stops cli() from seeding
.gitpr/conf/gitpr.config.yml. The seed runs on every invocation, and dozens of
CliRunner tests invoke the CLI with the repository as the working directory —
without the switch the first pytest run would create a real, versioned project
file in the checkout. The project-file tests create theirs in a temporary
repository instead.
"""

import os
import sys

import pytest

os.environ["GITPR_SHOW_LOGS"] = "false"
os.environ["GITPR_SKIP_UPDATE_CHECK"] = "true"
os.environ["GITPR_SKIP_PROJECT_CONFIG_SEED"] = "true"
os.environ["GITPR_LANG"] = "en_us"
os.environ["GITPR_LINTER_SECURITY"] = "false"

# Imported for its version constant, and for the side effect of loading src.i18n
# before the language variables below are added: i18n snapshots os.environ into
# AMBIENT_ENV_KEYS at import time, and the configuration screen flags every key
# in that snapshot as "set in the shell". A real session gets LANG_VERSION from
# the file, not from the shell, so the snapshot has to be taken first.
from src import i18n  # noqa: E402
from src.updater import __lang_version__  # noqa: E402

# With the marker already at the code's version, get_translations() skips the
# download for every language the tests switch to (set_lang("pt_br") in
# test_core.py, for instance), which would otherwise rewrite ~/.gitpr/langs/*.json
# on every __lang_version__ bump.
os.environ["LANG_VERSION"] = __lang_version__

# Several tests drive the PR flow; a developer profile with the issue-autoclose
# feature off would change which path they exercise. Set after the i18n
# snapshot so the configuration screen does not flag the field as "set in the
# shell".
os.environ["GITPR_ISSUE_AUTOCLOSE"] = "true"


@pytest.fixture(autouse=True)
def english_interface():
    """Pins the interface language to English around every test.

    English is the one language that needs no translation file — ``__()``
    falls back to the key itself — so assertions can name the expected text
    without depending on the developer's ``~/.gitpr/langs``. A test that wants
    another language patches ``src.i18n`` itself, which wins over this.

    The pin is repeated before every test, not just once at import, because
    two product paths change the language long after that and both are right
    to do so: the configuration screen re-reads the .env it has just saved
    (``load_dotenv(..., override=True)``) and applies GITPR_LANG from it, and
    the MCP tool path re-applies GITPR_LANG at every call (``_init_config()``
    -> ``set_lang()``), because a long-lived server should keep the user's
    language. Neither puts the previous value back, so the suite can inherit
    the developer's own profile (pt_br on the machine this was found) and
    every module collected after test_mcp_server.py then asserts English keys
    against Portuguese strings — 28 failures on 2026-11-07, in runs that
    differed only by timing. Autouse fixtures do run for the unittest.TestCase
    classes, so this reaches them too.
    """
    os.environ["GITPR_LANG"] = "en_us"
    i18n.CURRENT_LANG = "en_us"
    i18n.TRANSLATIONS = {}


@pytest.fixture(autouse=True)
def no_hook_script_sync(monkeypatch):
    """Keeps the hooks auto-sync out of every test that drives the CLI.

    ``cli()`` calls ``check_and_update_hooks_scripts()`` on every run. Its gate
    compares the markers in the developer's real ``~/.gitpr/.env`` against the
    shipped version and the wanted hook language; when they differ it downloads
    the hook scripts into ``.git/hooks`` of whatever repository is current and
    then re-reads that ``.env`` with ``load_dotenv(..., override=True)`` — which
    merges the whole profile into the test process, beating every pin this file
    sets at import.

    That is exactly what happened on 2026-11-07: a CliRunner test running in
    the checkout itself opened the gate, ``GITPR_LINTER_SECURITY`` went from the
    pinned ``false`` to the profile's ``true``, and the eight
    ``test_plugins.py::TestLoadLinterRulesWithPlugins`` tests that assert exact
    rule counts failed from that point on — while the same module passed alone,
    and while runs that skipped the gate were green. The run had also rewritten
    the developer's real ``.git/hooks`` and stamped SCRIPTS_INSTALLED_LANG in
    their profile: once stamped, the gate closes and the leak stops happening,
    which is why the failure came and went between runs.

    A test that wants the sync exercises ``src.core.check_and_update_hooks_scripts``
    directly (as tests/test_core.py does); a CLI test that needs to observe the
    call patches ``src.main.check_and_update_hooks_scripts`` itself, and that
    patch wins over this one. The attribute is patched only when ``src.main``
    has already been imported — every CLI test imports ``cli`` at module level,
    so it always is — because importing it here would pull the AI stack into
    runs that have nothing to do with the CLI.
    """
    main_module = sys.modules.get("src.main")
    if main_module is not None:
        monkeypatch.setattr(main_module, "check_and_update_hooks_scripts", lambda: None)
