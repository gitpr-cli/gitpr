---
name: tui-stdout-conflict-fix
description: Textual substitui sys.stdout e quebra click.secho() no Windows; wrapper _with_real_stdout() resolve
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-07_pr_publish_auto_commit.md
  date: 2026-08-07
  branch: develop_natan
---

Quando uma TUI do Textual está rodando, o framework substitui `sys.stdout` por um objeto `_PrintCapture`
que não possui um file descriptor válido no Windows. Qualquer chamada a `click.secho()` ou `click.echo()`
feita por código de backend (ex: `generate_pr_content()` → `get_skill_context()`) durante a execução
da TUI causa `OSError: [Errno 9] Bad file descriptor`.

O problema se manifestou em 2 níveis:
1. Chamada direta a `get_git_diff()` dentro da TUI (sem `quiet=True`) → primeiro crash.
2. `generate_pr_content()` → `get_skill_context()` também chama `click.secho()` internamente → segundo crash.

**Why:** Textual é dono do `sys.stdout` durante a TUI. O `click` escreve via `sys.stdout.write()` que o
`_PrintCapture` do Textual não consegue encaminhar corretamente no Windows (o objeto não tem fd real).
Isso é diferente do MCP server, onde usamos monkey-patching preventivo — na TUI o patching é temporário.

**How to apply:** Usar o wrapper `_with_real_stdout()` ao chamar funções de backend dentro de handlers de
TUI. O wrapper salva `sys.stdout` atual, restaura o `sys.__stdout__` real durante a chamada, e
re-restaura o `_PrintCapture` do Textual depois. Sempre que uma nova tela Textual precisar chamar
`generate_pr_content()`, `get_git_diff()`, ou qualquer função que use `click`, envolver com esse wrapper.

Ver também: [[mcp-server-isolation]]
