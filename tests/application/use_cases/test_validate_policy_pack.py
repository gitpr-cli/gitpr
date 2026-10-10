"""``gitpr policy validate`` — the answer a pack author and a pack adopter both need.

Two properties matter more than the report's shape. First: validation is
**offline and side-effect free** — a pack is text somebody else wrote, and the
command that inspects it must not run anything it contains, which is asserted
here by banning both ``subprocess`` and the network for the whole module.
Second: validation **does not stop at the first error**, because a validator
that reports one problem per run turns fixing a manifest into whack-a-mole.

Targets are directories under ``tempfile`` or the packs GitPR ships, so nothing
here depends on what the developer happens to have in ``~/.gitpr/policies``.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

from src.application.use_cases.validate_policy_pack import (
    parse_pack_target,
    split_reference,
    validate_policy_pack,
)

MANIFEST = """schema_version: 1
name: acme/team-policy
version: 1.0.0
description: The Acme house rules.
min_gitpr_version: ">=1.3.0"
license: MIT
authors:
  - Acme Platform

skills:
  review:
    additional_context: |
      Acme house rule: money is an integer in minor units.

linter:
  rules_file: linter.yml
  severity_overrides:
    - rule_name: acme-no-float-money
      level: warning
      reason: the float check is advisory while the migration is in flight

