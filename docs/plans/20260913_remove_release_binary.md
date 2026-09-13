# Remove the release binary — force updates via pip

## Context

GitPR currently ships two distribution channels: the PyPI package (`pip install gitpr-cli`) and a
standalone PyInstaller executable published as a GitHub Release asset. The auto-updater in
[src/updater.py](src/updater.py) branches on `getattr(sys, "frozen", False)`: frozen builds
download `gitpr.exe` from GitHub Releases and *hot-swap* themselves (`_perform_hot_swap`,
`os.rename` + `urllib.request.urlretrieve` + rollback); pip builds only print a notice.

The binary channel is being dropped. It has real defects today — `urlretrieve` has no timeout and
no checksum check, and [src/main.py:744-750](src/main.py#L744-L750) unconditionally deletes the
`.old` backup on the next run, so a truncated download is unrecoverable. It is also already
half-dead: the hardcoded asset name `"gitpr.exe"` is Windows-only, and **no release workflow was
ever committed** (`.github/workflows/` holds only `pr-review.yml`; `action.yml` already installs
from PyPI).

Replacing it: version detection stays, but finding a newer version on PyPI now **blocks execution**
and instructs the user to run `pip install --upgrade gitpr-cli`.

Source of truth for this task: [docs/plans/20260912_remocao_binario_release.md](docs/plans/20260912_remocao_binario_release.md).

### Decisions taken with the user

| Decision                                                                      | Choice                                                                                                      |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Behaviour on new version                                                      | **Hard block** — print instructions, exit non-zero, do no work. Suppressed in `--quiet`, `--hook`, `--mcp`. |
| `-u` / `--update` flag                                                        | **Kept**, but pip-only output (check PyPI + print the upgrade command).                                     |
| PyInstaller in Pipfile / `gitpr.spec` / `icon.ico`                            | **Removed.**                                                                                                |
| `run.py`                                                                      | **Kept** — it is not PyInstaller-only (see below).                                                          |
| Historical docs (`docs/plans/`, `docs/reports/`, `docs/claude-code/reports/`) | **Left untouched.**                                                                                         |

---

## 1. Code — `src/updater.py`

The whole file is the surgery site. Target end state:

- **Delete** `GITHUB_API_URL` (line 20) and `_perform_hot_swap()` (lines 179-200) entirely.
- **`get_latest_remote_version()`** (lines 43-101): drop the `is_compiled` parameter and the
  `if is_compiled:` GitHub branch (lines 63-75). Always query `PYPI_API_URL`. Return the version
  string instead of the `(version, download_url)` tuple, and stop writing `download_url` into
  `~/.gitpr/update_cache.json` (keep the daily-cache behaviour and the silent
  `except Exception: pass`; old cache files stay readable since the extra key is ignored).
- **Replace `print_update_notice()`** (lines 104-136): its end-of-run role is superseded by the
  startup block. The new function — e.g. `enforce_update_required()` — compares `__version__`
  against the remote version and, when older, prints the block message to stderr and exits
  non-zero. Return a bool/raise so the caller stays testable instead of calling `sys.exit` deep
  inside (`src/config.py:485` already sets the `sys.exit(1)` precedent for the offline guard).
- **Rewrite `check_and_update()`** (lines 139-176): delete the `if not is_compiled: … return`
  early-out and the `_perform_hot_swap` call. It becomes: query PyPI → if newer, print the new
  version + `pip install --upgrade gitpr-cli`; otherwise print "already on the latest version".

Leave the version constants (`__version__`, `__lang_version__`, `__scripts_version__`, lines 12-16)
and the `from src.i18n import __` placement (line 18) exactly as they are — `i18n.py` and
`pyproject.toml` (`version = {attr = "src.updater.__version__"}`) depend on that ordering.

## 2. Code — `src/main.py`

- **Remove** the `is_compiled` / `.old` cleanup block at lines 740-750 and its PyInstaller
  comment. This is the only hot-swap cleanup in the codebase.
- **Add** the blocking check inside `cli()`. The insertion point is **after the `--lang` handler
  (ends line 613) and before the hook-sync guard (line 615)**. Rationale: it must sit *after*
  `set_lang()` so the message renders in the requested language, and *before* the flag dispatch —
  `--linter` returns at ~758 and many flags return before `check_internet_connection()` at line
  854, so placing it next to the `--update` dispatch would leave most commands unguarded.
- **Exemptions** (block must not fire for): `--quiet`, `--hook`, `--mcp` (mirroring the existing
  guard at lines 615-619), the separate `gitpr-mcp` entry point
  ([src/mcp_server.py](src/mcp_server.py)), `--update` (chicken-and-egg — it is the very command
  that explains how to update), and the custom contextual-help path `help_flag`.
  `ctx.invoked_subcommand is not None` already returns at line 547, so the `release` subcommand is
  covered for free. **`--help` and `--version` need no exemption**: both are eager Click options
  (`@click.version_option` at line 271) that print and exit during parameter processing, before the
  callback body runs.
- **Remove** the five `print_update_notice()` call sites (lines 1474, 1489, 1506, 1517, 1597) and
  the import at line 45 — the startup block replaces them.
- **Rewrite the `update` help-entry description** at lines 120-127 (the i18n key mentioning
  "standalone binary (GitHub Releases) with hot-swap and automatic rollback").

**Offline behaviour:** when `get_latest_remote_version()` returns `""` (no network and a stale
daily cache) the block must **not** fire — an offline user must never be locked into a command
they cannot run. A stale cache can only exist if a live fetch succeeded earlier the same day, so
the worst case is a user who went online in the morning and is offline in the afternoon; that is
acceptable. Note the block runs before `check_internet_connection()` (line 854, which
`sys.exit(1)`s when offline), on purpose — otherwise the guard would pre-empt the block for every
normal command.

### Test-suite isolation (must be part of this change)

Every `cli()` invocation now performs a live PyPI lookup, and three existing suites drive the CLI
through `CliRunner` ([tests/test_release_cli.py](tests/test_release_cli.py),
[tests/test_config_cli.py](tests/test_config_cli.py),
[tests/test_main_suggest_reviewers.py](tests/test_main_suggest_reviewers.py)). All three are
`unittest.TestCase`-based, so **pytest autouse fixtures do not reach them** — and offline they
would each pay the 3s timeout on every invocation.

The fix follows an existing precedent: [tests/conftest.py](tests/conftest.py) already sets
`os.environ["GITPR_SHOW_LOGS"] = "false"` at import time, before any project module loads, relying
on the fact that every `load_dotenv()` in the codebase uses `override=False`. Add the same line for
a new `GITPR_SKIP_UPDATE_CHECK` read by the blocking check. `tests/test_updater.py` then overrides
it per-test to exercise the block itself.

> Honest consequence to note: because the variable is read by production code, it is technically a
> bypass a user could set. It is not advertised as one and is not a "compatibility mode keeping the
> binary" — rule 4 of the source plan only forbids fallbacks that keep the *binary* available. If
> you would rather have no bypass at all, the alternative is to have `tests/test_updater.py`
> monkeypatch `get_latest_remote_version` and accept a 3s network stall on offline test runs.

## 3. Build tooling

- **`Pipfile`** — drop `pyinstaller = "*"` from `[dev-packages]` (line 18). `pytest`, `pytest-cov`,
  `build`, `twine` stay.
- **Delete `icon.ico`** — tracked, and its only references are the PyInstaller build command in the
  five READMEs plus `CLAUDE.md`/`GEMINI.md`. Nothing else uses it.
- **Delete `gitpr.spec`** — the local PyInstaller spec (untracked; `.gitignore` has `*.spec`).
- **Keep `run.py`.** It is *not* PyInstaller-only: it is the dev entry point documented in
  `docs/git-hooks-locais.md`, referenced by the project skills, and — importantly — scanned by the
  i18n tooling ([tests/test_i18n.py](tests/test_i18n.py) `SCAN_ROOTS`, `tests/sync_i18n.py`,
  `scripts/fix_mangled_i18n_keys.py`). Deleting it would break those.
- **`.gitignore`** — leave `build/`, `dist/` (setuptools also writes there) but fix the
  `# Arquivos de Build do PyInstaller` comment.
- Leave the local `build/` and `dist/` directories alone; `build/gitpr.exe` is gitignored and
  `dist/` holds the wheels/sdist that are still published.

## 4. Documentation

The mechanism that spreads this change: every doc exists in 5 language variants
(`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`). All variants of a file must be updated
together.

| File (×5 variants)                                           | Change                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [docs/auto-update.md](docs/auto-update.md)                   | Delete §3.2 "Binary Installation (PyInstaller)"; collapse the §5 version-source table to PyPI only; reword §1 (`--update` checks, does not install); **add a section documenting the mandatory startup block**.                                                                                                          |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)                 | §17 "Auto-Update System" — remove the PyInstaller/hot-swap/relaunch paragraph (which also claims a seamless relaunch that never existed in code); stack table row `\| Packaging \| PyInstaller (standalone executable) \|`; the `updater.py` tree comment "Version check (PyPI + GitHub), hot-swap and version markers". |
| [docs/mcp-integration.md](docs/mcp-integration.md)           | Prerequisites line ~230: "`pip install gitpr-cli` or the standalone binary" → pip only.                                                                                                                                                                                                                                  |
| [docs/testar_sem_usar_pypi.md](docs/testar_sem_usar_pypi.md) | Line 34 — drop the warning about a leftover `gitpr.exe` in `dist/`.                                                                                                                                                                                                                                                      |
| [docs/version-markers.md](docs/version-markers.md)           | Line 3 — "resources **outside** the released binary" → reword to the installed package.                                                                                                                                                                                                                                  |
| [README.md](README.md)                                       | Delete the "📦 How to Compile the Executable Locally" section (lines 52-71); replace "⚙️ Installation and Configuration → Using the Executable (Recommended)" (lines 89-111) with the pip flow; rewrite "🔄 Auto-Updater (Over-The-Air Update)" (lines ~457-463) — no more "downloading the new `.exe`".                    |
| [CLAUDE.md](CLAUDE.md)                                       | Line 5 (distribution channels), line 125 (`-u/--update` table row), line 144 (`Packaging \| PyInstaller`), lines 165-166 (build command), lines 344-347 ("Auto-Updater (Hot-Swap)" section → describe the block).                                                                                                        |
| [GEMINI.md](GEMINI.md)                                       | Twin of `CLAUDE.md` — same edits (lines 5, 124, 147, 172-173, 374-377).                                                                                                                                                                                                                                                  |

