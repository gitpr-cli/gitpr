# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: stabilize headless commit flow waits and confirmation
```

---

## 🎯 Summary

Stabilizes the headless end-to-end test for the commit app flow. The test previously relied on a loose wait predicate that could match transient widget state and on a simulated click that occasionally failed under timing variance, causing flaky results. This change makes the wait deterministic and the confirmation step more reliable.

## 🛠️ Technical Changes

- Import `Button` from `textual.widgets` to interact with the confirm button directly.
- Increase the default `_wait_until` timeout from 5.0s to 10.0s to accommodate slower CI environments.
- Harden the wait predicate to require that `app.screen` is a mounted `CommitMessageScreen` containing `#btn_confirm`, avoiding premature matches.
- Replace `pilot.click("#btn_confirm")` with a direct `Button.press()` followed by `pilot.pause()` for a more reliable confirmation trigger.

## ⚠️ Impact/Warnings

- Test-only changes; no production behavior is modified.
- No database, environment variable, or dependency changes.

close #279

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)