---
name: implement-fixes
description: >-
  Workflow para implementar correções pendentes no GitPR CLI. O usuário ativa
  a skill e envia as correções (coladas, por argumento ou referenciando um
  relatório/trecho) e a skill se encarrega de corrigir, validar, testar e
  documentar cada uma. Use quando o usuário pedir para corrigir itens
  pendentes, resolver os "Próximos Passos" de um relatório, ou aplicar uma
  lista de correções.
---

# Fix Implementation Workflow

This skill implements a list of corrections end-to-end: parse each one,
implement it, validate, test, and document. Corrections arrive from the user
as skill arguments, pasted text, an IDE selection, or a reference to a report
section (e.g. the "Próximos Passos" of `docs/reports/relatorio_estado_vX.Y.Z.md`).

## Step 1 — Collect and parse the corrections

Corrections may arrive as:

- **Skill arguments** (`/implement-fixes <text>`), **pasted text**, or an
  **IDE selection** — parse the text into individual items.
- **A reference** such as "fix the Próximos Passos of
  relatorio_estado_v0.0.11.md" or "fix the next steps of the last report" —
  read the referenced report and extract its pending items.
- If the user sends no corrections, ask them for the list. Do not invent
  fixes on your own.

For each item, record: the description, the likely target files, and its
type: `code`, `i18n`, `docs`, `tests`, `dead-code`, or `config`.

## Step 2 — Plan before coding

1. Read context first: the relevant source files, and
   `docs/claude-code/reports/{branch}/` for task reports related to the area
   being fixed (continuity across sessions).
2. Create a `TodoWrite` list — one todo per correction, plus a final
   "write completion report" todo. Work one correction at a time.
3. **Ambiguity rule:** if a correction has multiple valid interpretations or
   its target is unclear, stop and present the options with
   `AskUserQuestion` — never silently pick one (CLAUDE.md: Think Before
   Coding).

## Step 3 — Implement surgically

One logical change per correction; touch only what is needed; match the
existing style. CLAUDE.md style rules apply: English identifiers, comments
and docstrings; `errors='replace'` on every `open()`/`subprocess`; `__()`
for all user-facing text.

Type-specific rules:

- **i18n:** new or changed `__()` keys go into all four language files —
  `langs/pt_br.json`, `langs/pt_pt.json`, `langs/es_es.json`,
  `langs/fr_fr.json`. Keys are the exact English string; keep the JSON valid;
  follow the existing terminology of each language.
- **docs:** the English file is canonical; mirror changes into the four
  translations (`docs/<name>.pt_br.md`, `.pt_pt.md`, `.es_es.md`,
  `.fr_fr.md`).
- **dead-code:** before removing a class/function, grep the whole repo for
  references (source, tests, TUI screens, MCP prompts) and delete the
  imports/registrations that pointed to it.
- **docs-only corrections** still require the final completion report.

## Step 4 — Validate

Run after each correction (or per logical group):

1. Static linter: `pipenv run python run.py -l`, or the gitpr MCP
   `run_linter` tool (checks the current diff against the YAML rules; no AI)
2. Import check:
   `pipenv run python -c "from src.main import cli; print('CLI OK')"`
3. i18n coverage: every `__("...")` key added or changed exists in all four
   language files — grep for the keys
4. JSON validity of every touched language file:
   `python -c "import json; json.load(open('langs/pt_br.json', encoding='utf-8'))"`

## Step 5 — Test

1. **Bug fixes:** write a test that reproduces the bug first, watch it fail,
   then apply the fix and watch it pass (CLAUDE.md: Goal-Oriented Execution).
2. Run the affected test file: `pipenv run python -m pytest tests/test_X.py -v`
3. Run the full suite: `pipenv run pytest tests/ -v`
4. If a test fails: fix and rerun until green. Report failures honestly —
   never claim the suite is green when a test failed.

## Step 6 — Document (mandatory)

1. Write the completion report at
   `docs/claude-code/reports/{branch}/{YYYY-MM-DD}_{taskname}.md` using the
   exact CLAUDE.md format (What was done / Changed files table / Impact /
   Next steps). `{taskname}` uses only lowercase letters, numbers and
   underscores. Create the folder if it does not exist.
2. If the corrections came from a status report's "Próximos Passos", list in
   the report's "Next steps" which items this session resolved — the
   status-report skill uses that to drop completed items.
3. If a correction changes user-facing behavior or documentation, the doc
   updates are part of the correction itself, not an afterthought.

## Step 7 — Commit (only when requested)

Do not commit unless the user explicitly asked. When committing:

- Atomic commits — one logical correction per commit (or a coherent group)
- Conventional Commits, English, imperative, no trailing period
- NEVER amend pushed commits; NEVER skip hooks
- `Co-Authored-By: Claude <noreply@anthropic.com>` trailer

## Done criteria

- [ ] Every correction implemented and verified with the Step 4 checks
- [ ] Full test suite green (or failures honestly reported)
- [ ] Completion report exists at
      `docs/claude-code/reports/{branch}/{date}_{taskname}.md`
- [ ] No accidentally staged files beyond the intended changes
