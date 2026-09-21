"""Executing a plan — the only split module that mutates the repository.

Everything before this is reversible. Here the index is written to, commits are
created, and there is no undo built in: the result is ordinary commits, and
``git reset`` is the tool for them, exactly as it is for any other commit the
user made. What this module owes instead is that it *stops* well — that the
index is never left holding somebody else's work, and that when a run ends
early the report says which groups were committed and which were not, rather
than leaving the user to reconstruct it from ``git status``.

The working tree is never written to. Every file on disk keeps every change it
had; at the end of a successful run ``git status`` is clean and the commits
hold the work. That is the guarantee the whole command rests on, and the reason
every group's patch is applied with ``--cached``.

The unstage at the top is not housekeeping — it is what makes the plan true. The
diff was captured against HEAD while the index still held whatever the user had
staged, because a staged new file appears in ``git diff HEAD`` *only* because
the index tracks it. Every hunk therefore carries a preimage taken from HEAD, and
resetting the index to HEAD is what makes those preimages apply. The permission
to discard that staging is asked once, by the CLI, before this runs.

Two checks run around every group, and neither is ceremony:

* ``index_is_clean`` *before* staging. The index is at HEAD at the top of every
  group either because the previous group committed or because the unstage
  emptied it. A group that leaked past its own commit would otherwise be staged
  on top of the next one, and the leak would surface much later, as a commit
  holding work nobody meant to put there.
* A verification *after* staging, comparing what reached the index against what
  the group was supposed to put there. ``stage_hunks`` being correct is an
  argument about the code; this is evidence about the repository.
"""
from dataclasses import dataclass, field

from src.i18n import __
from src.infrastructure.git.patch_applier import current_head, run_git
from src.infrastructure.git.selective_stager import (
    HunkConflictError,
    index_is_clean,
    stage_hunks,
    staged_numstat,
    staged_paths,
    unstage_all,
)
from src.split.split_plan import ChangeUnit, Hunk, SplitError, SplitPlan


@dataclass
class ApplySplitResult:
    """What a run did, in enough detail to report it without guessing.

    ``commits`` pairs each group id with the commit it produced, so the report
    can name a commit by its group — the ids in the printed plan and the hashes
    in the report are the same objects, which is what makes a run auditable
    after the fact.

    ``stopped_at`` is the group id the run gave up on, or "" if it finished.
    ``error`` is git's own words about why. Both are reported *verbatim*: a run
    that fails at group 3 of 5 must not leave the user to work out which of
    their changes are now committed.

    ``staged_but_not_committed`` distinguishes the two ways a run stops. A
    staging failure unstages and leaves the index clean; a commit failure leaves
    the group staged and correct, for the user to commit with their own message.
    Reporting them identically would hide which state the index is in.
    """

    commits: list[tuple[str, str]] = field(default_factory=list)
    uncommitted_units: list[ChangeUnit] = field(default_factory=list)
    staged_but_not_committed: bool = False
    stopped_at: str = ""
    error: str = ""

    @property
    def completed(self) -> bool:
        """True when every group in the plan became a commit."""
        return not self.stopped_at

    @property
    def total_commits(self) -> int:
        return len(self.commits)

    @property
    def committed_group_ids(self) -> list[str]:
        return [group_id for group_id, _ in self.commits]


def apply_split_plan(plan: SplitPlan, repo_path=None):
    """Create one commit per group, in the plan's order.

    Raises ``SplitError`` for the states in which the plan cannot be applied at
    all — no groups, no HEAD. Both are checked before the first write, so
    raising means nothing was touched.

    A failure *during* the sequence does not raise: it stops and comes back as
    an :class:`ApplySplitResult` carrying ``stopped_at`` and ``error``. The
    distinction matters, because by then commits exist and unwinding the stack
    would lose the only record of them.
    """
    if not plan.groups:
        raise SplitError(__("⚠️ There is nothing to apply: the plan has no groups."))

    if repo_path is None:
        repo_path = "."

    if current_head(repo_path) is None:
        raise SplitError(__("⚠️ This repository has no commits to build on."))

    result = ApplySplitResult()
    unstage_all(repo_path)

    for group in plan.groups:
        if not index_is_clean(repo_path):
            # Unreachable unless a group leaked past its own commit. Reported
            # rather than cleared silently, because it means the assumption the
            # whole loop runs on has broken.
            result.stopped_at = group.group_id
            result.error = __("unexpected staged changes before this group")
            unstage_all(repo_path)
            break

        try:
            stage_hunks(group.units, repo_path)
        except HunkConflictError as exc:
            # The plan was pre-validated, so this is the rare case that check
            # could not see. Nothing of this group stays behind.
            result.stopped_at = group.group_id
            result.error = str(exc)
            unstage_all(repo_path)
            break

        mismatch = _verification_failure(group, repo_path)
        if mismatch:
            result.stopped_at = group.group_id
            result.error = mismatch
            unstage_all(repo_path)
            break

        committed, output = _commit(group, repo_path)
        if not committed:
            # Deliberately *not* unstaged: the group is staged and correct, and
            # the user can retry the commit with their own message. Unstaging
            # would discard the only in-flight state and leave them to work out
            # which units were in it.
            result.stopped_at = group.group_id
            result.error = output
            result.staged_but_not_committed = True
            break

        result.commits.append((group.group_id, current_head(repo_path)))

    committed_ids = set(result.committed_group_ids)
    result.uncommitted_units = [
        unit
        for group in plan.groups
        if group.group_id not in committed_ids
        for unit in group.units
    ] + list(plan.ungrouped_units)

    return result


