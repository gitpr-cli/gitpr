"""Recording and clearing a decision about a finding.

`gitpr baseline suppress` and `gitpr baseline unsuppress` are the only commands
that write a human's decision into the record, and they are the reason an entry
carries the `suppressed`/`suppression_*` fields at all: §5.4 of the spec reads a
fingerprint that is present *and suppressed* as `ignored`, which is a state that
has to live somewhere the classification reads before it decides.

The one design decision this module makes is *where* each scope is written, and
it follows from how far the scope reaches:

- a decision about **one finding** is recorded on that finding's entry in
  `.gitpr/baseline.json`, which is the file the spec points at ("atualizar
  baseline com provenance") and the only one whose entries carry a status;
- a decision that has to reach past the findings that exist today — a whole
  rule, a file, a line range — is recorded in `.gitpr/baseline.overrides.yml`,
  the file whose schema carries the four scopes and whose suppressions the
  comparator matches against every finding, including ones with no entry yet.

Writing a rule scope onto one entry instead would record an intent the
classification does not apply, and a record that overstates itself is worse than
no record.

Nothing here validates by hand. The three decisions are built as raw mappings
and handed to `validate_suppression`/`validate_debt`, so a command cannot write
a line that `gitpr baseline validate` would then call a defect — the same
validators a hand-edited file goes through.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.domain.baseline import (
    AcceptedDebt,
    BaselineEntry,
    BaselineError,
    BaselineStatus,
    Overrides,
    Suppression,
    SuppressionScope,
    apply_overrides,
    match_suppression,
    parse_overrides,
    resolve_fingerprint_prefix,
    validate_debt,
    validate_suppression,
)
from src.i18n import __
from src.infrastructure.baseline.local_baseline_repository import (
    OVERRIDES_NAME,
    BaselineSnapshot,
    overrides_document,
    read_baseline,
    read_overrides,
    write_manifest,
    write_overrides,
)

PROVENANCE_COMMAND_SUPPRESS = "baseline suppress"
PROVENANCE_COMMAND_UNSUPPRESS = "baseline unsuppress"

# How the domain prefixes the origin of a decision that came from a policy pack
# (`policy:<name>`). A decision with it lives in the pack, not in this repo.
_POLICY_ORIGIN = "policy:"

# The scopes that can be recorded on one entry. Everything wider belongs to a
# file the classification matches against every finding — see the module
# docstring.
_ENTRY_SCOPES = (SuppressionScope.FINDING,)


@dataclass
class SuppressResult:
    """What suppressing a finding wrote, ready to be printed.

    ``entry`` and ``override`` are mutually exclusive by construction, and which
    one is set is exactly what tells the caller which file changed.
    """

    path: str
    entry: BaselineEntry | None = None
    override: Suppression | AcceptedDebt | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_debt(self) -> bool:
        """Whether what was recorded is accepted debt rather than a suppression."""
        return isinstance(self.override, AcceptedDebt) or (
            self.entry is not None and self.entry.is_debt()
        )


@dataclass
class UnsuppressResult:
    """What unsuppressing took back, and what it could not.

    ``removed`` is what the command deleted. ``warnings`` names the decisions
    that still cover the finding because they are wider than it: those live in
    the overrides file as a statement about a rule, a file or a range, and
    deleting one of them because a single finding was named would silently
    un-suppress every other finding it covered.
    """

    path: str
    entry: BaselineEntry | None = None
    removed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def suppress_finding(
    identifier: str,
    *,
    reason: str,
    scope: SuppressionScope = SuppressionScope.FINDING,
    debt: bool = False,
    owner: str | None = None,
    due_date: str | None = None,
    repo_path: str | None = None,
    configured_path: str | None = None,
    by: str | None = None,
    today: date | None = None,
) -> SuppressResult:
    """Records the decision about the finding *identifier* names.

    *identifier* is a fingerprint or a unique prefix of one (`sha256:ab12cd34`),
    the id `gitpr baseline show` prints. Raises ``BaselineError`` for anything
    the caller can fix: no baseline, an ambiguous id, a missing reason, an owner
    missing from accepted debt, or a debt assigned to something wider than a
    single finding.

    *configured_path* is `GITPR_BASELINE_PATH`, the file the decision is written
    to — the same one `load_baseline` reads back, so a decision cannot land in a
    file the classification never opens.
    """
    snapshot = _applicable_baseline(repo_path, configured_path)
    entry = _resolve_entry(snapshot, identifier)
    reference = today or date.today()
    author = by or _git_author()
    provenance = _provenance(PROVENANCE_COMMAND_SUPPRESS)

    if debt:
        if scope is not SuppressionScope.FINDING:
            raise BaselineError(
                __(
                    "Accepted debt is always about one finding: '{scope}' scope "
                    "belongs to a suppression. Drop --debt or drop --scope.",
                    scope=scope.value,
                )
            )
        accepted = validate_debt(
            {
                "fingerprint": entry.fingerprint,
                "owner": owner,
                "reason": reason,
                "due_date": due_date,
            }
        )
        _clear_decision(entry)
        entry.status = BaselineStatus.ACCEPTED_DEBT
        entry.accepted_debt_owner = accepted.owner
        entry.accepted_debt_reason = accepted.reason
        entry.accepted_debt_due_date = accepted.due_date
        entry.provenance = provenance
        path = write_manifest(
            _restamped(snapshot, provenance), repo_path, configured_path
        )
        return SuppressResult(path=path, entry=entry)

    raw = _suppression_document(entry, scope, reason, author, reference)
    suppression = validate_suppression(raw)

    if scope in _ENTRY_SCOPES:
        _clear_decision(entry)
        entry.status = BaselineStatus.IGNORED
        entry.suppressed = True
        entry.suppression_reason = suppression.reason
        entry.suppression_scope = suppression.scope
        entry.suppressed_by = suppression.by
        entry.suppressed_at = suppression.date
        entry.provenance = provenance
        path = write_manifest(
            _restamped(snapshot, provenance), repo_path, configured_path
        )
        return SuppressResult(path=path, entry=entry)

    # A scope wider than one finding, recorded where it is applied.
    if not _local_overrides_allowed():
        raise BaselineError(
            __(
                "This repository does not read {name} — "
                "GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES is off, so a '{scope}' "
                "suppression would be written and never applied.",
                name=OVERRIDES_NAME,
                scope=scope.value,
            )
        )
    stored, _ = read_overrides(repo_path)
    document = overrides_document(stored)
    document["overrides"]["suppressions"].append(raw)
    # The whole document is re-validated, not just the line added to it: a
    # duplicate fingerprint and a malformed neighbour are both defects of the
    # file this is about to write.
    merged = parse_overrides(document)
    path = write_overrides(merged, repo_path)
    return SuppressResult(path=path, override=merged.suppressions[-1])


def unsuppress_finding(
    identifier: str,
    *,
    repo_path: str | None = None,
    configured_path: str | None = None,
) -> UnsuppressResult:
    """Takes back what `suppress` recorded for *identifier*, and says what it left.

    Removes the decision on the entry and any override bound to that exact
    fingerprint. A wider suppression that also covers the finding is *reported*,
    never removed: it is a statement about a rule, a file or a range, and it is
    edited where it lives — the repository's overrides file, or the baseline
    block of the pack that declared it.
    """
    snapshot = _applicable_baseline(repo_path, configured_path)
    entry = _resolve_entry(snapshot, identifier)
    warnings: list[str] = []
    removed: list[str] = []

    stored, overrides_file = read_overrides(repo_path)
    layers = _in_force(stored)
    bound = [item for item in stored.suppressions if item.fingerprint == entry.fingerprint]
    if bound:
        stored.suppressions = [
            item for item in stored.suppressions if item.fingerprint != entry.fingerprint
        ]
        removed.extend(item.scope.value for item in bound)

    debts = [item for item in stored.accepted_debt if item.fingerprint == entry.fingerprint]
    if debts:
        stored.accepted_debt = [
            item for item in stored.accepted_debt if item.fingerprint != entry.fingerprint
        ]
        removed.append("accepted_debt")

    on_entry = entry.suppressed or entry.is_debt()
    if on_entry:
        removed.append("entry")

    covering = _wider_suppressions(layers, entry)
    if not removed:
        # The finding *is* silenced — by a statement about its rule, its file or
        # a range of lines. Saying "nothing suppresses it" would be false, and
        # deleting the decision because one finding was named would un-silence
        # every other finding it covers.
        if covering:
            wider = covering[0]
            where, path = _decision_home(wider, overrides_file)
            raise BaselineError(
                __(
                    "{identifier} is covered by a '{scope}' suppression for "
                    "'{identity}' in {where} — a decision about every finding of that "
                    "rule, so it is removed by editing the file.",
                    identifier=identifier,
                    scope=wider.scope.value,
                    identity=wider.rule_id or entry.identity(),
                    where=where,
                ),
                path=path,
            )
        raise BaselineError(
            __(
                "Nothing in the baseline suppresses {identifier} — there is no "
                "decision to take back.",
                identifier=identifier,
            )
        )

    for covering in covering:
        where, _ = _decision_home(covering, overrides_file)
        warnings.append(
            __(
                "A '{scope}' suppression for '{identity}' still covers this "
                "finding. It is removed by editing {where}, not by this command: "
                "it is a statement about every finding of that rule.",
                scope=covering.scope.value,
                identity=covering.rule_id,
                where=where,
            )
        )

    manifest_path = snapshot.path
    if on_entry:
        _clear_decision(entry)
        entry.status = BaselineStatus.EXISTING
        entry.provenance = _provenance(PROVENANCE_COMMAND_UNSUPPRESS)
        manifest_path = write_manifest(
            _restamped(snapshot, entry.provenance), repo_path, configured_path
        )

    if bound or debts:
        write_overrides(stored, repo_path)

    return UnsuppressResult(
        path=manifest_path, entry=entry, removed=removed, warnings=warnings
    )


def _applicable_baseline(
    repo_path: str | None, configured_path: str | None = None
) -> BaselineSnapshot:
    """The snapshot a write is allowed to touch, or the reason there is none.

    A file that cannot be applied is refused rather than edited: rewriting one
    would launder whatever made it unusable into a fresh checksum, which is the
    one thing the checksum exists to prevent.
    """
    snapshot = read_baseline(repo_path, configured_path)
    if not snapshot.exists:
        raise BaselineError(
            __(
                "There is no baseline in this repository — run "
                "'gitpr baseline create' first.",
                path=snapshot.path,
            ),
            path=snapshot.path,
        )
    if not snapshot.is_usable:
        raise BaselineError(
            __(
                "{path} cannot be edited: {problem} Run 'gitpr baseline update "
                "--recompute' to rebuild it from the working tree.",
                path=snapshot.path,
                problem=snapshot.first_problem(),
            ),
            path=snapshot.path,
        )
    return snapshot


def _resolve_entry(snapshot: BaselineSnapshot, identifier: str) -> BaselineEntry:
    """The entry the id names, refusing an id that names none of them."""
    manifest = snapshot.manifest
    assert manifest is not None
    fingerprint = resolve_fingerprint_prefix(
        identifier, [entry.fingerprint for entry in manifest.entries]
    )
    entry = manifest.entry_for(fingerprint)
    assert entry is not None
    if entry.status is BaselineStatus.RESOLVED:
        raise BaselineError(
            __(
                "{fingerprint} was resolved — {path} in {file} is not in the tree "
                "any more, so there is nothing to decide about it.",
                fingerprint=fingerprint,
                path=entry.file_path,
                file=entry.rule_id or entry.category,
            )
        )
    return entry


def _suppression_document(
    entry: BaselineEntry,
    scope: SuppressionScope,
    reason: str,
    author: str,
    reference: date,
) -> dict[str, Any]:
    """The raw suppression this scope means for this entry.

    A `finding` scope names the fingerprint; the wider ones name the rule
    identity the entry was fingerprinted under, which is the rule's id when it
    has one and its category when it does not — so the AI's prose findings can
    be silenced by category like anything else.
    """
    document: dict[str, Any] = {
        "scope": scope.value,
        "reason": reason,
        "by": author,
        "date": reference.isoformat(),
    }
    if scope is SuppressionScope.FINDING:
        document["fingerprint"] = entry.fingerprint
        return document

    document["rule_id"] = entry.identity()
    if scope is SuppressionScope.RULE:
        return document

    document["file_path"] = entry.file_path
    if scope is SuppressionScope.FILE:
        return document

    document["line_start"] = entry.line_start
    document["line_end"] = entry.line_end
    return document


def _in_force(stored: Overrides) -> Overrides:
    """The repository's layers plus the active pack's, in the gate's own order."""
    from src.application.use_cases.baseline_gate import pack_layers

    pack = pack_layers()
    return stored if pack is None else apply_overrides(stored, pack=pack)