**Left as historical record** (per the decision above): `docs/plans/*`, `docs/reports/relatorio_estado_*.md`,
`docs/claude-code/reports/*`, and existing dated `CHANGELOG.md` entries.

**One flagged exception:** [docs/plans/20260827_plano_specs_backlog.md](docs/plans/20260827_plano_specs_backlog.md)
Item 8 proposes *creating* a `release.yml` workflow that builds the binary with PyInstaller and
attaches it as a Release asset. It is a live backlog item, not a historical report, and it now
directly contradicts the architecture — this plan strikes it unless you say otherwise.

## 5. Changelog

Add an entry to the `## [Unreleased]` section of [CHANGELOG.md](CHANGELOG.md) (line 133): a
`### Removed` block covering the standalone binary, the hot-swap updater and the `gitpr.exe`
release asset, plus a note that updates are now enforced via `pip install --upgrade gitpr-cli`.
Do not rewrite the dated entries — line 313 describes the 0.0.26 auto-updater as it was then.

## 6. i18n — the lockstep requirement

English is the source language, so a new/changed key in `src/main.py` must be propagated by hand to
four places or the parity checks fail:

1. the English key in `src/main.py` (source of truth);
2. `langs/pt_br.json` — the **master key list**; `scripts/sync_all_langs.py` deletes any key from
   the other files that is absent here, and uses `pt_br` to seed `pt_pt` (line 1077);
