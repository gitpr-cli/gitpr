"""YAML front matter for skill files.

A skill may declare metadata in a leading YAML block, so the release flow can
write its changelog section in a language chosen by the repository instead of
the interface language. The block is stripped before the body reaches the AI
as the system instruction.
"""

import yaml

_FENCE = "---"
_BOM = chr(0xFEFF)


def split_front_matter(text):
    """Splits a leading YAML front matter block from a skill body.

    Front matter is recognized only when the first line — after an optional
    UTF-8 BOM — is a bare ``---`` fence and a closing ``---`` line exists
    before the text ends. Anything else is returned untouched, so a Markdown
    horizontal rule at the top of a skill never loses content.

    Args:
        text: the skill file content (the policy context may be appended).

    Returns:
        ``(metadata, body)``. ``metadata`` is an empty dict when there is no
        front matter or the block is not a YAML mapping; ``body`` is then the
        original text. A malformed block never raises.
    """
    if not isinstance(text, str) or not text:
        return {}, text

    content = text[1:] if text.startswith(_BOM) else text
    lines = content.splitlines(keepends=True)
    if not lines or not _is_fence(lines[0]):
        return {}, text

    closing = None
    for index in range(1, len(lines)):
        if _is_fence(lines[index]):
            closing = index
            break
    if closing is None:
        return {}, text

    metadata = _parse_block("".join(lines[1:closing]))
    if metadata is None:
        return {}, text
    return metadata, "".join(lines[closing + 1 :])


def _is_fence(line):
    """True when the line is exactly a ``---`` fence (trailing spaces allowed)."""
    return line.rstrip("\r\n").rstrip(" \t") == _FENCE


def _parse_block(block):
    """Returns the YAML mapping, ``{}`` for an empty block, or None when invalid."""
    if not block.strip():
        return {}
    try:
        data = yaml.safe_load(block)
    except Exception:
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        return None
    return data
