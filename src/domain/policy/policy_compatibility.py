"""Compatibility and safety checks a pack has to pass before it can be applied.

Three families of check live here, all of them cheap and all of them pure:

- **versions** — SemVer parsing and range matching, through ``packaging``. The
  hand-rolled ``parse_version()`` in ``src/updater.py`` returns (0,0,0) for
  anything that is not ``X.Y.Z``, so it cannot read a range at all.
- **references** — a pack may only name a skill that exists in the fixed
  registry, and a rule that the merged linter catalogue can actually resolve.
- **paths** — a declared asset is relative to the pack directory and may not
  escape it, which is what keeps a shared pack from reading the machine it lands
  on.

Nothing here touches the filesystem or the network, so validation is testable
without fixtures and costs nothing to run on every activation.
"""

import os
import re

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from src.domain.policy.policy_types import PolicyError
from src.i18n import __

# namespace/name, both halves non-empty and free of separators. A leading dot is
# refused so ".", ".." and hidden files can never be spelled here.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")

# Assets a manifest may point at. Kept deliberately narrow: a pack declares data
# files it ships, not an arbitrary path into the repository or the home folder.
_ASSET_SUFFIXES = (".yml", ".yaml", ".json", ".md")


def allowed_skill_types() -> tuple[str, ...]:
    """The fixed skill registry, imported lazily.

    ``SKILL_TYPES`` in ``src/config.py`` is the single source of truth — the
    configuration screen and the tests already hold it in agreement with
    ``SKILL_FILES_BY_TYPE``. It is imported at call time rather than at module
    import so the domain package stays free of the CLI/dotenv stack, and so a
    future ``config`` import of this package cannot become a cycle.
    """
    from src.config import SKILL_TYPES

    return SKILL_TYPES


def validate_pack_name(name: str) -> None:
    """Raises when *name* is not a ``namespace/name`` free of path traversal."""
    if not isinstance(name, str) or not _NAME_PATTERN.match(name):
        raise PolicyError(
            __(
                "Invalid pack name {name!r}: expected 'namespace/name' using letters, "
                "digits, dot, dash and underscore (e.g. gitpr/laravel-quality).",
                name=name,
            )
        )


def parse_semver(version: str, field: str = "version") -> Version:
    """Parses a strict three-component SemVer, or raises a PolicyError.

    ``packaging`` accepts short forms like ``1.0`` (PEP 440) which SemVer does
    not, so the release tuple is checked for exactly three components. Anything
    after a hyphen (``1.0.0-rc1``) is left to ``packaging``.
    """
    try:
        parsed = Version(str(version))
    except InvalidVersion:
        raise PolicyError(
            __("Invalid SemVer in {field}: {value!r}.", field=field, value=version)
        )
    if len(parsed.release) != 3:
        raise PolicyError(
            __(
                "Invalid SemVer in {field}: {value!r} (expected MAJOR.MINOR.PATCH).",
                field=field,
                value=version,
            )
        )
    return parsed


# Characters that make a string an operator expression rather than a bare
# version. Anything without one of these is read as an exact match.
_OPERATORS = "<>=!~"


def parse_specifier(spec: str, field: str = "min_gitpr_version") -> SpecifierSet:
    """Parses a version range, or raises a PolicyError naming the field.

    Three spellings mean the same thing and all three are accepted, because all
    three are written by hand:

    - ``>=1.0.0,<2.0.0`` — canonical PEP 440;
    - ``>=1.0.0 <2.0.0`` — the same range with a space, which is what people
      write in YAML where a comma list reads like a typo. A specifier never
      contains a space, so splitting on whitespace cannot misread a valid range;
    - ``1.0.0`` — a bare version, read as ``==1.0.0``. ``SpecifierSet`` rejects
      it today, so giving it a meaning cannot change what an existing range did.

    The error quotes what was written, not the rewritten form, so the message
    matches the line the author is looking at.
    """
    text = str(spec).strip()
    if " " in text or "\t" in text:
        text = ",".join(text.split())
    elif text and not any(operator in text for operator in _OPERATORS):
        text = f"=={text}"
    try:
        return SpecifierSet(text)
    except InvalidSpecifier:
        raise PolicyError(
            __(
                "Invalid version range in {field}: {value!r}. Use PEP 440 notation, "
                "for example '>=1.0.0,<2.0.0'.",
                field=field,
                value=spec,
            )
        )


def is_gitpr_compatible(min_gitpr_version: str, current_version: str) -> bool:
    """Whether the running GitPR satisfies the range the pack requires.

    An unparseable *current_version* counts as compatible: this gates third-party
    packs, and refusing to run any of them because our own version string is
    unusual would be a worse failure than the one it guards against.
    """
    try:
        running = Version(str(current_version))
    except InvalidVersion:
        return True
    return running in parse_specifier(min_gitpr_version, "min_gitpr_version")


def check_gitpr_compatibility(
    min_gitpr_version: str, current_version: str, pack_name: str
) -> None:
    """Raises when the pack requires a GitPR this build is not."""
    if not is_gitpr_compatible(min_gitpr_version, current_version):
        raise PolicyError(
            __(
                "Pack {pack} requires GitPR {required}, but this is {current}. "
                "Upgrade with 'pip install --upgrade gitpr-cli'.",
                pack=pack_name,
                required=min_gitpr_version,
                current=current_version,
            ),
            pack=pack_name,
        )


def check_skill_name(skill_name: str, pack_name: str) -> None:
    """Raises when a pack names a skill the fixed registry does not have.

    A pack can only activate a skill GitPR already runs. This is an error, never
    a warning: a silently dropped skill would leave the user believing a gate is
    in force that is not.
    """
    known = allowed_skill_types()
    if skill_name not in known:
        raise PolicyError(
            __(
                "Pack {pack} references unknown skill {skill}. Supported skills: {known}.",
                pack=pack_name,
                skill=skill_name,
                known=", ".join(known),
            ),
            pack=pack_name,
        )


def resolve_asset_path(pack_dir: str, relative: str, pack_name: str = "") -> str:
    """Absolute path of an asset declared by a pack, refusing to leave the pack.

    Absolute paths, drive-qualified paths and anything that resolves outside
    *pack_dir* raise. The check runs on the real path, so a symlink pointing out
    of the directory is caught too.
    """
    if not isinstance(relative, str) or not relative.strip():
        raise PolicyError(f"Empty asset path in pack {pack_name}", pack=pack_name or None)

    candidate = relative.strip().replace("\\", "/")
    if os.path.isabs(candidate) or (len(candidate) > 1 and candidate[1] == ":"):
        raise PolicyError(
            f"Asset path must be relative to the pack directory: {relative!r}",
            pack=pack_name or None,
        )

    pack_root = os.path.realpath(pack_dir)
    target = os.path.realpath(os.path.join(pack_root, candidate))
    try:
        inside = os.path.commonpath([pack_root, target]) == pack_root
    except ValueError:
        # Different drives on Windows — cannot share a common path, so it left.
        inside = False
    if not inside:
        raise PolicyError(
            f"Asset path escapes the pack directory: {relative!r}", pack=pack_name or None
        )

    if not target.lower().endswith(_ASSET_SUFFIXES):
        raise PolicyError(
            f"Asset must be a .yml, .yaml, .json or .md file: {relative!r}",
            pack=pack_name or None,
        )
    return target
