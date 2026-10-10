"""Where policy packs live, and how the lockfile and overrides are read and written.

Three sources, searched in this order:

1. ``.gitpr/policies/<name>/`` inside the repository — the team's own pack,
   versioned with the code;
2. ``~/.gitpr/policies/<name>/`` — packs the user installed;
3. ``src/policy_packs/<name>/`` — the packs GitPR ships in the wheel.

The order matters when two sources carry the same name: the closer one to the
repository wins, so a team can fork a bundled pack and have the fork take effect
without uninstalling anything. The checksum in the lockfile is what keeps that
from happening by accident — a fork has to be reactivated explicitly.

A pack that is already installed is never overwritten by `install` without a
confirmation the caller asks for; this module only writes what it is told to.
"""

import os
from typing import Any

import yaml

from src.domain.policy.policy_types import PolicySource

HOME_DIR_NAME = ".gitpr"
POLICIES_DIR_NAME = "policies"
LOCKFILE_NAME = "policy.lock.yml"
OVERRIDES_NAME = "policy.overrides.yml"

# The lockfile carries a schema of its own: it is read by a future GitPR that may
# not know today's keys, and it lives in the user's repository.
LOCKFILE_SCHEMA_VERSION = 1


def gitpr_home() -> str:
    """The user's GitPR directory (``~/.gitpr``)."""
    return os.path.join(os.path.expanduser("~"), HOME_DIR_NAME)


def installed_policies_dir() -> str:
    """Where `gitpr policy install` puts a pack (``~/.gitpr/policies``)."""
    return os.path.join(gitpr_home(), POLICIES_DIR_NAME)


def bundled_policies_dir() -> str:
    """The packs shipped inside the package (``src/policy_packs``).

    Computed from this file's location rather than from the current directory,
    because the packs have to be found from any repository the user runs in.
    """
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(package_root, "policy_packs")


def project_policies_dir(repo_path: str | None = None) -> str:
    """The repository's own packs (``<repo>/.gitpr/policies``)."""
    return os.path.join(repo_path or os.getcwd(), HOME_DIR_NAME, POLICIES_DIR_NAME)


def gitpr_dir(repo_path: str | None = None) -> str:
    """The repository's ``.gitpr`` directory."""
    return os.path.join(repo_path or os.getcwd(), HOME_DIR_NAME)


def lockfile_path(repo_path: str | None = None) -> str:
    """``<repo>/.gitpr/policy.lock.yml`` — versioned with the repository."""
    return os.path.join(gitpr_dir(repo_path), LOCKFILE_NAME)


def overrides_path(repo_path: str | None = None) -> str:
    """``<repo>/.gitpr/policy.overrides.yml`` — versioned with the repository."""
    return os.path.join(gitpr_dir(repo_path), OVERRIDES_NAME)


def install_dir_name(pack_name: str) -> str:
    """The directory an installed pack gets, derived from its name.

    A pack name carries a namespace (``gitpr/laravel-quality``) and a directory
    cannot, so the slash becomes a double underscore: flat enough for discovery
    to keep scanning one level, and unambiguous — turning it into a real
    subdirectory would make two packs named ``a/b`` and ``c/b`` collide.

    The directory name is only ever a container. Which pack lives there is read
    from the manifest, so a pack copied in by hand under any name still works.
    """
    return pack_name.strip().replace("/", "__")


def installed_pack_dir(pack_name: str) -> str:
    """Where ``gitpr policy install`` would put *pack_name*."""
    return os.path.join(installed_policies_dir(), install_dir_name(pack_name))


def source_search_order(repo_path: str | None = None) -> list[tuple[PolicySource, str]]:
    """The directories to search, nearest first, each with the source it means."""
    return [
        (PolicySource.LOCAL_PATH, project_policies_dir(repo_path)),
        (PolicySource.INSTALLED, installed_policies_dir()),
        (PolicySource.BUNDLED, bundled_policies_dir()),
    ]


def _read_yaml(path: str) -> Any:
    """Reads a YAML file, or returns None when it is not there.

    A malformed file raises — the caller wants to say which file is broken, and
    swallowing it here would turn a syntax error into "no policy active".
    """
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return yaml.safe_load(handle)


def read_lockfile(repo_path: str | None = None) -> dict[str, Any] | None:
    """The parsed lockfile, or None when the repository has no policy active."""
    return _read_yaml(lockfile_path(repo_path))


def read_overrides(repo_path: str | None = None) -> Any:
    """The parsed overrides file, or None when the repository has none."""
    return _read_yaml(overrides_path(repo_path))


def write_lockfile(data: dict[str, Any], repo_path: str | None = None, path: str | None = None) -> str:
    """Writes the lockfile atomically and returns the path written.

    Atomic because the lockfile is the first thing every later run reads: a
    truncated one would make the repository unusable until it was deleted by
    hand. The temporary file is created next to the target so os.replace is a
    rename within one filesystem.
    """
    target = path or lockfile_path(repo_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)

    temporary = f"{target}.tmp"
    with open(temporary, "w", encoding="utf-8", errors="replace", newline="\n") as handle:
        handle.write(text)
    os.replace(temporary, target)
    return target
