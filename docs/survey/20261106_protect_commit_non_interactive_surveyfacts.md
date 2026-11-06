# Survey Facts — Proteger `-c` em Execução Não Interativa (Interactive Run Guard)

- **Data:** 2026-11-06
- **Branch:** develop_natan
- **Task:** protect_commit_non_interactive

---

## 1. Contexto do Problema

O comando `gitpr -c` (`--commit`) foi originalmente concebido como um comando de console capaz de operar tanto em terminal interativo quanto em automações (hooks, CI, scripts de shell, `CliRunner`).

Com a introdução da interface gráfica em terminal [`CommitApp`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ui/commit_app.py) baseada em Textual, a rota do `commit` em [`src/main.py:1648-1675`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py#L1648-L1675) foi alterada para:

```python
    elif commit:
        action_type = "commit"
        if hook:
            if is_merge_in_progress():
                return  # merge in progress: git owns the message, skip AI silently
            diff_text = get_git_diff()
        else:
            # Interactive commit TUI flow
            from src.ui.commit_app import CommitApp

            app = CommitApp(
                provider=active_provider, skip_unstaged=no_unstaged_check
            )
            app.run()
            ...
            return
```

### Sintoma e Custo Real
Sem a passagem da flag interna `--hook`, qualquer invocação de `gitpr -c` tentava instanciar e executar `app.run()`. Em ambientes não interativos (como no runner de testes do Click `CliRunner`, em pipelines de CI, cron jobs ou pipes), `app.run()` não retorna, travando o processo indefinidamente.

Isso travava a suíte de testes em aproximadamente 33% da execução ao atingir o teste:
`tests/integration/test_baseline_effect_on_review_linter_risk.py::TestAnUnusableBaseline::test_a_flow_that_never_enforced_it_is_untouched`
que executa:
```python
with self.stubbed_ai():
    result = self.run_cli("-c", "--no-unstaged-check")
self.assertEqual(result.exit_code, 0, result.output)
self.assertIn("chore: stubbed", result.output)
```

Além disso, as linhas 1767–1775 de [`src/main.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py#L1767-L1775) continham código morto (`CONSOLE MODE: The original existing behavior`), pois o bloco `else` anterior sempre chamava `return` antes de qualquer fluxo de console ser atingido.

---

## 2. Fatos Levantados na Investigação

1. **Guarda canônica de terminal**:
   [`src/main.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/main.py#L64-L77) já define:
   ```python
   def _may_ask_the_user(quiet=False, hook=False, mcp=False):
       if quiet or hook or mcp:
           return False
       try:
           return sys.stdin.isatty() and sys.stdout.isatty()
       except Exception:
           return False
   ```
   E na linha 813 inicializa:
   `may_ask = _may_ask_the_user(quiet=quiet, hook=hook, mcp=mcp)`
   Essa variável já está disponível no escopo da função `cli()`.

2. **Alinhamento com o Vocabulário de Domínio ([`CONTEXT.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md#L29-L33))**:
   - Termo canônico: **Interactive run** ("A run attached to a terminal at both ends that is allowed to stop and ask the user. Scripts, pipes, hooks and the MCP server are never interactive. Avoid: CLI mode, TTY run").

3. **Verificação de Unstaged**:
   Para `--review` e `--fullreview`, o CLI utiliza:
   `check_unstaged_files(action, skip_check=no_unstaged_check, quiet=quiet, interactive=False)`
   No fluxo não interativo do `commit`, essa mesma proteção deve ser aplicada quando não estiver em modo `--hook`.

---

## 3. Decisões do Grill (Rodada 1)

- **Q1 (Critério de guarda para `CommitApp`)**:
  - **Decisão**: Usar `if may_ask:`. Se `may_ask` for verdadeiro (terminal interativo, sem quiet, sem hook, sem mcp), abre o `CommitApp`. Caso contrário, segue para o pipeline não interativo.
- **Q2 (Comportamento sem `--hook` em modo não interativo)**:
  - **Decisão**: Restaurar o fluxo de console em `main.py` (linhas 1767-1775), exibindo a sugestão gerada pela IA via `click.echo(msg)`.
- **Q3 (Unstaged files em modo não interativo)**:
  - **Decisão**: Executar `check_unstaged_files("commit", skip_check=no_unstaged_check, quiet=quiet, interactive=False)` no ramo não interativo fora de hook.
