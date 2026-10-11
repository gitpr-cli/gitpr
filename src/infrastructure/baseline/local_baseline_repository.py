"""Where the baseline lives on disk, and the two ways it can be unusable.

`.gitpr/baseline.json` is committed with the repository, so this module is the
only place that reads or writes it — one writer means one definition of the
bytes, and the diff a teammate reviews is the diff this wrote.

A file that is merely imperfect is still applied: a bad date on one entry must
not blind the gate for every other finding, and `gitpr baseline validate` is
where a document is judged line by line. Three conditions *do* stop the
classification, and they are the three that change its meaning:

- the checksum does not match — the file was edited outside GitPR (decision 6),
  unless the repository turned that guard off with
  `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH=false`;
- the fingerprint version is not this build's — every fingerprint in it is
  computed under different rules, so matching would be fiction;
- the schema version is not this build's — a file from a newer GitPR may mean
  something this one cannot read.

Each of them leaves `manifest` empty, which every consumer reads as "no
baseline": the run behaves as it would with no file at all, and the caller is
told why rather than being left with a gate that quietly answers for nothing.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

import yaml

from src.domain.baseline import (
    FINGERPRINT_VERSION,
    SCHEMA_VERSION,
    BaselineError,
    BaselineManifest,
    Overrides,
    checksum_matches,
    dump_manifest,
    parse_manifest,
    parse_overrides,
    validate_manifest_dict,
)
from src.infrastructure.policy.local_policy_repository import gitpr_dir
from src.i18n import __

BASELINE_NAME = "baseline.json"
OVERRIDES_NAME = "baseline.overrides.yml"

# The keys in the order a reader wants them: the header, then the entries, with
# the checksum last because it is computed over everything above it. The order
# is cosmetic — the digest is taken over sorted keys — but a committed file is
# read far more often than it is written.
_HEADER_ORDER = (
    "schema_version",
    "fingerprint_version",
    "policy_name",
    "policy_version",
    "gitpr_version",
    "created_at",
    "updated_at",
)


@dataclass
class BaselineSnapshot:
    """What the repository knows about its baseline right now.

    `manifest` is None in three different situations — no file, a file that
    cannot be read, a file that cannot be trusted — and `exists` plus `problems`
    is what tells them apart.
    """

    path: str
    manifest: BaselineManifest | None = None
    problems: list[str] = field(default_factory=list)
    exists: bool = False
    checksum_ok: bool = True

    @property
    def is_usable(self) -> bool:
        """Whether the classification may apply this manifest."""
        return self.manifest is not None

    def first_problem(self) -> str:
        """The line to show when there is something to say, or an empty string."""
        return self.problems[0] if self.problems else ""


def baseline_path(repo_path: str | None = None, path: str | None = None) -> str:
    """``<repo>/.gitpr/baseline.json``, or an explicit path when given one."""
    if path:
        return path
    return os.path.join(gitpr_dir(repo_path), BASELINE_NAME)


def overrides_path(repo_path: str | None = None, path: str | None = None) -> str:
    """``<repo>/.gitpr/baseline.overrides.yml`` — versioned with the repository."""
    if path:
        return path
    return os.path.join(gitpr_dir(repo_path), OVERRIDES_NAME)


def read_baseline(
    repo_path: str | None = None,
    path: str | None = None,
    fingerprint_version: str | None = FINGERPRINT_VERSION,
    require_checksum: bool = True,
) -> BaselineSnapshot:
    """Reads the baseline and says whether it may be applied.

    *require_checksum=False* is `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH`
    turned off: a divergent digest stops being fatal, and the manifest is applied
    even though the problem is still reported on the snapshot. The other two
    conditions have no such switch — a file fingerprinted under another version
    of the algorithm cannot be matched against, and one written by a newer
    schema may mean something this build cannot read.
    """
    target = baseline_path(repo_path, path)
    snapshot = BaselineSnapshot(path=target)
    if not os.path.isfile(target):
        return snapshot
    snapshot.exists = True

    try:
        data = _read_json(target)
    except (OSError, ValueError) as error:
        snapshot.problems.append(
            __("{path} is not valid JSON: {error}", path=target, error=error)
        )
        return snapshot

    snapshot.checksum_ok = _checksum_ok(data)
    snapshot.problems = validate_manifest_dict(data, fingerprint_version)
    if _blocking_problems(data, fingerprint_version, snapshot.checksum_ok, require_checksum):
        # The problems stay on the snapshot: the caller shows why the baseline
        # was ignored instead of only saying that it was.
        return snapshot

    try:
        snapshot.manifest = parse_manifest(data)
    except BaselineError as error:
        snapshot.problems.append(str(error))
    return snapshot


def read_manifest(
    repo_path: str | None = None,
    path: str | None = None,
    fingerprint_version: str | None = FINGERPRINT_VERSION,
    require_checksum: bool = True,
) -> tuple[BaselineManifest | None, list[str]]:
    """The manifest and every problem found in it — the shape `validate` prints."""
    snapshot = read_baseline(repo_path, path, fingerprint_version, require_checksum)
    return snapshot.manifest, snapshot.problems


def read_manifest_raw(
    repo_path: str | None = None, path: str | None = None
) -> tuple[BaselineManifest | None, list[str]]:
    """The manifest as the file holds it, ignoring whether it may be applied.

    The repair path, and the only reader that skips the three conditions:
    `gitpr baseline update --recompute` has to see what is in a file
    `read_baseline` refuses, in order to keep the decisions a human wrote
    there, and `create` reads the file it is about to replace so it can report
    the suppressions it would drop. Every other reader goes through
    `read_baseline`, which is what keeps those conditions meaningful.
    """
    target = baseline_path(repo_path, path)
    if not os.path.isfile(target):
        return None, []
    try:
        data = _read_json(target)
    except (OSError, ValueError) as error:
        return None, [__("{path} is not valid JSON: {error}", path=target, error=error)]
    try:
        # No version is handed to the validation: the caller is repairing the
        # file, so judging its version here would refuse the very case it came
        # for. What the validation *is* good for still applies — the shape.
        return parse_manifest(data), validate_manifest_dict(data, None)
    except BaselineError as error:
        return None, [str(error)]


def write_manifest(
    manifest: BaselineManifest,
    repo_path: str | None = None,
    path: str | None = None,
) -> str:
    """Writes the baseline atomically and returns the path written.

    Atomic because the file is read by every later run: a truncated baseline
    would answer for nothing until someone deleted it by hand. The temporary
    file is created next to the target so `os.replace` is a rename within one
    filesystem, and it is removed if anything fails between the two.
    """
    target = baseline_path(repo_path, path)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)

    data = dump_manifest(manifest)
    ordered: dict[str, Any] = {key: data[key] for key in _HEADER_ORDER}
    ordered["entries"] = data["entries"]
    ordered["checksum"] = data["checksum"]
    text = json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"

    temporary = f"{target}.tmp"
    try:
        with open(temporary, "w", encoding="utf-8", errors="replace", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, target)
    except OSError:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return target


def read_overrides(
    repo_path: str | None = None, path: str | None = None
) -> tuple[Overrides, str]:
    """The validated override layers and the path they came from.

    A file that is not there is an empty layer, not an error. A file that is
    there and malformed raises: the caller has to name it, because silently
    dropping a decision a human wrote is the one outcome this feature exists to
    prevent.
    """
    target = overrides_path(repo_path, path)
    if not os.path.isfile(target):
        return Overrides(), target
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as handle:
            data = yaml.safe_load(handle)
        return parse_overrides(data), target
    except BaselineError as error:
        # The path is in the message and not only in the attribute: the caller
        # that stops the run shows what it was handed, and "a suppression needs
        # a reason" without the file it came from is a bug report, not an answer.
        raise BaselineError(f"{target}: {error}", path=target) from error
    except yaml.YAMLError as error:
        raise BaselineError(
            __("{path} is not valid YAML: {error}", path=target, error=error), path=target
        ) from error


def write_overrides(
    overrides: Overrides,
    repo_path: str | None = None,
    path: str | None = None,
) -> str:
    """Writes the overrides file atomically and returns the path written.

    Written from the parsed layers rather than edited in place: appending text
    to a document with two lists is how a file stops being valid YAML, and this
    file is read by the classification on every run. What that costs is
    comments — a file this writes has none — and the two commands that write it
    (`baseline suppress` for a scope wider than one finding, `unsuppress` to take
    one back) are the ones that would otherwise leave a document nobody can
    parse behind.

    A layer with nothing left in it is written as an empty list rather than
    dropped: the file records that the layer exists and is empty, which is a
    different statement from a file that was never written.
    """
    target = overrides_path(repo_path, path)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)

    text = yaml.safe_dump(
        overrides_document(overrides),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )

    temporary = f"{target}.tmp"
    try:
        with open(temporary, "w", encoding="utf-8", errors="replace", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, target)
    except OSError:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return target


def overrides_document(overrides: Overrides) -> dict[str, Any]:
    """The YAML document an `Overrides` is written as, and read back from.

    One definition for both directions: the command that adds a suppression
    merges into this document and re-validates it as a whole, so what it writes
    is exactly what `read_overrides` parses. A key that carries nothing is
    dropped rather than dumped as `null` — nobody wants to review a file full of
    `by: null`.
    """
    return {
        "overrides": {
            "suppressions": [
                _without_empty(item.to_dict()) for item in overrides.suppressions
            ],
            "accepted_debt": [
                _without_empty(item.to_dict()) for item in overrides.accepted_debt
            ],
        }
    }


def _without_empty(data: dict[str, Any]) -> dict[str, Any]:
    """The mapping without the keys that carry nothing, so no `null` is written."""
    return {key: value for key, value in data.items() if value is not None}


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return json.load(handle)


def _checksum_ok(data: Any) -> bool:
    """Whether the recorded checksum is the one the content produces."""
    if not isinstance(data, dict) or not data.get("checksum"):
        return False
    return checksum_matches(data)


def _blocking_problems(
    data: Any,
    fingerprint_version: str | None,
    checksum_ok: bool,
    require_checksum: bool = True,
) -> bool:
    """The three conditions that make the file unusable rather than imperfect."""
    if not isinstance(data, dict):
        return True
    if not checksum_ok and require_checksum:
        return True
    if fingerprint_version and str(data.get("fingerprint_version") or "") != str(
        fingerprint_version
    ):
        return True
    return _recorded_schema_version(data) != SCHEMA_VERSION


def _recorded_schema_version(data: dict[str, Any]) -> int | None:
    """The schema the file declares, or None when it declares nothing readable.

    A hand-edited ``"schema_version": "one"`` is not this build's schema, and the
    answer to it is the same refusal as any other version — the file is not
    applied and `validate` names the problem. Raising on it instead would be a
    traceback where the whole point of the validator is to hand back a sentence.
    """
    try:
        return int(data.get("schema_version") or 0)
    except (TypeError, ValueError):
        return None
