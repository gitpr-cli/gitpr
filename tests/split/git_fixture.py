"""A throwaway repository for the ``gitpr split`` tests.

Split is a claim about what git does to a working tree and an index: which
hunks land in the index, which commit carries which file, whether the tree is
byte-identical at the end. None of that survives being mocked, so the tests run
against a real repository — the one ``tests/fix/git_fixture.py`` already builds,
which pins ``core.autocrlf=false`` and ``commit.gpgsign=false`` so the fixture
behaves the same on every machine.

What this subclass adds is a working tree worth splitting: files whose lines are
numbered, so a test can change line 3 and line 38 of the same file and know it
produced two separate hunks rather than one merged block.
"""
import contextlib
import os

from unittest.mock import patch

from src.split.generate_split_plan import generate_split_plan
from tests.fix.git_fixture import DEFAULT_IDENTITY, GitRepoTestCase


def block(prefix, count):
    """*count* numbered lines, all different, none of them blank.

    Numbered so a diff's hunk headers are predictable and a test can name the
    line it changed; all different so no two hunks can ever be byte-identical
    by accident; none blank so a line's diff prefix is never ambiguous between
    context and an empty line.
    """
    return "".join(f"{prefix}_{index:02d}\n" for index in range(1, count + 1))


class SplitRepoTestCase(GitRepoTestCase):
    """A seeded repository with a working tree that mixes concerns."""

    prefix = "gitpr_split_"

    def setUp(self):
        super().setUp()
        # The identity is written into the repository's own config, not only
        # passed as ``-c`` flags by ``_git``. ``run_git`` is what the production
        # code commits through and it passes no identity, so without this a
        # commit made by ``apply_split_plan`` would fail on "please tell me who
        # you are" — and the test would be exercising the fixture, not the code.
        name, email = DEFAULT_IDENTITY
        self._git("config", "user.name", name)
        self._git("config", "user.email", email)
        self.seed_multi()

    # ── seeding ──────────────────────────────────────────────────────────
    def seed_multi(self):
        """Commit two files: ``src/app.py`` (40 lines) and ``src/notes.md`` (20).

        The tree is deliberately left clean, so each test makes exactly the
        changes it is about and a diff captured afterwards contains nothing
        else.
        """
        self.commit("src/app.py", block("app", 40), message="chore: seed app")
        self.commit("src/notes.md", block("notes", 20), message="chore: seed notes")

    # ── stubs ────────────────────────────────────────────────────────────
    @contextlib.contextmanager
    def stubbed(self, ai=None, cached=None, api_key="key", commit_message=None):
        """Patch the AI edges; the git work in between stays real.

        The grouping answer is ``ai``; ``commit_message`` stands in for the
        per-group message pipeline, which is a separate call through
        ``core.generate_pr_content`` and would otherwise reach a provider.

        ``provider`` is stubbed in both modules that resolve one. ``hunk_grouper``
        resolves it internally and ``generate_split_plan`` resolves it before
        calling either edge, so patching only the first would leave the second
        reading the machine's own configuration — and a test asserting which
        provider was used would be asserting what happens to be in the
        developer's ``.env``.
        """
        mocks = {}
        with contextlib.ExitStack() as stack:
            mocks["ai"] = stack.enter_context(
                patch("src.split.hunk_grouper.call_ai_model", return_value=ai)
            )
            mocks["cached"] = stack.enter_context(
                patch("src.split.hunk_grouper.get_cached_response", return_value=cached)
            )
            mocks["saved"] = stack.enter_context(
                patch("src.split.hunk_grouper.save_cached_response")
            )
            for module in (
                "src.split.hunk_grouper",
                "src.split.generate_split_plan",
            ):
                stack.enter_context(
                    patch(f"{module}.get_ai_provider", return_value="gemini")
                )
            stack.enter_context(
                patch("src.split.hunk_grouper.get_api_key", return_value=api_key)
            )
            stack.enter_context(
                patch(
                    "src.split.hunk_grouper.get_api_model",
                    return_value="gemini-pro-latest",
                )
            )
            mocks["message"] = stack.enter_context(
                patch(
                    "src.split.generate_split_plan.generate_pr_content",
                    return_value={"commit_message": commit_message},
                )
            )
            yield mocks

    # ── planning ─────────────────────────────────────────────────────────
    def plan_with(self, diff, ai, commit_message="chore: a message", **kwargs):
        """``(plan, mocks)`` for *diff*, with every AI edge stubbed.

        Here rather than in a test class because two test modules need it, and
        the stubbing contract — which edges, in which modules — is the thing
        worth not writing twice.
        """
        kwargs.setdefault("repo_path", self.dir)
        kwargs.setdefault("quiet", True)
        with self.stubbed(ai=ai, commit_message=commit_message) as mocks:
            plan = generate_split_plan(diff, **kwargs)
        return plan, mocks

    @staticmethod
    def grouped(*ids, label="fix", justification="because"):
        """One group in the shape the grouping call returns it."""
        return {
            "unit_ids": list(ids),
            "intent_label": label,
            "justification": justification,
        }

    # ── snapshots ────────────────────────────────────────────────────────
    def snapshot(self):
        """Every file's bytes, for a byte-identical before/after comparison.

        ``.git`` is skipped: a split is *supposed* to change it — that is what
        creating commits means — so including it would only measure the clock.
        """
        files = {}
        for root, dirs, names in os.walk(self.dir):
            dirs[:] = [name for name in dirs if name != ".git"]
            for name in names:
                path = os.path.join(root, name)
                with open(path, "rb") as handle:
                    relative = os.path.relpath(path, self.dir).replace("\\", "/")
                    files[relative] = handle.read()
        return files

    # ── editing ──────────────────────────────────────────────────────────
    def edit_line(self, name, number, text):
        """Replace line *number* (1-based) of *name*, preserving LF endings."""
        lines = self.read(name).split("\n")
        lines[number - 1] = text
        self.write(name, "\n".join(lines))

    def add_line(self, name, number, text):
        """Insert *text* as line *number*, pushing the rest down."""
        lines = self.read(name).split("\n")
        lines.insert(number - 1, text)
        self.write(name, "\n".join(lines))

    def delete_line(self, name, number):
        """Remove line *number*."""
        lines = self.read(name).split("\n")
        del lines[number - 1]
        self.write(name, "\n".join(lines))

    # ── diffs ────────────────────────────────────────────────────────────
    def diff_now(self, *pathspec):
        """The working tree's diff against HEAD, exactly as split captures it.

        The flags are ``core.SPLIT_DIFF_ARGS`` written out rather than imported:
        a test that reads the constant it is testing cannot notice the constant
        changing.

        ``HEAD`` goes before the caller's pathspec, never after it: a ``--``
        ends the revisions, so ``diff ... -- path HEAD`` would make ``HEAD`` a
        filename and quietly return an empty diff.
        """
        return self._git("diff", "--binary", "-M", "-U3", "HEAD", *pathspec).stdout

    def restore(self):
        """Throw the working tree's changes away, back to HEAD.

        Used by round-trip tests, which need a clean tree for a rebuilt patch to
        apply against — and by nothing else, since every other test is about the
        changes staying put.
        """
        self._git("checkout", "--", ".")
        self._git("clean", "-fdq")
