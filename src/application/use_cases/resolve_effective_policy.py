"""Use case: turn the repository's lockfile into the policy this run operates under.

This runs once per process, before skills, linter or risk are touched, and it is
the only place that decides *which* packs are in force. It reads the manifest
text, composes it, verifies the checksums the lockfile recorded, and publishes
the result into ``src.domain.policy.ACTIVE_POLICY`` — the same way
``src/i18n.set_lang()`` publishes the language, so the eleven call sites of
``get_skill_context`` do not each have to be threaded with a policy argument.

**No lockfile means an empty policy**, and every consumer reads that as "change
nothing": ``load_risk_config()``, ``load_linter_rules()`` and the skill files
behave exactly as they did before this feature existed. That is a property of the
code path, not a promise in a document.

Three failures abort instead of degrading — a pack removed from
``~/.gitpr/policies/``, a pinned version that vanished after an upgrade, and a
checksum that no longer matches. An active pack is a promise that a gate is in
force; half-keeping it is worse than not keeping it, because the output would
still carry the policy label. *strict=False* is the escape hatch for the
``gitpr policy`` commands themselves: they are the tool that repairs a broken
lockfile, so they have to be able to run while one is broken.
"""

import os
from typing import Any

from src.domain.policy import set_active_policy
from src.domain.policy.policy_manifest import parse_overrides
from src.domain.policy.policy_resolver import compose_policy, resolve_graph
from src.domain.policy.policy_types import (
    EffectivePolicy,
    PackReference,
    PolicyError,
    PolicySource,
)
from src.i18n import __
from src.infrastructure.policy.local_policy_repository import (
    read_lockfile,
    read_overrides,
)
from src.infrastructure.policy.policy_pack_loader import (
    load_pack_at,
    load_pack_by_reference,
    make_loader,
)


def _source_from(value: Any) -> PolicySource:
    try:
        return PolicySource(str(value))
    except ValueError:
        return PolicySource.BUNDLED


def _load_locked(entry: dict[str, Any], repo_path: str | None) -> Any:
    """Loads a pack exactly as the lockfile recorded it.

    A ``path`` is honoured when present, so a pack versioned inside the
    repository is read from where it was when it was activated even if another
    copy of the same name exists somewhere else on the machine.
    """
    name = entry.get("name")
    version = entry.get("version")
    if not name or not version:
        raise PolicyError(__("The policy lockfile is missing a pack name or version."))
    relative = entry.get("path")
    if relative:
        pack_dir = os.path.join(repo_path or os.getcwd(), relative)
        if os.path.isdir(pack_dir):
            return load_pack_at(pack_dir, _source_from(entry.get("source")))
    return load_pack_by_reference(str(name), str(version), repo_path)


def _verify_checksum(pack: Any, entry: dict[str, Any], source_label: str) -> None:
    """Aborts when a pack's content no longer matches what the lockfile recorded."""
    expected = entry.get("checksum")
    if not expected:
        return
    if pack.reference.checksum == expected:
        return
    raise PolicyError(
        __(
            "Pack {pack} changed since it was activated: the lockfile records {expected} "
            "but the files on disk hash to {found}. Review the change and run "
            "'gitpr policy use {name}@{version}' to accept it.",
            pack=pack.tag,
            expected=str(expected)[:12],
            found=str(pack.reference.checksum or "")[:12],
            name=pack.reference.name,
            version=pack.reference.version,
        ),
        pack=pack.reference.name,
    )


def locked_reference(repo_path: str | None = None) -> PackReference | None:
    """The root pack the lockfile pins, or None when nothing is active."""
    lock = read_lockfile(repo_path)
    if not lock:
        return None
    root = lock.get("root")
    if not isinstance(root, dict) or not root.get("name") or not root.get("version"):
        raise PolicyError(
            __(
                "The policy lockfile is malformed: it has no 'root' pack. Delete "
                "{path} or reactivate a pack with 'gitpr policy use'.",
                path=os.path.join(repo_path or os.getcwd(), ".gitpr", "policy.lock.yml"),
            )
        )
    return PackReference(
        name=str(root["name"]),
        version=str(root["version"]),
        source=_source_from(root.get("source")),
        path=root.get("path"),
        checksum=root.get("checksum"),
    )


def resolve_effective_policy(
    repo_path: str | None = None,
    *,
    strict: bool = True,
    publish: bool = True,
    overrides: dict[str, Any] | None = None,
    context_max_characters: int | None = None,
) -> EffectivePolicy:
    """Composes the active policy for *repo_path* and publishes it.

    *overrides* may be passed pre-parsed (tests do); otherwise the repository's
    ``.gitpr/policy.overrides.yml`` is read and validated here. *strict=False*
    turns a resolution failure into a warning on an empty policy instead of an
    exception — see the module docstring for why that escape hatch exists.
    """
    try:
        return _resolve(repo_path, overrides, context_max_characters)
    except PolicyError as error:
        if strict:
            raise
        policy = EffectivePolicy(warnings=[error.message])
        if publish:
            set_active_policy(policy)
        return policy


def _resolve(
    repo_path: str | None,
    overrides: dict[str, Any] | None,
    context_max_characters: int | None,
) -> EffectivePolicy:
    from src.config import policy_context_max_characters, policy_enabled

    if not policy_enabled():
        policy = EffectivePolicy()
        set_active_policy(policy)
        return policy

    root_reference = locked_reference(repo_path)
    if root_reference is None:
        policy = EffectivePolicy()
        set_active_policy(policy)
        return policy

    lock = read_lockfile(repo_path) or {}
    recorded = {
        entry.get("name"): entry
        for entry in lock.get("packs", [])
        if isinstance(entry, dict) and entry.get("name")
    }

    root_entry = dict(lock.get("root") or {})
    root_entry.setdefault("name", root_reference.name)
    root_entry.setdefault("version", root_reference.version)
    root = _load_locked(root_entry, repo_path)

    if root.manifest.name != root_reference.name:
        raise PolicyError(
            __(
                "The lockfile pins {pinned}, but the pack found there is {found}.",
                pinned=root_reference.name,
                found=root.manifest.name,
            ),
            pack=root_reference.name,
        )

    packs = resolve_graph(root, make_loader(repo_path))

    for pack in packs:
        entry = recorded.get(pack.reference.name) or (
            root_entry if pack.reference.name == root.manifest.name else None
        )
        if entry:
            _verify_checksum(pack, entry, pack.reference.name)

    parsed_overrides = overrides
    if parsed_overrides is None:
        parsed_overrides = parse_overrides(read_overrides(repo_path))

    policy = compose_policy(
        packs,
        overrides=parsed_overrides,
        context_max_characters=(
            context_max_characters
            if context_max_characters is not None
            else policy_context_max_characters()
        ),
    )
    set_active_policy(policy)
    return policy
