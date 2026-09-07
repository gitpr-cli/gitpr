"""Unit tests for the pure reviewer suggestion scoring (no git, no network)."""
import unittest
from datetime import date

from src.reviewer_suggestion import (
    BlameHit,
    ReviewerCandidate,
    ReviewerSuggestionResult,
    aggregate_hits,
    compute_scores,
    is_bot,
    normalize_email,
    rank_reviewers,
)

# Fixed "today" so recency expectations are deterministic.
TODAY = date(2026, 9, 6)
_TODAY_ORDINAL = TODAY.toordinal()


def _hit(path, line, name, email, days_ago, commit="a" * 40):
    commit_date = date.fromordinal(_TODAY_ORDINAL - days_ago).isoformat()
    return BlameHit(
        file_path=path,
        line_number=line,
        author_name=name,
        author_email=email,
        commit_hash=commit,
        commit_date=commit_date,
    )


class TestRankingMatchesManualCalculation(unittest.TestCase):
    """Acceptance 1: ranking equals the manual calculation (default weights)."""

    def test_default_weights(self):
        hits = [
            _hit("a.py", 1, "Ana Silva", "ana@example.com", 30),
            _hit("a.py", 2, "Ana Silva", "ana@example.com", 30),
            _hit("a.py", 3, "Ana Silva", "ana@example.com", 30),
            _hit("b.py", 1, "Bob Lima", "bob@example.com", 10),
            _hit("b.py", 2, "Bob Lima", "bob@example.com", 10),
        ]
        result = rank_reviewers(
            hits, pr_author_email="carla@example.com", today=TODAY
        )
        self.assertEqual(len(result.candidates), 2)

        ana = result.candidates[0]
        bob = result.candidates[1]
        # Manual: total_lines=5, total_files=2.
        # Ana: 0.5*(3/5) + 0.3*(1/2) + 0.2*(1/(1+30/90)) = 0.3+0.15+0.15
        self.assertAlmostEqual(ana.score, 0.6, places=6)
        # Bob: 0.5*(2/5) + 0.3*(1/2) + 0.2*(1/(1+10/90)) = 0.2+0.15+0.18
        self.assertAlmostEqual(bob.score, 0.53, places=6)
        self.assertEqual(ana.author_email, "ana@example.com")
        self.assertEqual(ana.touched_lines, 3)
        self.assertEqual(ana.touched_files, 1)
        self.assertFalse(result.excluded_pr_author)

    def test_custom_weights(self):
        hits = [
            _hit("a.py", 1, "Ana Silva", "ana@example.com", 30),
            _hit("a.py", 2, "Ana Silva", "ana@example.com", 30),
            _hit("a.py", 3, "Ana Silva", "ana@example.com", 30),
            _hit("b.py", 1, "Bob Lima", "bob@example.com", 10),
            _hit("b.py", 2, "Bob Lima", "bob@example.com", 10),
        ]
        weights = {"lines": 1.0, "files": 0.0, "recency": 0.0}
        result = rank_reviewers(
            hits,
            pr_author_email="carla@example.com",
            weights=weights,
            today=TODAY,
        )
        self.assertAlmostEqual(result.candidates[0].score, 0.6, places=6)
        self.assertAlmostEqual(result.candidates[1].score, 0.4, places=6)


class TestExclusions(unittest.TestCase):
    """Acceptance 2 and 3: PR author and bots never appear."""

    def test_pr_author_excluded_even_if_top_owner(self):
        hits = [
            _hit("a.py", i, "Carla Reis", "carla@example.com", 1) for i in range(1, 11)
        ]
        hits.append(_hit("b.py", 1, "Ana Silva", "ana@example.com", 5))
        result = rank_reviewers(
            hits, pr_author_email="carla@example.com", today=TODAY
        )
        self.assertTrue(result.excluded_pr_author)
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].author_email, "ana@example.com")

    def test_pr_author_matched_by_name_when_email_unknown(self):
        hits = [
            _hit("a.py", 1, "Carla Reis", "carla@example.com", 1),
            _hit("b.py", 1, "Ana Silva", "ana@example.com", 5),
        ]
        result = rank_reviewers(
            hits, pr_author_name="Carla Reis", today=TODAY
        )
        self.assertTrue(result.excluded_pr_author)
        self.assertEqual(len(result.candidates), 1)

    def test_unknown_identity_does_not_exclude_everything(self):
        hits = [_hit("a.py", 1, "Carla Reis", "carla@example.com", 1)]
        result = rank_reviewers(
            hits, pr_author_email="unknown", pr_author_name="unknown", today=TODAY
        )
        self.assertFalse(result.excluded_pr_author)
        self.assertEqual(len(result.candidates), 1)

    def test_bots_excluded(self):
        hits = [
            _hit("a.py", 1, "dependabot[bot]", "dependabot[bot]@users.noreply.github.com", 1),
            _hit("a.py", 2, "GitHub Actions", "github-actions@github.com", 1),
            _hit("a.py", 3, "Some Bot", "bot[bot]@corp.com", 1),
            _hit("b.py", 1, "Ana Silva", "ana@users.noreply.github.com", 5),
        ]
        result = rank_reviewers(
            hits, pr_author_email="carla@example.com", today=TODAY
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].author_email, "ana@users.noreply.github.com")

    def test_excluded_authors_from_config(self):
        hits = [
            _hit("a.py", 1, "Ana Silva", "ana@example.com", 1),
            _hit("a.py", 2, "Bob Lima", "bob@example.com", 1),
            _hit("b.py", 1, "Carla Reis", "carla@example.com", 1),
        ]
        result = rank_reviewers(
            hits,
            pr_author_email="carla@example.com",
            excluded_authors=("ci-bot@empresa.com", "Bob Lima"),
            today=TODAY,
        )
        emails = [c.author_email for c in result.candidates]
        self.assertEqual(emails, ["ana@example.com"])


