"""Reading policy packs off disk.

Everything that touches the filesystem for a pack happens here: finding the
directories, parsing the manifest, reading the rules file, computing the
checksum. The resolver above it receives ``ResolvedPack`` values and never opens
a file, which is what keeps the composition rules testable without fixtures.

Nothing here downloads. A pack is bundled, installed or versioned in the
repository, and a name that cannot be found is simply not found — the message
says which sources were searched so the user knows what to add and where.
"""

import os
from dataclasses import dataclass
from typing import Any, Callable

import yaml

from src.domain.policy.policy_compatibility import (
    parse_semver,
    parse_specifier,
    resolve_asset_path,
)
from src.domain.policy.policy_checksum import MANIFEST_FILE, checksum_pack
from src.domain.policy.policy_manifest import parse_manifest
from src.domain.policy.policy_resolver import ResolvedPack
from src.domain.policy.policy_types import PackReference, PolicyError, PolicySource
from src.i18n import __
from src.infrastructure.policy.local_policy_repository import source_search_order


@dataclass
class DiscoveredPack:
    """A directory that looks like a pack.

    *reference* is None when the manifest could not be read at all, and *error*
    carries the reason — ``gitpr policy list`` shows those rows too, because a
    pack that silently disappears from the listing is worse than one that says
    why it is broken.
    """

    path: str
    source: PolicySource
    reference: PackReference | None = None
    error: str | None = None

    @property
    def name(self) -> str:
        if self.reference:
            return self.reference.name
        return os.path.basename(self.path.rstrip("/\\"))


def _read_yaml_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return yaml.safe_load(handle)


def load_pack_at(pack_dir: str, source: PolicySource) -> ResolvedPack:
    """Reads the pack in *pack_dir*: manifest, rules file, checksum.

    Raises ``PolicyError`` for anything that would make the pack unusable — a
    missing manifest, a manifest that fails validation, a rules file that is
    declared but absent or that escapes the directory.
    """
    manifest_path = os.path.join(pack_dir, MANIFEST_FILE)
    if not os.path.isfile(manifest_path):
        raise PolicyError(
            __(
                "No {manifest} in {path}. A policy pack is a directory with at least "
                "a manifest and, optionally, a rules file.",
                manifest=MANIFEST_FILE,
                path=pack_dir,
            )
        )

    try:
        data = _read_yaml_file(manifest_path)
    except yaml.YAMLError as error:
        raise PolicyError(__("Could not parse {path}: {error}", path=manifest_path, error=str(error)))

    with open(manifest_path, "r", encoding="utf-8", errors="replace") as handle:
        raw_text = handle.read()

    manifest = parse_manifest(data, pack_dir=pack_dir, raw_text=raw_text, source=source)

    rules: list[dict] = []
    asset_names: list[str] = []
    if manifest.rules_file:
        asset_names.append(manifest.rules_file)
        rules_path = resolve_asset_path(pack_dir, manifest.rules_file, manifest.name)
        if not os.path.isfile(rules_path):
            raise PolicyError(
                __(
                    "Pack {pack} declares linter.rules_file {file}, which does not exist "
                    "in {path}.",
                    pack=manifest.name,
                    file=manifest.rules_file,
                    path=pack_dir,
                ),
                pack=manifest.name,
            )
        try:
            catalogue = _read_yaml_file(rules_path) or {}
        except yaml.YAMLError as error:
            raise PolicyError(
                __(
                    "Pack {pack}: could not parse {file}: {error}",
                    pack=manifest.name,
                    file=manifest.rules_file,
                    error=str(error),
                ),
                pack=manifest.name,
            )
        found = catalogue.get("rules", []) if isinstance(catalogue, dict) else []
        if not isinstance(found, list):
            raise PolicyError(
                __(
                    "Pack {pack}: {file} must contain a 'rules' list.",
                    pack=manifest.name,
                    file=manifest.rules_file,
                ),
                pack=manifest.name,
            )
        rules = [rule for rule in found if isinstance(rule, dict)]

    reference = PackReference(
        name=manifest.name,
        version=manifest.version,
        source=source,
        path=os.path.abspath(pack_dir),
        checksum=checksum_pack(pack_dir, asset_names),
    )
    return ResolvedPack(reference=reference, manifest=manifest, rules=rules)


