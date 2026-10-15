# ADR-013 — `gitpr check`: unified CI command

**Status:** Accepted (2026-10-14)
**Spec:** `docs/plans/20261012_skill_gitpr_check_ci_spec.md`

## Context

The spec proposes a 6-level severity scale, YAML configuration files (`config.schema.yml`, `.gitpr/check.overrides.yml`) and treating every finding as `new` when there is no baseline. The codebase already has a 3-level `NormalizedFinding` (`error|warning|info`), configures everything through `~/.gitpr/.env` + environment, and the baseline gate deliberately refuses to classify without a baseline.

## Decisions

1. **Severity stays 3-level.** `--fail-on` accepts `info|warning|error`; the spec names are aliases (`minor→warning`, `major|critical|blocker→error`). Migrating `NormalizedFinding` to 6 levels would touch linter rules, bridges, baseline and risk — a separate decision.
2. **Configuration via `GITPR_CHECK_*` env keys**, flags > env > defaults. No `config.schema.yml`, no `check.overrides.yml`.
3. **No baseline → `baseline_status = null`**, every finding counts toward `--fail-on`. Nothing is labelled `new` without a baseline to support it. Unusable baseline → exit 2.
4. **Risk is informational only.** `--fail-on` evaluates severity of countable findings; risk appears in SARIF `properties.risk_score` and JSON `risk`.
5. **AI on by default, degrades without key** (warning, skipped). AI provider failure mid-run → exit 2.
6. **Single global deadline** (`GITPR_CHECK_TIMEOUT_SECONDS`, default 300). Exceeding it → exit 2, partial artifact with `incomplete: true`.
7. **Masking is a single choke point** in the output layer, before any serialization.
8. **stdout carries only the artifact** when `--output` is absent; logs go to stderr.
9. **Out of this delivery:** GitHub Checks API adapter. `action.yml` is updated to run `gitpr check` + `upload-sarif`.
10. **Diff base auto-detection in CI:** When `--base` is omitted, check checks `GITHUB_BASE_REF` (e.g. `origin/${GITHUB_BASE_REF}`), then falls back to `origin/main` (or default remote branch), and finally `HEAD` if no remote is reachable.
11. **Full delivery & 5-language parity:** Docs in `docs/check-ci.md` + 4 translations (`pt_br`, `pt_pt`, `es_es`, `fr_fr`), `README.*.md`, and `langs/*.json`.
12. **Dynamic SARIF `tool.driver.rules`:** Synthesized from encountered findings with `id`, `name`, `shortDescription`, and `defaultConfiguration.level` for GitHub Code Scanning / GitLab SAST compatibility.
13. **Structured JSON envelope:** Schema includes `version`, `gitpr_version`, `status`, `exit_code`, `incomplete`, `summary`, `risk`, and `findings`.
14. **Strict policy resolution:** An invalid or unknown policy requested via `--policy` exits with code 2 immediately.

## Consequences

- Existing commands are untouched; `check` only orchestrates existing engines.
- Exit codes are predictable: 0 / 1 / 2.
- CI pipelines can ingest SARIF, JUnit, or JSON without additional adapters.

