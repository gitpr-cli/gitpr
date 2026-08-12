# Implementation Plan — Run `/reports-to-memory` on GitPR (2026-08-11)

## 1. Objective

Execute the `reports-to-memory` skill against all reports in `docs/claude-code/reports/` and
`docs/gemini/reports/` on branch `develop_natan`, generating/updating atomic memories in
`.claude/memory/`, updating the `MEMORY.md` index, and syncing to the harness memory path.

## 2. Discovery — definitive results (ambiguity resolved)

Current state: 54 total reports (46 claude-code + 8 gemini), all under `develop_natan`.
Existing memories: 20 atomic + `MEMORY.md` index (generated 2026-08-09, commit `6210d97` at
2026-08-09 23:03, header reads "Baseado em 43 relatórios").

**How the 43 was determined:** 42 claude-code reports existed at the 08-09 23:03 run + 1 gemini
report (`fix_pylance_import_and_encoding`, which is the `source:` of the existing
`windows-utf8-encoding-fix` memory) = 43. Four reports were committed AFTER the last run.

### Reports to process this run (11 total)

**A. New claude-code reports (4)** — none referenced by any existing memory `source:`:

| # | Report | Committed |
|---|--------|-----------|
| A1 | `docs/claude-code/reports/develop_natan/2026-08-09_unstaged_files_check.md` | 08-10 00:38 |
| A2 | `docs/claude-code/reports/develop_natan/2026-08-10_smart_excludes_local_projeto.md` | 08-10 13:42 |
| A3 | `docs/claude-code/reports/develop_natan/2026-08-11_mcp_tool_cli_flag.md` | 08-11 16:30 |
| A4 | `docs/claude-code/reports/develop_natan/2026-08-11_merge_conflict_error_handling.md` | 08-11 19:31 |

**B. Gemini reports (7)** — committed 08-03/08-05, BEFORE the last run, but only
`fix_pylance_import_and_encoding` was processed then (it is the `source:` of the existing
`windows-utf8-encoding-fix` memory). The other 7 were silently skipped and are candidates now:

| # | Report | Notes |
|---|--------|-------|
| B1 | `docs/gemini/reports/develop_natan/2026-08-03_create_gemini_md.md` | Has durable fact (see matrix) |
| B2 | `docs/gemini/reports/develop_natan/2026-08-03_update_readme_installation.md` | Docs-only — expect skip |
| B3 | `docs/gemini/reports/develop_natan/2026-08-03_create_relatorio_estado_v0_0_6.md` | State snapshot; facts already covered by existing memories — expect skip |
| B4 | `docs/gemini/reports/develop_natan/2026-08-03_update_version_to_0_0_31.md` | Version bump — expect skip |
| B5 | `docs/gemini/reports/develop_natan/2026-08-03_translate_github_ci_linter_docs.md` | Convention fact (docs naming) |
| B6 | `docs/gemini/reports/develop_natan/2026-08-03_translate_guia_regex_gitpr.md` | Same convention as B5 — fold into one memory |
| B7 | `docs/gemini/reports/develop_natan/2026-08-03_translate_gitpr_issue_option_docs.md` | Same convention as B5 — fold into one memory |

**C. Already processed — DO NOT reprocess:**
- `docs/gemini/reports/develop_natan/2026-08-03_fix_pylance_import_and_encoding.md` — already
  processed (source of `windows-utf8-encoding-fix`). EXCEPTION: its pyright `[tool.pyright]`
  pyproject.toml fact is NOT covered by any memory — optional 1-fact extraction (see matrix C1).
- `docs/claude-code/reports/develop_natan/2026-08-09_aplicar_documentacao_pr-publish.md` — pure
  docs consolidation, was in the 43, no durable fact.
- `docs/claude-code/reports/develop_natan/2026-08-09_correcoes_confirmacao_commit.md` — already
  processed (source of `nothing-to-commit-detection`).

## 3. Per-report processing matrix

For each report: read fully, extract 1-3 durable facts (atomic, durable, non-obvious,
actionable). Expected outcomes below are guidance — the executor AI judgment governs.

