"""The embedded secret ruleset: what it catches, how it routes, and what it never prints.

Two invariants carry most of the weight here. The first is that every regex
compiles: a rule with a typo does not crash the linter, it *multiplies* — the
engine reports the invalid regex once per diff line, so a broken pattern turns a
one-line mistake into a wall of blocking alerts. The second is that no alert ever
contains the value it matched. An alert travels to the console, to the Markdown
report and, in the commit flow, to a pull request body; a message that echoed the
matched text would copy the secret into every one of those places, which is the
opposite of the point.

Assertions name the rule and the bucket it landed in, never the rendered
sentence: the messages go through ``__()``, so their text follows the machine's
language, and a test that asserted English prose would pass here and fail on a
translated machine (or the reverse).

Every fake secret below is assembled from fragments on purpose. ``gitpr -l``
runs from this repository's own pre-commit hook and exits non-zero on an error,
so a literal secret written here would be a diff that blocks its own commit.
"""

import json
import re
from pathlib import Path

import pytest

from src.linter_engine import _apply_rule, _is_rule_applicable, parse_diff_and_lint
from src.security_ruleset import SECURITY_RULES

REPO = Path(__file__).resolve().parent.parent
LANG_FILES = (
    "pt_br.json",
    "pt_pt.json",
    "es_es.json",
    "es.json",
    "fr_fr.json",
    "fr.json",
)

# Fragments, never contiguous literals — see the module docstring.
AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
GITHUB_TOKEN = "ghp_" + "a" * 36
SLACK_TOKEN = "xox" + "b-123456789012-abcdefghijklmnop"
GOOGLE_KEY = "AIza" + "B" * 35
PRIVATE_KEY_HEADER = "-----BEGIN OPENSSH " + "PRIVATE KEY-----"
DB_URL = "postgres://user:" + "s3cr3t@localhost:5432/db"
GENERIC_VALUE = "hunter2xyz"

# The keyword is split as well, not just the value: a contiguous
# ``password = "..."`` anywhere in this file — a fixture, an f-string, a literal
# in an assertion — is a line the rule under test reports on, and this repo's own
# pre-commit hook lints the diff that adds it.
CREDENTIAL_LINE = "pass" + 'word = "{}"'

# A realistic line per rule, for the tests that run one regex at a time.
POSITIVES = {
    "sec-aws-access-key": 'aws_access_key_id = "' + AWS_KEY + '"',
    "sec-github-token": 'github_token = "' + GITHUB_TOKEN + '"',
    "sec-slack-token": 'SLACK_BOT_TOKEN = "' + SLACK_TOKEN + '"',
    "sec-google-api-key": 'GOOGLE_API_KEY = "' + GOOGLE_KEY + '"',
    "sec-private-key-block": PRIVATE_KEY_HEADER,
    "sec-db-connection-string": 'DATABASE_URL = "' + DB_URL + '"',
    "sec-generic-credential-assignment": CREDENTIAL_LINE.format(GENERIC_VALUE),
}

# One line per rule for the end-to-end run. The assignments are deliberately
# bare: a variable named ``*_token`` would also satisfy the generic rule, and
# this test counts alerts, so each line has to trip exactly one rule.
NEUTRAL_POSITIVES = {
    "sec-aws-access-key": 'k1 = "' + AWS_KEY + '"',
    "sec-github-token": 'k2 = "' + GITHUB_TOKEN + '"',
    "sec-slack-token": 'k3 = "' + SLACK_TOKEN + '"',
    "sec-google-api-key": 'k4 = "' + GOOGLE_KEY + '"',
    "sec-private-key-block": PRIVATE_KEY_HEADER,
    "sec-db-connection-string": 'k5 = "' + DB_URL + '"',
    "sec-generic-credential-assignment": CREDENTIAL_LINE.format(GENERIC_VALUE),
}

# The values that must never appear in an alert.
SECRET_VALUES = {
    "sec-aws-access-key": "IOSFODNN7EXAMPLE",
    "sec-github-token": "a" * 36,
    "sec-slack-token": "abcdefghijklmnop",
    "sec-google-api-key": "B" * 35,
    "sec-private-key-block": "PRIVATE KEY",
    "sec-db-connection-string": "s3cr3t",
    "sec-generic-credential-assignment": GENERIC_VALUE,
}