def _wider_suppressions(layers: Overrides, entry: BaselineEntry) -> list[Suppression]:
    """The suppressions in force that cover *entry* and are wider than one finding."""
    matched = match_suppression(
        [
            suppression
            for suppression in layers.suppressions
            if suppression.scope is not SuppressionScope.FINDING
        ],
        fingerprint=entry.fingerprint,
        identity=entry.identity(),
        file_path=entry.file_path,
        line_start=entry.line_start,
        line_end=entry.line_end,
    )
    return [matched] if matched is not None else []


def _decision_home(suppression: Suppression, overrides_file: str) -> tuple[str, str | None]:
    """Where a decision this command will not remove is edited, and its path.

    A pack's decision is not in the repository at all: it is in the block of the
    pack the repository activated, and it is edited there. Naming
    ``baseline.overrides.yml`` for it would send the reader to a file that does
    not contain the line.
    """
    origin = suppression.origin or ""
    if origin.startswith(_POLICY_ORIGIN):
        pack = origin[len(_POLICY_ORIGIN) :]
        return (
            __("the baseline block of the policy pack {pack}", pack=pack),
            None,
        )
    return overrides_file, overrides_file


def _clear_decision(entry: BaselineEntry) -> None:
    """Removes whatever decision the entry carried, leaving its history alone."""
    entry.suppressed = False
    entry.suppression_reason = None
    entry.suppression_scope = None
    entry.suppressed_by = None
    entry.suppressed_at = None
    entry.accepted_debt_owner = None
    entry.accepted_debt_due_date = None
    entry.accepted_debt_reason = None


def _restamped(snapshot: BaselineSnapshot, provenance: dict[str, Any]):
    """The manifest with one entry's decision changed, stamped as this command."""
    from src.application.use_cases.create_baseline import stamp_manifest

    manifest = snapshot.manifest
    assert manifest is not None
    return stamp_manifest(
        manifest.entries,
        previous=manifest,
        command=provenance["command"],
    )


def _provenance(command: str) -> dict[str, Any]:
    from src.application.use_cases.create_baseline import PROVENANCE_ORIGIN, policy_tag

    return {"origin": PROVENANCE_ORIGIN, "command": command, "policy": policy_tag()}


def _git_author() -> str:
    """Who is recording the decision, from the git identity in force."""
    from src.cache import get_git_user_info

    return get_git_user_info()[0] or "unknown"


def _local_overrides_allowed() -> bool:
    """Whether this repository reads the overrides file at all."""
    from src.config import get_baseline_settings

    return get_baseline_settings()["allow_local_overrides"]
