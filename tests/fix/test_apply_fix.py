"""End-to-end tests for the fix pipeline, against a real repository.

The AI and the review cache are the only things stubbed: everything after them
— extraction, ``git apply --check``, classification, applying, the history —
runs for real, which is the point. A patch that reaches ``apply_candidates`` in
these tests is one git itself generated (``patch_for``), so "it applied" means
something.

The four acceptance criteria of the plan are here by name: the dry run writes
nothing, the batch takes only the SAFE patches, the branch is created from the
right HEAD with the original left intact, and every applied patch leaves a
fully populated history entry.
"""
import contextlib
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.fix.apply_fix import (
    FIX_ACTION,
    PROMPT_VERSION,
    FixError,
    apply_candidates,
    collect_candidates,
    find_candidate,
    findings_prompt,
    resolve_review,
    review_text,
    reviewed_diff,
    select_safe,
)
from src.fix.fix_history import find_entry, history_path, load_history
from src.fix.patch_applier import current_branch, current_head, repo_root
from src.fix.patch_provenance import PatchSafety
from src.updater import __version__
from tests.fix.git_fixture import GitRepoTestCase

NEW_BODY = "def greet(name):\n    return f'Hi, {name}!'\n"
OTHER_ORIGINAL = "VALUE = 1\n"
OTHER_BODY = "VALUE = 2\n"

#: What the tree looks like at collection time. Its content is irrelevant — the
#: pipeline only sends it to the model — but it must not be empty, because an
#: empty working diff is the "nothing to fix" error.
CURRENT_DIFF = "diff --git a/src/app.py b/src/app.py\n@@ -1,2 +1,2 @@\n"

REVIEW_RECORD = {
    "action_type": "review",
    "response": {"review": "## Review\n- greet() returns a hard-coded greeting\n"},
}


class FixTestCase(GitRepoTestCase):
    """A seeded repository plus the stubs that stand in for the AI."""

    prefix = "gitpr_fix_apply_"

    def setUp(self):
        super().setUp()
        self.original = self.seed()

    # ── stubs ────────────────────────────────────────────────────────────
    @contextlib.contextmanager
    def stubbed(self, ai=None, cached=None, diff=CURRENT_DIFF, api_key="key"):
        """Patch the pipeline's edges; the git work in between stays real."""
        mocks = {}
        with contextlib.ExitStack() as stack:
            mocks["ai"] = stack.enter_context(
                patch("src.fix.apply_fix.call_ai_model", return_value=ai)
            )
            mocks["cached"] = stack.enter_context(
                patch("src.fix.apply_fix.get_cached_response", return_value=cached)
            )
            mocks["saved"] = stack.enter_context(
                patch("src.fix.apply_fix.save_cached_response")
            )
            stack.enter_context(
                patch("src.fix.apply_fix.get_ai_provider", return_value="gemini")
            )
            stack.enter_context(
                patch("src.fix.apply_fix.get_api_key", return_value=api_key)
            )
            stack.enter_context(
                patch(
                    "src.fix.apply_fix.get_api_model",
                    return_value="gemini-pro-latest",
                )
            )
            stack.enter_context(
                patch("src.fix.apply_fix.reviewed_diff", return_value=diff)
            )
            # The skill file is read from the real working directory otherwise,
            # which would make these tests depend on the developer's checkout.
            stack.enter_context(patch("src.core.get_skill_context", return_value=""))
            yield mocks

    # ── builders ─────────────────────────────────────────────────────────
    def patch_text(self, content=NEW_BODY):
        """A patch changing src/app.py to *content*, as git wrote it."""
        return self.patch_for("src/app.py", content)

    def two_file_patch(self):
        """A patch touching two files — always EXPERIMENTAL."""
        self.commit("src/other.py", OTHER_ORIGINAL)
        return self.patch_for("src/app.py", NEW_BODY) + self.patch_for(
            "src/other.py", OTHER_BODY
        )

    def finding(self, diff, **overrides):
        """One finding as the model returns it."""
        data = {
            "file_path": "src/app.py",
            "line_start": 2,
            "line_end": 2,
            "severity": "minor",
            "category": "style",
            "message": "greet() returns a hard-coded greeting",
            "confidence": "high",
            "diff": diff,
            "suggested_test": "assert greet('a') == 'Hi, a!'",
        }
        data.update(overrides)
        return data

    def collect(self, findings, **kwargs):
        """Run the real pipeline with the model's answer stubbed in."""
        kwargs.setdefault("root", self.dir)
        kwargs.setdefault("quiet", True)
        with self.stubbed(ai={"findings": findings}):
            return collect_candidates(REVIEW_RECORD, **kwargs)


