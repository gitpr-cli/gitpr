# Reconciliar a Versão do Projeto e Estabelecer Convenção Canônica Única

## Goal Description
Atualmente, `CLAUDE.md` e `GEMINI.md` exibem `- **Current version:** 0.0.37` enquanto o código em `src/updater.py::__version__` está em **1.4.4** (e o `pyproject.toml` utiliza `dynamic = ["version"]` referenciando `src.updater.__version__`). O valor `0.0.37` coincide com `__lang_version__ = "v0.0.37"` e sofreu drift histórico.

Este plano reconcilia os documentos dos agentes com a versão real do pacote, formaliza `src/updater.py::__version__` como a **Single Source of Truth (SSOT)** canônica, registra as definições de domínio no `CONTEXT.md`, formaliza o ADR-0014 e cria uma suíte de testes de consistência (`tests/unit/test_version_consistency.py`) para evitar qualquer regressão ou drift futuro.

---

## User Review Required
> [!NOTE]
> As decisões de design foram alinhadas no Round 1 de grilling:
> 1. **SSOT canônica**: `src/updater.py::__version__`.
> 2. **Documentação de agentes (`CLAUDE.md` e `GEMINI.md`)**: Atualizados para `1.4.4` com remissão explícita à SSOT e blindados por teste automatizado.
> 3. **Glossário (`CONTEXT.md`)**: Inclusão de `Package version`, `Language asset version` e `Hook script version`.
> 4. **Registro Arquitetural**: Criação do `docs/adr/0014-canonical-package-version-ssot.md`.

---

## Proposed Changes

### Documentação de Agentes e Instruções

#### [MODIFY] `CLAUDE.md`
- Atualizar `- **Current version:** 0.0.37` para `- **Current version:** 1.4.4 (Canonical SSOT in src/updater.py)`.
- Adicionar menção à convenção de versionamento na seção de regras.

#### [MODIFY] `GEMINI.md`
- Atualizar `- **Current version:** 0.0.37` para `- **Current version:** 1.4.4 (Canonical SSOT in src/updater.py)`.
- Adicionar menção à convenção de versionamento na seção de regras.

---

### Domínio e Arquitetura

#### [MODIFY] `CONTEXT.md`
- Adicionar termos canônicos no glossário:
  * **Package version**: Identificador semântico (PEP 440 / SemVer) da distribuição GitPR no PyPI, definido exclusivamente em `src/updater.py::__version__`.
  * **Language asset version**: Identificador de versão (`__lang_version__`) dos esquemas e arquivos de tradução i18n (`langs/`), versionado independentemente do pacote.
  * **Hook script version**: Identificador de versão (`__scripts_version__`) dos templates de Git hooks em `scripts/`, versionado independentemente do pacote.

#### [NEW] `docs/adr/0014-canonical-package-version-ssot.md`
- Registro formal da decisão arquitetural sobre a SSOT da versão do pacote e a sincronização obrigatória com as regras de agentes (`CLAUDE.md`/`GEMINI.md`), prevenindo confusão com versões de assets (`__lang_version__`).

---

### Código e Testes de Consistência

#### [MODIFY] `src/updater.py`
- Adicionar comentários e docstring no bloco de versões reforçando que `__version__` é a SSOT consumida por `pyproject.toml`, Click CLI (`main.py`) e CI (`release.yml`).

#### [NEW] `tests/unit/test_version_consistency.py`
- Criar suíte de testes com `unittest`:
  1. `test_version_pep440_valid`: Valida que `src.updater.__version__` é uma versão PEP 440 válida (`packaging.version.Version`).
  2. `test_pyproject_toml_points_to_ssot`: Valida que `pyproject.toml` referencia `src.updater.__version__` em `[tool.setuptools.dynamic]`.
  3. `test_claude_md_version_matches_ssot`: Extrai o regex `Current version:\s*([0-9]+\.[0-9]+\.[0-9]+)` de `CLAUDE.md` e assegura igualdade estrita com `__version__`.
  4. `test_gemini_md_version_matches_ssot`: Extrai o regex de `GEMINI.md` e assegura igualdade estrita com `__version__`.
  5. `test_asset_versions_distinct_from_package_version`: Valida que `__lang_version__` e `__scripts_version__` são variáveis distintas e documentadas.

---

## Verification Plan

### Automated Tests
- Execução do novo teste unitário de consistência:
  `python -m unittest tests/unit/test_version_consistency.py` ou `pytest tests/unit/test_version_consistency.py`
- Execução dos testes existentes de updater:
  `python -m unittest tests/test_updater.py`

### Manual Verification
- Inspecionar `CLAUDE.md` e `GEMINI.md` confirmando que a versão indica `1.4.4` e referencia `src/updater.py`.
- Verificar formatação e links em `CONTEXT.md` e `docs/adr/0014-canonical-package-version-ssot.md`.
