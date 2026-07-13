## Completion Report — Move skill/config files to `.gitpr/skill/`

### What was done
- Introduced a canonical location for all skill/config files (`.gitpr.*.md`, `.gitpr.linter.yml`, legacy `.gitpr.md`): the project-local `.gitpr/skill/` folder.
- Added two shared helpers in `config.py`:
  - `get_skill_dir()` — returns `<cwd>/.gitpr/skill`.
  - `resolve_skill_path(filename)` — returns the path inside `.gitpr/skill/`, and **transparently migrates** a legacy root file into the folder (with a fallback to the root path if the move fails).
- Routed every skill-file resolver through `resolve_skill_path()`:
  - `core.py` → `get_skill_context()` (commit/pr/filereview/issue/review + legacy `.gitpr.md`)
  - `config.py` → `load_linter_rules()` (`.gitpr.linter.yml`)
  - `issue_engine.py` → `.gitpr.issue.md`
  - `blame_engine.py` → `.gitpr.blame.md`
- Updated `generate_skill_template()` (`--skill`) to create `.gitpr/skill/` and download templates directly into it, still skipping files that already exist (in the folder or migrated from root).
- Updated user-facing help/messages (`main.py`, `core.py`) to reference the new folder and added matching `pt_br.json` translations (including 2 new migration-warning strings).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/config.py | feat | Added `get_skill_dir()` + `resolve_skill_path()`; `load_linter_rules()` uses the helper; `import shutil` |
| src/core.py | refactor | `get_skill_context()` and `generate_skill_template()` use the helper; download into `.gitpr/skill/`; updated messages |
| src/issue_engine.py | refactor | `.gitpr.issue.md` resolved via helper |
| src/blame_engine.py | refactor | `.gitpr.blame.md` resolved via helper |
| src/main.py | docs | Updated `--skill` help texts to mention `.gitpr/skill/` |
| langs/pt_br.json | chore | Re-keyed/added translations for the new paths and migration messages |

### Impact
- **Functionality:** Skill files now live in `.gitpr/skill/`. Existing root files are auto-moved on first access (read or download) — no manual step for users. Downloads go straight into `.gitpr/skill/`.
- **Performance:** Negligible (one extra `os.path.exists` per resolve; a one-time `shutil.move` on migration).
- **Compatibility:** Backward-compatible. Legacy root files (including old `.gitpr.md`) are migrated automatically; if a move fails, the tool falls back to reading the root path.

### Next steps (if applicable)
- Consider adding `.gitpr/skill/` guidance to the docs (`docs/skill-template.md`) and its `pt_br` copy.
- Optionally mirror these translations in the other language files (`es`, `fr`, `pt_pt`) if/when they are added.
