"""Domain package for GitPR policy packs.

A policy pack is a declarative manifest that standardises the quality gate of a
repository across skills, linter rules, risk scoring and PR/commit conventions.
Packs are not skills: they can only configure what GitPR already runs, and every
name they mention is validated against the fixed registry before they activate.

Modules:

- ``policy_types`` — the value contracts (manifest, reference, effective policy);
- ``policy_manifest`` — parsing and closed-schema validation of ``policy.yml``
  and ``.gitpr/policy.overrides.yml``;
- ``policy_compatibility`` — SemVer ranges, skill names, asset path containment;
- ``policy_resolver`` — dependency graph, precedence, composition, provenance;
- ``policy_checksum`` — the SHA-256 the lockfile records.

See docs/plans/glossary-policy-packs.md for the vocabulary and
docs/plans/ADR-011-policy-packs.md for the decisions behind the shape.
"""

from src.domain.policy.policy_compatibility import (
    allowed_skill_types,
    check_gitpr_compatibility,
    check_skill_name,
    is_gitpr_compatible,
    parse_semver,
    parse_specifier,
    resolve_asset_path,
    validate_pack_name,
)
from src.domain.policy.policy_checksum import checksum_bytes, checksum_file, checksum_pack
from src.domain.policy.policy_manifest import (
    SCHEMA_VERSION,
    find_secret,
    parse_manifest,
    parse_overrides,
)
from src.domain.policy.policy_resolver import (
    DEFAULT_CONTEXT_MAX_CHARACTERS,
    ResolvedPack,
    check_severity_overrides_resolve,
    compose_policy,
    describe_origin,
    resolve_graph,
    risk_config_from_policy,
)
from src.domain.policy.policy_types import (
    DOWNGRADE,
    RULE_LEVELS,
    EffectivePolicy,
    PackReference,
    PolicyError,
    PolicyManifest,
    PolicySource,
    SeverityOverride,
    SkillPolicy,
)

# The active policy for the process, published the way src/i18n.py publishes the
# language: resolved once at startup by resolve_effective_policy, read by
# get_skill_context and the linter/risk integration points, and rebindable so a
# test can install one without touching the disk.
ACTIVE_POLICY = EffectivePolicy()


def set_active_policy(policy: EffectivePolicy | None) -> None:
    """Publishes *policy* as the process-wide effective policy.

    Called once per run by the resolver use case. Passing None resets to the
    empty policy, which every consumer reads as "change nothing".
    """
    global ACTIVE_POLICY
    ACTIVE_POLICY = policy or EffectivePolicy()


def get_active_policy() -> EffectivePolicy:
    """The policy the current process runs under. Empty when no pack is active."""
    return ACTIVE_POLICY


__all__ = [
    "ACTIVE_POLICY",
    "DEFAULT_CONTEXT_MAX_CHARACTERS",
    "DOWNGRADE",
    "RULE_LEVELS",
    "SCHEMA_VERSION",
    "EffectivePolicy",
    "PackReference",
    "PolicyError",
    "PolicyManifest",
    "PolicySource",
    "ResolvedPack",
    "SeverityOverride",
    "SkillPolicy",
    "allowed_skill_types",
    "check_gitpr_compatibility",
    "check_severity_overrides_resolve",
    "check_skill_name",
    "checksum_bytes",
    "checksum_file",
    "checksum_pack",
    "compose_policy",
    "describe_origin",
    "find_secret",
    "get_active_policy",
    "is_gitpr_compatible",
    "parse_manifest",
    "parse_overrides",
    "parse_semver",
    "parse_specifier",
    "resolve_asset_path",
    "resolve_graph",
    "risk_config_from_policy",
    "set_active_policy",
    "validate_pack_name",
]
