"""SHA-256 checksums for a policy pack, so an unexpected edit is detectable.

The lockfile records the checksum of every active pack. When the content on disk
no longer matches it, the pack changed without an explicit reactivation and the
run aborts — that is what stops a modified pack from silently weakening the gate.

The digest covers ``policy.yml`` plus every asset the manifest declares (the
linter rules file today). Untracked files in the pack directory are deliberately
out of scope: the pack is what it declares, and hashing a whole directory would
make an unrelated README edit invalidate a policy.
"""

import hashlib
import os

MANIFEST_FILE = "policy.yml"
_CHUNK = 65536


def checksum_bytes(data: bytes) -> str:
    """SHA-256 of *data*, hex-encoded."""
    return hashlib.sha256(data).hexdigest()


def checksum_file(path: str) -> str:
    """SHA-256 of the file at *path*, read in binary so no encoding is involved."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def checksum_pack(pack_dir: str, asset_paths: list[str] | None = None) -> str:
    """Combined SHA-256 of a pack's manifest and the assets it declares.

    Each file contributes ``relative_path:digest``, and the lines are sorted
    before the final hash — so the result depends on what the pack contains, not
    on the order the assets happened to be listed in the manifest.

    Raises ``FileNotFoundError`` when the manifest is missing; a declared asset
    that is not on disk is skipped, because policy_manifest.py already refuses it
    with a message that names the file.
    """
    lines = []
    manifest_path = os.path.join(pack_dir, MANIFEST_FILE)
    lines.append(f"{MANIFEST_FILE}:{checksum_file(manifest_path)}")

    for relative in asset_paths or []:
        full_path = os.path.join(pack_dir, relative.replace("/", os.sep))
        if not os.path.isfile(full_path):
            continue
        normalized = relative.replace(os.sep, "/")
        lines.append(f"{normalized}:{checksum_file(full_path)}")

    lines.sort()
    return checksum_bytes("\n".join(lines).encode("utf-8"))
