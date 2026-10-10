"""Activation and the resolution every later command runs under.

Two halves. The first pins what activation writes: one root pack, the graph
below it, and a checksum per pack, into a file meant to be committed. The second
— and the one that matters more — pins what resolution *refuses*: a pack
removed from disk, a checksum that no longer matches, a version pinned to a
range nothing satisfies. An active pack is a promise that a gate is in force,
and half-keeping it is worse than not keeping it, because the output would still
carry the policy's name.

The ``no_network`` guard is the third half of the point: resolution reads files
and hashes them, and a run that reached for a registry would be a different
feature wearing this one's name.
"""

import ipaddress
import os
import shutil
import socket
import tempfile
import unittest
from unittest.mock import patch

import pytest
from src.infrastructure.policy import local_policy_repository

from src.application.use_cases.activate_policy_pack import (
    activate_policy_pack,
    build_lockfile,
    deactivate_policy_pack,
    describe_lockfile,
)
from src.application.use_cases.resolve_effective_policy import (
    locked_reference,
    resolve_effective_policy,
)
from src.domain.policy import PolicyError, get_active_policy, set_active_policy


def _blocked():
    raise AssertionError("resolving a policy must not touch the network")


def _is_loopback(address):
    host = address[0] if isinstance(address, (tuple, list)) and address else address
    try:
        return ipaddress.ip_address(str(host)).is_loopback
    except ValueError:
        return str(host) == "localhost"


def _guard_method(real):
    def guarded(self, address, *args, **kwargs):
        if not _is_loopback(address):
            _blocked()
        return real(self, address, *args, **kwargs)

    return guarded


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any attempt to reach another machine fails the test.

    Copied from ``tests/split/conftest.py``: that guard is per-directory, and
    this module needs it too.
    """
    monkeypatch.setattr(socket.socket, "connect", _guard_method(socket.socket.connect))
    monkeypatch.setattr(
        socket.socket, "connect_ex", _guard_method(socket.socket.connect_ex)
    )


TEAM_MANIFEST = """schema_version: 1
name: acme/team-policy
version: 1.0.0
min_gitpr_version: ">=1.3.0"
license: MIT

skills:
  review:
    additional_context: |
      Acme house rule: money is an integer in minor units.

linter:
  rules_file: linter.yml
"""

RULES = """rules:
  - name: acme-no-float-money
    regex: "\\\\bfloat\\\\b"
    message: "Money is an integer in minor units."
    extensions: ["*"]
"""

BASE_MANIFEST = """schema_version: 1
name: acme/base-policy
version: 1.0.0
min_gitpr_version: ">=1.3.0"

skills:
  commit:
    additional_context: |
      Acme house rule: the scope names the squad, not the module.
