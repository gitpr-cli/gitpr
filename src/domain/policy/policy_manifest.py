"""Parsing and strict validation of a ``policy.yml``.

The schema is **closed**: a key this module does not know is an error, never a
silently ignored line. That is a deliberate inversion of the plugin linter's
precedent, where a third-party YAML enters through ``load_linter_rules()`` with
no validation at all (and where, as ADR-007 recorded, ``severity`` was quietly
accepted and ignored). A pack that wants to change behaviour has to say so in a
key that is understood.

The manifest text is also scanned with the linter's own secret rules before
anything else happens — a pack is shared between repositories, so a credential
committed into one is a credential published. Reusing SECURITY_RULES keeps a
single definition of "looks like a secret" in the project.

Only ``policy.yml`` is scanned. The declared assets are rule catalogues, whose
regexes legitimately look like the things they hunt for.
"""

import re
from typing import Any

from src.domain.policy.policy_compatibility import (
    check_gitpr_compatibility,
    parse_semver,
    parse_specifier,
    validate_pack_name,
)
from src.domain.policy.policy_types import (
    RULE_LEVELS,
    PackReference,
    PolicyError,
    PolicyManifest,
    PolicySource,
    SeverityOverride,
    SkillPolicy,
)
from src.i18n import __

SCHEMA_VERSION = 1


def running_gitpr_version() -> str:
    """The version of the GitPR doing the reading.

    Imported lazily: ``src/updater.py`` pulls ``requests`` and defines the
    network-checking entry points at module level, and the domain package is
    imported by tests that must not need either.
    """
    from src.updater import __version__

    return __version__

_OVERRIDES_KEYS = {
    "severity_overrides",
    "risk",
    "pr",
    "commit",
    "protected_paths",
    "skills",
}

# Keys whose value is an {add: [...], remove: [...]} pair. Removal is spelled
# out rather than implied by omission, because dropping a protected path or a
# required section is exactly the kind of change that has to be visible in a
# diff at review time.
_ADDITIVE_KEYS = {"add", "remove"}

_TOP_LEVEL_KEYS = {
    "schema_version",
    "name",
    "version",
    "description",
    "min_gitpr_version",
    "license",
    "authors",
    "extends",
    "skills",
    "linter",
    "risk",
    "pr",
    "commit",
    "protected_paths",
    "baseline",
}
_SKILL_KEYS = {"additional_context"}
_LINTER_KEYS = {"rules_file", "severity_overrides"}
_OVERRIDE_KEYS = {"rule_name", "level", "reason"}
_BASELINE_KEYS = {"suppressions", "accepted_debt"}
_EXTENDS_KEYS = {"name", "version"}
_RISK_KEYS = {"critical_paths", "weights", "thresholds", "test_patterns"}
_PR_KEYS = {"required_sections"}
_COMMIT_KEYS = {"allowed_types"}

# The only threshold keys the risk engine reads, and the only weight keys it
# knows. Validating against RiskSignal turns a typo into an error instead of a
# silently dropped weight.
_THRESHOLD_KEYS = ("low_max", "medium_max", "high_max")


def find_secret(text: str) -> str | None:
    """The name of the first SECURITY_RULES rule *text* trips, or None.

    Matched line by line, the way the linter engine does it, so a pattern
    anchored at the start of a line behaves the same here as it does there.
    """
    from src.security_ruleset import SECURITY_RULES

    lines = text.splitlines()
    for rule in SECURITY_RULES:
        pattern = rule.get("regex")
        if not pattern:
            continue
        try:
            compiled = re.compile(pattern)
        except re.error:
            continue
        for line in lines:
            if compiled.search(line):
                return rule.get("name", "secret")
    return None


def _fail(message: str, pack: str = "") -> None:
    raise PolicyError(message, pack=pack or None)


