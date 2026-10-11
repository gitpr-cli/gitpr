"""The ``gitpr baseline`` group through Click's runner.

Four properties are worth a test that goes in through the front door rather
than through the use case.

The first is the **write guard**, shared with the policy group: every command
that edits the record asks before it does, and ``--yes`` answers the question
without skipping the checks behind it. ``CliRunner`` is a terminal-less caller,
so the refusal is the default here and ``--yes`` is what has to be asked for.

The second is that the prompts and the verdicts are **about the right finding**.
An auditable suppression whose subject is invisible is not one, so the describe
step resolves the id before the question is asked, and the tests read the entry
back afterwards to check the decision landed where it said it would.

The third is that the group is **runnable at all** — six commands, their
options, their exit codes and the documentation link in the epilog are the
surface a user meets, and a missing import inside one of them only shows up
when it runs. That includes the exit codes, which are the contract a hook or a
CI job reads: a defect in the file is exit 1, a missing file is exit 1, and a
sound one is exit 0.

The fourth is that the tests never touch the developer's machine. The
repository is a ``tempfile`` tree the process moves into, the prompt cache is
redirected, the network probe is stubbed and the ledgers are patched, so a stray
run writes nothing anywhere real.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from src.domain.baseline import set_active_baseline
from src.main import cli
from tests.fix.git_fixture import GitRepoTestCase

# One rule, one construct: an alert line is the rule's message, which carries
# neither the rule's name nor a line number — the case that makes the fingerprint
# the only way to tell two findings apart.
LINTER_RULES = """rules:
  - name: legacy-no-eval
    regex: '\\beval\\('
    message: "eval() executes arbitrary code."
    extensions: ["*"]