def _verification_failure(group, repo_path):
    """Why the index does not hold exactly *group*, or "" when it does.

    Two comparisons, both against git's own report of the index rather than
    against the group's own data:

    * The path set from ``--name-only -M`` must equal the group's file set. A
      file in the index that no group asked for means something leaked.
    * The per-file ``(added, removed)`` from ``--numstat`` must equal the counts
      read off the units' ``+`` and ``-`` lines. Numstat and not the hunk
      headers: a header counts the region it covers, context included, and
      those numbers shift when a neighbouring commit moves the surrounding
      lines, so a header-based check would cry wolf on a perfectly correct plan.
    """
    staged = staged_paths(repo_path)
    expected = group.file_paths
    if staged != expected:
        return __(
            "the index holds {staged} but the group asked for {expected}",
            staged=", ".join(staged) or "nothing",
            expected=", ".join(expected),
        )

    actual = staged_numstat(repo_path)
    for path, counts in _unit_counts(group.units).items():
        if actual.get(path) != counts:
            return __(
                "the index holds {actual} line(s) for {path} but the group asked for {wanted}",
                actual=_format_counts(actual.get(path)),
                path=path,
                wanted=_format_counts(counts),
            )
    return ""


def _unit_counts(units):
    """``{path: (added, removed)}`` summed from the hunks' own diff lines.

    Opaque sections are skipped rather than recorded as zero, because zero is
    not what git reports for them: a mode-only change or a pure rename appears
    in ``--numstat`` as ``0 0``, and a binary as ``-``. Their presence is
    already proven by the path-set comparison, and guessing at their counts
    here would turn a correct plan into a reported failure.

    A line's first character is its side — ``+`` added, ``-`` removed, a space
    context, ``\\`` the "no newline" marker — and the hunk header is skipped by
    slicing it off. Nothing else needs classifying: a ``+++`` line inside a
    hunk is an added line whose text begins with ``++``, and treating it as a
    file header here would undercount it.
    """
    counts = {}
    for unit in units:
        if not isinstance(unit, Hunk):
            continue
        body = unit.content.split("\n")[1:]
        added = sum(1 for line in body if line.startswith("+"))
        removed = sum(1 for line in body if line.startswith("-"))
        previous = counts.get(unit.file_path, (0, 0))
        counts[unit.file_path] = (previous[0] + added, previous[1] + removed)
    return counts


def _format_counts(counts):
    """``(added, removed)`` for a message; ``None`` reads as "not line-counted"."""
    if counts is None:
        return __("no line counts (binary)")
    return f"+{counts[0]}/-{counts[1]}"


def _commit(group, repo_path):
    """Commit the staged group. Returns ``(committed, output)``.

    ``git commit`` through ``run_git`` and not ``core.execute_git_commit``: that
    one takes no ``cwd`` and commits in the process's working directory, so a
    plan applied to a repository other than the current one would silently
    commit the wrong tree. The flags are otherwise the same — no ``--no-verify``,
    so hooks run, which is the point of a pre-commit hook.

    ``git commit -m`` refuses an empty message, so a group whose message could
    not be generated gets a placeholder rather than being left staged with no
    explanation.
    """
    message = group.generated_commit_message or __(
        "chore: split changes ({group_id})", group_id=group.group_id
    )
    result = run_git(["commit", "-m", message], cwd=repo_path)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()
