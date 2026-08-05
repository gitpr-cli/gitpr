---
name: smart-excludes-remote-control
description: Lista de exclusão do git diff controlada remotamente via template JSON no GitHub
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-18_smart_excludes_remote.md
  date: 2026-07-18
  branch: develop_natan
---

A lista `SMART_EXCLUDES` (padrões git-pathspec para exclusão inteligente de diffs)
é gerenciada remotamente via `templates/gitpr.smart-excludes.json` no GitHub.

Resolução em 4 níveis:
1. Cópia local `~/.gitpr/conf/gitpr.smart-excludes.json` (quando `SMART_EXCLUDES_VERSION` bate com `__lang_version__`)
2. Download do GitHub (timeout 3s) — salva local + stampa `SMART_EXCLUDES_VERSION`
3. Cópia local stale (quando download falha)
4. `_FALLBACK_SMART_EXCLUDES` (constante, 12 padrões originais)

O template armazena padrões como **globs puros** (`"*.lock"`, sem prefixo `:(exclude)`).
O código aplica o prefixo — uma entrada malformada nunca quebra o `git diff`.

A lista é language-independent (um arquivo só, sem sufixo de idioma).
Redownload é disparado por bump de `__lang_version__` em `src/updater.py`.

**Why:** A lista de exclusão pode ser atualizada sem shipping um novo release
da CLI. Basta editar o template no branch `main` e bumpart `__lang_version__`.

**How to apply:**
1. Para adicionar novo padrão de exclusão, editar `templates/gitpr.smart-excludes.json`
2. Bumpar `__lang_version__` em `src/updater.py` para propagar a todos os clientes
3. O loader é 100% silencioso em falha — diff nunca quebra por causa dessa lista
4. Edições manuais do usuário em `~/.gitpr/conf/` sobrevivem até o próximo bump de versão

Relacionado: [[version-marker-pattern]], [[spinner-config-pattern]]
