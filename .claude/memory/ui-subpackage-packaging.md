---
name: ui-subpackage-packaging
description: src/ui/ requer __init__.py vazio e find-packages no pyproject.toml para ser incluído no .whl
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-02_build_fixes.md
  date: 2026-07-02
  branch: develop_natan
---

Sub-packages Python em `src/` precisam de dois requisitos para serem incluídos
corretamente no wheel (`.whl`) e funcionarem após `pip install`:

1. **`src/ui/__init__.py`**: arquivo vazio que torna o diretório um sub-package
   reconhecido pelo setuptools. Sem ele, o módulo não é descoberto.

2. **`pyproject.toml` com `[tool.setuptools.packages.find]`**:
   ```toml
   [tool.setuptools.packages.find]
   include = ["src", "src.*"]
   ```
   O formato `packages = ["src"]` (lista simples) não inclui sub-packages.

**Why:** Sem `__init__.py` + `find:`, o comando `pip install gitpr-cli` resultava
em `ModuleNotFoundError: No module named 'src.ui'` porque o sub-package
simplesmente não era incluído no arquivo `.whl`.

**How to apply:** Ao criar qualquer novo sub-package em `src/`:
1. Criar `__init__.py` (pode ser vazio ou com exports)
2. Verificar se `pyproject.toml` já cobre com `"src.*"` no `find.include`
3. Adicionar dependências do sub-package (ex: `textual`, `requests`) no `pyproject.toml`
4. Testar com `pip install -e .` antes de publicar

Relacionado: [[circular-import-lazy-pattern]]
