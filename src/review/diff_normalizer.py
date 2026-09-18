"""Apply the smart excludes to a diff that never went through git.

The local flows hand the patterns to git as ``:(exclude)`` pathspecs, so git
does the filtering and the diff arrives already clean. A diff fetched from a
forge API carries every file the pull request touched — lockfiles, bundles,
minified assets, prose — and those are exactly what the smart excludes exist to
keep away from the model. Re-running the same patterns here keeps a remote
review's input comparable to a local one's, at the price of a filter git is not
there to do.

Pure: it takes the patterns as an argument rather than reaching for
``core.SMART_EXCLUDES``, which keeps the module free of I/O and lets the tests
pin a pattern list instead of depending on whatever the user has downloaded.
"""

import fnmatch


def normalize_newlines(diff_text):
    """Drop the carriage returns a forge may embed in a diff body.

    The engine and every helper in ``diff_parser`` split on a bare "\\n", so a
    CRLF diff would leave a trailing "\\r" on each line — enough to break the
    ``diff --git`` and ``@@`` prefix checks. GitHub and Bitbucket serve LF, but
    a self-hosted forge behind a proxy is not guaranteed to.
    """
    if "\r" not in diff_text:
        return diff_text
    return diff_text.replace("\r\n", "\n").replace("\r", "\n")


def is_reviewable_diff(diff_text):
    """Whether *diff_text* is a unified diff the review engine can work on.

    A safety net behind ``ScmProvider.supports_reviewable_diff``: if a provider
    claims to serve a diff but answers with prose instead (the way Azure DevOps
    answers with a ``{path} (+a -d)`` summary), the review must stop here rather
    than spend tokens on text with no hunks in it. A file-modifying patch always
    carries at least one 'diff --git' or '@@' line — even a pure rename or a
    binary change has the former — so requiring one of them rejects summaries
    without rejecting any real patch.
    """
    for raw_line in diff_text.split("\n"):
        line = raw_line.rstrip("\r")
        if line.startswith("diff --git ") or line.startswith("@@"):
            return True
    return False


def filter_excluded_sections(diff_text, patterns):
    """Drop the files of *diff_text* whose path matches a smart exclude.

    Returns ``(filtered_diff, dropped_paths)``. The dropped list is what lets
    the caller tell the user which files were skipped — a review that silently
    ignored half a pull request would be worse than one that says so.

    Matching is ``fnmatch`` against the whole path, the same call
    ``core.get_changed_docs_list`` makes: fnmatch's ``*`` crosses "/", so a
    pattern like "*.lock" already covers "vendor/deep/thing.lock" and no
    separate basename pass is needed. Without patterns the input is returned
    untouched, which is also what an empty SMART_EXCLUDES produces.
    """
    if not patterns:
        return diff_text, []

    # Imported here: diff_parser is pure and cheap, but keeping the import at
    # module level would be the only thing this module needs from it.
    from src.diff_parser import split_patch_sections

    sections = split_patch_sections(diff_text)
    if not sections:
        return diff_text, []

    kept = []
    dropped = []
    for section in sections:
        if any(fnmatch.fnmatch(section.path, pattern) for pattern in patterns):
            dropped.append(section.path)
        else:
            kept.append(section.text)

    if not dropped:
        return diff_text, []
    return "\n".join(kept), dropped
