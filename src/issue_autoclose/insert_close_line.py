"""The closing line joins the pull request body at its single assembly point.

The PR flow builds the description once — after the reviewer guide and before
the local ``.md`` and ``pr_data`` are produced. :func:`insert_close_line` is
called from that point: when the close-issue decision produced a line, the body
gets it as its own paragraph, unless the body already mentions the issue with
any closing keyword (ADR-004).

The badge is attached later and always at the end of the body, so appending
here is what leaves the line immediately before it — this module never has to
look for a badge.
"""
import re

# GitHub accepts these verbs in English only, case-insensitively, and the same
# issue may be named as ``owner/repo#N``.
_CLOSING_KEYWORDS = r"(?:close[sd]?|fix(?:es|ed)?|resolve[sd]?)"
_CLOSING_REFERENCE = re.compile(
    rf"\b{_CLOSING_KEYWORDS}\s+(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#(\d+)\b",
    re.IGNORECASE,
)


def has_closing_reference(body, number):
    """Whether ``body`` already closes issue ``number`` with any keyword."""
    return any(
        int(match) == number for match in _CLOSING_REFERENCE.findall(body or "")
    )


def insert_close_line(body, decision):
    """Return ``body`` with the closing line appended, exactly once.

    A ``None`` decision means nothing was offered or the user declined: the
    body comes back unchanged. A body that already names the issue with a
    closing keyword is left alone too — the forge closes it either way.
    """
    if decision is None:
        return body

    body = body or ""
    if has_closing_reference(body, decision.number):
        return body

    text = body.rstrip()
    return f"{text}\n\n{decision.line}" if text else decision.line
