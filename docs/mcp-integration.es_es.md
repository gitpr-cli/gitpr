# Integración MCP — GitPR

GitPR soporta el **Model Context Protocol (MCP)**, permitiendo la integración directa
con editores y herramientas de IA compatibles con MCP como **VS Code**, **Cursor** y
**Claude Desktop**.

Al conectarse, GitPR expone sus capacidades con IA como herramientas que el
asistente de IA de su editor puede invocar — sin salir del editor ni abrir una terminal.

## Herramientas Disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `get_git_context` | Rama actual, nombre del repositorio y URL del remote |
| `analyze_diff` | Diff git de cambios no commiteados (`git diff HEAD`) |
| `get_full_diff` | Diff completo contra origin/main (`git fetch` + diff) |
| `generate_commit_message` | Mensaje de commit en formato Conventional Commits generado por IA |
| `review_code` | Code review con IA de cambios locales (no commiteados) |
| `full_review` | Code review con IA de todos los cambios desde origin/main |
| `generate_pr_description` | Descripción completa de PR (título + cuerpo) |
| `run_linter` | Linter estático basado en reglas de `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + clasificación IA (ORIGIN vs REFACTORING) |
| `generate_issue` | Issue estructurada a partir de diff, historial o contexto de blame |

## Recursos Disponibles

| URI | Contenido |
|-----|-----------|
| `skill://list` | Lista de todos los URIs de plantillas de skill disponibles |
| `skill://pr` | Instrucciones de IA personalizadas para descripciones de PR |
| `skill://commit` | Instrucciones de IA personalizadas para mensajes de commit |
| `skill://review` | Instrucciones de IA personalizadas para code reviews |
| `skill://filereview` | Instrucciones de IA personalizadas para auditorías de archivos |
| `skill://issue` | Instrucciones de IA personalizadas para generación de issues |
| `skill://blame` | Instrucciones de IA personalizadas para análisis de blame |
| `linter://config` | Reglas YAML del linter (`.gitpr.linter.yml`) |

## Configuración en Editores

### VS Code

Cree `.vscode/mcp.json` en la raíz de su proyecto:

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

O instale globalmente a través de la configuración de VS Code.

### Cursor

Cree `.cursor/mcp.json` en la raíz de su proyecto:

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

Agregue a `claude_desktop_config.json`:

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

Agregue a `settings.json`:

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

## Ejemplos de Uso

Después de conectar GitPR vía MCP, puede usar lenguaje natural en el chat de IA
de su editor:

- **"Revisa mis cambios actuales"** → llama a `review_code`
- **"Genera un mensaje de commit para estos cambios"** → llama a `generate_commit_message`
- **"Crea una descripción de PR de mi rama"** → llama a `generate_pr_description`
- **"Ejecuta el linter en mi diff"** → llama a `run_linter`
- **"Rastrea el origen de las líneas 10-20 en src/main.py"** → llama a `analyze_blame`
- **"Genera una issue a partir de mis cambios"** → llama a `generate_issue`
- **"¿En qué rama estoy?"** → llama a `get_git_context`

## Requisitos Previos

1. **GitPR instalado:** `pip install gitpr-cli` o el binario standalone
2. **Claves de API configuradas:** Ejecute `gitpr` una vez de forma interactiva para
   configurar las claves de API, o cree `~/.gitpr/.env` manualmente con sus claves encriptadas
3. **Un editor compatible con MCP:** VS Code, Cursor, Zed, Claude Desktop, etc.

## Cómo Funciona

El comando `gitpr-mcp` inicia un servidor MCP mediante **transporte stdio** (entrada/salida
estándar). El editor lo ejecuta como un proceso hijo y se comunica a través de mensajes
JSON-RPC 2.0.

Para mantener el canal JSON-RPC limpio, la salida de terminal de GitPR (banners, spinners,
mensajes coloreados) se redirige automáticamente a stderr al ejecutarse en
modo MCP. Esto no requiere ninguna configuración — ocurre de forma transparente.

## Solución de Problemas

### El editor no descubre las herramientas de GitPR
- Verifique que `gitpr-mcp` esté en su PATH: `which gitpr-mcp` (Linux/macOS) o `where gitpr-mcp` (Windows)
- Ejecute `pip install -e .` desde el directorio fuente de GitPR si está desarrollando localmente
- Revise los logs del editor para errores de conexión MCP

### Las herramientas devuelven errores
- Asegúrese de que las claves de API estén configuradas en `~/.gitpr/.env`
- Revise la salida stderr del servidor MCP (visible en los logs del editor)
- Ejecute `gitpr --help` normalmente para verificar que la CLI funciona

### Error "El prompt interactivo no está disponible"
- Necesita preconfigurar las claves de API en `~/.gitpr/.env` — el modo MCP no puede solicitar interactivamente
- Ejecute `gitpr` una vez en la terminal para completar la configuración inicial