ERROR_RULES = {name for name, rule in ((r["name"], r) for r in SECURITY_RULES) if rule["level"] == "error"}
WARNING_RULES = {r["name"] for r in SECURITY_RULES if r["level"] == "warning"}


def build_diff(lines):
    """A minimal unified diff whose added lines are ``lines``, in order."""
    body = "".join(f"+{line}\n" for line in lines)
    return (
        "diff --git a/app.py b/app.py\n"
        "index 1111111..2222222 100644\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        f"@@ -1,1 +1,{len(lines)} @@\n"
        f"{body}"
    )


def rules_by_name():
    return {rule["name"]: rule for rule in SECURITY_RULES}


@pytest.fixture
def linter(monkeypatch, tmp_path):
    """The linter with this machine's rules and telemetry taken out of the way.

    Without the first two patches the developer's own ``.gitpr/skill/`` rules
    and ``~/.gitpr/plugins/linter/`` would join every assertion; without the
    third, ``parse_diff_and_lint`` appends to the real ``~/.gitpr/metrics``.
    """
    monkeypatch.setattr(
        "src.config.resolve_skill_path", lambda name: str(tmp_path / "absent.yml")
    )
    monkeypatch.setattr("src.config.get_linter_plugins", lambda: [])
    monkeypatch.setattr("src.linter_engine.log_local_metric", lambda *a, **k: None)
    return tmp_path


class TestRulesetShape:
    def test_every_rule_has_the_schema_the_engine_reads(self):
        for rule in SECURITY_RULES:
            assert rule["name"]
            assert rule["regex"]
            assert rule["message"]
            assert rule["level"] in {"error", "warning"}
            assert rule["extensions"] == ["*"]

    def test_rule_names_are_unique_and_namespaced(self):
        names = [rule["name"] for rule in SECURITY_RULES]
        assert len(names) == len(set(names)) == 7
        assert all(name.startswith("sec-") for name in names)

    def test_messages_keep_both_placeholders(self):
        """The engine substitutes exactly two tokens, with str.replace.

        A message missing one of them still renders — it just loses the
        location, silently. That is the failure this holds shut.
        """
        for rule in SECURITY_RULES:
            assert "{file_name}" in rule["message"], rule["name"]
            assert "{line_number}" in rule["message"], rule["name"]


class TestRegexCompiles:
    def test_every_regex_compiles(self):
        """A typo here is not a crash — it is one blocking alert per line."""
        for rule in SECURITY_RULES:
            re.compile(rule["regex"])


class TestPositiveDetection:
    @pytest.mark.parametrize("name", sorted(POSITIVES))
    def test_the_category_is_detected(self, name):
        rule = rules_by_name()[name]
        assert re.search(rule["regex"], POSITIVES[name])


class TestNegativeDetection:
    """Near misses: a value that looks like the category but is not one."""

    NEAR_MISSES = {
        "sec-aws-access-key": ["k = " + '"AKIA' + 'IOSFODNN7EXAMPL"'],
        "sec-github-token": ["k = " + '"ghp_' + "a" * 35 + '"'],
        "sec-slack-token": ["k = " + '"xox' + 'b-12345"'],
        "sec-google-api-key": ["k = " + '"AIza' + "B" * 34 + '"'],
        "sec-private-key-block": [
            "-----BEGIN CERTIFICATE-----",
            "-----BEGIN PUBLIC " + "KEY-----",
        ],
        "sec-db-connection-string": [
            'DATABASE_URL = "postgresql://localhost:5432/db"',
            'DATABASE_URL = "postgresql://user@localhost/db"',
            'URL = "https://example.com/user:pass@host"',
        ],
        "sec-generic-credential-assignment": [CREDENTIAL_LINE.format("abc")],
    }

    @pytest.mark.parametrize("name", sorted(NEAR_MISSES))
    def test_the_near_miss_is_ignored(self, name):
        rule = rules_by_name()[name]
        for line in self.NEAR_MISSES[name]:
            assert not re.search(rule["regex"], line), line


