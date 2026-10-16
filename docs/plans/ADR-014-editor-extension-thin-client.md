# ADR-014 — Editor extension as an MCP thin client

**Status:** Accepted (2026-10-16)
**Spec:** `docs/plans/20261015_skill_gitpr_editor_extension_spec.md`

## Context

The spec assumes 12 MCP tools named `review_diff`, `run_check`, `create_pull_request`, `generate_pr_explanation` and `generate_mentor_explanation`, a `.gitpr/config.yml` passed through `GITPR_CONFIG`, a separate Cursor package, and review findings rendered as diagnostics. The server actually exposes 17 tools, none of those five; configuration is `~/.gitpr/.env` with Fernet-encrypted keys; Cursor installs the same VSIX; and `review_code` returns free Markdown with no file/line.

## Decisions

1. **VS Code + Cursor only, one VSIX** in `extensions/vscode/`. JetBrains is a separate later plan, once the MCP contract is stable.
2. **Missing capabilities become new MCP tools**, thin wrappers over existing use cases: `run_check` and `publish_pull_request`, plus opt-in `explain` on `generate_pr_description` and `mentor` on `review_code` / `full_review` (default `false`). Existing tools keep their signatures and outputs. The extension never shells out to the CLI.
3. **No parallel configuration.** No `config.yml`, no `GITPR_CONFIG`. Extension settings are only `gitpr.mcpCommand` (default `gitpr-mcp`), `gitpr.mcpArgs` and `gitpr.provider`. Secrets stay in `~/.gitpr/.env`; the extension never asks for or stores a key.
4. **Commit draft goes to the Source Control input box**; clipboard notification as fallback. The extension never commits.
5. **One lazy, persistent server session per workspace folder**, auto-reconnecting.
6. **Diagnostics come only from `run_check`.** Reviews and PR descriptions open as Markdown previews; the review template is not changed (cache and CLI untouched).
7. **TypeScript tests live in the extension package** (`@vscode/test-electron` + mocha); new server tools get pytest coverage in `tests/test_mcp_server.py`. The Python build gains no Node dependency.
8. **Publishing is two-step and never blind.** `Generate PR` opens an editable PR draft; `Publish PR` confirms in a modal and sends the edited text. `publish_pull_request` never commits or pushes; it answers `success` / `needs_push` / `already_exists` / `auth_required` / `error`. Updating an existing PR is out of v1.
9. **One publish use case.** The core of `_publish_pr_directly` moves to `src/application/use_cases/publish_pull_request.py` returning a structured result; `--no-edit` and the MCP tool both call it, and `--no-edit` keeps its messages.
10. **Contract check by tool names.** On connect the extension calls `listTools` and refuses with an upgrade hint if a required tool is missing. No `get_server_info` tool; `serverInfo.version` reports the SDK, not gitpr. The extension versions independently (`0.1.0`).
11. **`mentor` / `explain` are parameter-only in MCP.** The server does not OR them with the `.env` defaults, so existing MCP outputs never change. Commands: Commit, Review, Full Review, Review (Mentor), Generate PR, Generate PR (Explain), Publish PR, Check; status bar shows Commit, Review, PR, Check.
12. **`run_check` always returns the JSON envelope.** Extension setting `gitpr.check.useAI` defaults to `false`; `fail_on` and base come from `GITPR_CHECK_*`. Each run replaces the previous check diagnostics.
13. **Extension UI in en, pt-br, es, fr** (`package.nls.*`, `vscode.l10n`). VS Code has no pt-PT; pt-PT users get pt-br. Server messages arrive already localized by `GITPR_LANG`.
14. **Packaging, not publishing.** `npm run package` builds the VSIX; `.github/workflows/extension.yml` tests on PRs touching `extensions/**` and publishes to the VS Code Marketplace and Open VSX on `ext-v*` tags (`VSCE_PAT`, `OVSX_PAT`). Publisher `natanfiuza`, name `gitpr`.
15. **Defense-in-depth secret masking.** Server tools pass error/result text through `mask_sensitive_text`; the extension also masks common token patterns (`ghp_*`, `glpat-*`, `sk-*`, `AIza*`, `Bearer *`) before writing to the OutputChannel or notifications.
16. **Local ledger telemetry on the server only.** `run_check` and `publish_pull_request` record `mcp:check` and `mcp:publish_pr` in `~/.gitpr/metrics/telemetry.db` via `log_local_metric`; the extension emits zero telemetry and opens no network sockets.
17. **5-language documentation parity.** `docs/editor-extension*.md` and `README*.md` in all 5 locales (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`), plus `langs/*.json` entries for any new server i18n strings. No new `.env` keys, so `config_schema.py` is unchanged.

## Consequences

- Business logic stays in one place; every editor (and every MCP agent) gets the new tools.
- The server grows by two tools and two optional parameters — additive, no break for existing MCP clients.
- Review findings cannot be clicked to a line until the review output becomes structured — a separate decision.