def _check_unknown(mapping: dict, allowed: set[str], where: str, pack: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        _fail(
            __(
                "Pack {pack}: unknown key(s) in {where}: {keys}. The schema is closed — "
                "remove them or check the documentation for the current spelling.",
                pack=pack,
                where=where,
                keys=", ".join(unknown),
            ),
            pack,
        )


def _require_str(data: dict, key: str, pack: str, where: str = "") -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        label = f"{where}.{key}" if where else key
        _fail(__("Pack {pack}: {field} is required and must be a non-empty string.", pack=pack, field=label), pack)
    return value.strip()


def _string_list(value: Any, field: str, pack: str) -> list[str]:
    """A list of non-empty strings, in order, with duplicates removed."""
    if not isinstance(value, list):
        _fail(__("Pack {pack}: {field} must be a list.", pack=pack, field=field), pack)
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            _fail(
                __("Pack {pack}: {field} must contain non-empty strings.", pack=pack, field=field),
                pack,
            )
        cleaned = item.strip()
        if cleaned not in result:
            result.append(cleaned)
    return result


def _parse_extends(data: dict, pack: str, source: PolicySource) -> list[PackReference]:
    entries = data.get("extends")
    if entries is None:
        return []
    if not isinstance(entries, list):
        _fail(__("Pack {pack}: 'extends' must be a list of packs.", pack=pack), pack)

    dependencies: list[PackReference] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            _fail(__("Pack {pack}: each 'extends' entry must be a mapping.", pack=pack), pack)
        _check_unknown(entry, _EXTENDS_KEYS, "extends", pack)
        name = _require_str(entry, "name", pack, "extends")
        version = _require_str(entry, "version", pack, "extends")
        validate_pack_name(name)
        parse_specifier(version, f"extends[{name}].version")
        if name in seen:
            _fail(__("Pack {pack}: {name} is listed twice in 'extends'.", pack=pack, name=name), pack)
        seen.add(name)
        # The real source, path and checksum are filled in by the resolver; a
        # dependency usually lives wherever the dependent pack does.
        dependencies.append(PackReference(name=name, version=version, source=source))
    return dependencies


def _parse_skills(data: dict, pack: str) -> list[SkillPolicy]:
    block = data.get("skills")
    if block is None:
        return []
    if not isinstance(block, dict):
        _fail(__("Pack {pack}: 'skills' must be a mapping of skill name to settings.", pack=pack), pack)

    from src.domain.policy.policy_compatibility import check_skill_name

    skills: list[SkillPolicy] = []
    for skill_name, settings in block.items():
        check_skill_name(skill_name, pack)
        if settings is None:
            settings = {}
        if not isinstance(settings, dict):
            _fail(
                __("Pack {pack}: skills.{skill} must be a mapping.", pack=pack, skill=skill_name),
                pack,
            )
        _check_unknown(settings, _SKILL_KEYS, f"skills.{skill_name}", pack)
        context = settings.get("additional_context")
        if context is not None and not isinstance(context, str):
            _fail(
                __(
                    "Pack {pack}: skills.{skill}.additional_context must be text.",
                    pack=pack,
                    skill=skill_name,
                ),
                pack,
            )
        skills.append(
            SkillPolicy(skill_name=skill_name, additional_context=context or None)
        )
    return skills


def _parse_severity_overrides(data: dict, pack: str) -> list[SeverityOverride]:
    entries = data.get("severity_overrides")
    if entries is None:
        return []
    if not isinstance(entries, list):
        _fail(__("Pack {pack}: linter.severity_overrides must be a list.", pack=pack), pack)

    overrides: list[SeverityOverride] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            _fail(
                __("Pack {pack}: each severity override must be a mapping.", pack=pack), pack
            )
        _check_unknown(entry, _OVERRIDE_KEYS, "linter.severity_overrides", pack)
        rule_name = _require_str(entry, "rule_name", pack, "severity_overrides")
        level = _require_str(entry, "level", pack, "severity_overrides").lower()
        if level not in RULE_LEVELS:
            _fail(
                __(
                    "Pack {pack}: severity override for {rule} uses level {level!r}; "
                    "the engine has only {levels}.",
                    pack=pack,
                    rule=rule_name,
                    level=level,
                    levels=" and ".join(RULE_LEVELS),
                ),
                pack,
            )
        if rule_name in seen:
            _fail(
                __(
                    "Pack {pack}: rule {rule} is overridden twice; keep one entry.",
                    pack=pack,
                    rule=rule_name,
                ),
                pack,
            )
        seen.add(rule_name)
        reason = entry.get("reason")
        if reason is not None and not isinstance(reason, str):
            _fail(__("Pack {pack}: severity override reason must be text.", pack=pack), pack)
        # Lowering a rule from blocking to advising weakens the gate, so it has
        # to say why. Hardening one does not.
        if level == "warning" and not (reason or "").strip():
            _fail(
                __(
                    "Pack {pack}: severity override for {rule} lowers it to 'warning' "
                    "and needs a 'reason' explaining why.",
                    pack=pack,
                    rule=rule_name,
                ),
                pack,
            )
        overrides.append(
            SeverityOverride(rule_name=rule_name, level=level, reason=(reason or "").strip() or None)
        )
    return overrides


def _parse_linter(data: dict, pack: str) -> tuple[str | None, list[SeverityOverride]]:
    block = data.get("linter")
    if block is None:
        return None, []
    if not isinstance(block, dict):
        _fail(__("Pack {pack}: 'linter' must be a mapping.", pack=pack), pack)
    _check_unknown(block, _LINTER_KEYS, "linter", pack)

    rules_file = block.get("rules_file")
    if rules_file is not None:
        if not isinstance(rules_file, str) or not rules_file.strip():
            _fail(__("Pack {pack}: linter.rules_file must be a file name.", pack=pack), pack)
        rules_file = rules_file.strip().replace("\\", "/")
    return rules_file, _parse_severity_overrides(block, pack)


def _parse_risk(data: dict, pack: str) -> dict[str, Any]:
    block = data.get("risk")
    if block is None:
        return {}
    if not isinstance(block, dict):
        _fail(__("Pack {pack}: 'risk' must be a mapping.", pack=pack), pack)
    _check_unknown(block, _RISK_KEYS, "risk", pack)

    from src.domain.risk.risk_types import RiskSignal

    risk: dict[str, Any] = {}

    if "critical_paths" in block:
        risk["critical_paths"] = _string_list(block["critical_paths"], "risk.critical_paths", pack)
    if "test_patterns" in block:
        risk["test_patterns"] = _string_list(block["test_patterns"], "risk.test_patterns", pack)

    if "weights" in block:
        weights = block["weights"]
        if not isinstance(weights, dict):
            _fail(__("Pack {pack}: risk.weights must be a mapping.", pack=pack), pack)
        parsed_weights: dict[str, float] = {}
        for signal_name, value in weights.items():
            try:
                signal = RiskSignal(signal_name)
            except ValueError:
                _fail(
                    __(
                        "Pack {pack}: risk.weights has unknown signal {signal!r}.",
                        pack=pack,
                        signal=signal_name,
                    ),
                    pack,
                )
            try:
                parsed_weights[signal.value] = float(value)
            except (TypeError, ValueError):
                _fail(
                    __(
                        "Pack {pack}: risk.weights.{signal} must be a number.",
                        pack=pack,
                        signal=signal_name,
                    ),
                    pack,
                )
            # Only an explicit mitigating signal may subtract — the same rule
            # load_risk_config() enforces.
            if parsed_weights[signal.value] < 0 and signal is not RiskSignal.TEST_PRESENT:
                _fail(
                    __(
                        "Pack {pack}: risk.weights.{signal} cannot be negative; only "
                        "test_present mitigates.",
                        pack=pack,
                        signal=signal_name,
                    ),
                    pack,
                )
        risk["weights"] = parsed_weights

    if "thresholds" in block:
        thresholds = block["thresholds"]
        if not isinstance(thresholds, dict):
            _fail(__("Pack {pack}: risk.thresholds must be a mapping.", pack=pack), pack)
        unknown = sorted(set(thresholds) - set(_THRESHOLD_KEYS))
        if unknown:
            _fail(
                __(
                    "Pack {pack}: risk.thresholds has unknown key(s) {keys}.",
                    pack=pack,
                    keys=", ".join(unknown),
                ),
                pack,
            )
        parsed_thresholds: dict[str, float] = {}
        for key in _THRESHOLD_KEYS:
            if key not in thresholds:
                continue
            try:
                parsed_thresholds[key] = float(thresholds[key])
            except (TypeError, ValueError):
                _fail(
                    __(
                        "Pack {pack}: risk.thresholds.{setting} must be a number.",
                        pack=pack,
                        setting=key,
                    ),
                    pack,
                )
        ordered = [parsed_thresholds[k] for k in _THRESHOLD_KEYS if k in parsed_thresholds]
        if ordered != sorted(ordered):
            _fail(
                __(
                    "Pack {pack}: risk.thresholds must increase (low_max < medium_max < high_max).",
                    pack=pack,
                ),
                pack,
            )
        risk["thresholds"] = parsed_thresholds

    return risk


def _parse_scalar_block(
    data: dict, key: str, allowed: set[str], list_keys: tuple[str, ...], pack: str
) -> dict[str, Any]:
    block = data.get(key)
    if block is None:
        return {}
    if not isinstance(block, dict):
        _fail(
            __("Pack {pack}: '{setting}' must be a mapping.", pack=pack, setting=key), pack
        )
    _check_unknown(block, allowed, key, pack)
    parsed: dict[str, Any] = {}
    for list_key in list_keys:
        if list_key in block:
            parsed[list_key] = _string_list(block[list_key], f"{key}.{list_key}", pack)
    return parsed


def _parse_baseline(data: dict, pack: str) -> dict[str, list[dict[str, Any]]]:
    """The ``baseline:`` block: the suppressions and debt a pack brings with it.

    Validated by the very validators a hand-edited ``baseline.overrides.yml``
    goes through, and not by a second implementation of the same rules: a pack
    that could declare a suppression without a reason, or accepted debt nobody
    owns, would be a way around the auditability the feature exists for. The
    failure is re-raised as a ``PolicyError`` naming the pack, the half and the
    index, because that is what ``gitpr policy validate`` prints.

    The entries are returned as data, not as the domain's own types: composing
    the layer — and refusing a duplicate fingerprint between two packs — is the
    resolver's job, and it does it through the same ``parse_overrides``.
    """
    block = data.get("baseline")
    if block is None:
        return {}
    if not isinstance(block, dict):
        _fail(__("Pack {pack}: 'baseline' must be a mapping.", pack=pack), pack)
    _check_unknown(block, _BASELINE_KEYS, "baseline", pack)

    from src.domain.baseline import BaselineError, validate_debt, validate_suppression

    parsed: dict[str, list[dict[str, Any]]] = {}
    for key, validator in (
        ("suppressions", validate_suppression),
        ("accepted_debt", validate_debt),
    ):
        items = block.get(key)
        if items is None:
            continue
        if not isinstance(items, list):
            _fail(
                __("Pack {pack}: baseline.{half} must be a list.", pack=pack, half=key),
                pack,
            )
        entries: list[dict[str, Any]] = []
        for index, item in enumerate(items, start=1):
            try:
                entries.append(validator(item).to_dict())
            except BaselineError as error:
                _fail(
                    __(
                        "Pack {pack}: baseline.{half} #{index}: {error}",
                        pack=pack,
                        half=key,
                        index=index,
                        error=error,
                    ),
                    pack,
                )
        if entries:
            parsed[key] = entries
    return parsed


def _parse_additive_block(block: Any, where: str) -> dict[str, list[str]]:
    """An ``{add: [...], remove: [...]}`` pair, with either half optional."""
    if not isinstance(block, dict):
        _fail(
            __(
                "policy.overrides.yml: {where} must use 'add' and 'remove' lists.",
                where=where,
            )
        )
    _check_unknown(block, _ADDITIVE_KEYS, where, "policy.overrides.yml")
    parsed: dict[str, list[str]] = {}
    for half in ("add", "remove"):
        if half in block:
            parsed[half] = _string_list(block[half], f"{where}.{half}", "policy.overrides.yml")
    return parsed


def parse_overrides(data: Any) -> dict[str, Any]:
    """Validates ``.gitpr/policy.overrides.yml`` into the shape the resolver applies.

    A repository's overrides are the highest-precedence declarative input, so
    they get the same closed-schema treatment as a manifest. The file may be
    written under a top-level ``overrides:`` key (matching the documented
    example) or at the root; both are accepted.
    """
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PolicyError(__("policy.overrides.yml must be a YAML mapping."))
    root = data.get("overrides", data)
    if not isinstance(root, dict):
        raise PolicyError(__("policy.overrides.yml: 'overrides' must be a mapping."))
    _check_unknown(root, _OVERRIDES_KEYS, "the overrides file", "policy.overrides.yml")

    parsed: dict[str, Any] = {}

    if "severity_overrides" in root:
        parsed["severity_overrides"] = _parse_severity_overrides(
            {"severity_overrides": root["severity_overrides"]}, "policy.overrides.yml"
        )

    risk = root.get("risk")
    if risk is not None:
        if not isinstance(risk, dict):
            _fail(__("policy.overrides.yml: 'risk' must be a mapping."))
        _check_unknown(risk, _RISK_KEYS, "risk", "policy.overrides.yml")
        parsed_risk: dict[str, Any] = {}
        for key in ("critical_paths", "test_patterns"):
            if key in risk:
                parsed_risk[key] = _parse_additive_block(risk[key], f"risk.{key}")
        for key in ("weights", "thresholds"):
            if key not in risk:
                continue
            values = risk[key]
            if not isinstance(values, dict):
                _fail(
                    __("policy.overrides.yml: risk.{setting} must be a mapping.", setting=key)
                )
            parsed_risk[key] = dict(values)
        parsed["risk"] = parsed_risk

    pr = root.get("pr")
    if pr is not None:
        if not isinstance(pr, dict):
            _fail(__("policy.overrides.yml: 'pr' must be a mapping."))
        _check_unknown(pr, _PR_KEYS, "pr", "policy.overrides.yml")
        if "required_sections" in pr:
            parsed.setdefault("pr", {})["required_sections"] = _parse_additive_block(
                pr["required_sections"], "pr.required_sections"
            )

    commit = root.get("commit")
    if commit is not None:
        if not isinstance(commit, dict):
            _fail(__("policy.overrides.yml: 'commit' must be a mapping."))
        _check_unknown(commit, _COMMIT_KEYS, "commit", "policy.overrides.yml")
        if "allowed_types" in commit:
            parsed.setdefault("commit", {})["allowed_types"] = _parse_additive_block(
                commit["allowed_types"], "commit.allowed_types"
            )

    if "protected_paths" in root:
        parsed["protected_paths"] = _parse_additive_block(
            root["protected_paths"], "protected_paths"
        )

    if "skills" in root:
        skills = root["skills"]
        if not isinstance(skills, dict):
            _fail(__("policy.overrides.yml: 'skills' must be a mapping."))
        from src.domain.policy.policy_compatibility import check_skill_name

        parsed_skills: dict[str, dict[str, str]] = {}
        for skill_name, settings in skills.items():
            check_skill_name(skill_name, "policy.overrides.yml")
            if settings is not None and not isinstance(settings, dict):
                _fail(
                    __(
                        "policy.overrides.yml: skills.{skill} must be a mapping.",
                        skill=skill_name,
                    )
                )
            _check_unknown(settings or {}, _SKILL_KEYS, f"skills.{skill_name}", "policy.overrides.yml")
            context = (settings or {}).get("additional_context")
            if context is not None and not isinstance(context, str):
                _fail(
                    __(
                        "policy.overrides.yml: skills.{skill}.additional_context must be text.",
                        skill=skill_name,
                    )
                )
            parsed_skills[skill_name] = {"additional_context": context or ""}
        parsed["skills"] = parsed_skills

    return parsed


def parse_manifest(
    data: Any,
    pack_dir: str = "",
    raw_text: str = "",
    source: PolicySource = PolicySource.BUNDLED,
    gitpr_version: str | None = None,
) -> PolicyManifest:
    """Validates a parsed ``policy.yml`` and returns the manifest.

    *data* is what ``yaml.safe_load`` produced; *raw_text* is the file as read,
    scanned for credentials. Every failure is a ``PolicyError`` naming the pack
    and the key, so ``gitpr policy validate`` can print it as-is.

    *gitpr_version* is the build to check ``min_gitpr_version`` against, and
    defaults to the running one. Enforcing it here rather than at load time is
    what makes every path agree: listing, validating, resolving and activating a
    pack all go through this function, so an incompatible pack can never be
    silently selected as a candidate for a dependency that has no other option.
    """
    if not isinstance(data, dict):
        raise PolicyError(__("A policy manifest must be a YAML mapping."))

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise PolicyError(__("A policy manifest must declare a 'name'."))
    name = name.strip()
    validate_pack_name(name)

    if raw_text:
        secret_rule = find_secret(raw_text)
        if secret_rule:
            raise PolicyError(
                __(
                    "Pack {pack}: the manifest contains what looks like a credential "
                    "({rule}). Packs are shared — remove it.",
                    pack=name,
                    rule=secret_rule,
                ),
                pack=name,
            )

    _check_unknown(data, _TOP_LEVEL_KEYS, "the manifest", name)

    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise PolicyError(
            __(
                "Pack {pack}: unsupported schema_version {found}; this GitPR reads {expected}.",
                pack=name,
                found=schema_version,
                expected=SCHEMA_VERSION,
            ),
            pack=name,
        )

    version = _require_str(data, "version", name)
    parse_semver(version)
    min_gitpr_version = _require_str(data, "min_gitpr_version", name)
    parse_specifier(min_gitpr_version)
    check_gitpr_compatibility(min_gitpr_version, gitpr_version or running_gitpr_version(), name)

    description = data.get("description", "")
    if description is not None and not isinstance(description, str):
        raise PolicyError(__("Pack {pack}: 'description' must be text.", pack=name), pack=name)

    license_value = data.get("license")
    if license_value is not None and not isinstance(license_value, str):
        raise PolicyError(__("Pack {pack}: 'license' must be text.", pack=name), pack=name)

    authors: list[str] = []
    if data.get("authors") is not None:
        authors = _string_list(data["authors"], "authors", name)

    rules_file, severity_overrides = _parse_linter(data, name)

    protected_paths: list[str] = []
    if data.get("protected_paths") is not None:
        protected_paths = _string_list(data["protected_paths"], "protected_paths", name)

    return PolicyManifest(
        name=name,
        version=version,
        min_gitpr_version=min_gitpr_version,
        schema_version=SCHEMA_VERSION,
        description=(description or "").strip(),
        license=license_value,
        authors=authors,
        dependencies=_parse_extends(data, name, source),
        skills=_parse_skills(data, name),
        rules_file=rules_file,
        severity_overrides=severity_overrides,
        risk=_parse_risk(data, name),
        pr=_parse_scalar_block(data, "pr", _PR_KEYS, ("required_sections",), name),
        commit=_parse_scalar_block(data, "commit", _COMMIT_KEYS, ("allowed_types",), name),
        protected_paths=protected_paths,
        baseline=_parse_baseline(data, name),
    )
