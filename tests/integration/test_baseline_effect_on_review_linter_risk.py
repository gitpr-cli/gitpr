"""What a baseline does to the review, the linter, the risk score and the CLI.

The acceptance criterion of the spec is a repository, not a function: a legacy
tree that stops failing its own pipeline, a new finding that still fails it, and
a second clone that reaches the same verdict from the versioned files alone. So
every test here drives the real commands through ``CliRunner``, inside a real
git repository, against a real ``.gitpr/baseline.json``.

Three things have to be true for the "nothing changes without a file" promise to
be *testable*, and all three are arranged in ``setUp`` rather than trusted:

* the environment is pinned, because ``~/.gitpr/.env`` is loaded into every run
  and would otherwise decide what these tests exercise;
* the prompt cache is redirected, because a review cached by another session
  would answer the question the stub was supposed to answer;
* the output names are pinned to a fixed filename, because the default pattern
  carries a timestamp and two runs a second apart would then not be comparable.

The rules the fixture trips are four rules with one construct each, and that is
deliberate: an alert line is the rule's *message*, carrying neither the rule's
name nor the line number, so two findings of one rule render to the same string
— and the statuses written in front of them could then not be told apart.
"""

import contextlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from src.application.use_cases.compare_against_baseline import compare_against_baseline
from src.application.use_cases.create_baseline import create_baseline, update_baseline
from src.domain.baseline import (
    FINGERPRINT_VERSION,
    BaselineStatus,
    compute_fingerprint,
    set_active_baseline,
)
from src.infrastructure.baseline.local_baseline_repository import (
    baseline_path,
    read_manifest,
    write_manifest,
)
from src.infrastructure.scm.base import PullRequestResult, RepoRef
from src.linter_engine import lint_findings
from src.main import cli
from src.review.remote_pr import review_remote_pr
from tests.fix.git_fixture import GitRepoTestCase

# ── the legacy tree ──────────────────────────────────────────────────────────

# The rules a legacy tree trips. Four of them, one construct each: see the
# module docstring for why one rule with four matches would not do.
#
# No `level` on any of them, on purpose — the linter's default is `error`, and
# an error is what makes a legacy tree red on day one.
LINTER_RULES = r"""rules:
  - name: legacy-no-eval
    regex: '\beval\('
    message: "eval() executes arbitrary code."
    extensions: ["*"]
  - name: legacy-no-exec
    regex: '\bexec\('
    message: "exec() runs a string as code."
    extensions: ["*"]
  - name: legacy-no-compile
    regex: '\bcompile\('
    message: "compile() builds code at runtime."
    extensions: ["*"]
  - name: legacy-no-dunder-import
    regex: '__import__\('
    message: "__import__() bypasses the import system."
    extensions: ["*"]
"""

EVAL = "eval() executes arbitrary code."
EXEC = "exec() runs a string as code."
COMPILE = "compile() builds code at runtime."
DUNDER_IMPORT = "__import__() bypasses the import system."

LEGACY_FILE = "app/legacy.py"
CLEAN_SOURCE = "def boot():\n    return 0\n"

# `--hook` is not a flag but the commit-message file the hook was handed, and
# GitPR only ever uses it to know it is running inside one: the character of the
# run that matters here is that it skips the TUI and keeps printing. The path is
# never read.
HOOK = ".git/COMMIT_EDITMSG"

# Lines 2 to 4 of the legacy file, so the three findings the first baseline
# records sit where the seed's diff puts them.
LEGACY_LINES = (
    "def boot():",
    '    eval("boot_setup()")',
    '    exec("boot_load()")',
    '    compile("boot_run()", "<boot>", "exec")',
)
RETURN_LINE = "    return 0"
DUNDER_IMPORT_LINE = '    __import__("boot_plugin")'


def legacy_source(*extra):
    """The legacy file, with *extra* constructs appended *after* the three.

    Appended and never inserted: every test that grows the tree this way is
    about a finding arriving, and the three findings already recorded have to
    keep the line numbers their fingerprints were taken at.
    """
    return "\n".join([*LEGACY_LINES, *extra, RETURN_LINE]) + "\n"


def shifted_source():
    """The same four constructs, one line down.

    The documented cost of a fingerprint that covers the line's number and its
    content: an insertion above a recorded finding makes it a new one. The bias
    is deliberate — a false `new` is visible and one `update` repairs it, while
    a false `existing` would hide a finding nobody ever recorded.
    """
    return (
        "\n".join([LEGACY_LINES[0], DUNDER_IMPORT_LINE, *LEGACY_LINES[1:], RETURN_LINE])
        + "\n"
    )


def run_git(directory, *args):
    """git inside *directory*, pinned the way the fixture pins its own."""
    return subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=directory,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


