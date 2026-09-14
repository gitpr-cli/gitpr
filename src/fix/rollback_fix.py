"""Undoing a patch ``gitpr fix`` applied — the other half of the history file.

Rollback cannot lean on the commit history, because a patch applied by ``gitpr
fix`` is left uncommitted on purpose (the user reviews it, then commits it). The
stored diff is therefore the only description of what to undo, and
``git apply --reverse`` replays it — no commit, no stash, no reset.

The reversal is verified against the file by git itself: if the tree moved on,
the reverse fails and the error is reported. A file is never half-written.
"""
from src.fix.apply_fix import FixError
from src.fix.fix_history import find_entry, mark_rolled_back
from src.fix.patch_applier import current_branch, repo_root, reverse_patch
from src.i18n import __


def rollback_fix(patch_id, root=None):
    """Undo *patch_id* and stamp it as undone. Returns the entry that was undone.

    Refuses in three cases, each with its own reason, because they call for
    three different actions by the user: the patch was never applied (nothing to
    undo), it was already undone (undoing twice is a mistake, not a no-op), and
    it was applied on another branch (the file to restore is not here).
    """
    root = repo_root(cwd=root)
    if not root:
        raise FixError(__("❌ Not inside a git repository."))

    entry = find_entry(patch_id, root)
    if not entry:
        raise FixError(
            __(
                "❌ No applied patch with id '{patch_id}' was recorded here.",
                patch_id=patch_id,
            )
        )

    rolled_back_at = entry.get("rolled_back_at")
    if rolled_back_at:
        raise FixError(
            __(
                "❌ Patch '{patch_id}' was already rolled back at {when}.",
                patch_id=patch_id,
                when=rolled_back_at,
            )
        )

    applied_on = entry.get("branch")
    if applied_on and current_branch(cwd=root) != applied_on:
        raise FixError(
            __(
                "❌ Patch '{patch_id}' was applied on branch '{branch}': switch back to it to undo the patch.",
                patch_id=patch_id,
                branch=applied_on,
            )
        )

    reverted, error = reverse_patch(entry.get("diff") or "", cwd=root)
    if not reverted:
        raise FixError(
            __(
                "❌ Could not undo patch '{patch_id}': {error}",
                patch_id=patch_id,
                error=error,
            )
        )

    mark_rolled_back(patch_id, root)
    return entry