class TestResolveReview(FixTestCase):
    def test_no_cached_review_names_the_command_that_makes_one(self):
        with patch("src.fix.apply_fix.resolve_last_review", return_value=None):
            with self.assertRaises(FixError) as caught:
                resolve_review()
        self.assertIn("gitpr -r", str(caught.exception))

    def test_the_cached_review_is_returned(self):
        with patch("src.fix.apply_fix.resolve_last_review", return_value=REVIEW_RECORD):
            self.assertIs(resolve_review(), REVIEW_RECORD)

    def test_the_review_text_comes_out_of_the_record(self):
        self.assertEqual(review_text(REVIEW_RECORD), REVIEW_RECORD["response"]["review"])

    def test_a_record_without_a_response_reads_as_empty(self):
        self.assertEqual(review_text({"action_type": "review"}), "")


class TestReviewedDiff(FixTestCase):
    def test_a_review_re_derives_the_working_diff(self):
        with patch("src.core.get_git_diff", return_value="working\n") as working:
            self.assertEqual(reviewed_diff({"action_type": "review"}), "working\n")
        working.assert_called_once()

    def test_a_full_review_re_derives_the_branch_diff(self):
        with patch("src.core.get_git_diff", return_value="working\n") as working, patch(
            "src.core.get_git_full_diff", return_value="branch\n"
        ) as branch:
            self.assertEqual(reviewed_diff({"action_type": "fullreview"}), "branch\n")
        branch.assert_called_once()
        working.assert_not_called()

    def test_a_failed_diff_reads_as_empty(self):
        with patch("src.core.get_git_diff", return_value=None):
            self.assertEqual(reviewed_diff({"action_type": "review"}), "")


class TestFindingsPrompt(FixTestCase):
    def test_the_prompt_carries_the_review_and_the_diff(self):
        prompt = findings_prompt("the review prose", "the current diff")
        self.assertIn("the review prose", prompt)
        self.assertIn("the current diff", prompt)

    def test_the_prompt_asks_for_the_envelope_the_parser_reads(self):
        self.assertIn('"findings"', findings_prompt("r", "d"))


