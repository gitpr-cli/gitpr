# Plan: Inversão da Interface de Publicação + Auto-Commit com Lint

## Context

O plano `20260807_altera_interface_pullrequest_auto.md` define 8 regras de desenvolvimento. Este plano traduz essas regras em alterações concretas no código.

**Estado atual (working tree):** A TUI já abre por padrão após `gitpr` (linhas 803-859 de `main.py`). Os flags `--publish` e `--no-edit` existiam no staged/index mas foram removidos da working tree — ou seja, a inversão "publicar por padrão" já está parcialmente implementada. Porém:
- Os flags `--no-publish` e `--no-edit` precisam ser **adicionados** (não existem na working tree)
- Não existe fluxo de auto-commit — o usuário precisa commitar manualmente
- O código **nunca** executou `git commit` via Python (será a primeira vez)
- Documentação, i18n e READMEs ainda referenciam `--publish` como flag necessário

**Objetivo:**
1. Padrão: `gitpr` → gera PR + abre TUI (já funciona assim ✅)
2. `--no-publish` → gera PR + salva `.md` + sai (sem TUI) — NOVO
3. `--no-edit` → gera PR + auto-commit (com lint) + publica direto no GitHub — NOVO
4. TUI F3 → executa auto-commit flow antes de publicar — NOVO
5. Novas env vars: `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT` — NOVO

---

## Arquivos a Modificar (em ordem de implementação)

### 1. `src/core.py` — Novos helpers

Adicionar duas funções ao final do arquivo:

```python
def has_uncommitted_changes():
    """Returns True if there are uncommitted changes (staged or unstaged)."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--stat"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        return bool(result.stdout.strip())
    except Exception:
        return False

def execute_git_commit(message, no_verify=False):
    """Executes git commit -m with optional --no-verify. Returns (success: bool, output: str)."""
    cmd = ["git", "commit", "-m", message]
    if no_verify:
        cmd.insert(2, "--no-verify")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, str(e))
```

### 2. `src/config.py` — Novas env vars

Adicionar a `DEFAULT_CONFIG`:
```python
"GITPR_AUTO_COMMIT": "false",
"GITPR_SKIP_LINT": "false",
```

### 3. `src/main.py` — Principal: flags, fluxo, e auto-commit CLI

#### 3a. Novas flags Click (no decorator `@click.command`)

Adicionar antes de `--base`:
```python
@click.option('--no-publish', is_flag=True, help=__("Saves the PR file locally without opening the interactive publisher."))
@click.option('--no-edit', is_flag=True, help=__("Skips the interactive editor and publishes the Pull Request directly (with auto-commit)."))
```

#### 3b. Atualizar banner (linha ~47)

Remover referência a `--publish`; o comportamento padrão já inclui a TUI.

#### 3c. Adicionar entradas no HELP_MAP

```python
'no-publish': {
    'url': get_doc_url('pull-request-publication.md'),
    'title': __('Skip Interactive Publisher (--no-publish)'),
    'description': __('Generates the PR description and saves it locally without opening the interactive TUI.'),
},
'no-edit': {
    'url': get_doc_url('pull-request-publication.md'),
    'title': __('Direct Publish with Auto-Commit (--no-edit)'),
    'description': __('Generates the PR, auto-commits pending changes (with lint validation), and publishes directly to GitHub without opening the TUI.'),
},
```

#### 3d. Modificar função `cli` — adicionar `no_publish` e `no_edit` como parâmetros

#### 3e. Modificar bloco PR padrão (linhas ~781–859)

Reestruturar para:
```python
# Default Pull Request (.md file) - salva arquivo
output_filename = ...
# ... (salvamento do .md — igual ao atual, linhas 781-800)

# ── PR Publisher logic ──
if no_publish:
    # Apenas salva localmente, sai
    if not quiet:
        print_update_notice()
    return

# Auto-commit flow (para --no-edit)
if no_edit:
    # Verifica alterações, roda lint, gera commit msg, commita
    if not _run_auto_commit_cli(active_provider):
        return  # commit cancelado pelo usuário
    # Publica direto via API
    _publish_pr_directly(pr_data, repo_info, github_token, target_base, output_filename)
    if not quiet:
        print_update_notice()
    return

# Default: abre TUI (código existente, linhas 803-859)
# ... TUI code unchanged ...
```

#### 3f. Nova função `_run_auto_commit_cli(provider)` em main.py

