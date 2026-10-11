"""Composition: what a graph of packs folds into, and what it refuses to fold.

The resolver is where precedence becomes behaviour, so most of what is pinned
here is a refusal — a cycle, two unrelated packs disagreeing on a scalar, a
severity override naming a rule that does not exist — because a wrong answer
that *looks* like a right one is the failure mode this feature is most exposed
to. The rest pins the identity property: with no pack, composition returns the
very object it was handed.

Every pack below is built in memory as a ``ResolvedPack``. That is the point of
the loader/resolver split — composition has no file I/O to fake.
"""

import unittest

from src.domain.policy import (
    EffectivePolicy,
    PackReference,
    PolicyError,
    PolicyManifest,
    PolicySource,
    ResolvedPack,
    SeverityOverride,
    SkillPolicy,
    check_severity_overrides_resolve,
    compose_policy,
    describe_origin,
    resolve_graph,
    risk_config_from_policy,
)


def pack(
    name="gitpr/root",
    version="1.0.0",
    *,
    dependencies=(),
    skills=None,
    rules_file=None,
    severity_overrides=(),
    rules=(),
    risk=None,
    pr=None,
    commit=None,
    protected_paths=(),
    baseline=None,
):
    """A ``ResolvedPack`` built in memory, with only what a test names."""
    manifest = PolicyManifest(
        name=name,
        version=version,
        min_gitpr_version=">=1.0.0",
        dependencies=[
            PackReference(
                name=dependency[0],
                version=dependency[1],
                source=PolicySource.BUNDLED,
            )
            for dependency in dependencies
        ],
        skills=[SkillPolicy(skill_name=k, additional_context=v) for k, v in (skills or {}).items()],
        rules_file=rules_file,
        severity_overrides=list(severity_overrides),
        risk=risk or {},
        pr=pr or {},
        commit=commit or {},
        protected_paths=list(protected_paths),
        baseline=baseline or {},
    )
    return ResolvedPack(
        reference=PackReference(
            name=name,
            version=version,
            source=PolicySource.BUNDLED,
            path=f"/packs/{name}",
            checksum=f"checksum-{name}-{version}",
        ),
        manifest=manifest,
        rules=list(rules),
    )


class TestGraphOrder(unittest.TestCase):
    """Dependencies first, root last — the order everything else relies on."""

    def test_a_single_pack_is_its_own_order(self):
        root = pack("gitpr/only")

        ordered = resolve_graph(root, lambda name, spec: self.fail("no dependency to load"))

        self.assertEqual([p.reference.name for p in ordered], ["gitpr/only"])

    def test_dependencies_come_before_their_dependent(self):
        dependency = pack("gitpr/base")
        root = pack("gitpr/root", dependencies=[("gitpr/base", ">=1.0.0")])

        ordered = resolve_graph(root, lambda name, spec: dependency)

        self.assertEqual(
            [p.reference.name for p in ordered], ["gitpr/base", "gitpr/root"]
        )

    def test_a_dependency_is_loaded_once_even_when_reached_twice(self):
        calls = []

        def loader(name, spec):
            calls.append(name)
            return pack(name)

        a = pack("acme/a", dependencies=[("acme/shared", ">=1.0.0")])
        b = pack("acme/b", dependencies=[("acme/shared", ">=1.0.0")])
        root = pack(
            "acme/root",
            dependencies=[("acme/a", ">=1.0.0"), ("acme/b", ">=1.0.0")],
        )

        def resolve(name, spec):
            return {"acme/a": a, "acme/b": b, "acme/shared": pack("acme/shared")}[name]

        ordered = resolve_graph(root, resolve)

        self.assertEqual(
            [p.reference.name for p in ordered],
            ["acme/shared", "acme/a", "acme/b", "acme/root"],
        )

    def test_an_unresolvable_dependency_propagates_the_loader_error(self):
        root = pack("gitpr/root", dependencies=[("gitpr/missing", ">=1.0.0")])

        def loader(name, spec):
            raise PolicyError(f"Pack {name} not found.")

        with self.assertRaises(PolicyError) as caught:
            resolve_graph(root, loader)

        self.assertIn("gitpr/missing", str(caught.exception))


