# Walkthrough — Reconciliação da Versão do Projeto

A versão do projeto foi reconciliada e unificada sob uma convenção canônica única, eliminando o valor congelado `0.0.37` e estabelecendo `src/updater.py::__version__` (atualmente `1.4.4`) como a Single Source of Truth (SSOT).

## O que foi alterado

### 1. Documentação de Agentes
- **`CLAUDE.md`**: Atualizado o cabeçalho `- **Current version:** 1.4.4 (Canonical SSOT in \`src/updater.py\`)`.
- **`GEMINI.md`**: Atualizado o cabeçalho `- **Current version:** 1.4.4 (Canonical SSOT in \`src/updater.py\`)`.

### 2. Modelo de Domínio
- **`CONTEXT.md`**: Adicionadas as definições canônicas:
  - `Package version`: Versão do pacote PyPI/CLI definida em `src/updater.py::__version__`.
  - `Language asset version`: Versão de esquema/dicionário i18n (`__lang_version__`).
  - `Hook script version`: Versão dos scripts de hook (`__scripts_version__`).

### 3. Registro Arquitetural
- **`docs/adr/0014-canonical-package-version-ssot.md`**: Formalização da decisão arquitetural que estabelece `src/updater.py::__version__` como SSOT e a proibição de números de versão divergentes em arquivos de configuração de agentes.

### 4. Código Fonte
- **`src/updater.py`**: Comentários enriquecidos no bloco de variáveis de versão, explicitando o papel de `__version__` como SSOT consumida por `pyproject.toml`, Click CLI (`src/main.py`), release workflows (`release.yml`) e regras de agentes.

### 5. Blindagem por Testes Automatizados
- **`tests/unit/test_version_consistency.py`**: Nova suíte de testes de consistência:
  - `test_package_version_is_valid_pep440`: Verifica se `__version__` é PEP 440 válida sem prefixo "v".
  - `test_pyproject_toml_points_to_ssot`: Garante que `pyproject.toml` consome `src.updater.__version__`.
  - `test_claude_md_version_matches_ssot`: Garante que `CLAUDE.md` está em sincronia com `__version__`.
  - `test_gemini_md_version_matches_ssot`: Garante que `GEMINI.md` está em sincronia com `__version__`.
  - `test_asset_versions_distinct_from_package_version`: Valida a distinção entre versão do pacote e versões de ativos (`__lang_version__` e `__scripts_version__`).

## Resultados dos Testes

```
python -m unittest tests/unit/test_version_consistency.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.004s

OK
```
