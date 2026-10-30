# Survey — branch base do PR configurável por projeto

Data: 2026-10-30 · Branch: `develop_natan`

## Contexto da tarefa

Permitir que cada projeto defina a branch de destino do PR num arquivo versionado,
`.gitpr/conf/gitpr.config.yml`, criado automaticamente ao executar o `gitpr` ou no
`--install`. Padrão: `main`. A configuração deve ser editável no TUI `gitpr config`.

## Fatos levantados (exploração)

### Resolução atual do alvo do PR

- `src/main.py:1701` — `target_base = base or os.getenv("PR_DEFAULT_BASE") or get_base_branch()`.
- `src/mcp_server.py:1423-1427` — mesma cadeia com `.strip()` e `or "main"` final.
- `core.get_base_branch()` (`src/core.py:1464-1486`) lê `refs/remotes/origin/HEAD`; falha → aviso + `"main"`.
- **O alvo não influencia o diff da IA**: `get_git_full_diff()` (`src/core.py:1489`) sempre usa `origin/HEAD`.
  Um PR para `develop` é descrito/revisado contra `main`.
- Consumidores do alvo: TUI `PrPublishApp(base_branch=...)` (`src/main.py:1785`),
  `_publish_pr_directly` (`src/main.py:1731`), MCP `publish_pull_request`.
  `-f`, MCP de diff, `check/baseline/risk --base` usam conceitos distintos e não são afetados.

### Configuração e TUI existentes

- `gitpr config` já existe (`src/main.py:2085-2113` → `src/ui/config_app.py:launch_config_app`).
- Schema declarativo em `src/config_schema.py` (campos de `~/.gitpr/.env`), categorias em `CATEGORIES`,
  `PR_DEFAULT_BASE` em `:436-445` (categoria `pr`).
- A seção **Skills** é o precedente de conteúdo não-`.env`: campo-sentinela `SKILLS_FOLDER`
  (`read_only`) + painel próprio, salvo fora do `.env` (`_write_skills`).
- `_apply_save` (`config_app.py:1735`) grava `.env` via `save_config_values` e skills via `write_skill_file`.
- `gitpr config` imprime stdout vazio (`tests/test_config_cli.py`).

### `.gitpr/` no projeto

- `.gitpr/conf/` já existe e é versionado: `.gitpr/conf/gitpr.smart-excludes.json` está rastreado.
- `.gitignore` ignora apenas `.gitpr/metrics/`; skill e reports são conteúdo de projeto.
- Precedente de seed: `_seed_local_smart_excludes()` (`src/core.py:118-144`), best-effort,
  nunca sobrescreve, escreve `_comment`.
- `--install` (`core.run_install_wizard`, `:1757`) já grava skills, hooks e arquivos MCP no repo.

### Startup e testes

- Subcomandos retornam cedo em `src/main.py:688-699`; o seed precisa entrar antes.
- `tests/conftest.py` fixa env (lang, linter security, skip update) e não isola HOME/cwd;
  ~49 testes `CliRunner` rodam com cwd no checkout → seed precisa de escape de teste.
- `tests/test_config_schema.py` garante que toda chave de `DEFAULT_CONFIG` está no schema;
  chaves sentinela (como `SKILLS_FOLDER`) não pertencem ao `DEFAULT_CONFIG`.
- i18n: chaves são literais em inglês; seis arquivos `langs/*.json`; `tests/sync_i18n.py` sincroniza.

## Rodadas do grill e decisões

| # | Pergunta | Decisão |
|---|---|---|
| Q1 | Escopo do "base" | (b) só alvo do PR; diff da IA continua em `origin/HEAD` |
| Q2/Q8 | Precedência | `--base` > projeto > `PR_DEFAULT_BASE` > auto-detect > `main` |
| Q3 | Ciclo de vida | seed em toda invocação em repo git; nunca sobrescreve; versionado pelo usuário |
| Q4 | Local do arquivo | topo do repositório (`git rev-parse --show-toplevel`), fallback `cwd` |
| Q5 | Schema YAML | aninhado `pull_request.base_branch` + comentário de cabeçalho |
| Q6 | TUI | nova categoria **Project**; salva só YAML; campo global renomeado |
| Q7/Q13 | Falhas | YAML inválido → aviso e segue; branch inexistente → erro claro; TUI avisa sem bloquear |
| Q9 | Valor do seed | `PR_DEFAULT_BASE` se preenchido, senão `main` literal |
| Q10 | Versionamento | nunca `git add`; dica de uma linha; aviso se o caminho for ignorado |
| Q11 | Gatilho | toda invocação exceto ajuda |
| Q12 | Consumidores | fluxo default, `--no-edit`, `PrPublishApp`, MCP publish; MCP de diff e `-f` intocados |
| Q14 | Documentação | ADR-015 + glossário separando *PR target base* de *diff base* |