class TestCycle(unittest.TestCase):
    """A cycle has to name the chain — "cycle detected" leaves nowhere to look."""

    def test_a_two_pack_cycle_raises_with_the_chain(self):
        a = pack("acme/a", dependencies=[("acme/b", ">=1.0.0")])
        b = pack("acme/b", dependencies=[("acme/a", ">=1.0.0")])

        with self.assertRaises(PolicyError) as caught:
            resolve_graph(a, lambda name, spec: b)

        message = str(caught.exception)
        self.assertIn("acme/a", message)
        self.assertIn("acme/b", message)
        self.assertIn("->", message)

    def test_a_pack_extending_itself_raises(self):
        root = pack("acme/a", dependencies=[("acme/a", ">=1.0.0")])

        with self.assertRaises(PolicyError):
            resolve_graph(root, lambda name, spec: root)

    def test_a_three_pack_cycle_names_all_three(self):
        a = pack("acme/a", dependencies=[("acme/b", ">=1.0.0")])
        b = pack("acme/b", dependencies=[("acme/c", ">=1.0.0")])
        c = pack("acme/c", dependencies=[("acme/a", ">=1.0.0")])

        with self.assertRaises(PolicyError) as caught:
            resolve_graph(a, lambda name, spec: {"acme/b": b, "acme/c": c}[name])

        chain = caught.exception.chain
        self.assertEqual(len(set(chain)), 3)


class TestSiblings(unittest.TestCase):
    """Two unrelated packs may both add; they may not both disagree."""

    def test_siblings_disagreeing_on_a_weight_is_an_error(self):
        first = pack("acme/a", risk={"weights": {"large_diff": 20}})
        second = pack("acme/b", risk={"weights": {"large_diff": 40}})

        with self.assertRaises(PolicyError) as caught:
            compose_policy([first, second])

        message = str(caught.exception)
        self.assertIn("acme/a", message)
        self.assertIn("acme/b", message)
        self.assertIn("large_diff", message)

    def test_a_dependent_refining_its_dependency_is_allowed(self):
        dependency = pack("gitpr/base", risk={"weights": {"large_diff": 20}})
        # The `extends` edge is what makes this a refinement rather than a
        # conflict: the graph, not the argument order, decides.
        root = pack(
            "gitpr/root",
            dependencies=[("gitpr/base", ">=1.0.0")],
            risk={"weights": {"large_diff": 40}},
        )

        policy = compose_policy([dependency, root])

        self.assertEqual(policy.risk_config["weights"]["large_diff"], 40)
        self.assertEqual(policy.provenance["risk.weights.large_diff"], "gitpr/root@1.0.0")

    def test_two_siblings_agreeing_on_the_same_value_is_fine(self):
        first = pack("acme/a", risk={"weights": {"large_diff": 20}})
        second = pack("acme/b", risk={"weights": {"large_diff": 20}})

        policy = compose_policy([first, second])

        self.assertEqual(policy.risk_config["weights"]["large_diff"], 20)

    def test_two_siblings_setting_different_keys_are_fine(self):
        first = pack("acme/a", risk={"weights": {"large_diff": 20}})
        second = pack("acme/b", risk={"weights": {"no_test_change": 15}})

        policy = compose_policy([first, second])

        self.assertEqual(
            policy.risk_config["weights"], {"large_diff": 20, "no_test_change": 15}
        )


class TestListUnion(unittest.TestCase):
    """Lists accumulate; a pack may add somewhere to be careful, never remove."""

    def test_critical_paths_from_two_packs_are_unioned_in_order(self):
        first = pack("gitpr/base", risk={"critical_paths": ["**/db/**"]})
        root = pack("gitpr/root", risk={"critical_paths": ["routes/**"]})

        policy = compose_policy([first, root])

        self.assertEqual(policy.risk_config["critical_paths"], ["**/db/**", "routes/**"])
        self.assertEqual(
            policy.provenance["risk.critical_paths"],
            "gitpr/base@1.0.0, gitpr/root@1.0.0",
        )

    def test_a_pattern_declared_twice_appears_once(self):
        first = pack("gitpr/base", risk={"critical_paths": ["**/db/**"]})
        root = pack("gitpr/root", risk={"critical_paths": ["**/db/**"]})

        policy = compose_policy([first, root])

        self.assertEqual(policy.risk_config["critical_paths"], ["**/db/**"])

    def test_protected_paths_and_conventions_are_unioned(self):
        dependency = pack(
            "gitpr/base",
            commit={"allowed_types": ["feat", "fix"]},
            protected_paths=["config/**"],
        )
        root = pack(
            "gitpr/root",
            commit={"allowed_types": ["chore"]},
            protected_paths=["routes/**"],
            pr={"required_sections": ["Risks"]},
        )

        policy = compose_policy([dependency, root])

        self.assertEqual(
            policy.commit_config["allowed_types"], ["feat", "fix", "chore"]
        )
        self.assertEqual(policy.protected_paths, ["config/**", "routes/**"])
        self.assertEqual(policy.pr_config["required_sections"], ["Risks"])


