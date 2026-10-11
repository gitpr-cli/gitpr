"""The manifest is a closed schema, and these are the doors it has to keep shut.

Parsing is the single gate every pack passes through — listing, validating,
resolving, activating — so a hole here is a hole in all four. The tests below
pin the three properties the rest of the feature leans on: an unknown key is an
error (a typo must never be silently ignored), a name that mentions a skill
GitPR does not ship is an error (a pack configures what exists, it cannot invent
a skill), and a manifest carrying a credential is refused (packs are shared).

The credential case deliberately reuses ``src/security_ruleset.py`` instead of a
private pattern, so it is tested against a real rule the linter also enforces.
"""

import unittest

from src.domain.policy import (
    SCHEMA_VERSION,
    PolicyError,
    PolicySource,
    allowed_skill_types,
    find_secret,
    parse_manifest,
    parse_overrides,
)

MINIMAL = {
    "schema_version": SCHEMA_VERSION,
    "name": "acme/team-policy",
    "version": "1.0.0",
    "min_gitpr_version": ">=1.0.0",
}


def manifest(**overrides):
    """A valid manifest with *overrides* merged in — the tests' shared base."""
    data = dict(MINIMAL)
    data.update(overrides)
    return data


class TestRequiredKeys(unittest.TestCase):
    """The four keys a pack cannot be read without."""

    def test_a_minimal_manifest_parses(self):
        parsed = parse_manifest(manifest())

        self.assertEqual(parsed.name, "acme/team-policy")
        self.assertEqual(parsed.version, "1.0.0")
        self.assertEqual(parsed.schema_version, SCHEMA_VERSION)

    def test_a_missing_name_is_refused(self):
        data = manifest()
        del data["name"]

        with self.assertRaises(PolicyError) as caught:
            parse_manifest(data)

        self.assertIn("name", str(caught.exception))

    def test_a_missing_version_is_refused(self):
        data = manifest()
        del data["version"]

        with self.assertRaises(PolicyError):
            parse_manifest(data)

    def test_a_missing_min_gitpr_version_is_refused(self):
        data = manifest()
        del data["min_gitpr_version"]

        with self.assertRaises(PolicyError):
            parse_manifest(data)

    def test_an_unsupported_schema_version_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(schema_version=99))

        self.assertIn("schema_version", str(caught.exception))

    def test_a_manifest_that_is_not_a_mapping_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(["not", "a", "manifest"])


class TestClosedSchema(unittest.TestCase):
    """A key GitPR does not know is a mistake, not a value to ignore."""

    def test_an_unknown_top_level_key_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(tests="all the tests"))

        message = str(caught.exception)
        # The key and the pack, so the author knows which file to open and what
        # to delete in it — "invalid manifest" alone would send them reading.
        self.assertIn("tests", message)
        self.assertIn("acme/team-policy", message)

    def test_enabled_is_not_a_key(self):
        """The grill took ``enabled`` out: activating a pack *is* enabling it."""
        with self.assertRaises(PolicyError):
            parse_manifest(manifest(skills={"review": {"enabled": True}}))

    def test_an_unknown_skill_key_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(
                manifest(skills={"review": {"additional_context": "x", "weight": 1}})
            )

    def test_an_unknown_risk_key_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(manifest(risk={"critical_pathes": ["**/db/**"]}))


