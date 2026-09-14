"""Deciding how much a patch may be trusted — pure logic, no I/O, no AI.

The classification is deliberately conservative and entirely deterministic: the
same patch summary and the same settings always yield the same verdict, so a
patch that was SAFE in a dry run is still SAFE when ``--apply`` runs.

Three classes, in decreasing order of trust:

* ``SAFE`` — one file, one hunk, few changed lines, outside the sensitive
  paths, and it deletes no line that looks like a call. These are the only
  patches ``--all-safe`` will write.
* ``REVIEW_REQUIRED`` — it applies, but at least one SAFE condition failed.
* ``EXPERIMENTAL`` — it does not apply to this tree, spans several files, or
  the model declared low confidence. ``--all-safe`` never touches these.

The verdict is accompanied by a reason *code*, never a sentence: the display
layer owns the wording so every message goes through the i18n engine.
"""
import fnmatch
import re

from src.fix.patch_provenance import PatchSafety

# Reason codes — the classifier's public vocabulary. Stable strings, so a
# caller can match on them without importing a translation.
REASON_SAFE = "safe"
REASON_APPLY_CHECK_FAILED = "apply_check_failed"
REASON_MULTI_FILE = "multi_file"
REASON_LOW_CONFIDENCE = "low_confidence"
REASON_EXCLUDED_PATH = "excluded_path"
REASON_MULTIPLE_HUNKS = "multiple_hunks"
REASON_TOO_MANY_LINES = "too_many_lines"
REASON_REMOVES_CALL = "removes_call"

# A removed line that still carries a call-like token is never trivial: it is
# the shape of "you deleted something that was being used". The pattern is
# intentionally crude (\w+ followed by an open paren) and errs toward
# REVIEW_REQUIRED — a deleted comment containing "foo()" will trip it too, and
# that is the safe direction to be wrong in.
_CALL_LIKE_RE = re.compile(r"\w+\s*\(")


def classify_patch(
    summary,
    confidence="high",
    applies_cleanly=True,
    max_lines_changed=5,
    excluded_paths=(),
):
    """Return ``(PatchSafety, reason_code)`` for the patch *summary* describes.

    ``applies_cleanly`` is the caller's report of ``git apply --check`` — the
    classifier stays pure, so the check itself happens in ``patch_applier``.
    ``excluded_paths`` are fnmatch patterns of sensitive paths (migrations,
    workflows, docker, ...); a patch touching one applies but is never SAFE.
    """
    if not applies_cleanly:
        return PatchSafety.EXPERIMENTAL, REASON_APPLY_CHECK_FAILED

    if len(summary.files) > 1:
        return PatchSafety.EXPERIMENTAL, REASON_MULTI_FILE

    if str(confidence).strip().lower() == "low":
        return PatchSafety.EXPERIMENTAL, REASON_LOW_CONFIDENCE

    if _touches_excluded_path(summary.files, excluded_paths):
        return PatchSafety.REVIEW_REQUIRED, REASON_EXCLUDED_PATH

    if summary.hunks != 1:
        return PatchSafety.REVIEW_REQUIRED, REASON_MULTIPLE_HUNKS

    if summary.added + summary.removed > max_lines_changed:
        return PatchSafety.REVIEW_REQUIRED, REASON_TOO_MANY_LINES

    if _removes_a_call(summary.removed_lines):
        return PatchSafety.REVIEW_REQUIRED, REASON_REMOVES_CALL

    return PatchSafety.SAFE, REASON_SAFE


def _touches_excluded_path(files, excluded_paths):
    """True when any file matches any of the fnmatch *excluded_paths*.

    Plain ``fnmatch`` is enough because its ``*`` already crosses ``/``, so the
    ``docker/**`` style patterns used in the configuration behave as written —
    ``PurePath.match`` or ``glob`` would need their own ``**`` rules and would
    read the same configuration differently.
    """
    for path in files:
        # git prints './x' when the diff was taken from the repo root; the
        # configured patterns never carry that prefix.
        normalized = path[2:] if path.startswith("./") else path
        for pattern in excluded_paths:
            if pattern and fnmatch.fnmatch(normalized, pattern):
                return True
    return False


def _removes_a_call(removed_lines):
    """True when any removed line looks like a call to something."""
    return any(_CALL_LIKE_RE.search(line) for line in removed_lines)
