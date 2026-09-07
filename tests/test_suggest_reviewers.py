"""Tests for the reviewer suggestion use case (diff text -> ranked list).

Unit tests mock git blame (acceptance 4/5: files without history degrade
into warnings instead of raising); the integration test builds a real git
repository in a temp dir with multiple authors (acceptance 6) and validates
the whole pipeline without mocks and without any network access.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

from src.i18n import __
from src.reviewer_suggestion import (
    BlameHit,
    ReviewerCandidate,
    ReviewerSuggestionResult,
)
from src.suggest_reviewers import (
    MAX_RANGES_PER_FILE,
    _group_line_ranges,
    compute_reviewer_suggestions,
    format_candidate_line,
    format_suggestion_lines,
)

TODAY = date(2026, 9, 6)
_TODAY_ORDINAL = TODAY.toordinal()

_GIT_AVAILABLE = shutil.which("git") is not None


def _hit(file_path, line, name, email, days_ago, commit="a" * 40):
    commit_date = date.fromordinal(_TODAY_ORDINAL - days_ago).isoformat()
    return BlameHit(
        file_path=file_path,
        line_number=line,
        author_name=name,
        author_email=email,
        commit_hash=commit,
        commit_date=commit_date,
    )


def _diff_for(file_path, segments):
    """Build a minimal unified diff for one file.

    segments: list of (new_start, count) additions. The parser only counts
    '+' lines, so no context/deletion lines are needed.
    """
    head = (
        f"diff --git a/{file_path} b/{file_path}\n"
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
    )
    hunks = []
    for new_start, count in segments:
        hunks.append(f"@@ -0,0 +{new_start},{count} @@\n")
        hunks.extend(f"+line {i}\n" for i in range(count))
    return head + "".join(hunks)


def _candidate(name, email, lines=1, files=1, days_ago=5):
    return ReviewerCandidate(
        author_name=name,
        author_email=email,
        touched_lines=lines,
        touched_files=files,
        last_touch_date=date.fromordinal(_TODAY_ORDINAL - days_ago).isoformat(),
    )


class TestGroupLineRanges(unittest.TestCase):
    def test_contiguous_and_gapped_lines(self):
        self.assertEqual(_group_line_ranges([1, 2, 3, 5, 9, 10]), [(1, 3), (5, 5), (9, 10)])

    def test_single_and_empty(self):
        self.assertEqual(_group_line_ranges([7]), [(7, 7)])
        self.assertEqual(_group_line_ranges([]), [])


class TestComputeReviewerSuggestions(unittest.TestCase):
    """Acceptance 4 and 5: incomplete blame degrades to warnings, never raises."""

    def test_empty_diff_yields_warning_and_no_candidates(self):
        result = compute_reviewer_suggestions(
            "", pr_author_email="ana@example.com"
        )
        self.assertEqual(result.candidates, [])
        self.assertEqual(len(result.warnings), 1)

    def test_ranks_from_blamed_hits(self):
        diff_text = (
            _diff_for("a.py", [(1, 2)]) + _diff_for("b.py", [(1, 3)])
        )
        ana = [_hit("a.py", 1, "Ana", "ana@example.com", 5), _hit("a.py", 2, "Ana", "ana@example.com", 5)]
        bob = [_hit("b.py", i, "Bob", "bob@example.com", 40) for i in (1, 2, 3)]
        with patch(
            "src.suggest_reviewers.get_blame_for_range",
            side_effect=lambda path, start, end, repo_path=None: {"a.py": ana, "b.py": bob}.get(path, []),
        ) as mock_blame:
            result = compute_reviewer_suggestions(
                diff_text, pr_author_email="carla@example.com"
            )
        # Two contiguous segments: a.py [1,2] and b.py [1,3].
        self.assertEqual(
            [c.args[:3] for c in mock_blame.call_args_list],
            [("a.py", 1, 2), ("b.py", 1, 3)],
        )
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.excluded_pr_author, False)
        # Bob: 0.5*(3/5)+0.3*(1/2)+0.2*(1/(1+40/90)) = 0.588.
        # Ana: 0.5*(2/5)+0.3*(1/2)+0.2*(1/(1+5/90)) = 0.539.
        self.assertEqual([c.author_email for c in result.candidates], ["bob@example.com", "ana@example.com"])
        self.assertEqual(result.candidates[1].touched_lines, 2)

    def test_pr_author_excluded_while_remaining_files_rank(self):
        diff_text = _diff_for("a.py", [(1, 4)]) + _diff_for("b.py", [(1, 3)])
        ana = [_hit("a.py", i, "Ana", "ana@example.com", 1) for i in (1, 2, 3, 4)]
        bob = [_hit("b.py", i, "Bob", "bob@example.com", 1) for i in (1, 2, 3)]
        with patch(
            "src.suggest_reviewers.get_blame_for_range",
            side_effect=lambda path, start, end, repo_path=None: {"a.py": ana, "b.py": bob}.get(path, []),
        ):
            result = compute_reviewer_suggestions(
                diff_text, pr_author_email="ana@example.com"
            )
        self.assertTrue(result.excluded_pr_author)
        self.assertEqual([c.author_email for c in result.candidates], ["bob@example.com"])

    def test_file_without_history_warns_and_others_continue(self):
        diff_text = (
            _diff_for("new_file.py", [(1, 2)]) + _diff_for("known.py", [(1, 1)])
        )
        hits = [_hit("known.py", 1, "Bob", "bob@example.com", 3)]
        with patch(
            "src.suggest_reviewers.get_blame_for_range",
            side_effect=lambda path, start, end, repo_path=None: {"known.py": hits}.get(path, []),
        ):
            result = compute_reviewer_suggestions(
                diff_text, pr_author_email="ana@example.com"
            )
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("new_file.py", result.warnings[0])
        self.assertEqual([c.author_email for c in result.candidates], ["bob@example.com"])

    def test_all_files_without_history_yields_warnings_only(self):
        diff_text = _diff_for("a.py", [(1, 2)]) + _diff_for("b.py", [(1, 1)])
        with patch(
            "src.suggest_reviewers.get_blame_for_range", return_value=[]
        ):
            result = compute_reviewer_suggestions(
                diff_text, pr_author_email="ana@example.com"
            )
        self.assertEqual(result.candidates, [])
        self.assertEqual(len(result.warnings), 2)

    def test_segment_cap_truncates_and_warns(self):
        segments = [(i * 3 + 1, 1) for i in range(MAX_RANGES_PER_FILE + 5)]
        diff_text = _diff_for("big.py", segments)
        with patch(
            "src.suggest_reviewers.get_blame_for_range",
            side_effect=lambda path, start, end, repo_path=None: [_hit(path, start, "Ana", "ana@example.com", 1)],
        ) as mock_blame:
            result = compute_reviewer_suggestions(
                diff_text, pr_author_email="zoe@example.com"
            )
        self.assertEqual(len(mock_blame.call_args_list), MAX_RANGES_PER_FILE)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("big.py", result.warnings[0])
        self.assertEqual(len(result.candidates), 1)

    def test_top_n_and_excluded_authors_respected(self):
        diff_text = _diff_for("a.py", [(1, 1)]) + _diff_for("b.py", [(1, 1)]) + _diff_for("c.py", [(1, 1)])
        devs = {
            "a.py": [_hit("a.py", 1, "Dev A", "a@example.com", 1)],
            "b.py": [_hit("b.py", 1, "Dev B", "b@example.com", 1)],
            "c.py": [_hit("c.py", 1, "Carla", "carla@example.com", 1)],
        }
        with patch(
            "src.suggest_reviewers.get_blame_for_range",
            side_effect=lambda path, start, end, repo_path=None: devs.get(path, []),
        ):
            result = compute_reviewer_suggestions(
                diff_text,
                pr_author_email="zoe@example.com",
                excluded_authors=("a@example.com",),
                top_n=1,
            )
        self.assertEqual([c.author_email for c in result.candidates], ["b@example.com"])


class TestFormatHelpers(unittest.TestCase):
    def test_candidate_line_with_and_without_handle(self):
        candidate = _candidate("Ana Silva", "ana@example.com", lines=12, files=3, days_ago=5)
        line = format_candidate_line(candidate, who="@ana")
        self.assertTrue(line.startswith("Suggested @ana:"))
        self.assertIn("12", line)
        self.assertIn("3", line)
        default = format_candidate_line(candidate)
        self.assertTrue(default.startswith("Suggested Ana Silva:"))

    def test_unknown_date_falls_back(self):
        candidate = _candidate("Bob Lima", "bob@example.com")
        candidate.last_touch_date = ""
        line = format_candidate_line(candidate, who="@bob")
        self.assertIn(__("Unknown"), line)
        self.assertTrue(line.endswith("."))

    def test_suggestion_lines_use_who_map_by_normalized_email(self):
        result = ReviewerSuggestionResult(
            candidates=[
                _candidate("Ana Silva", "Ana@Example.com", lines=4, files=2),
                _candidate("Bob Lima", "bob@example.com", lines=1, files=1),
            ]
        )
        lines = format_suggestion_lines(
            result, who_map={"ana@example.com": "@ana"}
        )
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("Suggested @ana:"))
        # Missing map entry falls back to the author name.
        self.assertTrue(lines[1].startswith("Suggested Bob Lima:"))


@unittest.skipUnless(_GIT_AVAILABLE, "git binary not available")
class TestRealGitIntegration(unittest.TestCase):
    """Acceptance 6: end-to-end ranking on a real fixture repository.

    Three authors commit on separate files above a shared seed commit; the
    working tree then gains an uncommitted line (never a candidate). The diff
    text is produced the same way the PR flow produces it (git diff against
    the base, -U1 -w), no remote is configured and no mock is used.
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="gitpr_suggest_")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._git("init", "-b", "main")
        # Seed commit touching every file (its lines become diff context).
        for name in ("f1.py", "f2.py", "f3.py"):
            self._write(name, "seed line\n")
        self._git("add", "--", "f1.py", "f2.py", "f3.py")
        self._git(
            "commit", "-m", "chore: seed base",
            identity=("Seed Dev", "seed@example.com"),
        )
        self.seed = self._git("rev-parse", "HEAD").stdout.strip()

    def _git(self, *args, identity=None, env_extra=None, check=True):
        cmd = ["git"]
        if identity is not None:
            name, email = identity
            cmd += ["-c", f"user.name={name}", "-c", f"user.email={email}"]
        cmd += [
            "-c", "core.autocrlf=false",
            "-c", "commit.gpgsign=false",
        ]
        cmd += list(args)
        env = None
        if env_extra:
            env = dict(os.environ, **env_extra)
        return subprocess.run(
            cmd,
            cwd=self._tmp,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            check=check,
            env=env,
        )

    def _write(self, name, content):
        with open(
            os.path.join(self._tmp, name), "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(content)

    def _commit(self, name, content, identity, message, env_extra=None):
        self._write(name, content)
        self._git("add", "--", name)
        self._git(
            "commit", "-m", message, identity=identity, env_extra=env_extra
        )

    def _diff_against_seed(self, *files):
        result = self._git("diff", "-U1", "-w", self.seed, "--", *files)
        return result.stdout

    def test_ranking_excludes_author_and_uncommitted_lines(self):
        # Ana dominates the added lines (4) yet must not appear: she is the
        # PR author. Bob and Carla each add 3 lines; Carla's commit is dated
        # months ago, so recency ranks Bob above her.
        self._commit(
            "f1.py",
            "seed line\nana line 1\nana line 2\nana line 3\nana line 4\n",
            ("Ana Silva", "ana@example.com"),
            "feat: add ana logic",
        )
        self._commit(
            "f2.py",
            "seed line\nbob line 1\nbob line 2\nbob line 3\n",
            ("Bob Lima", "bob@example.com"),
            "feat: add bob logic",
        )
        self._commit(
            "f3.py",
            "seed line\ncarla line 1\ncarla line 2\ncarla line 3\n",
            ("Carla Reis", "carla@example.com"),
            "feat: add carla logic",
            env_extra={
                "GIT_AUTHOR_DATE": "2026-01-01T10:00:00",
                "GIT_COMMITTER_DATE": "2026-01-01T10:00:00",
            },
        )
        # Uncommitted working-tree line: git blame reports it as "Not
        # Committed Yet" and the pipeline must skip it.
        with open(
            os.path.join(self._tmp, "f2.py"), "a", encoding="utf-8", newline="\n"
        ) as f:
            f.write("uncommitted tail\n")

        diff_text = self._diff_against_seed("f1.py", "f2.py", "f3.py")
        result = compute_reviewer_suggestions(
            diff_text,
            pr_author_email="ana@example.com",
            repo_path=self._tmp,
        )

        self.assertEqual(result.warnings, [])
        self.assertTrue(result.excluded_pr_author)
        emails = [c.author_email for c in result.candidates]
        self.assertEqual(emails, ["bob@example.com", "carla@example.com"])
        # The NCY tail is not counted: Bob owns exactly his 3 committed lines.
        bob = result.candidates[0]
        self.assertEqual(bob.touched_lines, 3)
        self.assertEqual(bob.touched_files, 1)
        self.assertEqual(bob.author_name, "Bob Lima")
        # Carla's blame date comes from her authored commit.
        carla = result.candidates[1]
        self.assertEqual(carla.last_touch_date, "2026-01-01")

    def test_empty_working_tree_diff_degrades(self):
        diff_text = self._diff_against_seed("f1.py", "f2.py", "f3.py")
        result = compute_reviewer_suggestions(
            diff_text, pr_author_email="ana@example.com", repo_path=self._tmp
        )
        self.assertEqual(result.candidates, [])
        self.assertEqual(len(result.warnings), 1)


if __name__ == "__main__":
    unittest.main()
