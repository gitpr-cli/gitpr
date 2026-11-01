# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: resolve file risk path from file_path or path fallback
```

---

## 🎯 Summary

Risk aggregation in `run_check` assumed every file risk entry exposed a `path` attribute, so any producer emitting `file_path` instead silently contributed empty keys to `high_risk_files` and `file_risk_map`. That degraded the risk report without raising an error — the worst kind of failure. The lookup is now tolerant of both attribute names, keeping aggregation correct regardless of which risk model feeds it.

On top of that fix, this PR locks in the baseline exit-code contract that `docs/baseline-suppressions.md` publishes: an unusable baseline must be distinguishable from a failing run, otherwise CI pipelines cannot react to it.

## 🛠️ Technical Changes

- `run_check.py`: resolve the file path with `getattr(f, "file_path", getattr(f, "path", ""))` in both the high-risk filter and the per-file risk map, preserving the existing `\\` → `/` normalization and lowercasing.
- Added `tests/integration/test_baseline_exit_code_contract.py`, a suite built on the existing `BaselineIntegrationTestCase` fixtures with a fingerprint version (`99`) the build cannot read:
  - Asserts exit `1` plus a "cannot be applied" refusal for `lint`, `-r` (review), `-f` (full review), `-i` (file audit), `risk`, and `review-pr` — the latter verified both through the use case (`BaselineError`) and through the CLI with a patched SCM context, proving the refusal happens before the forge is contacted.
  - Asserts exit `2` for `check`, so pipelines can tell "failed" (1) from "could not evaluate" (2).
  - Asserts the commit flow (`-c --hook`) stays at exit `0` and never emits the refusal, since it never enforced the baseline.
- Added a `add_origin` helper that creates a bare repo in a temp dir and wires it as `origin` with a fetched `main` head, so `-f` runs fully offline.

## ⚠️ Impact/Warnings

- No database, environment variable, or dependency changes.
- Behavioral fix only: risk aggregation no longer drops entries whose risk model names the path `file_path`; consumers of the risk map may see additional populated files where keys were previously empty strings.
- The new test suite is a contract guard — any future change to baseline refusal exit codes will now fail CI by design.

close #248

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)