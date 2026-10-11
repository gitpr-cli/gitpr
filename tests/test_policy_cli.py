"""The ``gitpr policy`` group through Click's runner.

Three properties are worth a test that goes in through the front door rather
than through the use case.

The first is the **write guard**. Every policy command that writes asks before it
does, and ``--yes`` answers the question without skipping the checks behind it —
but a command running in a pipe or in CI has nobody to answer, so it has to
refuse with the instruction instead of blocking on a prompt no one will read.
``CliRunner`` is exactly such a terminal-less caller, so the refusal is the
default here and ``--yes`` is what has to be asked for.

The second is that the group is **runnable at all**: seven commands, their
options, and the documentation link in the epilog are part of the surface a user
meets, and a missing import inside one of them only shows up when it runs.

The third is that the tests never write to the developer's own machine. The
repository is a ``tempfile`` directory and the pack store is redirected at the
module the search order reads it from, so a stray ``policy install`` lands in
the sandbox rather than in ``~/.gitpr/policies``.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.infrastructure.policy import local_policy_repository
from src.main import cli


MANIFEST = """schema_version: 1
name: acme/team-policy
version: 1.0.0
min_gitpr_version: ">=1.0.0"

linter:
  rules_file: linter.yml
"""

RULES = """rules:
  - name: acme-no-float-money
    regex: "\\\\bfloat\\\\b"
    message: "Money is an integer in minor units."
    extensions: ["*"]
"""

# A fingerprint is a literal here because a pack has no finding to compute one
# from — it can only name a finding the repository already knows.
FINGERPRINT = "sha256:" + "a" * 64

# A pack that also carries decisions: the block a team standardising a legacy
# gate ships with the rules that gate it.
BASELINE_MANIFEST = (
    MANIFEST
    + """baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: "Money is an integer in minor units; the rule is a transition aid."
  accepted_debt:
    - fingerprint: "%s"
      owner: platform
      reason: "Migration planned for the next quarter."
      due_date: "2026-12-31"
