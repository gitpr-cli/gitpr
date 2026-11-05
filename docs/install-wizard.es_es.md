# Asistente de Configuración Interactivo de GitPR (`--install`)

El comando `gitpr --install` ejecuta un asistente guiado interactivo que prepara el entorno de su proyecto con todas las configuraciones esenciales de GitPR en un único flujo. Consolida varios pasos de configuración manual en una experiencia integrada.

## ✨ Qué Hace

El asistente le guía a través de **5 pasos**, solicitando confirmación antes de cada uno:

| Paso | Qué configura | Comando equivalente |
|------|---------------|---------------------|
| 1. Configuración Local del Proyecto | Inicializa `.gitpr/conf/` (`gitpr.config.yml`, `gitpr.smart-excludes.json`) | `gitpr seed` |
| 2. Plantillas de Skill & Linter | Descarga `.gitpr.*.md` y `.gitpr.linter.yml` en `.gitpr/skill/` (con opción de linters externos) | `gitpr --skill` / `gitpr --linter-setup` |
| 3. Git Hooks | Instala hooks `pre-commit` y `prepare-commit-msg` localmente | `gitpr --installhooks` |
| 4. Configuración MCP | Detecta automáticamente y configura editores (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 5. Verificación de Clave de API | Verifica o solicita la clave de API de su proveedor de IA | Asistente de primera ejecución |

Al finalizar, se muestra un enlace a esta documentación como referencia.

El archivo de configuración del proyecto `.gitpr/conf/gitpr.config.yml` define la rama a la que deben dirigirse los pull requests de este repositorio — `PR_DEFAULT_BASE` cuando está configurado, `main` en caso contrario. Los archivos existentes nunca se sobrescriben por defecto. Confírmelo en el repositorio para que todo el equipo apunte a la misma rama ([Publicación de Pull Request](pull-request-publication.es_es.md#91-el-archivo-del-proyecto)).

## 🚀 Cómo Usar

```bash
gitpr --install
```

El asistente:
1. Mostrará un encabezado de bienvenida
2. Para cada paso: explicará qué hace → solicitará confirmación (`[Y/n]`) → ejecutará o saltará
3. Mostrará los resultados y la URL de la documentación al finalizar

Cada paso se puede **saltar** respondiendo `n` (no) cuando se solicite. Los pasos omitidos se pueden ejecutar más adelante de forma individual utilizando sus comandos equivalentes.

## 📋 Requisitos Previos

- **Conexión a internet:** Necesaria para descargar plantillas, hooks y verificar actualizaciones.
- **Repositorio Git:** El comando debe ejecutarse dentro de un proyecto git (requerido para hooks y análisis de diff).
- **Entorno Python:** GitPR debe estar instalado y accesible en su PATH.

## 📖 Detalles Paso a Paso

### Paso 1 — Configuración Local del Proyecto

Inicializa los archivos de configuración locales en `.gitpr/conf/`:
- **`gitpr.config.yml`** — Configuración de la rama base de PR para el repositorio.
- **`gitpr.smart-excludes.json`** — Reglas específicas del proyecto de exclusión de archivos y carpetas para diffs de IA, unificadas con la lista global en runtime.

### Paso 2 — Plantillas de Skill & Linter

Descarga los archivos de plantilla de contexto de IA en la carpeta `.gitpr/skill/` de su proyecto:

- `.gitpr.commit.md` — Reglas para la generación de mensajes de commit
- `.gitpr.pr.md` — Estructura requerida para descripciones de PR
- `.gitpr.review.md` — Enfoque arquitectónico para revisiones de código
- `.gitpr.filereview.md` — Reglas de cohesión y acoplamiento para auditorías de archivos
- `.gitpr.issue.md` — Estructura para generación estandarizada de issues
- `.gitpr.blame.md` — Enfoque para rastreo de código heredado
- `.gitpr.linter.yml` — Reglas personalizadas de análisis estático local

Estos archivos **nunca se sobrescriben** si ya existen. Edítelos libremente para personalizar el comportamiento de la IA según las convenciones de su equipo.

Al descargar las plantillas, el asistente ofrece opcionalmente configurar puentes para linters externos (ESLint, PHPCS, Stylelint).

📚 Consulte también: [Sistema de Skills y Plantillas](skill-template.es_es.md)

### Paso 3 — Git Hooks

Instala dos Git hooks locales en `.git/hooks/`:

- **`pre-commit`** — Ejecuta el linter estático (`.gitpr.linter.yml`) antes de cada commit, bloqueando el código que viole sus reglas.
- **`prepare-commit-msg`** — Utiliza IA para generar un mensaje bajo el estándar Conventional Commits y lo inyecta en su editor de commit.

Esto permite la práctica de **Shift-Left** — detectando problemas en la máquina del desarrollador antes de que lleguen a CI/CD o a la revisión de código.

📚 Consulte también: [Git Hooks Locales](git-hooks-locais.es_es.md)

### Paso 4 — Configuración MCP

Detecta automáticamente qué editores impulsados por IA utiliza y crea los archivos de configuración necesarios:

| Editor | Archivo de config creado |
|--------|--------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Una vez configurado, puede usar lenguaje natural en el chat de IA de su editor para invocar herramientas de GitPR: "Revisa mis cambios", "Genera un mensaje de commit", "Crea una descripción de PR", etc.

Los archivos de configuración existentes se **fusionan** — otros servidores MCP nunca se sobrescriben.

📚 Consulte también: [Integración MCP](mcp-integration.es_es.md)

### Paso 5 — Configuración de la Clave de API

Comprueba si la clave de API de su proveedor de IA ya está configurada:

- **Si está configurada:** Muestra un mensaje de éxito — está listo para comenzar.
- **Si falta:** Ofrece configurarla interactivamente. La clave se cifra con Fernet (cifrado simétrico) y se almacena de forma segura en `~/.gitpr/.env`.

Puede omitir este paso y configurarla más tarde ejecutando `gitpr` (que activa el asistente de primera ejecución) o editando `~/.gitpr/.env` directamente.

📚 Consulte también: [Proveedores de IA](providers-ia.es_es.md)

---

## ⚡ Sembrado Directo de Configuraciones (`gitpr seed`)

Para sembrar los archivos de configuración del proyecto directamente, sin pasar por todo el asistente interactivo:

```bash
gitpr seed
```

O utilizando la opción raíz:
```bash
gitpr --seed
```

### Opciones:
- `--force` / `-f`: Sobrescribe los archivos existentes con las plantillas predeterminadas.
- `--all` / `-a`: También descarga las 12 plantillas de prompts de IA en `.gitpr/skill/`.

## 🔄 Ejecutar Pasos Individuales Más Tarde

Si omitió un paso, siempre puede ejecutar su comando equivalente más adelante:

```bash
gitpr seed                 # Paso 1: Configuración del proyecto
gitpr --skill              # Paso 2: Descargar plantillas
gitpr --linter-setup       # Paso 2 (opcional): Linters externos
gitpr --installhooks       # Paso 3: Instalar Git hooks
gitpr-mcp --install auto   # Paso 4: Configurar MCP
gitpr                      # Paso 5: Clave de API (primera ejecución)
```

## ⚙️ Entornos CI/CD

En flujos de CI/CD (detectados por las variables de entorno `CI` o `GITHUB_ACTIONS`), GitPR **no** solicitará claves de API interactivamente. Configure su clave con anticipación mediante variables de entorno o GitHub Secrets.

---
**Consejo:** Ejecute `gitpr --install` o `gitpr seed` en cada nuevo clon para configurar el repositorio en segundos.
