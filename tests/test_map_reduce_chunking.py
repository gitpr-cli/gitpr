"""Tests for the Map-Reduce cascade diff chunker and per-provider threshold resolution."""

import os
from unittest import mock
import pytest

from src.config import (
    DEFAULT_MAP_REDUCE_MAX_PART_TOKENS,
    DEFAULT_MAP_REDUCE_MAX_TOKENS,
    get_map_reduce_thresholds,
)
from src.core import (
    estimate_token_count,
    split_diff_into_chunks,
)


class TestMapReduceThresholds:
    """Verifies the hierarchical resolution of trigger and part size thresholds."""

    def test_default_thresholds_when_env_is_empty(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            max_tokens, max_part_tokens = get_map_reduce_thresholds("gemini")
            assert max_tokens == DEFAULT_MAP_REDUCE_MAX_TOKENS
            assert max_part_tokens == DEFAULT_MAP_REDUCE_MAX_PART_TOKENS

    def test_global_env_overrides_defaults(self):
        env = {
            "GITPR_MAP_REDUCE_MAX_TOKENS": "80000",
            "GITPR_MAP_REDUCE_MAX_PART_TOKENS": "40000",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            max_tokens, max_part_tokens = get_map_reduce_thresholds("gemini")
            assert max_tokens == 80000
            assert max_part_tokens == 40000

    def test_provider_specific_env_wins_over_global(self):
        env = {
            "GITPR_MAP_REDUCE_MAX_TOKENS": "80000",
            "GITPR_MAP_REDUCE_MAX_PART_TOKENS": "40000",
            "GITPR_MAP_REDUCE_MAX_TOKENS_DEEPSEEK": "60000",
            "GITPR_MAP_REDUCE_MAX_PART_TOKENS_DEEPSEEK": "25000",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            # DeepSeek gets provider-specific thresholds
            ds_max, ds_part = get_map_reduce_thresholds("deepseek")
            assert ds_max == 60000
            assert ds_part == 25000

            # Gemini falls back to global env
            gem_max, gem_part = get_map_reduce_thresholds("gemini")
            assert gem_max == 80000
            assert gem_part == 40000

    def test_part_tokens_capped_at_max_tokens(self):
        env = {
            "GITPR_MAP_REDUCE_MAX_TOKENS": "40000",
            "GITPR_MAP_REDUCE_MAX_PART_TOKENS": "70000",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            max_tokens, max_part_tokens = get_map_reduce_thresholds()
            assert max_tokens == 40000
            assert max_part_tokens == 40000

    def test_invalid_or_negative_values_fall_back_safely(self):
        env = {
            "GITPR_MAP_REDUCE_MAX_TOKENS": "-500",
            "GITPR_MAP_REDUCE_MAX_PART_TOKENS": "not-a-number",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            max_tokens, max_part_tokens = get_map_reduce_thresholds()
            assert max_tokens == DEFAULT_MAP_REDUCE_MAX_TOKENS
            assert max_part_tokens == DEFAULT_MAP_REDUCE_MAX_PART_TOKENS


class TestSplitDiffIntoChunks:
    """Verifies cascade chunking across files, hunks, and lines."""

    def test_small_diff_returns_single_chunk(self):
        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1,2 +1,2 @@\n"
            "-hello\n"
            "+world\n"
        )
        chunks = split_diff_into_chunks(diff, max_tokens=1000, max_part_tokens=500)
        assert len(chunks) == 1
        assert chunks[0] == diff

    def test_multi_file_diff_split_at_file_boundaries(self):
        file1 = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n"
            "+++ b/a.py\n"
            "@@ -1 +1 @@\n"
            + ("+line a\n" * 200)
        )
        file2 = (
            "diff --git a/b.py b/b.py\n"
            "--- a/b.py\n"
            "+++ b/b.py\n"
            "@@ -1 +1 @@\n"
            + ("+line b\n" * 200)
        )
        diff = file1 + file2
        # Set max_tokens low enough to trigger chunking, part tokens to fit exactly one file
        tok1 = estimate_token_count(file1)
        chunks = split_diff_into_chunks(diff, max_tokens=tok1, max_part_tokens=tok1)
        assert len(chunks) == 2
        assert "diff --git a/a.py" in chunks[0]
        assert "diff --git a/b.py" in chunks[1]

    def test_single_giant_file_split_at_hunk_boundaries(self):
        header = (
            "diff --git a/giant.py b/giant.py\n"
            "--- a/giant.py\n"
            "+++ b/giant.py\n"
        )
        hunk1 = "@@ -1,5 +1,50 @@\n" + ("+change 1\n" * 100)
        hunk2 = "@@ -60,5 +60,50 @@\n" + ("+change 2\n" * 100)
        giant_file = header + hunk1 + hunk2

        # Part tokens smaller than the whole file, but larger than individual hunks
        hunk1_tok = estimate_token_count(hunk1)
        chunks = split_diff_into_chunks(
            giant_file, max_tokens=hunk1_tok, max_part_tokens=hunk1_tok + 50
        )
        assert len(chunks) >= 2
        # Verify that all chunks have the file header and part indicator
        for idx, chunk in enumerate(chunks, 1):
            assert "diff --git a/giant.py" in chunk
            assert f"[giant.py - part {idx}]" in chunk
            assert estimate_token_count(chunk) <= (hunk1_tok + 100)

    def test_single_giant_hunk_split_at_line_boundaries(self):
        header = (
            "diff --git a/huge_hunk.py b/huge_hunk.py\n"
            "--- a/huge_hunk.py\n"
            "+++ b/huge_hunk.py\n"
        )
        # Single monolithic hunk with 1000 lines
        single_hunk = "@@ -1,1 +1,1000 @@\n" + ("+very long repetitive diff line here\n" * 1000)
        giant_file = header + single_hunk

        max_part = 200  # Small part size (200 tokens = ~800 chars)
        chunks = split_diff_into_chunks(
            giant_file, max_tokens=100, max_part_tokens=max_part
        )
        assert len(chunks) > 5
        for chunk in chunks:
            assert "diff --git a/huge_hunk.py" in chunk
            assert "huge_hunk.py - part" in chunk

    def test_fallback_line_chunking_when_no_headers_present(self):
        raw_text = "This is a raw text diff without standard headers.\n" * 500
        max_part = 100
        chunks = split_diff_into_chunks(raw_text, max_tokens=50, max_part_tokens=max_part)
        assert len(chunks) > 1
        for chunk in chunks:
            assert estimate_token_count(chunk) <= max_part * 2  # within bounds
