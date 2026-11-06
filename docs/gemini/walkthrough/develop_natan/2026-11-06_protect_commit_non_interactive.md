# Walkthrough — Proteção do `-c` em Execução Não Interativa

Este walkthrough descreve as mudanças implementadas para restaurar a guarda de terminal (**Interactive run**) no comando `gitpr -c`, garantindo a execução da interface gráfica interativa ([`CommitApp`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ui/commit_app.py)) apenas quando houver um terminal interativo (`may_ask == True`), e restaurando o modo de console para execuções não interativas (CI, scripts, `CliRunner`).

---

## 1. Alterações Realizadas

### [src/main.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py)
- Alterada a guarda de roteamento em `main.py` de `if hook:` para `if may_ask:`.
- No ramo interativo (`may_ask == True`): instancia e executa `CommitApp(provider=active_provider, skip_unstaged=no_unstaged_check)`.
- No ramo não interativo (`may_ask == False`):
  - Se `--hook` estiver presente e houver merge em andamento (`is_merge_in_progress()`), encerra silenciosamente.
  - Se `--hook` não estiver presente, executa `check_unstaged_files("commit", skip_check=no_unstaged_check, quiet=quiet, interactive=False)`.
  - Captura `diff_text = get_git_diff()` e prossegue no pipeline, invocando `generate_pr_content("commit", ...)` e exibindo a sugestão formatada no console (`📝 Commit Suggestion:`) nas linhas 1767–1775.

### [tests/test_commit_app.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/test_commit_app.py)
- Adicionada a classe `TestCliCommitRouting` cobrindo:
  - `test_commit_interactive_launches_commit_app`: valida que com `may_ask=True` o `CommitApp.run()` é disparado.
  - `test_commit_non_interactive_runs_console_mode`: valida que via `CliRunner` sem hook o `CommitApp` não é instanciado, a IA é invocada e a sugestão é impressa com código `0`.
  - `test_commit_non_interactive_checks_unstaged_files`: valida que arquivos unstaged barram a execução não interativa sem `--no-unstaged-check`.

---

## 2. Validação e Testes

### Teste de Integração (antes travava em ~33%)
```bash
python -m pytest tests/integration/test_baseline_effect_on_review_linter_risk.py -k "test_a_flow_that_never_enforced_it_is_untouched" -v
```
**Resultado:**
```text
tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched PASSED [100%]
====================== 1 passed, 33 deselected in 16.84s ======================
```

### Testes Unitários de Roteamento e CommitApp
```bash
python -m pytest tests/test_commit_app.py -v
```
**Resultado:**
```text
tests/test_commit_app.py::TestCommitAppUnit::test_on_mount_pushes_stage_screen_when_unstaged_files_exist PASSED [  5%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_mount_auto_stages_when_env_flag_set PASSED [ 11%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_mount_skips_stage_screen_when_skip_unstaged_true PASSED [ 17%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_stage_done_cancel_aborts PASSED [ 23%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_stage_done_stage_stages_files_and_generates PASSED [ 29%]
tests/test_commit_app.py::TestCommitAppUnit::test_check_diff_and_generate_no_changes_exits PASSED [ 35%]
tests/test_commit_app.py::TestCommitAppUnit::test_check_diff_and_generate_pushes_progress_screen PASSED [ 41%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_commit_msg_ready_pushes_message_screen PASSED [ 47%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_commit_message_result_cancel_aborts PASSED [ 52%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_commit_message_result_confirm_starts_commit PASSED [ 58%]
tests/test_commit_app.py::TestCommitAppUnit::test_run_commit_worker_executes_commit_and_marks_finished PASSED [ 64%]
tests/test_commit_app.py::TestCommitAppUnit::test_on_commit_progress_dismissed_sets_result PASSED [ 70%]
tests/test_commit_app.py::TestCommitAppUnit::test_schedule_auto_exit_sets_timer PASSED [ 76%]
tests/test_commit_app.py::TestCommitAppHeadlessFlow::test_headless_full_flow PASSED [ 82%]
tests/test_commit_app.py::TestCliCommitRouting::test_commit_interactive_launches_commit_app PASSED [ 88%]
tests/test_commit_app.py::TestCliCommitRouting::test_commit_non_interactive_runs_console_mode PASSED [ 94%]
tests/test_commit_app.py::TestCliCommitRouting::test_commit_non_interactive_checks_unstaged_files PASSED [100%]

============================= 17 passed in 6.40s ==============================
```
