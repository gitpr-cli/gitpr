# Plano de Execução — Fatiamento Intra-Arquivo e Limites por Provider no Map-Reduce

**Data:** 2026-11-11  
**Branch:** develop_natan  
**Task:** map_reduce_token_partitioning  

---

## 1. Objetivo

Eliminar de forma definitiva erros de limite de contexto de 1.048.576 tokens nos fluxos Map-Reduce do GitPR, introduzindo:
1. Resolução configurável de `MAX_TOKENS` (gatilho, padrão 90.000) e `MAX_PART_TOKENS` (tamanho por lote, padrão 50.000), personalizáveis globalmente e por provider (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) no `gitpr config`.
2. Fatiamento em cascata à prova de arquivos gigantes (Arquivo ➔ Hunk ➔ Linhas), preservando cabeçalhos de contexto `diff --git`.
3. Fallback inteligente para diffs sem cabeçalho e proteção no passo de Reduce.

---

## 2. Componentes e Implementação

### Componente 1: Schema de Configuração (`src/config_schema.py` & `src/config.py`)
- Adicionar campos de configuração sob `category="ai"` com `show_if=(("DEFAULT_AI_PROVIDER", ("<provider>",)),)`:
  - `GITPR_MAP_REDUCE_MAX_TOKENS_GEMINI` (default: "90000")
  - `GITPR_MAP_REDUCE_MAX_PART_TOKENS_GEMINI` (default: "50000")
  - `GITPR_MAP_REDUCE_MAX_TOKENS_DEEPSEEK` (default: "90000")
  - `GITPR_MAP_REDUCE_MAX_PART_TOKENS_DEEPSEEK` (default: "50000")
  - `GITPR_MAP_REDUCE_MAX_TOKENS_OLLAMA` (default: "90000")
  - `GITPR_MAP_REDUCE_MAX_PART_TOKENS_OLLAMA` (default: "50000")
- Em `src/config.py`:
  - Implementar função `get_map_reduce_thresholds(provider=None)`:
    - Retorna `(max_tokens, max_part_tokens)` resolvendo:
      1. `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` se definido.
      2. Senão `GITPR_MAP_REDUCE_MAX_TOKENS` se definido.
      3. Senão 90.000.
      E analogamente para `MAX_PART_TOKENS` (default 50.000).

### Componente 2: Algoritmo de Fatiamento em Cascata (`src/core.py`)
- Refatorar `split_diff_into_chunks(diff_text, max_tokens=90000, max_part_tokens=50000)`:
  - Se `estimate_token_count(diff_text) <= max_tokens`, retorna `[diff_text]`.
  - Quebra o diff por arquivos (`diff --git`). Se nenhum cabeçalho for detectado, cai no fallback de linhas.
  - Para cada arquivo:
    - Se o arquivo couber em `max_part_tokens`, acumula no lote atual.
    - Se o arquivo isoladamente exceder `max_part_tokens`:
      - Quebra por hunks (`@@ -... +... @@`).
      - Para qualquer hunk que isoladamente exceda `max_part_tokens`, quebra por linhas (`\n`).
      - Repete o cabeçalho original `diff --git a/... b/...` + indicador `[Part X/Y of file]` em cada sub-lote.
- Atualizar chamadas em `generate_pr_content()` e `src/issue_engine.py` para usar `get_map_reduce_thresholds(provider)`.

### Componente 3: Proteção no Passo de Reduce (`src/core.py`)
- Se `diff_unificado` (junção dos resumos parciais) exceder `max_tokens`, aplicar pré-reduce antes da chamada final.

### Componente 4: Governança, Documentação e ADR
- Criar `docs/adr/0022-map-reduce-per-provider-token-partitioning.md`.
- Atualizar `docs/map-reduce-diff.*.md` nos 5 idiomas descrevendo `MAX_PART_TOKENS` e as variáveis por provider.
- Atualizar `CONTEXT.md` com os termos canônicos.

### Componente 5: Testes Unitários
- Testes unitários para `split_diff_into_chunks`:
  - Diff com arquivo único gigante (> 50.000 tokens e > 1.048.576 tokens) deve ser fatiado sem que nenhum lote exceda `max_part_tokens`.
  - Preservação do cabeçalho em sub-blocos de arquivo único.
  - Diffs sem cabeçalho padrão fatiados por linha.
  - Resolução por provider em `get_map_reduce_thresholds`.