class TestAggregation(unittest.TestCase):
    def test_normalized_email_merges_case_and_spaces(self):
        hits = [
            _hit("a.py", 1, "Ana Silva", "Ana@Example.com", 20),
            _hit("a.py", 2, "ana silva", "ana@example.com", 2),
            _hit("b.py", 1, "Bob Lima", "bob@example.com", 5),
        ]
        result = rank_reviewers(
            hits, pr_author_email="carla@example.com", today=TODAY
        )
        self.assertEqual(len(result.candidates), 2)
        ana = result.candidates[0]
        self.assertEqual(ana.touched_lines, 2)
        self.assertEqual(ana.touched_files, 1)
        # The most recent hit's name wins.
        self.assertEqual(ana.author_name, "ana silva")

    def test_normalize_email(self):
        self.assertEqual(normalize_email("  ANA@Example.COM "), "ana@example.com")


class TestRecency(unittest.TestCase):
    def test_recency_halflife_and_invalid_dates(self):
        fresh = [_hit("a.py", 1, "Ana Silva", "ana@example.com", 0)]
        stale = [_hit("b.py", 1, "Bob Lima", "bob@example.com", 90)]
        result = rank_reviewers(
            fresh + stale, pr_author_email="carla@example.com", today=TODAY
        )
        self.assertEqual(result.candidates[0].author_email, "ana@example.com")
        self.assertEqual(result.candidates[1].author_email, "bob@example.com")
        # Half-life boundary: 90 days ago scores 1/(1+1) = 0.5 on the recency signal.
        self.assertAlmostEqual(
            result.candidates[1].score,
            0.5 * (1 / 2) + 0.3 * (1 / 2) + 0.2 * 0.5,
            places=6,
        )

    def test_invalid_date_never_crashes(self):
        bad = BlameHit(
            file_path="a.py",
            line_number=1,
            author_name="Ana Silva",
            author_email="ana@example.com",
            commit_hash="b" * 40,
            commit_date="not-a-date",
        )
        good = _hit("b.py", 1, "Bob Lima", "bob@example.com", 5)
        result = rank_reviewers([bad, good], pr_author_email="c@example.com", today=TODAY)
        self.assertEqual(len(result.candidates), 2)
        # The invalid-date candidate gets zero recency but still scores.
        ana = next(c for c in result.candidates if c.author_email == "ana@example.com")
        self.assertEqual(ana.score, 0.5 * (1 / 2) + 0.3 * (1 / 2) + 0.0)


class TestEmptyAndHelpers(unittest.TestCase):
    def test_empty_hits_returns_empty_result(self):
        result = rank_reviewers([], pr_author_email="a@example.com")
        self.assertIsInstance(result, ReviewerSuggestionResult)
        self.assertEqual(result.candidates, [])
        self.assertFalse(result.excluded_pr_author)

    def test_top_n_truncation(self):
        hits = [
            _hit(f"f{i}.py", 1, f"Dev {i}", f"dev{i}@example.com", 3) for i in range(5)
        ]
        result = rank_reviewers(
            hits, pr_author_email="a@example.com", top_n=2, today=TODAY
        )
        self.assertEqual(len(result.candidates), 2)

    def test_aggregate_hits_and_compute_scores_helpers(self):
        hits = [
            _hit("a.py", 1, "Ana Silva", "ana@example.com", 2),
            _hit("b.py", 1, "Bob Lima", "bob@example.com", 2),
        ]
        candidates = aggregate_hits(hits)
        self.assertIsInstance(candidates[0], ReviewerCandidate)
        compute_scores(candidates, 2, 2, today=TODAY)
        # 0.5*(1/2) + 0.3*(1/2) + 0.2*(1/(1+2/90)) per candidate.
        expected = 0.25 + 0.15 + 0.2 * (1 / (1 + 2 / 90))
        for candidate in candidates:
            self.assertAlmostEqual(candidate.score, expected, places=6)

    def test_is_bot_never_flags_noreply_users(self):
        self.assertTrue(is_bot("dependabot[bot]", "dependabot[bot]@x.com"))
        self.assertTrue(is_bot("", "github-actions@github.com"))
        self.assertTrue(is_bot("Renovate Bot", "bot[bot]@renovate.com"))
        self.assertFalse(is_bot("Ana Silva", "ana@users.noreply.github.com"))


if __name__ == "__main__":
    unittest.main()
