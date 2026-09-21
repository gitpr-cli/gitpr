"""Staging a subset of a file's changes — the part of split that writes.

Everything else in ``gitpr split`` reads. This module is the only place where a
diff reaches the index, and the index is the user's real repository, so the
rules here are strict on purpose:

* The patch is always rebuilt from units by ``build_patch``, never sliced out
  of the original diff text. A slice carries offsets that were correct in the
  whole-file diff and are wrong in a patch holding three of its nine hunks.
* ``--check`` runs first, every time. It costs one git call and it is the only
  thing standing between a bad patch and a corrupted index. Before the plan is
  shown the same check runs against a HEAD index built in a temporary file, so
  the plan is validated against the index it will actually meet rather than
  against whatever the user has staged.
* The apply goes through ``patch_applier``, never through ``git apply``
  directly: feeding the patch as bytes on stdin is the defence against
  Windows's text-mode newline translation, which would turn every ``\\n`` into
  ``\\r\\n`` and make git reject the whole patch — silently, and only there.

What this module will not do is decide what to do when a patch is refused. It
raises :class:`HunkConflictError` and lets the caller merge the offending units
into a wider group or give up on them; the recovery is a product decision, not
a staging one.
"""
import contextlib
import os
import tempfile

from src.infrastructure.git.patch_applier import (
    apply_patch_cached,
    check_patch_cached,
    run_git,
)
from src.split.hunk_parser import build_patch


class HunkConflictError(Exception):
    """These units cannot be staged together, or cannot be staged at all.

    Carries the units it was raised for, so the caller can widen the group
    around exactly them instead of re-deriving which ones were in flight.
    """

    def __init__(self, units, error):
        super().__init__(error)
        self.units = list(units)
        self.error = error


def check_units(units, repo_path):
    """Would *units* stage cleanly? Returns ``(ok, error)``, writes nothing.

    The cheap question, asked before anything is mutated: the caller uses it to
    validate a whole plan before the first commit exists, so a plan that cannot
    be applied is rejected while there is still nothing to undo.
    """
    if not units:
        return True, ""
    return check_patch_cached(build_patch(units), cwd=repo_path)


def check_units_at_head(units, repo_path):
    """Would *units* stage cleanly against a **clean** index? ``(ok, error)``.

    The question a plan needs answered before it is shown, and one the real
    index cannot answer: split captures its diff before it unstages, so the
    index the patch will actually meet — HEAD, and nothing else — does not exist
    yet. Asking the current index instead would report a conflict for every
    group that touches a file the user happens to have staged, which is a
    conflict with work that is about to be unstaged anyway.

    So :func:`_index_at_head` builds that index in a temporary file and the
    question is asked of that. The user's index is never read, written or moved.
    """
    if not units:
        return True, ""
    with _index_at_head(repo_path) as env:
        if env is None:
            # No readable HEAD means no clean index to check against. Reporting
            # a conflict for every group would be a worse lie than reporting
            # none: `stage_hunks` re-checks against the real index before every
            # apply, so nothing is applied unchecked.
            return True, ""
        return check_patch_cached(build_patch(units), cwd=repo_path, env=env)


@contextlib.contextmanager
def _index_at_head(repo_path):
    """Yield an environment whose index holds HEAD, or ``None`` if it cannot.

    ``git apply --cached`` reads its preimage from the index named by
    ``GIT_INDEX_FILE``, so an index populated by ``read-tree HEAD`` is HEAD as
    far as the check is concerned — and it is a file git creates, not the user's.

    The temporary file is unlinked before ``read-tree`` runs: git creates the
    index itself and an existing empty file is not a valid index.
    """
    handle, path = tempfile.mkstemp(prefix="gitpr-split-index-", suffix=".tmp")
    os.close(handle)
    os.unlink(path)
    env = dict(os.environ, GIT_INDEX_FILE=path)
    try:
        result = run_git(["read-tree", "HEAD"], cwd=repo_path, env=env)
        yield env if result.returncode == 0 else None
    finally:
        try:
            os.unlink(path)
        except OSError:
            # git may have removed it, or never created it. Neither is a problem.
            pass


def stage_hunks(units, repo_path):
    """Stage exactly *units* into the index, leaving the working tree alone.

    The files on disk keep every change they had, staged or not — this touches
    the index only. Nothing outside *units* reaches the index, which is what
    makes a group a group.

    Raises :class:`HunkConflictError` if git refuses, either on the check or on
    the apply itself. The second can only fail for a reason the first could not
    see (a lock, a permission), and it is reported the same way because the
    caller's response is the same.
    """
    if not units:
        raise ValueError("stage_hunks() needs at least one unit")

    patch = build_patch(units)

    applies, error = check_patch_cached(patch, cwd=repo_path)
    if not applies:
        raise HunkConflictError(units, error)

    staged, error = apply_patch_cached(patch, cwd=repo_path)
    if not staged:
        raise HunkConflictError(units, error)


def unstage_all(repo_path):
    """Empty the index back to HEAD, leaving the working tree untouched.

    The recovery for a staging failure: whatever reached the index is taken
    back out, and every change is once again uncommitted, which is the state
    the user was in before ``--apply``.
    """
    return run_git(["reset", "--mixed", "HEAD"], cwd=repo_path)


def index_is_clean(repo_path):
    """True when nothing is staged — the index matches HEAD.

    Checked before staging a group and again after committing it. A group that
    leaked past its own commit would otherwise be staged on top of the next
    one, and the leak would only surface as a commit containing somebody else's
    work.
    """
    result = run_git(["diff", "--cached", "--quiet"], cwd=repo_path)
    return result.returncode == 0


def staged_paths(repo_path):
    """The new-side paths with staged changes, as a tuple.

    Rename detection is on, so a rename reports its new path once rather than a
    deletion and an addition — which is the same shape the plan's groups carry.
    """
    result = run_git(["diff", "--cached", "--name-only", "-M"], cwd=repo_path)
    if result.returncode != 0:
        return ()
    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip())


def staged_numstat(repo_path):
    """``{path: (added, removed)}`` for everything staged.

    Line counts, not hunk headers. A header's numbers describe the region it
    covers — context included — and they shift when a neighbouring commit moves
    the surrounding lines, so a header-based check would report a false alarm
    on a plan that is perfectly correct. The count of ``+`` and ``-`` lines is
    invariant under exactly that.
    """
    result = run_git(["diff", "--cached", "--numstat", "-M"], cwd=repo_path)
    if result.returncode != 0:
        return {}

    counts = {}
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        if added == "-" or removed == "-":
            # Binary: git reports '-' instead of counts. Presence is the only
            # thing there is to compare, so record it as a marker.
            counts[path] = None
            continue
        counts[path] = (int(added), int(removed))
    return counts
