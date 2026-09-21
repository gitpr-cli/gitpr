"""Re-export shim — the module moved to ``src/infrastructure/git/patch_applier``.

``git apply`` is not a ``fix`` concern: it is how *any* feature that writes to
git talks to git, and ``gitpr split`` is the second such feature. The module
therefore lives under ``infrastructure``, where both features can reach it.

Unlike ``src/github_api.py`` this shim warns about nothing. That one covers a
public API being retired for users; this one is an internal path that moved,
and the imports below are all first-party. A ``DeprecationWarning`` here would
be noise printed at every ``gitpr fix`` startup.

New code should import from ``src.infrastructure.git.patch_applier`` directly.
"""
from src.infrastructure.git.patch_applier import (
    apply_patch,
    apply_patch_cached,
    check_patch,
    check_patch_cached,
    create_branch,
    current_branch,
    current_head,
    is_git_repository,
    modified_files,
    repo_root,
    reverse_patch,
    run_git,
)

__all__ = [
    "apply_patch",
    "apply_patch_cached",
    "check_patch",
    "check_patch_cached",
    "create_branch",
    "current_branch",
    "current_head",
    "is_git_repository",
    "modified_files",
    "repo_root",
    "reverse_patch",
    "run_git",
]