class TestCollectCandidates(FixTestCase):
    def test_a_patch_from_the_model_becomes_a_safe_candidate(self):
        candidates = self.collect([self.finding(self.patch_text())])
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.finding.id, "FIX-001")
        self.assertEqual(candidate.safety, PatchSafety.SAFE)
        self.assertEqual(candidate.safety_reason, "safe")
        self.assertEqual(candidate.diff_unified, self.patch_text())

    def test_findings_are_numbered_in_the_order_they_arrive(self):
        candidates = self.collect(
            [self.finding(self.patch_text()), self.finding(self.patch_text(NEW_BODY + "\n"))]
        )
        self.assertEqual([c.finding.id for c in candidates], ["FIX-001", "FIX-002"])

    def test_the_provenance_names_the_model_and_the_prompt(self):
        candidate = self.collect([self.finding(self.patch_text())])[0]
        provenance = candidate.provenance
        self.assertEqual(provenance.finding_id, "FIX-001")
        self.assertEqual(provenance.ai_provider, "gemini")
        self.assertEqual(provenance.ai_model, "gemini-pro-latest")
        self.assertEqual(provenance.prompt_version, PROMPT_VERSION)
        self.assertEqual(provenance.gitpr_version, __version__)
        self.assertRegex(provenance.generated_at, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_the_patch_id_is_stable_and_addressable(self):
        first = self.collect([self.finding(self.patch_text())])[0]
        again = self.collect([self.finding(self.patch_text())])[0]
        self.assertEqual(first.patch_id, again.patch_id)
        self.assertTrue(first.patch_id.startswith("FIX-001-"))

    def test_a_patch_that_does_not_apply_is_experimental(self):
        stale = self.patch_text()
        self.commit("src/app.py", "def greet(who):\n    return who\n")
        candidate = self.collect([self.finding(stale)])[0]
        self.assertEqual(candidate.safety, PatchSafety.EXPERIMENTAL)
        self.assertEqual(candidate.safety_reason, "apply_check_failed")

    def test_a_multi_file_patch_is_experimental(self):
        candidate = self.collect([self.finding(self.two_file_patch())])[0]
        self.assertEqual(candidate.safety, PatchSafety.EXPERIMENTAL)
        self.assertEqual(candidate.safety_reason, "multi_file")

    def test_a_declared_low_confidence_is_experimental(self):
        candidate = self.collect(
            [self.finding(self.patch_text(), confidence="low")]
        )[0]
        self.assertEqual(candidate.safety, PatchSafety.EXPERIMENTAL)
        self.assertEqual(candidate.safety_reason, "low_confidence")

    def test_an_excluded_path_is_never_safe(self):
        candidate = self.collect(
            [self.finding(self.patch_text())], excluded_paths=("src/**",)
        )[0]
        self.assertEqual(candidate.safety, PatchSafety.REVIEW_REQUIRED)
        self.assertEqual(candidate.safety_reason, "excluded_path")

    def test_a_long_patch_is_never_safe(self):
        candidate = self.collect(
            [self.finding(self.patch_text())], max_lines_changed=1
        )[0]
        self.assertEqual(candidate.safety, PatchSafety.REVIEW_REQUIRED)
        self.assertEqual(candidate.safety_reason, "too_many_lines")

    def test_a_finding_without_a_patch_stays_visible_and_unapplicable(self):
        candidate = self.collect([self.finding("")])[0]
        self.assertEqual(candidate.finding.id, "FIX-001")
        self.assertEqual(candidate.diff_unified, "")
        self.assertEqual(candidate.safety, PatchSafety.EXPERIMENTAL)
        self.assertEqual(candidate.safety_reason, "apply_check_failed")
        # The model's file path is all there is to fall back on.
        self.assertEqual(candidate.finding.file_path, "src/app.py")

    def test_prose_instead_of_the_envelope_is_not_a_crash(self):
        with self.stubbed(ai="I could not find anything to fix."):
            self.assertEqual(
                collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True), ()
            )

    def test_an_empty_envelope_is_not_a_crash(self):
        self.assertEqual(self.collect([]), ())

    def test_an_ai_failure_is_an_error(self):
        with self.stubbed(ai=None):
            with self.assertRaises(FixError):
                collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)

    def test_an_empty_working_diff_is_an_error(self):
        with self.stubbed(diff="   \n"):
            with self.assertRaises(FixError):
                collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)

    def test_a_missing_api_key_is_an_error(self):
        with self.stubbed(api_key=None):
            with self.assertRaises(FixError):
                collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)

    def test_outside_a_repository_it_refuses(self):
        outside = tempfile.mkdtemp(prefix="gitpr_fix_apply_outside_")
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        if repo_root(cwd=outside) is not None:
            self.skipTest("this machine's temp directory sits inside a repository")
        with self.assertRaises(FixError):
            collect_candidates(REVIEW_RECORD, root=outside, quiet=True)

    def test_the_findings_are_read_from_the_cache_without_calling_the_ai(self):
        cached = {"findings": [self.finding(self.patch_text())]}
        with self.stubbed(cached=cached) as mocks:
            candidates = collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)
        mocks["ai"].assert_not_called()
        self.assertEqual(candidates[0].finding.id, "FIX-001")
        self.assertEqual(candidates[0].safety, PatchSafety.SAFE)

    def test_a_cache_hit_is_still_re_checked_against_the_tree(self):
        # The cache holds the model's answer, never the verdict: the tree may
        # have moved since, and only the check against it decides whether the
        # patch can be applied now.
        stale = self.patch_text()
        self.commit("src/app.py", "def greet(who):\n    return who\n")
        with self.stubbed(cached={"findings": [self.finding(stale)]}):
            candidates = collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)
        self.assertEqual(candidates[0].safety, PatchSafety.EXPERIMENTAL)

    def test_the_answer_is_cached_under_the_fix_folder(self):
        with self.stubbed(ai={"findings": [self.finding(self.patch_text())]}) as mocks:
            collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)
        mocks["saved"].assert_called_once()
        folder, action_type, prompt, payload = mocks["saved"].call_args.args
        self.assertEqual((folder, action_type), (FIX_ACTION, FIX_ACTION))
        self.assertIn(REVIEW_RECORD["response"]["review"], prompt)
        self.assertEqual(len(payload["findings"]), 1)

    def test_telemetry_never_reaches_the_cache(self):
        with self.stubbed(
            ai={
                "findings": [self.finding(self.patch_text())],
                "_telemetry_meta": {"total_tokens": 10},
            }
        ) as mocks:
            collect_candidates(REVIEW_RECORD, root=self.dir, quiet=True)
        payload = mocks["saved"].call_args.args[3]
        self.assertEqual(sorted(payload), ["findings"])


