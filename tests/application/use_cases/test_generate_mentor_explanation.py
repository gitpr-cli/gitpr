"""Unit tests for src/application/use_cases/generate_mentor_explanation.py."""
import unittest
from unittest.mock import MagicMock, patch

from src.application.use_cases.generate_mentor_explanation import (
    MAX_FINDINGS_PER_RUN,
    MentorError,
    MentorRun,
    explain_review,
    generate_mentor_explanation,
    generate_mentor_explanations_for_review,
)
from src.fix.patch_provenance import (
    FindingRef,
    PatchCandidate,
    PatchProvenance,
    PatchSafety,
)


def _make_candidate(finding_id: str, severity: str = "medium", file_path: str = "src/foo.py"):
    return PatchCandidate(
        finding=FindingRef(
            id=finding_id,
            file_path=file_path,
            line_start=10,
            line_end=15,
            severity=severity,
            category="style",
            message=f"Message for {finding_id}",
        ),
        diff_unified="--- a/src/foo.py\n+++ b/src/foo.py\n@@ -10,3 +10,3 @@\n-old\n+new\n",
        suggested_test="test_something",
        confidence="high",
        safety=PatchSafety.SAFE,
        safety_reason="safe",
        provenance=PatchProvenance(
            finding_id=finding_id,
            ai_provider="gemini",
            ai_model="gemini-pro-latest",
            prompt_version="1",
            generated_at="2026-10-06 12:00:00",
            gitpr_version="1.3.0",
        ),
    )


class TestGenerateMentorExplanation(unittest.TestCase):
    @patch("src.application.use_cases.generate_mentor_explanation.get_api_key", return_value="fake-key")
    @patch("src.application.use_cases.generate_mentor_explanation.get_cached_response", return_value=None)
    @patch("src.application.use_cases.generate_mentor_explanation.save_cached_response")
    @patch("src.application.use_cases.generate_mentor_explanation.call_ai_model")
    def test_generate_mentor_explanations_for_review_success(
        self, mock_ai, mock_save, mock_cache, mock_key
    ):
        mock_ai.return_value = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Mutable default argument used.",
                    "why_it_matters": "Default lists are shared across function calls.",
                    "analogy": "Sharing a shopping cart.",
                    "learn_more_pointer": "Python Default Argument Gotchas",
                    "has_sufficient_evidence": True,
                }
            ]
        }

        cand = _make_candidate("FIX-001")
        diff_text = "diff --git a/src/foo.py b/src/foo.py\n@@ -10,3 +10,3 @@\n-def bar(x=[]):\n+def bar(x=None):"

        run = generate_mentor_explanations_for_review(
            candidates=[cand],
            diff_text=diff_text,
            ai_provider="gemini",
        )

        self.assertIsInstance(run, MentorRun)
        self.assertEqual(len(run.explanations), 1)
        self.assertEqual(run.explanations[0].finding_id, "FIX-001")
        self.assertIn("FIX-001", run.markdown)
        self.assertIn("Mutable default argument used.", run.markdown)
        mock_save.assert_called_once()

    @patch("src.application.use_cases.generate_mentor_explanation.get_api_key", return_value=None)
    def test_missing_api_key_raises_mentor_error(self, mock_key):
        cand = _make_candidate("FIX-001")
        with self.assertRaises(MentorError) as ctx:
            generate_mentor_explanations_for_review(
                candidates=[cand],
                diff_text="diff",
                ai_provider="gemini",
            )
        self.assertIn("No API key configured", str(ctx.exception))

    @patch("src.application.use_cases.generate_mentor_explanation.get_api_key", return_value="fake-key")
    @patch("src.application.use_cases.generate_mentor_explanation.get_cached_response")
    @patch("src.application.use_cases.generate_mentor_explanation.call_ai_model")
    def test_caching_prevents_ai_invocation(self, mock_ai, mock_cache, mock_key):
        mock_cache.return_value = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Cached explanation.",
                    "why_it_matters": "Cached why.",
                    "analogy": None,
                    "learn_more_pointer": "Cached topic",
                    "has_sufficient_evidence": True,
                }
            ]
        }
        cand = _make_candidate("FIX-001")
        run = generate_mentor_explanations_for_review(
            candidates=[cand],
            diff_text="diff",
            ai_provider="gemini",
        )
        self.assertEqual(len(run.explanations), 1)
        mock_ai.assert_not_called()

    @patch("src.application.use_cases.generate_mentor_explanation.get_api_key", return_value="fake-key")
    @patch("src.application.use_cases.generate_mentor_explanation.get_cached_response", return_value=None)
    @patch("src.application.use_cases.generate_mentor_explanation.save_cached_response")
    @patch("src.application.use_cases.generate_mentor_explanation.call_ai_model")
    def test_severity_sorting_and_cap_limit(self, mock_ai, mock_save, mock_cache, mock_key):
        # Create 12 candidates with different severities
        candidates = [
            _make_candidate(f"FIX-{i:03d}", severity="info" if i < 11 else "blocker")
            for i in range(1, 13)
        ]
        # FIX-011 and FIX-012 have severity 'blocker', so they should be prioritized first
        mock_ai.return_value = {
            "explanations": [
                {
                    "finding_id": c.finding.id,
                    "what_is_happening": f"Explanation {c.finding.id}",
                    "why_it_matters": "Why",
                }
                for c in candidates
            ]
        }

        run = generate_mentor_explanations_for_review(
            candidates=candidates,
            diff_text="diff",
            ai_provider="gemini",
        )

        self.assertEqual(len(run.explanations), MAX_FINDINGS_PER_RUN)
        self.assertEqual(len(run.skipped_ids), 2)
        # Verify that blockers were selected
        selected_ids = [e.finding_id for e in run.explanations]
        self.assertIn("FIX-011", selected_ids)
        self.assertIn("FIX-012", selected_ids)

    @patch("src.application.use_cases.generate_mentor_explanation.get_api_key", return_value="fake-key")
    @patch("src.application.use_cases.generate_mentor_explanation.get_cached_response", return_value=None)
    @patch("src.application.use_cases.generate_mentor_explanation.call_ai_model")
    def test_single_candidate_convenience_function(self, mock_ai, mock_cache, mock_key):
        mock_ai.return_value = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Single explanation",
                    "why_it_matters": "Why",
                }
            ]
        }
        cand = _make_candidate("FIX-001")
        item = generate_mentor_explanation(finding=cand, diff_text="diff")
        self.assertIsNotNone(item)
        self.assertEqual(item.finding_id, "FIX-001")


if __name__ == "__main__":
    unittest.main()

