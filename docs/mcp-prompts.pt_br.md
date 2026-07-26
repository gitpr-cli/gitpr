# MCP Prompts — Templates de Mensagem para Fluxos Comuns

O servidor MCP do GitPR expõe **prompts** (templates de mensagem pré-definidos) que
ajudam você a compor tarefas comuns do GitPR no chat de IA do seu editor. Em vez de digitar
instruções completas toda vez, selecione um prompt e deixe a IA preencher os detalhes.

## ✨ O Que São MCP Prompts?

No Model Context Protocol, **prompts** são templates de mensagem definidos pelo servidor.
Diferente de ferramentas (que executam código automaticamente), prompts são **mensagens iniciais**
que o usuário pode selecionar de uma lista em seu editor. A IA então usa o
template para invocar as ferramentas GitPR apropriadas para atender à solicitação.

## 📋 Prompts Disponíveis

| Prompt | O que faz | Ferramentas usadas |
|--------|-----------|--------------------|
| **Review PR** | Revisão completa de código de todas as alterações na branch atual | `full_review` |
| **Generate Commit Message** | Gera uma mensagem Conventional Commits a partir de alterações não commitadas | `generate_commit_message` |
| **Create PR Description** | Gera título e corpo para um Pull Request | `generate_pr_description` |
| **Run Code Linter** | Verifica alterações não commitadas contra as regras do `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Gera uma issue estruturada a partir das alterações atuais | `generate_issue` |
| **Trace Code Origin** | Investiga o histórico de uma região específica do código | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtém informações da branch atual e lista skills/templates disponíveis | `get_git_context`, `skill://list` |

## 🚀 Como Usar

Uma vez que o servidor MCP esteja configurado em seu editor, os prompts aparecem na lista
de prompts junto com outros prompts de servidores MCP. A localização exata varia por editor:

- **VS Code / Cursor:** No painel de chat de IA, procure pelo seletor "Prompts"
- **Claude Desktop:** Prompts aparecem como opções selecionáveis na interface de chat
- **Claude Code:** Use a lista de prompts no painel de chat
- **Zed:** Disponível na lista de prompts do assistente inline

Selecione um prompt e a IA invocará automaticamente as ferramentas GitPR apropriadas
para atender à solicitação.

## 🔧 Como Funciona

Cada prompt é definido como uma função decorada com `@mcp.prompt()` em
`src/mcp_server.py`. O conteúdo do prompt é carregado de **arquivos de template**
armazenados no diretório `templates/`:

```
templates/gitpr.prompt.review.md       (Inglês)
templates/gitpr.prompt.review.pt_br.md  (Português Brasileiro)
templates/gitpr.prompt.review.pt_pt.md  (Português Europeu)
templates/gitpr.prompt.review.es_es.md  (Espanhol)
templates/gitpr.prompt.review.fr_fr.md  (Francês)
```

Este design baseado em templates significa que as mensagens dos prompts podem ser
atualizadas e traduzidas independentemente do código Python. O servidor MCP carrega
a variante de idioma apropriada com base na configuração `GITPR_LANG` do usuário,
com fallback para o inglês.

Exemplo — o template do prompt "Review PR" (`gitpr.prompt.review.pt_br.md`):

```
Por favor, revise todas as alterações na minha branch atual executando uma
revisão completa de código contra origin/main. Execute também o linter estático
para verificar problemas de qualidade de código. Combine os resultados em um
único relatório abrangente com: 1) resumo das alterações, 2) problemas críticos
encontrados, 3) violações do linter, e 4) melhorias sugeridas.
```

O agente de IA que receber esta mensagem irá então chamar `full_review`, `run_linter`,
e compor uma resposta de revisão abrangente com base nos resultados.

### Recursos de Prompt

Os templates de prompt também são expostos como **recursos** MCP sob o esquema
URI `prompt://`, para que agentes de IA possam ler o conteúdo bruto do template:

| URI | Conteúdo |
|-----|----------|
| `prompt://list` | Lista JSON de todas as URIs de prompt disponíveis |
| `prompt://review` | Template do prompt de revisão de PR |
| `prompt://commit` | Template do prompt de mensagem de commit |
| `prompt://pr` | Template do prompt de descrição de PR |
| `prompt://linter` | Template do prompt do linter |
| `prompt://issue` | Template do prompt de issue |
| `prompt://blame` | Template do prompt de origem de código |
| `prompt://explore` | Template do prompt de contexto do projeto |

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Como configurar MCP para seu editor
- [Code Review com IA](code-review-ia.md) — Guia dos modos de revisão de código
- [Mensagens de Commit com IA](commit-message-ia.md) — Guia de Conventional Commits
- [Modo de Descrição de PR](pr-descricao-padrao.md) — Fluxo de geração de PR

---
**Dica profissional:** Combine prompts com skills (arquivos `.gitpr.*.md`) para
personalizar o comportamento da IA conforme as convenções da sua equipe. Execute
`gitpr --install` para configurar tudo de uma vez.
