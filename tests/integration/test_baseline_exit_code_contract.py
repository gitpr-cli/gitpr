"""The exit code every flow answers with when the baseline cannot be applied.

`docs/baseline-suppressions.md` (section 3, "Unusable baseline: exit codes per
flow") publishes a table, and this file is what keeps that table honest:

* the flows that enforce the baseline and are not `check` refuse with exit 1;
* `gitpr check` refuses with exit 2, because a pipeline has to tell "failed"
  (1) from "could not evaluate" (2);
* every flow that never enforced the baseline is untouched.

The unusable file is the one `TestAnUnusableBaseline` already builds: valid
JSON, correctly checksummed, but from a fingerprint version this build does not
know — the one condition with no off switch.
"""

import os
import shutil
import tempfile
from unittest.mock import patch

from src.domain.baseline import BaselineError
from src.infrastructure.baseline.local_baseline_repository import write_manifest
from src.infrastructure.scm.base import RepoRef
from src.review.remote_pr import review_remote_pr
from tests.integration.test_baseline_effect_on_review_linter_risk import (
    LEGACY_FILE,
    BaselineIntegrationTestCase,
)

REFUSAL = "cannot be applied"


class TestBaselineExitCodeContract(BaselineIntegrationTestCase):
    """One unusable baseline, every flow that reads it."""

    def setUp(self):
        super().setUp()
        self.seed_legacy()
        self.create()
        manifest = self.manifest()
        manifest.fingerprint_version = "99"
        for index, entry in enumerate(manifest.entries):
            entry.fingerprint = "sha256:" + "0" * 63 + str(index)
        write_manifest(manifest, self.dir)

    def add_origin(self):
        """The offline stand-in for a remote that `-f` fetches and diffs against."""
        origin = os.path.join(
            tempfile.mkdtemp(prefix="gitpr_baseline_origin_"), "origin.git"
        )
        self.addCleanup(shutil.rmtree, os.path.dirname(origin), ignore_errors=True)
        self._git("clone", "--bare", "--quiet", "--", self.dir, origin)
        self._git("remote", "add", "origin", origin)
        self._git("fetch", "--quiet", "origin")
        self._git("remote", "set-head", "origin", "main")

    # ── exit 1: the flows that enforce the baseline ─────────────────────
    def test_linter_exits_1(self):
        result = self.lint()
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(REFUSAL, result.stderr)

    def test_review_exits_1(self):
        with self.stubbed_ai():
            result = self.run_cli("-r", "--no-unstaged-check")
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(REFUSAL, result.stderr)

    def test_full_review_exits_1(self):
        self.add_origin()
        with self.stubbed_ai():
            result = self.run_cli("-f", "--no-unstaged-check")
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(REFUSAL, result.stderr)

    def test_file_audit_exits_1(self):
        with self.stubbed_ai():
            result = self.run_cli("-i", LEGACY_FILE, "--no-unstaged-check")
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(REFUSAL, result.stderr)

    def test_risk_exits_1(self):
        result = self.run_cli("risk", "--no-history", "--format", "json")
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(REFUSAL, result.stderr)

    def test_review_pr_exits_1(self):
        """The refusal comes before the forge is asked for anything."""

        class Forge:
            name = "github"
            supports_reviewable_diff = True

        repo_ref = RepoRef(
            raw="https://example.invalid/owner/repo.git",
            workspace="owner",
            name="repo",
            provider="github",
        )

        with self.assertRaises(BaselineError):
            review_remote_pr(42, scm_provider=Forge(), repo_ref=repo_ref)

        with patch(
            "src.main._resolve_scm_context", return_value=(Forge(), repo_ref)
        ), self.stubbed_ai():
            result = self.run_cli("review-pr", "42")
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn(REFUSAL, result.stderr)

    # ── exit 2: the pipeline command ────────────────────────────────────
    def test_check_exits_2(self):
        result = self.run_cli("check", "--no-ia", "--base", "HEAD", "--format", "json")
        self.assertEqual(result.exit_code, 2, result.output)

    # ── no effect: the flows that never enforced the baseline ───────────
    def test_commit_flow_is_untouched(self):
        self.write(".git/COMMIT_EDITMSG", "\n# Git commit message\n")
        with self.stubbed_ai():
            result = self.run_cli(
                "-c", "--hook", ".git/COMMIT_EDITMSG", "--no-unstaged-check"
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn(REFUSAL, result.output)
