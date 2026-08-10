# 📂 Git Status — Listagem de Arquivos Não Commitados e Verificação de Unstaged

O GitPR pode listar alterações de arquivos não commitados sem processamento de IA e verifica automaticamente arquivos fora do stage antes de executar qualquer comando de IA (commit, review, full review, issue e PR).

---

## 1. Flag `--status` — Listagem Rápida de Arquivos (Sem IA)

A flag `--status` lista todas as alterações de arquivos não commitados categorizadas por tipo — **sem IA, sem rede, sem git fetch**. Execução instantânea.

```bash
gitpr --status
```

Exemplo de saída:
```
📂 Uncommitted changes (no AI):
  ➕ New files (2):
    - src/new_module.py
    - tests/test_new_module.py
  ✏️ Modified files (3):
    - src/core.py
    - src/main.py
    - README.md
  🗑️ Deleted files (1):
    - old_deprecated.py
```

### Categorias

| Categoria | Códigos git status | Descrição |
|-----------|-------------------|-----------|
| **Novos** (`➕`) | `??` | Arquivos não rastreados — nunca adicionados ao Git |
| **Modificados** (`✏️`) | ` M`, `MM`, `AM`, `RM` | Modificações não staged na árvore de trabalho |
| **Deletados** (`🗑️`) | ` D`, `MD`, `AD`, `RD` | Deleções não staged na árvore de trabalho |

> **Nota:** Arquivos que estão staged (adicionados via `git add`) mas com a árvore de trabalho limpa (`M `, `A `, `D `) **não** são exibidos. A flag `--status` mostra apenas arquivos com **alterações na árvore de trabalho que ainda não estão na área de stage**.

---

## 2. Verificação de Arquivos Unstaged (Todos os Comandos)

Antes de gerar qualquer análise de IA, o GitPR agora verifica arquivos fora do stage em **todos** os comandos principais:

| Comando | Comportamento quando arquivos unstaged são encontrados |
|---------|-------------------------------------------------------|
| `gitpr` (PR padrão) | **Interativo** — abre modal TUI para stage, pular ou cancelar |
| `gitpr -c` (commit) | **Aviso** — alerta que arquivos unstaged NÃO entrarão no commit |
| `gitpr -r` (review) | **Informativo** — avisa que arquivos unstaged ainda são incluídos no diff |
| `gitpr -f` (fullreview) | **Informativo** — avisa que arquivos unstaged ainda são incluídos no diff |
| `gitpr -is` (issue, modo diff) | **Informativo** — avisa que arquivos unstaged ainda são incluídos no diff |

### Comportamento específico do commit

Ao executar `gitpr -c`, o aviso é mais forte porque arquivos unstaged **não** serão incluídos na mensagem de commit gerada pela IA:

```
⚠️ 3 arquivo(s) não estão em stage e NÃO serão incluídos no commit.
  ✏️ Modified files (2):
    - src/core.py
    - src/config.py
  ➕ New files (1):
    - src/new_feature.py
💡 Dica: Use 'git add <arquivo>' para adicioná-los ao stage, ou passe --no-unstaged-check para pular esta verificação.
```

Se `GITPR_AUTO_STAGE=true` estiver definido, `-c` fará auto-stage dos arquivos antes de gerar a mensagem de commit (mesmo comportamento do PR).

### Comportamento do Review/FullReview/Issue

Para `-r`, `-f` e `-is`, o diff já inclui alterações unstaged, então a análise é precisa. A mensagem é apenas informativa:

```
ℹ️ 2 arquivo(s) não estão em stage. Eles ainda serão incluídos nesta análise.
  ✏️ Modified files (2):
    - src/core.py
    - src/main.py
💡 Dica: Use 'git add <arquivo>' para adicioná-los ao stage, ou passe --no-unstaged-check para pular esta verificação.
```

> **Nota:** `GITPR_AUTO_STAGE` **não** é aplicado para review/fullreview/issue — fazer auto-stage como efeito colateral de um comando de análise somente leitura seria inesperado.

---

## 3. Flag `--no-unstaged-check`

Pula a verificação de unstaged para uma única execução:

```bash
gitpr -c --no-unstaged-check
```

Equivalente a definir `GITPR_SKIP_UNSTAGED_CHECK=true`, mas apenas para aquele comando.

---

## 4. Proteção no Modo Hook

Quando o GitPR é executado dentro de um hook do Git (flag `--hook`, usado pelo `prepare-commit-msg`), a verificação de unstaged é **completamente pulada** — qualquer prompt ou TUI travaria o processo de `git commit`.

---

## 5. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para pular a verificação de arquivos unstaged em todos os comandos |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para automaticamente adicionar ao stage todos os arquivos unstaged (apenas PR e commit) |

---

## 6. Ferramentas MCP

Duas novas ferramentas MCP estão disponíveis para integração com IDEs:

### `list_unstaged_files`
Retorna JSON estruturado com três listas categorizadas:
```json
{
  "status": "changes_found",
  "new": ["nao_rastreado.py"],
  "modified": ["editado.py"],
  "deleted": ["removido.py"],
  "total": 3,
  "message": ""
}
```

### `analyze_unstaged_diff`
Retorna apenas o diff **unstaged** (index vs árvore de trabalho), excluindo alterações staged:
```json
{
  "status": "changes_found",
  "diff": "diff --git a/x.py b/x.py\n-old\n+new"
}
```

> **Nota:** Arquivos não rastreados nunca aparecem em diffs do git. Use `list_unstaged_files` para vê-los.

A ferramenta existente `analyze_diff` foi esclarecida: ela retorna o diff **não commitado** (`git diff HEAD` — inclui tanto alterações staged quanto unstaged, mas não arquivos não rastreados).

---

## 7. Documentação Relacionada

- [Por que o GitPR ignorou meus arquivos novos?](untracked-files.pt_br.md) — Explica por que arquivos não rastreados não são incluídos automaticamente nos diffs
- [Publicação de Pull Request](pull-request-publication.md) — Fluxo completo de publicação de PR incluindo gerenciamento de arquivos unstaged
- [Git Hooks Locais](git-hooks-locais.md) — Como os hooks interagem com a verificação de unstaged
