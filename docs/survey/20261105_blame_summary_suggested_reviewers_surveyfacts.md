# Survey Facts — Resumo de Arquivos com e sem Blame na Sugestão de Revisores (`blame_summary_suggested_reviewers`)

- **Data:** 2026-11-05
- **Branch:** `develop_natan`
- **Task:** Substituição dos avisos repetitivos de arquivos sem blame por linha única consolidada de resumo na sugestão de revisores do PR.

## 1. Contexto da Tarefa e Fatos Levantados no Código

1. **Localização do Fluxo Interativo de PR (`src/main.py`)**:
   - No fluxo interativo default de criação/publicação de Pull Request, antes de abrir o `PrPublishApp` (TUI), `src/main.py` executa `compute_reviewer_suggestions(diff_text, ...)` quando `suggest_reviewers_enabled()` for verdadeiro.
   - Antes do cálculo, é impresso o status: `click.secho(__("🔍 Searching for suggested reviewers..."), fg="cyan", dim=True)`.
   - Após a execução do cálculo, se houver `suggestion_result`, o código itera sobre `suggestion_result.warnings` e imprime:
     `click.secho(f"  ⚠️ {warning}", fg="yellow", dim=True)` para cada item.

2. **Geração dos Avisos de Blame no Motor (`src/suggest_reviewers.py`)**:
   - A função `compute_reviewer_suggestions()` analisa cada arquivo presente em `added_lines` do diff unificado.
   - Para cada arquivo, executa `get_blame_for_range(file_path, start, end, repo_path=repo_path)`.
   - Quando `file_hits` retorna vazio (arquivos novos sem commits prévios ou arquivos binários), o código anteriormente executava:
     `result.warnings.append(__("File {path}: no blame history found (new or binary file?)", path=file_path))`
   - Em PRs com múltiplos arquivos novos (ex.: 10 a 50 arquivos), essa lógica gerava dezenas de linhas de alerta amarelo repetitivas, poluindo o terminal do usuário.

3. **Outros Warnings de `ReviewerSuggestionResult.warnings`**:
   - `No added lines to attribute — skipping reviewer suggestion.` (quando o diff não contém adições `+`).
   - `File {path}: too many added segments ({count}), analyzed only the first {limit}.` (quando o número de trechos em um único arquivo ultrapassa o teto anti-abuso `MAX_RANGES_PER_FILE = 40`).
   - Estes dois alertas pontuais são legítimos e raros, devendo ser preservados.

4. **Separação de Responsabilidade (Clean Architecture)**:
   - `ReviewerSuggestionResult` (em `src/reviewer_suggestion.py`) deve expor os dados estruturados de apuração:
     - `files_with_blame: list[str]`
     - `files_without_blame: list[str]`
   - O motor em `src/suggest_reviewers.py` apenas preenche essas listas e não gera warnings individuais para arquivos sem blame.
   - A camada de apresentação em `src/main.py` decide a formatação, cor e condição de exibição.

## 2. Decisões do Grill (Rodada 1)

### Q1 — Formato e Texto da Linha de Resumo
- **Decisão:** Adotar estilo informativo `ℹ️` com mensagem parametrizada pelo catálogo i18n:
  - Base em inglês: `"ℹ️ Blame analysis: {with_count} file(s) with blame, {without_count} without blame (new or binary)."`
  - Tradução pt-BR: `"ℹ️ Análise de blame: {with_count} arquivo(s) com blame, {without_count} sem blame (novos ou binários)."`
  - Traduções correspondentes em `pt_pt`, `es_es` e `fr_fr`.

### Q2 — Condição de Exibição da Linha de Resumo
- **Decisão:** Exibir a linha de resumo **apenas quando houver ao menos 1 arquivo sem blame** (`len(suggestion_result.files_without_blame) > 0`). Quando todos os arquivos modificados possuírem histórico normal de blame, nenhuma linha extra é impressa, mantendo o terminal limpo e conciso.

### Q3 — Estrutura de Dados em `ReviewerSuggestionResult`
- **Decisão:** Adicionar campos explícitos no dataclass:
  ```python
  files_with_blame: list[str] = field(default_factory=list)
  files_without_blame: list[str] = field(default_factory=list)
  ```
  O motor adiciona cada caminho de arquivo na respectiva lista e remove os warnings individuais de `result.warnings`.

### Q4 — Preservação de Outros Avisos
- **Decisão:** Manter inalterados quaisquer outros avisos em `result.warnings` (diff sem linhas adicionadas ou estouro de segmentos).

### Q5 — Modelagem de Domínio (`CONTEXT.md`) e ADR
- **Decisão:** Registrar o termo **Blame summary** no glossário `CONTEXT.md`. Dispensar ADR por se tratar de um refinamento de UX de console sem impacto no modelo ou contratos de API da forge.