"""

EVAL = "eval() executes arbitrary code."
LEGACY_FILE = "app/legacy.py"
CLEAN_SOURCE = "def boot():\n    return 0\n"
HOOK = ".git/COMMIT_EDITMSG"

BASELINE = os.path.join(".gitpr", "baseline.json")
OVERRIDES = os.path.join(".gitpr", "baseline.overrides.yml")

PINNED_ENV = {
    "GITPR_BASELINE_ENABLED": "true",
    "GITPR_BASELINE_PATH": "",
    "GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH": "true",
    "GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES": "true",
    "GITPR_LANG": "en_us",
    "GITPR_SKIP_UPDATE_CHECK": "true",
}


class BaselineCliTestCase(GitRepoTestCase):
    """A repository with a rules file, and a runner that stands inside it."""

    prefix = "gitpr_baseline_cli_"

    def setUp(self):
        super().setUp()
        self._cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, self._cwd)

        env = patch.dict(os.environ, dict(PINNED_ENV))
        env.start()
        self.addCleanup(env.stop)

        self.home = tempfile.mkdtemp(prefix="gitpr_baseline_cli_home_")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        cache = patch(
            "src.cache.get_cache_base_dir", return_value=Path(self.home, "prompts")
        )
        cache.start()
        self.addCleanup(cache.stop)

        for target in (
            "src.metrics.log_command_metric",
            "src.metrics.log_local_metric",
            "src.linter_engine.log_local_metric",
        ):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)

        net = patch("src.main.check_internet_connection", return_value=True)
        net.start()
        self.addCleanup(net.stop)

        set_active_baseline(None)
        self.addCleanup(set_active_baseline, None)

        self.runner = CliRunner()
        self.commit(
            ".gitpr/skill/.gitpr.linter.yml", LINTER_RULES, message="chore: linter rules"
        )
        self.commit(LEGACY_FILE, CLEAN_SOURCE, message="chore: seed the legacy module")

    # ── the CLI ──────────────────────────────────────────────────────────
    def run_cli(self, *args):
        """One invocation; an exception that is not an exit code fails the test."""
        result = self.runner.invoke(cli, list(args))
        exception = result.exception
        if exception is not None and not isinstance(exception, SystemExit):
            raise AssertionError(
                f"gitpr {' '.join(args)} raised {exception!r}\n{result.output}"
            )
        return result

    def baseline(self, *args):
        return self.run_cli("baseline", *args)

    def seed(self, *extra):
        """Puts the legacy constructs in the working tree; nothing is committed."""
        lines = ["def boot():"] + [f'    eval("{name}()")' for name in extra]
        lines.append("    return 0")
        self.write(LEGACY_FILE, "\n".join(lines) + "\n")

    def created(self):
        """The baseline as it stands on disk, read as JSON."""
        return self.read_json(BASELINE)

    def read_json(self, name):
        with open(
            os.path.join(self.dir, name), "r", encoding="utf-8", errors="replace"
        ) as handle:
            return json.load(handle)

    def entries(self):
        return self.created()["entries"]

    def entry_for(self, rule_id="legacy-no-eval", file_path=LEGACY_FILE):
        for entry in self.entries():
            if entry["rule_id"] == rule_id and entry["file_path"] == file_path:
                return entry
        raise AssertionError(f"no entry for {rule_id} in {file_path}")

    def identifier(self, index=0):
        """The id `show` prints, which is what `suppress` accepts."""
        fingerprint = self.entries()[index]["fingerprint"]
        return fingerprint[:19]

    def entry_with(self, identifier):
        """The entry an id names, read back from the file.

        By id and not by index: the entries are written in fingerprint order, so
        a run that adds one moves every later index — which is exactly the kind
        of thing a test about *keeping* a decision must not be fooled by.
        """
        for entry in self.entries():
            if entry["fingerprint"].startswith(identifier):
                return entry
        raise AssertionError(f"no entry for {identifier}")

    def status_of(self, identifier):
        return self.entry_with(identifier)["status"]

    @staticmethod
    def payload(result):
        """The JSON document a `--format json` run wrote to stdout."""
        return json.loads(result.output)


class TestCreate(BaselineCliTestCase):
    """`gitpr baseline create`, from the prompt to the file it writes."""

    def test_create_writes_the_baseline_and_reports_the_counts(self):
        """The counts read against the file being replaced, so a first run is all `new`."""
        self.seed("boot_setup")

        result = self.baseline("create", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(os.path.isfile(os.path.join(self.dir, BASELINE)))
        self.assertIn(BASELINE.replace("\\", os.sep), result.output)
        self.assertIn("1 new", result.output)

    def test_create_records_every_finding_of_the_diff(self):
        self.seed("boot_setup", "boot_load")

        self.baseline("create", "--yes")

        self.assertEqual(len(self.entries()), 2)
        for entry in self.entries():
            self.assertEqual(entry["status"], "existing")
            self.assertEqual(entry["rule_id"], "legacy-no-eval")
            self.assertEqual(entry["severity"], "error")

    def test_create_refuses_without_a_terminal_and_writes_nothing(self):
        self.seed("boot_setup")

        result = self.baseline("create")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--yes", result.output)
        self.assertFalse(os.path.exists(os.path.join(self.dir, BASELINE)))

    def test_create_describes_the_replacement_and_the_decisions_it_drops(self):
        self.seed("boot_setup")
        self.baseline("create", "--yes")
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        result = self.baseline("create")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("will be replaced", result.output)
        self.assertIn("1 suppression(s) or accepted debt(s)", result.output)
        self.assertIn("baseline update", result.output)

    def test_create_replacing_drops_the_decision_for_real(self):
        self.seed("boot_setup")
        self.baseline("create", "--yes")
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        self.baseline("create", "--yes")

        self.assertEqual(self.entry_for()["status"], "existing")
        self.assertFalse(self.entry_for()["suppressed"])

    def test_create_without_a_diff_says_what_to_do(self):
        result = self.baseline("create", "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no diff to record", result.output)

    def test_create_json_is_one_document(self):
        self.seed("boot_setup")

        result = self.baseline("create", "--yes", "--format", "json")

        self.assertEqual(result.exit_code, 0, result.output)
        document = self.payload(result)
        self.assertEqual(document["counts"]["new"], 1)
        self.assertTrue(document["created"])
        self.assertTrue(document["path"].replace("\\", "/").endswith(BASELINE.replace("\\", "/")))

    def test_create_json_keeps_warnings_out_of_the_document(self):
        """A warning goes beside the document: stdout has to stay parseable."""
        self.seed("boot_setup")
        self.baseline("create", "--yes")
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        result = self.baseline("create", "--yes", "--format", "json")

        self.assertEqual(result.exit_code, 0, result.output)
        self.payload(result)
        self.assertTrue(result.output)

    def test_create_refresh_without_a_cached_review_changes_nothing(self):
        """``--refresh`` asks the AI; with no provider configured it records the linter alone."""
        self.seed("boot_setup")
        with patch(
            "src.application.use_cases.create_baseline._fresh_review_findings",
            return_value=([], []),
        ):
            result = self.baseline("create", "--yes", "--refresh")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(len(self.entries()), 1)


class TestShow(BaselineCliTestCase):
    """`show` reads the record and the decisions in it."""

    def setUp(self):
        super().setUp()
        self.seed("boot_setup", "boot_load")
        self.baseline("create", "--yes")

    def test_show_counts_by_status(self):
        result = self.baseline("show")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("2 finding(s): 2 existing", result.output)

    def test_show_lists_a_decision_with_its_reason_and_scope(self):
        """A `rule` scope is recorded once and read back on every finding of the rule."""
        self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Legacy boot path.",
            "--scope",
            "rule",
            "--yes",
        )

        result = self.baseline("show")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Decisions recorded", result.output)
        self.assertIn("Legacy boot path.", result.output)
        self.assertIn("rule", result.output)
        self.assertIn("2 ignored", result.output)

    def test_show_filters_by_status(self):
        result = self.baseline("show", "--status", "ignored")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Nothing in the baseline matches that filter.", result.output)

    def test_show_filters_by_rule_and_by_file(self):
        by_rule = self.baseline("show", "--rule", "legacy-no-eval")
        by_file = self.baseline("show", "--file", "app/")
        other = self.baseline("show", "--rule", "no-such-rule")

        self.assertEqual(by_rule.exit_code, 0, by_rule.output)
        self.assertEqual(by_rule.output.count("legacy-no-eval"), 2)
        self.assertEqual(by_file.exit_code, 0, by_file.output)
        self.assertIn(LEGACY_FILE, by_file.output)
        self.assertIn("Nothing in the baseline matches that filter.", other.output)

    def test_show_without_a_baseline_refuses(self):
        os.remove(os.path.join(self.dir, BASELINE))

        result = self.baseline("show")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no baseline to show", result.output)

    def test_show_json_carries_the_entries(self):
        result = self.baseline("show", "--format", "json")

        self.assertEqual(result.exit_code, 0, result.output)
        document = self.payload(result)
        self.assertEqual(document["counts"]["existing"], 2)
        self.assertEqual(len(document["entries"]), 2)
        self.assertEqual(document["entries"][0]["fingerprint"][:7], "sha256:")


class TestValidate(BaselineCliTestCase):
    """`validate` is the strict reader: every defect is a problem and a non-zero exit."""

    def setUp(self):
        super().setUp()
        self.seed("boot_setup")
        self.baseline("create", "--yes")

    def test_validate_passes_on_a_sound_baseline(self):
        result = self.baseline("validate")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("sound", result.output)

    def test_validate_refuses_a_missing_baseline(self):
        os.remove(os.path.join(self.dir, BASELINE))

        result = self.baseline("validate")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no baseline at", result.output)

    def test_validate_names_a_tampered_checksum(self):
        document = self.created()
        document["entries"][0]["severity"] = "info"
        with open(
            os.path.join(self.dir, BASELINE), "w", encoding="utf-8", newline="\n"
        ) as handle:
            json.dump(document, handle, indent=2)

        result = self.baseline("validate")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("checksum", result.output.lower())

    def test_validate_reports_a_broken_overrides_file(self):
        self.write(OVERRIDES, "overrides: [this is not a mapping]\n")

        result = self.baseline("validate")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("overrides", result.output.lower())
        self.assertIn(OVERRIDES.replace("\\", os.sep), result.output)

    def test_validate_reports_overdue_debt(self):
        self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Migration planned.",
            "--debt",
            "--owner",
            "team-backend",
            "--due-date",
            "2020-01-01",
            "--yes",
        )

        result = self.baseline("validate")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("past its due date", result.output)
        self.assertIn("team-backend", result.output)

    def test_validate_json_carries_the_problems(self):
        os.remove(os.path.join(self.dir, BASELINE))

        result = self.baseline("validate", "--format", "json")

        self.assertEqual(result.exit_code, 1)
        document = self.payload(result)
        self.assertFalse(document["valid"])
        self.assertFalse(document["exists"])
        self.assertTrue(document["problems"])


class TestUpdate(BaselineCliTestCase):
    """`update` is the command that keeps what a human decided."""

    def setUp(self):
        super().setUp()
        self.seed("boot_setup")
        self.baseline("create", "--yes")

    def test_update_records_a_finding_the_baseline_never_saw(self):
        self.seed("boot_setup", "boot_load")

        result = self.baseline("update", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("1 new", result.output)
        self.assertEqual(len(self.entries()), 2)

    def test_update_keeps_the_decision_a_human_made(self):
        identifier = self.identifier()
        self.baseline("suppress", identifier, "--reason", "Legacy boot path.", "--yes")
        self.seed("boot_setup", "boot_load")

        self.baseline("update", "--yes")

        self.assertEqual(self.status_of(identifier), "ignored")
        kept = self.entry_with(identifier)
        self.assertEqual(kept["suppression_reason"], "Legacy boot path.")
        # And the finding the run just met came in without a decision of its own.
        added = [
            entry
            for entry in self.entries()
            if not entry["fingerprint"].startswith(identifier)
        ]
        self.assertEqual([entry["status"] for entry in added], ["existing"])

    def test_update_refuses_without_a_terminal(self):
        self.seed("boot_setup", "boot_load")

        result = self.baseline("update")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--yes", result.output)

    def test_update_refuses_a_divergent_checksum(self):
        document = self.created()
        document["entries"][0]["severity"] = "info"
        with open(
            os.path.join(self.dir, BASELINE), "w", encoding="utf-8", newline="\n"
        ) as handle:
            json.dump(document, handle, indent=2)
        self.seed("boot_setup", "boot_load")

        result = self.baseline("update", "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--recompute", result.output)

    def test_update_recompute_accepts_the_file_it_refused(self):
        document = self.created()
        document["entries"][0]["severity"] = "info"
        with open(
            os.path.join(self.dir, BASELINE), "w", encoding="utf-8", newline="\n"
        ) as handle:
            json.dump(document, handle, indent=2)
        self.seed("boot_setup", "boot_load")

        result = self.baseline("update", "--yes", "--recompute")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(len(self.entries()), 2)

    def test_update_over_an_empty_diff_writes_nothing(self):
        self.seed()
        before = self.read(BASELINE)

        result = self.baseline("update", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Nothing was written", result.output)
        self.assertEqual(self.read(BASELINE), before)


class TestSuppress(BaselineCliTestCase):
    """`suppress` records a decision, and the reason is not optional."""

    def setUp(self):
        super().setUp()
        self.seed("boot_setup", "boot_load")
        self.baseline("create", "--yes")

    def test_suppress_requires_a_reason(self):
        result = self.baseline("suppress", self.identifier())

        self.assertEqual(result.exit_code, 2)
        self.assertIn("--reason", result.output)

    def test_suppress_refuses_without_a_terminal_and_writes_nothing(self):
        before = self.read(BASELINE)

        result = self.baseline("suppress", self.identifier(), "--reason", "Legacy.")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--yes", result.output)
        self.assertEqual(self.read(BASELINE), before)

    def test_suppress_marks_the_entry_ignored_on_the_entry_itself(self):
        result = self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        self.assertEqual(result.exit_code, 0, result.output)
        entry = self.entry_for()
        self.assertEqual(entry["status"], "ignored")
        self.assertTrue(entry["suppressed"])
        self.assertEqual(entry["suppression_scope"], "finding")
        self.assertEqual(entry["suppression_reason"], "Legacy boot path.")
        self.assertTrue(entry["suppressed_by"])
        self.assertFalse(os.path.exists(os.path.join(self.dir, OVERRIDES)))

    def test_suppress_names_the_finding_before_it_asks(self):
        result = self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path."
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("legacy-no-eval", result.output)
        self.assertIn(LEGACY_FILE, result.output)

    def test_suppress_wider_than_one_finding_goes_to_the_overrides(self):
        result = self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Legacy boot path.",
            "--scope",
            "rule",
            "--yes",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(OVERRIDES.replace("\\", os.sep), result.output)
        self.assertTrue(os.path.isfile(os.path.join(self.dir, OVERRIDES)))
        self.assertEqual(self.entry_for()["status"], "existing")
        overrides = self.read(OVERRIDES)
        self.assertIn("scope: rule", overrides)
        self.assertIn("rule_id: legacy-no-eval", overrides)

    def test_suppress_a_wider_scope_warns_that_it_covers_more(self):
        result = self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Legacy boot path.",
            "--scope",
            "file",
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("not only this one", result.output)

    def test_suppress_a_wider_scope_is_refused_when_overrides_are_off(self):
        os.environ["GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES"] = "false"

        result = self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Legacy boot path.",
            "--scope",
            "rule",
            "--yes",
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("ALLOW_LOCAL_OVERRIDES", result.output)
        self.assertFalse(os.path.exists(os.path.join(self.dir, OVERRIDES)))

    def test_suppress_debt_records_owner_and_due_date(self):
        result = self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Migration planned.",
            "--debt",
            "--owner",
            "team-backend",
            "--due-date",
            "2030-12-31",
            "--yes",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        entry = self.entry_for()
        self.assertEqual(entry["status"], "accepted_debt")
        self.assertEqual(entry["accepted_debt_owner"], "team-backend")
        self.assertEqual(entry["accepted_debt_due_date"], "2030-12-31")

    def test_suppress_debt_without_an_owner_is_refused(self):
        result = self.baseline(
            "suppress", self.identifier(), "--reason", "Later.", "--debt", "--yes"
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("owner", result.output.lower())

    def test_suppress_debt_with_a_wider_scope_is_refused(self):
        result = self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Later.",
            "--debt",
            "--owner",
            "team-backend",
            "--scope",
            "rule",
            "--yes",
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("scope", result.output)

    def test_suppress_an_unknown_id_names_the_problem(self):
        result = self.baseline(
            "suppress", "sha256:000000000000", "--reason", "Whatever.", "--yes"
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("000000000000", result.output)

    def test_suppress_an_ambiguous_prefix_is_refused(self):
        os.remove(os.path.join(self.dir, BASELINE))
        self.baseline("create", "--yes")

        result = self.baseline("suppress", "sha256:", "--reason", "Whatever.", "--yes")

        self.assertEqual(result.exit_code, 1)

    def test_suppress_without_a_baseline_says_so(self):
        identifier = self.identifier()
        os.remove(os.path.join(self.dir, BASELINE))

        result = self.baseline("suppress", identifier, "--reason", "Whatever.", "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no baseline", result.output)

    def test_suppress_a_resolved_entry_is_refused(self):
        """Nothing in the tree answers to that id any more."""
        identifier = self.identifier()
        # The construct is committed and then taken back out, so the diff that
        # `update` walks is a real one and the finding really is gone.
        self.commit(
            LEGACY_FILE,
            'def boot():\n    eval("boot_setup()")\n    return 0\n',
            message="chore: introduce the legacy construct",
        )
        self.seed()
        self.baseline("update", "--yes")
        self.assertEqual(self.status_of(identifier), "resolved")

        result = self.baseline("suppress", identifier, "--reason", "Whatever.", "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("resolved", result.output)


class TestUnsuppress(BaselineCliTestCase):
    """`unsuppress` takes a decision back, and says what it could not take back."""

    def setUp(self):
        super().setUp()
        self.seed("boot_setup", "boot_load")
        self.baseline("create", "--yes")

    def test_unsuppress_clears_the_decision_and_keeps_the_finding(self):
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        result = self.baseline("unsuppress", self.identifier(), "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        entry = self.entry_for()
        self.assertEqual(entry["status"], "existing")
        self.assertFalse(entry["suppressed"])
        self.assertIsNone(entry["suppression_reason"])

    def test_unsuppress_refuses_without_a_terminal(self):
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        result = self.baseline("unsuppress", self.identifier())

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--yes", result.output)
        self.assertEqual(self.entry_for()["status"], "ignored")

    def test_unsuppress_names_the_decision_before_it_asks(self):
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )

        result = self.baseline("unsuppress", self.identifier())

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Legacy boot path.", result.output)

    def test_unsuppress_takes_back_a_wider_decision_on_the_entry(self):
        """A fingerprint-bound override is ours to delete — nothing else names it."""
        self.baseline(
            "suppress", self.identifier(), "--reason", "Legacy boot path.", "--yes"
        )
        overrides = self.read(OVERRIDES) if os.path.exists(
            os.path.join(self.dir, OVERRIDES)
        ) else None
        self.assertIsNone(overrides)

        result = self.baseline("unsuppress", self.identifier(), "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("entry", result.output)

    def test_unsuppress_reports_a_wider_suppression_instead_of_removing_it(self):
        """The decision is real, and it is not this command's to delete."""
        self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "Legacy boot path.",
            "--scope",
            "rule",
            "--yes",
        )

        result = self.baseline("unsuppress", self.identifier(), "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("covered by a 'rule' suppression", result.output)
        self.assertIn(OVERRIDES.replace("\\", os.sep), result.output)
        self.assertIn("scope: rule", self.read(OVERRIDES))

    def test_unsuppress_reports_what_a_wider_decision_still_covers(self):
        """Both decisions exist: the entry's is removed, the rule's is named."""
        self.baseline(
            "suppress", self.identifier(), "--reason", "This one only.", "--yes"
        )
        self.baseline(
            "suppress",
            self.identifier(),
            "--reason",
            "The whole rule.",
            "--scope",
            "rule",
            "--yes",
        )

        result = self.baseline("unsuppress", self.identifier(), "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("still covers this finding", result.output)
        self.assertEqual(self.entry_for()["status"], "existing")
        self.assertIn("The whole rule.", self.read(OVERRIDES))

    def test_unsuppress_without_a_decision_fails(self):
        result = self.baseline("unsuppress", self.identifier(), "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no decision", result.output)


class TestThePackLayer(BaselineCliTestCase):
    """The active pack's `baseline:` block, as the commands that audit read it.

    The block is a layer in memory: it decides what silences a finding and it is
    never written into `.gitpr/baseline.json`. That is exactly why the commands
    that edit the record have to name where a decision lives — a user asking to
    take one back deserves the true answer, and sometimes the true answer is
    "that one is the pack's, and this file is not where it is edited".
    """

    def setUp(self):
        super().setUp()
        self.seed("boot_setup", "boot_load")
        self.baseline("create", "--yes")

    def publish(self, *, suppressions=(), accepted_debt=()):
        """Puts a pack's block in force for this process, the way a run does.

        Built in memory rather than through a lockfile: what is under test is
        what the pack layer *reads*, and the resolver is covered on its own.
        """
        from src.domain.policy import (
            PackReference,
            PolicySource,
            ResolvedPack,
            set_active_policy,
        )
        from src.domain.policy.policy_resolver import compose_policy
        from src.domain.policy.policy_types import PolicyManifest

        manifest = PolicyManifest(
            name="acme/team-policy",
            version="1.0.0",
            min_gitpr_version=">=1.0.0",
            baseline={
                "suppressions": list(suppressions),
                "accepted_debt": list(accepted_debt),
            },
        )
        policy = compose_policy(
            [
                ResolvedPack(
                    reference=PackReference(
                        name="acme/team-policy",
                        version="1.0.0",
                        source=PolicySource.BUNDLED,
                    ),
                    manifest=manifest,
                )
            ]
        )
        set_active_policy(policy)
        self.addCleanup(set_active_policy, None)

    def test_show_reads_a_decision_from_the_pack_and_says_whose_it_is(self):
        self.publish(
            suppressions=[
                {
                    "scope": "rule",
                    "rule_id": "legacy-no-eval",
                    "reason": "Legacy boot path.",
                }
            ]
        )

        result = self.baseline("show")

        self.assertEqual(result.exit_code, 0, result.output)
        # Both findings of the rule, counted through the layer...
        self.assertIn("2 ignored", result.output)
        self.assertIn("Legacy boot path.", result.output)
        self.assertIn("policy:acme/team-policy@1.0.0", result.output)
        # ...and none of it in the file the repository owns.
        self.assertNotIn("Legacy boot path.", self.read(BASELINE))
        self.assertFalse(
            os.path.exists(os.path.join(self.dir, OVERRIDES)),
            "a pack's decision is not a reason to write a repository file",
        )

    def test_unsuppress_says_the_pack_is_where_a_wider_decision_is_edited(self):
        self.publish(
            suppressions=[
                {
                    "scope": "rule",
                    "rule_id": "legacy-no-eval",
                    "reason": "Legacy boot path.",
                }
            ]
        )
        self.baseline(
            "suppress", self.identifier(), "--reason", "This one only.", "--yes"
        )

        result = self.baseline("unsuppress", self.identifier(), "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.entry_for()["status"], "existing")
        self.assertIn("still covers this finding", result.output)
        self.assertIn(
            "the baseline block of the policy pack acme/team-policy", result.output
        )


class TestTheGroupItself(BaselineCliTestCase):
    """The surface a user meets, and the one thing it must never inherit."""

    def test_the_group_lists_its_six_commands(self):
        result = self.baseline("-h")

        self.assertEqual(result.exit_code, 0)
        for command in ("create", "show", "validate", "update", "suppress", "unsuppress"):
            self.assertIn(command, result.output)

    def test_the_group_points_at_its_documentation(self):
        result = self.baseline("-h")

        self.assertIn("baseline-suppressions", result.output)

    def test_the_baseline_never_holds_a_line_of_code(self):
        """The record names where a finding is; it never quotes what is there."""
        self.write(
            LEGACY_FILE,
            'def boot():\n    eval("setup(" + token + ")")\n    return 0\n',
        )

        self.baseline("create", "--yes")

        raw = self.read(BASELINE)
        self.assertNotIn("setup(", raw)
        self.assertNotIn("token", raw)

    def test_no_flow_but_the_baseline_commands_writes_the_record(self):
        """A lint run classifies against the file; it never moves it."""
        self.seed("boot_setup")
        self.baseline("create", "--yes")
        before = self.read(BASELINE)
        self.seed("boot_setup", "boot_load")

        self.run_cli("--linter", "--hook", HOOK)

        self.assertEqual(self.read(BASELINE), before)


if __name__ == "__main__":
    unittest.main()