class TestPlaceholderFilter:
    """The negative lookahead is the rule's whole reason to be a warning."""

    @pytest.mark.parametrize(
        "value",
        [
            "changeme",
            "CHANGEME",
            "your_password_here",
            "your-password-here",
            "xxxxxx",
            "placeholder",
            "example",
            "dummy",
            "sample",
            "sua_senha",
        ],
    )
    def test_a_placeholder_is_not_a_credential(self, value):
        rule = rules_by_name()["sec-generic-credential-assignment"]
        assert not re.search(rule["regex"], CREDENTIAL_LINE.format(value))

    def test_a_real_value_is_still_a_credential(self):
        rule = rules_by_name()["sec-generic-credential-assignment"]
        assert re.search(rule["regex"], CREDENTIAL_LINE.format(GENERIC_VALUE))

    def test_a_placeholder_with_a_suffix_is_a_value(self):
        """The lookahead matches the whole placeholder, not a prefix of it."""
        rule = rules_by_name()["sec-generic-credential-assignment"]
        assert re.search(rule["regex"], CREDENTIAL_LINE.format("your_password_here2"))


class TestLevelRouting:
    """Which bucket an alert lands in, read from the rule and not from prose."""

    @pytest.mark.parametrize("name", sorted(ERROR_RULES))
    def test_an_error_rule_blocks(self, name):
        rule = rules_by_name()[name]
        alerts = {"errors": [], "warnings": []}
        _apply_rule(rule, POSITIVES[name], 7, "app.py", alerts)
        expected = rule["message"].replace("{file_name}", "app.py").replace(
            "{line_number}", "7"
        )
        assert alerts == {"errors": [expected], "warnings": []}

    @pytest.mark.parametrize("name", sorted(WARNING_RULES))
    def test_a_warning_rule_reports(self, name):
        rule = rules_by_name()[name]
        alerts = {"errors": [], "warnings": []}
        _apply_rule(rule, POSITIVES[name], 7, "app.py", alerts)
        expected = rule["message"].replace("{file_name}", "app.py").replace(
            "{line_number}", "7"
        )
        assert alerts == {"errors": [], "warnings": [expected]}


class TestExtensionWildcard:
    """`extensions: ["*"]` is what covers the files secrets actually leak from."""

    def test_a_rule_applies_to_a_file_with_no_extension(self):
        rule = rules_by_name()["sec-aws-access-key"]
        assert _is_rule_applicable(rule, "id_rsa", "")

    def test_a_rule_applies_to_a_dotfile(self):
        rule = rules_by_name()["sec-aws-access-key"]
        assert _is_rule_applicable(rule, ".env", "env")

    def test_a_rule_without_the_wildcard_is_still_refused(self):
        """The wildcard is opt-in: the other rules keep their suffix filter."""
        rule = {"name": "x", "extensions": ["py"]}
        assert not _is_rule_applicable(rule, "id_rsa", "")
        assert not _is_rule_applicable(rule, ".env", "env")


class TestMergeIntoLoadLinterRules:
    def test_the_ruleset_is_off_when_configured_off(self, linter, monkeypatch):
        monkeypatch.setenv("GITPR_LINTER_SECURITY", "false")
        from src.config import load_linter_rules

        assert [r for r in load_linter_rules() if r["name"].startswith("sec-")] == []

    def test_the_ruleset_is_on_when_configured_on(self, linter, monkeypatch):
        monkeypatch.setenv("GITPR_LINTER_SECURITY", "true")
        from src.config import load_linter_rules

        names = {r["name"] for r in load_linter_rules()}
        assert names == {rule["name"] for rule in SECURITY_RULES}

    def test_a_single_rule_can_be_dropped_by_name(self, linter, monkeypatch):
        monkeypatch.setenv("GITPR_LINTER_SECURITY", "true")
        monkeypatch.setenv(
            "GITPR_LINTER_SECURITY_DISABLED_RULES", "sec-db-connection-string"
        )
        from src.config import load_linter_rules

        names = {r["name"] for r in load_linter_rules()}
        assert "sec-db-connection-string" not in names
        assert len(names) == len(SECURITY_RULES) - 1

    def test_the_project_and_plugin_rules_survive_the_merge(
        self, tmp_path, monkeypatch
    ):
        skill_dir = tmp_path / ".gitpr" / "skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / ".gitpr.linter.yml").write_text(
            "rules:\n"
            '  - name: "local-rule"\n'
            '    level: "error"\n'
            '    extensions: ["py"]\n'
            '    regex: "FIXME"\n'
            '    message: "FIXME in {file_name} (Line {line_number})."\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "src.config.resolve_skill_path",
            lambda name: str(skill_dir / ".gitpr.linter.yml"),
        )
        monkeypatch.setattr("src.config.get_linter_plugins", lambda: [])
        monkeypatch.setenv("GITPR_LINTER_SECURITY", "true")

        from src.config import load_linter_rules

        names = [r["name"] for r in load_linter_rules()]
        assert "local-rule" in names
        assert len(names) == len(SECURITY_RULES) + 1


