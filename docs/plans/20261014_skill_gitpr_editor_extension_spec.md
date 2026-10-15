# SPEC — GitPR Editor Extension (VS Code/Cursor/JetBrains)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: criar extensões thin client para VS Code, Cursor e JetBrains que consomem o servidor MCP já existente do GitPR (12 tools), oferecendo botões/commands de Commit, Review, Publish PR e Check sem duplicar lógica de negócio.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler a implementação do servidor MCP existente (`src/mcp/` ou caminho real confirmado) e extrair: (a) lista completa das 12 tools disponíveis, (b) assinatura de cada tool (parâmetros, retorno), (c) protocolo de transporte (stdio, SSE, HTTP), (d) mecanismo de autenticação/token, (e) como o servidor é iniciado/parado.
2. Confirmar quais editores já possuem integração MCP nativa (VS Code, Cursor, Zed, Claude Code/Desktop) e qual é o formato de configuração esperado por cada um.
3. Verificar se já existe alguma extensão de editor parcial ou planejada. Reaproveitar o que existir; não duplicar.
4. Confirmar o modelo de configuração do GitPR (`.gitpr/config.yml`, variáveis de ambiente) para que a extensão herde a mesma configuração sem duplicar parsing.
5. Verificar se existe algum mecanismo de autenticação/token já usado pelo MCP (Fernet, variável de ambiente, etc.) para reaproveitar na extensão.
6. Confirmar a convenção de comandos/flags do CLI que a extensão deve chamar via MCP (ex.: `gitpr -r`, `gitpr pr`, `gitpr check`), para mapear corretamente botões/commands da extensão.

Não prosseguir sem completar os passos 1–4. Se o MCP server não estiver maduro o suficiente (12 tools confirmadas), esta spec deve documentar dependência explícita ou implementar versão mínima compatível.

## 1. Escopo da feature

- **Objetivo:** criar extensões de editor (VS Code, Cursor, JetBrains) que expõem botões/commands de Commit, Review, Publish PR e Check, consumindo o servidor MCP já existente do GitPR, sem duplicar lógica de negócio.
- **Plataformas suportadas nesta primeira versão:**
  - VS Code (Marketplace oficial);
  - Cursor (Marketplace compatível com VS Code);
  - JetBrains (IntelliJ/PyCharm/WebStorm — Marketplace JetBrains).
- **Comandos/botões da extensão:**
  - `GitPR: Commit` — gera mensagem de commit semântica a partir do diff atual.
  - `GitPR: Review` — roda review de qualidade no diff atual.
  - `GitPR: Publish PR` — abre TUI/fluxo de publicação de PR.
  - `GitPR: Check` — executa `gitpr check` unificado (SARIF/JSON/JUnit).
  - `GitPR: Explain PR` — gera resumo para o revisor (se skill explain existir).
  - `GitPR: Mentor` — ativa modo didático no review (se skill mentor existir).
- **Arquitetura thin client:** a extensão não implementa lógica de negócio; apenas chama tools MCP e renderiza resultados.
- **Fora de escopo nesta fase:** extensão para outros editores (Zed, Neovim, Emacs), publicação automática de comentários inline no PR, dashboard web dentro da extensão, sincronização cloud de configuração.
- **Compatibilidade:** a extensão não deve alterar o comportamento do CLI/MCP existente. Deve consumir a mesma interface MCP sem duplicar lógica.

## 2. Árvore de arquivos

```text
extensions/
├── vscode/
│   ├── package.json               # NOVO — manifest da extensão VS Code
│   ├── src/
│   │   ├── extension.ts            # NOVO — entrypoint
│   │   ├── mcp_client.ts           # NOVO — cliente MCP
│   │   ├── commands/
│   │   │   ├── commit.ts
│   │   │   ├── review.ts
│   │   │   ├── publish_pr.ts
│   │   │   └── check.ts
│   │   └── ui/
│   │       └── status_bar.ts
│   ├── package.json
│   └── README.md
├── cursor/
│   └── (similar ao vscode, compatível com marketplace Cursor)
└── jetbrains/
    ├── build.gradle.kts            # NOVO — build Gradle para plugin JetBrains
    ├── src/main/kotlin/
    │   ├── GitPrMcpClient.kt       # NOVO — cliente MCP
    │   ├── actions/
    │   │   ├── CommitAction.kt
    │   │   ├── ReviewAction.kt
    │   │   ├── PublishPrAction.kt
    │   │   └── CheckAction.kt
    │   └── ui/
    │       └── StatusBarFactory.kt
    └── README.md

tests/extensions/
├── vscode/
│   ├── test_mcp_client.ts
│   └── test_commands.ts
└── jetbrains/
    └── test_mcp_client.kt
```

A skill DEVE adaptar caminhos à estrutura real do monorepo. Não duplicar lógica de MCP se já existir cliente/servidor.

## 3. Contrato — cliente MCP

```typescript
// extensions/vscode/src/mcp_client.ts
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";


export class GitPrMcpClient {
  private client: Client;
  private transport: StdioClientTransport;

  constructor(binaryPath: string, configPath: string) {
    this.transport = new StdioClientTransport({
      command: "gitpr",
      args: ["--mcp"],
      env: { GITPR_CONFIG: configPath },
    });
    this.client = new Client({ name: "gitpr-vscode", version: "1.0.0" });
  }

  async connect(): Promise<void> {
    await this.client.connect(this.transport);
  }

  async callTool(toolName: string, args: Record<string, unknown>): Promise<unknown> {
    return await this.client.callTool({ name: toolName, arguments: args });
  }

  async disconnect(): Promise<void> {
    await this.client.close();
  }
}
```

Requisitos:

