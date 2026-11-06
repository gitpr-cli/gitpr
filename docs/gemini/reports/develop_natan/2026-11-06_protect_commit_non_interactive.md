## Completion Report — Proteger `-c` em Execução Não Interativa (Interactive Run Guard)

### What was done
- Restaurada a guarda de terminal (`may_ask = _may_ask_the_user(...)`) na rota do comando `gitpr -c` em `src/main.py`.
- No modo interativo (`may_ask == True`), `CommitApp.run()` é disparado.
- No modo não interativo (`may_ask == False`):
  - Verifica merge em andamento se for `--hook`.
  - Verifica arquivos unstaged com `check_unstaged_files("commit", ...)` quando não for `--hook`.
  - Captura `diff_text = get_git_diff()`.
  - Invoca a IA via `generate_pr_content` e exibe a sugestão formatada no console (`📝 Commit Suggestion:`), restaurando a execução em scripts, CI e runners de teste.
- Adicionada a suite de testes `TestCliCommitRouting` em `tests/test_commit_app.py` cobrindo o roteamento interativo vs. não interativo e checagem de unstaged.
- Desbloqueado com sucesso o teste `test_a_flow_that_never_enforced_it_is_untouched` em `tests/integration/test_baseline_effect_on_review_linter_risk.py`, que antes travava a suíte completa de testes em ~33%.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/main.py` | fix | Substitui `if hook:` por `if may_ask:` no comando `commit`, direcionando execuções não interativas para o fluxo de console e validação de unstaged. |
| `tests/test_commit_app.py` | test | Adiciona testes `TestCliCommitRouting` cobrindo o despacho de `CommitApp` no modo interativo, o modo console no não interativo e a checagem de arquivos unstaged. |

### Impact
- **Functionality:** O comando `gitpr -c` agora detecta automaticamente se há terminal interativo (`may_ask`). Em execuções interativas, abre a interface TUI `CommitApp`. Em execuções não interativas (como via pipe `echo | gitpr -c`, automações em CI ou no `CliRunner`), gera a mensagem e a exibe no console em vez de congelar.
- **Performance:** Elimina o travamento de processo infinito que ocorria em ~33% da execução dos testes automatizados.
- **Compatibility:** Totalmente retrocompatível com a API de linha de comando existente, Git Hooks (`--hook`) e opções como `--no-unstaged-check`.

### Next steps (if applicable)
- N/A (item concluído e verificado).
