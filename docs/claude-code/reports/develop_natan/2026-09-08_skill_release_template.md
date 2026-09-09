# Completion Report — Skill `.gitpr.release.md` (5 idiomas) + fluxo `gitpr release`

## What was done

- Created the release skill family: `templates/gitpr.release.md` (EN) plus 4 whole-file manual translations (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`) following the `gitpr.issue.*` pattern — persona "Release Manager", strict `{"summary": "..."}` JSON contract, editable by the user as system instruction of the AI executive summary.
- Registered `release` in the `-s` skill downloader (`files_to_download` in `core.py`) and extracted a reusable per-file downloader (`download_skill_file`) + the language-gated `ensure_release_skill_template()`.
- **R4 — first-use auto-download:** `gitpr release` (markdown mode, CLI layer only) downloads `.gitpr.release.md` on first run respecting `CURRENT_LANG` (EN + pt_br/pt_pt/es_es/fr_fr variants), never overwrites, never raises on network failure, and is skipped entirely in `--format json` (stdout-only contract).
- **R3 — skill as system instruction:** `_generate_summary()` now loads `get_skill_context("release")` as the system instruction, falling back to the built-in translated persona; `get_skill_context()` gained `quiet=` (mandatory so the "found and loaded" message never pollutes JSON stdout).
- **R5 — per-run artifact:** every markdown run saves `result.markdown` to `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` via `resolve_output_path` + the new `OUTPUT_FILE_NAME_RELEASE` config key; a save failure is a non-fatal yellow warning; a changelog upsert error still exits 1 **before** the artifact is written.
- **R6 — version confirmation prompt:** when the version comes from the automatic suggestion, the engine asks "❓ Use the suggested version {version}?" (default accept; declining opens a validated semver input loop). Silent in `--format json`/quiet and whenever stdin is not a TTY; prompt happens before the AI call. `--version` explicit and `auto_bump=false` keep the v1 behavior.
- **R8 — MCP:** `release` added to `SKILL_FILES` + new `skill://release` resource handler (i18n name/description) + matching static entry in `_build_tools_catalog()` (resources 16 → 17). No `gitpr.prompt.release.*` family.
- 6 new i18n keys translated in all 6 language files (pt_br, pt_pt, es_es, es, fr_fr, fr) — added by direct JSON edit; `tests/sync_i18n.py` was never run again (it truncates keys built with implicit string concatenation).
- Tests: extended `test_release_engine.py` (skill-as-system-instruction + prompt matrix), `test_skill_command.py` (`-s` includes release, EN and language variant; `ensure_release_skill_template` behaviors), new `test_skill_context.py` (action mapping, quiet), new `test_release_cli.py` (CliRunner: download hook, artifact, exit-1 ordering, JSON purity), extended `test_mcp_server.py` (resource + catalog).
- Smoke E2E in a temporary copy of the repo (never in the real one): first-run download attempt in pt_br ("Baixando .gitpr.release.md..."), graceful 404 handling, seeded-skill run with silent non-TTY version acceptance (v1.2.4), CHANGELOG.md at the repo root byte-identical to the artifact, duplicate version → exit 1 without artifact, `--format json` → pure parseable stdout touching nothing, `--force` regeneration → second timestamped artifact. `gitpr-mcp --list` now lists `skill://release` (17 resources).

## Changed files

| File | Change type | Description |
|------|-------------|-------------|
| templates/gitpr.release.md | feat | EN release skill template (persona + strict JSON contract + 6 rules) |
| templates/gitpr.release.pt_br.md | feat | PT-BR whole-file translation |
| templates/gitpr.release.pt_pt.md | feat | PT-PT whole-file translation (European forms) |
| templates/gitpr.release.es_es.md | feat | ES-ES whole-file translation |
| templates/gitpr.release.fr_fr.md | feat | FR-FR whole-file translation |
| src/core.py | feat | `release` in `get_skill_context` + `quiet=` param; `_OUTPUT_FOLDER_MAP` + `OUTPUT_FILE_NAME_RELEASE`; new `download_skill_file()` / `ensure_release_skill_template()`; `-s` registry includes `gitpr.release{lang_suffix}.md` |
| src/config.py | feat | `DEFAULT_CONFIG` + `OUTPUT_FILE_NAME_RELEASE` |
| src/release_engine.py | feat | `get_skill_context("release", quiet=)` as summary system instruction (fallback persona); `ask_version` param + `_stdin_is_interactive()` / `_ask_about_suggested_version()` helpers |
| src/main.py | feat | `release`: auto-download hook (markdown only), `ask_version=not json_mode`, per-run artifact under `.gitpr/reports/release/` (best-effort, exit-1 ordering preserved), docstring |
| src/mcp_server.py | feat | `SKILL_FILES["release"]`, `skill://release` resource handler, static catalog entry (resources 16 → 17) |
| langs/pt_br.json | feat | 6 new keys translated (prompt, artifact, warnings, MCP name/description) |
| langs/pt_pt.json | feat | idem (European Portuguese) |
| langs/es_es.json | feat | idem |
| langs/es.json | feat | idem (variant pair with es_es) |
| langs/fr_fr.json | feat | idem (French typography) |
| langs/fr.json | feat | idem (variant pair with fr_fr) |
| tests/test_release_engine.py | test | Skill-as-system-instruction (3) + ask-version prompt matrix (8) |
| tests/test_skill_command.py | test | `-s` includes release EN/variant; `ensure_release_skill_template` (5) |
| tests/test_skill_context.py | test | New: action mapping, fallbacks, quiet mode (6) |
| tests/test_release_cli.py | test | New: CLI wiring — download hook, artifact, exit-1 ordering, JSON purity |
| tests/test_mcp_server.py | test | `skill://release` in runtime list, resource content round-trip, catalog |
| CLAUDE.md | docs | Skill types + `release`; templates tree + 5 lines; auto-download note; MCP resources 16 → 17; env list + `OUTPUT_FILE_NAME_RELEASE` |
| docs/skill-template.md | docs | `.gitpr.release.md` rows + auto-download note |
| docs/survey/20260908_skill_release_template_surveyfacts.md | docs | Grill survey: context, R1–R8, facts report |
| docs/claude-code/reports/develop_natan/2026-09-08_skill_release_template.md | docs | This report |

## Impact

- **Functionality:** `gitpr release` gains a user-editable skill (downloaded automatically on first use, language-aware, never overwriting) that steers the AI executive summary; every local run now also persists a per-run artifact under `.gitpr/reports/release/`; automatic version suggestions are confirmed interactively (silent in JSON/non-TTY contexts); `-s` and the MCP server expose the new skill.
- **Performance:** one extra HTTP HEAD-equivalent GET only when `.gitpr.release.md` is missing (timeout 3s, non-fatal); no impact on cached AI calls (cache stays keyed on the prompt, the skill text feeds the system instruction).
- **Compatibility:** fully additive — no API breaks, no changes to existing skills, engines, or the `--format json` stdout contract (verified: still pure JSON, no file writes). `publish_draft_by_default`, `--publish`, `--draft`, `--force`, `--since`, `--version` unchanged. Python 3.10+ kept (no new dependencies).

## Test results

- Targeted files: all green (e.g. `test_release_engine.py` 27/27, `test_mcp_server.py` 85/85).
- Full suite: 781 passed, 2 skipped, 7 failed — **all 7 pre-existing**, none introduced by this task: 6 known locale/timeout failures plus `test_no_missing_keys` (40 "missing" keys). That last one is **pre-existing working-tree debt**: the release-v1 code (uncommitted in this tree, absent at HEAD a645def — verified via detached worktree where the test passes) references ~40 keys that the 6 `langs/*.json` files never received. The 6 keys added by this task ARE present and translated in all 6 files. Translating the 40 release-v1 keys is a separate i18n task, out of scope here.

## Next steps

- **Publish `templates/gitpr.release*.md` to the remote `main` branch before the feature ships** — until then the first-use auto-download returns 404 and degrades gracefully (verified in smoke); after the merge it downloads normally.
- Translate the 40 release-v1 keys (from the uncommitted feature code) into the 6 `langs/*.json` files so `test_no_missing_keys` goes green — via direct JSON edit, never `tests/sync_i18n.py`.
- Nothing was committed or pushed: all changes remain in the working tree for review.
