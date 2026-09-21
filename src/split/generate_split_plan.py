"""Turning a diff into a plan — the read-only half of ``gitpr split``.

The whole module is a pipeline of refusals. A section the parser cannot make
sense of becomes opaque rather than a partial hunk list; an opaque section gets
its own commit rather than reaching a model that would invent an id for it; a
group whose files cannot be staged whole is widened until they can, and if even
that fails its units go back to the ungrouped list rather than being applied
half-way. Nothing here writes: no index, no working tree, no file. The plan is
a proposal, and proposing is what it does.

What it *does* touch is the AI: one call to group, and one call per group for
its commit message. Both are cached like every other call in the project, so a
second ``--dry-run`` on an unchanged tree prints the plan it printed before.

The order of the commits is the model's order for the groups it proposed, with
the opaque sections after them in traversal order. There is no better rule
available: opaque sections carry no intent to order by, and no ordering of
these commits rescues the intermediate states — a rename and the code that
references its new path are one change split across two commits in either
order. The plan is printed before anything runs, which is where an ordering
worth arguing about gets argued with.
"""
from src.config import get_ai_provider
from src.core import generate_pr_content
from src.i18n import __
from src.infrastructure.git.selective_stager import check_units_at_head
from src.split.hunk_grouper import group_units
from src.split.hunk_parser import build_patch, parse_units
from src.split.split_plan import Hunk, HunkGroup, OpaqueSection, SplitError, SplitPlan


def generate_split_plan(
    diff_text,
    repo_path=None,
    untracked=(),
    max_groups=5,
    max_units=50,
    provider=None,
    quiet=False,
):
    """The plan for *diff_text*: ``SplitPlan``, or ``SplitError`` for no work.

    *untracked* is a list of paths git does not track. They are out of scope —
    ``git diff HEAD`` does not describe them, so they have no units to group —
    but they are named in the warnings, because "nothing to do here" and "there
    was something here and I skipped it" must never look alike. The caller
    passes them rather than this module reading them, so the use case stays a
    function of its arguments.

    *repo_path* is where the conflict pre-validation runs. It defaults to the
    working directory, which is what the CLI wants.
    """
    units = parse_units(diff_text or "")
    if not units:
        raise SplitError(
            __("⚠️ No changes to split. Make some changes before running the command.")
        )

    # Resolved once, here: the grouping call and every commit-message call must
    # answer from the same provider, and a None reaching either would be read as
    # "no provider configured" rather than "the caller did not name one".
    provider = provider or get_ai_provider()

    warnings = []
    if untracked:
        warnings.append(
            __(
                "⚠️ {count} untracked file(s) are out of scope and were not split: {paths}",
                count=len(untracked),
                paths=", ".join(untracked),
            )
        )

    hunks = [unit for unit in units if isinstance(unit, Hunk)]
    opaque = [unit for unit in units if isinstance(unit, OpaqueSection)]

    groups, ungrouped, grouping_warnings = group_units(
        hunks,
        max_groups=max_groups,
        max_units=max_units,
        provider=provider,
        quiet=quiet,
    )
    warnings.extend(grouping_warnings)

    # An opaque section is indivisible, so it is a commit by construction — the
    # grouping call is never asked about it and the max_groups cap does not bind
    # it: leaving an unstageable binary out of the plan would not make the plan
    # smaller, only wrong about what is in the working tree.
    groups.extend(_opaque_groups(opaque))
    _renumber(groups)

    groups, ungrouped, conflict_warnings = _resolve_conflicts(
        groups, ungrouped, repo_path
    )
    warnings.extend(conflict_warnings)

    for group in groups:
        group.generated_commit_message = _commit_message(group, provider)

    return SplitPlan(
        groups=groups,
        ungrouped_units=ungrouped,
        total_units=len(units),
        warnings=warnings,
    )


def _opaque_groups(opaque):
    """One single-unit group per opaque section, in traversal order.

    The intent label is the section's own reason — ``binary``, ``rename``,
    ``mode``, ``empty``, ``malformed`` — and not a sentence: it is a code the
    display layer translates, so the same plan reads correctly in every
    language.
    """
    return [
        HunkGroup(
            group_id="",
            intent_label=unit.reason,
            justification=__("This section cannot be split further."),
            units=[unit],
        )
        for unit in opaque
    ]


def _renumber(groups):
    """Give *groups* ``G1..Gn`` in their final order, in place.

    The grouping call numbers the groups it proposed, but the opaque sections
    join afterwards, so the ids are assigned once the list is complete — which
    is what makes a group addressable in the printed plan.
    """
    for index, group in enumerate(groups, start=1):
        group.group_id = f"G{index}"


def _resolve_conflicts(groups, ungrouped, repo_path):
    """Widen or abandon the groups that cannot be staged. Returns the survivors.

    Two passes, and neither loops.

    1. A group refused by ``--cached --check`` absorbs **every unit of every
       file it touches**, from every group and from the ungrouped list. That is
       the fix for the realistic conflict — two hunks of one file that overlap,
       which a grouping cannot keep apart without also keeping the file's
       changes in one commit. A group emptied by the merge disappears.
    2. Whatever still cannot be staged is not committed at all: its units join
       the ungrouped list with a warning. A CRLF file and a binary unit reach
       here, and they reach it *whole* — never half-applied.

    Abandoned groups are why the caller regenerates commit messages afterwards:
    a message written for two hunks is a lie about a commit holding nine.
    """
    warnings = []

    for group in list(groups):
        ok, _ = check_units_at_head(group.units, repo_path)
        if not ok:
            ungrouped = _absorb_whole_files(group, groups, ungrouped)

    survivors = []
    for group in groups:
        ok, error = check_units_at_head(group.units, repo_path)
        if ok:
            survivors.append(group)
            continue
        ungrouped = ungrouped + list(group.units)
        warnings.append(
            __(
                "⚠️ Group {group_id} could not be staged and was left ungrouped: {error}",
                group_id=group.group_id,
                error=error,
            )
        )

    return survivors, ungrouped, warnings


def _absorb_whole_files(group, groups, ungrouped):
    """Move every unit of *group*'s files into *group*. Returns the remainder.

    *group* is mutated, *groups* has its emptied members dropped in place. The
    units absorbed keep ascending ordinal order, so the merged patch is built
    in the order the file's hunks appear in it — ``build_patch`` sorts by
    ordinal regardless, but a plan read by a human should not be reshuffled
    either.
    """
    files = set(group.file_paths)
    merged = list(group.units)

    for other in groups:
        if other is group:
            continue
        kept = [unit for unit in other.units if unit.file_path not in files]
        merged.extend(unit for unit in other.units if unit.file_path in files)
        other.units = kept

    merged.extend(unit for unit in ungrouped if unit.file_path in files)
    remainder = [unit for unit in ungrouped if unit.file_path not in files]

    group.units = sorted(merged, key=lambda unit: unit.ordinal)
    groups[:] = [other for other in groups if other is group or other.units]
    return remainder


def _commit_message(group, provider):
    """The message for *group*, from that group's patch alone.

    ``generate_pr_content`` is the same function the default commit flow uses,
    so the ``.gitpr.commit.md`` skill, the MD5 prompt cache and the map-reduce
    path for oversized patches are all inherited rather than duplicated. It
    receives the rebuilt patch and never the original diff: a message written
    from the whole diff would describe changes the commit does not contain.
    """
    result = generate_pr_content(
        "commit", "commit", build_patch(group.units), provider=provider
    )
    if not result:
        return None
    return result.get("commit_message")
