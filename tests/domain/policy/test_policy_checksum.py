"""The digest the lockfile records, and the things it must and must not notice.

The checksum is the only thing standing between "the pack I activated" and "the
pack that is on disk now", so the interesting cases are the *negative* ones: it
has to change when the manifest or a declared rule file changes, and it has to
ignore everything else — an unrelated README edit must not invalidate a policy,
or every repository would be re-activating packs for nothing.
"""

import os
import shutil
import tempfile
import unittest

from src.domain.policy import checksum_bytes, checksum_file, checksum_pack

MANIFEST = """schema_version: 1
name: acme/team-policy
version: 1.0.0
min_gitpr_version: ">=1.0.0"
"""

RULES = """rules:
  - name: acme-no-float-money
    regex: "\\\\bfloat\\\\b"
    message: "Money is an integer in minor units."
    extensions: ["*"]
"""


class ChecksumTestCase(unittest.TestCase):
    """A real pack directory on ``tempfile``, written file by file."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gitpr_policy_checksum_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write(self, name, content):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path) or self.dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return path

    def digest(self, raw=MANIFEST, rules=None, assets=None):
        self.write("policy.yml", raw)
        if rules is not None:
            self.write("linter.yml", rules)
        return checksum_pack(self.dir, assets)


class TestChecksumBytes(unittest.TestCase):
    def test_it_is_a_sha256_hex_digest(self):
        digest = checksum_bytes(b"policy")

        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))

    def test_the_same_bytes_give_the_same_digest(self):
        self.assertEqual(checksum_bytes(b"x"), checksum_bytes(b"x"))

    def test_different_bytes_give_different_digests(self):
        self.assertNotEqual(checksum_bytes(b"x"), checksum_bytes(b"y"))


class TestChecksumFile(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gitpr_policy_checksum_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def test_it_matches_the_bytes_it_read(self):
        path = os.path.join(self.dir, "policy.yml")
        with open(path, "wb") as handle:
            handle.write(b"name: acme/x\n")

        self.assertEqual(checksum_file(path), checksum_bytes(b"name: acme/x\n"))


class TestChecksumPack(ChecksumTestCase):
    def test_the_manifest_alone_produces_a_digest(self):
        first = self.digest()
        second = self.digest()

        self.assertEqual(first, second)

    def test_a_changed_manifest_changes_the_digest(self):
        before = self.digest()
        after = self.digest(raw=MANIFEST + "description: added later\n")

        self.assertNotEqual(before, after)

    def test_a_declared_asset_is_part_of_the_digest(self):
        before = self.digest(rules=RULES, assets=["linter.yml"])
        after = self.digest(
            rules=RULES + "  - name: acme-second-rule\n", assets=["linter.yml"]
        )

        self.assertNotEqual(before, after)

    def test_editing_an_undeclared_file_changes_nothing(self):
        """A pack is what it declares; a README edit is not a policy change."""
        before = self.digest(rules=RULES, assets=["linter.yml"])
        self.write("README.md", "notes about this pack\n")
        after = self.digest(rules=RULES, assets=["linter.yml"])

        self.assertEqual(before, after)

    def test_the_order_assets_are_declared_in_does_not_matter(self):
        self.write("policy.yml", MANIFEST)
        self.write("a.yml", "rules: []\n")
        self.write("b.yml", "rules: []\n")

        self.assertEqual(
            checksum_pack(self.dir, ["a.yml", "b.yml"]),
            checksum_pack(self.dir, ["b.yml", "a.yml"]),
        )

    def test_a_declared_asset_that_is_missing_is_skipped_not_fatal(self):
        """The manifest already refuses it by name; the digest stays total."""
        self.write("policy.yml", MANIFEST)
        self.write("linter.yml", RULES)

        with_missing = checksum_pack(self.dir, ["linter.yml", "absent.yml"])
        without = checksum_pack(self.dir, ["linter.yml"])

        self.assertEqual(with_missing, without)

    def test_a_missing_manifest_raises(self):
        with self.assertRaises(FileNotFoundError):
            checksum_pack(self.dir, [])

    def test_the_digest_is_over_raw_bytes_so_line_endings_count(self):
        """Read in binary, with no encoding pass in between.

        The consequence is worth knowing: a checkout that rewrites a pack's
        line endings (``core.autocrlf`` on a repository-versioned pack) changes
        its digest and the run aborts until it is reactivated. That is the loud
        half of the trade — the alternative is a digest that cannot tell a
        rewritten file from the one that was activated.
        """
        self.write("policy.yml", MANIFEST)
        lf_digest = checksum_pack(self.dir, [])

        self.write("policy.yml", MANIFEST.replace("\n", "\r\n"))
        crlf_digest = checksum_pack(self.dir, [])

        self.assertNotEqual(lf_digest, crlf_digest)

    def test_the_manifest_digest_is_of_the_file_as_written(self):
        self.write("policy.yml", MANIFEST)

        self.assertEqual(
            checksum_pack(self.dir, []),
            checksum_bytes(
                f"policy.yml:{checksum_file(os.path.join(self.dir, 'policy.yml'))}".encode(
                    "utf-8"
                )
            ),
        )


class TestTheBundledPacks(unittest.TestCase):
    """The four packs GitPR ships, hashed as the loader hashes them.

    These are the only files a checksum test can point at without inventing a
    fixture, and they are the ones a wheel must carry — so they double as the
    packaging check that the manifest assets are actually present.
    """

    def setUp(self):
        from src.infrastructure.policy.local_policy_repository import (
            bundled_policies_dir,
        )

        self.root = bundled_policies_dir()

    def test_the_four_packs_ship_with_their_manifests_and_rules(self):
        packs = sorted(
            name
            for name in os.listdir(self.root)
            if os.path.isdir(os.path.join(self.root, name))
        )

        self.assertEqual(
            packs, ["laravel-quality", "node-quality", "php-security", "vue-quality"]
        )
        for name in packs:
            with self.subTest(pack=name):
                digest = checksum_pack(os.path.join(self.root, name), ["linter.yml"])
                self.assertEqual(len(digest), 64)

    def test_two_different_bundled_packs_hash_differently(self):
        self.assertNotEqual(
            checksum_pack(os.path.join(self.root, "laravel-quality"), ["linter.yml"]),
            checksum_pack(os.path.join(self.root, "php-security"), ["linter.yml"]),
        )


if __name__ == "__main__":
    unittest.main()
