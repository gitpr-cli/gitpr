# Asistente de Configuración Interactivo de GitPR (`--install`)

El comando `gitpr --install` ejecuta un asistente interactivo guiado que prepara el entorno de tu proyecto con todas las configuraciones esenciales de GitPR en un solo flujo. Consolida varios pasos de configuración manual en una experiencia fluida.

## ✨ Qué Hace

El asistente te guía a través de **4 pasos**, solicitando confirmación antes de cada uno:

| Paso | Qué configura | Comando equivalente |
|------|---------------|---------------------|
| 1. Skill Templates | Descarga los archivos de plantilla `.gitpr.*.md` y `.gitpr.linter.yml` | `gitpr --skill` |
| 2. Git Hooks | Instala los hooks `pre-commit` y `prepare-commit-msg` localmente | `gitpr --installhooks` |
| 3. Configuración MCP | Detecta y configura automáticamente editores (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 4. Verificación de Clave API | Verifica o solicita la clave API de tu proveedor de IA | Asistente de primera ejecución |

Al final, se muestra un enlace a esta documentación como referencia.

## 🚀 Cómo Usar

```bash
gitpr --install
```

El asistente:
1. Mostrará un encabezado de bienvenida
2. Para cada paso: explicará qué hace → pedirá confirmación (`[Y/n]`) → ejecutará u omitirá
3. Mostrará los resultados y la URL de documentación al finalizar

Cada paso se puede **omitir** respondiendo `n` (no) cuando se solicite. Los pasos omitidos se pueden ejecutar más tarde individualmente usando sus comandos equivalentes.

## 📋 Prerrequisitos

- **Conexión a internet:** Necesaria para descargar plantillas, hooks y verificar actualizaciones.
- **Repositorio Git:** El comando debe ejecutarse dentro de un proyecto git (necesario para hooks y análisis de diff).
- **Entorno Python:** GitPR debe estar instalado y accesible en tu PATH.

## 📖 Detalles Paso a Paso

### Paso 1 — Skill Templates

Descarga los archivos de plantilla de contexto de IA en la carpeta `.gitpr/skill/` de tu proyecto:

- `.gitpr.commit.md` — Reglas para la generación de mensajes de commit
- `.gitpr.pr.md` — Estructura requerida para descripciones de PR
- `.gitpr.review.md` — Enfoque arquitectónico para code reviews
- `.gitpr.filereview.md` — Reglas de cohesión y acoplamiento para auditorías de archivos
- `.gitpr.issue.md` — Estructura para la generación estandarizada de issues
- `.gitpr.blame.md` — Enfoque para el rastreo de código legado
- `.gitpr.linter.yml` — Reglas personalizadas de análisis estático

Estos archivos **nunca se sobrescriben** si ya existen. Puedes editarlos libremente para personalizar el comportamiento de la IA según las convenciones de tu equipo.

📚 Ver también: [Sistema de Skills y Plantillas](skill-template.md)

### Paso 2 — Git Hooks

Instala dos hooks locales de Git en `.git/hooks/`:

- **`pre-commit`** — Ejecuta el linter estático (`.gitpr.linter.yml`) antes de cada commit, bloqueando el código que viola tus reglas.
- **`prepare-commit-msg`** — Usa IA para generar un mensaje en formato Conventional Commits y lo inyecta en tu editor de commits.

Esto habilita la práctica **Shift-Left** — detectando problemas en la máquina del desarrollador antes de que lleguen a CI/CD o a la revisión de código.

📚 Ver también: [Git Hooks Locales](git-hooks-locais.md)

### Paso 3 — Configuración MCP

Detecta automáticamente qué editores con IA utilizas y crea los archivos de configuración necesarios:

| Editor | Archivo de configuración creado |
|--------|----------------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Una vez configurado, puedes usar lenguaje natural en el chat de IA de tu editor para invocar las herramientas de GitPR: "Revisa mis cambios", "Genera un mensaje de commit", "Crea una descripción de PR", etc.

Los archivos de configuración existentes se **fusionan** — otros servidores MCP nunca se sobrescriben.

📚 Ver también: [Integración MCP](mcp-integration.md)

### Paso 4 — Configuración de Clave API

Verifica si la clave API de tu proveedor de IA ya está configurada:

- **Si está configurada:** Muestra un mensaje de éxito — estás listo para empezar.
- **Si falta:** Ofrece configurarla interactivamente. La clave se cifra con Fernet (cifrado simétrico) y se almacena de forma segura en `~/.gitpr/.env`.

Puedes omitir este paso y configurarlo más tarde ejecutando `gitpr` (que activa el asistente de primera ejecución) o editando `~/.gitpr/.env` directamente.

📚 Ver también: [Proveedores de IA](providers-ia.md)

## 🔄 Ejecutar Pasos Individuales Más Tarde

Si omitiste un paso, siempre puedes ejecutar su comando equivalente más tarde:

```bash
gitpr --skill              # Paso 1: Descargar plantillas
gitpr --installhooks    # Paso 2: Instalar Git hooks
gitpr-mcp --install auto   # Paso 3: Configurar MCP
gitpr                      # Paso 4: Clave API (asistente de primera ejecución)
```

## ⚙️ Entornos CI/CD

En pipelines CI/CD (detectados por las variables de entorno `CI` o `GITHUB_ACTIONS`), GitPR **no** solicitará claves API de forma interactiva. Configura tu clave con anticipación usando variables de entorno o GitHub Secrets.

---
**Pro tip:** Ejecuta `gitpr --install` en cada clon nuevo para tener la experiencia completa de GitPR configurada en segundos.
