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
