# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add SAST bridge integration for Semgrep, Gitleaks and Bandit
```

---

## 🎯 Summary
GitPR's linter was limited to regex-based rules and Checkstyle XML bridges, which can only catch patterns explicitly authored by the user. To raise the security bar of every review without adding cost to users who don't need it, this change introduces an opt-in SAST layer that plugs third-party security scanners (Semgrep, Gitleaks, Bandit) into the existing linter pipeline. The scanners run only when explicitly enabled, only over the files touched by the diff, and their findings are normalized and deduplicated against the existing regex ruleset so a secret detected by both the internal ruleset and Gitleaks is reported once with a multi-source confirmation marker instead of twice.

## 🛠️ Technical Changes
- Add `src/infrastructure/linter/external/` package with an `ExternalLinterBridge` abstract base (hardened `subprocess` execution: `shell=False`, strict timeout, `DEVNULL` stdin, UTF-8 with `errors='replace'`) and concrete bridges for `SemgrepBridge`, `GitleaksBridge` and `BanditBridge`.
- Introduce a shared `NormalizedFinding` / `ExternalLinterResult` data model so every tool produces findings in the same severity (`error`/`warning`/`info`) and shape.
- Add `src/domain/linter/sast_finding_mapper.py` with `format_finding_message()` (uniform alert formatting with tool and rule id) and `deduplicate_secret_findings()` (merges Gitleaks and regex findings on the same file and line into a single `[Gitleaks + Regex]` confirmed entry).
- Mask secret values in Gitleaks output (`mask_secret_value`) so credentials never leak into findings, logs or telemetry.
- Add `load_sast_config()` in `src/config.py`, reading defaults, then `.gitpr.linter.yml` (`sast` block, falling back to `linter.external`), then `GITPR_SAST_*` environment variables. All tools default to `enabled: false` (strict opt-in).
- Register three new config fields in `src/config_schema.py` (`GITPR_SAST_SEMGREP_ENABLED`, `GITPR_SAST_GITLEAKS_ENABLED`, `GITPR_SAST_BANDIT_ENABLED`), all `KIND_BOOL` in the `linter` category and default `false`.
- Wire SAST execution into `src/linter_engine.py` for both the full-file path and the diff path, filtering findings by added lines when in diff mode, and emitting a warning when a tool is enabled but missing from `PATH`.
- Normalize file paths from all bridges to forward slashes and relative-to-repo form so they match the diff's modified-file keys on Windows and Unix.
- Harden `_write_real_stdout` in `src/mcp_server.py` against `UnicodeEncodeError` on legacy Windows code pages (fall back to `buffer` or re-encode with `errors='replace'`).
- Add translation entries for the new SAST labels and messages across `es`, `es_es`, `fr`, `fr_fr`, `pt_br` and `pt_pt`, and alphabetize/reorder keys to keep parity with the English source.
- Add unit tests for the bridges (availability, subprocess timeout, missing binary, JSON parsing, severity mapping, secret masking, non-Python skipping) and for the finding mapper and deduplication logic.

## ⚠️ Impact/Warnings
- **New external dependencies (optional, runtime only):** `semgrep`, `gitleaks` and `bandit` are not Python packages added to `setup/requirements`; they are external binaries that must be installed and reachable on the `PATH`. If a tool is enabled but missing, GitPR logs `⚠️ SAST tool '{tool}' is enabled in config but was not found in PATH.` and continues without failing the run.
- **Behavior change:** when SAST is enabled, findings influenced by external rulesets will appear in linter output and in PR/review artifacts. Nothing is enabled by default (`enabled: false`), so existing users see no change until they opt in via `.gitpr.linter.yml` or the new `GITPR_SAST_*` environment variables.
- **New environment variables:** `GITPR_SAST_SEMGREP_ENABLED`, `GITPR_SAST_GITLEAKS_ENABLED`, `GITPR_SAST_BANDIT_ENABLED`, plus `GITPR_SAST_<TOOL>_TIMEOUT` to override defaults (60s / 30s / 45s). All optional and backward compatible.
- **Secrets handling:** Gitleaks does not emit raw secrets into findings — values are masked (`AKIA****`) before being surfaced.
- **No database changes.** Metrics export files under `.gitpr/metrics/export/` are generated artifacts.
- **Performance:** each enabled SAST tool spawns a subprocess per run (and per file for Gitleaks), bounded by strict timeouts. Enabling multiple tools on large diffs will increase linter latency; scope is limited to modified files to keep it bounded.

close #185

---

[![GitPR](https://img.shields.io/badge/GitPR-4_errors_%C2%B7_2_warnings-red)](https://gitpr.natanfiuza.dev.br/)