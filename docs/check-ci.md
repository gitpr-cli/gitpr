# Technical Documentation: Unified CI Check (`gitpr check`)

The `gitpr check` command provides a unified entry point designed for Continuous Integration (CI) pipelines (such as GitHub Actions, GitLab CI, and Jenkins). It orchestrates static analysis, external SAST bridges, secret scanning, optional AI code review, risk scoring, and baseline classification into a single command that outputs standard, machine-readable artifacts (**SARIF 2.1.0**, **JSON**, or **JUnit XML**) and deterministic exit codes.

---

## 1. Overview

```bash
# Run unified check and output SARIF directly to stdout
gitpr check

# Output structured SARIF file for GitHub Code Scanning
gitpr check --format sarif --output gitpr-results.sarif

# Fast zero-cost CI check without AI calls
gitpr check --no-ia

# Enforce stricter threshold (fail on warnings or errors)
gitpr check --fail-on warning

# Restrict AI review strictly to files evaluated as high risk
gitpr check --ia-only-high-risk

# Evaluate against a specific baseline manifest
gitpr check --baseline .gitpr/baseline.json

# Enforce a specific Policy Pack
gitpr check --policy security-strict@1.0.0
```

---

## 2. CLI Options and Environment Variables

Configuration follows the standard precedence: **CLI flags > Environment Variables > Defaults**.

| Flag | Env Variable | Default | Description |
|---|---|---|---|
| `--base <ref>` | `GITPR_CHECK_BASE` | Auto-detected | Base git reference for diff comparison (auto-detects `GITHUB_BASE_REF`, `origin/main`, or falls back to `HEAD`). |
| `--format {sarif\|json\|junit}` | `GITPR_CHECK_FORMAT` | `sarif` | Format of the output artifact. |
| `-o`, `--output <path>` | `GITPR_CHECK_OUTPUT` | `None` (stdout) | Path to write the output artifact. When omitted, the artifact is written to `stdout`. |
| `--fail-on <severity>` | `GITPR_CHECK_FAIL_ON` | `error` | Minimum severity that triggers exit code 1 (`info`, `warning`, `error`, `minor`, `major`, `critical`, `blocker`). |
| `--no-ia` | `GITPR_CHECK_NO_IA` | `false` | Disables AI code review (runs local linters, secrets, risk, and baseline only). |
| `--ia-only-high-risk` | `GITPR_CHECK_IA_ONLY_HIGH_RISK` | `false` | Only calls AI review for files whose risk level is high or critical. |
| `--baseline <path>` | `GITPR_CHECK_BASELINE_PATH` | `.gitpr/baseline.json` | Path to baseline JSON manifest. |
| `--policy <name>@<ver>` | `GITPR_CHECK_POLICY` | Active lockfile | Enforces a specific Policy Pack for the check run. |
| — | `GITPR_CHECK_TIMEOUT_SECONDS` | `300` | Global execution deadline in seconds. |

---

## 3. Exit Codes

Pipelines rely on predictable exit codes:

| Exit Code | Status | Meaning |
|---|---|---|
| **`0`** | Success | No countable finding met or exceeded the `--fail-on` severity threshold. |
| **`1`** | Failure | One or more countable findings met or exceeded the `--fail-on` threshold. |
| **`2`** | Error | Execution aborted due to invalid configuration, missing policy, corrupted baseline, AI provider failure in-flight, or timeout deadline exceeded. |

