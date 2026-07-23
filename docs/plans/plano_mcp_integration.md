# MCP Integration Plan — GitPR CLI

## Context

O relatório [relatorio_estado_v0.0.2.md](docs/reports/relatorio_estado_v0.0.2.md) lista **MCP (Model Context Protocol)** como um dos próximos passos do projeto. GitPR já está maduro como ferramenta CLI autônoma (v0.0.27, 5 idiomas, 3 provedores de IA, chat TUI), mas opera em isolamento — o desenvolvedor precisa sair do editor, abrir o terminal e executar comandos manualmente.

**MCP resolve isso:** transforma o GitPR de uma ferramenta de terminal para um **serviço de IA integrável** que editores e IDEs podem consumir diretamente.

---

## O Que Esta Funcionalidade Proporciona

### 1. Integração Direta com IDEs (VS Code, Cursor, Zed, etc.)
- O desenvolvedor pede "revisa meu código" dentro do editor e o GitPR responde sem sair do fluxo
- PR descriptions, commits, code reviews, linter — tudo acessível no contexto do editor

### 2. GitPR Como Ferramenta de Agentes de IA
- Claude Desktop, Cursor Agent, GitHub Copilot podem usar GitPR como um "tool"
- Exemplo: um agente gera código, chama `review_code` do GitPR, e itera sobre o feedback
- Fecha o loop: IA gera → IA revisa → IA corrige

### 3. Workflows Compostos
- CI/CD pode chamar GitPR tools para revisar PRs automaticamente
- Outras ferramentas MCP podem compor com GitPR (ex: revisa com GitPR → notifica Slack)

### 4. Experiência Unificada
- Fim do `Alt+Tab` entre terminal e editor
- Todo o poder do GitPR disponível como ferramentas MCP: `analyze_diff`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`

### 5. Configuração Exposta Como Recursos MCP
- Skill templates (`.gitpr.*.md`) e linter config (`.gitpr.linter.yml`) acessíveis como `skill://` e `linter://` resources
- IDEs podem ler e editar instruções customizadas de IA do projeto

---

## Abordagem Recomendada

**FastMCP Server customizado** usando o SDK oficial `mcp` da Anthropic.

### Por que não `click-mcp`?
`click-mcp` exige `@click.group()` com subcomandos. GitPR usa um único `@click.command()` plano com dispatch por flags `if/elif`. Refatorar para grupos quebraria compatibilidade retroativa. É mais limpo criar um módulo separado.

### Estratégia de Isolamento
O maior desafio técnico: o código existente do GitPR usa `click.secho()`, `click.echo()`, `sys.stdout.write()` (spinner), e `sys.exit()` — coisas que corrompem o protocolo JSON-RPC do MCP (que trafega em stdout) ou matam o processo servidor.

**Solução:** Monkey-patching no entry point `main()` do `mcp_server.py`:
- Redireciona `sys.stdout` → `stderr` (mas expõe `sys.__stdout__.buffer` para o MCP transport)
- Substitui `click.secho`/`click.echo` → versões que escrevem em stderr
- Substitui `sys.exit` → levanta `SystemExit` (capturado pelo `_safe_call`)
- Substitui `click.prompt` → `RuntimeError` (não há terminal interativo no modo MCP)

Isso toca **zero arquivos existentes** e isola toda a lógica MCP em um único módulo.

---

## Plano de Implementação

### Passo 1: Adicionar dependência `mcp`
**Arquivos:** `pyproject.toml`, `Pipfile`

- `pyproject.toml`: Adicionar `"mcp>=1.0.0"` em `dependencies`
- `pyproject.toml`: Adicionar entry point `gitpr-mcp = "src.mcp_server:main"` em `[project.scripts]`
- `Pipfile`: Adicionar `mcp = "*"` em `[packages]`

### Passo 2: Criar `src/mcp_server.py`
**Novo arquivo.** ~500 linhas. Estrutura:

1. **Sistema de patching de output** (~70 linhas)
   - `_patch_output()`: redireciona stdout→stderr, neutraliza `sys.exit()`, bloqueia `click.prompt()`
   - `_unpatch_output()`: restaura originais (para testes)

