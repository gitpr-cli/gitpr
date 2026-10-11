"""Composition of packs into one effective policy.

This is the only place that understands precedence. Everything downstream — the
skill loader, the linter, the risk calculator, the PR and commit prompts — reads
the composed result and never a manifest.

The ladder, lowest to highest:

1. GitPR's internal defaults (untouched: nothing here overrides them, the pack
   only *adds* to what the run already had);
2. dependency packs, in topological order of ``extends``;
3. the root pack;
4. ``.gitpr/policy.overrides.yml``;
5. CLI flags and environment variables, applied by the caller after this.

Two rules are worth stating because they are the ones a reader will look for:

- **Precedence along an edge is silent, between siblings it is an error.** When
  a pack sets a value its own dependency already set, the dependent wins — that
  is what extending means. When two packs that do not depend on each other set
  the same scalar to different values, this module raises and names both: there
  is no defensible way to pick, and picking silently is how a gate lies.
- **Context is concatenated, never replaced**, under a character budget. It is
  assembled in precedence order and, if it does not fit, whole contributions are
  dropped from the lowest-precedence end rather than truncated mid-sentence.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Callable

from src.domain.policy.policy_types import (
    EffectivePolicy,
    PackReference,
    PolicyError,
    PolicyManifest,
    SeverityOverride,
    SkillPolicy,
)
from src.i18n import __

# The default ceiling for the context a pack may add to one skill. Sized so the
# addition stays well inside a prompt that already carries the diff.
DEFAULT_CONTEXT_MAX_CHARACTERS = 12000

_CONTEXT_OPEN = "[policy: {tag}]"
_CONTEXT_CLOSE = "[/policy: {tag}]"


@dataclass
class ResolvedPack:
    """A pack that exists on disk, with its assets already read.

    The loader builds these, which is what keeps this module free of file I/O
    while still composing the rules file's contents into the policy.
    """

    reference: PackReference
    manifest: PolicyManifest
    rules: list[dict] = field(default_factory=list)

    @property
    def tag(self) -> str:
        return f"{self.reference.name}@{self.reference.version}"


def _graph_ancestors(packs: list[ResolvedPack]) -> dict[str, set[str]]:
    """For each pack, the set of pack names reachable through ``extends``."""
    dependencies = {p.reference.name: {d.name for d in p.manifest.dependencies} for p in packs}
    ancestors: dict[str, set[str]] = {}
    for name in dependencies:
        seen: set[str] = set()
        stack = list(dependencies.get(name, ()))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(dependencies.get(current, ()))
        ancestors[name] = seen
    return ancestors


def resolve_graph(
    root: ResolvedPack,
    loader: Callable[[str, str], ResolvedPack],
) -> list[ResolvedPack]:
    """Every pack reachable from *root*, dependencies first and root last.

    *loader* takes a dependency name and the version range the dependent asked
    for, and returns the resolved pack or raises ``PolicyError``. It is called
    once per distinct pack name; a name reached twice is checked against both
    ranges and fails if the resolved version does not satisfy them.

    A cycle raises with the chain that closes it, because "cycle detected" alone
    leaves the author of a five-pack graph with nowhere to look.
    """
    ordered: list[ResolvedPack] = []
    resolved: dict[str, ResolvedPack] = {}
    ranges: dict[str, list[tuple[str, str]]] = {}
    path: list[str] = []
    settled: set[str] = set()

    def visit(pack: ResolvedPack) -> None:
        name = pack.reference.name
        if name in settled:
            return
        if name in path:
            chain = path[path.index(name):] + [name]
            raise PolicyError(
                __(
                    "Cycle in 'extends': {chain}. Break it by removing one of those edges.",
                    chain=" -> ".join(chain),
                ),
                pack=name,
                chain=chain,
            )

        path.append(name)
        for dependency in pack.manifest.dependencies:
            ranges.setdefault(dependency.name, []).append((dependency.version, name))
            if dependency.name in resolved:
                continue
            resolved[dependency.name] = loader(dependency.name, dependency.version)
        for dependency in pack.manifest.dependencies:
            visit(resolved[dependency.name])
        path.pop()

        settled.add(name)
        if name not in {p.reference.name for p in ordered}:
            ordered.append(resolved.get(name, pack))

    resolved[root.reference.name] = root
    visit(root)

    from src.domain.policy.policy_compatibility import parse_specifier

    for name, requests in ranges.items():
        found = resolved.get(name)
        if found is None:
            continue
        for version_range, requester in requests:
            if not parse_specifier(version_range, f"extends[{name}].version").contains(
                found.reference.version
            ):
                raise PolicyError(
                    __(
                        "Pack {requester} requires {name} {range}, but {name} resolved to "
                        "{found}. Widen one of the ranges.",
                        requester=requester,
                        name=name,
                        range=version_range,
                        found=found.reference.version,
                    ),
                    pack=name,
                )
    return ordered


def _merge_rule_catalogue(rules: list[dict]) -> list[dict]:
    """Union by rule ``name``, later layers replacing earlier ones in place.

    The engine identifies a rule by ``name``, so two packs shipping the same name
    would otherwise raise two alerts for one line. First-seen position is kept so
    the catalogue reads in a stable order as packs are added.
    """
    positions: dict[str, int] = {}
    merged: list[dict] = []
    for rule in rules:
        name = rule.get("name")
        if not isinstance(name, str) or not name:
            # A nameless rule cannot be addressed by an override or deduplicated;
            # keep it (the engine tolerates it) rather than dropping a check.
            merged.append(rule)
            continue
        if name in positions:
            merged[positions[name]] = rule
        else:
            positions[name] = len(merged)
            merged.append(rule)
    return merged


def _append_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _remove_all(target: list[str], values: list[str]) -> None:
    for value in values:
        while value in target:
            target.remove(value)


def _format_context(contributions: list[tuple[str, str]]) -> tuple[str, list[str]]:
    """Assemble ``additional_context`` in precedence order under no budget yet.

    Returns the annotated text and the warnings it produced. Budget trimming
    happens in _apply_context_budget, which needs to know the total.
    """
    blocks = []
    for tag, text in contributions:
        body = text.strip()
        if not body:
            continue
        blocks.append(f"{_CONTEXT_OPEN.format(tag=tag)}\n{body}\n{_CONTEXT_CLOSE.format(tag=tag)}")
    return "\n\n".join(blocks), []


def _render_convention(lead_in: str, values: list[str]) -> str:
    """One generated block: a lead-in sentence and a bullet per value.

    Used for the three surfaces nothing consumes in code — ``required_sections``,
    ``allowed_types`` and ``protected_paths`` exist to be *said* to the model.
    """
    return lead_in + "\n" + "\n".join(f"- {value}" for value in values)


def _apply_context_budget(
    contributions: list[tuple[str, str]], budget: int, skill_name: str
) -> tuple[str, list[str]]:
    """The composed context for one skill, trimmed to *budget* characters.

    Drops whole pack contributions from the lowest-precedence end — a dependency
    is the safe thing to lose, the root pack is the team's own policy. Only when
    a single contribution alone exceeds the budget is it cut, and the cut is
    announced either way.
    """
    warnings: list[str] = []
    kept = list(contributions)
    dropped: list[str] = []

    def size(entries: list[tuple[str, str]]) -> int:
        return len(_format_context(entries)[0])

    while len(kept) > 1 and size(kept) > budget:
        dropped.append(kept.pop(0)[0])

    text, _ = _format_context(kept)
    if dropped:
        warnings.append(
            __(
                "Skill {skill}: the additional context exceeded {budget} characters; "
                "the contribution of {packs} was left out.",
                skill=skill_name,
                budget=budget,
                packs=", ".join(dropped),
            )
        )

    if len(text) > budget and kept:
        tag = kept[-1][0]
        text = text[:budget].rstrip() + "\n[... truncated by the policy context budget ...]"
        warnings.append(
            __(
                "Skill {skill}: the context from {pack} alone exceeds {budget} characters "
                "and was truncated.",
                skill=skill_name,
                pack=tag,
                budget=budget,
            )
        )
        _ = tag
    return text, warnings


def check_severity_overrides_resolve(
    overrides: dict[str, SeverityOverride], known_rule_names: set[str], origin: str
) -> None:
    """Raises when an override names a rule the merged catalogue does not have.

    Called where the catalogue is finally known — after the project rules, the
    global plugins and the embedded secret ruleset have been merged — because
    only there can the answer be trusted. A typo has to fail loudly: an override
    that quietly did nothing would leave the user believing a rule was relaxed
    when it was not, or hardened when it was not.
    """
    unknown = sorted(name for name in overrides if name not in known_rule_names)
    if unknown:
        raise PolicyError(
            __(
                "Severity override from {origin} names rule(s) that do not exist: {rules}. "
                "Check the rule name against the merged linter catalogue.",
                origin=origin,
                rules=", ".join(unknown),
            ),
            pack=origin,
        )


def compose_policy(
    packs: list[ResolvedPack],
    overrides: dict[str, Any] | None = None,
    context_max_characters: int = DEFAULT_CONTEXT_MAX_CHARACTERS,
) -> EffectivePolicy:
    """Folds *packs* (dependencies first, root last) into one effective policy.

    *overrides* is the parsed ``.gitpr/policy.overrides.yml`` — see
    ``parse_overrides`` in policy_manifest.py for its shape. It applies last here
    and always wins, because it is the repository speaking about itself.
    """
    if not packs:
        return EffectivePolicy()

    ancestors = _graph_ancestors(packs)
    policy = EffectivePolicy()

    skill_contexts: dict[str, list[tuple[str, str]]] = {}
    scalar_owner: dict[str, tuple[str, Any]] = {}
    rule_catalogue: list[dict] = []
    baseline_layer: list[tuple[str, str, dict[str, Any]]] = []

    def claim_scalar(key: str, value: Any, tag: str, name: str, declared: str) -> bool:
        """Records a scalar, refusing a disagreement between unrelated packs."""
        previous = scalar_owner.get(key)
        if previous is None:
            scalar_owner[key] = (name, value)
            return True
        previous_name, previous_value = previous
        if previous_name == name or previous_value == value:
            scalar_owner[key] = (name, value)
            return True
        if previous_name in ancestors.get(name, set()):
            # The dependency declared it first, the dependent refines it.
            scalar_owner[key] = (name, value)
            return True
        if name in ancestors.get(previous_name, set()):
            # Topological order puts dependencies first, so this can only happen
            # if the graph is malformed; treat it as the same refinement.
            scalar_owner[key] = (name, value)
            return True
        raise PolicyError(
            __(
                "Packs {first} and {second} both set {setting} to different values "
                "({first_value} and {second_value}) and neither depends on the other. "
                "Reconcile them or let one extend the other.",
                first=previous_name,
                second=name,
                setting=declared,
                first_value=previous_value,
                second_value=value,
            ),
            pack=name,
            chain=[previous_name, name],
        )

    for pack in packs:
        manifest = pack.manifest
        tag = pack.tag
        policy.packs.append(pack.reference)

        # --- skills -----------------------------------------------------------
        for skill in manifest.skills:
            entry = policy.enabled_skills.get(skill.skill_name)
            if entry is None:
                entry = SkillPolicy(skill_name=skill.skill_name)
                policy.enabled_skills[skill.skill_name] = entry
            if skill.additional_context:
                skill_contexts.setdefault(skill.skill_name, []).append(
                    (tag, skill.additional_context)
                )

        # --- linter -----------------------------------------------------------
        if manifest.rules_file:
            policy.linter_config["rules_file"] = manifest.rules_file
            policy.provenance["linter.rules_file"] = tag
        if pack.rules:
            rule_catalogue.extend(pack.rules)
            # Several packs may contribute rules; the provenance lists all of
            # them, since the rules are unioned and a single owner would be a lie.
            contributing = {
                part.strip()
                for part in (policy.provenance.get("linter.rules", "")).split(",")
                if part.strip()
            }
            contributing.add(tag)
            policy.provenance["linter.rules"] = ", ".join(sorted(contributing))

        for override in manifest.severity_overrides:
            # A rule's level is not a sibling conflict: the more specific pack
            # wins and the provenance records who said it.
            policy.severity_overrides[override.rule_name] = override
            policy.provenance[f"linter.severity_overrides.{override.rule_name}"] = tag

        # --- risk -------------------------------------------------------------
        risk = manifest.risk
        if "critical_paths" in risk:
            _append_unique(
                policy.risk_config.setdefault("critical_paths", []), risk["critical_paths"]
            )
            policy.provenance["risk.critical_paths"] = _join_provenance(
                policy.provenance.get("risk.critical_paths"), tag
            )
        if "test_patterns" in risk:
            _append_unique(
                policy.risk_config.setdefault("test_patterns", []), risk["test_patterns"]
            )
            policy.provenance["risk.test_patterns"] = _join_provenance(
                policy.provenance.get("risk.test_patterns"), tag
            )
        for signal, weight in (risk.get("weights") or {}).items():
            if claim_scalar(f"risk.weights.{signal}", weight, tag, manifest.name, f"risk.weights.{signal}"):
                policy.risk_config.setdefault("weights", {})[signal] = weight
                policy.provenance[f"risk.weights.{signal}"] = tag
        for key, value in (risk.get("thresholds") or {}).items():
            if claim_scalar(f"risk.thresholds.{key}", value, tag, manifest.name, f"risk.thresholds.{key}"):
                policy.risk_config.setdefault("thresholds", {})[key] = value
                policy.provenance[f"risk.thresholds.{key}"] = tag

        # --- pull request, commit, protected paths ----------------------------
        for section in manifest.pr.get("required_sections", []):
            _append_unique(policy.pr_config.setdefault("required_sections", []), [section])
        if manifest.pr.get("required_sections"):
            policy.provenance["pr.required_sections"] = _join_provenance(
                policy.provenance.get("pr.required_sections"), tag
            )

        for allowed in manifest.commit.get("allowed_types", []):
            _append_unique(policy.commit_config.setdefault("allowed_types", []), [allowed])
        if manifest.commit.get("allowed_types"):
            policy.provenance["commit.allowed_types"] = _join_provenance(
                policy.provenance.get("commit.allowed_types"), tag
            )

        if manifest.protected_paths:
            _append_unique(policy.protected_paths, manifest.protected_paths)
            policy.provenance["protected_paths"] = _join_provenance(
                policy.provenance.get("protected_paths"), tag
            )

        # --- baseline (suppressions and accepted debt the pack brings) --------
        # Collected here and composed below, so the merged document goes through
        # `parse_overrides` once. That is what refuses a duplicate fingerprint
        # two packs would otherwise each consider their own.
        for half in ("suppressions", "accepted_debt"):
            for item in manifest.baseline.get(half, []):
                baseline_layer.append((half, tag, item))
            if manifest.baseline.get(half):
                policy.provenance[f"baseline.{half}"] = _join_provenance(
                    policy.provenance.get(f"baseline.{half}"), tag
                )

    if rule_catalogue:
        policy.linter_config["rules"] = _merge_rule_catalogue(rule_catalogue)

    policy.baseline_overrides = _compose_baseline(baseline_layer)

    # --- conventions said as prompt context -----------------------------------
    # required_sections, allowed_types and protected_paths are read by no engine:
    # they exist so the model is told them, which is why they are rendered into
    # the skill context rather than left as data. They are rendered after the
    # overrides — the repository's own file is the last word on what its own PR
    # must contain — and before the budget, so a trim takes the prose of a
    # dependency before it takes a rule the team wrote down.
    if overrides:
        _apply_overrides(policy, overrides, skill_contexts)

    conventions = []
    if policy.pr_config.get("required_sections"):
        conventions.append(
            (
                "pr",
                policy.provenance["pr.required_sections"],
                _render_convention(
                    __("The pull request description must have these sections, in this order:"),
                    policy.pr_config["required_sections"],
                ),
            )
        )
    if policy.protected_paths:
        conventions.append(
            (
                "pr",
                policy.provenance["protected_paths"],
                _render_convention(
                    __(
                        "These paths are protected in this repository. A change to any of "
                        "them must be justified in the description:"
                    ),
                    policy.protected_paths,
                ),
            )
        )
    if policy.commit_config.get("allowed_types"):
        conventions.append(
            (
                "commit",
                policy.provenance["commit.allowed_types"],
                _render_convention(
                    __("The commit message must use one of these types:"),
                    policy.commit_config["allowed_types"],
                ),
            )
        )

    for skill_name, tag, text in conventions:
        entry = policy.enabled_skills.get(skill_name)
        if entry is None:
            entry = SkillPolicy(skill_name=skill_name)
            policy.enabled_skills[skill_name] = entry
        skill_contexts.setdefault(skill_name, []).append((tag, text))

    # --- context budget -------------------------------------------------------
    for skill_name, contributions in skill_contexts.items():
        text, warnings = _apply_context_budget(contributions, context_max_characters, skill_name)
        policy.enabled_skills[skill_name].additional_context = text or None
        policy.warnings.extend(warnings)
        # One skill can take two blocks from the same pack (the PR context takes
        # both the required sections and the protected paths), so the tags are
        # deduplicated without reordering.
        seen: list[str] = []
        for tag, _ in contributions:
            if tag not in seen:
                seen.append(tag)
        policy.provenance[f"skills.{skill_name}.additional_context"] = ", ".join(seen)

    return policy


def _join_provenance(existing: str | None, tag: str) -> str:
    """Provenance for a list, which several packs may contribute to."""
    if not existing:
        return tag
    if tag in existing.split(", "):
        return existing
    return f"{existing}, {tag}"


def _compose_baseline(
    contributions: list[tuple[str, str, dict[str, Any]]],
) -> Any:
    """The packs' baseline blocks as one layer, each entry stamped with its pack.

    Parsed in a single pass through ``parse_overrides`` — the very validator a
    hand-edited ``baseline.overrides.yml`` goes through — so a duplicate
    fingerprint between two packs is refused here rather than resolved by
    whichever pack happened to come last. The origin is written per entry, from
    the pack that declared it: the layer is displayed as ``policy:<name>``, and
    a dependency's decision shown as the root's would misserve the one surface
    that exists to attribute.
    """
    if not contributions:
        return None

    from src.domain.baseline import BaselineError, parse_overrides

    document: dict[str, list[dict[str, Any]]] = {"suppressions": [], "accepted_debt": []}
    origins: dict[str, list[str]] = {"suppressions": [], "accepted_debt": []}
    for half, tag, item in contributions:
        document[half].append(item)
        origins[half].append(f"policy:{tag}")

    try:
        layer = parse_overrides(document)
    except BaselineError as error:
        raise PolicyError(
            __(
                "The baseline block of these packs cannot be applied: {error}",
                error=error,
            )
        ) from error

    for half, items in (
        ("suppressions", layer.suppressions),
        ("accepted_debt", layer.accepted_debt),
    ):
        for entry, origin in zip(items, origins[half]):
            entry.origin = origin
    return layer


def _apply_overrides(
    policy: EffectivePolicy,
    overrides: dict[str, Any],
    skill_contexts: dict[str, list[tuple[str, str]]],
) -> None:
    """Applies the repository's own overrides — the last word before the CLI.

    Skill context joins *skill_contexts* rather than being written straight into
    the policy, so the whole set of contributions — packs, overrides and the
    generated conventions — passes through one budget pass at the end.
    """
    tag = "policy.overrides.yml"

    for override in overrides.get("severity_overrides", []):
        policy.severity_overrides[override.rule_name] = override
        policy.provenance[f"linter.severity_overrides.{override.rule_name}"] = tag

    risk = overrides.get("risk", {})
    for key in ("critical_paths", "test_patterns"):
        block = risk.get(key, {})
        if not block:
            continue
        target = policy.risk_config.setdefault(key, [])
        _append_unique(target, block.get("add", []))
        removed = [
            str(name) for name in block.get("remove", []) if isinstance(name, str)
        ]
        _remove_all(target, removed)
        # Recorded as well as applied: patterns contributed by the built-in
        # defaults are not in risk_config, so only the merge with RiskConfig can
        # take those out.
        _append_unique(policy.risk_removals.setdefault(key, []), removed)
        policy.provenance[f"risk.{key}"] = _join_provenance(
            policy.provenance.get(f"risk.{key}"), tag
        )
    for key in ("weights", "thresholds"):
        for name, value in (risk.get(key) or {}).items():
            policy.risk_config.setdefault(key, {})[name] = value
            policy.provenance[f"risk.{key}.{name}"] = tag

    pr_block = overrides.get("pr", {}).get("required_sections")
    if pr_block:
        target = policy.pr_config.setdefault("required_sections", [])
        _append_unique(target, pr_block.get("add", []))
        _remove_all(target, pr_block.get("remove", []))
        policy.provenance["pr.required_sections"] = _join_provenance(
            policy.provenance.get("pr.required_sections"), tag
        )

    commit_block = overrides.get("commit", {}).get("allowed_types")
    if commit_block:
        target = policy.commit_config.setdefault("allowed_types", [])
        _append_unique(target, commit_block.get("add", []))
        _remove_all(target, commit_block.get("remove", []))
        policy.provenance["commit.allowed_types"] = _join_provenance(
            policy.provenance.get("commit.allowed_types"), tag
        )

    paths_block = overrides.get("protected_paths")
    if paths_block:
        _append_unique(policy.protected_paths, paths_block.get("add", []))
        _remove_all(policy.protected_paths, paths_block.get("remove", []))
        policy.provenance["protected_paths"] = _join_provenance(
            policy.provenance.get("protected_paths"), tag
        )

    for skill_name, settings in (overrides.get("skills") or {}).items():
        context = (settings or {}).get("additional_context")
        if not context:
            continue
        if skill_name not in policy.enabled_skills:
            policy.enabled_skills[skill_name] = SkillPolicy(skill_name=skill_name)
        skill_contexts.setdefault(skill_name, []).append((tag, context))


def risk_config_from_policy(policy: EffectivePolicy, base: Any = None) -> Any:
    """Turns the composed risk block into a ``RiskConfig``.

    Starts from *base* — the config ``load_risk_config()`` already produced from
    ``.gitpr.risk.yml`` and the built-in defaults — so a pack refines the
    project's own settings instead of replacing them. Returns *base* untouched
    (or a fresh default) when no pack is active, which is what makes "no pack no
    change" a property of the code rather than a promise in a document.

    Pattern lists are **unioned**, matching the composition rule every other list
    in a pack follows: a pack may add somewhere to be careful, never quietly
    remove the built-in protection for ``**/payment/**``. Taking a pattern out is
    the repository's call, spelled in ``.gitpr/policy.overrides.yml`` — see
    ``risk_removals``.
    """
    from src.domain.risk.risk_rules import RiskConfig, RiskSignal

    if base is None:
        base = RiskConfig()
    if not policy.is_active or not policy.risk_config:
        return base

    if "weights" in policy.risk_config:
        for name, value in policy.risk_config["weights"].items():
            try:
                base.weights[RiskSignal(name)] = float(value)
            except (ValueError, KeyError):
                continue
    if "thresholds" in policy.risk_config:
        for key, value in policy.risk_config["thresholds"].items():
            if key in base.thresholds:
                base.thresholds[key] = float(value)

    for key, patterns in (
        ("critical_paths", base.critical_patterns.get(RiskSignal.CRITICAL_PATH, [])),
        ("test_patterns", base.test_patterns),
    ):
        removed = set(policy.risk_removals.get(key, []))
        merged = [pattern for pattern in patterns if pattern not in removed]
        for pattern in policy.risk_config.get(key, []):
            if pattern not in removed and pattern not in merged:
                merged.append(pattern)
        if key == "critical_paths":
            base.critical_patterns[RiskSignal.CRITICAL_PATH] = merged
        else:
            base.test_patterns = merged

    return base


def describe_origin(policy: EffectivePolicy, key: str) -> str:
    """The provenance of *key*, or a marker when nothing claimed it."""
    return policy.provenance.get(key, __("internal defaults"))


def relative_asset_name(policy: EffectivePolicy) -> str | None:
    """The pack's rules file name, as declared, for display purposes."""
    name = policy.linter_config.get("rules_file")
    return os.path.basename(name) if name else None
