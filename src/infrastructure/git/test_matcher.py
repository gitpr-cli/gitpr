"""Test matcher: correlates production files with test files changed in the diff."""

import os
from pathlib import Path
from typing import Optional

from src.domain.risk.risk_rules import is_non_executable_file, is_test_file
from src.domain.tests_generation.framework_detector import detect_test_framework


def find_related_test_files(
    file_path: str,
    all_changed_files: list[str],
    repo_path: Optional[str] = None,
) -> list[str]:
    """Finds test files in *all_changed_files* that correspond to *file_path*.

    Matches by naming convention (e.g. ``src/foo.py`` <-> ``tests/test_foo.py``,
    ``App/Services/Order.php`` <-> ``tests/Unit/OrderTest.php``).
    """
    if is_test_file(file_path) or is_non_executable_file(file_path):
        return []

    normalized_target = file_path.replace("\\", "/").strip().lower()
    base_name = os.path.basename(normalized_target)
    stem, ext = os.path.splitext(base_name)
    if not stem:
        return []

    # Potential test file stems for this production file stem
    candidate_stems = {
        f"test_{stem}",
        f"{stem}_test",
        f"{stem}test",
        f"{stem}.test",
        f"{stem}.spec",
    }

    matched: list[str] = []

    for other_file in all_changed_files:
        norm_other = other_file.replace("\\", "/").strip().lower()
        if norm_other == normalized_target:
            continue
        if not is_test_file(norm_other):
            continue

        other_base = os.path.basename(norm_other)
        other_stem, _ = os.path.splitext(other_base)

        # Handle double extensions like .test.js or .spec.ts
        if other_stem.endswith((".test", ".spec")):
            other_stem_core, _ = os.path.splitext(other_stem)
        else:
            other_stem_core = other_stem

        if (
            other_stem in candidate_stems
            or other_stem_core == stem
            or other_stem.startswith(f"test_{stem}")
            or other_stem.endswith(f"{stem}_test")
            or other_stem.endswith(f"{stem}test")
        ):
            matched.append(other_file)

    return matched


def requires_tests(file_path: str) -> bool:
    """Whether a modified file is executable production code that expects test coverage."""
    if is_test_file(file_path):
        return False
    if is_non_executable_file(file_path):
        return False
    return True