class TestLinterComposition(unittest.TestCase):
    """Rules union by name; the last pack to redefine one wins its position."""

    def test_rules_from_two_packs_are_unioned(self):
        first = pack("gitpr/base", rules=[{"name": "a", "level": "error"}], rules_file="base.yml")
        root = pack("gitpr/root", rules=[{"name": "b", "level": "warning"}], rules_file="root.yml")

        policy = compose_policy([first, root])

        self.assertEqual([r["name"] for r in policy.linter_config["rules"]], ["a", "b"])

    def test_a_redefined_rule_keeps_its_first_position(self):
        """Activating a pack must not reshuffle the order alerts are reported in."""
        first = pack("gitpr/base", rules=[{"name": "a"}, {"name": "b"}])
        root = pack("gitpr/root", rules=[{"name": "b", "level": "warning"}, {"name": "c"}])

        policy = compose_policy([first, root])

        rules = policy.linter_config["rules"]
        self.assertEqual([r["name"] for r in rules], ["a", "b", "c"])
        self.assertEqual(rules[1]["level"], "warning")

    def test_the_rules_file_is_the_root_packs(self):
        first = pack("gitpr/base", rules_file="base.yml")
        root = pack("gitpr/root", rules_file="root.yml")

        policy = compose_policy([first, root])

        self.assertEqual(policy.linter_config["rules_file"], "root.yml")
        self.assertEqual(policy.provenance["linter.rules_file"], "gitpr/root@1.0.0")

    def test_severity_overrides_are_recorded_with_who_said_them(self):
        dependency = pack(
            "gitpr/base",
            severity_overrides=[
                SeverityOverride("sec-aws-key", "error"),
                SeverityOverride("sec-db-url", "warning", "legacy schema"),
            ],
        )
        root = pack(
            "gitpr/root",
            severity_overrides=[SeverityOverride("sec-aws-key", "warning", "rotated")],
        )

        policy = compose_policy([dependency, root])

        self.assertEqual(policy.severity_overrides["sec-aws-key"].level, "warning")
        self.assertEqual(
            policy.provenance["linter.severity_overrides.sec-aws-key"], "gitpr/root@1.0.0"
        )
        self.assertEqual(
            policy.provenance["linter.severity_overrides.sec-db-url"], "gitpr/base@1.0.0"
        )


class TestSkillContext(unittest.TestCase):
    """The context the model is told, annotated with where each block came from."""

    def test_blocks_are_annotated_and_ordered_by_precedence(self):
        dependency = pack("gitpr/base", skills={"review": "dependency rule"})
        root = pack("gitpr/root", skills={"review": "root rule"})

        policy = compose_policy([dependency, root])

        context = policy.skill_context_for("review")
        self.assertLess(context.index("dependency rule"), context.index("root rule"))
        self.assertIn("[policy: gitpr/base@1.0.0]", context)
        self.assertIn("[policy: gitpr/root@1.0.0]", context)
        self.assertIn("[/policy: gitpr/base@1.0.0]", context)

    def test_a_skill_no_pack_mentions_is_not_enabled(self):
        policy = compose_policy([pack("gitpr/root", skills={"review": "x"})])

        self.assertIn("review", policy.enabled_skills)
        self.assertNotIn("telepathy", policy.enabled_skills)
        self.assertEqual(policy.skill_context_for("telepathy"), "")

    def test_conventions_are_rendered_into_the_prompt_context(self):
        policy = compose_policy(
            [
                pack(
                    "gitpr/root",
                    pr={"required_sections": ["Business impact", "Rollback plan"]},
                    commit={"allowed_types": ["feat", "fix"]},
                    protected_paths=["database/migrations/**"],
                )
            ]
        )

        pr_context = policy.skill_context_for("pr")
        self.assertIn("must have these sections, in this order:", pr_context)
        self.assertIn("- Business impact", pr_context)
        self.assertIn("- database/migrations/**", pr_context)

        commit_context = policy.skill_context_for("commit")
        self.assertIn("must use one of these types:", commit_context)
        self.assertIn("- feat", commit_context)

    def test_the_budget_drops_the_dependency_and_says_so(self):
        dependency = pack("gitpr/base", skills={"review": "D" * 400})
        root = pack("gitpr/root", skills={"review": "R" * 400})

        policy = compose_policy([dependency, root], context_max_characters=600)

        context = policy.skill_context_for("review")
        self.assertIn("R" * 400, context)
        self.assertNotIn("D" * 400, context)
        self.assertTrue(any("gitpr/base@1.0.0" in w for w in policy.warnings))

    def test_the_budget_truncates_when_one_pack_alone_is_too_big(self):
        root = pack("gitpr/root", skills={"review": "R" * 5000})

        policy = compose_policy([root], context_max_characters=500)

        context = policy.skill_context_for("review")
        self.assertIn("truncated by the policy context budget", context)
        self.assertTrue(any("truncated" in w for w in policy.warnings))

    def test_the_provenance_deduplicates_a_pack_that_contributed_twice(self):
        """The PR skill takes both the required sections and the protected paths."""
        policy = compose_policy(
            [
                pack(
                    "gitpr/root",
                    pr={"required_sections": ["Risks"]},
                    protected_paths=["config/**"],
                )
            ]
        )

        self.assertEqual(
            policy.provenance["skills.pr.additional_context"], "gitpr/root@1.0.0"
        )


