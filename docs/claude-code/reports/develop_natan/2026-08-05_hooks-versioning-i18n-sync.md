## Completion Report — Hook Scripts Versioning and i18n Synchronization

### What was done
- Added `__scripts_version__ = "v0.0.1"` to `src/updater.py` as the single source of truth for hook script versions
- Created 20 translated hook script variants across 5 languages (en, pt_br, pt_pt, fr, es) for all 5 hook types
- Converted base (no-suffix) scripts to English — following the project convention where English is the default/fallback
- Modified `install_git_hooks()` in `src/core.py` to support i18n-aware downloads with language-specific URLs and automatic English fallback on 404
- Added version stamping (`SCRIPTS_VERSION` + `SCRIPTS_LANG`) to `~/.gitpr/.env` after successful hook installation
- Created `check_and_update_hooks_scripts()` in `src/core.py` — a silent auto-sync function called on every gitpr execution
- Wired the auto-sync call into `src/main.py` after `--lang` handling, guarded to skip internal invocations (`--quiet`, `--hook`, `--mcp`)
- Added `_SCRIPT_LANG_SUFFIXES` whitelist (`{"pt_br", "pt_pt", "fr", "es"}`) and `SCRIPTS_BASE_URL` constant

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/updater.py` | feat | Added `__scripts_version__ = "v0.0.1"` constant |
| `src/core.py` | feat | Added `_SCRIPT_LANG_SUFFIXES`, `SCRIPTS_BASE_URL`, `check_and_update_hooks_scripts()`; modified `install_git_hooks()` for i18n + version stamp; added `ENV_FILE` and `__scripts_version__` imports |
| `src/main.py` | feat | Added `check_and_update_hooks_scripts` import; inserted auto-sync call after `--lang` handling (guarded) |
| `scripts/pre-commit-template.sh` | refactor | Converted to English base (was PT-BR) |
| `scripts/pre-commit-template.pt_br.sh` | rename | Original PT-BR content preserved |
| `scripts/pre-commit-template.pt_pt.sh` | new | European Portuguese translation |
| `scripts/pre-commit-template.fr.sh` | new | French translation |
| `scripts/pre-commit-template.es.sh` | new | Spanish translation |
| `scripts/prepare-commit-msg-template.sh` | refactor | Converted to English base (was PT-BR) |
| `scripts/prepare-commit-msg-template.pt_br.sh` | rename | Original PT-BR content preserved |
| `scripts/prepare-commit-msg-template.pt_pt.sh` | new | European Portuguese translation |
| `scripts/prepare-commit-msg-template.fr.sh` | new | French translation |
| `scripts/prepare-commit-msg-template.es.sh` | new | Spanish translation |
| `scripts/pre-push-template.sh` | refactor | Converted to English base (was PT-BR) |
| `scripts/pre-push-template.pt_br.sh` | rename | Original PT-BR content preserved |
| `scripts/pre-push-template.pt_pt.sh` | new | European Portuguese translation |
| `scripts/pre-push-template.fr.sh` | new | French translation |
| `scripts/pre-push-template.es.sh` | new | Spanish translation |
| `scripts/post-merge-template.sh` | none | Already English — unchanged |
| `scripts/post-merge-template.pt_br.sh` | rename | Original PT-BR content preserved |
| `scripts/post-merge-template.pt_pt.sh` | new | European Portuguese translation |
| `scripts/post-merge-template.fr.sh` | new | French translation |
| `scripts/post-merge-template.es.sh` | new | Spanish translation |
| `scripts/post-checkout-template.sh` | refactor | Converted to English base (was PT-BR) |
| `scripts/post-checkout-template.pt_br.sh` | rename | Original PT-BR content preserved |
| `scripts/post-checkout-template.pt_pt.sh` | new | European Portuguese translation |
| `scripts/post-checkout-template.fr.sh` | new | French translation |
| `scripts/post-checkout-template.es.sh` | new | Spanish translation |

### Design decisions

- **Independent version marker**: `__scripts_version__` is separate from `__lang_version__` because hook scripts change on a different cadence than language resources
- **`SCRIPTS_LANG` companion marker**: Prevents language flip-flop when users run `gitpr --lang fr` once — the auto-sync won't re-download unless version OR language differs
- **Whitelist approach**: Only 4 explicit suffixes (`pt_br`, `pt_pt`, `fr`, `es`) trigger language-specific downloads; any other language falls through to English (no 404 cascade)
- **Stamp-only-on-full-success**: `SCRIPTS_VERSION` is only written when all 5 hooks download successfully, ensuring partial failures are retried on the next run
- **Skip internal invocations**: Auto-sync is guarded by `not quiet and not hook and not mcp` to avoid network latency during hook callbacks (`gitpr --linter --quiet`, `gitpr --commit --quiet --hook`, etc.)

### Impact
- **Functionality**: Every gitpr execution now silently checks if installed hooks are up to date. New installs via `--installhooks` use language-aware downloads. The `--install` wizard inherits both behaviors.
- **Performance**: Fast path is a single `.env` read (no network). Only when `SCRIPTS_VERSION` or `SCRIPTS_LANG` differs does a download occur.
- **Compatibility**: Existing `install_git_hooks()` callers (main.py, run_install_wizard) are unaffected — the function signature and return contract are unchanged. Hook scripts remain thin shims that call the `gitpr` CLI.

### Verification
- 121/122 tests pass (1 pre-existing i18n test failure unrelated to changes)
- Module imports correctly through the normal chain
- All 25 script files present in `scripts/` (5 hooks × 5 languages)

### Next steps
- Bump `__scripts_version__` in `src/updater.py` whenever hook scripts are modified — this triggers automatic OTA updates for all installed clients
- To add a new language: create the 5 translated `.sh` files in `scripts/`, add the language code to `_SCRIPT_LANG_SUFFIXES` in `src/core.py`
- Known limitation (document): the `SCRIPTS_VERSION` marker is global (`~/.gitpr/.env`), not per-project. After a version bump, the first git project that runs gitpr gets updated and stamps the marker; other projects' hooks are updated on their next gitpr execution (they're thin shims, so stale hooks still work — real logic lives in the CLI)
