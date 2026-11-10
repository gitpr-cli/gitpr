# Implementation Plan — Git Diff com Arquivos Binários Grandes e Smart Excludes

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Plano:** `binary_diff_smart_excludes`

## Goal Description
Revisar e consolidar o tratamento do `git diff` em repositórios com arquivos binários grandes e decodificação não-UTF8 (`U+FFFD`), auditando a cobertura dos Smart Excludes em cenários reais e estabelecendo defesa em profundidade (Defense-in-Depth) diretamente na entrada do gerador de conteúdo de IA (`generate_pr_content`). Encerramento formal do débito técnico herdado.

## Proposed Changes

### 1. `templates/gitpr.smart-excludes.json`
- Adicionar extensões modernas de ML e datasets: `*.arrow`, `*.gguf`, `*.tflite`, `*.keras`.

### 2. `src/core.py`
- Adicionar `*.arrow`, `*.gguf`, `*.tflite`, `*.keras` a `_FALLBACK_SMART_EXCLUDES` mantendo paridade 1:1 com o template remoto.
- Inserir `diff_text = collapse_binary_hunks(diff_text)` no topo de `generate_pr_content()` logo após a validação de diff não-vazio.

### 3. `tests/test_smart_excludes.py`
- Atualizar `TestSmartExcludesBinaryCoverage.test_all_eight_binary_families_are_covered` adicionando as 4 novas extensões ao conjunto de padrões esperados da família 7.

### 4. `tests/test_full_diff_encoding.py`
- Adicionar teste unitário validando que `generate_pr_content` intercepta diffs brutos com `U+FFFD` e os entrega sanitizados para as chamadas de IA.

## Verification Plan

### Automated Tests
- `python -m pytest tests/test_smart_excludes.py -v`
- `python -m pytest tests/test_full_diff_encoding.py -v`
