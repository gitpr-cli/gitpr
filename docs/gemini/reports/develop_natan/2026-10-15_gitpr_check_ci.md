## Completion Report — `gitpr check`: Unified CI Command

### What was done
- Implemented `gitpr check` unified command for Continuous Integration (CI) pipelines (GitHub Actions, GitLab CI, Azure Pipelines, Jenkins).
- Created domain models in `src/domain/check/` (`check_types.py`, `check_config.py`, `check_output.py`):
  - Normalized 3-level severity scale (`error`, `warning`, `info`) with spec aliases (`minor -> warning`, `major|critical|blocker -> error`).
  - Precedence configuration: `CLI flags > Environment Variables (GITPR_CHECK_*) > Defaults`.
  - Structured output serialization for SARIF 2.1.0, JSON envelope, and JUnit XML with atomic file writing.
- Created infrastructure builders in `src/infrastructure/ci/`:
  - `masking.py`: Choke point for sensitive token, credential, and secret sanitization before serialization.
  - `sarif_builder.py`: Compliant with OASIS SARIF 2.1.0 and GitHub Code Scanning, with dynamically generated `tool.driver.rules`.
  - `junit_builder.py`: Standard testsuites XML mapping failing findings to `<failure>` tags and info/warning to `<system-out>`.
- Implemented application use case in `src/application/use_cases/run_check.py`:
  - Diff auto-detection (`--base`, `GITHUB_BASE_REF`, `origin/main`, fallback `HEAD`).
  - Strict policy resolution (`--policy`, exiting with 2 if invalid).
  - Linter regex, secret scanner, and external bridges execution.
  - Preliminary and aggregated risk scoring.
  - Optional AI code review (`--no-ia`, `--ia-only-high-risk`, graceful degradation if no key configured, in-flight failure exiting with 2).
  - Baseline classification (`new`, `existing`, `ignored`, `accepted_debt`, `resolved`), with corrupted baseline exiting with 2.
  - Fail threshold evaluation (`--fail-on`), with deterministic exit codes: `0` (success), `1` (failing findings), `2` (execution error/timeout).
- Registered `@cli.command("check")` in `src/main.py`:
  - Clean stream separation: stdout emits only the raw artifact when `--output` is absent; warnings and logs are written strictly to `stderr`.
- Updated `action.yml` to use `gitpr check`.
- Authored full technical documentation in 5 languages:
  - `docs/check-ci.md` (EN), `docs/check-ci.pt_br.md`, `docs/check-ci.pt_pt.md`, `docs/check-ci.es_es.md`, `docs/check-ci.fr_fr.md`.
- Updated `README.md` and 4 localized READMEs (`README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`).
- Added i18n translation keys across all 6 language files in `langs/`.
- Authored full unit and CLI test suite (37 tests across domain, infrastructure, use cases, and CLI).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/domain/check/check_types.py` | feat | Unified finding, summary, result, and severity domain models |
| `src/domain/check/check_config.py` | feat | Config loader with CLI > env > defaults precedence |
| `src/domain/check/check_output.py` | feat | Artifact formatter and atomic file writer |
| `src/domain/check/__init__.py` | feat | Package exports |
| `src/infrastructure/ci/masking.py` | feat | Secret and credential masking engine |
| `src/infrastructure/ci/sarif_builder.py` | feat | SARIF 2.1.0 builder with dynamic driver rules |
| `src/infrastructure/ci/junit_builder.py` | feat | JUnit XML builder with failure/system-out mapping |
| `src/infrastructure/ci/__init__.py` | feat | Package exports |
| `src/application/use_cases/run_check.py` | feat | Main orchestrator use case |
| `src/main.py` | feat | Click `@cli.command("check")` registration and stdout/stderr separation |
| `action.yml` | feat | Updated composite GitHub Action to run `gitpr check` |
| `docs/check-ci*.md` (5 files) | docs | Full user and pipeline documentation in EN, PT-BR, PT-PT, ES-ES, FR-FR |
| `README*.md` (5 files) | docs | Added `gitpr check` to command listings across all 5 languages |
| `langs/*.json` (6 files) | feat | Added i18n translation keys |
| `docs/plans/ADR-013-check-ci-command.md` | docs | Architectural Decision Record updated with grill decisions |
| `docs/plans/glossary-check-ci.md` | docs | Domain glossary |
| `docs/survey/20261012_check_ci_surveyfacts.md` | docs | Survey of grill decisions and codebase facts |
| `docs/plans/develop_natan/20261012_check_ci_plansfacts.md` | docs | Execution plan document |
| `tests/domain/check/*` | test | Unit tests for domain models and config |
| `tests/infrastructure/ci/*` | test | Unit tests for masking, SARIF, and JUnit builders |
| `tests/application/use_cases/test_run_check.py` | test | Use case tests covering exit codes, baseline, AI, and policies |
| `tests/test_check_cli.py` | test | Click runner CLI integration tests |

### Impact
- **Functionality:** Provides a unified command (`gitpr check`) specifically tailored for CI/CD pipelines, supporting SARIF upload to GitHub Code Scanning / GitLab SAST.
- **Performance:** `--no-ia` and `--ia-only-high-risk` allow sub-second local linting and secret scanning without network overhead.
- **Compatibility:** 100% backward compatible; existing commands (`gitpr -r`, `gitpr --linter`, `gitpr baseline`, `gitpr risk`) are completely untouched.

### Next steps (if applicable)
- In a future cycle, consider optional direct GitHub Checks API adapter if token-based direct check-run creation is desired without relying on composite actions.
