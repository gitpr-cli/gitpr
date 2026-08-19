# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat(mcp): add --list/--tool flags, guard stdout early, enrich config
```

---

## 🎯 Summary

Enable CLI discovery and direct invocation of MCP tools without an MCP host: `--list` prints the full tools catalog as JSON, `--tool <name>` runs a single tool and returns its result. Additionally, fix a protocol-corruption bug by applying stdout redirection before any module imports, and enrich editor config files with tool metadata and human-readable descriptions for seamless IDE integration.

## 🛠️ Technical Changes

- **New CLI flags** (`--list`, `--tool`, `--tool-args`) – `gitpr-mcp --list` outputs all tools, resources, and prompts; `--tool get_git_context` invokes a specific tool from the command line, with parameter support via `--tool-args`.
- **Tools catalog** – `_build_tools_catalog()` and `_get_compact_tools()` provide structured metadata for all 12 tools, 16 resources, and 7 prompts, enabling both JSON export and lightweight embedding.
- **Early stdout guard** – `sys.stdout` is replaced with `_MCPStdout()` at module level, before any `src.*` imports, preventing accidental writes (e.g., from `load_dotenv()`) from corrupting the MCP transport.
- **Config enrichment** – `_install_for_editor()` now includes a `description` field and a `_tools` array (name + description) for each gitpr server entry, giving editors and AI agents a local inventory of available capabilities.
- **UI improvement** – `_fmt_status()` helper in the PR publish app adds emoji and translated labels (New/Modified/Deleted) to file staging lists.
- **Code cleanup** – `core.py` uses `splitlines()` and `.strip()` for safer string handling.
- **Tests** – 7 new test classes covering tool catalog, registry, CLI arguments, output patching, and install enrichment; existing tests updated for the new `files` array in `list_unstaged_files`.

## ⚠️ Impact/Warnings

- **Backward compatible** – `gitpr-mcp` without flags still starts the stdio server as before.
- **Internal stdout fix** – the early redirection is transparent and does not affect normal behavior; it resolves a latent issue where module-level imports could emit unwanted bytes on stdout.
- **Config changes** – editor configs now carry extra metadata; existing installations are not broken.
- **New metrics files** – `.gitpr/metrics/export/gitpr_metrics_2026-08-11.{csv,json}` added; verify whether these generated artifacts should be versioned.

close #106