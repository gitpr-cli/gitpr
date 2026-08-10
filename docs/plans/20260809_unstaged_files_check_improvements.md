# Plano: Melhorias na Listagem e Verificação de Arquivos Unstaged

**Data:** 2026-08-09
**Branch:** develop_natan
**Status:** Aguardando aprovação

---

## Contexto

O GitPR já possui `get_unstaged_files()` em `src/core.py` que usa `git status --porcelain` para listar arquivos fora do stage (untracked `??`, modified ` M`, deleted ` D`). Porém:

1. A verificação de unstaged **só roda na geração de PR** — comandos `-c` (commit), `-r` (review), `-f` (fullreview) e `-is` (issue) não avisam sobre arquivos fora do stage
2. O MCP `analyze_diff` tem descrição enganosa ("unstaged") — `git diff HEAD` inclui staged + unstaged
3. Não há ferramenta MCP dedicada para listar arquivos unstaged como JSON categorizado
4. Não há flag CLI `--status` para listagem rápida sem AI
5. Labels de status combinados (`MM`, `AM`, `MD`) não são normalizados

## Objetivo

- Estender a verificação de unstaged para **todos** os comandos: `-c`, `-r`, `-f`, `-is`
- Nova tool MCP `list_unstaged_files` com 3 listas: `new`, `modified`, `deleted`
- Corrigir descrições e adicionar `analyze_unstaged_diff` (diff só do working tree)
- Nova flag CLI `--status` para listagem sem AI
- Normalizar labels de status no `get_unstaged_files()`

---

## Fase 1: Fundações em `src/core.py`

### 1.1 Normalizar labels no `get_unstaged_files()` (linha 1027)

Substituir o `dict.get(..., fallback)` por lógica explícita:

```python
if status_x == "?" and status_y == "?":
    status_label = "new"
elif status_y == "M":
    status_label = "mod"
else:  # status_y == "D"
    status_label = "del"
```

Isso garante que códigos combinados (`MM`, `AM`, `MD`, `AD`, `RM`, `RD`) sejam normalizados para `mod`/`del`.

### 1.2 Nova função `get_unstaged_categorized()`

Retorna `{"new": [...], "modified": [...], "deleted": [...]}` — fonte única de verdade para categorização. Usa `get_unstaged_files()` internamente.

### 1.3 Nova função `get_unstaged_diff(quiet=False)`

Usa `git diff -U1 -w -M -B --` (sem `HEAD` — compara index vs working tree). Retorna **apenas** mudanças unstaged, excluindo staged. Reutiliza `SMART_EXCLUDES`.

### 1.4 Nova função `get_uncommitted_summary()`

Retorna `{"staged": [...], "unstaged": [...], "untracked": [...]}` — visão completa do estado do repositório. Um arquivo pode aparecer em ambas as listas `staged` e `unstaged` (ex: `AM`).

`has_uncommitted_changes()` permanece inalterado (bool, retrocompatível).

---

## Fase 2: `src/mcp_server.py`

### 2.1 Corrigir descrição do `analyze_diff` (linha 268)

De: `"Get the current unstaged git diff (git diff HEAD)."`
Para: `"Get the current uncommitted git diff (git diff HEAD — includes both staged and unstaged changes)."`

### 2.2 Nova tool `list_unstaged_files`

Retorna JSON:
```json
{
  "status": "changes_found",
  "new": ["untracked_file.py"],
  "modified": ["edited_file.py"],
  "deleted": ["removed_file.py"],
  "total": 3,
  "message": ""
}
```

### 2.3 Nova tool `analyze_unstaged_diff`

Usa `get_unstaged_diff()` — retorna diff apenas do que está modificado na working tree (exclui staged). Descrição deixa claro que arquivos untracked não aparecem no diff (usar `list_unstaged_files` para esses).

---

## Fase 3: `src/main.py` — CLI

### 3.1 Novas flags

```python
@click.option('--status', is_flag=True,
    help=__("Lists uncommitted file changes (new/modified/deleted) without AI processing."))
@click.option('--no-unstaged-check', is_flag=True,
    help=__("Skips the unstaged files verification before AI processing."))
```

Adicionar `status` e `no_unstaged_check` na assinatura de `cli()` e no `HELP_MAP`/`HELP_PRIORITY`.

### 3.2 Helper `check_unstaged_files(action_type, skip_check, quiet, interactive)`

Função compartilhada que centraliza a verificação:

| `action_type` | Comportamento |
|---------------|---------------|
| `"pr"` | Fluxo existente (TUI ou auto-stage) — movido verbatim de linhas 731-766 |
| `"commit"` | Avisa que arquivos unstaged **NÃO** entrarão no commit. Auto-stage se `GITPR_AUTO_STAGE=true` |
| `"review"`, `"fullreview"`, `"issue"` | Aviso informativo (o diff já inclui esses arquivos). **Nunca** faz auto-stage |

Respeita `GITPR_SKIP_UNSTAGED_CHECK`, `GITPR_AUTO_STAGE`, `--no-unstaged-check` e `--quiet`.
**Nunca** executa em modo hook (`--hook`) para não travar `prepare-commit-msg`.

### 3.3 Wire nos comandos

```python
elif commit:
    if not hook and not check_unstaged_files("commit", ...):
        return
    diff_text = get_git_diff()
elif review:
    if not hook and not check_unstaged_files("review", ...):
        return
    diff_text = get_git_diff()
elif fullreview:
    if not hook and not check_unstaged_files("fullreview", ...):
        return
    diff_text = get_git_full_diff()
```

Issue (modo diff): inserir `check_unstaged_files("issue", ...)` antes de `get_git_diff()` na linha 588.

PR (default): substituir o bloco inline das linhas 731-766 pela chamada ao helper.

