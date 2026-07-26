# MCP Prompts — Plantillas de Mensaje para Flujos Comunes

El servidor MCP de GitPR expone **prompts** (plantillas de mensaje predefinidas) que
te ayudan a componer tareas comunes de GitPR en el chat de IA de tu editor. En lugar
de escribir instrucciones completas cada vez, selecciona un prompt y deja que la IA
complete los detalles.

## ✨ ¿Qué Son los MCP Prompts?

En el Model Context Protocol, los **prompts** son plantillas de mensaje definidas por
el servidor. A diferencia de las herramientas (que ejecutan código automáticamente),
los prompts son **mensajes iniciales** que el usuario puede seleccionar de una lista
en su editor. La IA utiliza entonces la plantilla para invocar las herramientas GitPR
adecuadas para responder a la solicitud.

## 📋 Prompts Disponibles

| Prompt | Qué hace | Herramientas usadas |
|--------|----------|---------------------|
| **Review PR** | Revisión completa de código de todos los cambios en la rama actual | `full_review` |
| **Generate Commit Message** | Genera un mensaje Conventional Commits a partir de cambios no confirmados | `generate_commit_message` |
| **Create PR Description** | Genera título y cuerpo para un Pull Request | `generate_pr_description` |
| **Run Code Linter** | Verifica cambios no confirmados contra las reglas de `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Genera una issue estructurada a partir de los cambios actuales | `generate_issue` |
| **Trace Code Origin** | Investiga el historial de una región específica del código | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtiene información de la rama actual y lista skills/plantillas disponibles | `get_git_context`, `skill://list` |

## 🚀 Cómo Usar

Una vez configurado el servidor MCP en tu editor, los prompts aparecen en la lista
de prompts junto con otros prompts de servidores MCP. La ubicación exacta varía
según el editor:

- **VS Code / Cursor:** En el panel de chat de IA, busca el selector "Prompts"
- **Claude Desktop:** Los prompts aparecen como opciones seleccionables en la interfaz de chat
- **Claude Code:** Usa la lista de prompts en el panel de chat
- **Zed:** Disponible en la lista de prompts del asistente inline

Selecciona un prompt y la IA invocará automáticamente las herramientas GitPR
adecuadas para responder a la solicitud.

## 🔧 Cómo Funciona

Cada prompt se define como una función decorada con `@mcp.prompt()` en
`src/mcp_server.py`. El contenido del prompt se carga desde **archivos de plantilla**
almacenados en el directorio `templates/`:

```
templates/gitpr.prompt.review.md       (Inglés)
templates/gitpr.prompt.review.pt_br.md  (Portugués Brasileño)
templates/gitpr.prompt.review.pt_pt.md  (Portugués Europeo)
templates/gitpr.prompt.review.es_es.md  (Español)
templates/gitpr.prompt.review.fr_fr.md  (Francés)
```

Este diseño basado en plantillas significa que los mensajes de los prompts pueden
actualizarse y traducirse independientemente del código Python. El servidor MCP carga
la variante de idioma adecuada según la configuración `GITPR_LANG` del usuario,
con fallback al inglés.

Ejemplo — la plantilla del prompt "Review PR" (`gitpr.prompt.review.es_es.md`):

```
Por favor, revisa todos los cambios en mi rama actual ejecutando una revisión
completa de código contra origin/main. Ejecuta también el linter estático para
verificar problemas de calidad de código. Combina los resultados en un único
informe completo con: 1) resumen de cambios, 2) problemas críticos encontrados,
3) violaciones del linter, y 4) mejoras sugeridas.
```

El agente de IA que reciba este mensaje llamará a `full_review`, `run_linter`,
y compondrá una respuesta de revisión completa basada en los resultados.

### Recursos de Prompt

Las plantillas de prompt también se exponen como **recursos** MCP bajo el esquema
URI `prompt://`, para que los agentes de IA puedan leer el contenido bruto de la
plantilla:

| URI | Contenido |
|-----|-----------|
| `prompt://list` | Lista JSON de todas las URIs de prompt disponibles |
| `prompt://review` | Plantilla del prompt de revisión de PR |
| `prompt://commit` | Plantilla del prompt de mensaje de commit |
| `prompt://pr` | Plantilla del prompt de descripción de PR |
| `prompt://linter` | Plantilla del prompt del linter |
| `prompt://issue` | Plantilla del prompt de issue |
| `prompt://blame` | Plantilla del prompt de origen de código |
| `prompt://explore` | Plantilla del prompt de contexto del proyecto |

## 📚 Documentación Relacionada

- [Integración MCP](mcp-integration.md) — Cómo configurar MCP para tu editor
- [Code Review con IA](code-review-ia.md) — Guía de modos de revisión de código
- [Mensajes de Commit con IA](commit-message-ia.md) — Guía de Conventional Commits
- [Modo de Descripción de PR](pr-descricao-padrao.md) — Flujo de generación de PR

---
**Consejo profesional:** Combina prompts con skills (archivos `.gitpr.*.md`) para
personalizar el comportamiento de la IA según las convenciones de tu equipo. Ejecuta
`gitpr --install` para configurarlo todo de una vez.
