"""Tests for the closing-line insertion (T5, ADR-004).

The helper is pure: a body in, a body out. The decision is the real
``CloseIssueDecision`` from T4 — the forge line is data, not something this
module builds.
"""
import unittest

from src.issue_autoclose.insert_close_line import (
    has_closing_reference,
    insert_close_line,
)
from src.issue_autoclose.resolve_close_issue import CloseIssueDecision

BODY = "## What\n\nSomething changes."
EXPLAIN = (
    "---\n\n## 🧐 Reviewer Guide (Explain My PR)\n\n"
    "### 🔍 What changes\n\nThe behaviour."
)
DECISION = CloseIssueDecision(number=7, title="Fix the thing", line="close #7")


class InsertTest(unittest.TestCase):
    def test_no_decision_leaves_a_plain_body_unchanged(self):
        self.assertEqual(insert_close_line(BODY, None), BODY)

    def test_no_decision_leaves_a_body_that_already_names_the_issue(self):
        body = f"{BODY}\n\nclose #7"
        self.assertEqual(insert_close_line(body, None), body)

    def test_line_is_appended_after_a_blank_line(self):
        self.assertEqual(insert_close_line(BODY, DECISION), f"{BODY}\n\nclose #7")

    def test_line_comes_after_the_explain_section(self):
        body = f"{BODY}\n\n{EXPLAIN}"

        result = insert_close_line(body, DECISION)

        self.assertEqual(result, f"{body}\n\nclose #7")
        self.assertTrue(result.startswith(BODY))

    def test_trailing_whitespace_collapses_to_one_blank_line(self):
        for suffix in ("\n", "\n\n\n", "  \n\t\n"):
            with self.subTest(suffix=repr(suffix)):
                self.assertEqual(
                    insert_close_line(BODY + suffix, DECISION),
                    f"{BODY}\n\nclose #7",
                )

    def test_empty_body_receives_only_the_line(self):
        for body in ("", "   ", "\n\n"):
            with self.subTest(body=repr(body)):
                self.assertEqual(insert_close_line(body, DECISION), "close #7")

    def test_forge_line_is_used_verbatim(self):
        decision = CloseIssueDecision(7, "Fix", "Closes #7")

        self.assertEqual(insert_close_line(BODY, decision), f"{BODY}\n\nCloses #7")

    def test_the_same_body_is_returned_when_the_line_is_already_there(self):
        body = f"{BODY}\n\nclose #7"

        self.assertEqual(insert_close_line(body, DECISION), body)


class IdempotencyTest(unittest.TestCase):
    def test_every_closing_keyword_is_honoured(self):
        for keyword in (
            "close",
            "closes",
            "closed",
            "fix",
            "fixes",
            "fixed",
            "resolve",
            "resolves",
            "resolved",
        ):
            for casing in (keyword, keyword.upper(), keyword.capitalize()):
                with self.subTest(keyword=casing):
                    body = f"Some text {casing} #7 in a sentence."
                    self.assertEqual(insert_close_line(body, DECISION), body)

    def test_extra_spaces_between_the_keyword_and_the_number_are_honoured(self):
        body = "Some text closes   #7."

        self.assertEqual(insert_close_line(body, DECISION), body)

    def test_owner_and_repository_prefix_is_honoured(self):
        for body in ("Fixes owner/repo#7.", "FIXES OWNER/Repo#7."):
            with self.subTest(body=body):
                self.assertEqual(insert_close_line(body, DECISION), body)

    def test_a_different_issue_number_is_not_a_reference(self):
        body = "This closes #8, not the tracked one."

        self.assertEqual(insert_close_line(body, DECISION), f"{body}\n\nclose #7")

    def test_a_longer_number_does_not_match(self):
        for number in ("#70", "#123", "#7a"):
            with self.subTest(number=number):
                body = f"Closes {number}."
                self.assertEqual(
                    insert_close_line(body, DECISION), f"{body}\n\nclose #7"
                )

    def test_the_keyword_must_start_a_word(self):
        for body in ("disclosed #7.", "prefixed #7.", "reclosed #7."):
            with self.subTest(body=body):
                self.assertEqual(
                    insert_close_line(body, DECISION), f"{body}\n\nclose #7"
                )


class ClosingReferenceTest(unittest.TestCase):
    def test_reference_for_the_same_number(self):
        self.assertTrue(has_closing_reference("Closes #7", 7))

    def test_reference_for_another_number(self):
        self.assertFalse(has_closing_reference("Closes #8", 7))

    def test_a_longer_number_is_not_the_same_issue(self):
        self.assertFalse(has_closing_reference("Closes #70", 7))
        self.assertFalse(has_closing_reference("Closes #123", 12))
        self.assertFalse(has_closing_reference("Closes #7a", 7))

    def test_the_keyword_must_start_a_word(self):
        self.assertFalse(has_closing_reference("disclosed #7", 7))

    def test_an_empty_body_has_no_reference(self):
        self.assertFalse(has_closing_reference("", 7))
        self.assertFalse(has_closing_reference(None, 7))


if __name__ == "__main__":
    unittest.main()
