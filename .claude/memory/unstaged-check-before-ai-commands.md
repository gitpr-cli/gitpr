---
name: unstaged-check-before-ai-commands
description: Verificação de arquivos unstaged antes de comandos de IA com escape hatch --no-unstaged-check
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-09_unstaged_files_check.md
  date: 2026-08-09
  branch: develop_natan
---

Todos os comandos que usam IA (`-c` commit, `-r` review, `-f` fullreview, `-is` issue,
e publish de PR) agora passam por uma verificação centralizada de arquivos unstaged
antes de executar. A função `check_unstaged_files()` em `src/main.py` é o gate único
— se houver arquivos não staged, exibe um resumo categorizado (new/modified/deleted)
com emojis e pergunta se o usuário quer continuar.

O flag `--no-unstaged-check` permite pular essa verificação por uma execução,
funcionando como escape hatch para cenários onde arquivos unstaged são intencionais.
O flag `--status` (sem IA) lista o estado do repositório com `get_uncommitted_summary()`,
que retorna `{"staged": [...], "unstaged": [...], "untracked": [...]}`.

No lado MCP, duas novas tools complementam: `list_unstaged_files` (JSON categorizado)
e `analyze_unstaged_diff` (diff apenas do working tree, sem staged). A função
`get_unstaged_categorized()` em `src/core.py` fornece a base para ambas,
normalizando códigos combinados do git porcelain (`AM`, `MM`, `MD`, `AD`) para
labels canônicas (`mod`/`del`).

**Why:** Antes dessa mudança, apenas o fluxo de PR verificava arquivos não commitados.
Os comandos `-c`, `-r`, `-f` e `-is` geravam resultados de IA sem alertar que
arquivos modificados não estavam incluídos no diff, levando a commits e reviews
incompletos. A centralização em um helper único evita inconsistências entre comandos.

**How to apply:**
1. Todo novo comando que usa `git diff` deve chamar `check_unstaged_files()` antes
2. Usar `get_uncommitted_summary()` para visão completa do estado do repositório
3. MCP tools que expõem estado do git devem seguir o padrão de 3 categorias
4. O escape hatch `--no-unstaged-check` deve ser respeitado em todos os comandos

Ver também: [[nothing-to-commit-detection]]