risk:
  test_patterns:
    - spec/**
  weights:
    large_diff: 20
"""

RULES = """rules:
  - name: acme-no-float-money
    regex: "\\\\bfloat\\\\b"
    message: "Money is an integer in minor units."
    extensions: ["*"]
"""


class PackDirTestCase(unittest.TestCase):
    """A pack directory on ``tempfile``, written from the strings above."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gitpr_policy_validate_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write(self, name, content):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path) or self.dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return path

    def make_pack(self, manifest=MANIFEST, rules=RULES):
        self.write("policy.yml", manifest)
        if rules is not None:
            self.write("linter.yml", rules)
        return self.dir


class TestOffline(PackDirTestCase):
    """Validating text must not execute it or ask anyone about it."""

    def test_no_subprocess_is_spawned(self):
        self.make_pack()
        real = subprocess.run

        def refuse(*args, **kwargs):
            self.fail(f"validate spawned a process: {args[:1]!r}")

        subprocess.run = refuse
        try:
            report = validate_policy_pack(self.dir)
        finally:
            subprocess.run = real

        self.assertTrue(report["ok"])

    def test_no_network_call_is_made(self):
        import socket

        self.make_pack()
        real = socket.create_connection

        def refuse(*args, **kwargs):
            self.fail("validate reached for the network")

        socket.create_connection = refuse
        try:
            report = validate_policy_pack(self.dir)
        finally:
            socket.create_connection = real

        self.assertTrue(report["ok"])


class TestReport(PackDirTestCase):
    def test_a_valid_pack_is_ok_and_reports_what_it_does(self):
        self.make_pack()

        report = validate_policy_pack(self.dir)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["pack"]["name"], "acme/team-policy")
        self.assertEqual(report["pack"]["version"], "1.0.0")
        self.assertEqual(len(report["pack"]["checksum"]), 64)
        self.assertEqual(report["source"], "local_path")

    def test_the_schema_section_reports_compatibility_rather_than_re_deriving_it(self):
        self.make_pack()

        report = validate_policy_pack(self.dir)

        self.assertEqual(report["schema"]["schema_version"], 1)
        self.assertTrue(report["schema"]["gitpr_compatible"])
        self.assertEqual(report["schema"]["min_gitpr_version"], ">=1.3.0")

    def test_skills_are_reported_with_their_size(self):
        self.make_pack()

        report = validate_policy_pack(self.dir)

        review = next(s for s in report["skills"] if s["name"] == "review")
        self.assertGreater(review["characters"], 0)

    def test_the_linter_section_counts_the_rules_and_the_overrides(self):
        self.make_pack()

        report = validate_policy_pack(self.dir)

        self.assertEqual(report["linter"]["rules_count"], 1)
        self.assertEqual(report["linter"]["rule_names"], ["acme-no-float-money"])
        self.assertTrue(report["linter"]["rules_file_found"])
        self.assertEqual(report["linter"]["packs_contributing_rules"], ["acme/team-policy"])

        override = report["linter"]["severity_overrides"][0]
        self.assertEqual(override["rule_name"], "acme-no-float-money")
        self.assertEqual(override["level"], "warning")
        self.assertTrue(override["weakens_the_gate"])

    def test_the_risk_section_carries_what_the_manifest_declared(self):
        self.make_pack()

        report = validate_policy_pack(self.dir)

        self.assertEqual(report["risk"]["test_patterns"], ["spec/**"])
        self.assertEqual(report["risk"]["weights"]["large_diff"], 20)


class TestBrokenPacks(PackDirTestCase):
    """A pack that cannot be read reports why, and never raises."""

    def test_a_directory_without_a_manifest_reports_it(self):
        report = validate_policy_pack(self.dir)

        self.assertFalse(report["ok"])
        self.assertTrue(report["errors"])

    def test_a_path_that_does_not_exist_reports_it(self):
        report = validate_policy_pack(os.path.join(self.dir, "nowhere"))

        self.assertFalse(report["ok"])
        self.assertTrue(report["errors"])

    def test_an_unknown_key_is_reported(self):
        self.make_pack(manifest=MANIFEST + "\ntests: run them all\n")

        report = validate_policy_pack(self.dir)

        self.assertFalse(report["ok"])
        self.assertTrue(any("tests" in error for error in report["errors"]))

    def test_an_unknown_skill_is_reported(self):
        broken = MANIFEST.replace("  review:", "  telepathy:")
        self.make_pack(manifest=broken)

        report = validate_policy_pack(self.dir)

        self.assertFalse(report["ok"])
        self.assertTrue(any("telepathy" in error for error in report["errors"]))

    def test_a_manifest_with_no_extends_target_reports_it(self):
        broken = MANIFEST + '\nextends:\n  - name: acme/nowhere\n    version: ">=1.0.0"\n'
        self.make_pack(manifest=broken)

        report = validate_policy_pack(self.dir)

        self.assertFalse(report["ok"], report)

    def test_a_severity_override_naming_a_rule_that_does_not_exist_is_reported(self):
        broken = MANIFEST.replace("acme-no-float-money", "acme-no-float-mony")
        self.make_pack(manifest=broken)

        report = validate_policy_pack(self.dir)

        self.assertFalse(report["ok"])
        self.assertTrue(
            any("acme-no-float-mony" in error for error in report["errors"])
        )

    def test_a_rules_file_that_is_not_on_disk_is_reported(self):
        self.make_pack(rules=None)

        report = validate_policy_pack(self.dir)

        self.assertFalse(report["ok"], report)
        self.assertTrue(any("linter.yml" in error for error in report["errors"]))

    def test_a_referenced_pack_that_does_not_exist_reports_the_sources_searched(self):
        report = validate_policy_pack("acme/nowhere-at-all")

        self.assertFalse(report["ok"])
        self.assertTrue(any("acme/nowhere-at-all" in e for e in report["errors"]))


class TestBundledPacks(unittest.TestCase):
    """The four packs that ship with GitPR validate as they are shipped."""

    def test_laravel_quality_and_its_dependency(self):
        report = validate_policy_pack("gitpr/laravel-quality")

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(
            [d["name"] for d in report["dependencies"]], ["gitpr/php-security"]
        )
        self.assertEqual(report["dependencies"][0]["range"], ">=1.0.0 <2.0.0")
        self.assertEqual(report["dependencies"][0]["resolved"], "1.0.0")
        # Rules come from both packs, and the report says so.
        self.assertEqual(
            sorted(report["linter"]["packs_contributing_rules"]),
            ["gitpr/laravel-quality", "gitpr/php-security"],
        )
        self.assertGreater(report["linter"]["rules_count"], 1)

    def test_every_bundled_pack_validates(self):
        for name in (
            "gitpr/laravel-quality",
            "gitpr/node-quality",
            "gitpr/php-security",
            "gitpr/vue-quality",
        ):
            with self.subTest(pack=name):
                report = validate_policy_pack(name)
                self.assertTrue(report["ok"], report["errors"])

    def test_a_range_that_excludes_the_shipped_version_is_refused(self):
        report = validate_policy_pack("gitpr/php-security@>=9.0.0")

        self.assertFalse(report["ok"])


class TestTargetParsing(unittest.TestCase):
    """A target is a path or a ``name@range``; the two are told apart by disk."""

    def test_a_directory_becomes_an_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(parse_pack_target(directory), os.path.abspath(directory))

    def test_anything_else_stays_a_reference(self):
        self.assertEqual(
            parse_pack_target("gitpr/laravel-quality"), "gitpr/laravel-quality"
        )

    def test_a_bare_name_means_any_version(self):
        self.assertEqual(
            split_reference("gitpr/php-security"), ("gitpr/php-security", ">=0.0.0")
        )

    def test_a_name_with_a_range_is_split_at_the_last_at_sign(self):
        self.assertEqual(
            split_reference("gitpr/php-security@>=1.0.0 <2.0.0"),
            ("gitpr/php-security", ">=1.0.0 <2.0.0"),
        )

    def test_a_trailing_at_sign_falls_back_to_any_version(self):
        self.assertEqual(
            split_reference("gitpr/php-security@"), ("gitpr/php-security", ">=0.0.0")
        )


if __name__ == "__main__":
    unittest.main()
