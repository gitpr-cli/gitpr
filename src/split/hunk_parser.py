"""Unified diff to units, and units back to a patch. Pure text, never git.

The two directions are deliberately in one module: ``build_patch`` is only
correct because it knows exactly what ``parse_units`` put in a ``Hunk``, and
splitting them across files would let the two drift until a patch stops
applying.

The file-level split is not re-implemented — ``split_patch_sections`` from
``src/diff_parser.py`` already does it, already handles both header shapes, and
is already the project's one way of reading a diff apart. What it does not do
is go below the file, which is the whole job here.

Two rules carry the weight:

* A hunk ends when its **declared counts are exhausted**, not at the next
  ``@@``. Inside a hunk, a ``--- `` or ``+++ `` at column 0 is
  indistinguishable from a file header — a removed line that happens to read
  ``--- foo`` looks exactly like one — while a context line always carries its
  leading space. Counting is therefore the only boundary rule that is right.
* A section that fails to parse degrades **whole** to one ``OpaqueSection``.
  Never a partial hunk list: half of a malformed section is not something to
  hand to ``git apply``, and a patch that applies *most* of a file is worse
  than one that refuses the file.
"""
import hashlib
import re

from src.diff_parser import split_patch_sections
from src.split.split_plan import Hunk, OpaqueSection

#: Both sides of a hunk header, counts optional.
#:
#: Deliberately its own regex rather than a widening of ``_HUNK_HEADER_RE`` in
#: ``diff_parser.py``: that one captures only the new side, and its capture
#: groups are consumed by ``summarize_patch`` and ``parse_added_lines``, so
#: adding groups there would break two callers to serve a third.
_FULL_HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)

#: What a section with no hunks actually is. Checked in this order: a binary
#: section can also carry mode lines, and a rename reports a mode change too.
_OPAQUE_MARKERS = (
    ("binary", ("GIT binary patch", "Binary files ")),
    ("rename", ("rename from ", "copy from ")),
    ("mode", ("old mode ", "new mode ")),
    ("empty", ("new file mode ", "deleted file mode ")),
)


def make_unit_id(ordinal, file_path, header, body):
    """``0007-1a2b3c4d`` — a unit's identity, stable across runs.

    Both halves are load-bearing. The ordinal prefix depends only on traversal
    order, which the diff text fixes, so the same working tree always yields
    the same ids — re-running ``--dry-run`` prints what it printed before. The
    hash suffix buys two things the prefix cannot. It keeps ids apart across
    re-parses of a tree whose lines moved, where the ordinals of unrelated
    hunks shift; and it is the only thing separating two files changed
    identically — a vendored copy and its original, say — which produce the
    same hunk header and the same hunk body, and differ in nothing but their
    path. Two hunks of one file can never collide: their headers carry
    different line numbers.
    """
    digest = hashlib.md5(f"{file_path}{header}{body}".encode("utf-8")).hexdigest()
    return f"{ordinal:04d}-{digest[:8]}"


def parse_units(diff_text):
    """Split *diff_text* into ``Hunk`` and ``OpaqueSection`` units, in order.

    One pass, units in the order they appear, so ``ordinal`` is simply the
    index and ``build_patch`` can restore the original arrangement. Sections
    that carry no hunks — binaries, pure renames, mode-only changes, empty file
    creations — become a single ``OpaqueSection`` each. So does any section
    whose hunk counts do not add up.
    """
    units = []
    for section in split_patch_sections(diff_text):
        lines = section.text.split("\n")
        while lines and lines[-1] == "":
            lines.pop()
        if not lines:
            continue

        header_end = _find_first_hunk(lines)
        if header_end is None:
            units.append(
                _opaque(section.path, lines, len(units), _classify_opaque(lines))
            )
            continue

        hunks = _parse_hunks(lines, header_end, section.path, len(units))
        if hunks is None:
            units.append(_opaque(section.path, lines, len(units), "malformed"))
            continue
        units.extend(hunks)
    return units


