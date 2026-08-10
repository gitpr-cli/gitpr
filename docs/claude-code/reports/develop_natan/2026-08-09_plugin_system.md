## Completion Report — Global Plugin System (Linter + Prompts)

### What was done
- Implemented a complete global plugin system allowing users to extend GitPR with custom linter rules and AI prompts that apply across all projects on their machine.
- Added infrastructure for plugin discovery (`get_linter_plugins()`, `get_prompt_plugins()`, `get_plugin_dir()`) in `src/config.py`.
- Plugin directories (`~/.gitpr/plugins/linter/`, `~/.gitpr/plugins/prompts/`) are auto-created on first run via `setup_environment()`.
- Refactored `load_linter_rules()` to merge local project rules with global plugin rules, with resilient error handling (malformed YAML shows yellow warning, flow continues).
- Extended MCP server to dynamically register plugin prompts as MCP resources and prompts using factory functions (closure pattern avoids late-binding bugs).
- Updated `list_prompts()` to include plugin URIs in the `prompt://plugin/<name>` namespace.
- Added `--plugins` CLI flag to list all active global plugins (linter packs and prompt templates).
- Created comprehensive unit tests (17 tests) covering discovery, rule merging, error resilience, and integration.
- Wrote full documentation in English and Portuguese (`docs/plugins-system.md`, `docs/plugins-system.pt_br.md`).
- Updated README files in all 5 languages (EN, PT-BR, PT-PT, ES, FR) with the new `--plugins` feature.
- Added 12 new translation strings to `langs/pt_br.json`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| [src/config.py](src/config.py) | feat | Added plugin directory creation in `setup_environment()`, 3 plugin discovery functions, refactored `load_linter_rules()` for local+global merge |
| [src/mcp_server.py](src/mcp_server.py) | feat | Updated `list_prompts()` for plugin URIs, added `_register_plugin_prompts()` with factory pattern for dynamic MCP registration |
| [src/main.py](src/main.py) | feat | Added `--plugins` flag, HELP_MAP/HELP_PRIORITY entries, handler block, banner update |
| [tests/test_plugins.py](tests/test_plugins.py) | feat | 17 unit tests covering discovery, merge, error resilience, and integration |
| [docs/plugins-system.md](docs/plugins-system.md) | docs | Complete English documentation with examples |
| [docs/plugins-system.pt_br.md](docs/plugins-system.pt_br.md) | docs | Complete Portuguese documentation with examples |
| [langs/pt_br.json](langs/pt_br.json) | i18n | 12 new translation strings + fixed missing closing `}` |
| [README.md](README.md) | docs | Added `--plugins` entry |
| [README.pt_br.md](README.pt_br.md) | docs | Added `--plugins` entry (PT-BR) |
| [README.pt_pt.md](README.pt_pt.md) | docs | Added `--plugins` entry (PT-PT) |
| [README.es_es.md](README.es_es.md) | docs | Added `--plugins` entry (ES) |
| [README.fr_fr.md](README.fr_fr.md) | docs | Added `--plugins` entry (FR) |

### Impact
- **Functionality:** Users can now create global linter rule packs in `~/.gitpr/plugins/linter/` that apply across all their projects (security checks, debug preventers, language-specific rules). Custom AI prompts in `~/.gitpr/plugins/prompts/` are auto-registered as MCP resources/prompts for use in VS Code, Cursor, and Claude Desktop. The `gitpr --plugins` command provides visibility into what's loaded.
- **Performance:** Plugin discovery is O(n) on directory listing — negligible overhead. MCP registration happens once at server startup.
- **Compatibility:** Fully backward-compatible. No existing APIs or behaviors changed. `load_linter_rules()` still returns the same list format; global plugins are additive only.

### Next steps
- Consider adding `--plugins --install <name>` subcommand to download curated plugin packs from GitHub (similar to `--skill`).
- Consider adding a plugin validation command (`--plugins --validate`) that checks syntax of all plugin files without running the full linter.
