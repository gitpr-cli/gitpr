# Completion Report — implement-fixes skill

## What was done
- Created the `/implement-fixes` skill (`.claude/skills/implement-fixes/SKILL.md`)
  following the conventions of the existing `new-feature` and `status-report`
  skills (kebab-case name, PT-BR frontmatter description, English body)
- The skill implements the full pipeline: parse corrections (arguments, pasted
  text, IDE selection, or a reference to a report's "Próximos Passos") →
  plan with TodoWrite and ambiguity questions → surgical implementation with
  type-specific rules (i18n, docs, dead-code) → validate (linter, import
  check, i18n coverage, JSON validity) → test (reproduce-first for bugs,
  targeted file, full suite) → document (mandatory completion report) →
  commit only when explicitly requested

## Changed files
| File | Change type | Description |
|------|-------------|-------------|
| .claude/skills/implement-fixes/SKILL.md | feat | New skill: end-to-end correction workflow (fix, validate, test, document) |

## Impact
- **Functionality:** New user-invocable skill `/implement-fixes`; no changes
  to the GitPR CLI codebase itself
- **Performance:** None
- **Compatibility:** None — additive file only, picked up by the Claude Code
  skill discovery

## Next steps (if applicable)
- Use the skill on the pending items of `docs/reports/relatorio_estado_v0.0.11.md`
  (staging translations for pt_pt/es_es/fr_fr, `FileStageScreen` dead code,
  MCP docs adjustments) as the first real-world validation
- Rename the skill (folder + `name:` field) if a different command name is
  preferred
