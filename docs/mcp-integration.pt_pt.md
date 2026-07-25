# Integração MCP — GitPR

O GitPR suporta o **Model Context Protocol (MCP)**, permitindo a integração direta
com editores e ferramentas de IA compatíveis com MCP como **VS Code**, **Cursor** e
**Claude Desktop**.

Quando ligado, o GitPR expõe as suas capacidades com IA como ferramentas que o
assistente de IA do seu editor pode invocar — sem sair do editor ou abrir um terminal.

## Instalação Rápida

A maneira mais fácil de configurar o MCP é com o instalador integrado:

```bash
# Instalar para um editor específico
gitpr-mcp --install vscode      # Cria .vscode/mcp.json
gitpr-mcp --install cursor      # Cria .cursor/mcp.json
gitpr-mcp --install claude      # Atualiza config do Claude Desktop
gitpr-mcp --install zed         # Atualiza config do Zed

# Auto-detectar editores e instalar para todos os encontrados
gitpr-mcp --install auto
gitpr-mcp --install              # Igual a --install auto
```

O instalador:

* Cria o diretório de config do editor se este não existir
* Faz merge com a config existente — nunca sobrescreve outros servidores
* Mostra quais editores foram configurados
* É idempotente — seguro executar várias vezes

## Ferramentas Disponíveis

| Ferramenta | Descrição |
|-----------|-------------|
| `get_git_context` | Branch atual, nome do repositório e URL do remote |
| `analyze_diff` | Diff git das alterações não commitadas (`git diff HEAD`) |
| `get_full_diff` | Diff completo contra origin/main (`git fetch` + diff) |
| `generate_commit_message` | Mensagem de commit no formato Conventional Commits gerada por IA |
| `review_code` | Code review com IA das alterações locais (não commitadas) |
| `full_review` | Code review com IA de todas as alterações desde origin/main |
| `generate_pr_description` | Descrição completa de PR (título + corpo) |
| `run_linter` | Linter estático baseado nas regras do `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + classificação IA (ORIGIN vs REFACTORING) |
| `generate_issue` | Issue estruturada a partir de diff, histórico ou contexto de blame |

## Recursos Disponíveis

| URI | Conteúdo |
|-----|---------|
| `skill://list` | Lista de todos os URIs de templates de skill disponíveis |
| `skill://pr` | Instruções de IA personalizadas para descrições de PR |
| `skill://commit` | Instruções de IA personalizadas para mensagens de commit |
| `skill://review` | Instruções de IA personalizadas para code reviews |
| `skill://filereview` | Instruções de IA personalizadas para auditorias de ficheiros |
| `skill://issue` | Instruções de IA personalizadas para geração de issues |
| `skill://blame` | Instruções de IA personalizadas para análise de blame |
| `linter://config` | Regras YAML do linter (`.gitpr.linter.yml`) |

## Configuração nos Editores

### VS Code

Crie `.vscode/mcp.json` na raiz do seu projeto:

```json
{
  "servers": {
    "gitpr": {
      "type": "stdio",
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

Ou instale globalmente através das configurações do VS Code.

### Cursor

Crie `.cursor/mcp.json` na raiz do seu projeto:

```json
{
  "mcpServers": {
    "gitpr": {
      "type": "stdio",
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Claude Desktop

Adicione ao `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gitpr": {
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Zed

Adicione ao `settings.json`:

```json
{
  "context_servers": {
    "gitpr": {
      "command": {
        "path": "gitpr-mcp",
        "args": []
      }
    }
  }
}
```

## Exemplos de Utilização

Após ligar o GitPR via MCP, pode usar linguagem natural no chat de IA
do seu editor:

- **"Revê as minhas alterações atuais"** → chama `review_code`
- **"Gera uma mensagem de commit para estas alterações"** → chama `generate_commit_message`
- **"Cria uma descrição de PR do meu branch"** → chama `generate_pr_description`
- **"Executa o linter no meu diff"** → chama `run_linter`
- **"Rastreia a origem das linhas 10-20 em src/main.py"** → chama `analyze_blame`
- **"Gera uma issue a partir das minhas alterações"** → chama `generate_issue`
- **"Em que branch estou?"** → chama `get_git_context`

## Pré-requisitos

1. **GitPR instalado:** `pip install gitpr-cli` ou o binário standalone
2. **Chaves de API configuradas:** Execute `gitpr` uma vez interativamente para
   configurar as chaves de API, ou crie `~/.gitpr/.env` manualmente com as suas chaves encriptadas
3. **Um editor compatível com MCP:** VS Code, Cursor, Zed, Claude Desktop, etc.

## Como Funciona

O comando `gitpr-mcp` inicia um servidor MCP através de **transporte stdio** (entrada/saída
padrão). O editor executa-o como um processo filho e comunica através de mensagens
JSON-RPC 2.0.

Para manter o canal JSON-RPC limpo, a saída de terminal do GitPR (banners, spinners,
mensagens coloridas) é automaticamente redirecionada para stderr ao executar no
modo MCP. Isto não requer nenhuma configuração — acontece de forma transparente.

## Resolução de Problemas

### O editor não descobre as ferramentas do GitPR
- Verifique se `gitpr-mcp` está no seu PATH: `which gitpr-mcp` (Linux/macOS) ou `where gitpr-mcp` (Windows)
- Execute `pip install -e .` do diretório fonte do GitPR se estiver a desenvolver localmente
- Verifique os logs do editor para erros de ligação MCP

### As ferramentas retornam erros
- Certifique-se de que as chaves de API estão configuradas em `~/.gitpr/.env`
- Verifique a saída stderr do servidor MCP (visível nos logs do editor)
- Execute `gitpr --help` normalmente para verificar se a CLI funciona

### Erro "Prompt interativo não está disponível"
- Precisa pré-configurar as chaves de API em `~/.gitpr/.env` — o modo MCP não pode solicitar interativamente
- Execute `gitpr` uma vez no terminal para completar a configuração inicial
