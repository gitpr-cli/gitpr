"""Pure parser for unified diffs produced by the project's git wrappers.

The PR flows diff with ``git diff -U1 -w -M -B <ancestor> -- <excludes>``
(core.get_git_full_diff); this module maps that text to the new-side line
numbers of the added ('+') lines, per file — the numbers used to blame the
working tree. It never runs git and never re-applies excludes: it only
interprets the diff text it is given.

``summarize_patch()`` reads the same text a second way — as a patch a whole:
which files it touches, how many hunks, how many lines it adds and removes.
That is what the ``gitpr fix`` safety classifier scores, and it accepts the
looser shape an AI returns (no ``diff --git`` line, just ``---``/``+++``).
"""
import re
from dataclasses import dataclass

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

_ESCAPE_CHARS = {
    "n": b"\n",
    "t": b"\t",
    "r": b"\r",
    "\\": b"\\",
    '"': b'"',
}


def _decode_git_path(token):
    """Unquote a path token as git prints it (double quotes + C escapes).

    git quotes paths that contain special characters (spaces, non-ASCII with
    core.quotePath on) with octal escapes of raw bytes, e.g.
    ``"caf\\303\\251.py"`` — each ``\\ooo`` is one UTF-8 byte, so a run is
    decoded as a byte sequence before the final UTF-8 decode. ``\\n``, ``\\t``,
    ``\\r``, ``\\\\`` and ``\\"`` cover the non-octal escapes git emits.
    Unquoted tokens are returned as-is; a broken escape sequence degrades to
    U+FFFD (errors="replace") instead of raising.
    """
    t = token.strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        raw = t[1:-1]
        out = bytearray()
        i = 0
        while i < len(raw):
            char = raw[i]
            if char == "\\" and i + 1 < len(raw):
                nxt = raw[i + 1]
                if nxt in _ESCAPE_CHARS:
                    out.extend(_ESCAPE_CHARS[nxt])
                    i += 2
                    continue
                if nxt in "01234567":
                    j = i + 1
                    while j < len(raw) and j < i + 4 and raw[j] in "01234567":
                        j += 1
                    out.append(int(raw[i + 1 : j], 8))
                    i = j
                    continue
            out.extend(char.encode("utf-8"))
            i += 1
        t = out.decode("utf-8", errors="replace")
    return t


def _header_path(header_line, marker=None):
    """Extract a path token from a diff header line.

    'diff --git a/X b/Y' carries two paths (the b/ side is the interesting
    one); '+++ b/X' / '--- a/X' carry one after their marker. Quoted tokens
    (paths with spaces) are handled by a quote-aware splitter.
    """
    body = header_line
    if header_line.startswith("diff --git "):
        tokens = _split_paths(body[len("diff --git "):])
        token = tokens[1] if len(tokens) > 1 else ""
    else:
        if marker is not None and header_line.startswith(marker):
            body = header_line[len(marker):]
        tokens = _split_paths(body)
        token = tokens[0] if tokens else ""
    return _decode_git_path(token)


def _split_paths(body):
    """Split header path tokens honoring git's double-quoted paths."""
    tokens = []
    current = []
    quoted = False
    for char in body:
        if char == '"':
            quoted = not quoted
            current.append(char)
        elif char.isspace() and not quoted:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def _strip_diff_prefix(path):
    """Remove the 'a/'/'b/' prefix git adds to paths (when present)."""
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def parse_added_lines(diff_text):
    """Return {file_path: [new-side added line numbers]} for a unified diff.

    Handles 'diff --git' headers (with quoted/renamed paths), '+++ b/path'
    vs '+++ /dev/null' (deletion-only), hunk headers '@@ -a,b +c,d @@',
    context/deletion lines, '\\ No newline at end of file', binary markers
    and mode-only changes. Only '+' content lines inside hunks are counted;
    files without added lines are omitted from the result.
    """
    added_by_file = {}
    current_path = None
    in_hunk = False
    new_line = 0

    for raw_line in diff_text.split("\n"):
        line = raw_line.rstrip("\r")

        if line.startswith("diff --git "):
            current_path = None
            in_hunk = False
            continue
        if line.startswith("+++ ") and not in_hunk:
            path = _strip_diff_prefix(_header_path(line, marker="+++ "))
            current_path = None if path == "/dev/null" else path
            in_hunk = False
            continue
        if line.startswith("@@"):
            match = _HUNK_HEADER_RE.match(line)
            if match:
                new_start = int(match.group(1))
                new_count = int(match.group(2) or 0)
                # A 0 start with a positive count still numbers lines from 1.
                new_line = max(1, new_start) if new_count else new_start
                in_hunk = True
            continue

        if current_path is None or not in_hunk:
            continue

        if line.startswith("\\ No newline"):
            continue
        if line.startswith("+"):
            if new_line > 0:
                added_by_file.setdefault(current_path, []).append(new_line)
            new_line += 1
        elif line.startswith("-"):
            pass
        elif line.startswith(" "):
            # Context line: advances both sides.
            new_line += 1
        # Unrecognized lines inside a hunk are ignored (safety).

    for lines in added_by_file.values():
        lines.sort()
    return added_by_file


