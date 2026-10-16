## Completion Report — Editor Extension (VS Code & Cursor) & MCP Server Integration

### What was done
- Recorded the domain model and resolved all 17 architectural questions in `docs/plans/glossary-editor-extension.md` and `docs/plans/ADR-014-editor-extension-thin-client.md` (marked **Accepted**).
- Extracted the shared Pull Request publication use case into `src/application/use_cases/publish_pull_request.py` (`publish_pull_request_use_case`, `PublishPrOutcome`, `format_recommended_commit_body`) so both the CLI (`--no-edit`) and the MCP server (`publish_pull_request`) execute the exact same branch, remote push, token, and multi-forge (`GitHub`, `GitLab`, `Bitbucket`, `Azure DevOps`) workflow.
- Refactored `_publish_pr_directly` in `src/main.py` to delegate to `publish_pull_request_use_case`.
- Extended `src/mcp_server.py` with two new MCP tools (`run_check` and `publish_pull_request`) and added optional `mentor: bool = False` on `review_code` / `full_review` and `explain: bool = False` on `generate_pr_description` (purely parameter-driven, never OR'd with `.env` defaults), updating `_build_tools_catalog()` (now 18 tools) and `_TOOL_FUNCS`.
- Updated `tests/test_mcp_server.py` (16 → 18 tools) and added `TestEditorExtensionMcpTools` covering `run_check`, `publish_pull_request`, `mentor`, and `explain` (all 115 tests in `tests/test_mcp_server.py` passing).
- Implemented the official VS Code & Cursor thin-client extension in `extensions/vscode/`:
  - `src/mcp_client.ts` — Lazy, persistent newline-delimited JSON-RPC 2.0 client over `stdio` (`cwd` = workspace folder root) with automatic reconnect, `tools/list` contract verification (`REQUIRED_MCP_TOOLS`), and custom `McpClientError` codes (`MCP_SPAWN_FAILED`, `MCP_CONTRACT_MISMATCH`, `MCP_TOOL_ERROR`).
  - `src/session_manager.ts` — Multi-root workspace session manager (`Map<string, McpClient>`), active folder resolution, and shared `GitPR` output channel logging.
  - `src/draft_and_diagnostics.ts` — Pure helper functions (`formatPrDraftDocument`, `parsePrDraftDocument`, `normalizeCheckFindings`) testable outside the VS Code host.
  - `src/masking.ts` — Client-side defense-in-depth secret masking mirroring `src/infrastructure/ci/masking.py`.
  - `src/commands/commit.ts` — Populates the native `vscode.git` Source Control input box (with clipboard fallback) and never commits automatically.
  - `src/commands/review.ts` — Runs `review_code` (standard or `mentor: true`) and `full_review`, opening rendered Markdown previews side-by-side.
  - `src/commands/publish_pr.ts` — Two-step PR workflow: `gitpr.generatePrDraft` opens an editable Markdown tab (`line 1` = title, rest = body) and `gitpr.publishPr` asks for modal confirmation and handles `success`, `needs_push`, `already_exists`, `auth_required`, and `error`.
  - `src/commands/check.ts` — Calls `run_check` (`no_ia = !gitpr.check.useAI`) and maps normalized findings to a `vscode.DiagnosticCollection("gitpr")` in the `Problems` panel.
  - `src/ui/status_bar.ts` — Displays live state (`$(git-pull-request) GitPR`, `$(sync~spin)`, `$(check)`, `$(warning)`, `$(error)`) and quick-pick action menu.
  - Localization bundles (`package.nls*.json` and `l10n/bundle.l10n*.json`) for EN, PT-BR, ES, and FR.
  - Mocha integration test suite (`src/test/mcp_client.test.ts`) spawning the real Python `src.mcp_server` over `stdio` (all 7 tests passing) and VSIX packaging (`gitpr-0.1.0.vsix`).
- Created `.github/workflows/extension.yml` for automated build, test, VSIX artifact upload, and dual publishing to VS Code Marketplace and Open VSX Registry on `ext-v*` tags.
- Created documentation in all 5 languages (`docs/editor-extension*.md`) and updated `README*.md`, `langs/*.json`, and `.gitignore`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/plans/glossary-editor-extension.md` | docs | Domain glossary for the Editor Extension bounded context |
| `docs/plans/ADR-014-editor-extension-thin-client.md` | docs | Architecture Decision Record (Accepted) with all 17 resolved design decisions |
| `src/application/use_cases/publish_pull_request.py` | feat | Shared PR publication use case (`publish_pull_request_use_case`) for CLI and MCP |
| `src/main.py` | refactor | Delegate `_publish_pr_directly` (`--no-edit`) to `publish_pull_request_use_case` |
| `src/mcp_server.py` | feat | Add `run_check`, `publish_pull_request`, `mentor`, and `explain` MCP support |
| `tests/test_mcp_server.py` | test | Update tool counts (18) and add `TestEditorExtensionMcpTools` |
| `extensions/vscode/package.json` | feat | VS Code / Cursor extension manifest, commands, menus, keybindings, settings |
| `extensions/vscode/tsconfig.json` | feat | TypeScript compiler configuration |
| `extensions/vscode/.vscodeignore` | feat | VSIX packaging exclusion rules |
| `extensions/vscode/README.md` | docs | Marketplace README for the VSIX package |
| `extensions/vscode/package.nls*.json` | feat | Manifest localization files (EN, PT-BR, ES, FR) |
| `extensions/vscode/l10n/bundle.l10n*.json` | feat | Runtime l10n bundles (EN, PT-BR, ES, FR) |
| `extensions/vscode/src/masking.ts` | feat | Client-side secret masking for output channel and notifications |
| `extensions/vscode/src/mcp_client.ts` | feat | Persistent stdio JSON-RPC 2.0 MCP client with contract verification |
| `extensions/vscode/src/draft_and_diagnostics.ts` | feat | PR draft parsing/formatting and check finding normalization |
| `extensions/vscode/src/session_manager.ts` | feat | Per-workspace-folder MCP session lifecycle manager |
| `extensions/vscode/src/ui/status_bar.ts` | feat | Status bar indicator and quick-pick menu |
| `extensions/vscode/src/commands/commit.ts` | feat | Commit message command populating `vscode.git` SCM input box |
| `extensions/vscode/src/commands/review.ts` | feat | Review, Full Review, and Mentor Review Markdown preview commands |
| `extensions/vscode/src/commands/publish_pr.ts` | feat | Two-step Generate PR Draft and Publish PR commands |
| `extensions/vscode/src/commands/check.ts` | feat | Quality Gate (`run_check`) command populating VS Code `Problems` |
| `extensions/vscode/src/extension.ts` | feat | Extension activation, command registration, and disposal |
| `extensions/vscode/src/test/mcp_client.test.ts` | test | Mocha unit and live stdio MCP integration tests |
| `.github/workflows/extension.yml` | feat | CI/CD workflow for building, testing, and publishing the VSIX |
| `docs/editor-extension*.md` | docs | Full technical guide in EN, PT-BR, PT-PT, ES-ES, and FR-FR |
| `README*.md` | docs | Added `run_check`, `publish_pull_request`, and Editor Extension links (5 languages) |
| `langs/*.json` | feat | Added i18n translations for new PR publication messages (4 languages) |
| `.gitignore` | chore | Ignored `extensions/vscode/node_modules/`, `out/`, and `*.vsix` |

### Impact
- **Functionality:** Developers using VS Code or Cursor can now run GitPR Commit, Review, Full Review, Mentor Review, two-step Pull Request drafting/publishing, and Check (`Problems` diagnostics) natively from the editor UI via a persistent `gitpr-mcp` stdio session.
- **Performance:** Lazy per-folder MCP process spawning avoids startup overhead when opening non-GitPR workspaces and reuses the warm Python server across commands. `gitpr.check.useAI` defaults to `false` for instant, zero-token static checks in the `Problems` panel.
- **Compatibility:** Fully backward-compatible with existing MCP clients (VS Code, Cursor, Claude Desktop, Antigravity) and CLI flags (`--no-edit`, `gitpr check`, `gitpr-mcp --tool`).

### Next steps (if applicable)
- When ready to publish the extension to the marketplaces, configure `VSCE_PAT` and `OVSX_PAT` repository secrets in GitHub Actions and push a tag matching `ext-v*` (e.g., `ext-v0.1.0`).
- JetBrains IDE support can be planned in a dedicated future specification once the VS Code / Cursor extension is battle-tested.