class TestBaselineBlock(unittest.TestCase):
    """The `baseline:` block, and the validation it may not go around.

    A pack shipping suppressions is the feature's whole point for a team that
    standardises a legacy gate — and the one place it could quietly undo the
    auditability the suppressions exist for. So the entries are put through the
    very validators a hand-edited `baseline.overrides.yml` goes through, and the
    failure is reported with the pack, the half and the index.
    """

    FINGERPRINT = "sha256:" + "a" * 64

    def test_a_block_with_a_suppression_and_debt_parses(self):
        parsed = parse_manifest(
            manifest(
                baseline={
                    "suppressions": [
                        {
                            "scope": "rule",
                            "rule_id": "warning-todo-fixme",
                            "reason": "Noisy rule in legacy code.",
                        }
                    ],
                    "accepted_debt": [
                        {
                            "fingerprint": self.FINGERPRINT,
                            "owner": "platform",
                            "reason": "Migration planned.",
                            "due_date": "2026-12-31",
                        }
                    ],
                }
            )
        )

        self.assertEqual(len(parsed.baseline["suppressions"]), 1)
        self.assertEqual(len(parsed.baseline["accepted_debt"]), 1)
        suppression = parsed.baseline["suppressions"][0]
        self.assertEqual(suppression["scope"], "rule")
        self.assertEqual(suppression["rule_id"], "warning-todo-fixme")

    def test_a_pack_without_the_block_carries_nothing(self):
        self.assertEqual(parse_manifest(manifest()).baseline, {})

    def test_an_unknown_key_in_the_block_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(baseline={"suppression": []}))

        self.assertIn("suppression", str(caught.exception))

    def test_a_suppression_without_a_reason_is_refused(self):
        """The rule that makes a suppression auditable has no exemption for packs."""
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(
                manifest(baseline={"suppressions": [{"scope": "rule", "rule_id": "x"}]})
            )

        message = str(caught.exception)
        self.assertIn("reason", message)
        self.assertIn("acme/team-policy", message)
        self.assertIn("#1", message)

    def test_debt_nobody_owns_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(
                manifest(
                    baseline={
                        "accepted_debt": [
                            {"fingerprint": self.FINGERPRINT, "reason": "Later."}
                        ]
                    }
                )
            )

        self.assertIn("owner", str(caught.exception))

    def test_a_debt_with_an_impossible_due_date_is_refused(self):
        """A deadline nobody can read is a deadline nobody can be held to."""
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(
                manifest(
                    baseline={
                        "accepted_debt": [
                            {
                                "fingerprint": self.FINGERPRINT,
                                "owner": "platform",
                                "reason": "Migration planned.",
                                "due_date": "31/12/2026",
                            }
                        ]
                    }
                )
            )

        message = str(caught.exception)
        self.assertIn("due_date", message)
        self.assertIn("acme/team-policy", message)

    def test_an_unknown_scope_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(
                manifest(
                    baseline={
                        "suppressions": [
                            {"scope": "everything", "reason": "Let it all through."}
                        ]
                    }
                )
            )

    def test_a_block_that_is_not_a_mapping_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(baseline=["all of it"]))

        self.assertIn("mapping", str(caught.exception))

    def test_a_half_that_is_not_a_list_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(baseline={"suppressions": {"scope": "rule"}}))

        self.assertIn("list", str(caught.exception))


class TestSkillNames(unittest.TestCase):
    """A pack configures skills GitPR ships; it cannot invent one."""

    def test_the_registry_is_the_one_config_declares(self):
        from src.config import SKILL_TYPES

        self.assertEqual(set(allowed_skill_types()), set(SKILL_TYPES))

    def test_an_unknown_skill_name_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(
                manifest(skills={"telepathy": {"additional_context": "read minds"}})
            )

        message = str(caught.exception)
        self.assertIn("telepathy", message)
        # The message has to list what *is* allowed, or the author is guessing.
        self.assertIn("review", message)

    def test_every_known_skill_name_is_accepted(self):
        for name in allowed_skill_types():
            with self.subTest(skill=name):
                parsed = parse_manifest(
                    manifest(skills={name: {"additional_context": f"about {name}"}})
                )
                self.assertEqual([s.skill_name for s in parsed.skills], [name])


class TestCredentials(unittest.TestCase):
    """A pack is meant to be shared, so a secret in it is refused up front."""

    def test_find_secret_names_the_rule_that_tripped(self):
        aws_key = 'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"'

        self.assertIsNotNone(find_secret(aws_key))

    def test_find_secret_returns_none_for_clean_text(self):
        self.assertIsNone(find_secret("name: acme/team-policy\nversion: 1.0.0\n"))

    def test_a_manifest_carrying_a_credential_is_refused(self):
        # The secret sits in the raw text, which is what the reader would ship.
        raw = "\n".join(f"{k}: {v}" for k, v in manifest().items())
        raw += '\ntoken: "AKIAIOSFODNN7EXAMPLE"\n'

        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(), raw_text=raw)

        message = str(caught.exception)
        self.assertIn("credential", message)
        self.assertIn("acme/team-policy", message)


class TestPackNames(unittest.TestCase):
    """``namespace/name``, and nothing that could escape the pack directory."""

    def test_a_name_without_a_namespace_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(manifest(name="team-policy"))

    def test_a_name_with_a_path_traversal_is_refused(self):
        for hostile in ("acme/../../etc", "acme/..", "../acme/x", "acme/x/../y"):
            with self.subTest(name=hostile):
                with self.assertRaises(PolicyError):
                    parse_manifest(manifest(name=hostile))

    def test_a_three_segment_name_is_refused(self):
        """One namespace, one name — deeper nesting would make ``extends`` ambiguous."""
        with self.assertRaises(PolicyError):
            parse_manifest(manifest(name="gitpr/laravel/quality"))


