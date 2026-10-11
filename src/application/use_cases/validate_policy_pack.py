"""Use case: answer "what does this pack actually do?" without applying it.

``gitpr policy validate`` is the command a pack author runs before sharing one
and the command a user runs before trusting one, so it has to answer in full
even when the pack is broken: a validator that stops at the first error makes
fixing a manifest a game of whack-a-mole.

The whole check is offline and side-effect free. It reads files, never a
subprocess and never the network — a pack is text somebody else wrote, and
validating it must not run anything it contains.

The report is a plain dict because it is rendered twice: as a terminal report
and as ``--format json`` for CI.
"""

import os
from typing import Any

from src.domain.policy.policy_manifest import running_gitpr_version
from src.domain.policy.policy_resolver import (
    check_severity_overrides_resolve,
    compose_policy,
    resolve_graph,
)
from src.domain.policy.policy_types import (
    PolicyError,
    PolicySource,
)
from src.i18n import __
from src.infrastructure.policy.policy_pack_loader import (
    load_pack_at,
    load_pack_by_reference,
    make_loader,
)

# A dependency target looks like "name" or "name@range"; the range defaults to
# "any version", which is what a bare name means.
_DEFAULT_RANGE = ">=0.0.0"


def parse_pack_target(target: str) -> str:
    """Normalises a validate/use target into either a path or a ``name@range``.

    A target that names a directory on disk becomes an absolute path — that is
    how a pack under construction is validated. Anything else is a reference,
    with the split taken at the *last* ``@`` so a range may contain one.
    """
    candidate = os.path.abspath(os.path.expanduser(target))
    if os.path.isdir(candidate):
        return candidate
    return target.strip()


def split_reference(reference: str) -> tuple[str, str]:
    """``name@range`` → ``(name, range)``; a bare name means any version."""
    if "@" in reference:
        name, version_range = reference.rsplit("@", 1)
        return name.strip(), version_range.strip() or _DEFAULT_RANGE
    return reference.strip(), _DEFAULT_RANGE


def _blank_report(target: str) -> dict[str, Any]:
    return {
        "target": target,
        "ok": False,
        "path": None,
        "source": None,
        "pack": None,
        "schema": {},
        "skills": [],
        "linter": {},
        "risk": {},
        "pr": {},
        "commit": {},
        "protected_paths": [],
        "dependencies": [],
        "baseline": {"suppressions": [], "accepted_debt": []},
        "errors": [],
        "warnings": [],
    }


def _resolve_target(target: str, repo_path: str | None) -> Any:
    normalised = parse_pack_target(target)
    if os.path.isdir(normalised):
        return load_pack_at(normalised, PolicySource.LOCAL_PATH)
    name, version_range = split_reference(normalised)
    return load_pack_by_reference(name, version_range, repo_path)


def _known_rule_names(packs: list[Any]) -> set[str]:
    """Every rule name an override could legitimately name.

    The project rules and the global plugins come from ``load_linter_rules()`` —
    the same function the linter itself calls.

    The embedded secret ruleset is added **unconditionally**, even when
    ``GITPR_LINTER_SECURITY`` has it switched off locally. The question this
    answers is "would this name resolve on a stock GitPR?", which is what a pack
    author and a team adopting a pack need to know; a local toggle must not turn
    a shared pack into a validation error. At runtime the same condition is
    reported as a warning instead, so switching the ruleset off degrades rather
    than breaks.
    """
    from src.config import load_linter_rules
    from src.security_ruleset import SECURITY_RULES

    names: set[str] = set()
    for rule in list(load_linter_rules()) + list(SECURITY_RULES):
        if isinstance(rule, dict) and rule.get("name"):
            names.add(str(rule["name"]))
    for pack in packs:
        for rule in pack.rules:
            if rule.get("name"):
                names.add(str(rule["name"]))
    return names


def _describe_skills(manifest: Any) -> tuple[list[dict], list[str]]:
    from src.config import skill_file_status

    skills: list[dict] = []
    warnings: list[str] = []
    for skill in manifest.skills:
        context = skill.additional_context or ""
        state, _detail = skill_file_status(skill.skill_name)
        skills.append(
            {
                "name": skill.skill_name,
                "characters": len(context),
                "has_local_file": state != "missing",
            }
        )
        if not context.strip():
            warnings.append(
                __(
                    "skills.{skill} declares no additional_context, so the pack does "
                    "nothing for that skill. Remove the entry or add context to it.",
                    skill=skill.skill_name,
                )
            )
    return skills, warnings


