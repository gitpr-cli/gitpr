# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: patch get_git_diff at mentor CLI usage site
```

---

## 🎯 Summary

Fixes the mentor CLI test suite so that `get_git_diff` is patched at the location where it is actually resolved (`src.main`) instead of its definition module (`src.core`). Because `src.main` imports the symbol directly, patching `src.core.get_git_diff` had no effect on the code under test, leaving the tests dependent on the real repository state and prone to flakiness or false positives.

## 🛠️ Technical Changes

- Updated `TestMentorCli` patch targets from `src.core.get_git_diff` to `src.main.get_git_diff` in both affected test cases.
- Aligned the mock boundary with the import style used by `src.main`, ensuring the stubbed diff is actually injected into the mentor CLI flow.
- Restored proper test isolation by removing implicit reliance on the real `git diff` output.

## ⚠️ Impact/Warnings

- No production code changes; test-only adjustment.
- No database, environment variable, or dependency changes.
- Behavior verified against the mentor CLI isolation plan; tests using `@patch("src.core.get_git_diff")` elsewhere may need the same correction if the symbol is imported directly.

close #238

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)