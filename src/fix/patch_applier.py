"""The project's shared git wrapper — the first one, and only for patches.

Every other module in gitpr shells out to git inline, because every other
module only ever *reads*: ``diff``, ``log``, ``blame``, ``status``. ``gitpr
fix`` is the first feature that writes, so it needs three things nothing else
does — a dry run that only asks whether a patch *would* apply, a real apply,
and the exact reverse of an apply. Those live here.

Nothing in this module decides policy: it never asks for confirmation and never
chooses a branch name. It reports what git said and lets the caller decide.

Failure is a value here, not an exception: ``apply_patch`` returning
``(False, "error: patch does not apply")`` is an ordinary outcome that the
command prints, not something to unwind the stack for.
"""
import os
import subprocess


def run_git(args, cwd=None):
    """Run ``git <args>`` and return the CompletedProcess (non-zero included).

    The encoding contract of the whole project applies: the repository may hold
    non-UTF8 bytes from legacy history, so decoding never raises.
    """
    return subprocess.run(
        ["git"] + list(args),
        cwd=cwd,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_error(result):
    """git's own words about a failure, preferring stderr over stdout."""
    message = (result.stderr or "").strip() or (result.stdout or "").strip()
    return message or f"git exited with status {result.returncode}"


def repo_root(cwd=None):
    """Absolute path of the repository top level, or None outside a repository.

    Every other function in this module is called with this as ``cwd``: a
    unified diff carries paths relative to the top level, so applying it from a
    subdirectory would look for files that are not there.
    """
    result = run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return os.path.abspath(root) if root else None


def is_git_repository(cwd=None):
    """True when *cwd* (or the working directory) sits inside a git repository."""
    return repo_root(cwd) is not None


def _apply(args, diff_text, cwd):
    """Feed *diff_text* to ``git apply`` over stdin and report the outcome.

    The patch travels through stdin rather than a temporary file: nothing is
    written to disk for a dry run, so a failed check leaves no trace at all.

    stdin is fed as bytes, never as text. subprocess opens a text-mode stdin
    with universal-newline *writing*, so on Windows every ``\\n`` in the patch
    would reach git as ``\\r\\n`` — and git would then refuse the whole patch,
    because a hunk whose context lines end in CR does not match an LF file.
    The failure is total and silent, and it happens only on Windows.
    """
    result = subprocess.run(
        ["git", "apply"] + list(args) + ["-"],
        cwd=cwd,
        input=diff_text.encode("utf-8"),
        capture_output=True,
    )
    if result.returncode == 0:
        return True, ""
    return False, _git_error(_Decoded(result))


class _Decoded:
    """A CompletedProcess whose bytes streams read as decoded text.

    ``git apply`` is the one call in the project that needs byte-exact stdin
    and human-readable output at once; this keeps ``_git_error`` working on
    both without a second code path.
    """

    def __init__(self, result):
        self.returncode = result.returncode
        self.stdout = (result.stdout or b"").decode("utf-8", errors="replace")
        self.stderr = (result.stderr or b"").decode("utf-8", errors="replace")


def check_patch(diff_text, cwd=None):
    """Return ``(applies, error)`` for *diff_text* without touching any file."""
    return _apply(["--check"], diff_text, cwd)


def apply_patch(diff_text, cwd=None):
    """Write *diff_text* into the working tree. Returns ``(applied, error)``."""
    return _apply([], diff_text, cwd)


def reverse_patch(diff_text, cwd=None):
    """Undo a previously applied *diff_text*. Returns ``(reverted, error)``."""
    return _apply(["--reverse"], diff_text, cwd)


def current_branch(cwd=None):
    """The checked-out branch name, or None outside a repository.

    A detached HEAD reports ``HEAD`` — which is the truth, and is what makes
    the rollback branch check fail loudly instead of reverting on the wrong
    commit.
    """
    result = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def current_head(cwd=None):
    """The full SHA of HEAD, or None outside a repository."""
    result = run_git(["rev-parse", "HEAD"], cwd=cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def create_branch(name, cwd=None):
    """Create *name* at the current HEAD and switch to it.

    Returns ``(created, error)``; an invalid or already existing name is a
    failure reported by git, with the working tree left as it was.
    """
    result = run_git(["checkout", "-b", name], cwd=cwd)
    if result.returncode == 0:
        return True, ""
    return False, _git_error(result)


def modified_files(cwd=None):
    """Repo-relative paths with uncommitted changes, as a tuple.

    Covers staged, unstaged and untracked entries; for a rename or a copy the
    new path is the one reported, since that is the file the patch will touch.
    A path holding a character git escapes (a tab, a non-ASCII byte under
    core.quotePath) keeps its escape: this feeds a warning, not a decision.
    """
    result = run_git(["status", "--porcelain"], cwd=cwd)
    if result.returncode != 0:
        return ()

    paths = []
    for line in result.stdout.splitlines():
        # 'XY <path>' — the first three columns are the status codes.
        if len(line) < 4:
            continue
        entry = line[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        entry = entry.strip()
        if len(entry) >= 2 and entry.startswith('"') and entry.endswith('"'):
            entry = entry[1:-1]
        if entry:
            paths.append(entry)
    return tuple(paths)