3. the `FR` dict (line 20) **and** `ES` dict (line 540) inside `scripts/sync_all_langs.py` — these
   hold the comprehensive translations and are the second source of truth;
4. then regenerate: `python scripts/sync_all_langs.py` rewrites `langs/{pt_pt,es,fr,es_es,fr_fr}.json`.

Because the English help string at `src/main.py:124` **changes text**, its old key must be removed
from `langs/pt_br.json` and both sync dicts, not just replaced — otherwise an orphan key survives.

New keys needed: the block message (with `{current_version}` / `{latest_version}` placeholders) and
the rewritten `--update` output lines, following the existing `__("… {version}", version=…)` style.

## 7. Verification

1. **Static — zero remaining references.** Rule 9 of the source plan, scoped to exclude the
   historical folders:
   ```bash
   grep -rn "gitpr\.exe\|PyInstaller\|pyinstaller\|hot-swap\|onefile" \
     --include="*.py" --include="*.md" --include="*.yml" --include="*.toml" --include="*.json" . \
     | grep -v "^./docs/plans/" | grep -v "^./docs/reports/" \
     | grep -v "^./docs/claude-code/reports/" | grep -v "^./build/" | grep -v "^./.git/"
   ```
   Expect only unrelated `.exe` hits (`gitpr-mcp.exe` console script, linter path-splitting).
