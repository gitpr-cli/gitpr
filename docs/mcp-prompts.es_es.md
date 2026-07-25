# MCP Prompts — Plantillas de Mensaje para Flujos Comunes

El servidor MCP de GitPR expone **prompts** (plantillas de mensaje predefinidas) que
le ayudan a componer tareas comunes de GitPR en el chat de IA de su editor. En lugar de escribir
instrucciones completas cada vez, seleccione un prompt y deje que la IA complete los detalles.

## ¿Qué Son los MCP Prompts?

En el Model Context Protocol, los **prompts** son plantillas de mensaje definidas por el servidor.
A diferencia de las herramientas (que ejecutan código automáticamente), los prompts son **mensajes iniciales**
que el usuario puede seleccionar de una lista en su editor. La IA usa entonces la
plantilla para invocar las herramientas GitPR adecuadas para cumplir con la solicitud.

## Prompts Disponibles

| Prompt | Qué hace | Herramientas usadas |
|--------|----------|---------------------|
| **Review PR** | Revisión de código completa de todos los cambios en la branch actual | `full_review` |
| **Generate Commit Message** | Genera un mensaje en formato Conventional Commits a partir de cambios no consolidados | `generate_commit_message` |
| **Create PR Description** | Genera un título y cuerpo para un Pull Request | `generate_pr_description` |
| **Run Code Linter** | Verifica cambios no consolidados contra las reglas de `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Genera una issue estructurada a partir de los cambios actuales | `generate_issue` |
| **Trace Code Origin** | Investiga el historial de una región específica del código | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtiene información de la branch actual y lista skills/templates disponibles | `get_git_context`, `skill://list` |

## Cómo Usar

Una vez que el servidor MCP esté configurado en su editor, los prompts aparecen en la lista
de prompts junto con otros prompts de servidores MCP. La ubicación exacta varía según el editor:

- **VS Code / Cursor:** En el panel de chat de IA, busque el selector "Prompts"
- **Claude Desktop:** Los prompts aparecen como opciones seleccionables en la interfaz de chat
- **Claude Code:** Use la lista de prompts en el panel de chat
- **Zed:** Disponible en la lista de prompts del asistente inline

Seleccione un prompt y la IA invocará automáticamente las herramientas GitPR adecuadas
para cumplir con la solicitud.

## Cómo Funciona

Cada prompt se define como una función decorada con `@mcp.prompt()` en
`src/mcp_server.py`. La función devuelve una cadena de mensaje que el agente de IA del editor
envía al modelo, instruyéndolo para llamar a herramientas GitPR específicas con los
parámetros adecuados.

Ejemplo — el prompt "Review PR":

```python
@mcp.prompt()
def review_pr_prompt() -> str:
    return (
        "Review all changes in my current branch. "
        "Run a full review against origin/main, "
        "check the linter, and suggest improvements."
    )
```

El agente de IA que reciba este mensaje llamará entonces a `full_review`, `run_linter`,
y compondrá una respuesta de revisión exhaustiva basada en los resultados.

## Documentación Relacionada

- [Integración MCP](mcp-integration.md) — Cómo configurar MCP para su editor
- [Code Review con IA](code-review-ia.md) — Guía de los modos de revisión de código
- [Mensajes de Commit con IA](commit-message-ia.md) — Guía de Conventional Commits
- [Modo de Descripción de PR](pr-descricao-padrao.md) — Flujo de generación de PR

---
**Consejo profesional:** Combine prompts con skills (archivos `.gitpr.*.md`) para personalizar
el comportamiento de la IA según las convenciones de su equipo. Ejecute `gitpr --install` para configurar
todo de una vez.
