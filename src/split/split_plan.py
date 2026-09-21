"""The data contract of ``gitpr split`` — the shapes every other module shares.

Nothing here touches the filesystem, the network or git: these are the values
that travel between the parser, the AI grouping call, the commit-message
pipeline and the applier.

The unit of a split is a :class:`Hunk`, not a file: the whole point of the
command is that one file's changes may belong to two different concerns. But
not every part of a diff *has* hunks — a binary blob, a pure rename, a mode
change — and those still have to reach a commit. They travel as
:class:`OpaqueSection`, and the two together make up :data:`ChangeUnit`.
"""
from dataclasses import dataclass, field
from typing import Optional


class SplitError(Exception):
    """The pipeline cannot run — no repository, no changes, no AI key.

    Raised for the situations where carrying on would produce a *meaningless*
    answer rather than a failure: with a clean working tree there is nothing to
    split, and without a provider there is nothing to group by. It is always
    raised before any mutation, so catching it means the repository is exactly
    as it was.
    """


@dataclass(frozen=True)
class Hunk:
    """One ``@@`` block of one file, with everything needed to reapply it alone.

    ``content`` is the hunk body verbatim — header line included, ``+``/``-``/
    space prefixes intact, ``\\ No newline at end of file`` markers included —
    because that is exactly what ``git apply`` expects to read back.

    ``file_header`` is the whole ``diff --git`` block that precedes the hunks
    (index line, mode lines, ``---``/``+++``). It is stored rather than
    reconstructed from ``file_path`` because it is *not* reconstructible:
    ``new file mode``, ``deleted file mode``, ``old mode``/``new mode`` and
    git's quoted form for non-ASCII or spaced paths are all unrecoverable from
    the path alone, and synthesizing them produces a patch git refuses.

    ``old_count``/``new_count`` are the counts from the hunk header, and they
    are what makes hunk boundaries decidable: a hunk ends when its declared
    lines are consumed, never at the next ``@@``, because ``--- `` and ``+++ ``
    at column 0 inside a hunk are indistinguishable from file headers. They
    count *context and changed lines together*, so they are not the number of
    ``+``/``-`` lines — that count is read off ``content`` where it is needed.

    ``ordinal`` is the position in the original traversal, 0-based. It decides
    the order hunks are re-emitted in — ``build_patch`` sorts by it, since a
    patch whose hunks are out of ascending order applies at the wrong offsets.
    """
    file_path: str
    hunk_header: str
    content: str
    line_start_old: int
    line_start_new: int
    id: str
    file_header: str
    old_count: int
    new_count: int
    ordinal: int


@dataclass(frozen=True)
class OpaqueSection:
    """A section of the diff that carries no hunks, kept whole and verbatim.

    Binaries (``GIT binary patch``), pure renames, mode-only changes and any
    section the parser could not make sense of all land here. They cannot be
    split — there is nothing finer to split them into — so they become atomic
    single-unit groups and never reach the AI: no grouping decision is being
    asked of it, and a unit it cannot express an opinion about is a unit it
    would invent an id for.

    ``text`` is the whole section verbatim, its ``diff --git`` header included,
    so ``build_patch`` emits it and nothing else — an opaque section is copied
    through, never reassembled. That is why it carries no separate
    ``file_header``: there is no header to re-emit apart from the text.

    ``reason`` is a short machine-readable code (``binary``, ``rename``,
    ``mode``, ``empty``, ``malformed``), not a sentence: the display layer
    translates it.
    """
    file_path: str
    text: str
    id: str
    ordinal: int
    reason: str


#: Everything a group can hold. A PEP 604 union and not a base class: the two
#: members share no behaviour — nothing calls a method on a ``ChangeUnit`` and
#: expects both to answer — so an ABC would buy a shared type at the cost of an
#: inheritance relation that says nothing true. Callers dispatch with
#: ``isinstance`` where the distinction matters, which is only in ``build_patch``.
ChangeUnit = Hunk | OpaqueSection


@dataclass
class HunkGroup:
    """One proposed atomic commit: the units it stages, and why they belong.

    ``group_id`` is ``G1``, ``G2``, ... assigned by gitpr in the order the
    model returned the groups, never by the model itself — the same diff and
    the same response therefore always yield the same ids, which is what makes
    a group addressable in the printed plan.

    ``units`` is a list and the dataclass is not frozen: forcing a conflicting
    group to absorb whole files rewrites this list in place, and
    ``generated_commit_message`` is filled in after the group exists.
    """
    group_id: str
    intent_label: str
    justification: str
    units: list[ChangeUnit]
    generated_commit_message: Optional[str] = None

    @property
    def file_paths(self) -> tuple[str, ...]:
        """The distinct files this group touches, sorted.

        Sorted because it is compared as a set — against the staging result,
        to prove no other file leaked into the index.
        """
        return tuple(sorted({unit.file_path for unit in self.units}))

    @property
    def has_hunks(self) -> bool:
        """True when at least one unit is a real hunk rather than an opaque one."""
        return any(isinstance(unit, Hunk) for unit in self.units)


@dataclass
class SplitPlan:
    """The whole proposal: the commits to make, in order, and what stays behind.

    ``ungrouped_units`` is the explicit remainder — units the model did not
    classify, units whose group had to be abandoned, units trimmed away for
    exceeding the budget. They are never dropped silently and they are never
    committed: at the end of an ``--apply`` they are still uncommitted in the
    working tree, for the user to deal with.
    """
    groups: list[HunkGroup]
    ungrouped_units: list[ChangeUnit]
    total_units: int
    warnings: list[str] = field(default_factory=list)

    @property
    def total_groups(self) -> int:
        """How many commits this plan would create."""
        return len(self.groups)
