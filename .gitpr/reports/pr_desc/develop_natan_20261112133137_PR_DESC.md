# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: skip headless flow on Windows and mock internet check
```

---

## 🎯 Summary

Stabilizes the commit app test suite on Windows and isolates CLI routing tests from real network access. The headless Textual flow test relies on `pilot.pause`, which blocks indefinitely on Windows environments without a real TTY, and the CLI routing tests previously depended on the actual internet connectivity check, making results environment-dependent and flaky.

## 🛠️ Technical Changes

- Add `sys` import to `tests/test_commit_app.py` to support platform detection.
- Apply `@pytest.mark.skipif(sys.platform == "win32")` to `TestCommitAppHeadlessFlow.test_headless_full_flow`, documenting the Textual `pilot.pause` TTY limitation on Windows.
- Patch `src.main.check_internet_connection` with `return_value=True` in `TestCliCommitRouting` so routing assertions no longer depend on real network state.

## ⚠️ Impact/Warnings

- Test-only change; no production code, database, environment variable, or dependency modifications.
- The headless full-flow test is now skipped on Windows, reducing coverage of that scenario on that platform. Local contributors on Windows should validate the flow manually or via a real TTY.
- CI behavior on Linux/macOS is unchanged.

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)