"""


class RepoTestCase(unittest.TestCase):
    """A repository directory and a pack store, both on ``tempfile``.

    ``setUp`` resets the process-wide policy: it is published the way
    ``src/i18n`` publishes the language, so a test that activated one would
    otherwise leak it into every test after it.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gitpr_policy_activate_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = os.path.join(self.root, "repo")
        self.store = os.path.join(self.root, "store")
        os.makedirs(self.repo)
        os.makedirs(self.store)
        # The installed-pack directory is the user's own; redirect it at the
        # module the search order resolves it from, so a pack written here is
        # found exactly as an installed one would be — and nothing touches the
        # developer's real ~/.gitpr/policies.
        patcher = patch.object(
            local_policy_repository, "installed_policies_dir", return_value=self.store
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        set_active_policy(None)
        self.addCleanup(set_active_policy, None)

    def write(self, directory, name, content):
        path = os.path.join(directory, name)
        os.makedirs(os.path.dirname(path) or directory, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return path

    def make_pack(self, name, manifest, rules=RULES, store=None):
        """Writes a pack into the store under the flat directory convention."""
        directory = os.path.join(
            store or self.store, local_policy_repository.install_dir_name(name)
        )
        self.write(directory, "policy.yml", manifest)
        if rules is not None:
            self.write(directory, "linter.yml", rules)
        return directory

    def resolve(self, **kwargs):
        return resolve_effective_policy(self.repo, **kwargs)


class TestBuildLockfile(RepoTestCase):
    """What activation writes — before anything is written."""

    def test_a_single_pack_pins_itself(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)

        data = build_lockfile("acme/team-policy", self.repo)

        self.assertEqual(data["root"]["name"], "acme/team-policy")
        self.assertEqual(data["root"]["version"], "1.0.0")
        self.assertEqual(data["root"]["source"], "installed")
        self.assertEqual(len(data["root"]["checksum"]), 64)
        self.assertEqual([p["name"] for p in data["packs"]], ["acme/team-policy"])

    def test_the_lockfile_records_every_dependency_with_its_own_checksum(self):
        self.make_pack("acme/base-policy", BASE_MANIFEST)
        self.make_pack(
            "acme/team-policy",
            TEAM_MANIFEST + '\nextends:\n  - name: acme/base-policy\n    version: ">=1.0.0"\n',
        )

        data = build_lockfile("acme/team-policy", self.repo)

        self.assertEqual(
            [p["name"] for p in data["packs"]], ["acme/base-policy", "acme/team-policy"]
        )
        checksums = {p["name"]: p["checksum"] for p in data["packs"]}
        self.assertNotEqual(checksums["acme/base-policy"], checksums["acme/team-policy"])

    def test_a_pack_inside_the_repository_is_recorded_by_relative_path(self):
        # A team pack lives wherever the team put it, rather than in the flat
        # directory installed packs use — and the lockfile records where, so a
        # teammate reads it from the same place instead of from their own store.
        pack_dir = os.path.join(self.repo, ".gitpr", "policies", "team")
        self.write(pack_dir, "policy.yml", TEAM_MANIFEST)
        self.write(pack_dir, "linter.yml", RULES)

        data = build_lockfile("acme/team-policy", self.repo)

        self.assertEqual(data["root"]["source"], "local_path")
        self.assertEqual(data["root"]["path"], ".gitpr/policies/team")

    def test_a_pack_outside_the_repository_is_recorded_by_name_only(self):
        """So a teammate with the pack installed elsewhere still gets a valid lockfile."""
        self.make_pack("acme/team-policy", TEAM_MANIFEST)

        data = build_lockfile("acme/team-policy", self.repo)

        self.assertNotIn("path", data["root"])

    def test_building_writes_nothing(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)

        build_lockfile("acme/team-policy", self.repo)

        self.assertFalse(os.path.exists(os.path.join(self.repo, ".gitpr")))

    def test_an_unresolvable_pack_raises_without_writing(self):
        with self.assertRaises(PolicyError):
            build_lockfile("acme/nowhere", self.repo)

        self.assertFalse(os.path.exists(os.path.join(self.repo, ".gitpr")))

    def test_describe_lockfile_counts_only_the_dependencies(self):
        self.make_pack("acme/base-policy", BASE_MANIFEST)
        self.make_pack(
            "acme/team-policy",
            TEAM_MANIFEST + '\nextends:\n  - name: acme/base-policy\n    version: ">=1.0.0"\n',
        )

        data = build_lockfile("acme/team-policy", self.repo)

        self.assertEqual(
            describe_lockfile(data), "acme/team-policy@1.0.0 with 1 dependency pack(s)"
        )


class TestActivation(RepoTestCase):
    def test_activating_writes_the_lockfile(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)

        path = activate_policy_pack("acme/team-policy", self.repo)

        self.assertTrue(os.path.isfile(path))
        self.assertEqual(path, os.path.join(self.repo, ".gitpr", "policy.lock.yml"))

    def test_the_next_run_reads_the_lockfile_and_publishes_the_policy(self):
        """Activation records a decision; resolution is what enforces it.

        ``use`` writes the file and exits, so the pack takes force on the run
        after it — which is also what makes the lockfile, rather than this
        process, the thing the team shares.
        """
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        set_active_policy(None)

        self.resolve()

        self.assertTrue(get_active_policy().is_active)
        self.assertEqual(get_active_policy().policy_tag(), "acme/team-policy@1.0.0")

    def test_activating_a_second_pack_replaces_the_first(self):
        """One root pack per repository; the graph below it is reached by extends."""
        self.make_pack("acme/base-policy", BASE_MANIFEST)
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/base-policy", self.repo)

        activate_policy_pack("acme/team-policy", self.repo)

        policy = self.resolve()
        self.assertEqual([p.name for p in policy.packs], ["acme/team-policy"])
        self.assertEqual(policy.policy_tag(), "acme/team-policy@1.0.0")

    def test_deactivating_removes_the_lockfile_and_leaves_the_rest(self):
        pack_dir = self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        self.write(os.path.join(self.repo, ".gitpr"), "policy.overrides.yml", "risk: {}\n")

        removed = deactivate_policy_pack(self.repo)

        self.assertTrue(removed)
        self.assertFalse(os.path.isfile(os.path.join(self.repo, ".gitpr", "policy.lock.yml")))
        # A decision to stop following a pack is not a decision to delete it.
        self.assertTrue(os.path.isdir(pack_dir))
        self.assertTrue(
            os.path.isfile(os.path.join(self.repo, ".gitpr", "policy.overrides.yml"))
        )
        self.assertFalse(get_active_policy().is_active)

    def test_deactivating_a_repository_that_had_none_says_so(self):
        self.assertFalse(deactivate_policy_pack(self.repo))

    def test_locked_reference_reports_the_root_pack(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)

        reference = locked_reference(self.repo)

        self.assertEqual(reference.name, "acme/team-policy")
        self.assertEqual(reference.version, "1.0.0")

    def test_locked_reference_is_none_without_a_lockfile(self):
        self.assertIsNone(locked_reference(self.repo))


class TestResolution(RepoTestCase):
    def test_a_repository_with_no_lockfile_gets_an_empty_policy(self):
        """This is the line §12.10 rests on: nothing active, nothing changes."""
        policy = self.resolve()

        self.assertFalse(policy.is_active)
        self.assertEqual(policy.cache_scope(), "")
        self.assertEqual(get_active_policy().policy_tag(), "")

    def test_resolution_composes_the_whole_graph(self):
        self.make_pack("acme/base-policy", BASE_MANIFEST)
        self.make_pack(
            "acme/team-policy",
            TEAM_MANIFEST + '\nextends:\n  - name: acme/base-policy\n    version: ">=1.0.0"\n',
        )
        activate_policy_pack("acme/team-policy", self.repo)

        policy = self.resolve()

        self.assertEqual(
            [p.name for p in policy.packs], ["acme/base-policy", "acme/team-policy"]
        )
        self.assertIn("Acme house rule", policy.skill_context_for("review"))
        self.assertIn("Acme house rule", policy.skill_context_for("commit"))

    def test_the_cache_scope_carries_the_name_the_version_and_the_checksum(self):
        """Without this, activating a pack over a cached diff would change nothing."""
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)

        policy = self.resolve()

        scope = policy.cache_scope()
        self.assertIn("::policy::acme/team-policy@1.0.0::", scope)
        self.assertEqual(len(scope.rsplit("::", 1)[-1]), 64)

    def test_overrides_are_read_from_the_repository_and_win(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        self.write(
            os.path.join(self.repo, ".gitpr"),
            "policy.overrides.yml",
            'protected_paths:\n  add:\n    - legacy/**\n',
        )

        policy = self.resolve()

        self.assertEqual(policy.protected_paths, ["legacy/**"])


class TestResolutionRefuses(RepoTestCase):
    """The three failures that abort instead of degrading."""

    def test_a_pack_removed_from_disk_aborts_and_says_where_it_looked(self):
        pack_dir = self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        shutil.rmtree(pack_dir)

        with self.assertRaises(PolicyError) as caught:
            self.resolve()

        message = str(caught.exception)
        self.assertIn("acme/team-policy", message)
        # Naming the roots is what turns "not found" into "here is where to put it".
        self.assertIn(self.store, message)

    def test_an_edited_asset_aborts_and_says_how_to_reactivate(self):
        pack_dir = self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        self.write(pack_dir, "linter.yml", RULES + "  - name: added-later\n")

        with self.assertRaises(PolicyError) as caught:
            self.resolve()

        message = str(caught.exception)
        self.assertIn("changed since it was activated", message)
        self.assertIn("gitpr policy use acme/team-policy@1.0.0", message)

    def test_an_edited_manifest_aborts_too(self):
        pack_dir = self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        self.write(pack_dir, "policy.yml", TEAM_MANIFEST + "description: edited\n")

        with self.assertRaises(PolicyError):
            self.resolve()

    def test_a_version_that_vanished_after_an_upgrade_aborts(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        # Rewrite the lockfile to pin a version that is not on this machine.
        from src.infrastructure.policy.local_policy_repository import (
            read_lockfile,
            write_lockfile,
        )

        data = read_lockfile(self.repo)
        for entry in [data["root"], *data["packs"]]:
            entry["version"] = "9.9.9"
            entry["source"] = "bundled"
            entry.pop("path", None)
        write_lockfile(data, self.repo)

        with self.assertRaises(PolicyError) as caught:
            self.resolve()

        self.assertIn("9.9.9", str(caught.exception))

    def test_a_lockfile_pinning_a_name_that_now_holds_another_pack_aborts(self):
        """The failure a hand-edited or merged lockfile produces."""
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        from src.infrastructure.policy.local_policy_repository import (
            read_lockfile,
            write_lockfile,
        )

        data = read_lockfile(self.repo)
        data["root"]["name"] = "acme/something-else"
        data["root"]["source"] = "bundled"
        data["root"].pop("path", None)
        write_lockfile(data, self.repo)

        with self.assertRaises(PolicyError):
            self.resolve()

    def test_a_malformed_lockfile_says_how_to_recover(self):
        self.write(os.path.join(self.repo, ".gitpr"), "policy.lock.yml", "schema_version: 1\n")

        with self.assertRaises(PolicyError) as caught:
            self.resolve()

        message = str(caught.exception)
        self.assertIn("root", message)
        self.assertIn("policy use", message)

    def test_a_broken_overrides_file_aborts(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        self.write(
            os.path.join(self.repo, ".gitpr"),
            "policy.overrides.yml",
            "protected_paths:\n  - legacy/**\n",  # a bare list, not add/remove
        )

        with self.assertRaises(PolicyError):
            self.resolve()

    def test_strict_false_degrades_to_a_warning_instead_of_raising(self):
        """The escape hatch the ``gitpr policy`` commands run under."""
        pack_dir = self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        shutil.rmtree(pack_dir)

        policy = self.resolve(strict=False)

        self.assertFalse(policy.is_active)
        self.assertTrue(policy.warnings)

    def test_a_disabled_run_ignores_an_active_pack_entirely(self):
        self.make_pack("acme/team-policy", TEAM_MANIFEST)
        activate_policy_pack("acme/team-policy", self.repo)
        os.environ["GITPR_POLICY_ENABLED"] = "false"
        self.addCleanup(os.environ.pop, "GITPR_POLICY_ENABLED", None)

        policy = self.resolve()

        self.assertFalse(policy.is_active)


if __name__ == "__main__":
    unittest.main()