class TestTheDefaultIsOn:
    def test_an_unset_variable_keeps_the_ruleset_on(self, linter, monkeypatch):
        """The opt-out is fail-open: only a recognised negative turns it off.

        ``ENV_FILE`` is redirected so the answer does not depend on whether the
        developer's own profile already carries the key.
        """
        monkeypatch.setattr("src.config.ENV_FILE", str(linter / "profile.env"))
        monkeypatch.delenv("GITPR_LINTER_SECURITY", raising=False)
        from src.config import load_linter_rules

        names = {r["name"] for r in load_linter_rules()}
        assert names == {rule["name"] for rule in SECURITY_RULES}

    def test_unknown_text_does_not_turn_the_ruleset_off(self, linter, monkeypatch):
        monkeypatch.setenv("GITPR_LINTER_SECURITY", "maybe")
        from src.config import load_linter_rules

        assert len(load_linter_rules()) == len(SECURITY_RULES)


class TestEndToEndThroughTheEngine:
    def _run(self, linter, monkeypatch):
        monkeypatch.setenv("GITPR_LINTER_SECURITY", "true")
        diff = build_diff([NEUTRAL_POSITIVES[name] for name in sorted(NEUTRAL_POSITIVES)])
        return parse_diff_and_lint(diff, skip_external=True)

    def test_each_rule_lands_in_the_bucket_its_level_names(self, linter, monkeypatch):
        alerts = self._run(linter, monkeypatch)
        assert len(alerts["errors"]) == len(ERROR_RULES)
        assert len(alerts["warnings"]) == len(WARNING_RULES)

    def test_no_alert_echoes_the_value_it_matched(self, linter, monkeypatch):
        """The invariant that keeps the secret out of reports and pull requests."""
        alerts = self._run(linter, monkeypatch)
        for alert in alerts["errors"] + alerts["warnings"]:
            for value in SECRET_VALUES.values():
                assert value not in alert, alert

    def test_the_alert_names_the_file_and_the_line(self, linter, monkeypatch):
        alerts = self._run(linter, monkeypatch)
        for alert in alerts["errors"] + alerts["warnings"]:
            assert "app.py" in alert


class TestTranslations:
    """The six catalogues carry the new keys, translated, with the placeholders.

    Read straight from ``langs/`` as JSON — no ``src.i18n`` involved, so the
    result does not depend on the language this process happened to start in.
    """

    KEYS = [rule["message"] for rule in SECURITY_RULES] + [
        "Secret Scanning",
        "Disabled Security Rules",
        "Looks for hardcoded credentials in every file: provider keys, private key blocks, database URLs and password assignments.",
        "Security rule names to skip, separated by semicolons. Empty runs all of them.",
    ]

    @pytest.mark.parametrize("filename", LANG_FILES)
    def test_every_new_key_is_present_and_translated(self, filename):
        data = json.loads((REPO / "langs" / filename).read_text(encoding="utf-8"))
        for key in self.KEYS:
            assert key in data, f"{filename}: missing {key!r}"
            assert data[key] != key, f"{filename}: untranslated {key!r}"

    @pytest.mark.parametrize("filename", LANG_FILES)
    def test_the_rule_messages_keep_both_placeholders(self, filename):
        data = json.loads((REPO / "langs" / filename).read_text(encoding="utf-8"))
        for rule in SECURITY_RULES:
            value = data[rule["message"]]
            assert "{file_name}" in value, f"{filename}: {rule['name']}"
            assert "{line_number}" in value, f"{filename}: {rule['name']}"
