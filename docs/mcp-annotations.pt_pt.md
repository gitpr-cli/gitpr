# Anotações de Ferramentas MCP — Dicas para Integração com IDEs

As ferramentas MCP do GitPR incluem **anotações** (`readOnlyHint`, `destructiveHint`,
`idempotentHint`) que ajudam IDEs e agentes de IA a compreender o comportamento da
ferramenta rapidamente. Estas anotações permitem decisões de IU mais inteligentes —
como mostrar diálogos de confirmação para operações destrutivas ou armazenar em
cache resultados de chamadas idempotentes.

## ✨ O Que São Anotações de Ferramenta?

No Model Context Protocol, cada ferramenta pode declarar **dicas** comportamentais
através de um objeto `ToolAnnotations`. Estas dicas não são impostas pelo servidor —
são metadados consultivos que o IDE/cliente pode usar para melhorar a experiência do
utilizador.

Os campos de anotação padrão são:

| Campo | Tipo | Significado |
|-------|------|-------------|
| `readOnlyHint` | `bool` | Se `true`, a ferramenta **não** modifica o seu ambiente |
| `destructiveHint` | `bool` | Se `true`, a ferramenta pode realizar atualizações destrutivas (só é relevante quando `readOnlyHint` é `false`) |
| `idempotentHint` | `bool` | Se `true`, chamar a ferramenta repetidamente com os mesmos argumentos não tem efeitos colaterais adicionais |

## 📋 Anotações das Ferramentas GitPR

### Ferramentas Só de Leitura (sem efeitos colaterais)

Estas ferramentas apenas leem estado local — seguras para chamar a qualquer
momento, sem necessidade de confirmação:

| Ferramenta | `readOnlyHint` | `idempotentHint` |
|------|:---:|:---:|
| `get_git_context` | ✅ | ✅ |
| `analyze_diff` | ✅ | ✅ |
| `run_linter` | ✅ | ✅ |

### Ferramentas com Efeitos Colaterais (chamadas de rede)

Estas ferramentas fazem chamadas de rede (APIs de IA, git fetch) mas **não**
escrevem ou eliminam ficheiros. São seguras para invocar sem aviso de operação
destrutiva:

| Ferramenta | `readOnlyHint` | `destructiveHint` | `idempotentHint` |
|------|:---:|:---:|:---:|
| `get_full_diff` | ❌ | ❌ | ❌ |
| `generate_commit_message` | ❌ | ❌ | ❌ |
| `review_code` | ❌ | ❌ | ❌ |
| `full_review` | ❌ | ❌ | ❌ |
| `generate_pr_description` | ❌ | ❌ | ❌ |
| `analyze_blame` | ❌ | ❌ | ❌ |
| `generate_issue` | ❌ | ❌ | ❌ |

> **Nota:** `destructiveHint` é `false` para todas as ferramentas GitPR porque
> nenhuma delas modifica, elimina ou sobrescreve ficheiros. Os "efeitos colaterais"
> limitam-se a chamadas de API de rede.

## 🚀 Benefícios para Integração com IDEs

As anotações permitem que os editores:

- **VS Code / Cursor:** Mostrar ícone de escudo para ferramentas só de leitura,
  avisar antes de executar ferramentas marcadas como `destructiveHint=true`
- **Claude Desktop:** Organizar ferramentas em grupos seguro/inseguro na IU
- **Claude Code:** Armazenar em cache resultados de ferramentas idempotentes
  para evitar chamadas redundantes
- **Zed:** Exibir nível de segurança da ferramenta no assistente inline

## 🔧 Implementação

As anotações são definidas através da classe `ToolAnnotations` em `src/mcp_server.py`:

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    description=__("Obtém a branch git atual, nome do repositório e URL do remote origin."),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def get_git_context() -> str:
    ...
```

A anotação de cada ferramenta é escolhida com base no seu comportamento real:
- **Só de leitura + idempotente** para ferramentas que apenas inspecionam estado local
- **Não só de leitura + não destrutiva** para ferramentas que fazem chamadas de rede
- Nenhuma ferramenta é marcada como `destructiveHint=true` já que o GitPR nunca escreve ficheiros

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Como configurar o MCP para o seu editor
- [MCP Prompts](mcp-prompts.md) — Modelos de mensagem pré-definidos para fluxos comuns

---
**Dica profissional:** Anotações de ferramenta são dicas, não garantias. Configure
as chaves de API em `~/.gitpr/.env` antes de usar qualquer ferramenta. Execute
`gitpr --install` para configurar tudo de uma só vez.
