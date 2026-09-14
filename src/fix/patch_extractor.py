"""Reading the code an AI hands back — for the chat shortcuts and for ``gitpr fix``.

Both the chat's auto-patch shortcuts (F5, ctrl+s) and ``gitpr fix`` read AI
output that carries code inside fenced blocks. This module owns that reading so
the two can never drift apart: the chat takes every block, joined — its
historical behaviour, preserved exactly — while ``gitpr fix`` needs a patch it
can hand to git, and so accepts a candidate only when it parses as a real diff.
"""
import re

from src.diff_parser import summarize_patch


def extract_code_blocks(text):
    """Return the fenced code blocks of *text*, in order, or ``[]``.

    The primary pass is a regex over triple backticks (`````python``,
    ````` python``, bare fences, ...); when it matches nothing, the text is
    split on the fences and the odd-indexed parts are taken, with a leading
    language identifier stripped. Both passes are the ones the chat shortcuts
    have always used.
    """
    if not text:
        return []

    code_blocks = re.findall(r"`{3}\s*(?:\w+)?\s*\n(.*?)`{3}", text, re.DOTALL)
    if code_blocks:
        return code_blocks

    # Fallback: split by triple backticks and take odd-indexed parts
    parts = text.split("```")
    for i in range(1, len(parts), 2):
        block = parts[i].strip()
        if block:
            # Strip language identifier from first line if present
            first_line_end = block.find("\n")
            if first_line_end > 0 and first_line_end < 20:
                first_line = block[:first_line_end].strip()
                if first_line and " " not in first_line:
                    block = block[first_line_end + 1 :]
            code_blocks.append(block.strip())
    return code_blocks


def extract_unified_diff(text):
    """Return the unified diff *text* carries, or ``None`` when it carries none.

    A bare diff and one wrapped in a fenced block are both accepted — models
    fence diffs even when asked for raw text. A candidate survives only when it
    parses as a real patch (a file section with at least one hunk), so prose or
    a plain snippet can never reach ``git apply``. The returned text always ends
    with a newline, which is what git expects of a patch file.
    """
    if not text or not text.strip():
        return None

    for candidate in extract_code_blocks(text) or [text]:
        summary = summarize_patch(candidate)
        if summary.files and summary.hunks:
            return candidate.rstrip("\n") + "\n"
    return None
