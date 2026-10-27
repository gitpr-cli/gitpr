## Completion Report — Fix silent branch diff failure on non-UTF-8 content

### What was done
- Fixed the root cause: `get_git_full_diff()` decoded `git diff` output as strict
  UTF-8, so a single Latin-1 byte (`0xFA`) killed the subprocess reader thread.
  On Python 3.13/Windows the failure surfaced as `stdout=None` with no exception,
  and the CLI reported it as "no new code found".
- Swept every text-mode `subprocess.run()` in `src/` that decoded git output
  without `errors=`: 10 call sites across `core.py`, `cache.py`,
  `issue_engine.py` and `main.py`. All now use
  `encoding="utf-8", errors="replace"`.
- Converted the `git fetch origin` call from bytes mode to text mode, so its
  error message no longer renders as `b'...'`.
- Added a failure guard in the shared PR/review/fullreview/commit block:
  `get_git_full_diff()`/`get_git_diff()` returning `None` now exits 1 instead of
  printing the empty-diff message. An empty diff still exits 0. `--hook` fails
  open (`return`) so a non-zero `prepare-commit-msg` hook never aborts the
  user's commit.
- Added regression coverage: a real temporary git repository with a committed
  Latin-1 file, plus three CLI tests for the exit-code contract.
- Bumped `__version__` to 1.4.2 and added the 1.4.2 changelog section
  (placeholder, to be regenerated with links by `gitpr release --force`).

### Changed files
| File | Change type | Description |
| --- | --- | --- |
| src/core.py | fix | encoding/errors on 5 git calls; `git fetch` moved to text mode |
| src/cache.py | fix | encoding/errors on `git config user.name/email` |
| src/issue_engine.py | fix | encoding/errors on `git remote -v` |
| src/main.py | fix | encoding/errors on `git config`; `None` diff guard with exit 1 and hook fail-open |
| src/updater.py | chore | `__version__` = 1.4.2 |
| CHANGELOG.md | docs | 1.4.2 section (placeholder, no hash links yet) |
| tests/test_full_diff_encoding.py | test | real repo + Latin-1 file reproduces the bug and asserts U+FFFD replacement |
| tests/test_diff_failure_cli.py | test | None → exit 1, empty → exit 0, `--hook` → exit 0 |

### Impact
- **Functionality:** Repositories with legacy non-UTF-8 content now produce a
  diff instead of a bogus "no new code" message. Invalid bytes are replaced with
  `U+FFFD` in the text sent to the AI. A genuine git failure now exits non-zero
  in the PR, review, fullreview and commit flows — except in hook mode, which
  stays fail-open by design. `gitpr risk`, the MCP tools and `gitpr fix` are
  unchanged.
- **Performance:** None measurable; one extra decode parameter per call.
- **Compatibility:** No public API change. Two behavioral notes: an invalid byte
  now yields `U+FFFD` (this changes the AI cache key for such diffs, so affected
  branches regenerate their cached response once), and scripts that relied on
  exit 0 when git failed will now see exit 1. `get_git_full_diff` still does not
  catch `FileNotFoundError` (git missing), unlike `get_git_diff` — unchanged,
  out of scope.

### Verification
- `python -m pytest tests/test_full_diff_encoding.py tests/test_diff_failure_cli.py -v`
  → 4 passed. The encoding test failed before the fix (`assertIsNotNone`) with
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe7`, red-first confirmed.
- `python -m pytest tests/fix -q` → 204 passed, 39 subtests.
- `python -m pytest tests/test_updater.py tests/test_release_engine.py tests/test_changelog_builder.py -q`
  → 98 passed; the 1.4.2 changelog anchor resolves to `1.4.1`, as intended.
- Full suite (`python -m pytest -q`) → 2951 passed, 2 skipped, 10 failed
  (447.94s). All 10 are pre-existing and unrelated: 3 in `tests/test_i18n.py`
  (missing/orphan keys that already failed before this task) and 7 in
  `tests/badge/test_badge_paths.py` (environment token).
- AST scan of `src/`: no text-mode `subprocess.run()` left without `errors=`.
- Smoke test on the failing repository (`SIG-Novo`, read-only + `git fetch`):
  `get_git_full_diff()` returned `str` with 339,292 characters, `U+FFFD` present,
  no traceback.
- `git status` — nothing staged or committed; changes left in the working tree.

### Next steps (if applicable)
- Commit the working tree, then run `gitpr release --force` to regenerate the
  1.4.2 section with commit hashes and links (the manual section deliberately
  carries no hash, so it must not serve as the next release anchor).
- Pre-existing test debt, not touched here: the 3 i18n key mismatches and the 7
  badge tests that depend on a valid GitHub token.