| Report | Expected durable fact(s) | Memory slug (pt-BR content) | Type | Link to |
|--------|--------------------------|------------------------------|------|---------|
| A1 unstaged_files_check | All AI commands (commit/review/fullreview/issue/PR) gate on `check_unstaged_files()`; `--no-unstaged-check` escape hatch; `--status` = no-AI listing | `unstaged-check-before-ai-commands` | project | `[[nothing-to-commit-detection]]` |
| A2 smart_excludes_local_projeto | Local file `.gitpr/conf/gitpr.smart-excludes.json` merged (union+dedup) with global; idempotent auto-seed; env overrides `GITPR_SKIP_SMART_EXCLUDES` / `GITPR_SMART_EXCLUDES_GLOBAL` / `GITPR_SMART_EXCLUDES_LOCAL` | `smart-excludes-local-projeto` | project | `[[smart-excludes-remote-control]]` |
| A3 mcp_tool_cli_flag | `gitpr-mcp --tool <name> [--tool-args json]` invokes the 12 MCP tools without stdio server; registry pattern `_TOOL_FUNCS` + `_get_tool_registry()`; JSON on real stdout / diagnostics on stderr via `_write_real_stdout()` | `mcp-tool-cli-invocacao-direta` | project | `[[mcp-server-isolation]]` |
| A4 merge_conflict_error_handling | Merge failure must never silently proceed to browser prompt; HTTP 405 = conflicts must be resolved manually on GitHub; error modal with open-in-browser | `merge-conflict-error-handling` | feedback | — |
| A4 (2nd fact, optional) | Textual UI state updates only on main thread via `call_from_thread`; merge split into spawn/success/failure callbacks | `tui-main-thread-callbacks` | feedback | `[[merge-conflict-error-handling]]` |
| B1 create_gemini_md | `GEMINI.md` rulebook mandates a completion report at `docs/gemini/reports/{branch}/{date}_{task}.md` for every Gemini task; must stay in sync with CLAUDE.md | `gemini-reports-convention` | project | — |
| B5+B6+B7 translate_* | Docs convention: English is canonical base, localizations as `docs/<name>.<lang_code>.md` (pt_br/pt_pt/fr_fr/es_es), resolved by `get_doc_url()`; code blocks/env vars/endpoints stay in English | `docs-multilingue-convencao` (ONE memory, not three) | reference | — |
| C1 fix_pylance (optional) | `[tool.pyright]` with `executionEnvironments` root `.` fixes Pylance "Cannot find module src.i18n" | `pyright-config-project-root` | feedback | `[[windows-utf8-encoding-fix]]` |
| B2, B3, B4 | No durable fact — SKIP silently (B3 facts all already covered by `metrics-telemetry-architecture`, `ai-call-duration-tracking`, `github-token-reauth-flow`, `dashboard-repo-scope`) | — | — | — |

Expected output: 6-8 new memories. Maximum 3 facts per report.

## 4. Memory type classification rules

- **project**: architecture decision, established pattern, technical constraint, component/endpoint
  created (A1, A2, A3, B1).
- **feedback**: bug with root cause, approach that worked, lesson learned (A4, A4-2nd, C1).
- **reference**: generated documentation, external links/APIs, conventions about docs (B5/B6/B7).
- **user**: team preference, product decision (none expected this run).

## 5. Deduplication strategy

1. **Never duplicate**: before writing a memory, check the fact against the 21 existing memory
   files and the `source:` field of each (a report whose path appears in a `source:` was already
   processed).
2. **Extension, not duplicate**: A2 extends `smart-excludes-remote-control` but is a different
   mechanism (local file + env vars vs. remote template) — create a NEW atomic memory and
   cross-link with `[[smart-excludes-remote-control]]`; do NOT rewrite the existing one.
3. **Skip rules**: no durable fact → skip silently; fact already covered → skip or update the
   existing memory; fact visible in code/git → never create a memory for it.
4. **Link related memories** with `[[kebab-slug]]` in the body (link targets must exist or be
   created in the same run).

## 6. Memory file generation (Fase 3)

Create each file in `c:\Users\nataniel\projetos\python\gitpr\.claude\memory\` with EXACTLY this
frontmatter (mirrors `plugin-system-architecture.md`):

```markdown
---
name: <kebab-case-slug-curto>          # unique, <=64 chars
description: <uma linha — para recall>
metadata:
  type: project | feedback | reference | user
  source: <caminho-relativo-do-report>  # ex.: docs/claude-code/reports/develop_natan/2026-08-11_mcp_tool_cli_flag.md
  date: <YYYY-MM-DD>                    # date of the SOURCE report
  branch: develop_natan
---