class TestFindCandidate(FixTestCase):
    def setUp(self):
        super().setUp()
        self.candidates = self.collect(
            [self.finding(self.patch_text()), self.finding(self.patch_text(NEW_BODY + "\n"))]
        )

    def test_the_right_candidate_comes_back(self):
        self.assertEqual(find_candidate(self.candidates, "FIX-002").finding.id, "FIX-002")

    def test_the_id_is_accepted_in_any_case(self):
        self.assertEqual(find_candidate(self.candidates, "fix-001").finding.id, "FIX-001")

    def test_an_unknown_id_lists_the_known_ones(self):
        with self.assertRaises(FixError) as caught:
            find_candidate(self.candidates, "FIX-999")
        message = str(caught.exception)
        self.assertIn("FIX-999", message)
        self.assertIn("FIX-001, FIX-002", message)

    def test_an_unknown_id_with_no_candidates_says_so(self):
        with self.assertRaises(FixError):
            find_candidate((), "FIX-001")


class TestSelectSafe(FixTestCase):
    def test_only_the_safe_ones_come_back(self):
        candidates = self.collect(
            [self.finding(self.patch_text())],
            excluded_paths=("src/**",),
        )
        self.assertEqual(select_safe(candidates), ())

    def test_the_order_is_kept(self):
        candidates = self.collect(
            [self.finding(self.patch_text()), self.finding(self.patch_text(NEW_BODY + "\n"))]
        )
        self.assertEqual(
            [c.finding.id for c in select_safe(candidates)], ["FIX-001", "FIX-002"]
        )


class TestDryRun(FixTestCase):
    def test_the_working_tree_is_untouched(self):
        candidates = self.collect([self.finding(self.patch_text())])
        before = self.status_porcelain()

        results = apply_candidates(candidates, root=self.dir, dry_run=True)

        self.assertEqual(self.status_porcelain(), before)
        self.assertEqual(self.read("src/app.py"), self.original)
        self.assertFalse(results[0].applied)

    def test_nothing_is_recorded_in_the_history(self):
        candidates = self.collect([self.finding(self.patch_text())])
        apply_candidates(candidates, root=self.dir, dry_run=True)
        self.assertEqual(load_history(self.dir), [])

    def test_the_result_still_carries_the_diff(self):
        candidates = self.collect([self.finding(self.patch_text())])
        results = apply_candidates(candidates, root=self.dir, dry_run=True)
        self.assertEqual(results[0].dry_run_diff, candidates[0].diff_unified)
        self.assertEqual(results[0].patch_id, candidates[0].patch_id)
        self.assertEqual(results[0].files_changed, ("src/app.py",))

    def test_no_branch_is_created(self):
        candidates = self.collect([self.finding(self.patch_text())])
        results = apply_candidates(
            candidates, root=self.dir, dry_run=True, branch="fix/gitpr-20260913120000"
        )
        self.assertEqual(self.current_branch(), "main")
        self.assertIsNone(results[0].branch_created)
        self.assertEqual(self._git("branch", "--list", "fix/gitpr-*").stdout.strip(), "")


