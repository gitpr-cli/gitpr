"""Tests for resolve_last_review — the entry point of the fix pipeline.

Home is redirected to a temporary directory, the way tests/test_chat_backend.py
does it for the chat-command cache, so nothing touches the real ~/.gitpr.
"""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cache import resolve_last_review

REPO = "owner/repo"
BRANCH = "develop_natan"


class ReviewCacheTestCase(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.home = tempfile.mkdtemp(prefix="gitpr_fix_review_home_")
        self.addCleanup(self._rmtree, self.home)
        # Path.home() returns a Path, so the stand-in must be one too.
        self._patch = patch("src.cache.Path.home", return_value=Path(self.home))
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def _rmtree(self, path):
        import shutil

        shutil.rmtree(path, ignore_errors=True)

    @property
    def review_dir(self):
        import os

        return os.path.join(self.home, ".gitpr", "cache", "prompts", "review")

    def write_record(
        self,
        filename,
        *,
        repo=REPO,
        branch=BRANCH,
        action_type="review",
        review="## Review\n- something to fix",
        datetime_str="2026-09-13 12:00:00",
        raw=None,
    ):
        import os

        os.makedirs(self.review_dir, exist_ok=True)
        path = os.path.join(self.review_dir, filename)
        with open(path, "w", encoding="utf-8") as handle:
            if raw is not None:
                handle.write(raw)
            else:
                json.dump(
                    {
                        "md5": filename.replace(".json", ""),
                        "repo": repo,
                        "branch": branch,
                        "datetime": datetime_str,
                        "action_type": action_type,
                        "prompt": "...",
                        "response": {"review": review},
                    },
                    handle,
                    ensure_ascii=False,
                )
        return path


class TestResolveLastReview(ReviewCacheTestCase):
    def test_a_missing_cache_gives_none(self):
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_an_empty_review_folder_gives_none(self):
        import os

        os.makedirs(self.review_dir, exist_ok=True)
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_the_only_review_is_returned(self):
        self.write_record("a.json")
        record = resolve_last_review(REPO, BRANCH)
        self.assertIsNotNone(record)
        self.assertEqual(record["response"]["review"], "## Review\n- something to fix")
        self.assertEqual(record["action_type"], "review")

    def test_the_most_recent_review_wins(self):
        self.write_record("old.json", review="old text", datetime_str="2026-09-13 09:00:00")
        self.write_record("new.json", review="new text", datetime_str="2026-09-13 18:30:00")
        self.assertEqual(resolve_last_review(REPO, BRANCH)["response"]["review"], "new text")

    def test_a_full_review_counts(self):
        self.write_record("f.json", action_type="fullreview", review="full text")
        self.assertEqual(resolve_last_review(REPO, BRANCH)["response"]["review"], "full text")

    def test_a_file_review_is_not_a_branch_review(self):
        self.write_record("f.json", action_type="filereview")
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_a_newer_file_review_does_not_shadow_a_branch_review(self):
        self.write_record("r.json", review="branch text", datetime_str="2026-09-13 09:00:00")
        self.write_record(
            "f.json", action_type="filereview", review="file text", datetime_str="2026-09-13 20:00:00"
        )
        self.assertEqual(resolve_last_review(REPO, BRANCH)["response"]["review"], "branch text")

    def test_another_branch_is_ignored(self):
        self.write_record("a.json", branch="main")
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_another_repository_is_ignored(self):
        self.write_record("a.json", repo="someone/else")
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_a_record_without_review_text_is_ignored(self):
        self.write_record("a.json", review="")
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_a_record_without_an_action_type_is_ignored(self):
        self.write_record("a.json", action_type=None)
        self.assertIsNone(resolve_last_review(REPO, BRANCH))

    def test_a_corrupt_file_does_not_hide_a_good_one(self):
        self.write_record("broken.json", raw="{not json")
        self.write_record("good.json", review="good text")
        self.assertEqual(resolve_last_review(REPO, BRANCH)["response"]["review"], "good text")

    def test_only_corrupt_files_give_none(self):
        self.write_record("broken.json", raw="[1, 2, 3]")
        self.assertIsNone(resolve_last_review(REPO, BRANCH))


if __name__ == "__main__":
    unittest.main()
