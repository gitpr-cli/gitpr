---
name: skill-folder-auto-migration
description: resolve_skill_path() migra arquivos legacy da raiz para .gitpr/skill/ transparentemente
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-13_skill_files_gitpr_skill_folder.md
  date: 2026-07-13
  branch: develop_natan
---

Arquivos de skill/config (`.gitpr.*.md`, `.gitpr.linter.yml`, `.gitpr.md` legado)
agora residem em `.gitpr/skill/` no projeto local. Duas funções em `src/config.py`
gerenciam a transição:

- `get_skill_dir()`: retorna `<cwd>/.gitpr/skill`
- `resolve_skill_path(filename)`: retorna o path dentro de `.gitpr/skill/` e
  **migra transparentemente** um arquivo legado da raiz para a pasta (com fallback
  para o path raiz se o `shutil.move` falhar)

Todos os resolvers de skill passam por `resolve_skill_path()`:
- `get_skill_context()` em `core.py`
- `load_linter_rules()` em `config.py`
- `generate_skill_template()` em `core.py` (download direto para `.gitpr/skill/`)
- `issue_engine.py` e `blame_engine.py`

**Why:** Arquivos `.gitpr.*.md` na raiz poluíam o projeto. A migração automática
evita step manual para usuários existentes. Se o move falhar (permissão, disco),
o sistema faz fallback para ler do path raiz — nunca quebra.

**How to apply:**
1. NUNCA referenciar arquivos de skill diretamente na raiz — sempre usar `resolve_skill_path()`
2. O download de novos templates (`--skill`) deve criar `.gitpr/skill/` e baixar direto lá
3. Arquivos que já existem (na pasta ou migrados da raiz) NUNCA são sobrescritos
4. Mensagens de ajuda devem referenciar `.gitpr/skill/`, não a raiz
