"""Data contracts for policy packs: the manifest, a pack reference, the resolved policy.

A policy pack is a declarative, versioned manifest that standardises the quality
gate of a repository. It is not a skill: it can only activate, parameterise, add
complementary context to, or select the format of a skill GitPR already knows how
to run. Every name it mentions has to exist in the fixed registry — that
invariant is enforced in policy_manifest.py, never here.

These are plain value types. Nothing in this module reads a file, touches the
network or knows about YAML; that keeps the domain testable without fixtures on
disk. See docs/plans/glossary-policy-packs.md for the vocabulary and
docs/plans/ADR-011-policy-packs.md for why the shape is what it is.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# The two levels the linter engine actually implements: anything that is not
# "warning" blocks (src/linter_engine.py). A third level between them would add
# a word without adding behaviour — the same reason ADR-007 rejected one for the
# secret ruleset. Policy packs inherit that ceiling here.
RULE_LEVELS = ("error", "warning")

# A severity override that moves a rule from "error" to "warning" weakens the
# gate, so it has to carry a reason; hardening a rule does not.
DOWNGRADE = ("error", "warning")


class PolicySource(str, Enum):
    """Where a pack was read from."""

    BUNDLED = "bundled"        # src/policy_packs/, inside the installed wheel
    LOCAL_PATH = "local_path"  # .gitpr/policies/<name>/, versioned with the repo
    INSTALLED = "installed"    # ~/.gitpr/policies/<name>/, installed by the user


class PolicyError(Exception):
    """A pack is unusable and the run cannot continue.

    Carries the pack name and, when the failure has one, the chain that produced
    it (a cycle in ``extends``, two sibling packs disagreeing on a scalar) so the
    message can name what the user has to fix instead of just saying "invalid".
    """

    def __init__(self, message: str, pack: str | None = None, chain: list[str] | None = None):
        super().__init__(message)
        self.message = message
        self.pack = pack
        self.chain = list(chain or [])


@dataclass
class PackReference:
    """A pack named by a manifest, or resolved to a concrete file on disk."""

    name: str                      # namespace/name, e.g. gitpr/laravel-quality
    version: str                   # exact SemVer once resolved; a range in extends
    source: PolicySource
    path: str | None = None        # directory holding policy.yml, once resolved
    checksum: str | None = None    # SHA-256 of policy.yml + declared assets

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "source": self.source.value,
            "path": self.path,
            "checksum": self.checksum,
        }


@dataclass
class SkillPolicy:
    """The activation of a fixed skill, plus the context the pack adds to it."""

    skill_name: str
    additional_context: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "additional_context": self.additional_context,
        }


@dataclass
class SeverityOverride:
    """A change of ``level`` for one linter rule, named by its ``name`` key."""

    rule_name: str
    level: str                     # one of RULE_LEVELS
    reason: str | None = None

    @property
    def weakens_the_gate(self) -> bool:
        """Whether this override moves a rule from blocking to warning."""
        return self.level == "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "level": self.level,
            "reason": self.reason,
        }


@dataclass
class PolicyManifest:
    """A validated ``policy.yml``.

    Parsing and validation live in policy_manifest.py; an instance of this class
    has already passed every check, so consumers may read it without re-checking.
    """

    name: str
    version: str
    min_gitpr_version: str
    schema_version: int = 1
    description: str = ""
    license: str | None = None
    authors: list[str] = field(default_factory=list)
    dependencies: list[PackReference] = field(default_factory=list)
    skills: list[SkillPolicy] = field(default_factory=list)
    rules_file: str | None = None
    severity_overrides: list[SeverityOverride] = field(default_factory=list)
    risk: dict[str, Any] = field(default_factory=dict)
    pr: dict[str, Any] = field(default_factory=dict)
    commit: dict[str, Any] = field(default_factory=dict)
    protected_paths: list[str] = field(default_factory=list)


@dataclass
class EffectivePolicy:
    """The composed policy a run operates under.

    ``packs`` is the resolved ``extends`` graph in topological order, dependencies
    first and the root pack last. ``provenance`` answers "where did this value
    come from" for every composed key, which is what ``gitpr policy show`` reads.

    An empty instance (no ``packs``, all mappings empty) is what a repository with
    no active pack gets; every consumer treats it as "change nothing".
    """

    packs: list[PackReference] = field(default_factory=list)
    enabled_skills: dict[str, SkillPolicy] = field(default_factory=dict)
    linter_config: dict[str, Any] = field(default_factory=dict)
    severity_overrides: dict[str, SeverityOverride] = field(default_factory=dict)
    risk_config: dict[str, Any] = field(default_factory=dict)
    # Patterns the repository's overrides asked to remove. Kept apart from
    # risk_config because they have to be subtracted from the *merged* config —
    # the built-in patterns are not in risk_config, so a removal that only
    # touched it could never drop one of them.
    risk_removals: dict[str, list[str]] = field(default_factory=dict)
    pr_config: dict[str, Any] = field(default_factory=dict)
    commit_config: dict[str, Any] = field(default_factory=dict)
    protected_paths: list[str] = field(default_factory=list)
    provenance: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Whether any pack is in force. False means "behave exactly as before"."""
        return bool(self.packs)

    @property
    def root(self) -> PackReference | None:
        """The root pack — the last one in topological order, if any."""
        return self.packs[-1] if self.packs else None

    def policy_tag(self) -> str:
        """The ``name@version`` label the review output and the cache scope use."""
        root = self.root
        return f"{root.name}@{root.version}" if root else ""

    def cache_scope(self) -> str:
        """The cache-key suffix that makes a policy change invalidate the cache.

        The skill context travels in ``instrucao_sistema``, which is NOT part of
        the MD5 key — so without this, activating a pack over an already cached
        diff would return the old answer while the output claimed the new policy.
        """
        root = self.root
        if root is None:
            return ""
        return f"::policy::{root.name}@{root.version}::{root.checksum or ''}"

    def skill_context_for(self, skill_name: str) -> str:
        """The additional context a pack declares for *skill_name*, or ""."""
        policy = self.enabled_skills.get(skill_name)
        return (policy.additional_context or "") if policy else ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "packs": [p.to_dict() for p in self.packs],
            "enabled_skills": {k: v.to_dict() for k, v in self.enabled_skills.items()},
            "linter_config": self.linter_config,
            "severity_overrides": {k: v.to_dict() for k, v in self.severity_overrides.items()},
            "risk_config": self.risk_config,
            "risk_removals": {k: list(v) for k, v in self.risk_removals.items()},
            "pr_config": self.pr_config,
            "commit_config": self.commit_config,
            "protected_paths": list(self.protected_paths),
            "provenance": dict(self.provenance),
            "warnings": list(self.warnings),
        }