def build_patch(units):
    """Rebuild a unified diff holding exactly *units* — no more, no less.

    Sections come out in the order their units first appeared, which is the
    original diff's order, so a patch is readable and its hunks stay in
    ascending line order. Within a file the hunks are sorted by ``ordinal`` and
    never by the caller's order: a patch whose hunks skip backwards applies its
    later hunks at the offsets the earlier ones shifted, silently corrupting
    the file.

    A ``Hunk``'s ``file_header`` is emitted once per file, with the ``index``
    line dropped. That line names the blob the patch expects to find, and by
    the time a second group is staged the index has legitimately moved past it
    — keeping it makes git refuse a patch whose content matches perfectly.
    Opaque sections are copied through verbatim, ``index`` line and all,
    because a ``GIT binary patch`` needs it to name its blobs.
    """
    ordered = []
    for unit in units:
        ordered.append((unit.ordinal, unit))

    hunk_files = {}
    opaque = []
    for _, unit in ordered:
        if isinstance(unit, OpaqueSection):
            opaque.append((unit.ordinal, unit.text))
            continue
        entry = hunk_files.setdefault(unit.file_path, {"header": None, "hunks": []})
        if entry["header"] is None:
            entry["header"] = _normalize_header(unit.file_header)
        entry["hunks"].append(unit)

    sections = []
    for path, entry in hunk_files.items():
        hunks = sorted(entry["hunks"], key=lambda hunk: hunk.ordinal)
        body = [entry["header"]] + [hunk.content for hunk in hunks]
        sections.append((min(hunk.ordinal for hunk in hunks), "\n".join(body)))
    sections.extend(opaque)
    sections.sort(key=lambda pair: pair[0])

    if not sections:
        return ""
    return "\n".join(text for _, text in sections) + "\n"


def _normalize_header(header):
    """*header* without its ``index`` line — see ``build_patch``."""
    kept = [line for line in header.split("\n") if not line.startswith("index ")]
    return "\n".join(kept)


def _find_first_hunk(lines):
    """Index of the first well-formed hunk header, or None if there is none."""
    for index, line in enumerate(lines):
        if _FULL_HUNK_RE.match(line):
            return index
    return None


def _parse_hunks(lines, start, path, first_ordinal):
    """Every hunk from *start* to the end of *lines*, or None if malformed.

    Returning None rather than raising is what lets the caller degrade the
    whole section: a count mismatch anywhere means the boundaries after it are
    guesswork, so no hunk from this section can be trusted.
    """
    file_header = "\n".join(lines[:start])
    hunks = []
    index = start

    while index < len(lines):
        match = _FULL_HUNK_RE.match(lines[index])
        if match is None:
            return None

        old_count = _count(match.group("old_count"))
        new_count = _count(match.group("new_count"))
        old_remaining, new_remaining = old_count, new_count
        header_line = lines[index]
        body = [header_line]
        index += 1

        while old_remaining > 0 or new_remaining > 0:
            if index >= len(lines):
                return None
            line = lines[index]
            if line.startswith("\\"):
                # '\ No newline at end of file' annotates the line before it and
                # belongs to neither side's count.
                body.append(line)
                index += 1
                continue
            if line.startswith("+"):
                new_remaining -= 1
            elif line.startswith("-"):
                old_remaining -= 1
            elif line.startswith(" "):
                old_remaining -= 1
                new_remaining -= 1
            else:
                # An empty line, a stray '@@', anything else: the counts above
                # cannot be reconciled with what follows.
                return None
            body.append(line)
            index += 1

        # A trailing '\ No newline' after the final counted line belongs here.
        while index < len(lines) and lines[index].startswith("\\"):
            body.append(lines[index])
            index += 1

        ordinal = first_ordinal + len(hunks)
        body_text = "\n".join(body[1:])
        hunks.append(
            Hunk(
                file_path=path,
                hunk_header=header_line,
                content="\n".join(body),
                line_start_old=int(match.group("old_start")),
                line_start_new=int(match.group("new_start")),
                id=make_unit_id(ordinal, path, header_line, body_text),
                file_header=file_header,
                old_count=old_count,
                new_count=new_count,
                ordinal=ordinal,
            )
        )

    return hunks


def _count(value):
    """A hunk header count: absent means 1, an explicit ``0`` means 0."""
    return 1 if value is None else int(value)


def _opaque(path, lines, ordinal, reason):
    """Wrap a hunk-less or unparseable section as one whole unit."""
    text = "\n".join(lines)
    return OpaqueSection(
        file_path=path,
        text=text,
        id=make_unit_id(ordinal, path, "", text),
        ordinal=ordinal,
        reason=reason,
    )


def _classify_opaque(lines):
    """Why a section carries no hunks — the most specific marker that matches."""
    for reason, markers in _OPAQUE_MARKERS:
        for line in lines:
            if line.startswith(markers):
                return reason
    return "malformed"
