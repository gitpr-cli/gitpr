# Spec — MCP technical docs audit after silent CLI / timeout / DNS changes

> Task spec for the 2026-09-01 audit of `docs/mcp-annotations.md`, `docs/mcp-integration.md`, and `docs/mcp-prompts.md` against the behavior shipped in commit `681a7fa` ("fix: silence CLI tool output and bound DNS resolution").

## Objective

Verify whether the previous changes (silent `--tool` CLI mode, `GITPR_AI_TIMEOUT` 600→180s, DNS-bounded AI clients) invalidated any statement in the three MCP technical docs, correct what is stale, and produce the mandatory completion report plus this spec.

## Scope

**In scope**
- Read/audit: `docs/mcp-annotations.md`, `docs/mcp-integration.md`, `docs/mcp-prompts.md` (canonical English).
- Correction of stale claims found, mirrored across the 4 localized variants (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`) to preserve multilingual parity (convention: canonical English + suffix localizations).
- Repo-wide grep for `GITPR_AI_TIMEOUT`/`600` in `docs/` to catch other live references.
- Deliverables: completion report per CLAUDE.md rule + this task spec + the feature spec.

**Out of scope**
- Code, tests, or CLI behavior changes (documentation only).
- Historical reports/plans mentioning the old 600s default (e.g., `2026-08-18` reports) — records of the past, not edited.
- Pre-existing markdownlint style warnings (MD004/MD022/MD032/MD060) in untouched sections.
- Other docs (e.g., `providers-ia.md`, `ARCHITECTURE.md`) — only flagged as optional next steps.

## Audit Findings

| File | Verdict | Details |
|------|---------|---------|
| `docs/mcp-integration.md` | **Stale — fixed** | "Direct CLI Invocation" paragraph claimed diagnostics go to stderr in CLI mode; `--tool` is now silent (messages suppressed, stderr 0 bytes). "How It Works" (server mode → stderr) was correct and untouched. |
| `docs/mcp-integration.{pt_br,pt_pt,es_es,fr_fr}.md` | **Stale — fixed** | Same mirrored sentence in each language (confirmed by grep/read, line ~68-69). |
| `docs/mcp-annotations.md` | Correct | "Direct CLI Invocation" describes annotation semantics only; no output-behavior claims. |
| `docs/mcp-prompts.md` | Correct | "CLI Equivalents" maps prompts to tools; no output-behavior claims. |
| `docs/` grep `GITPR_AI_TIMEOUT`/`600` | Correct | Matches only in historical reports/plans (2026-08-18) — no live doc to fix. |

## Acceptance Criteria

1. The stale "diagnostics go to stderr" sentence is gone from the CLI invocation section in all 5 files; zero remaining matches of the old phrasing in CLI-mode context.
2. The corrected paragraph in each language states: `--tool` mode = JSON-only stdout, diagnostics suppressed, stderr empty; server mode = messages to stderr as usual.
3. Server-mode statements ("How It Works" section) remain byte-identical.
4. Completion report exists at `docs/claude-code/reports/develop_natan/2026-09-01_mcp_docs_audit_spec.md` following the CLAUDE.md template (What was done / Changed files / Impact / Next steps).
5. Both specs exist in `.scratch/`: `mcp-silent-cli/spec.md` (feature) and `mcp-docs-audit/spec.md` (this task), in English.
6. Nothing committed or pushed (CLAUDE.md rule — changes stay in the working tree).

## Test Cases

| Case | Input | Expected |
|------|-------|----------|
| Old phrase gone | `grep -i "diagnostic messages"` on the CLI section of the 5 files | 0 matches in CLI context |
| Server section intact | diff of "How It Works" lines before/after | No changes |
| Multilingual parity | Read corrected paragraphs in pt_br/pt_pt/es_es/fr_fr | Same semantics as EN, correct grammar per language |
| Deliverables present | File existence check | 5 edited docs + 1 report + 2 specs |

## Deliverables

- 5 corrected files: `docs/mcp-integration.md` + 4 variants
- `docs/claude-code/reports/develop_natan/2026-09-01_mcp_docs_audit_spec.md`
- `.scratch/mcp-silent-cli/spec.md`, `.scratch/mcp-docs-audit/spec.md`
