"""Unit tests for src/domain/mentor/mentor_explanation_builder.py."""
import unittest

from src.domain.mentor.mentor_explanation_builder import (
    MentorExplanation,
    build_mentor_markdown,
    build_mentor_section,
    parse_mentor_payload,
)


class TestMentorExplanationBuilder(unittest.TestCase):
    def test_parse_complete_valid_payload(self):
        payload = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Using string formatting inside SQL query.",
                    "why_it_matters": "Allows SQL injection which compromises DB security.",
                    "analogy": "Leaving your front door unlocked.",
                    "learn_more_pointer": "OWASP SQL Injection Prevention",
                    "has_sufficient_evidence": True,
                }
            ]
        }
        res = parse_mentor_payload(
            payload,
            expected_ids=["FIX-001"],
            technical_messages={"FIX-001": "Direct SQL concatenation detected"},
            finding_labels={"FIX-001": "FIX-001 · security · db.py:10"},
        )
        self.assertEqual(len(res), 1)
        item = res[0]
        self.assertEqual(item.finding_id, "FIX-001")
        self.assertEqual(item.what_is_happening, "Using string formatting inside SQL query.")
        self.assertEqual(item.why_it_matters, "Allows SQL injection which compromises DB security.")
        self.assertEqual(item.analogy, "Leaving your front door unlocked.")
        self.assertEqual(item.learn_more_pointer, "OWASP SQL Injection Prevention")
        self.assertTrue(item.has_sufficient_evidence)
        self.assertIn("FIX-001 · security · db.py:10", item.markdown)
        self.assertIn("Direct SQL concatenation detected", item.markdown)
        self.assertIn("Leaving your front door unlocked.", item.markdown)

    def test_parse_null_analogy(self):
        payload = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Missing return type annotation.",
                    "why_it_matters": "Type checker cannot catch subtle bugs.",
                    "analogy": None,
                    "learn_more_pointer": "PEP 484 Type Hints",
                    "has_sufficient_evidence": True,
                }
            ]
        }
        res = parse_mentor_payload(payload, expected_ids=["FIX-001"])
        self.assertEqual(len(res), 1)
        item = res[0]
        self.assertIsNone(item.analogy)
        self.assertNotIn("Analogy:", item.markdown)
        self.assertNotIn("Analogia:", item.markdown)

    def test_include_analogy_flag_disabled(self):
        payload = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Unclosed file descriptor.",
                    "why_it_matters": "Causes resource leaks.",
                    "analogy": "Leaving the tap running.",
                    "learn_more_pointer": "Python Context Managers",
                    "has_sufficient_evidence": True,
                }
            ]
        }
        res = parse_mentor_payload(payload, expected_ids=["FIX-001"], include_analogy=False)
        self.assertEqual(len(res), 1)
        item = res[0]
        self.assertIsNone(item.analogy)
        self.assertNotIn("Leaving the tap running", item.markdown)

    def test_finding_link_strictly_enforced_and_ordered(self):
        payload = {
            "explanations": [
                {
                    "finding_id": "FIX-999",  # Hallucinated ID
                    "what_is_happening": "Ghost issue",
                    "why_it_matters": "Does not exist",
                },
                {
                    "finding_id": "FIX-002",
                    "what_is_happening": "Issue 2",
                    "why_it_matters": "Why 2",
                },
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Issue 1",
                    "why_it_matters": "Why 1",
                },
            ]
        }
        # Expected order is FIX-001, FIX-002
        res = parse_mentor_payload(payload, expected_ids=["FIX-001", "FIX-002"])
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].finding_id, "FIX-001")
        self.assertEqual(res[1].finding_id, "FIX-002")

    def test_strips_urls_from_learn_more_pointer(self):
        payload = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Issue",
                    "why_it_matters": "Why",
                    "learn_more_pointer": "Check https://example.com/docs/magic for info",
                },
                {
                    "finding_id": "FIX-002",
                    "what_is_happening": "Issue 2",
                    "why_it_matters": "Why 2",
                    "learn_more_pointer": "See www.somelink.org",
                },
            ]
        }
        res = parse_mentor_payload(payload, expected_ids=["FIX-001", "FIX-002"])
        self.assertEqual(len(res), 2)
        self.assertIsNone(res[0].learn_more_pointer)
        self.assertIsNone(res[1].learn_more_pointer)

    def test_epistemic_honesty_fallback(self):
        payload = {
            "explanations": [
                {
                    "finding_id": "FIX-001",
                    "what_is_happening": "Renamed local variable",
                    "why_it_matters": "",  # Empty why
                    "has_sufficient_evidence": False,
                },
                {
                    "finding_id": "FIX-002",
                    "what_is_happening": "Changed constant",
                    "why_it_matters": "[FILL: Why did this change?]",
                },
            ]
        }
        res = parse_mentor_payload(
            payload,
            expected_ids=["FIX-001", "FIX-002"],
            insufficient_ids=frozenset(["FIX-001"]),
        )
        self.assertEqual(len(res), 2)
        self.assertFalse(res[0].has_sufficient_evidence)
        self.assertIn("Could not safely infer", res[0].why_it_matters)
        self.assertFalse(res[1].has_sufficient_evidence)
        self.assertIn("Could not safely infer", res[1].why_it_matters)

    def test_malformed_payload_returns_empty_list(self):
        self.assertEqual(parse_mentor_payload("not json", expected_ids=["FIX-001"]), [])
        self.assertEqual(parse_mentor_payload({}, expected_ids=["FIX-001"]), [])
        self.assertEqual(parse_mentor_payload({"explanations": "not a list"}, expected_ids=["FIX-001"]), [])
        self.assertEqual(parse_mentor_payload(None, expected_ids=["FIX-001"]), [])

    def test_build_mentor_section_formatting(self):
        exp1 = MentorExplanation(
            finding_id="FIX-001",
            what_is_happening="W1",
            why_it_matters="Y1",
            analogy=None,
            learn_more_pointer="P1",
            has_sufficient_evidence=True,
            markdown="### 💡 FIX-001\n**What:** W1",
        )
        section = build_mentor_section([exp1], skipped_ids=["FIX-002", "FIX-003"])
        self.assertIn("## 🎓", section)
        self.assertIn("### 💡 FIX-001", section)
        self.assertIn("2 additional finding(s) not expanded here", section)
        self.assertIn("FIX-002, FIX-003", section)


if __name__ == "__main__":
    unittest.main()