def validate_policy_pack(target: str, repo_path: str | None = None) -> dict[str, Any]:
    """Everything that can be said about *target* before it is applied.

    *target* is a pack name (``gitpr/laravel-quality``), a name with a range
    (``gitpr/laravel-quality@^1.0.0``), or a directory holding a ``policy.yml``.
    """
    report = _blank_report(target)

    try:
        root = _resolve_target(target, repo_path)
    except PolicyError as error:
        report["errors"].append(error.message)
        return report

    manifest = root.manifest
    report["path"] = root.reference.path
    report["source"] = root.reference.source.value
    report["pack"] = {
        "name": manifest.name,
        "version": manifest.version,
        "tag": root.tag,
        "checksum": root.reference.checksum,
    }
    report["schema"] = {
        "schema_version": manifest.schema_version,
        "min_gitpr_version": manifest.min_gitpr_version,
        "gitpr_version": running_gitpr_version(),
        # Reaching this line means parse_manifest accepted it, which is where the
        # check runs — reported rather than re-derived so there is one verdict.
        "gitpr_compatible": True,
        "description": manifest.description,
        "license": manifest.license,
        "authors": list(manifest.authors),
    }
    report["protected_paths"] = list(manifest.protected_paths)
    report["pr"] = dict(manifest.pr)
    report["commit"] = dict(manifest.commit)
    # Reported, not re-checked: reaching this line means `parse_manifest`
    # accepted the block, which is where the entries went through the same
    # validators a hand-edited `baseline.overrides.yml` does.
    report["baseline"] = {
        "suppressions": list(manifest.baseline.get("suppressions", [])),
        "accepted_debt": list(manifest.baseline.get("accepted_debt", [])),
    }
    report["risk"] = {
        key: value for key, value in manifest.risk.items() if not key.startswith("_")
    }

    skills, skill_warnings = _describe_skills(manifest)
    report["skills"] = skills
    report["warnings"].extend(skill_warnings)

    # --- graph -----------------------------------------------------------------
    try:
        packs = resolve_graph(root, make_loader(repo_path))
    except PolicyError as error:
        report["errors"].append(error.message)
        return report

    by_name = {pack.reference.name: pack for pack in packs}
    for dependency in manifest.dependencies:
        resolved = by_name.get(dependency.name)
        report["dependencies"].append(
            {
                "name": dependency.name,
                "range": dependency.version,
                "resolved": resolved.reference.version if resolved else None,
            }
        )

    # --- linter ----------------------------------------------------------------
    # Reported across the whole graph rather than the root alone: what matters is
    # the rules and the levels that will actually be in force, and a dependency
    # pack contributes both.
    rule_names: list[str] = []
    rules_file = None
    rules_file_found = False
    for pack in packs:
        if pack.manifest.rules_file and not rules_file:
            rules_file = pack.manifest.rules_file
        rules_file_found = rules_file_found or bool(pack.rules)
        for rule in pack.rules:
            if rule.get("name") and str(rule["name"]) not in rule_names:
                rule_names.append(str(rule["name"]))
    report["linter"] = {
        "rules_file": rules_file,
        "rules_file_found": rules_file_found,
        "rules_count": len(rule_names),
        "rule_names": sorted(rule_names),
        "packs_contributing_rules": [
            pack.reference.name for pack in packs if pack.rules
        ],
        "severity_overrides": [
            {
                "rule_name": override.rule_name,
                "level": override.level,
                "reason": override.reason,
                "weakens_the_gate": override.weakens_the_gate,
                "from": pack.reference.name,
            }
            for pack in packs
            for override in pack.manifest.severity_overrides
        ],
    }

    # --- composition -----------------------------------------------------------
    try:
        policy = compose_policy(packs)
        report["warnings"].extend(policy.warnings)
        check_severity_overrides_resolve(
            policy.severity_overrides,
            _known_rule_names(packs),
            manifest.name,
        )
    except PolicyError as error:
        report["errors"].append(error.message)

    report["ok"] = not report["errors"]
    return report