class TestApply(FixTestCase):
    def test_the_patch_is_written_and_recorded(self):
        candidates = self.collect([self.finding(self.patch_text())])

        results = apply_candidates(candidates, root=self.dir, dry_run=False)

        self.assertTrue(results[0].applied)
        self.assertEqual(self.read("src/app.py"), NEW_BODY)
        self.assertIn("src/app.py", self.status_porcelain())

        entry = find_entry(results[0].patch_id, self.dir)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["finding_id"], "FIX-001")
        self.assertEqual(entry["file_path"], "src/app.py")
        self.assertEqual(entry["files_changed"], ["src/app.py"])
        self.assertEqual(entry["safety"], "safe")
        self.assertIsNone(entry["branch"])
        self.assertEqual(entry["diff"], candidates[0].diff_unified)
        self.assertRegex(entry["applied_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertIsNone(entry["rolled_back_at"])
        self.assertEqual(entry["provenance"]["ai_provider"], "gemini")
        self.assertEqual(entry["provenance"]["ai_model"], "gemini-pro-latest")
        self.assertEqual(entry["provenance"]["prompt_version"], PROMPT_VERSION)
        self.assertEqual(entry["provenance"]["gitpr_version"], __version__)

    def test_a_patch_git_refuses_is_reported_and_not_recorded(self):
        stale = self.patch_text()
        self.commit("src/app.py", "def greet(who):\n    return who\n")
        candidates = self.collect([self.finding(stale)])
        self.assertEqual(candidates[0].safety, PatchSafety.EXPERIMENTAL)

        results = apply_candidates(candidates, root=self.dir, dry_run=False)

        self.assertFalse(results[0].applied)
        self.assertTrue(results[0].warnings)
        self.assertEqual(load_history(self.dir), [])

    def test_a_refused_patch_leaves_the_file_alone(self):
        stale = self.patch_text()
        moved = "def greet(who):\n    return who\n"
        self.commit("src/app.py", moved)
        candidates = self.collect([self.finding(stale)])
        apply_candidates(candidates, root=self.dir, dry_run=False)
        self.assertEqual(self.read("src/app.py"), moved)

    def test_the_batch_continues_after_a_refused_patch(self):
        stale = self.patch_text()
        self.commit("src/app.py", "def greet(who):\n    return who\n")
        good = self.patch_for("src/app.py", NEW_BODY)
        candidates = self.collect([self.finding(stale), self.finding(good)])

        results = apply_candidates(candidates, root=self.dir, dry_run=False)

        self.assertFalse(results[0].applied)
        self.assertTrue(results[1].applied)
        self.assertEqual(self.read("src/app.py"), NEW_BODY)

    def test_only_the_subset_handed_over_is_applied(self):
        candidates = self.collect(
            [self.finding(self.patch_text()), self.finding(self.patch_text(NEW_BODY + "\n"))]
        )

        results = apply_candidates(candidates[:1], root=self.dir, dry_run=False)

        self.assertEqual([r.patch_id for r in results], [candidates[0].patch_id])
        self.assertEqual(self.read("src/app.py"), NEW_BODY)
        self.assertIsNone(find_entry(candidates[1].patch_id, self.dir))

    def test_a_multi_file_patch_is_never_in_the_safe_batch(self):
        candidates = self.collect(
            [self.finding(self.patch_text()), self.finding(self.two_file_patch())]
        )
        self.assertEqual([c.finding.id for c in select_safe(candidates)], ["FIX-001"])

        apply_candidates(select_safe(candidates), root=self.dir, dry_run=False)

        self.assertEqual(self.read("src/app.py"), NEW_BODY)
        self.assertEqual(self.read("src/other.py"), OTHER_ORIGINAL)


class TestBranch(FixTestCase):
    def test_the_branch_is_created_from_head_and_keeps_the_original_intact(self):
        head_before = current_head(cwd=self.dir)
        candidates = self.collect([self.finding(self.patch_text())])

        results = apply_candidates(
            candidates,
            root=self.dir,
            dry_run=False,
            branch="fix/gitpr-20260913120000",
        )

        self.assertEqual(results[0].branch_created, "fix/gitpr-20260913120000")
        self.assertEqual(results[0].warnings, ())
        self.assertEqual(self.current_branch(), "fix/gitpr-20260913120000")
        self.assertEqual(current_head(cwd=self.dir), head_before)
        self.assertEqual(self.read("src/app.py"), NEW_BODY)
        # The original branch's commit is untouched — the fix is uncommitted.
        self.assertEqual(self._git("show", "main:src/app.py").stdout, self.original)

    def test_the_history_remembers_the_branch(self):
        candidates = self.collect([self.finding(self.patch_text())])
        results = apply_candidates(
            candidates, root=self.dir, dry_run=False, branch="fix/gitpr-x"
        )
        self.assertEqual(find_entry(results[0].patch_id, self.dir)["branch"], "fix/gitpr-x")

    def test_a_branch_that_cannot_be_created_aborts_before_anything_is_written(self):
        candidates = self.collect([self.finding(self.patch_text())])

        with self.assertRaises(FixError):
            apply_candidates(candidates, root=self.dir, dry_run=False, branch="main")

        self.assertEqual(self.read("src/app.py"), self.original)
        self.assertEqual(load_history(self.dir), [])

    def test_applying_in_place_creates_no_branch(self):
        candidates = self.collect([self.finding(self.patch_text())])
        results = apply_candidates(candidates, root=self.dir, dry_run=False)
        self.assertIsNone(results[0].branch_created)
        self.assertEqual(self.current_branch(), "main")
        self.assertEqual(self.read("src/app.py"), NEW_BODY)


class TestDirtyTreeWarning(FixTestCase):
    def test_a_target_with_uncommitted_changes_is_warned_about(self):
        candidates = self.collect([self.finding(self.patch_text())])
        self.write("src/app.py", self.original + "# a local edit\n")

        results = apply_candidates(candidates, root=self.dir, dry_run=True)

        self.assertTrue(any("src/app.py" in warning for warning in results[0].warnings))

    def test_an_unrelated_dirty_file_is_not_warned_about(self):
        candidates = self.collect([self.finding(self.patch_text())])
        self.write("notes.txt", "scratch\n")

        results = apply_candidates(candidates, root=self.dir, dry_run=True)

        self.assertEqual(results[0].warnings, ())

    def test_a_clean_tree_is_not_warned_about(self):
        candidates = self.collect([self.finding(self.patch_text())])
        results = apply_candidates(candidates, root=self.dir, dry_run=True)
        self.assertEqual(results[0].warnings, ())


class TestRepositoryRoot(FixTestCase):
    def test_a_subdirectory_root_is_normalized_to_the_top_level(self):
        # A unified diff carries paths relative to the repository top level, so
        # a caller standing in a subdirectory must still find the patch applied
        # where it belongs — and the history at the top level, not in the
        # subdirectory it happened to be called from.
        subdir = os.path.join(self.dir, "src")
        candidates = self.collect([self.finding(self.patch_text())])

        results = apply_candidates(candidates, root=subdir, dry_run=False)

        self.assertTrue(results[0].applied)
        self.assertEqual(self.read("src/app.py"), NEW_BODY)
        self.assertTrue(os.path.exists(history_path(self.dir)))
        self.assertFalse(os.path.exists(os.path.join(subdir, ".gitpr")))


if __name__ == "__main__":
    unittest.main()
