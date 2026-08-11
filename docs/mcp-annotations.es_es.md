# Anotaciones de Herramientas MCP — Sugerencias para Integración con IDEs

Las herramientas MCP de GitPR incluyen **anotaciones** (`readOnlyHint`, `destructiveHint`,
`idempotentHint`) que ayudan a los IDEs y agentes de IA a comprender el comportamiento
de la herramienta rápidamente. Estas anotaciones permiten decisiones de IU más
inteligentes — como mostrar diálogos de confirmación para operaciones destructivas
o almacenar en caché los resultados de llamadas idempotentes.

## ✨ ¿Qué Son las Anotaciones de Herramienta?

En el Model Context Protocol, cada herramienta puede declarar **sugerencias** de
comportamiento a través de un objeto `ToolAnnotations`. Estas sugerencias no son
impuestas por el servidor — son metadatos consultivos que el IDE/cliente puede
usar para mejorar la experiencia del usuario.

Los campos de anotación estándar son:

| Campo | Tipo | Significado |
|-------|------|-------------|
| `readOnlyHint` | `bool` | Si `true`, la herramienta **no** modifica su entorno |
| `destructiveHint` | `bool` | Si `true`, la herramienta puede realizar actualizaciones destructivas (solo relevante cuando `readOnlyHint` es `false`) |
| `idempotentHint` | `bool` | Si `true`, llamar a la herramienta repetidamente con los mismos argumentos no tiene efectos colaterales adicionales |

## 📋 Anotaciones de las Herramientas GitPR

### Herramientas de Solo Lectura (sin efectos colaterales)

Estas herramientas solo leen estado local — seguras para llamar en cualquier
momento, sin necesidad de confirmación:

| Herramienta | `readOnlyHint` | `idempotentHint` |
|------|:---:|:---:|
| `get_git_context` | ✅ | ✅ |
| `analyze_diff` | ✅ | ✅ |
| `run_linter` | ✅ | ✅ |

### Herramientas con Efectos Colaterales (llamadas de red)

Estas herramientas realizan llamadas de red (APIs de IA, git fetch) pero **no**
escriben ni eliminan archivos. Son seguras para invocar sin advertencia de
operación destructiva:

| Herramienta | `readOnlyHint` | `destructiveHint` | `idempotentHint` |
|------|:---:|:---:|:---:|
| `get_full_diff` | ❌ | ❌ | ❌ |
| `generate_commit_message` | ❌ | ❌ | ❌ |
| `review_code` | ❌ | ❌ | ❌ |
| `full_review` | ❌ | ❌ | ❌ |
| `generate_pr_description` | ❌ | ❌ | ❌ |
| `analyze_blame` | ❌ | ❌ | ❌ |
| `generate_issue` | ❌ | ❌ | ❌ |

> **Nota:** `destructiveHint` es `false` para todas las herramientas GitPR porque
> ninguna de ellas modifica, elimina o sobrescribe archivos. Los "efectos colaterales"
> se limitan a llamadas a APIs de red.

## 🚀 Beneficios para la Integración con IDEs

Las anotaciones permiten a los editores:

- **VS Code / Cursor:** Mostrar icono de escudo para herramientas de solo lectura,
  advertir antes de ejecutar herramientas marcadas como `destructiveHint=true`
- **Claude Desktop:** Organizar herramientas en grupos seguro/inseguro en la UI
- **Claude Code:** Almacenar en caché resultados de herramientas idempotentes
  para evitar llamadas redundantes
- **Zed:** Mostrar el nivel de seguridad de la herramienta en el asistente inline

## 🔧 Implementación

Las anotaciones se establecen a través de la clase `ToolAnnotations` en `src/mcp_server.py`:

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    description=__("Obtiene la rama git actual, nombre del repositorio y URL del remote origin."),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def get_git_context() -> str:
    ...
```

La anotación de cada herramienta se elige en función de su comportamiento real:
- **Solo lectura + idempotente** para herramientas que solo inspeccionan estado local
- **No solo lectura + no destructiva** para herramientas que realizan llamadas de red
- Ninguna herramienta se marca como `destructiveHint=true` ya que GitPR nunca escribe archivos

## 🔧 Invocación Directa por CLI

La bandera `--tool` permite invocar cualquier herramienta anotada directamente desde la terminal,
omitiendo completamente el transporte MCP:

```bash
gitpr-mcp --tool get_git_context
gitpr-mcp --tool run_linter
```

En modo CLI, las anotaciones (`readOnlyHint`, `destructiveHint`, `idempotentHint`)
**no se aplican** — son sugerencias para clientes MCP (IDEs y agentes de IA) para
mejorar la UX. El comportamiento de la función subyacente es idéntico en ambas vías,
lo que hace que `--tool` sea útil para verificar que la semántica de las anotaciones
coincide con el comportamiento real (ej.: `run_linter` es `readOnlyHint` y de hecho no modifica nada).

Consulte [Integración MCP — Invocación Directa por CLI](mcp-integration.md#invocación-directa-por-cli)
para obtener detalles completos de uso.

## 📚 Documentación Relacionada

- [Integración MCP](mcp-integration.md) — Cómo configurar MCP para tu editor
- [MCP Prompts](mcp-prompts.md) — Plantillas de mensaje predefinidas para flujos comunes

---
**Consejo profesional:** Las anotaciones de herramienta son sugerencias, no garantías.
Configura las claves de API en `~/.gitpr/.env` antes de usar cualquier herramienta.
Ejecuta `gitpr --install` para configurarlo todo de una vez.