class TestOverrides(unittest.TestCase):
    """``.gitpr/policy.overrides.yml`` is the repository speaking, so it wins."""

    def test_an_override_appends_a_pattern(self):
        root = pack("gitpr/root", risk={"critical_paths": ["routes/**"]})

        policy = compose_policy(
            [root], overrides={"risk": {"critical_paths": {"add": ["**/legacy/**"]}}}
        )

        self.assertEqual(
            policy.risk_config["critical_paths"], ["routes/**", "**/legacy/**"]
        )

    def test_an_override_is_the_only_way_to_remove_a_pattern(self):
        root = pack("gitpr/root", risk={"critical_paths": ["routes/**", "**/legacy/**"]})

        policy = compose_policy(
            [root], overrides={"risk": {"critical_paths": {"remove": ["**/legacy/**"]}}}
        )

        self.assertEqual(policy.risk_config["critical_paths"], ["routes/**"])
        # The removal is kept apart so it can also be subtracted from the
        # built-in patterns, which never live in risk_config.
        self.assertEqual(policy.risk_removals["critical_paths"], ["**/legacy/**"])

    def test_an_override_replaces_a_severity_set_by_the_pack(self):
        root = pack(
            "gitpr/root",
            severity_overrides=[SeverityOverride("sec-aws-key", "warning", "pack said so")],
        )

        policy = compose_policy(
            [root],
            overrides={
                "severity_overrides": [
                    SeverityOverride("sec-aws-key", "error", None)
                ]
            },
        )

        self.assertEqual(policy.severity_overrides["sec-aws-key"].level, "error")
        self.assertEqual(policy.severity_overrides["sec-aws-key"].reason, None)
        # The provenance names the overrides file, not a pack: `policy show`
        # must be able to tell the reader it was the repository that spoke.
        self.assertEqual(
            policy.provenance["linter.severity_overrides.sec-aws-key"],
            "policy.overrides.yml",
        )

    def test_an_override_adds_context_to_a_skill(self):
        root = pack("gitpr/root", skills={"review": "pack rule"})

        policy = compose_policy(
            [root], overrides={"skills": {"review": {"additional_context": "local rule"}}}
        )

        context = policy.skill_context_for("review")
        self.assertIn("pack rule", context)
        self.assertIn("local rule", context)
        self.assertLess(context.index("pack rule"), context.index("local rule"))


class TestEmptyPolicy(unittest.TestCase):
    """No packs is not a special case to remember — it is an empty composition."""

    def test_composing_nothing_gives_an_inactive_policy(self):
        policy = compose_policy([])

        self.assertFalse(policy.is_active)
        self.assertEqual(policy.policy_tag(), "")
        self.assertEqual(policy.cache_scope(), "")

    def test_composing_nothing_ignores_overrides_rather_than_applying_them(self):
        """Overrides refine a pack; with no pack there is nothing to refine."""
        policy = compose_policy([], overrides={"protected_paths": {"add": ["config/**"]}})

        self.assertFalse(policy.is_active)
        self.assertEqual(policy.protected_paths, [])


