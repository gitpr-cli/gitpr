# Integração MCP — GitPR

O GitPR suporta o **Model Context Protocol (MCP)**, permitindo integração direta
com editores e ferramentas de IA compatíveis com MCP como **VS Code**, **Cursor** e
**Claude Desktop**.

Quando conectado, o GitPR expõe suas capacidades com IA como ferramentas que o
assistente de IA do seu editor pode invocar — sem sair do editor ou abrir um terminal.

## Instalação Rápida

A maneira mais fácil de configurar o MCP é com o instalador integrado:

```bash
# Instalar para um editor específico
gitpr-mcp --install vscode      # Cria .vscode/mcp.json
gitpr-mcp --install cursor      # Cria .cursor/mcp.json
gitpr-mcp --install claude      # Atualiza config do Claude Desktop
gitpr-mcp --install zed         # Atualiza config do Zed

# Auto-detectar editores e instalar para todos encontrados
gitpr-mcp --install auto
gitpr-mcp --install              # Igual a --install auto
```

O instalador:

* Cria o diretório de config do editor se ele não existir
* Mescla com a config existente — nunca sobrescreve outros servidores
* Mostra quais editores foram configurados
* É idempotente — seguro executar múltiplas vezes

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
| `skill://list` | Lista de todas as URIs de templates de skill disponíveis |
| `skill://pr` | Instruções de IA personalizadas para descrições de PR |
| `skill://commit` | Instruções de IA personalizadas para mensagens de commit |
| `skill://review` | Instruções de IA personalizadas para code reviews |
| `skill://filereview` | Instruções de IA personalizadas para auditorias de arquivos |
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

Ou instale globalmente via configurações do VS Code.

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

## Exemplos de Uso

Após conectar o GitPR via MCP, você pode usar linguagem natural no chat de IA
do seu editor:

- **"Revise minhas alterações atuais"** → chama `review_code`
- **"Gere uma mensagem de commit para estas alterações"** → chama `generate_commit_message`
- **"Crie uma descrição de PR da minha branch"** → chama `generate_pr_description`
- **"Execute o linter no meu diff"** → chama `run_linter`
- **"Rastreie a origem das linhas 10-20 em src/main.py"** → chama `analyze_blame`
- **"Gere uma issue a partir das minhas alterações"** → chama `generate_issue`
- **"Em qual branch estou?"** → chama `get_git_context`

## Pré-requisitos

1. **GitPR instalado:** `pip install gitpr-cli` ou o binário standalone
2. **Chaves de API configuradas:** Execute `gitpr` uma vez interativamente para
   configurar as chaves de API, ou crie `~/.gitpr/.env` manualmente com suas chaves criptografadas
3. **Um editor compatível com MCP:** VS Code, Cursor, Zed, Claude Desktop, etc.

## Como Funciona

O comando `gitpr-mcp` inicia um servidor MCP via **transporte stdio** (entrada/saída
padrão). O editor o executa como um processo filho e se comunica via mensagens
JSON-RPC 2.0.

Para manter o canal JSON-RPC limpo, a saída de terminal do GitPR (banners, spinners,
mensagens coloridas) é automaticamente redirecionada para stderr ao executar no
modo MCP. Isso não requer nenhuma configuração — acontece de forma transparente.

## Solução de Problemas

### O editor não descobre as ferramentas do GitPR
- Verifique se `gitpr-mcp` está no seu PATH: `where gitpr-mcp` (Windows) ou `which gitpr-mcp` (Linux/macOS)
- Execute `pip install -e .` do diretório fonte do GitPR se estiver desenvolvendo localmente
- Verifique os logs do editor para erros de conexão MCP

### As ferramentas retornam erros
- Certifique-se de que as chaves de API estão configuradas em `~/.gitpr/.env`
- Verifique a saída stderr do servidor MCP (visível nos logs do editor)
- Execute `gitpr --help` normalmente para verificar se a CLI funciona

### Erro "Prompt interativo não está disponível"
- Você precisa pré-configurar as chaves de API em `~/.gitpr/.env` — o modo MCP não pode solicitar interativamente
- Execute `gitpr` uma vez no terminal para completar a configuração inicial
