"""Unit tests for the skill YAML front matter splitter."""

import unittest

from src.skill_frontmatter import split_front_matter


class TestSplitFrontMatter(unittest.TestCase):
    def test_language_front_matter_is_parsed_and_stripped(self):
        metadata, body = split_front_matter(
            "---\nlanguage: en_us\n---\nBody"
        )
        self.assertEqual(metadata, {"language": "en_us"})
        self.assertEqual(body, "Body")

    def test_body_without_front_matter_is_untouched(self):
        text = "You are a Release Manager."
        self.assertEqual(split_front_matter(text), ({}, text))

    def test_leading_rule_without_a_closing_delimiter_is_not_front_matter(self):
        text = "---\nJust a Markdown rule\n"
        self.assertEqual(split_front_matter(text), ({}, text))

    def test_unbalanced_delimiters_leave_the_text_untouched(self):
        text = "---\nlanguage: en_us\n"
        self.assertEqual(split_front_matter(text), ({}, text))

    def test_blank_line_before_the_opening_delimiter_is_not_front_matter(self):
        text = "\n---\nlanguage: en_us\n---\nBody"
        self.assertEqual(split_front_matter(text), ({}, text))

    def test_non_mapping_yaml_is_ignored(self):
        text = "---\n- a\n- b\n---\nBody"
        self.assertEqual(split_front_matter(text), ({}, text))

    def test_malformed_yaml_is_ignored_and_never_raises(self):
        text = "---\nlanguage: [oops\n---\nBody"
        self.assertEqual(split_front_matter(text), ({}, text))

    def test_empty_front_matter_is_stripped(self):
        self.assertEqual(split_front_matter("---\n---\nBody"), ({}, "Body"))

    def test_bom_before_the_opening_delimiter_is_accepted(self):
        text = chr(0xFEFF) + "---\nlanguage: en_us\n---\nBody"
        self.assertEqual(
            split_front_matter(text), ({"language": "en_us"}, "Body")
        )

    def test_crlf_delimiters_are_accepted(self):
        text = "---\r\nlanguage: en_us\r\n---\r\nBody\r\n"
        metadata, body = split_front_matter(text)
        self.assertEqual(metadata, {"language": "en_us"})
        self.assertEqual(body, "Body\r\n")

    def test_non_string_input_is_safe(self):
        self.assertEqual(split_front_matter(None), ({}, None))


if __name__ == "__main__":
    unittest.main()
