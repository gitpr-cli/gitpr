# Plano — Modal de progresso animado ao confirmar o merge do PR

## Contexto

O fluxo de commit já exibe `CommitProgressScreen` com barra animada, linha de status e mensagens de progresso. O merge do PR (`_on_merge_prompt_result` → `_do_merge`) apenas iniciava uma thread, sem empilhar tela alguma: o TUI editável permanecia visível por segundos sem feedback. O auto-merge (`GITPR_AUTO_MERGE`) cai no mesmo caminho.

## Decisões (grilling)

1. **Escopo:** merge manual + auto-merge, ambos via `_do_merge`.
2. **Componente:** reutilizar `CommitProgressScreen` com parâmetro opcional `title`; `mark_finished(show_close=False)` para o sucesso.
3. **Exibição:** imediata ao iniciar o merge.
4. **Sucesso:** status `✅ PR #{number} merged successfully!`, barra completa, sem Close, fecha sozinho após 1,2 s e segue para `_prompt_open_browser`.
5. **Falha:** fecha o progresso e reutiliza `_on_merge_failure`; exceções inesperadas também são roteadas para a falha (status 0).
6. **Textos:** título `🔄 Merging Pull Request...` e status inicial `🔄 Merging PR #{number} on {provider}...`, usando `provider_display_name()`.

## Implementação

- `src/ui/pr_publish_app.py`
  - `CommitProgressScreen.__init__`: novo `title=None`.
  - `compose`: `self._title or __("📦 Processing commit...")`.
  - `mark_finished(show_close=True)`.
  - `PrPublishApp.__init__`: `_merge_progress_screen = None`.
  - `_do_merge`: empilha o modal e inicia a thread pelo `work_callback` do `on_mount` (0,3 s), evitando a corrida entre `call_from_thread` e a composição da tela; captura `ScmProviderError` e `Exception` genérica.
  - `_on_merge_success(pr_number, pr_url)`: status de sucesso + `mark_finished(show_close=False)` + timer de 1,2 s.
  - `_finish_merge_success(pr_url)`: pop guardado por identidade de tela e segue para o prompt de navegador.
  - `_on_merge_failure`: pop guardado antes do modal de erro existente.
- `langs/*.json` (6 arquivos): três novas chaves traduzidas, exigência de paridade do `tests/test_i18n.py`.
- `tests/test_pr_publish_app.py`: 10 testes (modal genérico + fluxos manual/auto, sucesso, conflito 405, exceção inesperada e dispensa antecipada).

## Verificação

- `python -m pytest tests/test_pr_publish_app.py -v -k "CommitProgressScreen or MergeProgress"`
- `python -m pytest tests/test_pr_publish_app.py tests/test_pr_publish_linter_modal.py`
- `python -m pytest tests/ -q` (falhas restantes são pré-existentes: i18n e badge).
