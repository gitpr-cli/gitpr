# **🚀 GitPR - Automatización Inteligente de Code Review y Pull Requests**

El **GitPR** es una herramienta de Interfaz de Línea de Comandos (CLI) desarrollada en Python que actúa como un asistente de ingeniería de software directamente en la terminal. Combina la velocidad de las validaciones estáticas locales con el poder analítico de Inteligencias Artificiales (**Google Gemini**, **DeepSeek** y **Ollama** — local) para automatizar y elevar la calidad de Commits, Code Reviews, Issues y Pull Requests.

Además de la CLI, GitPR también opera como **servidor MCP (Model Context Protocol)** — exponiendo todas sus capacidades de IA a editores como VS Code, Cursor, Claude Desktop, Zed y Claude Code — y ofrece interfaces TUI (Textual) para publicación de PRs, creación de Issues, chat de programación en pareja y dashboard de métricas.

## **🎯 ¿Para qué sirve?**

El objetivo principal de GitPR es eliminar el trabajo repetitivo y garantizar un alto estándar de calidad (*Quality Gate*) en el ciclo de vida del desarrollo de software. Resuelve tres problemas principales:

1. **Historial de Git Contaminado:** Impone el uso de *Conventional Commits* y genera mensajes semánticos automáticamente — incluso mediante git hooks instalados en el repositorio.  
2. **Pull Requests Vacíos o Pobres:** Escribe descripciones detalladas basadas en el diff, separando los cambios técnicos del impacto en el negocio, y publica el PR directamente en GitHub mediante TUI.  
3. **Deuda Técnica y Bugs:** Realiza Code Reviews semánticos y validaciones de reglas (Regex) antes incluso de que el código salga de la máquina del desarrollador (enfoque *Shift-Left*), además de arqueología de código con `git blame` para rastrear el origen de las reglas de negocio.

---

## **✨ Funcionalidades Principales**

