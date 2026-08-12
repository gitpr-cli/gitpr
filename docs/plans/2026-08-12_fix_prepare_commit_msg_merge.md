# Plano — Corrigir sugestão de commit por IA disparada em `git pull`

> Data: 2026-08-12 · Branch: `develop_natan` · Status: **implementado**

## Contexto

Ao rodar `git pull` num repositório com os hooks do GitPR instalados, o hook `prepare-commit-msg` disparava a geração de mensagem de commit por IA para o **merge commit** criado pelo pull. O esperado é que `git pull` apenas **registre o evento nas métricas** — o que já funciona via hook `post-merge` → `gitpr --hook-event "post-merge" --quiet` → `log_command_metric(command="hook:post-merge", ...)` (`src/main.py:298-302`). **Nenhuma mudança em métricas foi necessária.**

### Causa raiz

1. `git pull` com branches divergentes cria um merge commit; o git invoca `prepare-commit-msg` com `$2 = merge`.
2. `scripts/prepare-commit-msg-template.sh:14` só pulava a IA quando `COMMIT_SOURCE = "message"` — não cobria `merge` (nem `squash`/`commit`).
3. O hook chama `gitpr --commit --quiet --hook "$COMMIT_MSG_FILE"`; no modo hook (`src/main.py:790-798`) a mensagem da IA era injetada no topo de `.git/MERGE_MSG`, corrompendo a mensagem de merge (o diff de `git diff HEAD` é não-vazio durante o merge).
4. Não existia detecção de merge em `core.py`/`main.py` (grep por `MERGE_HEAD|MERGE_MSG` não retorna nada em `src/`).

## Mudanças

### 1. Templates — pular fontes de mensagem geradas pelo git (5 idiomas)

`scripts/prepare-commit-msg-template.sh` + variantes `.pt_br.sh`, `.pt_pt.sh`, `.fr.sh`, `.es.sh` — guarda trocada por:

```sh
# Skip AI for git-generated messages: -m/--file (message), merges (merge),
# squash (squash) and --amend/-c/-C (commit). Git's own message wins.
case "$COMMIT_SOURCE" in
    message|merge|squash|commit)
        exit 0
        ;;
esac

# Belt-and-braces: never touch a merge message even with an unusual source
if [ -f .git/MERGE_HEAD ]; then
    exit 0
fi
```

- `case` é POSIX puro (seguro sob `#!/bin/sh`).
- O check de `.git/MERGE_HEAD` protege o cenário template-novo + CLI-antiga. Não cobre worktrees (`.git` é arquivo) — a guarda da CLI cobre essa lacuna.
- Line endings LF preservados.

### 2. CLI — guarda de defesa (defense-in-depth)

Novo helper em `src/core.py` (após `get_git_diff()`):

```python
def is_merge_in_progress():
    """Returns True when a merge is in progress (MERGE_HEAD exists)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return result.returncode == 0
    except Exception:
        return False  # git missing/unavailable — never block the commit
```

Em `src/main.py`, no fluxo `--commit` (modo hook), antes de `get_git_diff()`:

```python
        if hook and is_merge_in_progress():
            return  # merge in progress: git owns the message, skip AI silently
```

Decisões: guarda **apenas no modo hook** (execução manual de `gitpr -c` durante merge é ação explícita do usuário); retorno silencioso (exit 0 → git prossegue com o MERGE_MSG intacto); **sem** check de `SQUASH_MSG` na CLI (não é ref; o caso `squash` já é coberto pelo template via `COMMIT_SOURCE`).

### 3. Bump de versão dos scripts (auto-sync)

`src/updater.py:14`: `__scripts_version__` `"v0.0.1"` → `"v0.0.2"`.
Na próxima execução de `gitpr` sem `--quiet`, `check_and_update_hooks_scripts()` re-baixa os 5 hooks no repositório atual. **Restrição de ordenação:** os templates corrigidos precisam estar no `main` do GitHub antes de liberar a CLI com o bump, senão o auto-sync reinstalaria os templates quebrados.

### 4. Documentação (5 idiomas)

Seção "Preserving Manual Flow" de `docs/git-hooks-locais.md` e variantes `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`: o hook também silencia a IA quando a mensagem vem do git — `git pull`/`git merge` (fonte "merge"), `git merge --squash` ("squash") e `--amend`/`-c`/`-C` ("commit").

### 5. Testes

`tests/test_core.py` — nova classe `TestIsMergeInProgress` (3 testes): `returncode == 0` → `True` (com assert do comando exato), `returncode == 1` → `False`, exceção → `False`.

## Verificação executada

1. `sh -n` nos 5 templates — OK.
2. Matriz de fontes (`message|merge|squash|commit`) → exit 0 silencioso; fonte vazia sem `MERGE_HEAD` → hook chama `gitpr` normalmente (fluxo normal preservado).
3. Merge real em repo scratch com hook instalado → sem IA; `git log -1 --format=%B` = "Merge branch 'feature'".
4. Fonte vazia + `.git/MERGE_HEAD` presente → silencioso (belt-and-braces).
5. Guarda CLI: `run.py --commit --quiet --hook .git/MERGE_MSG` com merge em progresso → arquivo intacto, sem saída.
6. `python -m pytest tests/ -v` — 209 passed; 1 falha pré-existente e flaky (`test_metrics.py::TestMetricsDashboardF5`, passa isolado — sem relação com esta mudança).

## Riscos / mudanças de comportamento

- `git commit --amend` deixa de receber IA (desejado — antes a IA corrompia o amend).
- Rebase/cherry-pick: já pulavam via fonte `message` — sem regressão.
- Bump sobrescreve `.git/hooks/*` customizados pelo usuário — comportamento documentado do auto-sync.
- Worktrees: check de `.git/MERGE_HEAD` do template não funciona (`.git` é arquivo) — coberto pela guarda da CLI.
