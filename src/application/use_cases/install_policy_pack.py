"""Use case: put a pack on this machine so it can be referenced by name.

There is no registry and no download. A pack is a directory, and installing one
means copying it into ``~/.gitpr/policies/`` where ``load_pack_by_reference``
will find it — from any repository, not just the one it was installed from.

The source is validated *before* anything is written, so a broken pack cannot
land in the policies directory and turn every later command into a resolution
failure. Nothing here asks the user anything: the CLI layer owns the
confirmation, because this function is also the one tests call.
"""

import os
import shutil
from typing import Any

from src.domain.policy.policy_types import PolicyError, PolicySource
from src.i18n import __
from src.infrastructure.policy.local_policy_repository import installed_pack_dir
from src.infrastructure.policy.policy_pack_loader import load_pack_at


def load_source_pack(source_dir: str) -> Any:
    """Reads the pack in *source_dir*, or says why it cannot be used."""
    source = os.path.abspath(os.path.expanduser(source_dir))
    if not os.path.isdir(source):
        raise PolicyError(
            __(
                "There is no directory at {path}. 'gitpr policy install' takes the "
                "path of a pack directory, which must contain a policy.yml.",
                path=source_dir,
            )
        )
    return load_pack_at(source, PolicySource.LOCAL_PATH)


def install_policy_pack(
    source_dir: str, *, overwrite: bool = False, target_dir: str | None = None
) -> str:
    """Copies the pack in *source_dir* into the user's policies directory.

    Returns the directory the pack was written to. *overwrite* replaces an
    existing installation; without it, an occupied destination is refused rather
    than merged, because half of one pack and half of another would still parse.
    *target_dir* overrides the destination and exists for the tests, which must
    not write to the real home directory.
    """
    source = os.path.abspath(os.path.expanduser(source_dir))
    pack = load_source_pack(source)
    name = pack.manifest.name
    destination = target_dir or installed_pack_dir(name)

    if os.path.exists(destination):
        if not overwrite:
            raise PolicyError(
                __(
                    "Pack {pack} is already installed at {path}. Re-run with "
                    "--force to replace it.",
                    pack=name,
                    path=destination,
                ),
                pack=name,
            )
        shutil.rmtree(destination)

    parent = os.path.dirname(destination)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.copytree(source, destination)

    return destination
