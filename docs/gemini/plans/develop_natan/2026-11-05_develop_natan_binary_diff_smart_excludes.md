# Revisão de `git diff` com Arquivos Binários Grandes e Cobertura de Smart Excludes

## Goal Description

A decodificação de saídas do Git com `encoding="utf-8", errors="replace"` resolveu falhas em repositórios legados com codificação Latin-1/Windows-1252 (como `SIG-Novo`), mas expôs dois problemas complementares em repositórios com arquivos binários grandes:

1. **Lacuna nos padrões de `Smart Excludes`:** Apesar de `docs/smart-excludes.md` afirmar que a camada *Core Exclusions* filtra arquivos binários, `templates/gitpr.smart-excludes.json` inclui apenas lockfiles, assets web minificados (`*.min.js`, `*.min.css`, `*.bundle.*`, `*.map`, `*.svg`), `*.log`, `bun.lockb`, `*.pyc`, `*.pyo`, `.DS_Store` e `Thumbs.db`. Além disso, `_FALLBACK_SMART_EXCLUDES` em `src/core.py` ficou defasado (13 itens contra 35 do JSON). Extensões binárias reais (imagens, PDFs/Office, pacotes compactados, fontes, áudio/vídeo, binários compilados, bancos SQLite/datasets e certificados binários) não estavam excluídas no pathspec do `git diff`.
2. **Vazamento de sequências de `U+FFFD` para o modelo de IA:** O Git só classifica um blob como binário se encontrar um byte `NUL` (`0x00`) nos primeiros 8.000 bytes (ou se configurado via `.gitattributes`). Quando um arquivo binário tem cabeçalho ASCII longo (ex.: PDFs, PostScript, dumps híbridos) ou extensão proprietária/desconhecida forçada como texto, o `git diff` emite hunks gigantes que `errors="replace"` converte em sequências de `U+FFFD` (`\ufffd`), desperdiçando dezenas de milhares de tokens.

Esta mudança implementa uma **defesa em dupla camada**:
- **Camada 1 — Pathspec (`Smart Excludes`):** Expansão de `templates/gitpr.smart-excludes.json` com 8 categorias de extensões binárias reais, paridade 1:1 com `_FALLBACK_SMART_EXCLUDES` em `src/core.py` e bump de `__lang_version__` para `"v0.0.39"` em `src/updater.py`.
- **Camada 2 — Pós-diff (`Binary hunk guard`):** Sanitização determinística em Python que inspeciona as seções do diff (`diff --git ...`) e colapsa os hunks daquelas que apresentarem fluxo binário decodificado como `U+FFFD` (`>= 8` `U+FFFD` contíguos **ou** `>= 32` `U+FFFD` com densidade `>= 10%` nos caracteres dos hunks) para o marcador padrão `Binary files a/<path> and b/<path> differ`, preservando 100% dos arquivos de código legado em Latin-1/CP1252.

---

## Proposed Changes

### 1. Modelo de Domínio (`CONTEXT.md`)
- Atualizar **Smart Excludes** para incluir *binary assets* dentro de *Core Exclusions*.
- Adicionar **Binary hunk guard** ao glossário.

### 2. Templates e Versão de Assets (`templates/gitpr.smart-excludes.json` e `src/updater.py`)
- Expandir `templates/gitpr.smart-excludes.json` com as 8 famílias de extensões binárias (imagens, documentos Office/PDF, pacotes/arquivos compactados, fontes, áudio/vídeo, compilados/bibliotecas/bytecode, bancos/datasets/pesos ML, certificados/keystores).
- Atualizar `__lang_version__` em `src/updater.py` de `"v0.0.38"` para `"v0.0.39"`.

### 3. Parser & Binary Hunk Guard (`src/diff_parser.py` e `src/review/diff_normalizer.py`)
- Implementar `collapse_binary_hunks(diff_text)` em `src/diff_parser.py` com limiar combinado (`BINARY_FFFD_CONTIGUOUS_RUN = 8`, `BINARY_FFFD_MIN_COUNT = 32`, `BINARY_FFFD_MIN_DENSITY = 0.10`).
- Integrar `collapse_binary_hunks` em `filter_excluded_sections` (`src/review/diff_normalizer.py`).

### 4. Orquestração e Pontos de Captura de Diff (`src/core.py`, `src/main.py`, `src/application/use_cases/`)
- Sincronizar `_FALLBACK_SMART_EXCLUDES` em `src/core.py` em paridade 1:1 com `templates/gitpr.smart-excludes.json`.
- Aplicar `collapse_binary_hunks` em `get_git_diff`, `get_git_staged_diff`, `get_unstaged_diff`, `get_git_full_diff`, `get_check_diff`, `current_diff` e nos diffs diretos de `main.py` (`tests --file` e `risk --base`), mantendo `get_split_diff()` intacto.

### 5. Documentação (`docs/smart-excludes*.md`)
- Atualizar `docs/smart-excludes.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md` e `.fr_fr.md` documentando as categorias binárias e a guarda de hunks binários.

### 6. Testes Automatizados (`tests/test_smart_excludes.py` e `tests/test_full_diff_encoding.py`)
- Teste de paridade 1:1 entre `_FALLBACK_SMART_EXCLUDES` e `templates/gitpr.smart-excludes.json`.
- Testes das 8 categorias de extensões binárias.
- Testes unitários e de integração (com repositório Git real) para `collapse_binary_hunks`, validando que código legado Latin-1 é preservado e binários vazados têm hunks colapsados para `Binary files a/... and b/... differ`.

---

## Verification Plan
- `python -m pytest tests/test_smart_excludes.py tests/test_full_diff_encoding.py tests/test_diff_parser.py tests/review/test_remote_pr.py -v`
- `python -m pytest tests/test_core.py tests/test_i18n.py tests/check/ -q`
