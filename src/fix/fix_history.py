"""The record of applied patches — what makes ``--rollback`` deterministic.

Rollback cannot lean on the commit history: a patch applied by ``gitpr fix`` is
left *uncommitted* on purpose (the user reviews it first), so there is no commit
to revert. The full diff is therefore stored here, and ``git apply --reverse``
reads it back.

The file lives at ``<root>/.gitpr/fix_history.json`` and is tracked in git — the
behaviour the feature was specified with. The consequence is deliberate and
known: applying a fix dirties a tracked file, so it shows up in ``gitpr -c`` and
in PR descriptions until it is committed. ``templates/gitpr.smart-excludes.json``
carries an entry for it.

Schema of one entry — ``make_entry`` is its only author, so the names cannot
drift from the readers in ``rollback_fix``:

    patch_id        "FIX-001-1a2b3c4d" — what --rollback addresses
    finding_id      "FIX-001"
    file_path       the file the review pointed at
    files_changed   every path the diff touches
    safety          "safe" / "review_required" / "experimental"
    branch          branch the patch was applied on (None if created in place)
    applied_at      "%Y-%m-%d %H:%M:%S", the project's cache timestamp format
    diff            the complete unified diff, verbatim
    provenance      provider, model, prompt_version, gitpr_version, generated_at
    rolled_back_at  timestamp once undone, else None
"""
import json
import os
from dataclasses import asdict
from datetime import datetime

from src.fix.patch_provenance import PatchSafety

HISTORY_DIR = ".gitpr"
HISTORY_FILENAME = "fix_history.json"

#: The same timestamp shape the prompt cache writes, so both sort as strings.
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class FixHistoryError(Exception):
    """The history exists but cannot be used — unreadable, or not a list.

    Raised rather than swallowed: a corrupt history means "we cannot tell you
    what was applied", which a rollback must never confuse with "nothing was
    applied". A file that is simply *absent* is an empty history, not an error.
    """


def history_path(root=None):
    """Absolute path of the history file below *root* (default: cwd)."""
    return os.path.join(os.path.abspath(root or os.getcwd()), HISTORY_DIR, HISTORY_FILENAME)


def load_history(root=None):
    """Every recorded patch, oldest first. A missing file gives ``[]``."""
    path = history_path(root)
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise FixHistoryError(f"cannot read {path}: {exc}") from exc

    if not isinstance(data, list):
        raise FixHistoryError(f"{path} does not hold a list of patches")
    return data


def save_history(entries, root=None):
    """Write *entries* to the history file, creating ``.gitpr/`` if needed.

    The write goes to a sibling temporary file and is then moved into place, so
    an interrupted run can never leave a half-written history behind — losing
    the file would lose the record of every patch ever applied.
    """
    path = history_path(root)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    temporary = path + ".tmp"
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(entries, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
    except OSError as exc:
        if os.path.exists(temporary):
            try:
                os.remove(temporary)
            except OSError:
                pass
        raise FixHistoryError(f"cannot write {path}: {exc}") from exc


def append_entry(entry, root=None):
    """Add *entry* to the history and return the updated list."""
    entries = load_history(root)
    entries.append(entry)
    save_history(entries, root)
    return entries


def find_entry(patch_id, root=None):
    """The most recent entry for *patch_id*, or None when it was never applied."""
    for entry in reversed(load_history(root)):
        if isinstance(entry, dict) and entry.get("patch_id") == patch_id:
            return entry
    return None


def mark_rolled_back(patch_id, root=None) -> bool:
    """Stamp *patch_id* as undone. False when it is not in the history."""
    entries = load_history(root)
    for entry in reversed(entries):
        if isinstance(entry, dict) and entry.get("patch_id") == patch_id:
            entry["rolled_back_at"] = datetime.now().strftime(TIMESTAMP_FORMAT)
            save_history(entries, root)
            return True
    return False


def make_entry(
    patch_id,
    finding,
    diff,
    provenance,
    files_changed=(),
    safety=PatchSafety.EXPERIMENTAL,
    branch=None,
    applied_at=None,
):
    """Build one history entry — the schema's single author.

    ``safety`` accepts the enum or its plain value, because the entry is JSON
    and the enum is not: storing ``PatchSafety.SAFE`` would fail to serialise
    while looking correct in the signature.
    """
    return {
        "patch_id": patch_id,
        "finding_id": finding.id,
        "file_path": finding.file_path,
        "files_changed": [str(path) for path in files_changed],
        "safety": safety.value if isinstance(safety, PatchSafety) else str(safety),
        "branch": branch,
        "applied_at": applied_at or datetime.now().strftime(TIMESTAMP_FORMAT),
        "diff": diff,
        "provenance": asdict(provenance),
        "rolled_back_at": None,
    }