### 3.4 Rota `--status`

Inserir após o bloco de plugins (linha 355), antes do banner:
- Chama `get_unstaged_categorized()`
- Imprime as 3 categorias com emojis (➕ novos, ✏️ modificados, 🗑️ deletados)
- Retorna imediatamente — sem AI, sem rede, sem git fetch

---

## Fase 4: i18n

Novas chaves em inglês (a sincronizar via `python tests/sync_i18n.py`):

- Descrições das flags `--status` e `--no-unstaged-check`
- Descrições das tools MCP `list_unstaged_files` e `analyze_unstaged_diff`
- Descrição corrigida do `analyze_diff`
- Headers de categoria: `➕ New files ({count})`, `✏️ Modified files ({count})`, `🗑️ Deleted files ({count})`
- Mensagens de aviso para `-c`, `-r/-f/-is`
- Texto do `HELP_MAP` para as novas flags

Chaves existentes do fluxo de PR são **reutilizadas** (sem novas traduções necessárias).

---

## Fase 5: Testes

### `tests/test_core.py`
- `get_unstaged_files()`: mock `git status --porcelain` com fixtures `??`, ` M`, ` D`, `AM`, `MM`, `MD`, `AD`, `A `, `UU` — verificar labels canônicos
- `get_unstaged_categorized()`: verificar agrupamento correto nas 3 listas
- `get_unstaged_diff()`: assert comando sem `HEAD`, stdout passthrough, erro → `None`
- `get_uncommitted_summary()`: `A ` → só staged; `AM` → ambos; `??` → untracked

### `tests/test_mcp_server.py`
- `list_unstaged_files`: patch `get_unstaged_categorized`, assert JSON shape e variante vazia
- `analyze_unstaged_diff`: patch `get_unstaged_diff`, assert JSON shape
- `analyze_diff`: assert que descrição não contém mais "unstaged"

---

## Fase 6: Documentação

Seguir o workflow da skill `new-feature`:

1. Novo `docs/git-status.md` + 4 traduções — documenta `--status`, `--no-unstaged-check`, env vars, e tools MCP
2. Atualizar `README.md` + traduções com as novas flags
3. Atualizar `docs/mcp-integration.md` + traduções com `list_unstaged_files` e `analyze_unstaged_diff`
4. `CHANGELOG.md`: entrada resumindo todas as mudanças

---

## Arquivos modificados

| Arquivo | Tipo de mudança |
|---------|-----------------|
| `src/core.py` | feat: normalizar labels + 3 novas funções |
| `src/mcp_server.py` | feat: 2 novas tools + correção de descrição |
| `src/main.py` | feat: 2 novas flags + helper + wire em 5 comandos |
| `tests/test_core.py` | test: cobertura para funções novas/modificadas |
| `tests/test_mcp_server.py` | test: cobertura para novas tools MCP |
| `langs/*.json` (6 arquivos) | i18n: novas chaves (via sync_i18n.py) |
| `docs/git-status.md` + 4 traduções | docs: nova página |
| `README.md` + 4 traduções | docs: atualização |
| `docs/mcp-integration.md` + 4 traduções | docs: atualização |
| `CHANGELOG.md` | docs: entrada |

---

## Riscos e edge cases

1. **Hook mode**: `check_unstaged_files()` NUNCA executa com `--hook` — um prompt travaria o `git commit`
2. **Fresh repo (0 commits)**: `get_unstaged_diff()` funciona sem `HEAD`; `get_git_diff()` falharia — a nova função é mais segura
3. **Merge conflicts (`UU`)**: coluna Y = `U`, corretamente excluído de todas as categorias
4. **Renames (`R `)**: `line[3:]` pode capturar `old -> new` como path — limitação pré-existente, documentada
5. **Auto-stage safety**: `GITPR_AUTO_STAGE` NÃO faz stage para review/fullreview/issue (mutação de index durante comando de leitura seria surpreendente)
6. **Untracked invisível no diff**: `analyze_unstaged_diff` nunca mostra `??` — documentado; usar `list_unstaged_files`
7. **TUI display**: labels normalizados (`[MM]` → `[mod]`) — melhoria cosmética no `FileStageScreen`
8. **Double warning**: `get_git_diff()` já avisa sobre untracked; novo check imprime seu próprio resumo — complementar, não redundante

---

## Verificação

1. `gitpr --status` — lista categorizada sem AI
2. `gitpr -c` com arquivos unstaged — warning + prossegue (ou auto-stage se configurado)
3. `gitpr -r` com arquivos unstaged — warning informativo + prossegue
4. `gitpr -f` com arquivos unstaged — warning informativo + prossegue
5. `gitpr -is` com arquivos unstaged — warning informativo + prossegue
6. `gitpr` (PR) — fluxo existente preservado (TUI/auto-stage)
7. `gitpr -c --no-unstaged-check` — silencia a verificação
8. `GITPR_SKIP_UNSTAGED_CHECK=true gitpr -c` — silencia a verificação
9. `gitpr -c --hook` — NÃO executa verificação (protege prepare-commit-msg)
10. MCP `list_unstaged_files` — retorna JSON com `new`/`modified`/`deleted`
11. MCP `analyze_unstaged_diff` — retorna diff só do working tree
12. MCP `analyze_diff` — descrição corrigida
13. `python -m pytest tests/ -v` — todos os testes passam

## Documentação

Crie um arquivo com esta nova implementação em docs/, lembre-se de criar nos outros idiomas
Verifique se na documentação @docs\untracked-files.md tem alguma modificação a fazer.
Adicione ao README.md as novas mudanças
Verifuqe na documentação do Pull Request Publication @docs\pull-request-publication.md se tem algo a refatorar sobre.