> The other flows that enforce the baseline (`-l`, `-r`, `-f`, `-i`, `risk`, `review-pr`) exit **1** on an unusable baseline. See [Baseline: exit codes per flow](baseline-suppressions.md#unusable-baseline-exit-codes-per-flow).

---

## 4. Pipeline Execution Order

1. **Policy Resolution**: Loads active or requested `--policy`. Fails with code 2 if invalid.
2. **Diff Extraction**: Computes normalized diff against base ref or HEAD with smart exclusions.
3. **Static Linter & Secrets**: Executes regex rules, secret scanners, and external bridges (Semgrep, Gitleaks, Bandit).
4. **Preliminary Risk Scoring**: Identifies file-level and aggregated PR risk metrics.
5. **AI Code Review (Optional)**: Calls AI provider (if `--no-ia` is false and API key is present). Degrades gracefully if no key is configured.
6. **Baseline Classification**: If a valid baseline exists, findings are classified as `new`, `existing`, `ignored`, `accepted_debt`, or `resolved`. Without a baseline, findings are unclassified and all count toward failure.
7. **Threshold Evaluation**: Checks countable findings against `--fail-on`.
8. **Artifact Generation & Masking**: Sanitizes secrets and formats report into SARIF, JSON, or JUnit XML.

---

## 5. Artifact Formats

### SARIF 2.1.0 (`--format sarif`)
Follows the official OASIS SARIF 2.1.0 specification.
- Ingested natively by **GitHub Code Scanning**, **GitLab SAST**, and VS Code SARIF Viewer.
- Populates `tool.driver.rules` dynamically from detected findings.
- Maps `error` to level `error`, `warning` to `warning`, and `info` to `note`.
- Carries `fingerprint`, `baseline_status`, and `risk_score` in `properties`.

### JSON Envelope (`--format json`)
Structured JSON envelope containing execution status, summary, risk metrics, and detailed findings:
```json
{
  "version": "1.0.0",
  "gitpr_version": "0.0.37",
  "status": "failure",
  "exit_code": 1,
  "incomplete": false,
  "fail_on": "error",
  "summary": {
    "total": 5,
    "countable": 1,
    "errors": 1,
    "warnings": 4,
    "info": 0,
    "new": 1,
    "existing": 4
  },
  "risk": {
    "score": 65.0,
    "level": "medium",
    "files_count": 3
  },
  "findings": [...]
}
```

### JUnit XML (`--format junit`)
Standard XML test report supported by Jenkins, GitLab CI test summary, and Azure Pipelines.
- Findings that fail the threshold are mapped to `<failure>` tags.
- Non-failing findings are recorded as informational `<system-out>` elements.

---

## 6. GitHub Actions Integration

Use the official composite action in `.github/workflows/ci.yml`:

```yaml
name: CI Check

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Required for GitHub Code Scanning SARIF upload
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run GitPR Check
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }}
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Upload SARIF to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

---

## 7. Migration Guide: Upgrading from Legacy Action Workflow

Prior to the introduction of `gitpr check`, the official composite action (`action.yml`) executed two sequential discrete commands:
1. `gitpr --linter` (failed fast if static errors occurred).
2. `gitpr --fullreview` (generated an unclassified text file `*_PR_FULLREVIEW.txt` on disk, which was optionally concatenated into `$GITHUB_STEP_SUMMARY`).

This design created a breaking contract change when upgrading to modern GitPR:
- **No `*_PR_FULLREVIEW.txt` on disk**: `gitpr check` does not create this text file. Workflows relying on `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` will fail or append nothing.
- **SARIF / Native Code Scanning**: Output is now standard SARIF 2.1.0 (`gitpr-results.sarif` by default), JSON, or JUnit XML, which integrates directly into GitHub's **Security > Code scanning alerts** tab via `github/codeql-action/upload-sarif@v3`.
- **Optional API Key & Zero-Cost CI**: `api-key` is no longer required (`required: false`). Workflows can run entirely offline/zero-cost with `no-ia: "true"`.
- **Deterministic Exit Codes & Baseline Suppressions**: Rather than blindly failing on any linter/review finding, exit codes are strictly controlled by `--fail-on` (default `error`). Findings registered in `.gitpr/baseline.json` are suppressed and do not break the pipeline.

### Contract Comparison: Before vs. After

| Feature | Legacy Workflow (`v0.0.12` – `v0.0.36`) | Modern Unified Check (`v0.0.37+`) |
|---|---|---|
| **Underlying Command** | `gitpr --linter` then `gitpr --fullreview` | `gitpr check` |
| **Output Artifact** | `*_PR_FULLREVIEW.txt` (raw text file) | `gitpr-results.sarif` (SARIF 2.1.0), JSON, or JUnit XML |
| **GitHub UI Integration** | Manual markdown dump into `$GITHUB_STEP_SUMMARY` | Native **Code Scanning** inline PR annotations and alerts |
| **API Key Requirement** | Required (`required: true`) | Optional (`required: false`); supports `no-ia: "true"` |
| **Failure Policy** | Linter failure on error; review unsuppressed | Configurable `--fail-on` (`info`, `warning`, `error`) |
| **Baseline Support** | No suppressions in CI | Full baseline suppressions (`.gitpr/baseline.json`) |
| **Exit Codes** | Ad-hoc per sub-step | Normalized: `0` (clean), `1` (threshold failed), `2` (system error) |

### Workflow Examples: Before & After

#### ❌ Before (Legacy Workflow)

```yaml
name: CI Code Review (Legacy)

on:
  pull_request:
    branches: [main]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # Legacy composite action invocation
      - name: Run GitPR Review
        uses: natanfiuza/gitpr@v0.0.36
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # was mandatory

      # Dependent step that breaks in modern versions:
      - name: Publish Step Summary
        if: always()
        run: |
          REVIEW_FILE=$(ls *_PR_FULLREVIEW.txt 2>/dev/null | head -n 1)
          if [ -f "$REVIEW_FILE" ]; then
            cat "$REVIEW_FILE" >> $GITHUB_STEP_SUMMARY
          fi
```

#### ✅ After (Modern Unified Check)

```yaml
name: CI Check (Modern)

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Required for Code Scanning SARIF upload
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run GitPR Unified CI Check
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # optional when no-ia is true
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Upload SARIF to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

### Preserving Standalone Text Reviews

If your workflow specifically requires generating `*_PR_FULLREVIEW.txt` as a raw text artifact (e.g. for legacy archiving or custom downstream parsers), run `gitpr --fullreview` as a standalone run step instead of using `action.yml`:

```yaml
      - name: Run Standalone Full Review (Legacy Output)
        env:
          DEFAULT_AI_PROVIDER: gemini
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          pip install gitpr-cli
          gitpr --fullreview
```
