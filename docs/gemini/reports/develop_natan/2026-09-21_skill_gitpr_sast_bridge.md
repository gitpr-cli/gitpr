## Completion Report — GitPR SAST Bridge (Semgrep, Gitleaks, Bandit)

### What was done
- **Infrastructure Bridges:** Implemented `src/infrastructure/linter/external/base_bridge.py` (`ExternalLinterBridge`, `ExternalLinterResult`, `NormalizedFinding`) with strict subprocess hardening invariants (`shell=False`, argument list passing, explicit timeouts, UTF-8 output capture with `errors='replace'`).
- **Dedicated SAST Tool Bridges:**
  - `src/infrastructure/linter/external/gitleaks_bridge.py`: Gitleaks integration with entropy secret scanning, `--no-git` diff-only support, and strict secret masking (`mask_secret_value`).
  - `src/infrastructure/linter/external/semgrep_bridge.py`: Semgrep multi-language SAST integration with severity mapping (`ERROR`/`WARNING`/`INFO` -> `error`/`warning`/`info`).
  - `src/infrastructure/linter/external/bandit_bridge.py`: Bandit Python SAST integration conditioned to modified `.py` files.
- **Domain & Mapper:** Implemented `src/domain/linter/sast_finding_mapper.py` for standard message formatting and automatic deduplication between static regex rules (`security_ruleset.py`) and Gitleaks (`[Gitleaks + Regex]`).
- **Configuration & Opt-in:** Added `load_sast_config()` in `src/config.py` and configuration fields in `src/config_schema.py` for `.env` overrides (`GITPR_SAST_*`). All bridges default to `enabled: false` (opt-in).
- **Linter Engine Integration:** Connected SAST bridges in `src/linter_engine.py` across diff and full-file modes, with error & warning aggregation.
- **i18n & MCP Fixes:** Added all localized keys in `langs/` and hardened stdout encoding in `src/mcp_server.py` for legacy Windows terminal encodings (cp1252).
- **Test Suite:** Created complete unit test coverage for bridges, subprocess security, JSON parsing fixtures, secret masking, and deduplication (all 123 tests passing).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/infrastructure/linter/external/base_bridge.py` | feat | Base abstract bridge and NormalizedFinding/ExternalLinterResult models |
| `src/infrastructure/linter/external/__init__.py` | feat | Package marker for external linter & SAST bridges |
| `src/infrastructure/linter/external/gitleaks_bridge.py` | feat | Gitleaks secret scanning bridge with secret masking |
| `src/infrastructure/linter/external/semgrep_bridge.py` | feat | Semgrep multi-language SAST bridge |
| `src/infrastructure/linter/external/bandit_bridge.py` | feat | Bandit Python SAST bridge |
| `src/domain/linter/sast_finding_mapper.py` | feat | Finding message formatter and regex/Gitleaks deduplication |
| `src/domain/linter/__init__.py` | feat | Package marker for domain linter module |
| `src/config.py` | feat | SAST config loader from .env and .gitpr.linter.yml |
| `src/config_schema.py` | feat | Configuration schema fields for GITPR_SAST_* |
| `src/linter_engine.py` | feat | SAST execution integration in diff and full-file linting pipelines |
| `src/mcp_server.py` | fix | UTF-8 stdout encoding fallback for Windows terminals |
| `langs/*.json` | feat | Added i18n translations for SAST config and warnings |
| `tests/infrastructure/linter/external/*` | test | Unit tests for base, Gitleaks, Semgrep, and Bandit bridges |
| `tests/domain/linter/*` | test | Unit tests for SAST finding mapper and deduplication |

### Impact
- **Functionality:** Users can now opt-in to advanced SAST tools (Semgrep, Gitleaks, Bandit) within GitPR's linter and PR validation flow without breaking environments where these binaries are not installed.
- **Security:** Strict subprocess execution guarantees (no `shell=True`, argument sanitization, strict timeouts, secret masking in findings).
- **Compatibility:** 100% backward compatible with existing linter configurations and Checkstyle bridges.

### Next steps (if applicable)
- Add documentation in `docs/sast-integration.md` explaining how to install and enable each SAST tool.

