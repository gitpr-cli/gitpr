# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add baseline suppressions with fingerprinting and gate
```

---

## 🎯 Summary

Introduces a first-class **baseline suppressions** capability that lets teams silence known findings and keep CI/lint noise focused on what is actually new. The problem it solves: linters and AI reviews re-report the same pre-existing issues on every run, forcing reviewers to mentally diff the output. The baseline records a snapshot of accepted findings in `.gitpr/baseline.json`, fingerprints them stably across runs, and lets the pipeline classify each new finding as *new* or *already known*.

To make this reliable, the finding model was refactored into a canonical domain type, so every linter bridge fingerprints the same data. The feature is fully opt-in and stays a no-op (no file read, no output) when disabled or when no baseline exists, so existing users see no behaviour change.

## 🛠️ Technical Changes

- **i18n**: added ~166 translation keys across six locale files covering all baseline messaging (validation errors, CLI help, config labels, suppression/debt wording, checksum warnings, and the `baseline show/create/update/validate/suppress/unsuppress` surfaces).
- **Finding model refactor**: moved `NormalizedFinding` out of `infrastructure/linter/external/base_bridge.py` into a new canonical `src/domain/finding` package (with `snippet_hash` and `rule_version`); updated all bridges (semgrep, gitleaks, bandit, sast_finding_mapper, calculate_risk, linter_engine) to import from the domain package, with `base_bridge` re-exporting for backwards compatibility.
- **New `src/domain/baseline` package**:
  - `baseline_fingerprint.py` — stable identity (rule identity, normalized path, lines, sha256 of the whitespace-collapsed line; never stores the raw line).
  - `baseline_types.py` — `BaselineStatus`, `SuppressionScope`, `BaselineEntry`, `BaselineManifest`, `BaselineError`, persisted statuses and scope precedence.
  - `baseline_manifest.py` — canonical JSON, checksum, parse/validate (unknown keys, schema/fingerprint versions, suppression and debt invariants, duplicate fingerprints, line ranges).
  - `baseline_comparator.py` — classification, status counts and entry resolution (resolved-then-back reads as new).
  - `suppression_policy.py` — suppressions, accepted debt, overrides, validators, layered matching (entry vs overrides vs policy pack) with specificity and layer precedence, plus overdue debt tracking.
- **Application use cases**: `baseline_gate` (single pipeline entry point; loads/classifies/annotates and composes entry/local/policy override layers), `baseline_summary` (read-only JSON view for IDE/MCP agents), `compare_against_baseline`, `create_baseline` (create/update with provenance, checksums and human-decision preservation), and `suppress_finding` (suppress/unsuppress across finding, line, file and rule scopes).
- **Policy pack integration**: parses and validates a new `baseline:` block via the same validators; the resolver composes it into a tagged layer, and `policy_validate` now reports the pack's baseline block.
- **Infrastructure**: `local_baseline_repository.py` is the sole reader/writer of `.gitpr/baseline.json` and `.gitpr/baseline.overrides.yml`, with atomic writes, checksum/version gating and a repair path.
- **Config**: new `GITPR_BASELINE_ENABLED`, `GITPR_BASELINE_PATH`, `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH`, `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` settings, registered under a new `baseline` category.
- **Risk and linter plumbing**: added `RiskSignal.BASELINE_FINDING` for zero-weight informational evidence; extended the AI review envelope with an optional structured `findings` array; added a `findings_out` side channel in the linter engine recording normalized findings alongside alert strings, plus a fix to the new-side line counter so context lines advance correctly.
- **CLI**: added baseline-aware gate resolution and classification helpers, threaded the gate through the lint, review and `review_pr()` flows, made the exit code baseline-aware for enforcing flows, renamed shared helpers for reuse, and added the `baseline` Click group (`create`, `show`, `validate`, `update`, `suppress`, `unsuppress`, all supporting `--format json`).
- **MCP server**: added the read-only `get_baseline_status` tool and the `baseline://summary` resource, both backed by `baseline_summary` and reporting failures as structured errors rather than raising.
- **Remote PR review**: resolves the baseline before the first network call, merges gate warnings, and annotates linter alerts before composing the report/comment.
- **Templates**: excluded `.gitpr/baseline.json` and `.gitpr/baseline.overrides.yml` from GitPR's own scans.
- **Tests**: added a large suite covering gate, summary, create/update, suppress/unsuppress, domain types, comparator, fingerprint golden digests, manifest, suppression policy, repository, structured linter findings and CLI/MCP integration; extended policy manifest/resolver tests and stabilized env handling in `test_config_app.py`.

## ⚠️ Impact/Warnings

- **No database or dependency changes.** The feature is fully gated behind `GITPR_BASELINE_*` environment variables and is a no-op when disabled or when no baseline file exists.
- **Behavioural change in enforcing flows**: a baseline file that cannot be applied now aborts the lint, review, full review, file audit, remote PR and risk flows with exit code 1.
- **Exit code semantics**: for the lint flow the exit code now follows baseline-aware blocking rather than raw `has_errors`, so new findings still fail while known ones do not.
- **New files created on disk**: `.gitpr/baseline.json` and `.gitpr/baseline.overrides.yml` when the feature is used; both are excluded from GitPR's own scans.
- **Config surface change**: new environment variables must be documented for operators enabling the feature.

close #204

---

[![GitPR](https://img.shields.io/badge/GitPR-4_errors_%C2%B7_10_warnings-red)](https://gitpr.natanfiuza.dev.br/)