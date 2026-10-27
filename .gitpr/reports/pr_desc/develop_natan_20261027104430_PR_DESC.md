# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: tolerate non-UTF-8 git output and fail on git errors
```

---

## 🎯 Summary

Two unrelated-looking symptoms had the same root cause: git ran successfully but GitPR silently behaved as if the branch had no changes.

1. A repository containing a single legacy-encoded (Latin-1) file made the full-diff capture blow up. `git diff` output was decoded with `encoding="utf-8"` and no error handler, the decoding error killed the subprocess reader thread, `stdout` came back as `None`, and the run reported "No new code found" instead of the actual branch changes. The project contract is now explicit everywhere: decode as UTF-8 and replace undecodable bytes with `U+FFFD` so the rest of the diff survives.
2. `get_git_full_diff()` / `get_git_diff()` return `None` when git itself fails. That sentinel was folded into the same "no new code found" path used for a genuinely empty diff, hiding real failures (missing repo, broken remote, auth error) behind a green exit code and a misleading message.

## 🛠️ Technical Changes

- Added `encoding="utf-8"` and `errors="replace"` to every `subprocess.run` that captures git output in `src/cache.py`, `src/core.py`, `src/issue_engine.py` and `src/main.py` (`git config user.name`/`user.email`, `git remote -v`, `git diff`, `git log`, `merge-base`, `symbolic-ref`).
- Added the missing `text=True` to the `git diff` capture in `get_git_full_diff()`, which previously relied on implicit behaviour.
- Split the diff guard in `src/main.py` into two distinct paths: `diff_text is None` (git failure) now exits with code `1`, while an empty/whitespace diff keeps exiting `0` with the "No new code found" warning.
- Hook mode (`--hook`, used by `prepare-commit-msg`) fails open: on a git failure it returns instead of exiting non-zero, because a non-zero hook aborts the user's commit.
- Bumped `__version__` to `1.4.2` in `src/updater.py`.
- New `tests/test_full_diff_encoding.py`: end-to-end fixture with a real bare origin and a committed Latin-1 file, asserting the file appears in the diff and that byte `0xFA` surfaces as `U+FFFD`.
- New `tests/test_diff_failure_cli.py`: asserts exit code `1` and no "No new code found" on git failure, exit code `0` plus the warning on an empty diff, and fail-open behaviour in hook mode.

## ⚠️ Impact/Warnings

- **Behaviour change (CLI):** a git failure now exits non-zero where it previously exited `0`. Scripts and CI pipelines that treated the old exit code as success will now see a failure — this is the intended fix.
- **Behaviour change (hook mode):** deliberately fail-open. If `git diff` fails inside `prepare-commit-msg`, GitPR exits `0` silently rather than blocking the commit; the failure is not surfaced beyond that.
- **Data fidelity:** undecodable bytes are lossily replaced with `U+FFFD` in the diff sent to the model and in commit-message/PR generation. Legacy-encoded files are readable, but their original characters are not recoverable in that context.
- No database, environment variable or dependency changes.


close #221

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)