@dataclass(frozen=True)
class PatchSummary:
    """What a unified diff touches, as the safety classifier needs to see it.

    ``files`` holds each file the patch mentions, in order of appearance, taken
    from the new side — the 'diff --git' line when there is one (a deletion
    keeps its name there, since its '+++ /dev/null' carries none), otherwise the
    '+++ b/path' header. ``hunks`` counts well-formed '@@' headers, and
    ``added``/``removed`` count content lines inside those hunks, so headers and
    the '\\ No newline' marker never count. ``removed_lines`` keeps the text of
    each removed line — what lets a caller spot a deleted function call.
    """
    files: tuple[str, ...]
    hunks: int
    added: int
    removed: int
    removed_lines: tuple[str, ...]


def summarize_patch(diff_text):
    """Return a PatchSummary for *diff_text* (see the dataclass docstring).

    Pure like parse_added_lines: it interprets the text it is given and never
    runs git. Text with no recognizable diff section yields an empty summary
    rather than an error — the caller decides whether that means "no patch".
    """
    files = []
    hunks = 0
    added = 0
    removed = 0
    removed_lines = []
    in_hunk = False

    for raw_line in diff_text.split("\n"):
        line = raw_line.rstrip("\r")

        if line.startswith("diff --git "):
            _remember_file(files, _strip_diff_prefix(_header_path(line)))
            in_hunk = False
            continue
        if line.startswith("+++ ") and not in_hunk:
            path = _strip_diff_prefix(_header_path(line, marker="+++ "))
            if path and path != "/dev/null":
                _remember_file(files, path)
            in_hunk = False
            continue
        if line.startswith("@@"):
            if _HUNK_HEADER_RE.match(line):
                hunks += 1
                in_hunk = True
            continue

        if not in_hunk or line.startswith("\\ No newline"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
            removed_lines.append(line[1:])

    return PatchSummary(
        files=tuple(files),
        hunks=hunks,
        added=added,
        removed=removed,
        removed_lines=tuple(removed_lines),
    )


def _remember_file(files, path):
    """Append *path* to *files* once, preserving appearance order."""
    if path and path not in files:
        files.append(path)


@dataclass(frozen=True)
class PatchSection:
    """One file's slice of a unified diff, with the path it belongs to.

    ``path`` is the new-side path (the b/ side), so a deletion keeps its name —
    its own '+++ /dev/null' header carries none. ``text`` is the section
    verbatim, headers included, so the pieces of a split diff concatenate back
    into something the review engine can still read.
    """
    path: str
    text: str


def split_patch_sections(diff_text):
    """Split *diff_text* into one PatchSection per file, in order.

    The counterpart of summarize_patch for callers that must drop whole files
    (the remote-PR smart-excludes filter): it needs each file's path next to its
    own text, which no other helper here exposes. Accepts both header shapes
    summarize_patch accepts — git's own output ('diff --git' plus a '---'/'+++'
    pair per file) and the looser shape an AI returns (bare '---'/'+++' pairs).
    Text before the first header is dropped, as are sections whose path never
    resolves; a diff with no recognizable file yields [].

    Pure, like its siblings: it interprets the text it is given, never runs git.
    """
    lines = [raw.rstrip("\r") for raw in diff_text.split("\n")]
    sections = []
    start = None
    path = ""
    in_hunk = False

    def flush(end):
        if start is not None and path:
            sections.append(
                PatchSection(path=path, text="\n".join(lines[start:end]))
            )

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("diff --git "):
            flush(i)
            start, in_hunk = i, False
            # The b/ side names the file on the new revision, and unlike the
            # '+++ /dev/null' of a deletion it is always populated.
            path = _strip_diff_prefix(_header_path(line))
            i += 1
            continue

        # A '---' immediately followed by a '+++' is a file header pair. Inside
        # a 'diff --git' section it is that section's own header; anywhere else
        # it opens a new file, which is how the AI's looser patches arrive.
        if (
            line.startswith("--- ")
            and i + 1 < len(lines)
            and lines[i + 1].startswith("+++ ")
        ):
            candidate = _strip_diff_prefix(_header_path(lines[i + 1], marker="+++ "))
            if candidate == "/dev/null":
                candidate = ""
            already_open = start is not None and lines[start].startswith("diff --git ")
            if not already_open:
                flush(i)
                start, in_hunk = i, False
                path = candidate
            elif candidate:
                path = candidate
            i += 1
            continue

        if line.startswith("@@"):
            in_hunk = bool(_HUNK_HEADER_RE.match(line))

        i += 1

    flush(len(lines))
    return sections


#: Binary hunk guard thresholds (see CONTEXT.md).
#:
#: A legitimate Latin-1 / Windows-1252 source file decoded with errors="replace"
#: produces 1 or 2 contiguous U+FFFD characters on isolated accented letters and
#: stays well below 2-5% across a file's hunks. A binary blob diffed as text
#: (e.g. a file with an ASCII header > 8000 bytes before the first NUL byte, or
#: forced as text by .gitattributes) produces either contiguous runs of U+FFFD
#: or a high density of replacement characters across the hunk body.
BINARY_FFFD_CONTIGUOUS_RUN = 8
BINARY_FFFD_MIN_COUNT = 32
BINARY_FFFD_MIN_DENSITY = 0.10


def _is_binary_hunk_section(lines, first_hunk_idx):
    """True when the hunk content lines from *first_hunk_idx* carry binary U+FFFD streams."""
    contiguous_needle = "\ufffd" * BINARY_FFFD_CONTIGUOUS_RUN
    total_fffd = 0
    total_chars = 0

    for line in lines[first_hunk_idx:]:
        if line.startswith("@@") or line.startswith("\\ No newline"):
            continue
        if line.startswith(("+", "-", " ")):
            payload = line[1:]
            if contiguous_needle in payload:
                return True
            total_fffd += payload.count("\ufffd")
            total_chars += len(payload)

    if total_fffd >= BINARY_FFFD_MIN_COUNT and total_chars > 0:
        return (total_fffd / total_chars) >= BINARY_FFFD_MIN_DENSITY
    return False


def _collapse_section_to_binary_marker(section):
    """Replace the hunks of *section* with git's standard 'Binary files ... differ' line."""
    lines = section.text.split("\n")
    while lines and lines[-1] == "":
        lines.pop()

    first_hunk_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("@@") and _HUNK_HEADER_RE.match(line):
            first_hunk_idx = idx
            break

    if first_hunk_idx is None or not _is_binary_hunk_section(lines, first_hunk_idx):
        return None

    old_label = f"a/{section.path}"
    new_label = f"b/{section.path}"
    kept_headers = []

    for line in lines[:first_hunk_idx]:
        if line.startswith("--- "):
            raw_old = _strip_diff_prefix(_header_path(line, marker="--- "))
            old_label = "/dev/null" if raw_old == "/dev/null" else f"a/{raw_old or section.path}"
            continue
        if line.startswith("+++ "):
            raw_new = _strip_diff_prefix(_header_path(line, marker="+++ "))
            new_label = "/dev/null" if raw_new == "/dev/null" else f"b/{raw_new or section.path}"
            continue
        kept_headers.append(line)

    if not kept_headers:
        kept_headers.append(f"diff --git a/{section.path} b/{section.path}")

    kept_headers.append(f"Binary files {old_label} and {new_label} differ")
    return "\n".join(kept_headers)


def collapse_binary_hunks(diff_text):
    """Binary hunk guard: collapse U+FFFD-heavy binary hunks into binary markers.

    Fast-paths in O(1) when *diff_text* contains no U+FFFD character, and
    returns *diff_text* verbatim when no section crosses the binary thresholds
    (preserving legitimate Latin-1 / Windows-1252 source code byte for byte).
    """
    if not diff_text or "\ufffd" not in diff_text:
        return diff_text

    sections = split_patch_sections(diff_text)
    if not sections:
        return diff_text

    changed = False
    rebuilt = []
    for section in sections:
        collapsed = _collapse_section_to_binary_marker(section)
        if collapsed is not None:
            rebuilt.append(collapsed)
            changed = True
        else:
            rebuilt.append(section.text.rstrip("\n"))

    if not changed:
        return diff_text

    trailing = "\n" if diff_text.endswith("\n") else ""
    return "\n".join(rebuilt) + trailing
