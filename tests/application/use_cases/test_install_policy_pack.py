"""Installing a pack: validate the source, then copy it — never merge.

There is no registry and no download here, so what is worth pinning is the
order. A broken pack must not land in the user's policies directory, because
every later command in every repository would fail its resolution instead of
this one command failing for a reason the user can read. And an occupied
destination is refused rather than merged: half of one pack and half of another
would still parse, which is the worst possible outcome.

``target_dir`` exists for exactly these tests, so nothing below writes to the
developer's real ``~/.gitpr/policies``.
"""

import os
import shutil
import tempfile
import unittest

from src.application.use_cases.install_policy_pack import (
    install_policy_pack,
    load_source_pack,
)
from src.domain.policy import PolicyError

MANIFEST = """schema_version: 1
name: acme/team-policy
version: 1.0.0
min_gitpr_version: ">=1.3.0"

linter:
  rules_file: linter.yml
"""

RULES = """rules:
  - name: acme-no-float-money
    regex: "\\\\bfloat\\\\b"
    message: "Money is an integer in minor units."
    extensions: ["*"]
"""


class InstallTestCase(unittest.TestCase):
    """A source pack and a destination store, both on ``tempfile``."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_policy_install_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.source = os.path.join(self.root, "source")
        # Where `gitpr policy install` would put this pack, with the store
        # redirected away from the real home directory. The flat directory name
        # is `installed_pack_dir`'s business and is asserted on its own below.
        from src.infrastructure.policy.local_policy_repository import install_dir_name

        self.store = os.path.join(self.root, "store")
        self.destination = os.path.join(self.store, install_dir_name("acme/team-policy"))

    def write_source(self, manifest=MANIFEST, rules=RULES, extra=None):
        self.write(self.source, "policy.yml", manifest)
        if rules is not None:
            self.write(self.source, "linter.yml", rules)
        for name, content in (extra or {}).items():
            self.write(self.source, name, content)
        return self.source

    def write(self, directory, name, content):
        path = os.path.join(directory, name)
        os.makedirs(os.path.dirname(path) or directory, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return path

    def install(self, **kwargs):
        """Installs into the redirected store, the way the CLI would."""
        return install_policy_pack(self.source, target_dir=self.destination, **kwargs)


class TestLoadSourcePack(InstallTestCase):
    def test_a_valid_source_is_read(self):
        self.write_source()

        pack = load_source_pack(self.source)

        self.assertEqual(pack.manifest.name, "acme/team-policy")
        self.assertEqual(len(pack.rules), 1)

    def test_a_missing_directory_says_what_the_command_takes(self):
        with self.assertRaises(PolicyError) as caught:
            load_source_pack(os.path.join(self.root, "nowhere"))

        message = str(caught.exception)
        self.assertIn("policy install", message)
        self.assertIn("policy.yml", message)

    def test_a_directory_without_a_manifest_is_refused(self):
        os.makedirs(self.source)

        with self.assertRaises(PolicyError):
            load_source_pack(self.source)

    def test_a_broken_manifest_is_refused_before_anything_is_copied(self):
        self.write_source(manifest=MANIFEST + "\nunknown_key: true\n")

        with self.assertRaises(PolicyError):
            load_source_pack(self.source)


class TestInstall(InstallTestCase):
    def test_a_pack_is_copied_to_the_destination_it_was_given(self):
        self.write_source()

        destination = self.install()

        self.assertEqual(destination, self.destination)
        self.assertTrue(os.path.isfile(os.path.join(destination, "policy.yml")))
        self.assertTrue(os.path.isfile(os.path.join(destination, "linter.yml")))

    def test_the_installed_copy_is_readable_as_a_pack(self):
        self.write_source()

        destination = self.install()

        self.assertEqual(load_source_pack(destination).manifest.name, "acme/team-policy")

    def test_an_occupied_destination_is_refused_without_overwrite(self):
        self.write_source()
        self.install()

        with self.assertRaises(PolicyError) as caught:
            self.install()

        self.assertIn("--force", str(caught.exception))

    def test_overwrite_replaces_rather_than_merges(self):
        self.write_source(extra={"stale.yml": "rules: []\n"})
        destination = self.install()
        self.assertTrue(os.path.isfile(os.path.join(destination, "stale.yml")))

        # The source no longer carries the file the first copy had.
        os.remove(os.path.join(self.source, "stale.yml"))
        self.install(overwrite=True)

        self.assertFalse(
            os.path.isfile(os.path.join(destination, "stale.yml")),
            "a replacement must not leave a file from the previous copy behind",
        )

    def test_a_broken_source_never_reaches_the_store(self):
        self.write_source(rules=None)  # the manifest declares linter.yml

        with self.assertRaises(PolicyError):
            self.install()

        self.assertFalse(os.path.exists(self.destination))

    def test_everything_the_pack_carries_travels_with_it(self):
        """The copy is a copy: a README and a CHANGELOG are part of the pack."""
        self.write_source(extra={"README.md": "# Team policy\n", "CHANGELOG.md": "## 1.0.0\n"})

        destination = self.install()

        self.assertEqual(
            sorted(os.listdir(destination)),
            ["CHANGELOG.md", "README.md", "linter.yml", "policy.yml"],
        )


if __name__ == "__main__":
    unittest.main()
