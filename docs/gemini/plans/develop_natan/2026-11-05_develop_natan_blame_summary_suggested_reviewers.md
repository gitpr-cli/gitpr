# Implementation Plan — Resumo de Arquivos com e sem Blame na Sugestão de Revisores (`blame_summary_suggested_reviewers`)

- **Data:** 2026-11-05
- **Branch:** `develop_natan`
- **Tarefa:** Substituir linhas repetitivas de avisos por arquivo sem blame por uma única linha de resumo consolidada.

## 1. Visão Geral
Durante o fluxo de publicação de PR, a etapa de sugestão de revisores analisa os trechos de código adicionados no diff unificado através do `git blame`. Quando múltiplos arquivos são novos ou binários, o GitPR atualmente imprime no terminal uma linha de aviso `⚠️ Arquivo {path}: nenhum histórico de blame encontrado...` para cada um deles, o que polui a saída de console.
Este plano consolida essa contagem em uma única linha de resumo informativa (`ℹ️ Análise de blame: X arquivo(s) com blame, Y sem blame (novos ou binários)`), exibida apenas quando há arquivos sem blame.

## 2. Modificações Propostas

### `src/reviewer_suggestion.py`
- Adicionar os campos `files_with_blame: list = field(default_factory=list)` e `files_without_blame: list = field(default_factory=list)` na classe `ReviewerSuggestionResult`.

### `src/suggest_reviewers.py`
- Em `compute_reviewer_suggestions()`:
  - Rastrear listas de arquivos com e sem blame.
  - Remover o `result.warnings.append` individual por arquivo sem histórico.
  - Retornar as listas preenchidas em `ReviewerSuggestionResult`.

### `src/main.py`
- No bloco pós-cálculo de revisores:
  - Se `suggestion_result.files_without_blame` não for vazio, emitir a linha de resumo com a contagem usando `click.secho()`.
  - Continuar emitindo outros `warnings` residuais caso existam.

### `CONTEXT.md`
- Documentar o novo termo de domínio `Blame summary`.

### `langs/*.json` & `src/updater.py`
- Registrar a chave nos arquivos de tradução e incrementar `__lang_version__ = "v0.0.41"`.

### `tests/`
- Atualizar testes de `suggest_reviewers` para verificar os novos atributos `files_with_blame` e `files_without_blame`.
- Adicionar cobertura para a linha de resumo.
