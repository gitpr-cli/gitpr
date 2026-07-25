# MCP Prompts — Modelos de Mensagem para Fluxos Comuns

O servidor MCP do GitPR expõe **prompts** (modelos de mensagem pré-definidos) que
ajudam a compor tarefas comuns do GitPR no chat de IA do seu editor. Em vez de digitar
instruções completas de cada vez, selecione um prompt e deixe a IA preencher os detalhes.

## O Que São MCP Prompts?

No Model Context Protocol, **prompts** são modelos de mensagem definidos pelo servidor.
Ao contrário de ferramentas (que executam código automaticamente), prompts são **mensagens iniciais**
que o utilizador pode selecionar de uma lista no seu editor. A IA usa então o
modelo para invocar as ferramentas GitPR apropriadas para atender ao pedido.

## Prompts Disponíveis

| Prompt | O que faz | Ferramentas usadas |
|--------|-----------|--------------------|
| **Review PR** | Revisão de código completa de todas as alterações na branch atual | `full_review` |
| **Generate Commit Message** | Gera uma mensagem no formato Conventional Commits a partir de alterações não consolidadas | `generate_commit_message` |
| **Create PR Description** | Gera um título e corpo para um Pull Request | `generate_pr_description` |
| **Run Code Linter** | Verifica alterações não consolidadas contra as regras do `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Gera uma issue estruturada a partir das alterações atuais | `generate_issue` |
| **Trace Code Origin** | Investiga o histórico de uma região específica do código | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtém informações da branch atual e lista skills/templates disponíveis | `get_git_context`, `skill://list` |

## Como Usar

Assim que o servidor MCP estiver configurado no seu editor, os prompts aparecem na lista
de prompts juntamente com outros prompts de servidores MCP. A localização exata varia por editor:

- **VS Code / Cursor:** No painel de chat de IA, procure pelo seletor "Prompts"
- **Claude Desktop:** Prompts aparecem como opções selecionáveis na interface de chat
- **Claude Code:** Use a lista de prompts no painel de chat
- **Zed:** Disponível na lista de prompts do assistente inline

Selecione um prompt e a IA invocará automaticamente as ferramentas GitPR apropriadas
para atender ao pedido.

## Como Funciona

Cada prompt é definido como uma função decorada com `@mcp.prompt()` em
`src/mcp_server.py`. A função retorna uma string de mensagem que o agente de IA do editor
envia para o modelo, instruindo-o a chamar ferramentas GitPR específicas com os
parâmetros apropriados.

Exemplo — o prompt "Review PR":

```python
@mcp.prompt()
def review_pr_prompt() -> str:
    return (
        "Review all changes in my current branch. "
        "Run a full review against origin/main, "
        "check the linter, and suggest improvements."
    )
```

O agente de IA que receber esta mensagem irá então chamar `full_review`, `run_linter`,
e compor uma resposta de revisão abrangente com base nos resultados.

## Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Como configurar MCP para o seu editor
- [Code Review com IA](code-review-ia.md) — Guia dos modos de revisão de código
- [Mensagens de Commit com IA](commit-message-ia.md) — Guia de Conventional Commits
- [Modo de Descrição de PR](pr-descricao-padrao.md) — Fluxo de geração de PR

---
**Dica profissional:** Combine prompts com skills (ficheiros `.gitpr.*.md`) para personalizar
o comportamento da IA de acordo com as convenções da sua equipa. Execute `gitpr --install` para configurar
tudo de uma só vez.
