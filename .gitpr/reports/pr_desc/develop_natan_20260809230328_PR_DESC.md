# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add plugin system for linters and prompts
```

---

## 🎯 Summary

Introduces a global plugin system that allows users to extend GitPR with custom linter rules and AI prompts without modifying the core code. This enables teams to share security checks, coding standards, and reusable AI prompts across multiple projects.

## 🛠️ Technical Changes

- **Plugin Directory Structure**: Creates `plugins/linter` and `plugins/prompts` under `~/.gitpr/` during setup.
- **Linter Rule Merging** (`config.py`): `load_linter_rules()` now collects rules from both the project’s local `.gitpr.linter.yml` and all `*.yml`/`*.yaml` files in the global linter plugins directory. Malformed global plugins are gracefully skipped with a warning.
- **Prompt Plugin Discovery** (`config.py`): Adds `get_prompt_plugins()` to list `*.md` files in the global prompts directory.
- **New CLI Flag** (`main.py`): `--plugins` flag displays all active global linter packs and custom prompts, along with the plugin directory location.
- **MCP Integration** (`mcp_server.py`): Dynamically registers each plugin prompt as both an MCP resource (`prompt://plugin/{name}`) and a named prompt, making them available to AI assistants.
- **Full Test Coverage** (`tests/test_plugins.py`): Validates plugin discovery, rule merging, error handling, and directory creation.

## ⚠️ Impact/Warnings

- **No breaking changes** – existing behavior for project-local linters remains identical.
- **New directories** `~/.gitpr/plugins/linter` and `~/.gitpr/plugins/prompts` are created automatically.
- **Users can add global plugins** by placing `.yml` files (rules) or `.md` files (prompts) in the respective directories.
- **Plugin errors are suppressed** to avoid disrupting the main workflow; syntax issues are logged as warnings.
- **`--plugins` flag** is now available to verify what is installed globally.

close #97