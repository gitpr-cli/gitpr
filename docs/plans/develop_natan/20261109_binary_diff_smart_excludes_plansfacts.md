# Plano de Execução — Git Diff com Arquivos Binários Grandes e Smart Excludes

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Task:** `binary_diff_smart_excludes`
- **Origem:** Grill `/plan /grill-with-docs` (1 rodada, 3 decisões)
- **Estado:** Pronto para Execução

---

## 1. Objetivos

1. **Defesa em Profundidade na Entrada da IA:**
   - Garantir que `generate_pr_content()` em `src/core.py` aplique `diff_text = collapse_binary_hunks(diff_text)` logo após verificar se o diff não é vazio.
2. **Atualização do Catálogo de Smart Excludes:**
   - Adicionar as extensões modernas de ML e datasets (`*.arrow`, `*.gguf`, `*.tflite`, `*.keras`) em:
     - `templates/gitpr.smart-excludes.json`
     - `_FALLBACK_SMART_EXCLUDES` em `src/core.py`
     - `tests/test_smart_excludes.py` (`TestSmartExcludesBinaryCoverage.test_all_eight_binary_families_are_covered`)
3. **Validação de Testes:**
   - Adicionar teste unitário validando que `generate_pr_content` intercepta e colapsa diffs brutos com `U+FFFD`.
   - Executar a suíte de testes de `smart_excludes` e `full_diff_encoding`.
4. **Relatório de Conclusão:**
   - Gerar o completion report obrigatório em `docs/gemini/reports/develop_natan/2026-11-09_binary_diff_smart_excludes.md`.

---

## 2. Detalhamento das Mutações

### 2.1. `src/core.py`
- Adicionar `*.arrow`, `*.gguf`, `*.tflite`, `*.keras` em `_FALLBACK_SMART_EXCLUDES`.
- Em `generate_pr_content()`:
  ```python
  if not diff_text or not diff_text.strip():
      ...
      return None

  diff_text = collapse_binary_hunks(diff_text)
  ```

### 2.2. `templates/gitpr.smart-excludes.json`
- Adicionar `*.arrow`, `*.gguf`, `*.tflite`, `*.keras` na seção de datasets/ML, mantendo paridade 1:1 com `_FALLBACK_SMART_EXCLUDES`.

### 2.3. `tests/test_smart_excludes.py`
- Atualizar a família 7 em `TestSmartExcludesBinaryCoverage.test_all_eight_binary_families_are_covered` incluindo `*.arrow`, `*.gguf`, `*.tflite`, `*.keras`.

### 2.4. `tests/test_full_diff_encoding.py`
- Adicionar caso de teste demonstrando que `generate_pr_content` colapsa hunks binários antes de processar os prompts da IA.

---

## 3. Critérios de Aceite e Verificação

- `pytest tests/test_smart_excludes.py -v` passa 100%.
- `pytest tests/test_full_diff_encoding.py -v` passa 100%.
- Paridade 1:1 estrita entre `templates/gitpr.smart-excludes.json` e `_FALLBACK_SMART_EXCLUDES`.