def discover_packs(repo_path: str | None = None) -> list[DiscoveredPack]:
    """Every pack directory in the three sources.

    A directory is a candidate when it holds a ``policy.yml``. Names already
    found in a nearer source are not listed again from a farther one, so the
    listing mirrors what resolution would actually pick.
    """
    found: list[DiscoveredPack] = []
    claimed: set[str] = set()

    for source, root in source_search_order(repo_path):
        if not os.path.isdir(root):
            continue
        for entry in sorted(os.listdir(root)):
            pack_dir = os.path.join(root, entry)
            if not os.path.isdir(pack_dir):
                continue
            if not os.path.isfile(os.path.join(pack_dir, MANIFEST_FILE)):
                continue
            try:
                pack = load_pack_at(pack_dir, source)
            except PolicyError as error:
                found.append(DiscoveredPack(path=pack_dir, source=source, error=error.message))
                continue
            if pack.reference.name in claimed:
                continue
            claimed.add(pack.reference.name)
            found.append(DiscoveredPack(path=pack_dir, source=source, reference=pack.reference))

    return found


def load_pack_by_reference(
    name: str, version_range: str, repo_path: str | None = None
) -> ResolvedPack:
    """The best pack named *name* whose version satisfies *version_range*.

    Highest version wins when several sources or several copies qualify. Raises
    with the searched directories listed when nothing matches: the two usual
    causes — a typo in the name, and a pack that was never installed — need
    different fixes, and the message has to support telling them apart.
    """
    specifier = parse_specifier(version_range, f"extends[{name}].version")
    searched: list[str] = []
    candidates: list[ResolvedPack] = []
    broken: dict[str, str] = {}

    for source, root in source_search_order(repo_path):
        searched.append(root)
        if not os.path.isdir(root):
            continue
        if os.path.isfile(os.path.join(root, MANIFEST_FILE)):
            # The root itself is a pack directory, not a container of them.
            directories = [root]
        else:
            directories = [os.path.join(root, e) for e in sorted(os.listdir(root))]
        for pack_dir in directories:
            if not os.path.isdir(pack_dir):
                continue
            if not os.path.isfile(os.path.join(pack_dir, MANIFEST_FILE)):
                continue
            try:
                pack = load_pack_at(pack_dir, source)
            except PolicyError as error:
                # A pack that cannot be read is not a candidate. Its message is
                # kept under the directory's own name, because the directory is
                # usually named after the pack — that guess is what turns a bare
                # "not found" into "it is there, and this is what is wrong".
                broken.setdefault(os.path.basename(pack_dir.rstrip("/\\")), error.message)
                continue
            if pack.reference.name != name:
                continue
            try:
                parse_semver(pack.reference.version)
            except PolicyError:
                continue
            if specifier.contains(pack.reference.version, prereleases=True):
                candidates.append(pack)

    if not candidates:
        reason = broken.get(name.rsplit("/", 1)[-1])
        if reason:
            raise PolicyError(
                __("Pack {name} is installed but unusable: {reason}", name=name, reason=reason),
                pack=name,
            )
        raise PolicyError(
            __(
                "Pack {name} {range} not found. Searched: {searched}. "
                "Use 'gitpr policy list' to see what is available, or "
                "'gitpr policy install <path>' to add it.",
                name=name,
                range=version_range,
                searched=", ".join(searched),
            ),
            pack=name,
        )

    return max(candidates, key=lambda p: parse_semver(p.reference.version))


def make_loader(repo_path: str | None = None) -> Callable[[str, str], ResolvedPack]:
    """A loader bound to *repo_path* for ``resolve_graph``."""
    return lambda name, version_range: load_pack_by_reference(name, version_range, repo_path)