class TestRiskConfigFromPolicy(unittest.TestCase):
    """The adapter the risk engine actually calls."""

    def test_with_no_pack_it_returns_the_very_object_it_was_handed(self):
        """This identity is what makes "no pack, no change" a property, not a promise."""
        from src.domain.risk.risk_rules import load_risk_config

        base = load_risk_config()

        self.assertIs(risk_config_from_policy(EffectivePolicy(), base), base)

    def test_with_no_pack_and_no_base_it_still_returns_a_usable_config(self):
        from src.domain.risk.risk_rules import RiskConfig

        self.assertIsInstance(risk_config_from_policy(EffectivePolicy()), RiskConfig)

    def test_a_pack_unions_the_patterns_into_the_project_config(self):
        from src.domain.risk.risk_rules import RiskSignal, load_risk_config

        policy = compose_policy(
            [pack("gitpr/root", risk={"critical_paths": ["routes/**"], "test_patterns": ["spec/**"]})]
        )

        config = risk_config_from_policy(policy, load_risk_config())

        critical = config.critical_patterns[RiskSignal.CRITICAL_PATH]
        self.assertIn("routes/**", critical)
        # The built-ins stay: a pack may add somewhere to be careful, never
        # quietly drop the protection for **/payment/**.
        self.assertIn("**/payment/**", critical)
        self.assertIn("spec/**", config.test_patterns)

    def test_a_pack_raises_a_weight_but_does_not_invent_one(self):
        from src.domain.risk.risk_rules import RiskConfig, RiskSignal

        policy = compose_policy([pack("gitpr/root", risk={"weights": {"large_diff": 30}})])

        config = risk_config_from_policy(policy, RiskConfig())

        self.assertEqual(config.weights[RiskSignal.LARGE_DIFF], 30.0)

    def test_a_weight_name_the_engine_does_not_know_is_skipped(self):
        """Validation refuses these at parse time; the adapter stays total anyway."""
        from src.domain.risk.risk_rules import RiskConfig

        policy = compose_policy([pack("gitpr/root")])
        policy.risk_config = {"weights": {"not_a_signal": 10}}

        config = risk_config_from_policy(policy, RiskConfig())

        self.assertNotIn("not_a_signal", {s.value for s in config.weights})

    def test_an_override_can_still_remove_a_built_in_pattern(self):
        """The built-ins are not in risk_config, so the removal has to reach them."""
        from src.domain.risk.risk_rules import RiskConfig, RiskSignal

        base = RiskConfig()
        built_in = base.critical_patterns[RiskSignal.CRITICAL_PATH]
        removed = built_in[0]

        policy = compose_policy(
            [pack("gitpr/root")],
            overrides={"risk": {"critical_paths": {"remove": [removed]}}},
        )
        config = risk_config_from_policy(policy, base)

        self.assertNotIn(removed, config.critical_patterns[RiskSignal.CRITICAL_PATH])
        self.assertEqual(
            len(config.critical_patterns[RiskSignal.CRITICAL_PATH]), len(built_in) - 1
        )


class TestSeverityOverridesResolve(unittest.TestCase):
    """A typo'd rule name has to fail loudly — a silent no-op misleads."""

    def test_an_override_that_resolves_passes(self):
        check_severity_overrides_resolve(
            {"sec-aws-key": SeverityOverride("sec-aws-key", "warning", "x")},
            {"sec-aws-key", "other"},
            "acme/team-policy@1.0.0",
        )

    def test_an_override_that_does_not_resolve_raises_naming_both(self):
        with self.assertRaises(PolicyError) as caught:
            check_severity_overrides_resolve(
                {"sec-aws-kye": SeverityOverride("sec-aws-kye", "warning", "x")},
                {"sec-aws-key"},
                "acme/team-policy@1.0.0",
            )

        message = str(caught.exception)
        self.assertIn("sec-aws-kye", message)
        self.assertIn("acme/team-policy@1.0.0", message)

    def test_several_unknown_names_are_listed_together(self):
        with self.assertRaises(PolicyError) as caught:
            check_severity_overrides_resolve(
                {
                    "b-rule": SeverityOverride("b-rule", "warning", "x"),
                    "a-rule": SeverityOverride("a-rule", "warning", "x"),
                },
                set(),
                "acme/team-policy@1.0.0",
            )

        self.assertIn("a-rule, b-rule", str(caught.exception))


