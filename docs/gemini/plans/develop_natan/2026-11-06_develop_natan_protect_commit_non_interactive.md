# Implementation Plan — Proteger `-c` em Execução Não Interativa

- **Date:** 2026-11-06
- **Branch:** develop_natan
- **Plan Name:** protect_commit_non_interactive

---

## 1. Context and Problem Statement

O comando `gitpr -c` (`--commit`) foi configurado para invocar a TUI `CommitApp` em qualquer chamada sem a flag interna `--hook` (`main.py:1650-1661`).
Como consequência, chamadas originadas de ambientes não interativos (como `CliRunner`, scripts em shell, cron, pipes e CI) entram em `app.run()`, que trava indefinidamente por ausência de um terminal interativo (Interactive run).

Nesta suíte de testes, o teste `test_a_flow_that_never_enforced_it_is_untouched` em `tests/integration/test_baseline_effect_on_review_linter_risk.py` executa `gitpr -c --no-unstaged-check` via `CliRunner` e congela em ~33% da execução total do pytest.

Além disso, a implementação original de console em `main.py` (linhas 1767-1775) tornou-se código inalcançável porque o bloco de `CommitApp` finalizava com `return`.

## 2. Proposed Changes

### [MODIFY] `src/main.py`
Substituir a guarda `if hook:` no bloco `elif commit:` (linhas 1648-1675) para verificar `if may_ask:`, aproveitando a verificação canônica `may_ask = _may_ask_the_user(quiet=quiet, hook=hook, mcp=mcp)` calculada na linha 813.

No ramo `else` (não interativo):
- Se `hook`: verifica se há merge em andamento (`is_merge_in_progress()`) e sai silenciosamente.
- Se não for `hook`: verifica arquivos unstaged via `check_unstaged_files("commit", skip_check=no_unstaged_check, quiet=quiet, interactive=False)`.
- Captura `diff_text = get_git_diff()`.
- O processamento comum em seguida chama a IA (`generate_pr_content`) e, na saída de `action_type == "commit"` (linhas 1746-1775), escreve no arquivo do hook se `hook` estiver presente, ou exibe no console (`📝 Commit Suggestion:`) se não estiver em hook.

### [MODIFY] `tests/test_commit_app.py`
Adicionar testes para cobrir o roteamento do `cli()` com `-c`:
- `test_commit_interactive_launches_commit_app`: quando `may_ask` é True, o `CommitApp` é invocado.
- `test_commit_non_interactive_runs_console_mode`: quando chamado via `CliRunner` sem hook, não abre `CommitApp` e imprime a sugestão no stdout.
- `test_commit_non_interactive_checks_unstaged`: valida que arquivos unstaged são checados e respeitam `--no-unstaged-check`.

## 3. Verification Plan
- Executar `tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched`.
- Executar `tests/test_commit_app.py`.
- Executar a suíte de testes completa para garantir estabilidade.
