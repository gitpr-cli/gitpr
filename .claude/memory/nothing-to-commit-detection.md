---
name: nothing-to-commit-detection
description: Detecção multilingue de "nothing to commit" no git commit — trata como sucesso, não erro
metadata:
  type: feedback
  source: docs/claude-code/reports/develop_natan/2026-08-09_correcoes_confirmacao_commit.md
  date: 2026-08-09
  branch: develop_natan
---

Quando `git commit` retorna código de saída não-zero mas a saída contém frases indicando que não há
alterações para commitar, o fluxo deve tratar como **sucesso** e prosseguir — não como erro. O Git
emite essas mensagens em inglês independente do locale da máquina, então a detecção cobre 6 padrões:

1. `"nothing to commit"` — caso mais comum
2. `"nothing added to commit"` — quando nada foi staged
3. `"no changes added to commit"` — variante
4. `"changes not staged"` — alterações existem mas não estão staged
5. `"working tree clean"` — repositório limpo
6. `"no changes"` — genérico

**Why:** No fluxo de auto-commit do `--no-edit` e do F3 da TUI de PR, se o commit falha como erro
o fluxo de publicação é interrompido desnecessariamente. O caso "nada para commitar" é comum quando
o usuário já fez commit manual antes de publicar o PR. Tratar como sucesso permite que o fluxo
continue direto para o push/publicação.

**How to apply:** A função `execute_git_commit()` em `core.py` já tem essa detecção. Se um novo
ponto de entrada precisar verificar saída de commit, usar `execute_git_commit()` em vez de chamar
`subprocess.run(['git', 'commit', ...])` diretamente. Se precisar adicionar novos padrões, manter
a busca case-insensitive e adicionar ao array de padrões.