class TestBaselineLayer(unittest.TestCase):
    """The suppressions and debt a pack brings, as one in-memory layer.

    This layer is never written into `.gitpr/baseline.json` — it is the pack's
    opinion about findings, not the repository's record of them — so what has to
    hold is that it composes completely, that each decision keeps the name of
    the pack that declared it, and that two packs cannot disagree about one
    finding in silence.
    """

    FINGERPRINT = "sha256:" + "b" * 64

    def test_no_pack_leaves_the_layer_absent(self):
        self.assertIsNone(compose_policy([pack("gitpr/root")]).baseline_overrides)

    def test_a_declared_suppression_becomes_a_layer_entry(self):
        policy = compose_policy(
            [
                pack(
                    "gitpr/root",
                    baseline={
                        "suppressions": [
                            {
                                "scope": "rule",
                                "rule_id": "warning-todo-fixme",
                                "reason": "Noisy in legacy code.",
                            }
                        ]
                    },
                )
            ]
        )

        layer = policy.baseline_overrides
        self.assertEqual(len(layer.suppressions), 1)
        self.assertEqual(layer.suppressions[0].rule_id, "warning-todo-fixme")
        self.assertEqual(policy.provenance["baseline.suppressions"], "gitpr/root@1.0.0")

    def test_a_dependency_keeps_its_own_name_in_the_origin(self):
        """The layer is shown as `policy:<name>`, and a dependency is not the root."""
        dependency = pack(
            "gitpr/base",
            baseline={
                "suppressions": [
                    {"scope": "rule", "rule_id": "from-base", "reason": "Base rule."}
                ]
            },
        )
        root = pack(
            "gitpr/root",
            dependencies=[("gitpr/base", "1.0.0")],
            baseline={
                "suppressions": [
                    {"scope": "rule", "rule_id": "from-root", "reason": "Root rule."}
                ]
            },
        )

        policy = compose_policy([dependency, root])

        origins = {item.rule_id: item.origin for item in policy.baseline_overrides.suppressions}
        self.assertEqual(origins["from-base"], "policy:gitpr/base@1.0.0")
        self.assertEqual(origins["from-root"], "policy:gitpr/root@1.0.0")
        self.assertEqual(
            policy.provenance["baseline.suppressions"], "gitpr/base@1.0.0, gitpr/root@1.0.0"
        )

    def test_two_packs_claiming_one_fingerprint_are_refused(self):
        """Both would be applied to the same finding; there is no defensible pick."""
        debt = {
            "fingerprint": self.FINGERPRINT,
            "owner": "platform",
            "reason": "Migration planned.",
        }

        with self.assertRaises(PolicyError) as caught:
            compose_policy(
                [
                    pack("gitpr/base", baseline={"accepted_debt": [debt]}),
                    pack("gitpr/root", baseline={"accepted_debt": [dict(debt)]}),
                ]
            )

        self.assertIn(self.FINGERPRINT, str(caught.exception))

    def test_the_layer_reads_as_data_with_the_pack_that_declared_it(self):
        """`gitpr policy show` prints this, so the origin travels with the entry."""
        policy = compose_policy(
            [
                pack(
                    "gitpr/root",
                    baseline={
                        "suppressions": [
                            {"scope": "rule", "rule_id": "x", "reason": "Because."}
                        ]
                    },
                )
            ]
        )

        document = policy.to_dict()["baseline"]

        self.assertEqual(document["suppressions"][0]["origin"], "policy:gitpr/root@1.0.0")
        self.assertEqual(document["suppressions"][0]["reason"], "Because.")

    def test_a_policy_without_the_block_serialises_it_as_nothing(self):
        self.assertEqual(compose_policy([pack("gitpr/root")]).to_dict()["baseline"], {})


class TestDescribeOrigin(unittest.TestCase):
    """``gitpr policy show`` reads this, so it has to say something for every key."""

    def test_a_claimed_key_names_its_pack(self):
        policy = compose_policy([pack("gitpr/root", rules_file="linter.yml")])

        self.assertEqual(describe_origin(policy, "linter.rules_file"), "gitpr/root@1.0.0")

    def test_an_unclaimed_key_says_so_instead_of_raising(self):
        policy = compose_policy([pack("gitpr/root")])

        self.assertEqual(
            describe_origin(policy, "nothing.claims.this"), "internal defaults"
        )


if __name__ == "__main__":
    unittest.main()
