"""Version ranges, pack names and asset containment.

These three checks are what keep a pack from being *loaded at all* when it does
not belong on this machine, and what keeps a manifest from reading a file
somewhere it has no business reading. They are pure, so they run without a
fixture on disk — except the containment check, which needs a real directory to
resolve against, and gets one from ``tempfile``.
"""

import os
import shutil
import tempfile
import unittest

from src.domain.policy import (
    PolicyError,
    check_gitpr_compatibility,
    check_skill_name,
    is_gitpr_compatible,
    parse_semver,
    parse_specifier,
    resolve_asset_path,
    validate_pack_name,
)


class TestPackName(unittest.TestCase):
    """``namespace/name``: the shape that makes ``extends`` unambiguous."""

    def test_a_namespaced_name_is_accepted(self):
        for name in ("gitpr/laravel-quality", "acme/team_policy", "me/policy.v2"):
            with self.subTest(name=name):
                validate_pack_name(name)  # must not raise

    def test_names_that_escape_or_confuse_are_refused(self):
        for name in (
            "",
            "team-policy",
            "acme/",
            "/policy",
            "acme/../etc",
            "acme/a/b",
            "acme\\policy",
            "acme policy",
        ):
            with self.subTest(name=name):
                with self.assertRaises(PolicyError):
                    validate_pack_name(name)


class TestSemVer(unittest.TestCase):
    """Three components, because a range comparison needs all three."""

    def test_a_three_component_version_parses(self):
        self.assertEqual(str(parse_semver("1.3.0")), "1.3.0")

    def test_a_pre_release_suffix_is_allowed(self):
        self.assertEqual(str(parse_semver("1.0.0-rc1")), "1.0.0rc1")

    def test_two_components_are_refused(self):
        """``packaging`` reads ``1.0`` as valid PEP 440; SemVer does not."""
        with self.assertRaises(PolicyError) as caught:
            parse_semver("1.0")

        self.assertIn("MAJOR.MINOR.PATCH", str(caught.exception))

    def test_text_is_refused(self):
        with self.assertRaises(PolicyError):
            parse_semver("latest")


class TestSpecifier(unittest.TestCase):
    """Three spellings, all of them written by hand, all meaning a range."""

    def test_the_canonical_comma_form(self):
        self.assertIn("1.3.0", parse_specifier(">=1.0.0,<2.0.0"))

    def test_the_space_form_reads_the_same_as_the_comma_form(self):
        """YAML authors write a space; a specifier never contains one."""
        self.assertEqual(
            str(parse_specifier(">=1.0.0 <2.0.0")),
            str(parse_specifier(">=1.0.0,<2.0.0")),
        )

    def test_a_bare_version_means_exactly_that_version(self):
        exact = parse_specifier("1.0.0")

        self.assertIn("1.0.0", exact)
        self.assertNotIn("1.0.1", exact)

    def test_the_error_quotes_what_was_written(self):
        with self.assertRaises(PolicyError) as caught:
            parse_specifier("approximately 1.0")

        self.assertIn("approximately 1.0", str(caught.exception))


class TestGitprCompatibility(unittest.TestCase):
    """A pack states which GitPR builds it was written against."""

    def test_a_satisfied_range_is_compatible(self):
        self.assertTrue(is_gitpr_compatible(">=1.0.0,<2.0.0", "1.3.0"))

    def test_a_range_above_the_running_build_is_not(self):
        self.assertFalse(is_gitpr_compatible(">=2.0.0", "1.3.0"))

    def test_an_unparseable_running_version_counts_as_compatible(self):
        """This gates *third-party* packs; refusing them all over our own odd
        version string would be the worse failure."""
        self.assertTrue(is_gitpr_compatible(">=9.0.0", "not a version"))

    def test_checking_raises_and_names_the_upgrade(self):
        with self.assertRaises(PolicyError) as caught:
            check_gitpr_compatibility(">=2.0.0", "1.3.0", "acme/team-policy")

        message = str(caught.exception)
        self.assertIn("acme/team-policy", message)
        self.assertIn(">=2.0.0", message)
        self.assertIn("pip install --upgrade gitpr-cli", message)


class TestSkillNames(unittest.TestCase):
    """The registry is closed: a pack configures what GitPR runs."""

    def test_a_known_skill_passes(self):
        check_skill_name("review", "acme/team-policy")  # must not raise

    def test_an_unknown_skill_raises_with_the_list_of_what_exists(self):
        with self.assertRaises(PolicyError) as caught:
            check_skill_name("telepathy", "acme/team-policy")

        message = str(caught.exception)
        self.assertIn("telepathy", message)
        self.assertIn("review", message)


class TestAssetPath(unittest.TestCase):
    """A manifest may only read files inside its own directory."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gitpr_policy_assets_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def test_a_relative_path_inside_the_pack_resolves(self):
        expected = os.path.join(self.dir, "linter.yml")

        self.assertEqual(resolve_asset_path(self.dir, "linter.yml"), expected)

    def test_a_nested_relative_path_is_fine(self):
        expected = os.path.join(self.dir, "rules", "php.yml")

        self.assertEqual(resolve_asset_path(self.dir, "rules/php.yml"), expected)

    def test_climbing_out_of_the_pack_is_refused(self):
        for hostile in ("../linter.yml", "../../etc/passwd", "rules/../../outside.yml"):
            with self.subTest(path=hostile):
                with self.assertRaises(PolicyError):
                    resolve_asset_path(self.dir, hostile, "acme/team-policy")

    def test_an_absolute_path_is_refused(self):
        absolute = os.path.abspath(os.sep + "etc" + os.sep + "passwd")

        with self.assertRaises(PolicyError):
            resolve_asset_path(self.dir, absolute, "acme/team-policy")

    def test_a_windows_drive_qualified_path_is_refused(self):
        with self.assertRaises(PolicyError):
            resolve_asset_path(self.dir, "C:/windows/system32/config", "acme/team-policy")

    def test_an_empty_path_is_refused(self):
        for empty in ("", "   "):
            with self.subTest(path=empty):
                with self.assertRaises(PolicyError):
                    resolve_asset_path(self.dir, empty, "acme/team-policy")


if __name__ == "__main__":
    unittest.main()