2. **Unit tests (new `tests/test_updater.py`).** There is no updater test today. Add
   `os.environ["GITPR_SKIP_UPDATE_CHECK"] = "true"` to [tests/conftest.py](tests/conftest.py)
   (next to the existing `GITPR_SHOW_LOGS` line) so the pre-existing CLI suites stay offline-safe,
   then have `tests/test_updater.py` override it per-test. Use the `HomeSandbox` pattern from
   [tests/test_usage_log.py](tests/test_usage_log.py) (lines 32-47) to isolate
   `~/.gitpr/update_cache.json`, and monkeypatch the remote-version lookup:
   - newer version available → block fires, exit non-zero, nothing else runs;
   - same version → no block;
   - `--quiet`, `--hook`, `--mcp`, `--update`, contextual `-h --<flag>` → never block;
   - offline / empty remote version → no block (must not brick an offline user);
   - `check_and_update()` with `--update` prints the pip command and performs no download.
3. **i18n parity.**
   ```bash
   python scripts/validate_i18n.py && python -m pytest tests/test_i18n.py -v
   ```
4. **Full suite + smoke tests.**
   ```bash
   python -m pytest tests/ -v
   pipenv run python run.py -h          # help renders, --update description updated
   pipenv run python run.py -u          # prints the pip upgrade command
   pipenv run python run.py -c          # normal command unaffected when up to date
   ```
5. **Force the block** by temporarily lowering `__version__` in `src/updater.py` (or seeding
   `~/.gitpr/update_cache.json` with a higher version for today's date) and confirming the CLI
   exits non-zero with the pip instructions, then restoring it.
6. **Mandatory completion report** at
   `docs/claude-code/reports/develop_natan/2026-09-13_remocao_binario_release.md`
   (per the CLAUDE.md task workflow).

## Notes and risks

- **The block will not fire today.** PyPI's latest `gitpr-cli` is `1.0.0`, identical to
  `__version__` in [src/updater.py:12](src/updater.py#L12), so the tool stays usable right after
  this change lands. It becomes active only when a newer version is published — which means the
  first release cut after this change is the real test of the block.
- **The hard block is aggressive.** A user who pinned an old version on purpose — or who installed
  via `pipx`/`uv`/`poetry` rather than `pip` — will be locked out, and the printed command may not
  match their installer. The exemption list protects hooks, CI and MCP; everything interactive is
  blocked.
- **No `git commit`/`git push`** — per CLAUDE.md, all changes stay in the working tree.
- Deleting the tracked `icon.ico` and removing `pyinstaller` from the `Pipfile` will require a
  `pipenv lock` refresh if the user keeps the lockfile current.