2. **Inicialização silenciosa** (~20 linhas)
   - `_init_config()`: carrega `.env` sem `setup_environment()` (evita prompts interativos)
   - Respeita `GITPR_LANG` para i18n

3. **Wrapper seguro** (~15 linhas)
   - `_safe_call(fn, *args, **kwargs)`: captura `SystemExit` e exceções

4. **FastMCP App + 10 Tools** (~350 linhas)

   | Tool | Descrição | Função Existente |
   |------|-----------|-----------------|
   | `get_git_context` | Branch, repo, remote | `get_current_branch()`, `get_repo_name()` |
   | `analyze_diff` | Retorna diff atual (git diff HEAD) | `get_git_diff()` |
   | `get_full_diff` | Diff contra origin/main | `get_git_full_diff()` |
   | `generate_commit_message` | Mensagem Conventional Commits via IA | `generate_pr_content("commit")` |
   | `review_code` | Code review de mudanças locais | `generate_pr_content("review")` |
   | `full_review` | Code review completo (fetch + diff) | `generate_pr_content("fullreview")` |
   | `generate_pr_description` | Descrição completa de PR | `generate_pr_content("pr")` |
   | `run_linter` | Linter estático local (.gitpr.linter.yml) | `parse_diff_and_lint()` |
   | `analyze_blame` | Arqueologia de código (git blame + IA) | `run_blame_analysis()` |
   | `generate_issue` | Issue estruturada (What/Why/Where/How) | `generate_issue_content()` |

5. **MCP Resources** (~60 linhas)
   - `skill://{pr,commit,review,filereview,issue,blame}` — conteúdo dos templates
   - `linter://config` — conteúdo do `.gitpr.linter.yml`

6. **Entry point `main()`** (~30 linhas)
   - Aplica patches → inicia config → `mcp.run(transport="stdio")` → restaura patches

### Passo 3: Adicionar flag `--mcp` no CLI
**Arquivo:** `src/main.py`

- Adicionar `@click.option('--mcp', is_flag=True, hidden=True)` 
- Handler ANTES de `setup_environment()`: delega para `src.mcp_server.main()`
- Serve como alias de conveniência; o primary entry point é `gitpr-mcp`

### Passo 4: Criar testes
**Novo arquivo:** `tests/test_mcp_server.py`

- Testes unitários para cada tool (mock das funções de `src.core`, `src.linter_engine`, `src.blame_engine`)
- Testes de integração: verificar que `gitpr-mcp` inicia e lista tools

### Passo 5: Criar documentação
**Novo arquivo:** `docs/mcp-integration.md`

- Configuração para VS Code (`.vscode/mcp.json`)
- Configuração para Cursor (`.cursor/mcp.json`)
- Configuração para Claude Desktop (`claude_desktop_config.json`)

---

## Verificação

### Testes de unidade
```bash
pipenv run pytest tests/test_mcp_server.py -v
```

### Teste manual do servidor MCP
```bash
# Instalar em modo dev
pip install -e .

# Iniciar servidor (stdio) e listar tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | gitpr-mcp
```

### Teste com VS Code
1. Criar `.vscode/mcp.json` com a config do GitPR
2. Abrir um projeto git, fazer mudanças
3. No chat do VS Code: "Review my changes using gitpr"
4. Verificar se o VS Code descobre as tools e as invoca corretamente

### Teste de regressão da CLI
```bash
gitpr --help          # Deve funcionar normalmente
gitpr -c              # Commit message sem alterações
gitpr -l              # Linter sem alterações
```

---

## Arquivos Afetados

| Arquivo | Tipo | Mudança |
|---------|------|---------|
| `src/mcp_server.py` | **Novo** | Módulo completo do servidor MCP |
| `pyproject.toml` | Editar | +`mcp>=1.0.0` em deps, +`gitpr-mcp` entry point |
| `Pipfile` | Editar | +`mcp = "*"` em packages |
| `src/main.py` | Editar | +`--mcp` flag com handler precoce (~5 linhas) |
| `tests/test_mcp_server.py` | **Novo** | Testes unitários para tools MCP |
| `docs/mcp-integration.md` | **Novo** | Documentação de configuração |
