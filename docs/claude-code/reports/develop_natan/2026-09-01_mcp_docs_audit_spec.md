## Completion Report — MCP docs audit after silent CLI / timeout / DNS changes + specs

### What was done
- **Audited** the three MCP technical docs against the previous task's changes (commit `681a7fa` — silent `--tool` CLI mode, `GITPR_AI_TIMEOUT` 600→180s, DNS-bounded AI clients):
  - `docs/mcp-annotations.md` — **no changes needed**: its "Direct CLI Invocation" section describes annotation semantics, not output behavior.
  - `docs/mcp-prompts.md` — **no changes needed**: "CLI Equivalents" documents tool-to-prompt mapping only.
  - `docs/mcp-integration.md` — **one stale claim fixed**: the "Direct CLI Invocation" paragraph said *"all diagnostic messages (spinners, banners, logs) go to stderr"*, but in `--tool` mode the CLI is now silent — messages are suppressed entirely and stderr stays empty (0 bytes verified). The same mirrored sentence existed in all 4 localized variants, so the fix was applied in all 5 files to keep the multilingual convention's parity.
  - A repo-wide grep for `GITPR_AI_TIMEOUT`/`600` found only historical reports/plans (2026-08-18) — no other live doc needed changes.
- **Corrected** the CLI output paragraph in `docs/mcp-integration.md` and its `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr` variants: JSON is the only output in `--tool` mode (diagnostics suppressed, stderr empty), while server (MCP) mode keeps sending messages to stderr. The "How It Works" section (server mode → stderr) was confirmed correct and left untouched.
- **Generated the completion report** for the previous task's follow-up deliverables and **two specs** in `.scratch/` (EN, per user decision): the feature spec for the MCP fix and the task spec for this docs audit.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| docs/mcp-integration.md | fix | CLI output paragraph now describes silent `--tool` mode (JSON-only stdout, suppressed diagnostics) vs. server mode (stderr) |
| docs/mcp-integration.pt_br.md | fix | Mirrored correction (PT-BR) |
| docs/mcp-integration.pt_pt.md | fix | Mirrored correction (PT-PT) |
| docs/mcp-integration.es_es.md | fix | Mirrored correction (ES) |
| docs/mcp-integration.fr_fr.md | fix | Mirrored correction (FR) |
| .scratch/mcp-silent-cli/spec.md | feat | Feature spec — silent CLI mode, 180s AI timeout, DNS-bounded clients |
| .scratch/mcp-docs-audit/spec.md | feat | Task spec — docs audit scope, findings, and acceptance criteria |

### Impact
- **Functionality:** documentation-only change; no code, CLI behavior, or API surface touched.
- **Performance:** none.
- **Compatibility:** docs now match the shipped behavior of commit `681a7fa`; localized variants stay in parity with the canonical English file (multilingual convention).

### Next steps (if applicable)
- `docs/mcp-annotations.md` and `docs/mcp-prompts.md` needed no updates — no action required.
- Optional: consider documenting `GITPR_AI_TIMEOUT` (now 180s default) in a general configuration doc (e.g., `providers-ia.md`); not part of this task's scope.