# Everything a run would otherwise inherit from the machine it runs on.
PINNED_ENV = {
    # The four baseline keys, at their documented defaults.
    "GITPR_BASELINE_ENABLED": "true",
    "GITPR_BASELINE_PATH": "",
    "GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH": "true",
    "GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES": "true",
    # Fixed names, so a run's stdout does not carry a timestamp and the report
    # of two runs lands in the same file instead of beside it.
    "OUTPUT_FILE_NAME_LINTER": "fixture_LINTER.md",
    "OUTPUT_FILE_NAME_REVIEW": "fixture_REVIEW.txt",
    "OUTPUT_FILE_NAME_FULLREVIEW": "fixture_FULLREVIEW.txt",
    # The review carries the risk section by default; on, so the tests that read
    # a report also see the section the baseline prefixes.
    "GITPR_RISK_INCLUDE_IN_REVIEW": "true",
    "GITPR_LANG": "en_us",
    "GITPR_SKIP_UPDATE_CHECK": "true",
}


class BaselineIntegrationTestCase(GitRepoTestCase):
    """A repository, a rules file, a redirected cache, and a runner.

    ``setUp`` moves the process into the repository — the linter rules, the
    skill files, the smart excludes and every relative path in the CLI resolve
    against the current directory — and moves it back before the tree is
    removed, because Windows will not delete a directory that is somebody's
    working directory.
    """

    prefix = "gitpr_baseline_integration_"

    def setUp(self):
        super().setUp()
        self._cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, self._cwd)

        env = patch.dict(os.environ, dict(PINNED_ENV))
        env.start()
        self.addCleanup(env.stop)

        self.home = tempfile.mkdtemp(prefix="gitpr_baseline_home_")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        # The prompt cache is the one directory these runs would otherwise write
        # to under the developer's real profile.
        cache = patch(
            "src.cache.get_cache_base_dir", return_value=Path(self.home, "prompts")
        )
        cache.start()
        self.addCleanup(cache.stop)

        # The ledgers are nobody's business in a test run, and the two the code
        # writes through are patched where the functions that call them look.
        for target in (
            "src.metrics.log_command_metric",
            "src.metrics.log_local_metric",
            "src.linter_engine.log_local_metric",
        ):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)

        # The guardian probes 8.8.8.8:53, and the suite's `no_network` guard
        # turns that probe into a failure. Every flow here is offline by design,
        # so it is stubbed rather than skipped.
        net = patch("src.main.check_internet_connection", return_value=True)
        net.start()
        self.addCleanup(net.stop)

        set_active_baseline(None)
        self.addCleanup(set_active_baseline, None)

        self.runner = CliRunner()
        self.commit(
            ".gitpr/skill/.gitpr.linter.yml", LINTER_RULES, message="chore: linter rules"
        )
        # The file the diff is taken against. Committed clean and touched up by
        # `seed_legacy`, so every test starts from the same revision and the
        # bare clone the full-review test needs is already in place.
        self.commit(LEGACY_FILE, CLEAN_SOURCE, message="chore: seed the legacy module")

    # ── running the CLI ──────────────────────────────────────────────────
    def run_cli(self, *args):
        """One invocation; an exception that is not an exit code fails the test."""
        result = self.runner.invoke(cli, list(args))
        exception = result.exception
        if exception is not None and not isinstance(exception, SystemExit):
            raise AssertionError(
                f"gitpr {' '.join(args)} raised {exception!r}\n{result.output}"
            )
        return result

    def lint(self, *args):
        """``--linter`` in a hook: no TUI, and the console still gets the verdict."""
        return self.run_cli("--linter", "--hook", HOOK, *args)

    def seed_legacy(self, *extra):
        """Puts the legacy constructs in the working tree; nothing is committed."""
        self.write(LEGACY_FILE, legacy_source(*extra))

    @contextlib.contextmanager
    def stubbed_ai(self, findings=()):
        """The AI edge: one canned review, and the prompts it was asked.

        Yields the list the prompts are appended to, so a test can read what the
        model was actually handed.
        """
        prompts = []

        def fake_call(provider, api_key, api_model, prompt, system_instruction, action=None):
            prompts.append(prompt)
            return {
                "review": "## Review\n\nStubbed.",
                "commit_message": "chore: stubbed",
                "findings": [dict(item) for item in findings],
            }

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch("src.core.call_ai_model", side_effect=fake_call))
            stack.enter_context(patch("src.core.get_api_key", return_value="key"))
            stack.enter_context(patch("src.core.get_api_model", return_value="stub-model"))
            yield prompts

    # ── the baseline on disk ─────────────────────────────────────────────
    def create(self, **kwargs):
        """Records the current diff, the way `gitpr baseline create` will.

        Driven through the use case rather than the CLI: the `gitpr baseline`
        group is a later phase, and what this file is about is what the *other*
        commands do with the file these two write.
        """
        return create_baseline(repo_path=self.dir, **kwargs)

    def update(self, **kwargs):
        return update_baseline(repo_path=self.dir, **kwargs)

    def baseline_bytes(self):
        with open(baseline_path(self.dir), "rb") as handle:
            return handle.read()

    def write_baseline_bytes(self, content):
        with open(baseline_path(self.dir), "wb") as handle:
            handle.write(content)

    def manifest(self):
        """The manifest on disk, asserting it is one this build can apply."""
        manifest, problems = read_manifest(self.dir)
        self.assertEqual(problems, [], "the run left an unapplicable baseline")
        self.assertIsNotNone(manifest, "there is no baseline on disk")
        return manifest

    def entries(self):
        return self.manifest().entries

    def entry_at(self, line):
        """The one entry the linter recorded for the finding on *line*."""
        matched = [entry for entry in self.entries() if entry.line_start == line]
        self.assertEqual(
            len(matched),
            1,
            f"the baseline does not record exactly one finding on line {line}",
        )
        return matched[0]

    def write_overrides(self, content):
        self.write(".gitpr/baseline.overrides.yml", content)

    def commit_baseline(self):
        """Tracks the baseline, so it stops being an untracked file.

        What this buys is a comparable stdout: the untracked warning names every
        entry of `git ls-files --others`, and a file one run leaves behind is a
        difference the next run would print.
        """
        self._git("add", "--", ".gitpr/baseline.json")
        self._git("commit", "-m", "chore: record the baseline")

    def reports(self, folder):
        directory = Path(self.dir) / ".gitpr" / "reports" / folder
        if not directory.exists():
            return []
        return sorted(directory.glob("*"), key=lambda path: path.stat().st_mtime)

    def report(self, folder):
        """The newest report under ``.gitpr/reports/<folder>``, as text."""
        written = self.reports(folder)
        self.assertTrue(written, f"no report was written under .gitpr/reports/{folder}")
        with open(written[-1], "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    # ── the risk document ────────────────────────────────────────────────
    def risk_json(self, *args):
        """``gitpr risk --format json``, parsed — stdout is the document."""
        result = self.run_cli("risk", "--no-history", "--format", "json", *args)
        self.assertEqual(result.exit_code, 0, result.output)
        return json.loads(result.stdout)

    def informational(self, payload, status=None):
        """The zero-weight evidence of the change's one file."""
        files = payload["files"]
        self.assertEqual(
            [item["file_path"] for item in files], [LEGACY_FILE], payload
        )
        evidence = [
            item for item in files[0]["evidence"] if item["signal"] == "baseline_finding"
        ]
        if status is not None:
            evidence = [
                item for item in evidence if item["details"]["status"] == status
            ]
        return evidence

    # ── the two decisions a human writes ─────────────────────────────────
    def suppression_file(self, fingerprint, reason="Synthetic secret in a fixture."):
        return (
            "overrides:\n"
            "  suppressions:\n"
            f'    - fingerprint: "{fingerprint}"\n'
            "      scope: finding\n"
            f'      reason: "{reason}"\n'
            '      by: "alice"\n'
            '      date: "2026-01-01"\n'
        )

    def debt_file(self, fingerprint):
        return (
            "overrides:\n"
            "  accepted_debt:\n"
            f'    - fingerprint: "{fingerprint}"\n'
            '      owner: "time-plataforma"\n'
            '      reason: "The template engine is replaced in the migration."\n'
            '      due_date: "2026-12-31"\n'
        )


class TestWithoutABaselineNothingChanges(BaselineIntegrationTestCase):
    """§12.10 — the repository that never hears about any of this.

    Two halves of one promise: a tree with no file at all, and a tree that *has*
    one while the feature is switched off. The second is the one that can rot
    unnoticed, because it is the escape hatch a team reaches for.
    """

    @contextlib.contextmanager
    def feature_off(self):
        with patch.dict(os.environ, {"GITPR_BASELINE_ENABLED": "false"}):
            yield

    def test_the_linter_still_blocks_on_a_legacy_error(self):
        self.seed_legacy()

        result = self.lint()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Validation failed! Found 3 critical error(s)", result.output)
        self.assertNotIn("🧾", result.output, "no baseline, no status line")
        report = self.report("linter")
        for message in (EVAL, EXEC, COMPILE):
            self.assertIn(f"- {message}", report)
        self.assertNotIn("[existing]", report)
        self.assertNotIn("[new]", report)

    def test_switching_the_feature_off_reproduces_the_run_byte_for_byte(self):
        self.seed_legacy()
        before = self.lint()
        report_before = self.report("linter")
        self.assertEqual(before.exit_code, 1, before.output)

        self.create()
        # Ordered for comparability, not for tidiness: the report of the first
        # run is an untracked file while the second run takes its diff, and the
        # untracked warning would then name it. Tracking the baseline and
        # clearing the reports leaves both runs looking at a clean tree.
        shutil.rmtree(os.path.join(self.dir, ".gitpr", "reports"), ignore_errors=True)
        self.commit_baseline()

        with self.feature_off():
            after = self.lint()

        self.assertEqual(after.exit_code, 1, after.output)
        self.assertEqual(after.output, before.output)
        self.assertEqual(self.report("linter"), report_before)

    def test_the_risk_document_is_reproduced_when_the_feature_is_off(self):
        self.seed_legacy()
        before = self.risk_json()

        self.create()

        with self.feature_off():
            after = self.risk_json()

        self.assertEqual(after, before)


class TestTheLegacyAdoptionLoop(BaselineIntegrationTestCase):
    """The definition of done, walked: record, pass, grow, fail.

    Three findings the team accepts as the state of the tree, then the fourth —
    the one this change adds — which is the only one allowed to stop a pipeline.
    """

    def setUp(self):
        super().setUp()
        self.seed_legacy()

    def test_the_three_legacy_errors_are_recorded_and_stop_blocking(self):
        run = self.create()

        self.assertTrue(run.created)
        self.assertEqual(run.counts["new"], 3, "a fresh baseline accepts what it finds")
        self.assertEqual(len(self.entries()), 3)
        self.assertTrue(all(entry.status is BaselineStatus.EXISTING for entry in self.entries()))

        result = self.lint()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("🧾 Baseline: 3 existing", result.output)
        self.assertNotIn("Validation failed", result.output)
        self.assertNotIn(
            "Clean code",
            result.output,
            "the run found three errors and says so above",
        )
        report = self.report("linter")
        for message in (EVAL, EXEC, COMPILE):
            self.assertIn(f"[existing] {message}", report)

    def test_the_fourth_error_is_new_and_fails_the_run(self):
        self.create()
        self.seed_legacy(DUNDER_IMPORT_LINE)

        result = self.lint()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("🧾 Baseline: 1 new, 3 existing", result.output)
        self.assertIn(f"[new] {DUNDER_IMPORT}", self.report("linter"))

    def test_the_run_goes_green_again_when_the_new_error_leaves(self):
        self.create()
        self.seed_legacy(DUNDER_IMPORT_LINE)
        self.assertEqual(self.lint().exit_code, 1)

        self.seed_legacy()

        self.assertEqual(self.lint().exit_code, 0)

    def test_a_new_warning_is_reported_and_never_blocks(self):
        """The exit code has always followed the alert's level, not the status."""
        self.create()
        self.write(
            ".gitpr/skill/.gitpr.linter.yml",
            LINTER_RULES.replace(
                "  - name: legacy-no-dunder-import\n",
                "  - name: legacy-no-dunder-import\n    level: warning\n",
            ),
        )
        self.seed_legacy(DUNDER_IMPORT_LINE)

        result = self.lint()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("1 new, 3 existing", result.output)
        self.assertIn("1 best practice warning(s)", result.output)
        self.assertNotIn("Validation failed", result.output)

    def test_a_shifted_finding_reads_as_new_until_the_record_moves(self):
        """The documented cost of the fingerprint, and its remedy."""
        self.create()

        self.write(LEGACY_FILE, shifted_source())
        result = self.lint()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("4 new", result.output)

        run = self.update()

        self.assertTrue(run.written)
        # The three whose fingerprint moved are closed, not silently dropped:
        # the file keeps the history of what it once recorded.
        resolved = [
            entry for entry in self.entries() if entry.status is BaselineStatus.RESOLVED
        ]
        self.assertEqual(len(resolved), 3)
        after = self.lint()
        self.assertEqual(after.exit_code, 0)
        self.assertIn("🧾 Baseline: 4 existing", after.output)

    def test_classifying_never_rewrites_the_baseline(self):
        """§5.9: the file moves through `baseline create`/`update`, nothing else."""
        self.create()
        before = self.baseline_bytes()

        self.lint()
        self.risk_json()
        with self.stubbed_ai():
            self.assertEqual(
                self.run_cli("-r", "--no-unstaged-check").exit_code, 0
            )

        self.assertEqual(self.baseline_bytes(), before)


class TestSuppressionsAndDebt(BaselineIntegrationTestCase):
    """The two decisions a human writes, and what each of them buys."""

    def setUp(self):
        super().setUp()
        self.seed_legacy()
        self.create()

    def test_a_suppressed_finding_reads_ignored(self):
        self.write_overrides(self.suppression_file(self.entry_at(2).fingerprint))

        result = self.lint()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("🧾 Baseline: 2 existing, 1 ignored", result.output)
        self.assertIn(f"[ignored] {EVAL}", self.report("linter"))

    def test_the_suppression_reason_travels_into_the_risk_document(self):
        self.write_overrides(
            self.suppression_file(
                self.entry_at(2).fingerprint, reason="Synthetic secret in a fixture."
            )
        )

        ignored = self.informational(self.risk_json(), status="ignored")

        self.assertEqual(len(ignored), 1, ignored)
        self.assertEqual(ignored[0]["points"], 0.0)
        self.assertEqual(ignored[0]["details"]["reason"], "Synthetic secret in a fixture.")
        self.assertEqual(ignored[0]["details"]["scope"], "finding")
        self.assertEqual(ignored[0]["details"]["origin"], "local")
        self.assertEqual(ignored[0]["details"]["line_start"], 2)

    def test_accepted_debt_is_worth_zero_points_and_names_its_owner(self):
        self.write_overrides(self.debt_file(self.entry_at(2).fingerprint))

        debt = self.informational(self.risk_json(), status="accepted_debt")

        self.assertEqual(len(debt), 1, debt)
        self.assertEqual(debt[0]["points"], 0.0)
        self.assertEqual(debt[0]["details"]["owner"], "time-plataforma")
        self.assertEqual(debt[0]["details"]["due_date"], "2026-12-31")
        self.assertIn("migration", debt[0]["details"]["reason"])

    def test_only_the_new_finding_moves_the_score(self):
        """The same diff twice: only the status of the fourth finding differs.

        The counts run the other way from what "more findings, more noise"
        suggests, and that is the point: a `new` finding is what the score is
        made of, so it is not *also* filed as zero-weight evidence. The four
        known ones are — with the fourth among them the change scores strictly
        less, over the very same lines.
        """
        three = self.baseline_bytes()
        self.seed_legacy(DUNDER_IMPORT_LINE)
        self.create()
        four = self.baseline_bytes()

        self.write_baseline_bytes(three)
        one_new = self.risk_json()

        self.write_baseline_bytes(four)
        all_known = self.risk_json()

        self.assertEqual(len(self.informational(one_new)), 3)
        self.assertEqual(
            len(self.informational(all_known)),
            4,
            "everything the baseline knows is evidence, and worth nothing",
        )
        self.assertGreater(one_new["score"], all_known["score"])
        self.assertEqual(one_new["total_changed_lines"], all_known["total_changed_lines"])


class TestTheReviewFlow(BaselineIntegrationTestCase):
    """`-r`: the statuses reach the report and the risk section, and nothing blocks."""

    def setUp(self):
        super().setUp()
        self.seed_legacy()

    def review(self, *args):
        with self.stubbed_ai() as prompts:
            result = self.run_cli("-r", "--no-unstaged-check", *args)
        self.assertEqual(result.exit_code, 0, result.output)
        return result, prompts

    def test_the_report_carries_the_status_of_every_alert(self):
        self.create()

        _, prompts = self.review()

        report = self.report("review")
        for message in (EVAL, EXEC, COMPILE):
            self.assertIn(f"[existing] {message}", report)
        self.assertIn("**Baseline: 3 existing**", report)
        self.assertEqual(len(prompts), 1)

    def test_a_new_error_is_reported_and_does_not_fail_the_command(self):
        """`-r` has never exited non-zero over a finding, baseline or not."""
        self.create()
        self.seed_legacy(DUNDER_IMPORT_LINE)

        result, _ = self.review()

        self.assertIn(f"[new] {DUNDER_IMPORT}", self.report("review"))
        self.assertIn("**Baseline: 1 new, 3 existing**", self.report("review"))
        self.assertIn("🧾 Baseline: 1 new, 3 existing", result.output)

    def test_no_fingerprint_reaches_the_prompt(self):
        """§8.5 by abstention: the classification is post hoc, so nothing to send."""
        self.create()
        fingerprints = {entry.fingerprint for entry in self.entries()}
        self.assertEqual(len(fingerprints), 3)

        _, prompts = self.review()

        for fingerprint in fingerprints:
            self.assertNotIn(fingerprint, prompts[0])

    def test_the_review_of_this_diff_feeds_the_next_baseline(self):
        """The optional `findings` array of the review envelope, end to end."""
        ai_finding = {
            "file_path": LEGACY_FILE,
            "line_start": 2,
            "line_end": 2,
            "severity": "warning",
            "category": "review",
            "message": "The template engine is called with raw input.",
        }
        with self.stubbed_ai(findings=[ai_finding]):
            self.assertEqual(
                self.run_cli("-r", "--no-unstaged-check").exit_code, 0
            )

        run = self.create()

        self.assertEqual(run.ai_findings, 1, run.warnings)
        self.assertEqual(len(self.entries()), 4)
        ai_entries = [entry for entry in self.entries() if entry.source == "ai"]
        self.assertEqual(len(ai_entries), 1)
        self.assertTrue(
            ai_entries[0].low_confidence,
            "an AI finding has no rule to be identified by",
        )
        self.assertEqual(ai_entries[0].status, BaselineStatus.EXISTING)

    def test_a_cached_review_of_another_diff_is_refused(self):
        """Findings located by line number are worthless against another revision."""
        ai_finding = {
            "file_path": LEGACY_FILE,
            "line_start": 2,
            "line_end": 2,
            "severity": "warning",
            "category": "review",
            "message": "The template engine is called with raw input.",
        }
        with self.stubbed_ai(findings=[ai_finding]):
            self.assertEqual(
                self.run_cli("-r", "--no-unstaged-check").exit_code, 0
            )

        self.seed_legacy(DUNDER_IMPORT_LINE)
        run = self.create()

        self.assertEqual(run.ai_findings, 0)
        self.assertTrue(
            any("--refresh" in warning for warning in run.warnings), run.warnings
        )
        self.assertEqual(
            len(self.entries()), 4, "only the linter's findings were recorded"
        )


class TestTheFullReviewFlow(BaselineIntegrationTestCase):
    """`-f`: the same statuses, over a diff taken against the branch point.

    The baseline is built from the local diff, and the assertion is that the
    classification does not depend on which of the two diffs produced it — the
    same change over the same lines fingerprints the same either way.
    """

    def setUp(self):
        super().setUp()
        self.seed_legacy()
        origin = os.path.join(tempfile.mkdtemp(prefix="gitpr_baseline_origin_"), "origin.git")
        self.addCleanup(shutil.rmtree, os.path.dirname(origin), ignore_errors=True)
        # A bare clone of the fixture is the offline stand-in for a remote: the
        # full review fetches it, resolves the branch point from it and diffs
        # against it, all over the file protocol.
        self._git("clone", "--bare", "--quiet", "--", self.dir, origin)
        self._git("remote", "add", "origin", origin)
        self._git("fetch", "--quiet", "origin")
        self._git("remote", "set-head", "origin", "main")

    def test_the_full_review_reports_the_same_statuses(self):
        self.create()

        with self.stubbed_ai():
            result = self.run_cli("-f", "--no-unstaged-check")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("🧾 Baseline: 3 existing", result.output)
        report = self.report("full_review")
        for message in (EVAL, EXEC, COMPILE):
            self.assertIn(f"[existing] {message}", report)

    def test_a_new_error_does_not_fail_the_full_review_either(self):
        self.create()
        self.seed_legacy(DUNDER_IMPORT_LINE)

        with self.stubbed_ai():
            result = self.run_cli("-f", "--no-unstaged-check")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(f"[new] {DUNDER_IMPORT}", self.report("full_review"))


class TestTheRemotePullRequestReview(BaselineIntegrationTestCase):
    """`review-pr`: the same classification, on a diff that came from a forge."""

    class Forge:
        """The three methods the remote review uses, and the comment it posted."""

        name = "github"
        supports_reviewable_diff = True

        def __init__(self, diff):
            self.diff = diff
            self.comments = []

        def get_pull_request(self, repo, pr_id):
            return PullRequestResult(
                id=pr_id,
                url=f"https://example.invalid/pull/{pr_id}",
                number=pr_id,
                state="open",
                source_branch="feature/legacy",
                target_branch="main",
                provider="github",
            )

        def get_pull_request_diff(self, repo, pr_id):
            return self.diff

        def add_comment(self, repo, pr_id, body):
            self.comments.append(body)

    def setUp(self):
        super().setUp()
        self.seed_legacy()

    def remote_diff(self):
        """The diff of the change, as the forge would serve it."""
        return self._git("diff", "-U1", "-w", "-M", "-B", "HEAD").stdout

    def review(self, post_comment):
        forge = self.Forge(self.remote_diff())
        with self.stubbed_ai():
            result = review_remote_pr(
                42,
                scm_provider=forge,
                repo_ref=RepoRef(
                    raw="https://example.invalid/owner/repo.git",
                    workspace="owner",
                    name="repo",
                    provider="github",
                ),
                post_comment=post_comment,
            )
        return result, forge

    def test_the_alerts_and_the_published_comment_carry_the_status(self):
        self.create()

        result, forge = self.review(post_comment=True)

        self.assertEqual(len(result.compared), 3)
        errors = result.linter_results["errors"]
        self.assertEqual(len(errors), 3)
        self.assertTrue(
            all(alert.startswith("[existing] ") for alert in errors), errors
        )
        self.assertEqual(len(forge.comments), 1)
        self.assertIn(f"[existing] {EVAL}", forge.comments[0])
        self.assertNotIn("🧾", forge.comments[0], "the comment is the report, not the run")

    def test_a_new_error_still_reads_as_new_in_the_comment(self):
        self.create()
        self.seed_legacy(DUNDER_IMPORT_LINE)

        _, forge = self.review(post_comment=True)

        self.assertIn(f"[new] {DUNDER_IMPORT}", forge.comments[0])


class TestAnUnusableBaseline(BaselineIntegrationTestCase):
    """A file that cannot be applied: the run stops, and says how to repair it."""

    def setUp(self):
        super().setUp()
        self.seed_legacy()
        self.create()
        self.tamper()

    def tamper(self):
        """A file that is valid JSON, checksummed by GitPR, and from the future.

        Written through `write_manifest` rather than by editing the bytes, so
        the digest is correct and the *version* is the only thing wrong: the one
        condition with no off switch, which is the point of the test.
        """
        manifest = self.manifest()
        manifest.fingerprint_version = "99"
        for index, entry in enumerate(manifest.entries):
            entry.fingerprint = "sha256:" + "0" * 63 + str(index)
        write_manifest(manifest, self.dir)

    def test_the_linter_refuses_instead_of_calling_everything_new(self):
        result = self.lint()

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("cannot be applied", result.stderr)
        self.assertIn("fingerprint_version is 99", result.stderr)
        self.assertIn("baseline validate", result.stderr)
        self.assertIn("baseline update --recompute", result.stderr)
        self.assertNotIn(EVAL, result.stdout, "the run stopped before linting")

    def test_the_review_refuses_too(self):
        with self.stubbed_ai():
            result = self.run_cli("-r", "--no-unstaged-check")

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("cannot be applied", result.stderr)

    def test_the_notice_never_lands_in_the_json_document(self):
        result = self.run_cli("risk", "--no-history", "--format", "json")

        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("cannot be applied", result.stderr)
        self.assertNotIn("cannot be applied", result.stdout)
        self.assertEqual(result.stdout.strip(), "", "stdout stays a JSON stream")

    def test_a_flow_that_never_enforced_it_is_untouched(self):
        """`-c` never read a finding, so a broken baseline is not its business."""
        with self.stubbed_ai():
            result = self.run_cli("-c", "--no-unstaged-check")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("chore: stubbed", result.output)
        self.assertNotIn("cannot be applied", result.output)


class TestUpdateMovesTheRecordForward(BaselineIntegrationTestCase):
    """`update`: what a human decided survives, and what is gone is closed."""

    def setUp(self):
        super().setUp()
        self.seed_legacy()
        # Recorded yesterday, so "the date a finding was first seen" can be told
        # apart from "the date this run stamped".
        self.yesterday = date.today() - timedelta(days=1)
        self.create(today=self.yesterday)

    def test_a_finding_that_is_gone_is_marked_resolved_with_its_history(self):
        self.seed_legacy(DUNDER_IMPORT_LINE)
        self.update()
        self.assertEqual(len(self.entries()), 4)

        self.seed_legacy()
        run = self.update()

        self.assertTrue(run.written)
        resolved = [
            entry for entry in self.entries() if entry.status is BaselineStatus.RESOLVED
        ]
        self.assertEqual([entry.line_start for entry in resolved], [5])
        self.assertTrue(resolved[0].resolved_at)
        # The date it entered the record is the one it keeps.
        self.assertEqual(self.entry_at(2).first_seen_date, self.yesterday.isoformat())
        self.assertEqual(self.entry_at(2).status, BaselineStatus.EXISTING)

    def test_a_file_outside_the_diff_is_left_alone(self):
        """A narrow diff is no evidence about a file it does not mention.

        The finding is still there — it was committed, not fixed — and its entry
        has to survive a run that never looked at that file. Calling it
        `resolved` here is the dangerous direction: the next run would read the
        finding as `new` and block on work nobody did.
        """
        self.commit(LEGACY_FILE, legacy_source(), message="chore: keep legacy")
        self.commit("app/other.py", "def helper():\n    return 1\n", message="chore: helper")
        self.write("app/other.py", "def helper():\n    return 2\n")

        run = self.update()  # only app/other.py is in the diff now

        self.assertTrue(run.written)
        legacy = [entry for entry in self.entries() if entry.file_path == LEGACY_FILE]
        self.assertEqual(len(legacy), 3)
        self.assertEqual({entry.status for entry in legacy}, {BaselineStatus.EXISTING})
        self.assertEqual(
            {entry.first_seen_date for entry in legacy},
            {self.yesterday.isoformat()},
            "a run that never saw the file does not touch its entries",
        )

    def test_recompute_re_fingerprints_and_carries_the_decision(self):
        """What a FINGERPRINT_VERSION bump points at, and why it is not a reset."""
        manifest = self.manifest()
        manifest.fingerprint_version = "99"
        for index, entry in enumerate(manifest.entries):
            entry.fingerprint = "sha256:" + "0" * 63 + str(index)
        debt = manifest.entries[0]
        debt.status = BaselineStatus.ACCEPTED_DEBT
        debt.accepted_debt_owner = "time-plataforma"
        debt.accepted_debt_reason = "The template engine leaves in the migration."
        debt.accepted_debt_due_date = "2026-12-31"
        write_manifest(manifest, self.dir)

        run = self.update(recompute=True)

        self.assertEqual(run.warnings, [])
        self.assertEqual(self.manifest().fingerprint_version, FINGERPRINT_VERSION)
        updated = self.entry_at(debt.line_start)
        self.assertEqual(updated.status, BaselineStatus.ACCEPTED_DEBT)
        self.assertEqual(updated.accepted_debt_owner, "time-plataforma")
        self.assertEqual(updated.accepted_debt_due_date, "2026-12-31")
        self.assertEqual(updated.first_seen_date, self.yesterday.isoformat())
        self.assertEqual(len(self.entries()), 3)
        # Re-fingerprinted: the file now carries this build's digests.
        expected = {
            compute_fingerprint(finding, self.dir)
            for finding in lint_findings(self.current_diff(), repo_path=self.dir)
        }
        self.assertEqual({entry.fingerprint for entry in self.entries()}, expected)

    def test_an_empty_diff_writes_nothing(self):
        before = self.baseline_bytes()
        self.commit(LEGACY_FILE, legacy_source(), message="chore: keep legacy")

        run = self.update()

        self.assertFalse(run.written)
        self.assertEqual(self.baseline_bytes(), before)
        self.assertTrue(
            any("nothing was written" in warning for warning in run.warnings),
            run.warnings,
        )

    def current_diff(self):
        return self._git("diff", "-U1", "-w", "-M", "-B", "HEAD").stdout


class TestReproducibilityInASecondClone(BaselineIntegrationTestCase):
    """The criterion the spec is built around: the versioned files are enough.

    A teammate clones the repository — baseline included — applies the same
    change and reaches the same verdict, with nothing of the first machine in
    the record and no network at all.
    """

    def test_a_second_clone_reaches_the_same_verdict(self):
        self.seed_legacy()
        self.create()
        self.commit_baseline()

        second = os.path.join(tempfile.mkdtemp(prefix="gitpr_baseline_clone_"), "clone")
        self.addCleanup(shutil.rmtree, os.path.dirname(second), ignore_errors=True)
        # `-c core.autocrlf=false` on the clone itself: a machine with the
        # system default of `true` would check the file out with CRLF endings
        # and hash a different line than the first repository did.
        run_git(self.dir, "-c", "core.autocrlf=false", "clone", "--quiet", "--", self.dir, second)
        with open(
            os.path.join(second, LEGACY_FILE), "w", encoding="utf-8", newline="\n"
        ) as handle:
            handle.write(legacy_source())

        manifest, problems = read_manifest(second)
        self.assertEqual(problems, [])
        self.assertIsNotNone(manifest)
        self.assertEqual(
            {entry.fingerprint for entry in manifest.entries},
            {entry.fingerprint for entry in self.entries()},
            "the identity of a finding does not depend on the machine",
        )

        diff = run_git(second, "diff", "-U1", "-w", "-M", "-B", "HEAD").stdout
        compared = compare_against_baseline(
            lint_findings(diff, repo_path=second), manifest, repo_path=second
        )

        self.assertEqual(len(compared), 3)
        self.assertEqual(
            {item.baseline_status for item in compared}, {BaselineStatus.EXISTING}
        )
        self.assertEqual(
            {item.fingerprint for item in compared},
            {entry.fingerprint for entry in manifest.entries},
        )
        self.assertFalse(
            any(item.is_blocking for item in compared),
            "nothing in this change is new work",
        )


class TestTheFixtureItself(BaselineIntegrationTestCase):
    """Guards on the guards: what answers, and what is kept off the network."""

    def test_the_network_guard_is_installed(self):
        with self.assertRaises(AssertionError):
            socket.create_connection(("8.8.8.8", 53), timeout=0.1)

    def test_the_review_stub_is_what_answers(self):
        self.seed_legacy()

        with self.stubbed_ai():
            result = self.run_cli("-r", "--no-unstaged-check")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Stubbed.", self.report("review"))

    def test_the_prompt_cache_lives_outside_the_home_directory(self):
        import src.cache

        resolved = str(src.cache.get_cache_base_dir())
        self.assertTrue(resolved.startswith(self.home), resolved)


if __name__ == "__main__":
    unittest.main()
