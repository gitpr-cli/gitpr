## Completion Report — Update repository URLs

### What was done
- Implemented a Python script to recursively walk the project directory and replace old GitHub repository URLs with the new https://github.com/gitpr-cli/gitpr.git.
- Executed the script from the project root, updating all occurrences in markdown, documentation, source code, language files, and other text files.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| CHANGELOG.md | feat | Updated repository URL links |
| README.md | feat | Replaced old URL with new URL |
| README.es_es.md | feat | Updated URL |
| README.fr_fr.md | feat | Updated URL |
| README.pt_br.md | feat | Updated URL |
| README.pt_pt.md | feat | Updated URL |
| build/lib/src/core.py | feat | Updated URL references |
| build/lib/src/main.py | feat | Updated URL references |
| docs/auto-update.md | feat | Updated URL |
| docs/auto-update.es_es.md | feat | Updated URL |
| docs/auto-update.fr_fr.md | feat | Updated URL |
| docs/auto-update.pt_br.md | feat | Updated URL |
| docs/auto-update.pt_pt.md | feat | Updated URL |
| docs/github-ci-linter.md | feat | Updated URL |
| docs/github-ci-linter.es_es.md | feat | Updated URL |
| docs/github-ci-linter.fr_fr.md | feat | Updated URL |
| docs/github-ci-linter.pt_br.md | feat | Updated URL |
| docs/github-ci-linter.pt_pt.md | feat | Updated URL |
| docs/map-reduce-diff.md | feat | Updated URL |
| docs/map-reduce-diff.es_es.md | feat | Updated URL |
| docs/map-reduce-diff.fr_fr.md | feat | Updated URL |
| docs/map-reduce-diff.pt_br.md | feat | Updated URL |
| docs/map-reduce-diff.pt_pt.md | feat | Updated URL |
| docs/skill-template.md | feat | Updated URL |
| docs/skill-template.es_es.md | feat | Updated URL |
| docs/skill-template.fr_fr.md | feat | Updated URL |
| docs/skill-template.pt_br.md | feat | Updated URL |
| docs/skill-template.pt_pt.md | feat | Updated URL |
| docs/smart-excludes.md | feat | Updated URL |
| docs/smart-excludes.es_es.md | feat | Updated URL |
| docs/smart-excludes.fr_fr.md | feat | Updated URL |
| docs/smart-excludes.pt_br.md | feat | Updated URL |
| docs/smart-excludes.pt_pt.md | feat | Updated URL |
| langs/es.json | feat | Updated URL |
| langs/es_es.json | feat | Updated URL |
| langs/fr.json | feat | Updated URL |
| langs/fr_fr.json | feat | Updated URL |
| langs/pt_br.json | feat | Updated URL |
| langs/pt_pt.json | feat | Updated URL |
| scripts/sync_all_langs.py | feat | Updated URL |
| src/main.py | feat | Updated URL |
| src/tui_issue.py | feat | Updated URL |
| src/ui/chat_app.py | feat | Updated URL |
| src/ui/help_screen.py | feat | Updated URL |

### Impact
- **Functionality:** All documentation, source files, and language resources now point to the correct repository URL (gitpr-cli/gitpr).
- **Performance:** No runtime impact; only static text changes.
- **Compatibility:** No breaking API changes. Existing code behavior unchanged.

### Next steps (if applicable)
- Verify that any external scripts or CI pipelines that reference the old URL are also updated.
- Optionally add a test that asserts the new URL is present in README.md.
