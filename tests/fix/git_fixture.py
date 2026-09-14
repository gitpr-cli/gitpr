"""A throwaway git repository for the ``gitpr fix`` tests.

Applying, reversing and branching cannot be tested against mocks: the whole
point is what git does to a real tree. This base class follows the one existing
precedent in the suite (tests/test_suggest_reviewers.py) — ``tempfile.mkdtemp``
plus ``addCleanup``, and a ``_git`` that pins ``core.autocrlf=false`` and
``commit.gpgsign=false`` so the fixture behaves the same on every machine.

Patches are never hand-written: ``patch_for`` writes the new content, captures
the ``git diff`` that produced it, and puts the file back. A test therefore
starts from a patch git itself generated, which is the only way "it applies" is
a meaningful assertion.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

DEFAULT_IDENTITY = ("GitPR Fix Tests", "fix-tests@example.com")


class GitRepoTestCase(unittest.TestCase):
    """A TestCase whose working directory is a fresh repository on ``main``."""

    #: Overridden by subclasses to make the temp prefix self-describing.
    prefix = "gitpr_fix_"

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix=self.prefix)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self._git("init", "-b", "main")
        self._git("config", "core.autocrlf", "false")
        self._git("config", "commit.gpgsign", "false")

    # ── git plumbing ─────────────────────────────────────────────────────
    def _git(self, *args, identity=DEFAULT_IDENTITY, check=True):
        """Run git inside the fixture repository and return the CompletedProcess."""
        name, email = identity
        cmd = [
            "git",
            "-c", f"user.name={name}",
            "-c", f"user.email={email}",
            "-c", "core.autocrlf=false",
            "-c", "commit.gpgsign=false",
        ] + list(args)
        return subprocess.run(
            cmd,
            cwd=self.dir,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check,
        )

    # ── files ────────────────────────────────────────────────────────────
    def write(self, name, content):
        """Write *content* to *name*, always with LF endings."""
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path) or self.dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)

    def read(self, name):
        """Read *name* back from the working tree."""
        with open(
            os.path.join(self.dir, name), "r", encoding="utf-8", errors="replace"
        ) as handle:
            return handle.read()

    def exists(self, name):
        return os.path.exists(os.path.join(self.dir, name))

    # ── commits and patches ──────────────────────────────────────────────
    def commit(self, name, content, message="chore: update", identity=DEFAULT_IDENTITY):
        """Write *name* and commit it."""
        self.write(name, content)
        self._git("add", "--", name)
        self._git("commit", "-m", message, identity=identity)

    def patch_for(self, name, content):
        """Return a real diff that changes *name* to *content*, then revert it.

        The file must already be committed, so that ``git diff`` describes the
        change against HEAD. Afterwards the tree is exactly as it was, which is
        what lets a test call this and then assert the patch applies.
        """
        original = self.read(name)
        self.write(name, content)
        diff = self._git("diff", "--", name).stdout
        self.write(name, original)
        return diff

    def status_porcelain(self):
        """The working tree's fingerprint, for before/after comparisons."""
        return self._git("status", "--porcelain").stdout

    def current_branch(self):
        return self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    def seed(self):
        """Create and commit ``src/app.py``; returns its committed content.

        Every test starts from this one file, so a patch built with
        ``patch_for`` has a stable target to apply against.
        """
        content = "def greet(name):\n    return f'Hello, {name}'\n"
        self.commit("src/app.py", content, message="chore: seed")
        return content
