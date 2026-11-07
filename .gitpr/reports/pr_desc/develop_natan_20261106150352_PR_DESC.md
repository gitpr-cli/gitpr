# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: gate interactive commit TUI on TTY availability
```

---

## 🎯 Summary

The `-c/--commit` flow previously decided between the interactive `CommitApp` TUI and the headless console flow based only on the `hook` flag. As a result, the TUI could be launched in environments without a terminal (CI pipelines, piped input, cron jobs), causing the command to hang or fail. This change makes the routing decision depend on whether the process is actually allowed to prompt the user (`_may_ask_the_user()`), ensuring the interactive TUI only opens when a real TTY is present and that headless contexts degrade gracefully to the console flow. Test coverage was added to lock in this routing behavior.

## 🛠️ Technical Changes

- Reworked the `-c/--commit` branch in `src/main.py` to gate the interactive `CommitApp` on `_may_ask_the_user()` (`may_ask`) instead of on `hook` alone.
- Added an explicit non-interactive branch that:
  - skips the AI call when in hook mode during a merge-in-progress;
  - runs `check_unstaged_files('commit', ...)` for non-hook runs;
  - only then retrieves the diff via `get_git_diff()`.
- Removed the trailing blank line from the `print_banner()` raw string, trimming one empty line from the rendered ASCII signature.
- Applied whitespace-only normalization across `src/main.py` (banner literals, decorators, help map, command bodies) with no logic impact.
- Added `TestCliCommitRouting` in `tests/test_commit_app.py` using `CliRunner` and `src.main.cli`, covering:
  - interactive mode launches `CommitApp.run` when `_may_ask_the_user` returns `True`;
  - headless mode invokes the console flow, exits successfully, and prints the generated commit suggestion;
  - `check_unstaged_files` is called with `commit`, `skip_check=False`, `quiet=False`, `interactive=False`, and the command still exits with code 0.
- Used `unittest.mock.patch` to isolate environment setup, diff retrieval, PR generation, connectivity checks, and unstaged file checks.

## ⚠️ Impact/Warnings

- **Behavioral change:** non-interactive contexts (hook, CI, pipe, cron) no longer attempt to open the TUI; they now always use the console flow. Scripts relying on the previous behavior in a TTY-less environment will see different output.
- **No breaking changes:** the remaining ~29 flags, subcommands, policy/baseline gates, and exit-code semantics are unchanged.
- **Cosmetic:** the banner output is one line shorter.
- No new dependencies, environment variables, or database changes.

close #283

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_7_warnings-yellow)](https://gitpr.natanfiuza.dev.br/)