* **📝 Auto-Commit (`-c` / `--commit`):** Lee los cambios en *staged* (git diff) y genera un mensaje de commit conciso en formato imperativo (Conventional Commits). En modo hook (`--hook`), inyecta el mensaje directamente en el archivo temporal de Git; ignora merges, squashes y amends. Los commits llevan el trailer `Co-Authored-By`, añadido solo en el momento de la ejecución — las pantallas de edición de la TUI nunca lo muestran.  
* **📖 Generación de Pull Request → Publicador de PR (Predeterminado):** Analiza el diff entre la rama actual y la principal, generando un .md con resumen, impacto y detalles técnicos. A continuación abre una TUI (Textual) para revisar, editar y publicar el PR directamente en GitHub — con auto-commit validado por linter, push automático, actualización de PR existente y merge opcional. Modificadores: `--no-publish` (solo guarda localmente), `--no-edit` (publica directamente, sin TUI) y `--base <branch>` (rama de destino).  
* **🕵️ Code Review Inteligente (`-r` / `--review`):** Inspecciona el código modificado en busca de malas prácticas de arquitectura, violaciones de SOLID y vulnerabilidades de seguridad.  
* **🔬 Auditoría de Archivo Completo (`-i` / `--input`):** Permite apuntar GitPR a un archivo específico (p. ej., código legado) para que la IA realice un análisis arquitectónico de arriba a abajo, sugiriendo refactorizaciones para el archivo completo.  
* **⚡ Linter Estático Local (`-l` / `--linter`):** Un motor de Expresiones Regulares (Regex) ultrarrápido que se ejecuta localmente para detectar errores obvios (p. ej., console.log, claves hardcoded) sin gastar tokens de IA. También admite **linters externos** (ESLint, PHPCS, Stylelint) como puente Checkstyle — configurados mediante un asistente interactivo (`--linter-setup`).  
* **🪝 Integración con Git Hooks (`-ih` / `--installhooks`):** Inyecta GitPR en el ciclo natural de Git, ejecutando el Linter en un pre-commit o sugiriendo mensajes en un prepare-commit-msg. Instala **5 hooks** (pre-commit, prepare-commit-msg, pre-push, post-checkout, post-merge) con **auto-sync versionado y localizado** (EN, PT-BR, PT-PT, ES, FR).  
* **🗿 Arqueología de Código (`-b` / `--blame`):** Rastrea el origen de una regla de negocio con `git blame` + IA (profundidad máxima de 4 commits padre), clasificando cada commit como **ORIGIN** u **REFACTORING** y generando una línea de tiempo con resumen ejecutivo.  
* **📋 Issues Estandarizadas (`-is` / `--issue`):** Genera un borrador de Issue en formato **What / Why / Where / How** y abre una TUI para edición o publicación mediante la API REST de GitHub. Tiene **3 motores de contexto**: diff (predeterminado), historial de la rama (`-ht`) y blame (`-b file:lines`).  
* **💬 Chat de Programación en Pareja (`-ch` / `--chat`):** TUI interactiva donde la IA ve el diff actual y mantiene una conversación contextual, con memoria por rama, slash commands (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patch y exportación de sesión.  
* **🔌 Servidor MCP (`--mcp` / `gitpr-mcp`):** Expone todas las capacidades de IA como **12 tools**, **resources** y **7 prompts** para editores compatibles con MCP (VS Code, Cursor, Claude Desktop, Zed, Claude Code). Instalación automática mediante `gitpr-mcp --install <editor|auto>`. Invocación directa sin servidor persistente: `gitpr-mcp --tool <name> --tool-args '{...}'` — JSON en stdout, diagnóstico en stderr (seguro para pipes, scripts y CI).  
* **📊 Métricas y Telemetría Local (`--metrics` / `--dashboard`):** Recolección offline de eventos (comando, estado, proveedor, tokens, duración) con exportación CSV/JSON y dashboard TUI con alcance por repositorio, enriquecido con tokens reales leídos de la caché de prompts.  
* **🧙 Asistente de Configuración (`--install`):** Configuración guiada en 4 pasos — plantillas de skills, git hooks, configuración MCP en los editores detectados y verificación de la API key del proveedor de IA.  
* **🔎 Estado de Archivos (`--status`):** Lista archivos sin commitear categorizados (new / modified / deleted) — rápido, sin IA y sin red.  
* **🧩 Sistema de Plugins (`--plugins`):** Paquetes globales de reglas de linter (`~/.gitpr/plugins/linter/*.yml`) y prompts MCP (`~/.gitpr/plugins/prompts/*.md`) aplicados de forma aditiva en todos los proyectos.  
* **🔄 Multi-Model (Agnóstico de IA):** Permite elegir entre **Google Gemini**, **DeepSeek** u **Ollama** (local, sin red) como motor de razonamiento, alternando dinámicamente mediante .env o la flag `--provider`, con fallback automático entre proveedores.  
* **🌐 Internacionalización (`--lang`):** Interfaz en 5 idiomas con detección automática del sistema operativo, fallback al inglés y override temporal por flag.  
* **🗜️ Optimización de Tokens (Map-Reduce + Smart Excludes):** Los diffs por encima de ~90k tokens se dividen en chunks por archivo y se resumen (Map) antes de la consolidación final (Reduce). Los lockfiles, archivos minificados y la documentación se excluyen del diff automáticamente (listas remotas + configuración local por proyecto).  
* **🔄 Auto-Update (`-u` / `--update`):** Consulta los Releases de GitHub (binario) o PyPI (pip) y reemplaza su propio ejecutable (*hot-swap*) con rollback en caso de fallo.  

---

## **🛠️ Detalles de Desarrollo y Arquitectura**

GitPR fue diseñado con foco en **Rendimiento**, **Seguridad** y **Extensibilidad**.

### **1. Facade/Mediator (core.py)**

El módulo `core.py` orquesta todo: operaciones git, ensamblaje de prompts, caché, skills, hooks, smart excludes y salida de archivos. La CLI (`main.py`) solo enruta flags; los módulos especializados (IA, linter, blame, issues, MCP, métricas, TUI) son coordinados por el core. Los componentes visuales permanecen aislados en el sub-paquete `src/ui/`.

### **2. Sistema de "Skills" (Prompt Engineering Desacoplado)**

En lugar de tener los *prompts* de la IA fijos en el código Python, GitPR utiliza un sistema de archivos .md locales (Skills) que actúan como *System Instructions*.

* .gitpr.commit.md  
* .gitpr.pr.md  
* .gitpr.review.md  
* .gitpr.filereview.md  
* .gitpr.issue.md  
* .gitpr.blame.md  

Esto permite que cada equipo adapte la "personalidad" y las reglas de negocio de la IA sin cambiar una sola línea del código fuente de la herramienta. Los archivos viven en `.gitpr/skill/` (con migración automática de rutas legacy desde la raíz del proyecto).

### **3. Strategy Pattern para Proveedores de IA**

El módulo `ai_providers.py` aísla la comunicación con las APIs externas. El motor (Core) solo pide un JSON, y este módulo decide cómo formatear la solicitud usando el SDK de Google (Gemini) o el SDK de OpenAI (DeepSeek y Ollama — 100% compatibles con la API de OpenAI). Características:

* **Retry Automático** (3 intentos, intervalo de 2s) para inestabilidades de red.  
* **Fallback automático** al otro proveedor en caso de fallo del configurado.  
* **JSON estructurado obligatorio** y temperature 0.0 para salida determinista.  
* **Tiering de modelos por complejidad:** las tareas simples (commit) usan el modelo secundario/barato; las tareas avanzadas (review, PR, issue) usan el modelo primario.

### **4. Seguridad de Claves (Cryptography)**

Las claves de API (API_KEYS) nunca se guardan en texto plano. El módulo `security.py` utiliza la biblioteca cryptography (Fernet) para generar una clave maestra local y almacenar las credenciales cifradas en el archivo `~/.gitpr/.env`. El **GitHub PAT** sigue el mismo patrón y se valida contra `api.github.com/user` antes de cualquier uso, con bucle de re-autenticación (máx. 3 intentos) cuando expira.

### **5. Sistema de Caché MD5**

Para ahorrar consumo de Tokens de IA (dinero) y tiempo (latencia), GitPR crea un hash MD5 del *prompt* generado a partir del *diff*. Si el desarrollador pide un Code Review del mismo código dos veces, el sistema recupera la respuesta del directorio `~/.gitpr/cache/prompts/` al instante. Cada entrada guarda **repo + branch** — el doble filtro evita colisiones entre proyectos con el mismo nombre de rama, y el historial de PRs en caché alimenta el contexto de issues de historial (`-ht`).

### **6. Triple "Quality Gate" (Rendimiento)**

La herramienta fue diseñada para equilibrar el consumo de recursos:

* **Capa 1 (Linter Local):** Rápida (<100ms), offline, centrada en sintaxis (mediante linter_engine.py y .gitpr.linter.yml).  
* **Capa 2 (Linters Externos):** Puente Checkstyle — ejecuta ESLint/PHPCS/Stylelint y filtra errores solo para las líneas modificadas en el diff.  
* **Capa 3 (IA Cloud):** Profunda (2s-8s), online, centrada en semántica e intención.

### **7. Map-Reduce para Diffs Gigantes**

Cuando el diff supera ~90k tokens estimados, GitPR lo divide en chunks por archivo (preservando las cabeceras `diff --git`), pide a la IA un resumen técnico de cada parte (Map) y unifica todo en el mensaje final de commit, review, PR o issue (Reduce). Activación automática, sin flags — con progreso en consola y métrica propia.

### **8. Smart Excludes (Optimización de Tokens)**

Los archivos que no son código se eliminan del diff antes de enviarlo a la IA, con dos capas controladas remotamente: lockfiles/generados (`.lock`, `*.min.js`, `*.map`, `*.svg`…) y prosa de documentación (`*.md`, `*.txt`, `*.rst`…). La documentación modificada se comunica igualmente a la IA como **metadatos** (solo las rutas, sin contenido). Cada proyecto puede añadir exclusiones locales en `.gitpr/conf/gitpr.smart-excludes.json`, fusionadas con la lista global en runtime. Overrides vía env: `GITPR_SKIP_SMART_EXCLUDES`.

### **9. Verificación de Archivos Unstaged**

Antes de cualquier comando de IA, GitPR lista los archivos sin commitear (new/modified/deleted) y ofrece una TUI de selección de staging — o auto-stage cuando `GITPR_AUTO_STAGE=true`. El comportamiento se adapta por comando (PR/issue exigen staging, review solo informa) y puede desactivarse con `--no-unstaged-check`.

### **10. Salida Centralizada (.gitpr/reports/)**

Todos los artefactos generados (PR, review, full review, file review, blame, issue, linter) se guardan en `.gitpr/reports/<tipo>/` mediante `resolve_output_path()`. Se respetan las rutas personalizadas del `.env` (con separador de directorios) — solo los nombres de archivo "desnudos" se redirigen (retrocompatible). El informe del linter solo se genera cuando se encuentran violaciones.

### **11. Telemetría Offline (Fire-and-Forget)**

El módulo `metrics.py` registra eventos en hilos daemon — la telemetría nunca puede romper la CLI. Cada evento guarda comando, estado, proveedor, tokens, duración (mediante `time.perf_counter()`), repo y rama. El dashboard enriquece los eventos con **tokens reales** leídos de la caché de prompts y hace merge incremental con la caché.

### **12. Sistema de Plugins Globales**

`~/.gitpr/plugins/` contiene paquetes de reglas de linter (`linter/*.yml`) y plantillas de prompts MCP (`prompts/*.md`). Las reglas se fusionan **aditivamente** con el `.gitpr.linter.yml` del proyecto; los prompts se convierten en resources y prompts MCP dinámicos mediante factory closures (evitando late-binding en bucles). Los plugins malformados generan un warning, nunca rompen la ejecución.

### **13. Servidor MCP (Aislamiento de stdout)**

El `mcp_server.py` se ejecuta sobre stdio y expone 12 tools anotadas (`get_git_context`, `analyze_diff`, `analyze_unstaged_diff`, `get_full_diff`, `list_unstaged_files`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`), resources (skills, linter, prompts) y 7 prompts preconstruidos. La arquitectura aísla el JSON-RPC mediante **monkey-patching de stdout** (todo print se redirige a stderr, exponiendo solo el buffer real al transporte MCP) — aplicado antes de cualquier import interno. El modo `--tool` permite invocar cualquier herramienta directamente desde la línea de comandos sin servidor persistente. Como el SDK ejecuta los handlers síncronos en línea sobre el event loop, los 12 handlers se envuelven en un decorador `_offload` (hilos de trabajo de anyio) para que el trabajo bloqueante (subprocesos de git, descargas, llamadas de IA) nunca congele el servidor stdio.

### **14. Ecosistema TUI (Textual)**

Las interfaces visuales viven en `src/ui/` y siguen patrones comunes: retorno de estado mediante `final_action`/`final_message` (permitiendo bucles de re-autenticación en main), llamadas a la IA en hilos en segundo plano, modales de ayuda (F1) con URLs localizadas, y el wrapper `_with_real_stdout()` que soluciona el conflicto Textual×click en Windows. Aplicaciones: `PrPublishApp` (publicación de PR con pantallas de staging, commit, linter y error), `IssueApp`, `ChatApp`, `MetricsApp` y `LinterApp`.

### **15. Motor de Internacionalización (__())**

`src/i18n.py` implementa un motor inspirado en el helper `__()` de Laravel: claves en inglés en el código, traducciones en JSON (`~/.gitpr/langs/{lang}.json`) descargadas OTA cuando cambia el idioma, fallback al propio texto en inglés y soporte de placeholders con nombre. Idiomas: EN, PT-BR, PT-PT, ES, FR.

### **16. Version Markers (Recursos OTA)**

Los recursos remotos (traducciones, thinking words, smart excludes, presets de linter, scripts de hooks) se vuelven a descargar en bloque cuando cambian los marcadores de versión (`__lang_version__`, `__scripts_version__` en `updater.py`). Los hooks instalados se comparan con `SCRIPTS_VERSION` + `SCRIPTS_LANG` en `.env` y se **auto-sincronizan silenciosamente** en cada ejecución (respetando el idioma del usuario).

### **17. Sistema de Auto-Update**

Construido con empaquetado PyInstaller, el módulo `updater.py` consulta los *Releases* del repositorio en GitHub. Si existe una nueva versión, el ejecutable descarga el nuevo binario, se reemplaza a sí mismo (*hot-swap*) y relanza el comando sin interrupciones — con rollback automático en caso de fallo. Verificación diaria en caché (`~/.gitpr/update_cache.json`) y guarda de conexión (socket `8.8.8.8:53`) antes de cualquier operación de red.

### **18. Spinner Adaptativo**

Durante las llamadas a la IA, el `spinner.py` se ejecuta en un hilo en segundo plano con caracteres braille, "palabras de pensamiento" descubiertas letra a letra (lista controlada remotamente, con caché por versión) y velocidad adaptativa al tamaño de la frase.

---

## **💻 Stack Tecnológico**

| Componente | Tecnología |
| --- | --- |
| CLI framework | click >= 8.0.0 |
| TUI (issues, PRs, chat, dashboard) | Textual (ModalScreen, App, bindings) |
| IA (Gemini) | `google-genai` SDK |
| IA (DeepSeek / Ollama) | `openai` SDK (API compatible) |
| MCP Server | `mcp` (SDK oficial de Python) |
| GitHub API | `requests` (REST, PAT vía header) |
| i18n | Motor propio `__()` inspirado en Laravel |
| Config/Build | `pyproject.toml` + setuptools >= 61 |
| Cifrado | `cryptography.fernet` (simétrico) |
| Linter | `pyyaml` (reglas) + regex |
| Tests | pytest + unittest.mock |
| Empaquetado | PyInstaller (ejecutable standalone) |

---

## **🗂️ Estructura del Proyecto**

```text
src/
├── main.py           # CLI (Click) — enrutamiento de comandos y flags
├── core.py           # Orquestación — git ops, prompts de IA, caché, skills, hooks
├── config.py         # Configuración, .env, API keys, modelos, plugins
├── security.py       # Cifrado Fernet (API keys en reposo)
├── cache.py          # Caché local de respuestas de IA (MD5, repo+branch)
├── ai_providers.py   # Capa unificada de llamadas de IA (Gemini + DeepSeek + Ollama)
├── spinner.py        # Spinner braille animado con palabras de pensamiento
├── i18n.py           # Motor de internacionalización (__())
├── linter_engine.py  # Análisis estático con regex (reglas YAML) + linters externos
├── linter_wizard.py  # Asistente de configuración de linters externos (puente Checkstyle)
├── blame_engine.py   # Arqueología de código con git blame + IA
├── issue_engine.py   # Generación de issues con IA (3 motores de contexto)
├── chat_memory.py    # Persistencia de sesiones del chat (repo+branch, historial de diffs)
├── tui_issue.py      # Validación de token de GitHub y punto de entrada de la TUI
├── metrics.py        # Telemetría offline (fire-and-forget, enriquecimiento vía caché)
├── github_api.py     # Llamadas centralizadas a la API REST de GitHub (PRs)
├── mcp_server.py     # Servidor MCP (stdio) + tools/resources/prompts + modo --tool
├── updater.py        # Verificación de versión (PyPI + GitHub), hot-swap y version markers
└── ui/               # Sub-paquete: componentes TUI (Textual)
    ├── __init__.py       # Marcador de paquete (descubrimiento de setuptools)
    ├── issue_app.py      # TUI de edición y publicación de Issues
    ├── pr_publish_app.py # TUI del publicador de PRs + selección de staging + pantallas de commit
    ├── chat_app.py       # TUI del chat de programación en pareja
    ├── metrics_app.py    # Dashboard TUI de métricas
    ├── linter_app.py     # Visualización de violaciones del linter
    ├── help_screen.py    # Modal de ayuda (F1) — atajos e instrucciones
    └── pr_publish_help.py # Modal de ayuda del publicador de PR

scripts/            # Plantillas de git hooks localizadas (5 idiomas)
templates/          # Plantillas remotas servidas desde GitHub (--skill)
langs/              # Archivos de traducción (pt_br, pt_pt, es, fr)
tests/              # Tests unitarios (unittest + mock)
docs/               # Documentación técnica (EN canónico + sufijos de idioma)
```

---

## **📚 Documentación Detallada**

Cada funcionalidad tiene una guía dedicada en `docs/` (inglés canónico + `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr`):

* [pull-request-publication.md](pull-request-publication.md) — Publicador de PR (TUI, auto-commit, merge)  
* [pr-descricao-padrao.md](pr-descricao-padrao.md) — Modo de descripción de PR predeterminado  
* [understanding_chat_functionality.md](understanding_chat_functionality.md) — Chat de programación en pareja  
* [mcp-integration.md](mcp-integration.md) — Integración MCP con editores  
* [mcp-annotations.md](mcp-annotations.md) — Anotaciones de las tools MCP  
* [mcp-prompts.md](mcp-prompts.md) — Prompts predefinidos de MCP  
* [metricas-telemetria.md](metricas-telemetria.md) — Métricas y telemetría local  
* [plugins-system.md](plugins-system.md) — Sistema de plugins globales  
* [map-reduce-diff.md](map-reduce-diff.md) — Map-reduce para diffs gigantes  
* [smart-excludes.md](smart-excludes.md) — Optimización de tokens  
* [hooks-versioning.md](hooks-versioning.md) — Versionado y auto-sync de los hooks  
* [git-hooks-locais.md](git-hooks-locais.md) — Guía de git hooks locales  
* [linter-regras-customizadas.md](linter-regras-customizadas.md) — Reglas de linter y linters externos  
* [guia-regex-gitpr.md](guia-regex-gitpr.md) — Guía de regex para reglas del linter  
* [github-ci-linter.md](github-ci-linter.md) — Integración del linter con CI  
* [blame-arqueologo.md](blame-arqueologo.md) — Arqueología de código (git blame)  
* [issue-tui-help.md](issue-tui-help.md) — Issues estandarizadas y TUI  
* [gitpr-issue-option.md](gitpr-issue-option.md) — Opciones de generación de issues  
* [commit-message-ia.md](commit-message-ia.md) — Mensajes de commit con IA  
* [code-review-ia.md](code-review-ia.md) — Code review con IA  
* [install-wizard.md](install-wizard.md) — Asistente de configuración  
* [i18n_explanation.md](i18n_explanation.md) — Motor de i18n  
* [github-pat-integration.md](github-pat-integration.md) — Seguridad del GitHub PAT  
* [git-status.md](git-status.md) — Listado del estado de archivos sin commitear  
* [untracked-files.md](untracked-files.md) — Explicación de archivos untracked  
* [auto-update.md](auto-update.md) — Auto-actualizador (hot-swap)  
* [providers-ia.md](providers-ia.md) — Proveedores de IA (Gemini, DeepSeek, Ollama)  
* [skill-template.md](skill-template.md) — Sistema de skills y plantillas  

Tutoriales (solo en portugués):

* [github-issue-prompt-com-gh.md](github-issue-prompt-com-gh.md) — Formatear y actualizar issues mediante gh CLI  
* [como_reverter_commit_git_localmente.md](como_reverter_commit_git_localmente.md) — Revertir commits localmente  
* [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md) — Probar sin gastar una versión en PyPI  
* [otimizacao-de-tokens.md](otimizacao-de-tokens.md) — Optimización de tokens en los archivos de contexto (.gitpr.*.md)  

---
