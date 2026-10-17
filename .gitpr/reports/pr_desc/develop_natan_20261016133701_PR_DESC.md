# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat(vscode): add thin MCP client extension for GitPR workflows
```

---

## 🎯 Summary

Developers currently have to leave the editor and switch to a terminal to generate commit messages, run AI code reviews, draft Pull Requests, publish them and inspect linter/security diagnostics. This PR brings those GitPR workflows into VS Code and Cursor through a **thin MCP client extension**, so the editor only orchestrates calls to the existing `gitpr-cli` MCP server and never duplicates business logic.

To support the extension, two MCP tools (`run_check`, `publish_pull_request`) and two optional parameters (`mentor`, `explain`) were added to the Python server, plus a new shared use case so the CLI `--no-edit` flow and the MCP tool publish Pull Requests through the same code path.

## 🛠️ Technical Changes

- Add `extensions/vscode` extension (TypeScript) with 8 commands: `gitpr.commit`, `gitpr.review`, `gitpr.fullReview`, `gitpr.reviewMentor`, `gitpr.generatePr`, `gitpr.generatePrExplain`, `gitpr.publishPr`, `gitpr.check`.
- Implement `GitPrMcpClient` over stdio (`@modelcontextprotocol/sdk`) with contract verification against the 7 required MCP tools, automatic reconnect, and a `MissingMcpToolsError` that instructs users to run `pip install --upgrade gitpr-cli`.
- Add `SessionManager` with per-workspace-folder sessions, multi-root folder resolution, provider/`check.useAI` settings, and terminal-based recovery actions (`gitpr`, `gitpr --install`).
- Add defense-in-depth secret masking (`masking.ts`) mirroring `src/infrastructure/ci/masking.py`, applied to notifications, OutputChannel logs and tool payloads.
- Map `run_check` findings into the Problems panel via a `DiagnosticCollection`, filtering `ignored`/`resolved` baseline entries and converting 1-based lines to 0-based ranges.
- Add PR draft workflow: format/parse Markdown drafts, publish from the active draft (publish or publish-as-draft) and handle `success`, `already_exists`, `needs_push`, `auth_required` and `error` outcomes with contextual actions (`Open in Browser`, `Push & Publish`, `Open Terminal`).
- Add status bar items (connection state, Commit, Review, PR, Check) and a GitPR OutputChannel.
- Add l10n bundles (`bundle.l10n*.json`, `package.nls*.json`) for `en`, `es`, `fr`, `pt-br` and new error strings in `langs/*.json`.
- Add new use case `src/application/use_cases/publish_pull_request.py` with structured `PublishPrOutcome`, remote-state checks (token presence, unpushed branch, existing open PR) and forge-error mapping with masked messages.
- Refactor `src/main.py::_publish_pr_directly` to reuse `publish_pull_request_use_case` and `format_recommended_commit_body` instead of inline SCM calls.
- Add MCP tools `run_check` (read-only JSON check envelope, `no_ia` default true) and `publish_pull_request` (never commits or pushes) with catalog entries, annotations and local metrics (`mcp:check`, `mcp:publish_pr`).
- Add `mentor` to `review_code`/`full_review` and `explain` to `generate_pr_description`, appending the Junior Mentor and Reviewer Guide sections only when requested.
- Add unit tests for the registry/catalog (16 → 18 tools) and for the new tools and parameters, plus extension tests covering the MCP contract, masking, draft round-trip and diagnostics normalization.
- Add GitHub Actions workflow `.github/workflows/extension.yml` to build, test and package the VSIX on PRs and publish to the VS Code Marketplace and Open VSX on `ext-v*` tags; update `.gitignore` for `node_modules/`, `out/` and `*.vsix`.

## ⚠️ Impact/Warnings

- **Dependencies:** the extension requires Node.js 20+ and `@modelcontextprotocol/sdk`; CI uses Python 3.11 and `npm install`/`vsce package --no-dependencies`.
- **Environment variables / secrets:** publishing requires the repository secrets `VSCE_PAT` (VS Code Marketplace) and `OVSX_PAT` (Open VSX). Each publish step is skipped when its secret is empty. No database, migration or schema changes.
- **Compatibility:** the extension hard-fails with an explicit upgrade message when the installed `gitpr-cli` does not expose the 7 required MCP tools, so older CLI versions must be upgraded.
- **Behavior change:** the `mentor` and `explain` parameters add extra AI calls (token/latency cost) and are opt-in; `run_check` defaults to `no_ia=true` to keep editor checks fast.
- **Security:** secret masking is a defense-in-depth layer only; token handling remains on the CLI side and the extension only opens a terminal for authentication.
- **New tool contract:** MCP clients must handle the new `run_check` and `publish_pull_request` tools and their structured statuses (`success`, `needs_push`, `already_exists`, `auth_required`, `error`).

close #211

---

[![GitPR](https://img.shields.io/badge/GitPR-9_errors_%C2%B7_0_warnings-red)](https://gitpr.natanfiuza.dev.br/)