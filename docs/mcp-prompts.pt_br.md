# MCP Prompts — Templates de Mensagem para Fluxos Comuns

O servidor MCP do GitPR expõe **prompts** (templates de mensagem pré-definidos) que
ajudam você a compor tarefas comuns do GitPR no chat de IA do seu editor. Em vez de digitar
instruções completas toda vez, selecione um prompt e deixe a IA preencher os detalhes.

## O Que São MCP Prompts?

No Model Context Protocol, **prompts** são templates de mensagem definidos pelo servidor.
Diferente de ferramentas (que executam código automaticamente), prompts são **mensagens iniciais**
que o usuário pode selecionar de uma lista em seu editor. A IA então usa o
template para invocar as ferramentas GitPR apropriadas para atender à solicitação.

## Prompts Disponíveis

| Prompt | O que faz | Ferramentas usadas |
|--------|-----------|--------------------|
| **Review PR** | Revisão de código completa de todas as alterações na branch atual | `full_review` |
| **Generate Commit Message** | Gera uma mensagem no formato Conventional Commits a partir de alterações não commitadas | `generate_commit_message` |
| **Create PR Description** | Gera um título e corpo para um Pull Request | `generate_pr_description` |
| **Run Code Linter** | Verifica alterações não commitadas contra as regras do `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Gera uma issue estruturada a partir das alterações atuais | `generate_issue` |
| **Trace Code Origin** | Investiga o histórico de uma região específica do código | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtém informações da branch atual e lista skills/templates disponíveis | `get_git_context`, `skill://list` |

## Como Usar

Uma vez que o servidor MCP esteja configurado em seu editor, os prompts aparecem na lista
de prompts junto com outros prompts de servidores MCP. A localização exata varia por editor:

- **VS Code / Cursor:** No painel de chat de IA, procure pelo seletor "Prompts"
- **Claude Desktop:** Prompts aparecem como opções selecionáveis na interface de chat
- **Claude Code:** Use a lista de prompts no painel de chat
- **Zed:** Disponível na lista de prompts do assistente inline

Selecione um prompt e a IA invocará automaticamente as ferramentas GitPR apropriadas
para atender à solicitação.

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

- [Integração MCP](mcp-integration.md) — Como configurar MCP para seu editor
- [Code Review com IA](code-review-ia.md) — Guia dos modos de revisão de código
- [Mensagens de Commit com IA](commit-message-ia.md) — Guia de Conventional Commits
- [Modo de Descrição de PR](pr-descricao-padrao.md) — Fluxo de geração de PR

---
**Dica:** Combine prompts com skills (arquivos `.gitpr.*.md`) para personalizar
o comportamento da IA conforme as convenções da sua equipe. Execute `gitpr --install` para configurar
tudo de uma vez.
