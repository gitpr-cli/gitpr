"""Acceptance 2: the safety classification matrix, criterion by criterion.

Every row isolates one criterion (or one precedence between two) and asserts
both the class and the reason code. A failing row names itself in the output.
"""
import unittest

from src.diff_parser import PatchSummary
from src.fix.patch_provenance import PatchSafety
from src.fix.patch_safety_classifier import (
    REASON_APPLY_CHECK_FAILED,
    REASON_EXCLUDED_PATH,
    REASON_LOW_CONFIDENCE,
    REASON_MULTI_FILE,
    REASON_MULTIPLE_HUNKS,
    REASON_REMOVES_CALL,
    REASON_SAFE,
    REASON_TOO_MANY_LINES,
    classify_patch,
)

EXCLUDED = (
    "database/migrations/**",
    ".github/workflows/**",
    "docker/**",
    "**/*.ci.yml",
)


def summary(files=("src/a.py",), hunks=1, added=1, removed=0, removed_lines=()):
    """A PatchSummary built from the pieces a test cares about."""
    return PatchSummary(
        files=tuple(files),
        hunks=hunks,
        added=added,
        removed=removed,
        removed_lines=tuple(removed_lines),
    )


class TestClassifyPatchMatrix(unittest.TestCase):
    def _assert_case(self, expected_class, expected_reason, **kwargs):
        patch_summary = kwargs.pop("summary")
        result = classify_patch(patch_summary, **kwargs)
        self.assertEqual(result, (expected_class, expected_reason))

    def test_safe_baseline(self):
        self._assert_case(PatchSafety.SAFE, REASON_SAFE, summary=summary())

    def test_apply_check_failure_is_experimental(self):
        self._assert_case(
            PatchSafety.EXPERIMENTAL,
            REASON_APPLY_CHECK_FAILED,
            summary=summary(),
            applies_cleanly=False,
        )

    def test_apply_check_failure_outranks_every_other_criterion(self):
        # A perfect-looking patch that git refuses is still EXPERIMENTAL, and
        # the reason names the check, not the secondary criteria.
        self._assert_case(
            PatchSafety.EXPERIMENTAL,
            REASON_APPLY_CHECK_FAILED,
            summary=summary(
                files=("a.py", "b.py"),
                hunks=4,
                added=50,
                removed=50,
                removed_lines=("do_thing()",),
            ),
            confidence="low",
            applies_cleanly=False,
            excluded_paths=EXCLUDED,
        )

    def test_several_files_is_experimental(self):
        self._assert_case(
            PatchSafety.EXPERIMENTAL,
            REASON_MULTI_FILE,
            summary=summary(files=("src/a.py", "src/b.py")),
        )

    def test_multi_file_outranks_low_confidence(self):
        self._assert_case(
            PatchSafety.EXPERIMENTAL,
            REASON_MULTI_FILE,
            summary=summary(files=("src/a.py", "src/b.py")),
            confidence="low",
        )

    def test_low_confidence_is_experimental(self):
        for declared in ("low", "LOW", "  Low  "):
            with self.subTest(confidence=declared):
                self._assert_case(
                    PatchSafety.EXPERIMENTAL,
                    REASON_LOW_CONFIDENCE,
                    summary=summary(),
                    confidence=declared,
                )

    def test_confidence_is_allowed_to_be_absent(self):
        for declared in (None, "", "medium", "high", "desconhecida"):
            with self.subTest(confidence=declared):
                self._assert_case(
                    PatchSafety.SAFE, REASON_SAFE, summary=summary(), confidence=declared
                )

    def test_excluded_path_is_review_required(self):
        for path, pattern in (
            ("database/migrations/2026_add_x.py", "database/migrations/**"),
            (".github/workflows/ci.yml", ".github/workflows/**"),
            ("svc/app.ci.yml", "**/*.ci.yml"),
            ("docker/api/Dockerfile", "docker/**"),
        ):
            with self.subTest(path=path, pattern=pattern):
                self._assert_case(
                    PatchSafety.REVIEW_REQUIRED,
                    REASON_EXCLUDED_PATH,
                    summary=summary(files=(path,)),
                    excluded_paths=(pattern,),
                )

    def test_a_path_outside_the_excluded_ones_stays_safe(self):
        self._assert_case(
            PatchSafety.SAFE,
            REASON_SAFE,
            summary=summary(files=("src/database/migrations_helper.py",)),
            excluded_paths=EXCLUDED,
        )

    def test_a_leading_double_star_pattern_needs_a_directory(self):
        # fnmatch turns '**/' into a mandatory path segment, so a root-level
        # 'app.ci.yml' is not covered by '**/*.ci.yml'. Pinned here because the
        # default configuration ships that pattern and the limit is silent.
        self._assert_case(
            PatchSafety.SAFE,
            REASON_SAFE,
            summary=summary(files=("app.ci.yml",)),
            excluded_paths=("**/*.ci.yml",),
        )

    def test_dot_slash_prefix_does_not_defeat_a_pattern(self):
        self._assert_case(
            PatchSafety.REVIEW_REQUIRED,
            REASON_EXCLUDED_PATH,
            summary=summary(files=("./database/migrations/x.py",)),
            excluded_paths=EXCLUDED,
        )

    def test_excluded_path_outranks_hunk_and_size_criteria(self):
        self._assert_case(
            PatchSafety.REVIEW_REQUIRED,
            REASON_EXCLUDED_PATH,
            summary=summary(
                files=("docker/Dockerfile",), hunks=3, added=40, removed=40,
                removed_lines=("run_server()",),
            ),
            excluded_paths=EXCLUDED,
        )

    def test_hunk_count_other_than_one_is_review_required(self):
        for hunks in (0, 2, 7):
            with self.subTest(hunks=hunks):
                self._assert_case(
                    PatchSafety.REVIEW_REQUIRED,
                    REASON_MULTIPLE_HUNKS,
                    summary=summary(hunks=hunks),
                )

    def test_the_size_limit_is_inclusive(self):
        self._assert_case(
            PatchSafety.SAFE, REASON_SAFE, summary=summary(added=3, removed=2)
        )

    def test_one_line_over_the_limit_is_review_required(self):
        self._assert_case(
            PatchSafety.REVIEW_REQUIRED,
            REASON_TOO_MANY_LINES,
            summary=summary(added=4, removed=2),
        )

    def test_the_size_limit_is_configurable(self):
        self._assert_case(
            PatchSafety.SAFE,
            REASON_SAFE,
            summary=summary(added=20, removed=5),
            max_lines_changed=25,
        )

    def test_size_outranks_the_removed_call_criterion(self):
        self._assert_case(
            PatchSafety.REVIEW_REQUIRED,
            REASON_TOO_MANY_LINES,
            summary=summary(added=10, removed=1, removed_lines=("helper()",)),
        )

    def test_removing_a_call_like_line_is_review_required(self):
        for line in (
            "    return compute(x)",
            "helper()",
            "obj.method(arg)",
            "# calls helper() sometimes",
        ):
            with self.subTest(line=line):
                self._assert_case(
                    PatchSafety.REVIEW_REQUIRED,
                    REASON_REMOVES_CALL,
                    summary=summary(added=1, removed=1, removed_lines=(line,)),
                )

    def test_removing_plain_text_stays_safe(self):
        for line in ("", "    # an outdated note", "old value = 1"):
            with self.subTest(line=line):
                self._assert_case(
                    PatchSafety.SAFE,
                    REASON_SAFE,
                    summary=summary(added=1, removed=1, removed_lines=(line,)),
                )

    def test_an_empty_patch_is_never_safe(self):
        self._assert_case(
            PatchSafety.REVIEW_REQUIRED,
            REASON_MULTIPLE_HUNKS,
            summary=summary(files=(), hunks=0, added=0, removed=0),
        )


class TestClassificationIsDeterministic(unittest.TestCase):
    def test_the_same_input_always_gives_the_same_verdict(self):
        cases = (
            (summary(), {}),
            (summary(files=("a", "b")), {}),
            (summary(hunks=2), {"confidence": "low"}),
            (summary(added=9), {"max_lines_changed": 3}),
            (summary(files=("docker/x",)), {"excluded_paths": ("docker/**",)}),
        )
        for patch_summary, kwargs in cases:
            with self.subTest(summary=patch_summary):
                first = classify_patch(patch_summary, **kwargs)
                self.assertEqual(first, classify_patch(patch_summary, **kwargs))

    def test_excluded_paths_do_not_leak_between_calls(self):
        # The default must stay empty: a previous call's patterns may not
        # change the verdict of a later one.
        classify_patch(summary(files=("docker/x",)), excluded_paths=("docker/**",))
        self.assertEqual(
            classify_patch(summary(files=("docker/x",))), (PatchSafety.SAFE, REASON_SAFE)
        )


if __name__ == "__main__":
    unittest.main()
