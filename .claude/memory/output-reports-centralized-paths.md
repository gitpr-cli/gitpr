---
name: output-reports-centralized-paths
description: Centralização de paths de output em .gitpr/reports/ com resolve_output_path() e fallback por env var
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-06_reorganize_default_output_paths.md
  date: 2026-08-06
  branch: develop_natan
---

Todos os artefatos gerados pelo GitPR (PR, review, full review, file review, blame, issue) são salvos em
`.gitpr/reports/{tipo}/` por padrão, em vez de poluírem a raiz do projeto. A função `resolve_output_path()`
em `src/core.py` centraliza essa lógica com um dicionário `_OUTPUT_FOLDER_MAP` que mapeia cada env var
de output para sua subpasta.

A resolução segue 3 cenários em ordem de prioridade:
1. Se a env var contém um separador de diretório (`/` ou `\`) → caminho é usado como está (usuário definiu
   diretório customizado).
2. Se a env var contém apenas nome de arquivo (sem diretório) → prefixa com `.gitpr/reports/{tipo}/`.
3. Se a env var está vazia → usa o padrão `{branch}_{datetime}_TIPO.ext` dentro de `.gitpr/reports/{tipo}/`.

**Why:** Antes cada módulo duplicava a lógica de `os.getenv()` + `.format()` para resolver o path de output,
com padrões diferentes e dispersos. Centralizar em `resolve_output_path()` eliminou 4 call sites duplicados
e garante consistência entre todos os tipos de artefato. A migração de outputs da raiz para `.gitpr/reports/`
mantém o projeto organizado.

**How to apply:** Ao adicionar um novo tipo de artefato (ex: novo comando que gera arquivo), criar a env var
no `DEFAULT_CONFIG`, adicionar a entrada no `_OUTPUT_FOLDER_MAP`, e usar `resolve_output_path()` no call site.
Não duplicar a lógica de path — sempre delegar ao helper.
