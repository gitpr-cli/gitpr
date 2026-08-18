---
name: status-report
description: >-
  Gera a próxima versão do relatório de status do projeto em docs/reports/.
  Detecta a última versão (relatorio_estado_vX.Y.Z.md), coleta implementações
  novas de docs/, descrições de PR geradas pelo GitPR (.gitpr/reports/pr_desc/),
  git log e relatórios de tarefas, e escreve o próximo relatório no formato
  consolidado. Use quando o usuário pedir para atualizar/gerar o relatório de
  status do projeto.
---

# Status Report Generator

Generates the next version of the project status report. The report file
itself must be written in **Portuguese (Brazil)**, matching every previous
report. Never overwrite an existing report — always create the new file.

## Sources of truth

| Source | What it provides |
|---|---|
| `docs/reports/relatorio_estado_v*.md` | Previous report: the base to evolve, and the "previous" column values |
| `.gitpr/reports/pr_desc/*_PR_DESC.*` | GitPR-generated PR descriptions (commit message, summary, technical changes) |
| `docs/*.md` (top level) | Newly documented features/topics |
| `git log` | Commits since the previous report |
| `docs/claude-code/reports/develop_natan/` and `docs/gemini/reports/` | Task reports since the previous report |
| `src/updater.py` | Current versions: `__version__`, `__lang_version__`, `__scripts_version__` |
| `langs/*.json`, `tests/test_*.py` | i18n key coverage and test-suite statistics |

## Step 1 — Determine the next report version

List `docs/reports/` and parse the version from each filename with the regex
`relatorio_estado_v(\d+)\.(\d+)\.(\d+)\.md`. Gotchas:

- The legacy first report is named `relatorio_estado_ GitPR-CLI.md` (space, no
  version). Treat it as **v0.0.1** — do not let it break the sort.
- Sort numerically, not lexically (v0.0.10 > v0.0.9).

The next report is the highest version with its last component incremented
(v0.0.10 → **v0.0.11**). The new file is
`docs/reports/relatorio_estado_vX.Y.Z.md`.

## Step 2 — Read the previous report

Read the latest report **completely**. It is the base document:

- Its footer date ("Relatório gerado em: YYYY-MM-DD") is the **cutoff** — only
  things after that date are "new".
- Its "Evolução desde o Relatório Anterior" table supplies the "anterior"
  column values for the new report.
- Its numbered module sections, test table, and doc-topic list are the
  baseline that the new report evolves (add, don't rebuild).

## Step 3 — Collect what is new since the cutoff

For each source, filter strictly by the cutoff date and list findings:

1. **PR descriptions** — `.gitpr/reports/pr_desc/`. Parse the timestamp from
   the filename: `{branch}_{YYYYMMDDHHMMSS}_PR_DESC.txt`. Keep files whose
   date is **after** the cutoff. **Ignore** anything that does not end in
   `_PR_DESC.txt` (e.g. `_issue-*.json.txt` is an issue draft, not a PR).
   Extract from each: the recommended commit message, the "Summary", and the
   "Technical Changes" bullets. Skip this source silently if the folder does
   not exist.
2. **Git log** — `git log --since="<cutoff date>" --oneline` for commit
   history, and `git log --since="<cutoff date>" --name-only` to see which
   files (docs, sources, tests, langs) were touched.
3. **New/updated docs** — top-level `docs/*.md` only (ignore
   `docs/reports/`, `docs/plans/`, `docs/claude-code/`, `docs/gemini/`,
   `docs/assets/`). Strip language suffixes (`.pt_br.md`, `.pt_pt.md`,
   `.es_es.md`, `.fr_fr.md`) to get the canonical topic name. A topic is
   **new** if it was not mentioned in the previous report and its file mtime
   or git history is after the cutoff; a topic is **updated** if only its
   files changed after the cutoff.
4. **Task reports** — `docs/claude-code/reports/develop_natan/` and
   `docs/gemini/reports/`: filenames start with `YYYY-MM-DD`, so keep those
   dated after the cutoff. They describe finished tasks not always visible in
   the diff.
5. **Versions** — read `__version__`, `__lang_version__`,
   `__scripts_version__` from `src/updater.py`.
6. **Test suite** — count files in `tests/test_*.py`; run
   `python -m pytest -q` if feasible and record the scenario count. If the
   run fails or is impractical, keep the previous report's numbers and note
   which files got new tests from the diff.
7. **i18n coverage** — count top-level keys in `langs/pt_br.json` (e.g. with
   a quick `python -c` one-liner reading the JSON).

Cross-reference sources: a PR_DESC, a commit, and a doc change often describe
the same feature — dedupe and mention them once.

## Step 4 — Write the next report

Copy the structure of the previous report exactly, updating its content:

1. **Title** — `# **🚀 Relatório de Status do Projeto: GitPR CLI — vX.Y.Z (YYYY-MM-DD)**` (today's date).
2. **📌 Visão Geral** — keep the overview paragraph; replace the "Novidades
   desta versão" bullets with the genuinely new items from Step 3 (bold
   feature name + one-line description, matching the existing style); update
   the metadata block (versões, idiomas, links) with Step 3.5 values.
3. **🏗️ Arquitetura e Bibliotecas Base** — update only what changed (test
   counts, MCP tool counts, new libraries).
4. **🧩 Módulos Implementados** — keep the numbered module sections; mark new
   bullets with 🆕; when a new major area landed (new module/flag/TUI), add a
   new numbered section or extend the closest existing one, same voice and
   bullet style.
5. **📊 Testes e Qualidade** — update the table (new test files, changed
   counts) and the totals line from Step 3.6.
6. **🌐 Internacionalização e Documentação** — list new and updated doc
   topics (Step 3.3), update the i18n key count (Step 3.7), update topic
   totals, memory-index and reports counts.
7. **🔄 Pipeline de Distribuição** — update only if it changed.
8. **📈 Evolução desde o Relatório Anterior** — comparison table: "anterior"
   column = previous report's values, "atual" = new values (version numbers,
   flag/tool counts, test counts, doc counts, commits/PRs since cutoff — the
   PRs come from `close #NN` lines in the PR_DESC files). Add rows for brand
   new areas.
9. **🚧 Próximos Passos** — carry over unfinished items from the previous
   report, drop the ones that were completed, append new suggestions that
   follow naturally from the new work.
10. **Footer** — `Relatório gerado em:` (today), `Branch:` (current git
    branch), `Autor:` Natan Fiuza (contato@natanfiuza.dev.br).

Keep the same length and level of detail as the previous report (~300 lines).
Write everything in PT-BR with the same emoji section headers.

## Step 5 — Verify

- The new file exists at `docs/reports/relatorio_estado_vX.Y.Z.md` (never
  overwrote an older one).
- Section list matches the previous report (no section lost, none invented).
- Every "new" claim is actually after the cutoff: cross-check the PR_DESC
  timestamps, git log dates, and doc dates one more time.
- Version numbers in the report match `src/updater.py`.
- No `_issue-*.json.txt` content leaked into the PR list.