"""
    % FINGERPRINT
)


class PolicyCliTestCase(unittest.TestCase):
    """A throwaway repository, a throwaway pack store, and a runner."""

    def setUp(self):
        self.runner = CliRunner()
        self.root = tempfile.mkdtemp(prefix="gitpr_policy_cli_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = os.path.join(self.root, "repo")
        self.store = os.path.join(self.root, "store")
        self.source = os.path.join(self.root, "source")
        for path in (self.repo, self.store, self.source):
            os.makedirs(path)
        # ``policy list`` and ``policy show`` read the lockfile from the current
        # directory, so the run has to happen inside the fixture. chdir back
        # before removing the directory (cleanups run last-registered-first) or
        # Windows refuses to delete the tree the process still stands in.
        self.previous_cwd = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, self.previous_cwd)
        patcher = patch.object(
            local_policy_repository, "installed_policies_dir", return_value=self.store
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, content, directory=None):
        path = os.path.join(directory or self.repo, name)
        os.makedirs(os.path.dirname(path) or directory or self.repo, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return path

    def make_source_pack(self, manifest=MANIFEST, rules=RULES):
        self.write("policy.yml", manifest, directory=self.source)
        if rules is not None:
            self.write("linter.yml", rules, directory=self.source)
        return self.source

    def run_policy(self, *args):
        return self.runner.invoke(cli, ["policy", *args])

    @property
    def lockfile(self):
        return os.path.join(self.repo, ".gitpr", "policy.lock.yml")


class TestWriteGuard(PolicyCliTestCase):
    """A command that writes, with no terminal to confirm it."""

    def test_use_refuses_without_a_terminal_and_writes_nothing(self):
        result = self.run_policy("use", "gitpr/laravel-quality")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--yes", result.output)
        self.assertIn("writes files", result.output)
        self.assertFalse(os.path.exists(self.lockfile))

    def test_use_writes_with_yes(self):
        result = self.run_policy("use", "gitpr/laravel-quality", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(os.path.isfile(self.lockfile))
        self.assertIn("Policy activated", result.output)

    def test_init_refuses_without_a_terminal(self):
        self.write("composer.json", "{}\n")
        self.write("artisan", "<?php\n")

        result = self.run_policy("init", "--stack", "laravel")

        self.assertEqual(result.exit_code, 1)
        self.assertFalse(os.path.exists(self.lockfile))

    def test_off_refuses_without_a_terminal_and_leaves_the_lockfile(self):
        self.run_policy("use", "gitpr/laravel-quality", "--yes")

        result = self.run_policy("off")

        self.assertEqual(result.exit_code, 1)
        self.assertTrue(os.path.isfile(self.lockfile))

    def test_install_refuses_without_a_terminal_and_copies_nothing(self):
        self.make_source_pack()

        result = self.run_policy("install", self.source)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(os.listdir(self.store), [])

    def test_install_refuses_debt_nobody_owns(self):
        """Installing is the first moment a pack's decisions could reach a machine."""
        self.make_source_pack(
            manifest=MANIFEST
            + "baseline:\n"
            "  accepted_debt:\n"
            '    - fingerprint: "%s"\n'
            '      reason: "Somebody will get to it."\n' % FINGERPRINT
        )

        result = self.run_policy("install", self.source, "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("owner", result.output)
        self.assertEqual(os.listdir(self.store), [])

    def test_show_names_the_pack_that_brought_the_baseline_block(self):
        """In force means in force: the decisions travel with the pack that declares them."""
        self.make_source_pack(manifest=BASELINE_MANIFEST)
        self.run_policy("install", self.source, "--yes")
        self.run_policy("use", "acme/team-policy", "--yes")

        result = self.run_policy("show")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("baseline.suppressions = acme-no-float-money", result.output)
        self.assertIn("← acme/team-policy@1.0.0", result.output)


class TestReading(PolicyCliTestCase):
    """The three commands that only read."""

    def test_list_reports_the_defaults_when_nothing_is_active(self):
        result = self.run_policy("list")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("runs on the GitPR defaults", result.output)
        self.assertIn("gitpr/laravel-quality", result.output)
        self.assertIn("gitpr/node-quality", result.output)
        self.assertIn("gitpr/php-security", result.output)
        self.assertIn("gitpr/vue-quality", result.output)

    def test_list_marks_the_pack_in_force(self):
        self.run_policy("use", "gitpr/laravel-quality", "--yes")

        result = self.run_policy("list")

        self.assertIn("→ gitpr/laravel-quality@1.0.0", result.output)
        # The dependency travels with it, without the marker one root pack owns.
        self.assertIn("gitpr/php-security@1.0.0", result.output)
        self.assertNotIn("→ gitpr/php-security", result.output)

    def test_validate_reports_a_bundled_pack_and_its_dependency(self):
        result = self.run_policy("validate", "gitpr/laravel-quality")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("gitpr/laravel-quality@1.0.0 from bundled", result.output)
        self.assertIn("Checksum:", result.output)

    def test_validate_reports_the_baseline_block_a_pack_brings(self):
        """A pack that standardises a legacy gate says so, and says it in counts.

        Counted rather than listed on purpose: a suppression is a decision about
        a finding, and read without that finding it is evidence of nothing.
        `gitpr baseline show` is where the entries are read, against the findings
        they silence.
        """
        self.write("policy.yml", BASELINE_MANIFEST)
        self.write("linter.yml", RULES)

        result = self.run_policy("validate", self.repo)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(
            "Baseline: 1 suppression(s) and 1 accepted debt(s)", result.output
        )

    def test_validate_refuses_a_suppression_with_no_reason(self):
        """Packs are another door into the record, and it is kept shut the same way."""
        self.write(
            "policy.yml",
            MANIFEST
            + "baseline:\n"
            "  suppressions:\n"
            "    - scope: rule\n"
            "      rule_id: acme-no-float-money\n",
        )

        result = self.run_policy("validate", self.repo)

        self.assertEqual(result.exit_code, 1)
        self.assertIn("reason", result.output)
        # The pack, so the author knows which manifest to open.
        self.assertIn("acme/team-policy", result.output)

    def test_validate_of_a_broken_pack_fails_so_a_ci_run_can_gate_on_it(self):
        """The failure is the answer, and the answer is a non-zero exit."""
        self.write("policy.yml", MANIFEST + "\nunknown_key: true\n")

        result = self.run_policy("validate", self.repo)

        self.assertEqual(result.exit_code, 1)
        self.assertIn("unknown_key", result.output)

    def test_validate_of_a_pack_that_is_not_there_fails_with_the_sources(self):
        result = self.run_policy("validate", "acme/nowhere")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("acme/nowhere", result.output)
        self.assertIn(self.store, result.output)

    def test_show_renders_the_precedence_and_the_provenance(self):
        self.run_policy("use", "gitpr/laravel-quality", "--yes")

        result = self.run_policy("show")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Precedence, lowest first", result.output)
        self.assertIn("1. gitpr/php-security@1.0.0", result.output)
        self.assertIn("2. gitpr/laravel-quality@1.0.0", result.output)
        self.assertIn("policy.overrides.yml", result.output)
        self.assertIn("← gitpr/laravel-quality@1.0.0", result.output)

    def test_show_without_a_pack_says_there_is_nothing_to_show(self):
        result = self.run_policy("show")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("No policy pack is active", result.output)


class TestWriting(PolicyCliTestCase):
    """The three commands that write, once they are allowed to."""

    def test_install_copies_a_local_directory_into_the_store(self):
        self.make_source_pack()

        result = self.run_policy("install", self.source, "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        installed = os.path.join(
            self.store, local_policy_repository.install_dir_name("acme/team-policy")
        )
        self.assertTrue(os.path.isfile(os.path.join(installed, "policy.yml")))
        # And the copy is what the next command reads.
        self.assertIn("acme/team-policy@1.0.0", self.run_policy("list").output)

    def test_install_of_an_occupied_destination_fails_without_force(self):
        self.make_source_pack()
        self.run_policy("install", self.source, "--yes")

        result = self.run_policy("install", self.source, "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--force", result.output)

    def test_off_removes_the_lockfile_and_leaves_the_pack(self):
        self.run_policy("use", "gitpr/laravel-quality", "--yes")

        result = self.run_policy("off", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(os.path.exists(self.lockfile))
        self.assertIn("Policy deactivated", result.output)
        self.assertIn("runs on the GitPR defaults", self.run_policy("list").output)

    def test_off_without_a_pack_answers_instead_of_failing(self):
        result = self.run_policy("off", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("No policy pack is active", result.output)

    def test_init_detects_the_stack_from_the_project(self):
        self.write("composer.json", '{"require": {"laravel/framework": "^11.0"}}\n')
        self.write("artisan", "<?php\n")

        result = self.run_policy("init", "--yes")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Detected stack: laravel", result.output)
        self.assertIn("gitpr/laravel-quality", open(self.lockfile, encoding="utf-8").read())

    def test_init_with_an_unknown_stack_names_the_ones_it_takes(self):
        result = self.run_policy("init", "--stack", "cobol", "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("cobol", result.output)
        self.assertIn("laravel", result.output)

    def test_init_that_cannot_tell_the_stack_says_how_to_name_it(self):
        result = self.run_policy("init", "--yes")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--stack", result.output)


class TestSurface(PolicyCliTestCase):
    """What a user meets before running anything."""

    def test_the_group_lists_its_commands_and_links_the_documentation(self):
        result = self.run_policy()

        self.assertEqual(result.exit_code, 0, result.output)
        for command in ("list", "validate", "show", "use", "off", "install", "init"):
            with self.subTest(command=command):
                self.assertIn(command, result.output)
        self.assertIn("policy-packs", result.output)

    def test_every_command_has_its_own_help(self):
        for command in ("list", "validate", "show", "use", "off", "install", "init"):
            with self.subTest(command=command):
                result = self.run_policy(command, "--help")
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("Usage:", result.output)

    def test_the_group_is_reachable_from_the_top_level_help(self):
        result = self.runner.invoke(cli, ["-h"])

        self.assertIn("policy", result.output)


if __name__ == "__main__":
    unittest.main()
