"""Unit tests for test file matching and correlation."""

import unittest
from src.infrastructure.git.test_matcher import (
    find_related_test_files,
    requires_tests,
)


class TestTestMatcher(unittest.TestCase):

    def test_finds_related_test_files_by_convention(self):
        diff_files = [
            "src/domain/user_service.py",
            "tests/test_user_service.py",
            "docs/index.md",
        ]
        matched = find_related_test_files("src/domain/user_service.py", diff_files)
        self.assertEqual(matched, ["tests/test_user_service.py"])

    def test_finds_related_test_files_php_and_ts(self):
        diff_files = [
            "app/Services/OrderService.php",
            "tests/Unit/OrderServiceTest.php",
            "src/components/button.tsx",
            "src/components/button.test.tsx",
        ]
        matched_php = find_related_test_files("app/Services/OrderService.php", diff_files)
        self.assertEqual(matched_php, ["tests/Unit/OrderServiceTest.php"])

        matched_ts = find_related_test_files("src/components/button.tsx", diff_files)
        self.assertEqual(matched_ts, ["src/components/button.test.tsx"])

    def test_test_file_itself_does_not_require_tests(self):
        self.assertFalse(requires_tests("tests/test_user_service.py"))
        self.assertFalse(requires_tests("tests/Unit/OrderServiceTest.php"))
        self.assertFalse(requires_tests("src/components/button.test.tsx"))

    def test_docs_and_non_executable_do_not_require_tests(self):
        self.assertFalse(requires_tests("README.md"))
        self.assertFalse(requires_tests("docs/architecture.txt"))
        self.assertFalse(requires_tests("Pipfile.lock"))
        self.assertFalse(requires_tests("package-lock.json"))
        self.assertFalse(requires_tests(".gitignore"))

    def test_production_code_requires_tests(self):
        self.assertTrue(requires_tests("src/core.py"))
        self.assertTrue(requires_tests("app/Models/User.php"))
        self.assertTrue(requires_tests("src/components/Modal.tsx"))

