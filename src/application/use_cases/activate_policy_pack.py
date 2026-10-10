"""Use case: record which pack a repository follows.

The record is ``.gitpr/policy.lock.yml``, a file meant to be committed: it is
what makes the policy the same for everyone on the team and what lets a later
run notice that a pack changed under it.

Activation is **one pack per repository**. Choosing a second one replaces the
first rather than adding to it, so there is never a question about which pack
owns a value — the graph below the root is reached through ``extends``, and only
through it.

Building the lockfile and writing it are separate functions because the CLI has
to show the user what will be written *before* asking whether to write it. A
command that writes first and asks afterwards is not asking.
"""

import os
from datetime import datetime, timezone
from typing import Any

from src.domain.policy import set_active_policy
from src.domain.policy.policy_resolver import resolve_graph
from src.i18n import __
from src.infrastructure.policy.local_policy_repository import (
    LOCKFILE_SCHEMA_VERSION,
    lockfile_path,
    write_lockfile,
)
from src.infrastructure.policy.policy_pack_loader import (
    load_pack_by_reference,
    make_loader,
)

from src.application.use_cases.validate_policy_pack import split_reference


def _relative_to_repo(absolute: str, repo_path: str) -> str | None:
    """*absolute* as a repository-relative POSIX path, or None when outside.

    Only packs that live inside the repository are recorded by path. A pack in
    ``~/.gitpr/policies/`` is recorded by name and version instead, so the
    lockfile stays valid for a teammate who has it installed somewhere else.
    """
    try:
        relative = os.path.relpath(absolute, repo_path)
    except ValueError:
        # Different drives on Windows.
        return None
    parts = relative.split(os.sep)
    if not relative or parts[0] == "..":
        return None
    return relative.replace(os.sep, "/")


def _lockfile_entry(pack: Any, repo_path: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "name": pack.reference.name,
        "version": pack.reference.version,
        "source": pack.reference.source.value,
        "checksum": pack.reference.checksum,
    }
    if pack.reference.path:
        relative = _relative_to_repo(pack.reference.path, repo_path)
        if relative:
            entry["path"] = relative
    return entry


def build_lockfile(root_reference: str, repo_path: str | None = None) -> dict[str, Any]:
    """Resolves *root_reference* and the lockfile that would pin it.

    Raises ``PolicyError`` when the pack cannot be found or its graph does not
    resolve, and writes nothing. The CLI calls this first, shows the result, and
    only then decides whether to call :func:`activate_policy_pack`.
    """
    from src.updater import __version__

    repo = os.path.abspath(repo_path or os.getcwd())
    name, version_range = split_reference(root_reference)
    root = load_pack_by_reference(name, version_range, repo)
    packs = resolve_graph(root, make_loader(repo))

    return {
        "schema_version": LOCKFILE_SCHEMA_VERSION,
        "gitpr_version": __version__,
        "activated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": _lockfile_entry(root, repo),
        "packs": [_lockfile_entry(pack, repo) for pack in packs],
    }


def activate_policy_pack(root_reference: str, repo_path: str | None = None) -> str:
    """Pins *root_reference* for the repository and returns the lockfile path."""
    data = build_lockfile(root_reference, repo_path)
    return write_lockfile(data, repo_path)


def deactivate_policy_pack(repo_path: str | None = None) -> bool:
    """Removes the lockfile. Returns whether there was one to remove.

    The overrides file and the packs themselves are left alone: they are the
    user's material, and a decision to stop following a pack is not a decision to
    delete it.
    """
    target = lockfile_path(repo_path)
    if not os.path.isfile(target):
        return False
    os.remove(target)
    set_active_policy(None)
    return True


def describe_lockfile(data: dict[str, Any]) -> str:
    """A one-line summary for the confirmation prompt."""
    root = data.get("root") or {}
    dependencies = [p for p in data.get("packs", []) if p.get("name") != root.get("name")]
    return __(
        "{pack}@{version} with {count} dependency pack(s)",
        pack=root.get("name", "?"),
        version=root.get("version", "?"),
        count=len(dependencies),
    )