```python
def _run_auto_commit_cli(provider):
    """Auto-commit flow for --no-edit mode. Returns True if commit succeeded or no changes."""
    from src.core import has_uncommitted_changes, execute_git_commit
    from src.linter_engine import parse_diff_and_lint

    if not has_uncommitted_changes():
        return True  # nada a commitar, prossegue

    skip_lint = os.getenv("GITPR_SKIP_LINT", "false").lower() == "true"
    auto_commit = os.getenv("GITPR_AUTO_COMMIT", "false").lower() == "true"

    # Linter
    no_verify = False
    if not skip_lint:
        click.secho("🔍 " + __("Running linter..."), fg="cyan")
        diff_text = get_git_diff()
        linter_results = parse_diff_and_lint(diff_text)
        has_errors = len(linter_results["errors"]) > 0
        has_warnings = len(linter_results["warnings"]) > 0

        if has_warnings:
            click.secho(__("\n⚠️ Linter generated {count} warning(s):", count=len(linter_results['warnings'])), fg="yellow")
            for w in linter_results["warnings"]:
                click.echo(f"  - {w}")

        if has_errors:
            click.secho(__("\n🚨 Linter found {count} error(s):", count=len(linter_results['errors'])), fg="red")
            for e in linter_results["errors"]:
                click.echo(f"  - {e}")
            if click.confirm(__("\n⚠ Commit with --no-verify anyway?"), default=False):
                no_verify = True
            else:
                click.secho(__("❌ Commit aborted by user."), fg="red")
                return False
        else:
            if has_warnings:
                click.secho(__("\n✅ Linter passed with warnings."), fg="green")
            else:
                click.secho(__("✅ Linter passed — no violations."), fg="green")

    # Gerar mensagem de commit via AI
    click.secho("📝 " + __("Generating commit message..."), fg="cyan")
    diff_text = get_git_diff()
    commit_data = generate_pr_content("commit", "commit", diff_text, provider)
    commit_msg = commit_data.get("commit_message", __("Code update")) if commit_data else __("Code update")

    click.secho(__("\n📝 Commit Message:\n"), fg="green", bold=True)
    click.echo(commit_msg)
    click.echo("")

    if not auto_commit:
        if not click.confirm(__("Proceed with this commit message?"), default=True):
            click.secho(__("❌ Commit cancelled by user."), fg="red")
            return False

    # Executar commit
    click.secho("📦 " + __("Executing commit..."), fg="cyan")
    success, output = execute_git_commit(commit_msg, no_verify=no_verify)
    if success:
        click.secho(__("✅ Commit executed successfully!"), fg="green")
        return True
    else:
        click.secho(__("❌ Commit failed: {output}", output=output), fg="red")
        return False


def _publish_pr_directly(pr_data, repo_info, github_token, target_base, output_filename):
    """Publish PR directly to GitHub without TUI (for --no-edit mode)."""
    from src.github_api import create_pull_request

    commit_msg = pr_data.get("commit_message", "")
    pr_body = pr_data.get("pr_description", "")

    full_body = (
        __("**Recommended Commit Message:**\n")
        + "```text\n"
        + f"{commit_msg}\n"
        + "```\n\n---\n\n"
        + pr_body
    )

    head_branch = get_current_branch()
    click.secho("🚀 " + __("Publishing Pull Request to GitHub..."), fg="cyan")

    ok, data, status = create_pull_request(
        repo_info, github_token, commit_msg, full_body, head_branch, target_base
    )

    if ok:
        pr_url = data.get("url")
        click.secho(__("✅ PR successfully created on GitHub:\n👉 {pr_url}", pr_url=pr_url), fg="green", bold=True)
        from src.metrics import log_command_metric
        log_command_metric(command="pr:publish", status="success", provider="github")
        if click.confirm(__("🔗 Open the Pull Request in your browser?")):
            import webbrowser
            webbrowser.open(pr_url)
    elif status == 401:
        click.secho(__("🔐 GitHub token expired or invalid. Use 'gitpr' (without --no-edit) to re-authenticate interactively."), fg="red")
    else:
        click.secho(__("❌ GitHub API Error ({code}): {msg}", code=status, msg=data.get("message", "")), fg="red")
