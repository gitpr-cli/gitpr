## Completion Report — Git Diff com Arquivos Binários Grandes e Smart Excludes

### What was done
- Auditada a cobertura de arquivos binários grandes no `git diff` e a atuação dos Smart Excludes em cenários reais, formalizando o encerramento do item herdado.
- Adicionado reforço de defesa em profundidade (Defense-in-Depth) através da invocação defensiva de `collapse_binary_hunks(diff_text)` no ponto de entrada de `generate_pr_content()` em `src/core.py`.
- Expandido o catálogo de Smart Excludes com 4 novas extensões modernas de ML e datasets (`*.arrow`, `*.gguf`, `*.tflite`, `*.keras`) em `templates/gitpr.smart-excludes.json` e `_FALLBACK_SMART_EXCLUDES` (`src/core.py`).
- Atualizados os testes de cobertura de Smart Excludes (`tests/test_smart_excludes.py`) e adicionado teste unitário para `generate_pr_content` (`tests/test_full_diff_encoding.py`).
- Registrados artefatos de governança em `docs/survey/` e `docs/plans/`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat | Expansão de `_FALLBACK_SMART_EXCLUDES` com 4 extensões ML/data e adição defensiva de `collapse_binary_hunks` em `generate_pr_content` |
| `templates/gitpr.smart-excludes.json` | feat | Inclusão de `*.arrow`, `*.gguf`, `*.tflite`, `*.keras` na família de datasets e pesos ML |
| `tests/test_smart_excludes.py` | test | Inclusão das novas extensões na validação da família 7 em `TestSmartExcludesBinaryCoverage` |
| `tests/test_full_diff_encoding.py` | test | Novo teste `test_generate_pr_content_defensively_collapses_binary_hunks` |
| `docs/survey/20261109_binary_diff_smart_excludes_surveyfacts.md` | docs | Survey de fatos, decisões do grill e auditoria de cobertura |
| `docs/plans/develop_natan/20261109_binary_diff_smart_excludes_plansfacts.md` | docs | Plano de execução e validação da sessão |
| `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_binary_diff_smart_excludes.md` | docs | Registro do plano de desenvolvimento da branch |
| `docs/gemini/walkthrough/develop_natan/2026-11-09_binary_diff_smart_excludes.md` | docs | Walkthrough das mudanças implementadas e resultados de testes |

### Impact
- **Functionality:** Diffs que contenham sequências densas ou contíguas de `U+FFFD` (bytes binários decodificados com substituição) agora são colapsados para `Binary files ... differ` em todas as entradas de geração de conteúdo de IA, incluindo chamadas que injetam `diff_text` externamente (via MCP ou automações).
- **Performance:** Sem impacto negativo. `collapse_binary_hunks()` possui atalho $O(1)$ que retorna imediatamente quando o caractere `\ufffd` não está presente no diff.
- **Compatibility:** Totalmente retrocompatível. Códigos em Latin-1 / Windows-1252 com acentos esparsos continuam preservados integralmente sem falso-positivo.

### Next steps (if applicable)
- Nenhum. O item técnico herdado foi auditado, reforçado e encerrado formalmente.
