# Survey and Facts — Map-Reduce Token Partitioning & Per-Provider Part Limits

**Data:** 2026-11-11  
**Branch:** develop_natan  
**Task:** map_reduce_token_partitioning  

---

## 1. Contexto e Problema Identificado

No processamento de diffs gigantes via Map-Reduce, o modelo de IA (notadamente o Gemini com limite estrito de contexto de 1.048.576 tokens / $2^{20}$ tokens) estava recebendo lotes que ultrapassavam esse teto, resultando em erros 400 de excesso de tokens.

### Causa Raiz no Código
1. **Ausência de fatiamento intra-arquivo**: `split_diff_into_chunks` em `src/core.py` utilizava `re.split(r"(^diff --git a/)")`, agrupando arquivos inteiros. Se um único arquivo contivesse mais de 1M tokens (arquivos de migração massiva, lockfiles, bundles ou código gerado), ele era mantido como um bloco único indivisível, furando qualquer teto global.
2. **Ausência de distinção entre o gatilho e o tamanho dos lotes**: O código usava uma única constante `max_tokens=90000` tanto para decidir se entra em Map-Reduce quanto para tentar agrupar arquivos.
3. **Falta de controle por Provider**: Provedores diferentes (Gemini, DeepSeek, Ollama) possuem limites de contexto e tolerâncias a latência diferentes. Usuários não tinham como configurar os limites pelo `gitpr config` ou `.env`.

---

## 2. Decisões do Grill (Rodadas 1 e 2)

1. **Separação de Papéis das Variáveis**:
   - **Gatilho do Map-Reduce**: Limite de tokens totais do diff para disparar o modo Map-Reduce. Padrão: 90.000 tokens.
   - **Tamanho Máximo de Cada Lote (`MAX_PART_TOKENS`)**: Limite de tokens para cada fatia individual enviada à IA. Padrão: **50.000 tokens**.
2. **Configuração por Provider**:
   - `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) com fallback para `GITPR_MAP_REDUCE_MAX_TOKENS` e default 90.000.
   - `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>` (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) com fallback para `GITPR_MAP_REDUCE_MAX_PART_TOKENS` e default 50.000.
3. **Fatiamento Intra-Arquivo em Cascata**:
   - Se um arquivo individual ultrapassar `MAX_PART_TOKENS`:
     1. Tenta fatiar por hunks (`@@ -... +... @@`).
     2. Se um único hunk for maior que `MAX_PART_TOKENS`, fatia por linhas (`\n`).
     3. Em cada sub-bloco gerado, repete o cabeçalho original `diff --git` e injeta a marcação contextual `[Part X of file Y]` para manter o entendimento da IA.
4. **Fallback para Diffs Não Convencionais ou Texto Puro**:
   - Regex flexível para detectar `diff --git (a/|b/| )` ou `--- [ab]/`. Se não encontrar cabeçalhos, fatia diretamente por quebra de linha respeitando `MAX_PART_TOKENS`.
5. **Integração com `gitpr config` (TUI)**:
   - Declarar os campos no `src/config_schema.py` sob a categoria `ai`, com filtro condicional `show_if` exibindo as variáveis do provedor atualmente selecionado.
6. **Proteção no Passo de Reduce**:
   - Instrução de resumo parcial conciso no prompt do Map + pré-reduce se a união dos resumos parciais ultrapassar o limite.

---

## 3. Matriz de Arquivos Afetados

| Arquivo | Mudança | Escopo |
|---|---|---|
| `src/core.py` | Refatoração de `split_diff_into_chunks` com cascata (arquivo -> hunk -> linha) e resolução de limites por provider | Motor Principal |
| `src/config.py` | Função helper `get_map_reduce_thresholds(provider)` com fallback em cadeia | Configuração |
| `src/config_schema.py` | Declaração de `GITPR_MAP_REDUCE_MAX_TOKENS_*` e `GITPR_MAP_REDUCE_MAX_PART_TOKENS_*` | Schema TUI |
| `src/issue_engine.py` | Adoção dos thresholds dinâmicos por provider | Issues Map-Reduce |
| `src/review/remote_pr.py` | Adoção dos thresholds dinâmicos no cálculo de batches | Remote PR |
| `docs/map-reduce-diff.md` (e 4 traduções) | Atualização da documentação sobre o fatiamento intra-arquivo e variáveis | Documentação |
| `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` | Formalização da decisão arquitetural | ADR |
| `tests/test_core.py` & `tests/test_config_schema.py` | Testes unitários para a cascata de fatiamento e resolução por provider | Testes |
