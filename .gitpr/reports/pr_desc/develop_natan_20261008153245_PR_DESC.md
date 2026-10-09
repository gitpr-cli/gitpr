# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add deterministic local risk scoring for diffs
```

---

## 🎯 Summary

Adds a new **deterministic, explainable risk scoring engine** that evaluates the local diff and produces a 0–100 risk score with a `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` level. The goal is to surface review hotspots (critical paths, security-sensitive files, missing tests, migrations, and historical bug/revert/churn patterns) **without relying on AI**, so reviewers can prioritize attention where it matters most. The score is also injected into the AI review prompt as read-only context and embedded in the review report.

## 🛠️ Technical Changes

- Add new `src/domain/risk/` package with pure, side-effect-free modules:
  - `risk_types.py`: enums and dataclasses (`RiskLevel`, `RiskSignal`, `RiskEvidence`, `FileRisk`, `PullRequestRisk`).
  - `risk_rules.py`: default weights, thresholds, critical path patterns, glob matching, test/non-executable detection, and YAML config loading.
  - `risk_calculator.py`: file score calculation (with 0–100 clamping) and PR aggregation using a **50/30/20** formula (max file / line-weighted average / critical evidence), plus mandatory elevation rules (score ≥ 80 → at least HIGH; blocker or score ≥ 90 → CRITICAL).
  - `risk_explanation.py`: badge, markdown review section, and compact AI prompt context formatting.
- Add `src/application/use_cases/calculate_risk.py` orchestrator that correlates parsed diff sections, findings, test matches, and git history into `FileRisk`/`PullRequestRisk`, degrading gracefully when signals are unavailable.
- Add infrastructure adapters:
  - `src/infrastructure/git/risk_history_reader.py`: safe `git log` reader extracting commits, bug fixes, and reverts over a 90-day window.
  - `src/infrastructure/git/test_matcher.py`: convention-based test-to-production file matching across multiple language layouts.
- Add new `gitpr risk` CLI command with `--file`, `--format text|json`, `--base`, and `--no-history` flags, plus help/priority registration.
- Integrate risk section into `review`/`fullreview` flows and PR reviews, gated by the new `GITPR_RISK_INCLUDE_IN_REVIEW` config flag (`src/config.py`, `src/core.py`, `src/main.py`).
- Extend `compose_review_content` / `render_review_result` in `src/review/render.py` to optionally prepend the risk assessment section above linter alerts.
- Add `templates/gitpr.risk.yml` configuration template for customizing weights, thresholds, and critical paths.
- Add unit and CLI test coverage across the new domain, application, infrastructure, and CLI layers.

## ⚠️ Impact/Warnings

- **Environment variable:** introduces `GITPR_RISK_INCLUDE_IN_REVIEW` (defaults to `true`), which injects a new "⚡ Risk Assessment" section into review reports by default. Set to `false` to disable in reviews.
- **Dependencies:** relies on `PyYAML` (already used elsewhere for config loading); no new runtime dependency is introduced.
- **Database:** no schema or migration changes.
- **Behavioral:** risk computation may invoke `git log` on the local repository during reviews (skipped for remote PRs and when `--no-history` is used); all history failures degrade to warnings rather than errors.
- **Configuration:** a new optional `.gitpr/skill/gitpr.risk.yml` (or `.gitpr.risk.yml`) can override default weights/thresholds; negative weights are only accepted for mitigating signals such as `test_present`. Default behavior is unchanged if no config file is present.


close #199

---

[![GitPR](https://img.shields.io/badge/GitPR-0_errors_%C2%B7_5_warnings-yellow)](https://gitpr.natanfiuza.dev.br/)