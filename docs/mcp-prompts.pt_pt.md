# MCP Prompts — Modelos de Mensagem para Fluxos Comuns

O servidor MCP do GitPR expõe **prompts** (modelos de mensagem pré-definidos) que
ajudam a compor tarefas comuns do GitPR no chat de IA do seu editor. Em vez de escrever
instruções completas sempre, selecione um prompt e deixe a IA preencher os detalhes.

## ✨ O Que São MCP Prompts?

No Model Context Protocol, **prompts** são modelos de mensagem definidos pelo servidor.
Ao contrário das ferramentas (que executam código automaticamente), os prompts são
**mensagens iniciais** que o utilizador pode selecionar de uma lista no seu editor.
A IA utiliza então o modelo para invocar as ferramentas GitPR apropriadas para
responder ao pedido.

## 📋 Prompts Disponíveis

| Prompt | O que faz | Ferramentas usadas |
|--------|-----------|--------------------|
| **Review PR** | Revisão completa de código de todas as alterações na branch atual | `full_review` |
| **Generate Commit Message** | Gera uma mensagem Conventional Commits a partir de alterações não commitadas | `generate_commit_message` |
| **Create PR Description** | Gera título e corpo para um Pull Request | `generate_pr_description` |
| **Run Code Linter** | Verifica alterações não commitadas contra as regras do `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Gera uma issue estruturada a partir das alterações atuais | `generate_issue` |
| **Trace Code Origin** | Investiga o histórico de uma região específica do código | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtém informações da branch atual e lista skills/modelos disponíveis | `get_git_context`, `skill://list` |

## 🚀 Como Utilizar

Uma vez configurado o servidor MCP no seu editor, os prompts aparecem na lista
de prompts juntamente com outros prompts de servidores MCP. A localização exata
varia conforme o editor:

- **VS Code / Cursor:** No painel de chat de IA, procure o seletor "Prompts"
- **Claude Desktop:** Os prompts aparecem como opções selecionáveis na interface de chat
- **Claude Code:** Utilize a lista de prompts no painel de chat
- **Zed:** Disponível na lista de prompts do assistente inline

Selecione um prompt e a IA invocará automaticamente as ferramentas GitPR apropriadas
para responder ao pedido.

## 🔧 Como Funciona

Cada prompt é definido como uma função decorada com `@mcp.prompt()` em
`src/mcp_server.py`. O conteúdo do prompt é carregado a partir de **ficheiros de
modelo** armazenados no diretório `templates/`:

```
templates/gitpr.prompt.review.md       (Inglês)
templates/gitpr.prompt.review.pt_br.md  (Português Brasileiro)
templates/gitpr.prompt.review.pt_pt.md  (Português Europeu)
templates/gitpr.prompt.review.es_es.md  (Espanhol)
templates/gitpr.prompt.review.fr_fr.md  (Francês)
```

Este design baseado em modelos significa que as mensagens dos prompts podem ser
atualizadas e traduzidas independentemente do código Python. O servidor MCP carrega
a variante de idioma adequada com base na configuração `GITPR_LANG` do utilizador,
com fallback para o inglês.

Exemplo — o modelo do prompt "Review PR" (`gitpr.prompt.review.pt_pt.md`):

```
Por favor, reveja todas as alterações na minha branch atual executando uma
revisão completa de código contra origin/main. Execute também o linter estático
para verificar problemas de qualidade de código. Combine os resultados num
único relatório abrangente com: 1) resumo das alterações, 2) problemas críticos
encontrados, 3) violações do linter, e 4) melhorias sugeridas.
```

O agente de IA que receber esta mensagem irá então chamar `full_review`, `run_linter`,
e compor uma resposta de revisão abrangente com base nos resultados.

### Recursos de Prompt

Os modelos de prompt também são expostos como **recursos** MCP sob o esquema
URI `prompt://`, para que os agentes de IA possam ler o conteúdo bruto do modelo:

| URI | Conteúdo |
|-----|----------|
| `prompt://list` | Lista JSON de todas as URIs de prompt disponíveis |
| `prompt://review` | Modelo do prompt de revisão de PR |
| `prompt://commit` | Modelo do prompt de mensagem de commit |
| `prompt://pr` | Modelo do prompt de descrição de PR |
| `prompt://linter` | Modelo do prompt do linter |
| `prompt://issue` | Modelo do prompt de issue |
| `prompt://blame` | Modelo do prompt de origem de código |
| `prompt://explore` | Modelo do prompt de contexto do projeto |

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Como configurar o MCP para o seu editor
- [Code Review com IA](code-review-ia.md) — Guia dos modos de revisão de código
- [Mensagens de Commit com IA](commit-message-ia.md) — Guia de Conventional Commits
- [Modo de Descrição de PR](pr-descricao-padrao.md) — Fluxo de geração de PR

---
**Dica profissional:** Combine prompts com skills (ficheiros `.gitpr.*.md`) para
personalizar o comportamento da IA conforme as convenções da sua equipa. Execute
`gitpr --install` para configurar tudo de uma só vez.
