# Walkthrough — Fatiamento Intra-Arquivo e Limites por Provider no Map-Reduce

**Data:** 2026-11-11  
**Branch:** `develop_natan`  
**Tarefa:** `map_reduce_token_partitioning`  

---

## O que foi realizado

1. **Separação de Limites de Disparo e Tamanho de Lote**:
   - `GITPR_MAP_REDUCE_MAX_TOKENS`: Limite total de tokens do diff para disparar o modo Map-Reduce (padrão: **90.000 tokens**).
   - `GITPR_MAP_REDUCE_MAX_PART_TOKENS`: Limite estrito de tokens para cada lote parcial individual na etapa de Map (padrão: **50.000 tokens**).
   - Ambos configuráveis globalmente ou por provedor (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) no `~/.gitpr/.env` e na TUI `gitpr config`.

2. **Fatiamento em Cascata (Arquivo ➔ Hunk ➔ Linhas)**:
   - Refatorada a função `split_diff_into_chunks` em `src/core.py`.
   - Se um arquivo individual for maior que `MAX_PART_TOKENS`, ele é fatiado em hunks (`@@ -... +... @@`).
   - Se um único hunk ainda for maior que `MAX_PART_TOKENS`, ele é fatiado por quebras de linha (`\n`) ou fatias de caracteres.
   - Em cada sublote gerado, o cabeçalho original `diff --git` e a marcação contextual `# [<filename> - part X]` são preservados.
   - Fallback por quebra de linha para textos ou diffs sem cabeçalho padrão.

3. **Salvaguarda na Etapa de Reduce**:
   - Implementada redução intermediária (pré-reduce) em `src/core.py` caso a união dos resumos parciais (`diff_unificado`) ultrapasse o limite de disparo antes da síntese final.

4. **Schema de Configuração & TUI**:
   - Declarados os campos `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` e `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>` em `src/config_schema.py` com `show_if` condicional ao provedor ativo.
   - Implementado o resolvedor hierárquico `get_map_reduce_thresholds(provider)` em `src/config.py`.

5. **Documentação & ADR**:
   - Criada a [`docs/adr/0022-map-reduce-per-provider-token-partitioning.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/adr/0022-map-reduce-per-provider-token-partitioning.md).
   - Atualizados os documentos [`docs/map-reduce-diff.*.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/map-reduce-diff.md) em 5 idiomas.
   - Registrados termos de domínio em `CONTEXT.md` (`Map-reduce trigger threshold`, `Map-reduce part size`, `Cascade chunking`).

6. **Testes Unitários**:
   - Criado `tests/test_map_reduce_chunking.py` com 10 testes cobrindo resolução por provider, fatiamento multi-arquivo, fatiamento intra-arquivo por hunks e linhas, e fallback.
   - Sincronizados e validados os arquivos de internacionalização em `tests/test_i18n.py`.

---

## Resultados da Validação

```bash
python -m pytest tests/test_map_reduce_chunking.py tests/test_config_schema.py tests/test_i18n.py -v
```

Resultado:
- **101 testes executados e 100% aprovados** (10 em `test_map_reduce_chunking.py`, 55 em `test_config_schema.py`, 22 em `test_i18n.py`, etc.).