1. Cliente MCP deve usar o SDK oficial (`@modelcontextprotocol/sdk`).
2. Transporte stdio (o GitPR MCP server já usa stdio).
3. Config path herdado do GitPR (`.gitpr/config.yml`).
4. Nenhuma lógica de negócio duplicada — apenas chamadas MCP.

## 4. Mapeamento de tools MCP para commands

| Command da extensão | Tool MCP chamada | Parâmetros esperados |
|---|---|---|
| `GitPR: Commit` | `generate_commit_message` | `{ diff: string, framework?: string }` |
| `GitPR: Review` | `review_diff` | `{ diff: string, skill?: string }` |
| `GitPR: Publish PR` | `create_pull_request` | `{ title, body, head, base }` |
| `GitPR: Check` | `run_check` | `{ format: "sarif"|"json"|"junit", fail_on?: string }` |
| `GitPR: Explain PR` | `generate_pr_explanation` | `{ diff: string }` |
| `GitPR: Mentor` | `generate_mentor_explanation` | `{ finding_id: string }` |

A skill DEVE confirmar os nomes reais das 12 tools no servidor MCP e ajustar o mapeamento conforme necessário. Não inventar nomes de tools.

## 5. UX da extensão

### Status Bar
- Indicador de status do MCP (conectado/desconectado).
- Botões rápidos: Commit, Review, Publish PR, Check.

### Command Palette
- Todos os commands registrados via `vscode.commands.registerCommand`.
- Atalhos de teclado configuráveis.

### Notifications
- Sucesso/falha de cada operação.
- Link para abrir resultado completo (ex.: SARIF no Problems panel).

### Problems Panel
- Findings do review/check aparecem como diagnostics.
- Clique navega para linha/arquivo.

## 6. Configuração da extensão

```json
// settings.json
{
  "gitpr.mcpCommand": "gitpr",
  "gitpr.mcpArgs": ["--mcp"],
  "gitpr.configPath": ".gitpr/config.yml",
  "gitpr.defaultOutputFormat": "sarif"
}
```

Requisitos:

1. Config path herdado do GitPR (mesmo arquivo usado pelo CLI).
2. Nenhuma configuração paralela — extensão consome a mesma config.
3. Token/API key nunca deve ser armazenado na extensão — usar o mesmo mecanismo Fernet do GitPR.

## 7. Testes obrigatórios — critérios de aceite

1. **Cliente MCP conecta:** `connect()` deve estabelecer conexão com o servidor MCP sem erro.
2. **Chamada de tool:** `callTool("generate_commit_message", ...)` deve retornar resposta válida.
3. **Commands registrados:** todos os 6 commands devem estar registrados no Command Palette.
4. **Problems Panel:** findings do review/check aparecem como diagnostics.
5. **Não-regressão do MCP:** servidor MCP existente mantém comportamento anterior.
6. **Privacidade/offline:** extensão não abre rede além do MCP local.
7. **Config herdada:** extensão usa o mesmo `configPath` do GitPR.
8. **Multi-editor:** VS Code e Cursor compartilham a mesma base de código (compatibilidade de API).
9. **JetBrains:** cliente Kotlin deve chamar as mesmas tools MCP via stdio.

Critério de feature completa: extensão VS Code instalada via Marketplace conecta ao MCP local, executa Commit/Review/Publish PR/Check, e renderiza resultados no Problems Panel sem duplicar lógica de negócio.

## 8. Ordem de execução recomendada

1. Confirmar as 12 tools MCP reais e suas assinaturas (passo 0.1).
2. Implementar `mcp_client.ts` (VS Code) reaproveitando SDK oficial.
3. Implementar commands básicos (Commit, Review) primeiro.
4. Implementar Publish PR e Check.
5. Implementar Explain PR e Mentor (se skills existirem).
6. Implementar StatusBar e Problems Panel.
7. Empacotar e publicar no VS Code Marketplace.
8. Adaptar para Cursor (compatibilidade VS Code).
9. Implementar cliente JetBrains em Kotlin, seguindo o mesmo contrato MCP.
10. Atualizar README e documentação de instalação.

Cada etapa deve ser um commit/PR isolado e revisável. Não começar por JetBrains; validar primeiro que VS Code/Cursor resolvem o problema de descoberta.

## 9. Riscos e dependências

- **Dependência:** servidor MCP maduro com 12 tools; sem ele, extensão não tem valor.
- **Dependência:** SDK oficial MCP (`@modelcontextprotocol/sdk`) para VS Code/Cursor.
- **Dependência:** JetBrains Platform SDK para plugin Kotlin.
- **Risco:** nomes de tools MCP podem mudar entre versões. Versionar contrato de tools.
- **Risco:** segredo em texto pleno em notification/log pode vazar. Mascaramento obrigatório.
- **Risco:** extensão pode conflitar com outras extensões MCP. Namespace próprio (`gitpr.*`).

## 10. Fora de escopo

- Extensão para Zed, Emacs, Vim.
- Dashboard web dentro da extensão.
- Sincronização cloud de configuração.
- SSO/RBAC.
- Marketplace de skills/packs dentro da extensão.
- Execução de scripts/hooks/código arbitrário.
- Skills arbitrárias descobertas dinamicamente.

## 11. Encaixe estratégico

Extensão de editor é o canal de descoberta que o CLI/MCP sozinhos não entregam: usuários que nunca abririam um terminal descobrem o GitPR pela loja de extensões. Nesta primeira versão deve permanecer no tier Free/Community, porque o valor imediato é adoção e descoberta. A monetização futura deve estar na colaboração: skills oficiais, suporte SLA, dashboards agregados — não no bloqueio do uso local da extensão.
