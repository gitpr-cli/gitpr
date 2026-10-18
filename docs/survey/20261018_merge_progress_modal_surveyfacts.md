# Survey — Feedback animado no merge do PR

## Contexto da tarefa

Usuário relatou: ao confirmar um commit, o modal animado com mensagens aparece; ao confirmar o merge do PR, o modal não aparece e o TUI com os textos do PR permanece visível e editável por alguns segundos, sem indicar o que está acontecendo. Pedido: exibir o mesmo modal animado com os textos do que está sendo feito.

## Fatos levantados

### Fluxo de commit (referência de UX)

- `CommitProgressScreen` em `src/ui/pr_publish_app.py` (linha 364 antes das mudanças): `ModalScreen` com barra de blocos animada por `set_interval(0.05, _tick_animation)`.
- Título fixo `📦 Processing commit...` em `compose`.
- Linha de status única `#progress_status`, atualizada por `add_log()`.
- `mark_finished()` para a animação, preenche a barra e exibe/foca o botão Close.
- Trabalho iniciado pelo `work_callback` agendado no `on_mount` (0,3 s), garantindo que a tela esteja montada antes de qualquer callback.
- Fluxos: `_start_progress_and_commit` (linter + mensagem) e `_start_commit_and_publish` (commit + push + criação do PR).

### Fluxo de merge (problema)

- `_prompt_merge` empilha `CommitConfirmScreen` com "Yes, Merge Now".
- `_on_merge_prompt_result("yes")` chama `_do_merge`.
- `_do_merge` apenas inicia `threading.Thread(target=_merge, daemon=True)`; nenhuma tela é empilhada.
- `_merge` chama `provider.merge_pull_request` (HTTP síncrono, timeout de 15 s) e só então usa `call_from_thread` para `_on_merge_success`/`_on_merge_failure`.
- Resultado: o TUI principal (título/corpo editáveis) fica na frente, sem modal nem status, até o HTTP terminar.
- `_after_attach_continue` com `GITPR_AUTO_MERGE` chama `_do_merge` direto — mesmo problema.
- Exceções diferentes de `ScmProviderError` matavam a thread em silêncio; com um modal, ficaria animando para sempre.
- `src/spinner.py` (spinner do CLI) escreve ANSI em `sys.stdout` e não pode ser reutilizado dentro do Textual; a prática do projeto é `set_interval` + `Static.update()`.

### Testes e i18n

- Padrões existentes: `_ModalHostApp` + `run_test`/`pilot.pause` para modais isolados; `_make_app` + `_Recorder` para o fluxo completo.
- `tests/test_i18n.py` exige o mesmo conjunto de chaves nos seis arquivos de idioma (`pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr`) e que toda chave `__()` exista em todos.
- Dívida pré-existente confirmada (não causada por esta task): 8 chaves `__()` ausentes nos seis arquivos; 2 chaves órfãs em quatro arquivos; `es.json`/`fr.json` sem essas duas órfãs (paridade já falhava).

## Rodadas de decisão

### Rodada 1

- **Escopo:** merge manual + auto-merge. (Recomendado e aceito.)
- **Componente:** reutilizar `CommitProgressScreen` com título opcional. (Recomendado e aceito.)
- **Sucesso:** mostrar mensagem e fechar sozinho. (Recomendado e aceito.)
- **Falha:** usar o modal de erro existente, capturando também exceções inesperadas. (Recomendado e aceito.)

### Rodada 2

- **Textos:** com nome do provider — título `🔄 Merging Pull Request...`, status inicial `🔄 Merging PR #{number} on {provider}...`, sucesso `✅ PR #{number} merged successfully!`. (Recomendado e aceito.)
- **Duração do sucesso:** 1,2 s (usuário escolheu; recomendação era 0,8 s).
- **Aparecer:** imediatamente. (Recomendado e aceito.)

## Execução

- `CommitProgressScreen`: `title` opcional e `mark_finished(show_close=...)`.
- `_do_merge`: modal empilhado e worker iniciado pelo `work_callback` do `on_mount`; `except Exception` roteia para a falha com status 0.
- `_on_merge_success`: status de sucesso, barra completa, sem Close, timer de 1,2 s.
- `_finish_merge_success`: pop guardado por identidade de tela + `_prompt_open_browser`.
- `_on_merge_failure`: pop guardado + modal existente.
- Traduções nas seis línguas.
- 10 testes novos; todos passam.

## Verificação

- Novos testes: 10 passed.
- `test_pr_publish_app.py` + `test_pr_publish_linter_modal.py`: todos passam.
- Suíte completa: 2940 passed, 10 failed — 3 de i18n e 7 de badge, todos pré-existentes e sem relação com a mudança.
