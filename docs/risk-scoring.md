# Technical Documentation: Local Risk Scoring (gitpr risk)

`gitpr risk` computes a local, deterministic, and explainable risk score for individual modified files and the pull request / diff as a whole. It uses repository and Git signals—critical paths, missing tests, database migrations, bug and revert histories, diff size, and static findings—to prioritize human reviewer attention and guide AI review focus, without requiring network access, consuming AI tokens, or blocking workflows.

---

## 1. Overview

Local Risk Scoring operates across three surfaces:

1. **Standalone CLI (`gitpr risk`)**: Evaluates the working tree or branch diff against a base reference and prints a color-coded breakdown of risk levels, scores, and contributing factors.
2. **File-Specific Inspection (`gitpr risk --file <path>`)**: Isolates the risk calculation for a single target file, detailing its specific signals and test correlations.
3. **Additive Code Review Context (`gitpr -r` / `gitpr -f` / `gitpr --review-pr`)**: When enabled (`GITPR_RISK_INCLUDE_IN_REVIEW=true`), automatically attaches a `## ⚡ Risk Assessment` section to generated code review files and injects a structured summary into the AI prompt to focus scrutiny on critical files.

### 1.1 Command Reference

```bash
gitpr risk                        # Computes risk score for the current uncommitted diff (or branch diff)
gitpr risk --file src/auth.py     # Decomposes risk factors for a specific file
gitpr risk --format json          # Outputs structured JSON for CI/CD and automation
gitpr risk --base main            # Evaluates risk against an explicit git base ref
gitpr risk --no-history           # Disables git log extraction for faster local calculation
```

| Option | Description |
|---|---|
| **`--file <path>`** | Calculates detailed risk factors for a specific file |
| **`--format {text\|json}`** | Selects human-readable terminal output (default) or structured JSON |
| **`--base <ref>`** | Computes the diff against an explicit git branch or commit reference |
| **`--no-history`** | Skips git log commit history reading to optimize execution speed |

---

## 2. Scoring Model & Aggregation Formula

All scores are strictly normalized within the range **`0.0 – 100.0`**.

### 2.1 Risk Levels & Thresholds

| Risk Level | Score Range | Badge | Meaning |
|---|---|---|---|
| **LOW** | 0.0 – 24.0 | `LOW 🟢` | Routine changes with low regression likelihood |
| **MEDIUM** | 25.0 – 49.0 | `MEDIUM 🟡` | Moderate changes requiring normal review vigilance |
| **HIGH** | 50.0 – 79.0 | `HIGH 🟠` | Significant changes touching critical areas or lacking tests |
| **CRITICAL** | 80.0 – 100.0 | `CRITICAL 🔴` | High regression exposure, blockers, or sensitive architectural impacts |

### 2.2 Signal Weights Table

| Signal | Default Points | Condition / Pattern |
|---|---:|---|
| **`CRITICAL_PATH`** | +25 | Authentication, authorization, permissions, payments, policies, billing |
| **`SECURITY_SENSITIVE`** | +25 | Security configurations, cryptographic routines, sessions, token management |
| **`DATABASE_MIGRATION`** | +20 | Schema changes, database migrations, structural SQL |
| **`INFRASTRUCTURE`** | +20 | CI/CD workflows, Dockerfiles, Terraform, Kubernetes configurations |
| **`NO_TEST_CHANGE`** | +15 | Executable production code modified without matching test updates in diff |
| **`LARGE_DIFF`** | +5 to +15 | Diff volume: >= 50 lines (+5), >= 100 lines (+10), >= 300 lines (+15) |
| **`HISTORICAL_BUGS`** | +10 to +20 | File associated with bug-fix commits in the recent window (90 days / 50 commits) |
| **`HISTORICAL_REVERTS`** | +10 | File touched by revert or rollback commits |
| **`HIGH_CHURN`** | +15 | File with elevated commit frequency (>= 20 commits in window) |
| **`FINDING_BLOCKER`** | +25 | Blocker security finding reported by local linter or secret scanner |
| **`FINDING_CRITICAL`** | +15 | Critical error finding reported by static linter |
| **`FINDING_WARNING`** | +3 | Non-blocking warning reported by static linter |
| **`TEST_PRESENT`** | -10 | Mitigating signal: matching test file modified or added alongside code |
| **`NEW_FILE`** | 0 | Informational: newly created file with no prior commit history |

### 2.3 Aggregation Formula (50 / 30 / 20)

The aggregate pull request score combines individual file scores:
- **50%**: Maximum individual file score (`max_file_score`)
- **30%**: Weighted average of file scores by lines changed (`weighted_avg_lines`)
- **20%**: Aggregated critical evidence score (`critical_evidence_score`)

### 2.4 Mandatory Elevation Rules

1. **High Floor**: If any single file scores **>= 80.0**, the aggregate PR level cannot be classified lower than `HIGH`.
2. **Critical Floor**: If any blocker finding (`FINDING_BLOCKER`) is present or any single file scores **>= 90.0**, the aggregate PR level is automatically elevated to `CRITICAL`.
3. **Saturation**: Scores are clamped between `0.0` and `100.0`. Negative points are restricted to explicit mitigating signals (`TEST_PRESENT`).

---

## 3. Configuration & Customization

### 3.1 Global Configuration (`~/.gitpr/.env` or `gitpr config`)

| Key | Type | Default | Description |
|---|---|---|---|
| `GITPR_RISK_INCLUDE_IN_REVIEW` | boolean | `true` | Automatically appends the Risk Assessment section to code reviews (`-r`, `-f`, `--review-pr`). |

### 3.2 Custom Rules via YAML (`.gitpr/skill/gitpr.risk.yml`)

You can define project-specific paths, weights, and thresholds in `.gitpr/skill/gitpr.risk.yml` or `.gitpr.risk.yml`:

```yaml
risk:
  enabled: true
  include_in_review: true
  analysis_version: "1.0"
  thresholds:
    low_max: 24
    medium_max: 49
    high_max: 79
  weights:
    critical_path: 25
    security_sensitive: 25
    database_migration: 20
    infrastructure: 20
    no_test_change: 15
    test_present: -10
  critical_paths:
    - "app/Http/Middleware/**"
    - "app/Policies/**"
    - "database/migrations/**"
    - ".github/workflows/**"
```

---

## 4. Performance & Privacy Guarantees

- **100% Offline & Deterministic**: Runs entirely on local file diffs and Git metadata. Never makes network requests or sends code to external servers.
- **Sub-Second Execution**: Evaluates diffs in milliseconds, making it suitable for pre-commit hooks and CI pipelines.
- **Epistemic Honesty**: If git history is unavailable (e.g. shallow clone in CI), it marks the signal as `SIGNAL_UNAVAILABLE` with a non-blocking warning rather than inventing synthetic risk points.

