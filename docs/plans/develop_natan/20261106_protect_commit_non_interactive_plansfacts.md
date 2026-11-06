# Plano de Execução — Proteger `-c` em Execução Não Interativa (Interactive Run Guard)

- **Data:** 2026-11-06
- **Branch:** develop_natan
- **Task:** protect_commit_non_interactive

---

## 1. Objetivo

Restaurar a guarda de terminal (*interactive run*) na rota do comando `gitpr -c`, garantindo que:
1. `CommitApp` seja instanciado e executado **apenas** quando `may_ask` for verdadeiro (terminal interativo com `stdin` e `stdout` TTY, sem quiet/hook/mcp).
2. Em execuções não interativas sem `--hook` (ex.: chamadas via `CliRunner`, scripts e CI), o fluxo execute o pipeline não interativo de console, gerando a mensagem via IA e exibindo a sugestão via stdout.
3. Se houver merge em andamento e estiver em `--hook`, encerre silenciosamente (o git gerencia a mensagem).
4. Em execuções não interativas sem `--hook`, arquivos unstaged sejam validados via `check_unstaged_files("commit", skip_check=no_unstaged_check, quiet=quiet, interactive=False)`.
5. Destravar o teste `test_a_flow_that_never_enforced_it_is_untouched` e adicionar testes de regressão específicos para o roteamento interativo vs. não interativo.

---

## 2. Modificações Planejadas

### `src/main.py`
Substituir a verificação de `if hook:` no bloco `elif commit:` por:

```python
    elif commit:
        action_type = "commit"
        if may_ask:
            # Interactive commit TUI flow
            from src.ui.commit_app import CommitApp

            app = CommitApp(
                provider=active_provider, skip_unstaged=no_unstaged_check
            )
            app.run()
            if app.result == "no_changes":
                click.secho(
                    __(
                        "\n⚠️ No new code found. Make some changes or check your branch before running the command.\n"
                    ),
                    fg="yellow",
                )
            elif app.result == "committed":
                click.secho(
                    __("\n✅ Commit created successfully!\n"), fg="green", bold=True
                )
                if app._commit_output and app._commit_output.strip():
                    click.echo(app._commit_output.strip() + "\n")
            return
        else:
            # Non-interactive / Hook / CI / Pipe flow
            if hook:
                if is_merge_in_progress():
                    return  # merge in progress: git owns the message, skip AI silently
            else:
                if not check_unstaged_files(
                    "commit", skip_check=no_unstaged_check, quiet=quiet, interactive=False
                ):
                    return
            diff_text = get_git_diff()
```

### `tests/test_commit_app.py`
Adicionar testes unitários/de integração verificando:
1. `gitpr -c` com `may_ask=True` instancia `CommitApp` e chama `app.run()`.
2. `gitpr -c` com `may_ask=False` sem `--hook` não instancia `CommitApp`, executa `generate_pr_content` e imprime a sugestão.
3. `gitpr -c` com `may_ask=False` com arquivos unstaged sem `--no-unstaged-check` é bloqueado por `check_unstaged_files`.

---

## 3. Critérios de Sucesso e Verificação

1. `test_a_flow_that_never_enforced_it_is_untouched` em `tests/integration/test_baseline_effect_on_review_linter_risk.py` passa sem travar.
2. Novos testes em `tests/test_commit_app.py` cobrem a alternância interativa vs. não interativa.
3. A suíte completa de testes passa sem regressões.