class TestParsedPayload(unittest.TestCase):
    """What a valid manifest actually carries into the resolver."""

    def test_extends_becomes_a_reference_per_dependency(self):
        parsed = parse_manifest(
            manifest(
                extends=[{"name": "gitpr/php-security", "version": ">=1.0.0 <2.0.0"}]
            )
        )

        dependency = parsed.dependencies[0]
        self.assertEqual(dependency.name, "gitpr/php-security")
        self.assertEqual(dependency.version, ">=1.0.0 <2.0.0")
        self.assertEqual(dependency.source, PolicySource.BUNDLED)

    def test_an_extends_entry_without_a_version_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(manifest(extends=[{"name": "gitpr/php-security"}]))

    def test_linter_rules_file_and_overrides_are_parsed(self):
        parsed = parse_manifest(
            manifest(
                linter={
                    "rules_file": "linter.yml",
                    "severity_overrides": [
                        {"rule_name": "sec-aws-key", "level": "warning", "reason": "legacy"}
                    ],
                }
            )
        )

        self.assertEqual(parsed.rules_file, "linter.yml")
        self.assertEqual(parsed.severity_overrides[0].rule_name, "sec-aws-key")
        self.assertEqual(parsed.severity_overrides[0].level, "warning")

    def test_protected_paths_and_conventions_are_parsed(self):
        parsed = parse_manifest(
            manifest(
                pr={"required_sections": ["Risks"]},
                commit={"allowed_types": ["feat", "fix"]},
                protected_paths=["config/**"],
            )
        )

        self.assertEqual(parsed.pr["required_sections"], ["Risks"])
        self.assertEqual(parsed.commit["allowed_types"], ["feat", "fix"])
        self.assertEqual(parsed.protected_paths, ["config/**"])

    def test_risk_keeps_only_the_keys_the_engine_reads(self):
        parsed = parse_manifest(
            manifest(
                risk={
                    "critical_paths": ["database/migrations/**"],
                    "test_patterns": ["tests/**"],
                    "weights": {"database_migration": 25},
                }
            )
        )

        self.assertEqual(parsed.risk["critical_paths"], ["database/migrations/**"])
        self.assertEqual(parsed.risk["test_patterns"], ["tests/**"])
        self.assertEqual(parsed.risk["weights"]["database_migration"], 25)

    def test_a_weight_name_the_risk_engine_does_not_know_is_refused(self):
        """A typo'd weight would be dropped in silence, so it is an error here."""
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(manifest(risk={"weights": {"databse_migration": 25}}))

        self.assertIn("databse_migration", str(caught.exception))


class TestDowngradeReason(unittest.TestCase):
    """Weakening a gate is allowed; doing it without a stated reason is not."""

    def test_a_downgrade_without_a_reason_is_refused(self):
        with self.assertRaises(PolicyError) as caught:
            parse_manifest(
                manifest(
                    linter={
                        "severity_overrides": [
                            {"rule_name": "sec-aws-key", "level": "warning"}
                        ]
                    }
                )
            )

        self.assertIn("reason", str(caught.exception))

    def test_a_hardening_needs_no_reason(self):
        parsed = parse_manifest(
            manifest(
                linter={
                    "severity_overrides": [
                        {"rule_name": "my-rule", "level": "error"}
                    ]
                }
            )
        )

        self.assertEqual(parsed.severity_overrides[0].reason, None)

    def test_a_level_outside_the_two_the_engine_implements_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_manifest(
                manifest(
                    linter={
                        "severity_overrides": [
                            {"rule_name": "x", "level": "critical", "reason": "because"}
                        ]
                    }
                )
            )


class TestOverrides(unittest.TestCase):
    """``.gitpr/policy.overrides.yml`` speaks about the repository, and wins."""

    def test_an_empty_overrides_file_parses_to_nothing(self):
        self.assertEqual(parse_overrides(None), {})
        self.assertEqual(parse_overrides({}), {})

    def test_a_severity_override_carries_the_same_rules_as_a_pack(self):
        parsed = parse_overrides(
            {
                "severity_overrides": [
                    {"rule_name": "sec-aws-key", "level": "warning", "reason": "legacy"}
                ]
            }
        )

        self.assertEqual(parsed["severity_overrides"][0].rule_name, "sec-aws-key")

    def test_an_unknown_overrides_key_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_overrides({"everything": True})

    def test_add_remove_is_the_only_way_to_change_a_list(self):
        parsed = parse_overrides(
            {"risk": {"critical_paths": {"add": ["**/db/**"], "remove": ["**/payment/**"]}}}
        )

        block = parsed["risk"]["critical_paths"]
        self.assertEqual(block["add"], ["**/db/**"])
        self.assertEqual(block["remove"], ["**/payment/**"])

    def test_a_bare_list_for_an_additive_key_is_refused(self):
        """Removal is spelled out: a list that silently replaced would hide a drop."""
        with self.assertRaises(PolicyError):
            parse_overrides({"risk": {"critical_paths": ["**/db/**"]}})


if __name__ == "__main__":
    unittest.main()