<fato em pt-BR, 1-4 parágrafos, nomes reais de arquivos/funções>

**Why:** <contexto que levou ao fato>

**How to apply:** <como usar em decisões futuras>

Ver também: [[memoria-relacionada]]
```

Rules: content in pt-BR; kebab-case slugs; real file/function names; link related memories.

## 7. Index update (Fase 4)

Rewrite `c:\Users\nataniel\projetos\python\gitpr\.claude\memory\MEMORY.md`:

- Header: `> Gerado automaticamente por /reports-to-memory em 2026-08-11` and
  `> Baseado em 54 relatórios de 1 branch` (54 = 43 previous + 11 processed now).
- Keep all existing 20 entries (organized under `## Project`, `## Reference`, `## Feedback`;
  no `## User` section exists).
- Append new entries under the correct type section, format
  `- [Título](file.md) — descrição curta (develop_natan, YYYY-MM-DD)`.
- Maintain existing ordering (chronological by date within each section).

## 8. Harness sync (Fase 5)

Copy ALL files (21 existing + new memories + updated `MEMORY.md`) to:

`C:\Users\nataniel\.claude\projects\c--Users-nataniel-projetos-python-gitpr\memory\`

This is the verified harness path for this repo (currently 22 files, byte-identical to the
project folder — confirmed via `diff -rq`). Source of truth is the git-versioned
`.claude/memory/` in the project; the harness path is a machine-local copy. Sync by full copy
(cp of each file), not by rename.

## 9. Verification checklist

1. **Frontmatter**: every new file has valid frontmatter — `name` unique/kebab-case/<=64 chars,
   `type` in enum, `source` is a real relative report path that exists, `date` matches the
   report date, `branch: develop_natan`.
2. **Dedup**: no new memory duplicates a fact of the 21 existing files; every `[[link]]` in new
   memories resolves to an existing or co-created file.
3. **Coverage**: the 11 processed reports are each either (a) the `source:` of a new memory, or
   (b) explicitly listed as skipped in the final report (B2/B3/B4 + folded B6/B7).
4. **Index**: `MEMORY.md` says 54 relatórios / 1 branch, dated 2026-08-11, all entries present.
5. **Mirror**: `diff -rq` between project `.claude/memory/` and harness path returns no
   differences.
6. **Optional git step**: `git add .claude/memory/` and commit (skill suggested team flow)
   — only if the user requests a commit.

## 10. Final report (Fase 6)

Summarize: reports processed (11), facts extracted, new memories created (with links),
memories updated (0 expected), memories ignored/duplicated, and the skip list with reasons.

## 11. Execution sequence

1. Fase 1 discovery — already completed (this document); re-verify with a fresh listing.
2. Fase 2 — process A1, A2, A3, A4 (read + extract), then B1-B7 (read + extract; B5/B6/B7 fold
   into one convention fact; B2/B3/B4 expected skips).
3. Fase 3 — write memory files to `.claude/memory/`.
4. Fase 4 — rewrite `MEMORY.md` (54 reports).
5. Fase 5 — sync to harness path.
6. Fase 6 — run verification checklist, then output the summary report.

## 12. Key paths

- Reports (claude-code): `c:\Users\nataniel\projetos\python\gitpr\docs\claude-code\reports\develop_natan\`
- Reports (gemini): `c:\Users\nataniel\projetos\python\gitpr\docs\gemini\reports\develop_natan\`
- Memory (source of truth): `c:\Users\nataniel\projetos\python\gitpr\.claude\memory\`
- Memory (harness mirror): `C:\Users\nataniel\.claude\projects\c--Users-nataniel-projetos-python-gitpr\memory\`
- Skill definition: `C:\Users\nataniel\.claude\skills\reports-to-memory\SKILL.md`

## 13. Risks / notes

- **Count mismatch risk**: if the executor recounts reports and finds more/less than 54, trust
  the memory `source:` fields and git add-dates over any stated count; the header count must
  equal the number of distinct reports that existed at run time.
- **B3 temptation**: `relatorio_estado_v0.0.6` summarizes many facts — all are already covered
  by existing memories; resist creating a duplicate "state report" memory (becomes obsolete).
- **pt-BR discipline**: memory bodies and index descriptions in Portuguese (team language),
  even though this plan is in English.
- **Do not touch code**: this run only creates/updates `.claude/memory/` files and the harness
  mirror; no source code changes.