```

#### 3g. Remover lógica `PR_AUTO_PUBLISH` antiga

A lógica da env var `PR_AUTO_PUBLISH` deve ser removida já que publicação agora é padrão. Verificar se há referências no código.

### 4. `src/ui/pr_publish_app.py` — Auto-commit na TUI (F3)

#### 4a. Modificar `action_publish_pr`

Adicionar fluxo de auto-commit antes da publicação. Como a TUI é Textual (sync), usaremos `self.push_screen` com callbacks para os modais de confirmação.

**Nova estrutura de `action_publish_pr`:**
```python
def action_publish_pr(self):
    """F3: Auto-commit (if needed) then publish PR."""
    from src.core import has_uncommitted_changes

    if has_uncommitted_changes():
        self._start_auto_commit_flow()
    else:
        self._do_publish_pr()
```

#### 4b. Novo método `_start_auto_commit_flow`

Chain de modais:
1. `self.notify("📝 Uncommitted changes detected...")` 
2. Push `CommitConfirmScreen` perguntando "Auto-commit before publishing?"
   - Callback: se Sim → `_run_linter_and_commit()`; se Não → `_do_publish_pr()`; se Cancelar → nada
3. `_run_linter_and_commit()`:
   - Roda linter (sync)
   - Se erros: push modal perguntando `--no-verify`
   - Gera commit msg via AI (sync, com notify de progresso)
   - Push `CommitMessageScreen` mostrando a mensagem para confirmação
   - Callback: se Confirmar → executa commit → `_do_publish_pr()`

#### 4c. Novos ModalScreen widgets

Adicionar ao mesmo arquivo (ou criar `src/ui/pr_commit_screens.py`):

- **`CommitConfirmScreen(ModalScreen)`**: Mensagem + botões [Yes, Commit] [No, Skip] [Cancel]
- **`CommitMessageScreen(ModalScreen)`**: Mostra mensagem de commit + [Confirm] [Cancel]

### 5. `src/ui/pr_publish_help.py` — Atualizar texto de ajuda

Atualizar o texto do modal F1 para refletir o novo fluxo (auto-commit no F3).

### 6. Documentação — `docs/pull-request-publication*.md` (5 arquivos)

Reescrever todos os 5 arquivos (EN, PT-BR, PT-PT, ES, FR) com a nova estrutura:

**Seções principais:**
1. **Comportamento Padrão**: `gitpr` → gera PR + abre TUI
2. **`--no-publish`**: Gera PR e salva localmente (sem TUI)
3. **`--no-edit`**: Gera PR + auto-commit com lint + publica direto
4. **Fluxo de Auto-Commit**: Detalhamento do processo (lint → commit msg → confirmação)
5. **Atalhos da TUI**: F1/F2/F3/Esc (atualizar descrição do F3)
6. **Variáveis de Ambiente**: Tabela com TODAS as env vars (existentes + novas)
   - `GITHUB_TOKEN_ENCRYPTED`, `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`
7. **Exemplos Práticos**: Atualizados com `--no-publish` e `--no-edit`
8. **Fluxograma**: Decisão do linter no auto-commit

### 7. i18n — `langs/*.json` (4 arquivos: pt_br, pt_pt, es_es, fr_fr)

Novas chaves a adicionar em cada arquivo (EN é sempre o source, os outros recebem tradução):

| Chave (EN)                                                                                                                           | PT-BR                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `"Saves the PR file locally without opening the interactive publisher."`                                                             | `"Salva o arquivo do PR localmente sem abrir o publicador interativo."`                                                            |
| `"Skips the interactive editor and publishes the Pull Request directly (with auto-commit)."`                                         | `"Pula o editor interativo e publica o Pull Request diretamente (com auto-commit)."`                                               |
| `"Skip Interactive Publisher (--no-publish)"`                                                                                        | `"Pular Publicador Interativo (--no-publish)"`                                                                                     |
| `"Direct Publish with Auto-Commit (--no-edit)"`                                                                                      | `"Publicação Direta com Auto-Commit (--no-edit)"`                                                                                  |
| `"Generates the PR description and saves it locally without opening the interactive TUI."`                                           | `"Gera a descrição do PR e salva localmente sem abrir a TUI interativa."`                                                          |
| `"Generates the PR, auto-commits pending changes (with lint validation), and publishes directly to GitHub without opening the TUI."` | `"Gera o PR, faz auto-commit das alterações pendentes (com validação do linter) e publica diretamente no GitHub sem abrir a TUI."` |
| `"📝 Generating commit message..."`                                                                                                   | `"📝 Gerando mensagem de commit..."`                                                                                                |
| `"🔍 Running linter..."`                                                                                                              | `"🔍 Executando linter..."`                                                                                                         |
| `"✅ Linter passed — no violations."`                                                                                                 | `"✅ Linter aprovado — sem violações."`                                                                                             |
| `"✅ Linter passed with warnings."`                                                                                                   | `"✅ Linter aprovado com avisos."`                                                                                                  |
| `"\n⚠️ Linter generated {count} warning(s):"`                                                                                         | `"\n⚠️ Linter gerou {count} aviso(s):"`                                                                                             |
| `"\n🚨 Linter found {count} error(s):"`                                                                                               | `"\n🚨 Linter encontrou {count} erro(s):"`                                                                                          |
| `"\n⚠ Commit with --no-verify anyway?"`                                                                                              | `"\n⚠ Fazer commit com --no-verify mesmo assim?"`                                                                                  |
| `"❌ Commit aborted by user."`                                                                                                        | `"❌ Commit abortado pelo usuário."`                                                                                                |
| `"📦 Executing commit..."`                                                                                                            | `"📦 Executando commit..."`                                                                                                         |
| `"✅ Commit executed successfully!"`                                                                                                  | `"✅ Commit executado com sucesso!"`                                                                                                |
| `"❌ Commit failed: {output}"`                                                                                                        | `"❌ Falha no commit: {output}"`                                                                                                    |
| `"Proceed with this commit message?"`                                                                                                | `"Prosseguir com esta mensagem de commit?"`                                                                                        |
| `"❌ Commit cancelled by user."`                                                                                                      | `"❌ Commit cancelado pelo usuário."`                                                                                               |
| `"🚀 Publishing Pull Request to GitHub..."`                                                                                           | `"🚀 Publicando Pull Request no GitHub..."`                                                                                         |
| `"🔐 GitHub token expired or invalid. Use 'gitpr' (without --no-edit) to re-authenticate interactively."`                             | `"🔐 Token do GitHub expirado ou inválido. Use 'gitpr' (sem --no-edit) para reautenticar interativamente."`                         |
| `"Uncommitted changes detected. Auto-commit before publishing?"`                                                                     | `"Alterações não commitadas detectadas. Fazer auto-commit antes de publicar?"`                                                     |
| `"📝 Commit Message:\n"`                                                                                                              | `"📝 Mensagem de Commit:\n"`                                                                                                        |

Também **remover** ou **atualizar** chaves obsoletas:
- `"🔐 GitHub token expired or invalid. Please run --publish without --no-edit to re-authenticate."` → atualizar
- `"⚠️ --no-edit ignored: use it with --publish or set PR_AUTO_PUBLISH=true in ~/.gitpr/.env."` → remover ou atualizar
- `"PR Publication to GitHub (--publish)"` → atualizar para `"PR Publication to GitHub"`
- `"Skips the interactive editor and publishes the Pull Request immediately (requires --publish or PR_AUTO_PUBLISH=true)."` → atualizar

### 8. READMEs — 5 arquivos (README.md, README.pt_br.md, README.pt_pt.md, README.fr_fr.md, README.es_es.md)

Atualizar a linha que menciona `--publish` para refletir o novo comportamento padrão.

---

## Ordem de Implementação

1. `src/core.py` — helpers (sem dependências)
2. `src/config.py` — env vars (sem dependências)
3. `src/main.py` — flags, fluxo CLI, auto-commit CLI
4. `src/ui/pr_publish_app.py` — auto-commit TUI + modais
5. `src/ui/pr_publish_help.py` — atualizar texto F1
6. `langs/*.json` (4 arquivos) — novas chaves i18n
7. `docs/pull-request-publication*.md` (5 arquivos) — documentação
8. `README*.md` (5 arquivos) — referências nos READMEs
9. Relatório da tarefa

---

## Verification

1. `gitpr --no-publish` → gera `.md`, NÃO abre TUI, sai limpo
2. `gitpr --no-edit` (com alterações) → gera `.md`, faz lint, gera commit msg, commita, publica PR
3. `gitpr --no-edit` (sem alterações) → gera `.md`, pula commit, publica PR
4. `gitpr` (padrão) → gera `.md`, abre TUI com F1/F2/F3/Esc
5. TUI F3 (com alterações) → mostra modal de confirmação → commit → publica
6. `gitpr --no-publish -h` → ajuda contextual
7. `GITPR_SKIP_LINT=true gitpr --no-edit` → pula lint mas ainda commita/publica
8. `GITPR_AUTO_COMMIT=true gitpr --no-edit` → commita sem pedir confirmação
9. Testes unitários: `pipenv run pytest -v`
10. Rodar `gitpr -l` para verificar linter
