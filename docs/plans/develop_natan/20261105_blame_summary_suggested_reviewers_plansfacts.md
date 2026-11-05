# Plano de Execução — Resumo de Arquivos com e sem Blame na Sugestão de Revisores (`blame_summary_suggested_reviewers`)

- **Data:** 2026-11-05
- **Branch:** `develop_natan`
- **Origem:** Sessão `/plan` e `/grill-with-docs`

## 1. Objetivo

Substituir as múltiplas linhas repetitivas de aviso emitidas por cada arquivo novo ou binário na busca de revisores (`⚠️ Arquivo {path}: nenhum histórico de blame encontrado...`) por uma única linha agregada de resumo quando houver arquivos sem blame:
`ℹ️ Análise de blame: {with_count} arquivo(s) com blame, {without_count} sem blame (novos ou binários).`

## 2. Arquitetura e Componentes Afetados

```
Unified Diff
     │
     ▼
src/suggest_reviewers.py (compute_reviewer_suggestions)
     │  - Popula files_with_blame: list[str]
     │  - Popula files_without_blame: list[str]
     │  - Remove os warnings individuais de "no blame history found"
     ▼
src/reviewer_suggestion.py (ReviewerSuggestionResult)
     │  - Adiciona campos files_with_blame e files_without_blame
     ▼
src/main.py
     │  - Se files_without_blame não for vazio:
     │      imprime a linha resumida formatada via __()
     │  - Exibe warnings restantes de result.warnings (se existirem)
     ▼
langs/*.json + src/updater.py
     │  - Adiciona nova chave i18n em todos os idiomas
     │  - Atualiza __lang_version__ (v0.0.40 -> v0.0.41)
```

## 3. Detalhamento das Alterações

1. **`src/reviewer_suggestion.py`**:
   - No dataclass `ReviewerSuggestionResult`, adicionar:
     ```python
     files_with_blame: list = field(default_factory=list)  # list[str]
     files_without_blame: list = field(default_factory=list)  # list[str]
     ```

2. **`src/suggest_reviewers.py`**:
   - Em `compute_reviewer_suggestions()`:
     - Inicializar `files_with_blame = []` e `files_without_blame = []`.
     - Ao verificar `if not file_hits:`:
       - Adicionar `file_path` a `files_without_blame`.
       - Não adicionar mais warning individual em `result.warnings`.
     - Ao verificar `else:`:
       - Adicionar `file_path` a `files_with_blame`.
     - Passar `files_with_blame` e `files_without_blame` na construção de `ReviewerSuggestionResult` (inclusive no retorno antecipado quando `not hits`).

3. **`src/main.py`**:
   - No bloco de tratamento de `suggestion_result` (linha ~2013):
     ```python
     if suggestion_result:
         if suggestion_result.files_without_blame:
             click.secho(
                 __(
                     "ℹ️ Blame analysis: {with_count} file(s) with blame, {without_count} without blame (new or binary).",
                     with_count=len(suggestion_result.files_with_blame),
                     without_count=len(suggestion_result.files_without_blame),
                 ),
                 fg="yellow",
                 dim=True,
             )
         for warning in suggestion_result.warnings:
             click.secho(f"  ⚠️ {warning}", fg="yellow", dim=True)
         reviewer_suggestion = _reviewer_suggestion_view(
             suggestion_result, provider, repo_ref
         )
     ```

4. **`CONTEXT.md`**:
   - Adicionar o termo canônico **Blame summary**.

5. **`langs/*.json` e `src/updater.py`**:
   - Adicionar a nova chave nos 6 dicionários de tradução:
     - `en_us`: `"ℹ️ Blame analysis: {with_count} file(s) with blame, {without_count} without blame (new or binary)."`
     - `pt_br`: `"ℹ️ Análise de blame: {with_count} arquivo(s) com blame, {without_count} sem blame (novos ou binários)."`
     - `pt_pt`: `"ℹ️ Análise de blame: {with_count} ficheiro(s) com blame, {without_count} sem blame (novos ou binários)."`
     - `es_es` e `es`: `"ℹ️ Análisis de blame: {with_count} archivo(s) con blame, {without_count} sin blame (nuevos o binarios)."`
     - `fr_fr` e `fr`: `"ℹ️ Analyse de blame : {with_count} fichier(s) avec blame, {without_count} sans blame (nouveaux ou binaires)."`
   - Incrementar `__lang_version__ = "v0.0.41"` em `src/updater.py`.

6. **Testes Unitários**:
   - Atualizar `tests/test_suggest_reviewers.py`:
     - `test_file_without_history_warns_and_others_continue` -> verificar `files_without_blame` e `files_with_blame`.
     - `test_all_files_without_history_yields_warnings_only` -> verificar que `files_without_blame` contém os arquivos e `warnings` não contém mais as linhas por arquivo.
   - Adicionar novo teste em `tests/test_main_suggest_reviewers.py` ou `tests/test_suggest_reviewers.py` cobrindo a formatação e a regra de exibição da linha de resumo.
