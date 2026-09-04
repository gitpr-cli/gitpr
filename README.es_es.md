# **GitPR CLI 🚀** — Español

<p align="center">
  <img src="https://raw.githubusercontent.com/natanfiuza/gitpr/main/docs/logo.png" alt="GitPR Logo" width="150">
</p>

GitPR CLI es una herramienta de automatización por línea de comandos que utiliza inteligencia artificial de **Google Gemini**, **DeepSeek** y **Ollama** para analizar tus cambios de código (git diff) o archivos completos. La herramienta genera automáticamente mensajes de commit en el estándar *Conventional Commits*, descripciones detalladas de Pull Request y revisiones profundas de código enfocadas en reducir la deuda técnica.

🌐 **Sitio web:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/) · 📂 **Repositorio:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)

----

## ⚡ **Inicio Rápido**

### **1. Instalación vía PyPI**

Instala GitPR CLI usando `pip`:

```bash
pip install gitpr-cli
```

### **2. Inicialización en un Nuevo Repositorio**

Para inicializar GitPR en la carpeta de un nuevo repositorio, ejecuta:

```bash
gitpr --install
```

> **Configuración Guiada:** Configuración guiada que descarga plantillas de skill, instala Git Hooks, configura MCP para tus editores y verifica la clave de API de tu proveedor de IA.  
> 📖 **Documentación completa:** [https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=es_es](https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=es_es)

## **🛠️ Tecnologías y Librerías Utilizadas**

Este proyecto fue desarrollado en Python y utiliza las siguientes librerías principales:

* [**Click**](https://click.palletsprojects.com/): Para crear una interfaz de línea de comandos (CLI) robusta y amigable.
* [**Google GenAI**](https://pypi.org/project/google-genai/): SDK oficial para integración directa con la API de Gemini.
* [**OpenAI**](https://pypi.org/project/openai/): Librería utilizada debido a su total compatibilidad con la potente API de **DeepSeek**.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/): Para la gestión segura de variables de entorno.
* [**Pytest**](https://docs.pytest.org/): Para ejecutar pruebas unitarias de forma simple, colorida y legible en la consola.
* [**Cryptography**](https://cryptography.io/): Para garantizar que tu `GEMINI_API_KEY` se almacene de forma encriptada y segura en disco.
* [**PyYAML**](https://pyyaml.org/): Usado para leer y procesar las reglas personalizadas de análisis estático del archivo `.gitpr.linter.yml`.
* [**Textual**](https://textual.textualize.io/): Potente librería para crear Interfaces Gráficas de Terminal (TUI), usada en el panel interactivo de generación y edición de issues.
* [**Requests**](https://pypi.org/project/requests/): Librería elegante y robusta para peticiones HTTP, usada para comunicarse con la API REST de GitHub.
* [**MCP**](https://pypi.org/project/mcp/): SDK oficial de Python para el Model Context Protocol, permitiendo que GitPR se integre directamente con editores e IDEs con tecnología de IA.

----

## 📦 Cómo Compilar el Ejecutable Localmente

Si deseas generar tu propio binario a partir del código fuente, utilizamos **PyInstaller**. Asegúrate de estar en el directorio raíz del proyecto con el entorno virtual configurado.

1. Instala las dependencias de desarrollo (si aún no lo has hecho):
   ```bash
   pipenv install --dev
   ```

2. Ejecuta el comando de build apuntando a nuestro punto de entrada (`run.py`):
   ```bash
   pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py
   ```
> **Nota técnica:** La flag `--onefile` garantiza que todo Python, librerías y dependencias se compriman en un único binario. 🛠️

Después de ejecutar este comando, PyInstaller creará algunas carpetas (`build` y `dist`).
Tu archivo final listo para usar estará dentro de la carpeta **`dist/`** con el nombre `gitpr` (o `gitpr.exe` en Windows).


----

## 🧪 Ejecutando Pruebas

Para garantizar que la lógica de captura de Git y la integración con la IA funcionan correctamente, utilizamos pruebas unitarias.

1. Instala las dependencias de prueba (si aún no lo has hecho):
   ```bash
   pipenv install --dev pytest
   ```

2. Ejecuta las pruebas con el comando:
   ```bash
   pipenv run pytest -v
   ```
Pytest detectará automáticamente los archivos dentro de la carpeta `tests/` y mostrará un informe detallado de la ejecución.

----
## **⚙️ Instalación y Configuración**

### **Usando el Ejecutable (Recomendado)**

1. Descarga el ejecutable de GitPR en la pestaña "Releases" de GitHub.
2. Mueve el ejecutable a una carpeta que esté en tu PATH (ej.: /usr/local/bin en Linux/Mac o tu carpeta de usuario en Windows).
3. En la primera ejecución, el asistente te guiará:
   ```bash
   $ gitpr
   ```
```bash
🚀 Intelligent PR Automation with AI

🔧 First run detected! Let's configure GitPR CLI.

🔑 Enter your GEMINI_API_KEY:

📄 Default output filename pattern [{branch}_{datetime}_PR_DESC.md]:
```
*Nota: Tu configuración se guardará de forma segura en el archivo `~/.gitpr/.env`.*

> **🔒 Nota de Seguridad:** GitPR CLI usa encriptación simétrica (Fernet). Tu clave API se almacena como un hash en el archivo `.env`, y la clave maestra para desencriptación se genera automáticamente en `~/.gitpr/secret.key`. **Nunca compartas tu archivo secret.key.**

### A Partir del Código Fuente

1. Clona el repositorio: `git clone https://github.com/gitpr-cli/gitpr.git.git`

2. Entra en la carpeta: `cd gitpr`

3. Configura el entorno:
```bash
pipenv install google-genai openai python-dotenv click cryptography
```
4. Ejecuta: pipenv run python src/main.py

## **💻 Cómo Usar**

GitPR tiene un comportamiento predeterminado potente y varias opciones avanzadas para ayudarte en tu día a día como desarrollador.

### **Comportamiento Predeterminado (Pull Request)**
Simplemente ejecuta el comando sin flags en tu terminal:
```bash
gitpr
```
La herramienta se sincronizará con el remoto (`git fetch`), comparará tus cambios con la rama principal remota (ej.: `origin/main`) y generará un archivo Markdown (ej.: `feature-login_20260421110134_PR_DESC.md`) en la raíz de tu proyecto con la sugerencia completa para tu Pull Request.

### **Opciones y Comandos Avanzados**
Puedes pasar las siguientes *flags* para acciones específicas:

* `-c` o `--commit`: Ejecuta un `git diff` local y muestra **solo el mensaje de commit sugerido**.
* `-r` o `--review`: Realiza un **Code Review** detallado de los cambios locales.
* `-f` o `--fullreview`: Realiza un **Code Review Completo** analizando todos los cambios desde la rama remota.
* `-i <archivo>` o `--input <archivo>`: **Auditoría Completa de Archivo.** Debe usarse junto con `-r` o `-f`; ignora el historial git y hace un Code Review del archivo completo. Excelente para actuar como consultor en refactorización de código legacy.
* `--provider <gemini|deepseek|ollama>`: Fuerza el uso de una IA específica solo para esta ejecución, ignorando la predeterminada guardada en `.env`.
* `--lang <código>`: Fuerza el idioma de la interfaz para esta ejecución (ej.: `en_us`, `es_es`). Sobrescribe el `GITPR_LANG` del `.env` sin persistir el cambio.
* `-ch` o `--chat`: Abre el **Chat Interactivo de Pair Programming** — un terminal TUI donde la IA ve tu diff actual y mantiene una conversación contextual. Dispone de memoria por rama, comandos slash (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patching (F5), actualización de diff (F2) y exportación de sesión (F6).
* `-l` o `--linter`: Ejecuta **solo el linter estático local** (sin llamadas a IA). Ideal para usar en pipelines de CI/CD para bloquear código no conforme.
* `--status`: Lista cambios de archivos no commiteados categorizados como **nuevos**, **modificados** y **eliminados** — rápido, sin IA, sin red. 📖 [Documentación completa](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/git-status.md)
* `--no-unstaged-check`: Omite la verificación de archivos unstaged antes del procesamiento de IA para una sola ejecución. Equivalente a `GITPR_SKIP_UNSTAGED_CHECK=true` para una ejecución. 📖 [Documentación completa](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/git-status.md)
* `--linter-setup`: **Asistente interactivo de linters externos.** Guía la instalación y configuración de linters externos (ESLint, PHPCS, Stylelint) como bridge vía Checkstyle XML. 📖 [Documentación completa](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/linter-regras-customizadas.md)
* `--mcp`: Inicia GitPR como un **servidor MCP** (Model Context Protocol) en transporte stdio. Permite la integración con VS Code, Cursor, Claude Desktop y otros editores compatibles con MCP — exponiendo todas las capacidades de IA de GitPR como herramientas directamente dentro de tu IDE. También disponible como comando independiente `gitpr-mcp`.
* `--plugins`: Lista todos los **plugins instalados globalmente** — paquetes de linter personalizados de `~/.gitpr/plugins/linter/` y plantillas de prompt MCP de `~/.gitpr/plugins/prompts/`. Estos plugins se aplican a todos tus proyectos sin duplicación. 📖 [Documentación completa](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/plugins-system.md)
* `--install`: **Asistente de Configuración Interactivo.** Ejecuta una configuración guiada en 4 pasos: descarga skill templates, instala Git Hooks, configura MCP para los editores detectados y verifica/solicita tu clave de API del proveedor de IA. Cada paso pide confirmación antes de continuar.
* `-ih` o `--installhooks`: Instala automáticamente **Git Hooks locales** (`pre-commit` y `prepare-commit-msg`) en tu repositorio.
* `-s` o `--skill`: Crea los archivos de plantilla de contexto de IA (`.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md`) y el Linter (`.gitpr.linter.yml`) en la raíz del proyecto.
* `-is` o `--issue`: Genera automáticamente un borrador de una **Issue estandarizada** y abre una interfaz interactiva (TUI) para edición o envío directo vía API REST. Esta funcionalidad tiene **3 motores de contexto** según la combinación de comandos:
  * **Issue de Código Nuevo (`gitpr -is`):** Lee el `git diff` actual. **Por qué usar:** Ideal para documentar rápidamente la tarea que acabas de programar, antes de hacer commit.
  * **Issue de Épico/Release (`gitpr -is -ht`):** Lee el historial completo de la rama actual (Git Log + Caché de PR). **Por qué usar:** Ideal para generar documentación consolidada de un release completo o de una *feature* grande que llevó varios días/commits completar.
  * **Issue de Deuda Técnica/Arqueológica (`gitpr -is -b archivo:líneas`):** Lee la línea de tiempo de una regla de negocio específica. **Por qué usar:** Ideal para documentar deuda técnica, explicando cómo un bloque de código legacy evolucionó y por qué necesita ser refactorizado.
* **Publicador de PR (predeterminado):** Ejecutar `gitpr` genera la descripción del PR con IA, guarda el archivo `.md` en `.gitpr/reports/pr_desc/` y abre una interfaz interactiva en el terminal (TUI) para revisar, editar y publicar el Pull Request directamente en GitHub vía REST API. Antes de la generación, detecta archivos sin commitear (*unstaged*) y ofrece un modal para gestionarlos. Usa `--no-publish` para guardar solo el archivo del PR localmente sin abrir el publicador, o `--no-edit` para hacer auto-commit de los cambios pendientes (con validación de lint), auto-push y publicar inmediatamente — con manejo de actualizaciones de PR existentes, auto-merge opcional y retroalimentación clara de error cuando ocurren conflictos de merge. Usa `--base <branch>` para cambiar la rama de destino. 📖 [Documentación completa](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/pull-request-publication.es_es.md)
* `-h` o `--help`: Muestra la ayuda general con todas las opciones. Úsalo junto con otra flag para **ayuda contextual** (ej.: `gitpr -h --issue`, `gitpr -h --linter`) con un enlace directo a la documentación detallada de cada funcionalidad.
* `-u` o `--update`: Verifica e instala la versión más reciente de GitPR (Auto-Updater).

> **⚙️ Nota Técnica (--hook):** GitPR tiene una flag oculta `--hook <archivo>` que se activa exclusivamente por el sistema de Git Hooks en segundo plano. Permite que la IA inyecte el mensaje sugerido directamente en el archivo temporal de Git, sin contaminar tu terminal.
>
> **⚙️ Nota Técnica (--pre-save):** GitPR tiene una flag oculta de debug `--pre-save` que puede combinarse con cualquier comando de IA (ej.: `gitpr -c --pre-save`). Antes de cada llamada a la IA, guarda el payload completo que se enviará al modelo (system instruction + prompt + contadores de caracteres) en un archivo `_{accion}-{fechahora}.json` en la carpeta actual, y luego continúa normalmente. Útil para inspeccionar prompts muy grandes. Nota: cuando la respuesta proviene de la caché local, no se realiza ninguna llamada y no se genera ningún archivo.

### 📦 Diffs Enormes (Map-Reduce)

Cuando el diff es demasiado grande para una sola llamada a la IA (por encima de ~90 mil tokens estimados), GitPR lo divide automáticamente en lotes por archivo, pide a la IA un resumen técnico de cada parte (Map) y unifica todo en el mensaje de commit, review o descripción de PR final (Reduce). Sin flags — se activa bajo demanda y muestra el progreso en la consola.

📚 Documentación completa: [docs/map-reduce-diff.md](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/map-reduce-diff.md)

## 🛡️ Linter Local (Análisis Estático)

GitPR CLI te permite definir reglas estrictas que se validarán instantáneamente durante `--review` o `--fullreview`, sin depender de IA. Esto es ideal para evitar que errores comunes (como `console.log` o IPs de prueba) lleguen al repositorio.

### Cómo configurar `.gitpr.linter.yml`:
Al ejecutar `gitpr --skill`, se generará una plantilla. Puedes configurar reglas usando Expresiones Regulares (Regex):

```yaml
rules:
  - name: "check-localhost"
    extensions: ["js", "php"] # Extensiones a validar
    regex: 'http(s)?://(localhost|127\.0\.0\.1)' # Qué buscar
    message: "🚨 Localhost usage detected in file {file_name}"
    ignore_comments: true # Ignora si la línea está comentada
    ignore_paths: # Carpetas o archivos ignorados (acepta *)
      - "vendor/*"
      - "node_modules/*"
```

El Linter analiza solo las **líneas añadidas** en tu `git diff`, garantizando una ejecución enfocada y extremadamente rápida. Si hay violaciones, aparecerán resaltadas en la parte superior de tu archivo de review.

### Linters Externos (Bridge vía Checkstyle)

Si tu proyecto ya usa herramientas como ESLint, PHP_CodeSniffer o Stylelint, GitPR puede actuar como bridge — ejecutándolas en segundo plano y filtrando errores **solo de las líneas que cambiaste** en tu diff actual. Cualquier linter que emita informes en formato `checkstyle` es compatible.

En lugar de configurar el YAML manualmente, usa el asistente interactivo:

```bash
gitpr --linter-setup
```

El asistente muestra presets preconfigurados (PHPCS, ESLint, Stylelint — controlados remotamente vía `templates/gitpr.linter-presets.json`), te guía con el comando de instalación nativa (ej.: `npm install --save-dev eslint`) e inyecta el bloque `external_linters` correcto en tu `.gitpr.linter.yml`.

Cada ejecución — manual vía `--linter` o automática antes de los commits — consolida las Reglas Regex y los Linters Externos en un único informe Markdown guardado en `.gitpr/reports/linter/` (personalizable vía `OUTPUT_FILE_NAME_LINTER`). El informe se genera solo cuando hay infracciones — las ejecuciones limpias no crean archivos.

## 🤝 Firma de Coautoría

Todos los mensajes de commit generados por GitPR incluyen automáticamente el trailer de coautoría:

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

El trailer se añade programáticamente (nunca por la IA) en todos los flujos: sugerencia en consola (`gitpr -c`), hook `prepare-commit-msg`, auto-commit (`--no-edit`), TUI de publicación de PR y la herramienta MCP `generate_commit_message`. Es idempotente — nunca se duplica cuando el mensaje ya lo contiene — y permanece oculto en la pantalla de edición de la TUI, inyectándose solo al ejecutar el commit.

📖 **Documentación completa:** [docs/commit-message-ia.md](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/commit-message-ia.md)

## 🧠 Arquitectura Multi-Modelo (IA Agnóstica)

GitPR no está atado a una única Inteligencia Artificial. Durante la configuración inicial, el usuario puede elegir su motor predeterminado. Actualmente ofrecemos soporte para:
* **Google Gemini** (Predeterminado: `gemini-pro-latest`)
* **DeepSeek** (Predeterminado: `deepseek-v4-pro`)
* **Ollama** (Local) — ejecuta modelos localmente sin internet, totalmente compatible con el formato de la API OpenAI

Puedes alternar dinámicamente los modelos configurando las variables `GEMINI_API_MODEL_PRIMARY` o `DEEPSEEK_API_MODEL_PRIMARY` en tu archivo `~/.gitpr/.env`, o alternar en tiempo real usando la flag `--provider`.

## 🎯 Sistema de "Skills" Personalizables (Prompt Engineering)

En lugar de ocultar instrucciones de IA en el código fuente, GitPR usa archivos Markdown locales que actúan como *System Instructions*. Al ejecutar `gitpr -s`, se generan los siguientes archivos en la raíz de tu proyecto para personalizar la "persona" de la IA según las reglas de negocio de tu empresa:

* `.gitpr.commit.md`: Reglas para generar mensajes de commit cortos.
* `.gitpr.pr.md`: Estructura de temas obligatoria para la descripción del Pull Request.
* `.gitpr.review.md`: Define el enfoque arquitectónico (ej.: SOLID, Clean Code) para el análisis del diff.
* `.gitpr.filereview.md`: Define reglas estrictas de cohesión y acoplamiento para la auditoría completa de archivos (usado con `--input`).
* `.gitpr.issue.md`: Define la estructura y el nivel de detalle necesarios para generar Issues estandarizadas (usado con `--issue`).
* `.gitpr.blame.md`: Define el enfoque del análisis arqueológico para el rastreo de código legacy (usado con `--blame`).

## 🌐 Internacionalización (i18n)

GitPR detecta automáticamente el idioma de tu sistema y muestra los mensajes en tu idioma nativo. El sistema i18n está inspirado en el **helper `__()` de Laravel**:

* **Detección automática:** En la primera ejecución, GitPR detecta el idioma del SO y lo guarda en `~/.gitpr/.env` (`GITPR_LANG`).
* **Archivos de traducción:** Los paquetes de idioma se descargan automáticamente del repositorio oficial a `~/.gitpr/langs/`.
* **5 idiomas:** Inglés, Portugués (Brasil), Portugués (Portugal), Español y Francés. Los paquetes están versionados (`__lang_version__`) y se actualizan automáticamente (OTA) cuando se publica una nueva versión de traducciones.
* **Fallback en inglés:** Si falta una traducción, el texto en inglés se muestra directamente.
* **API del desarrollador:** Usa `from src.i18n import __` y envuelve todas las cadenas de interfaz con `__("Tu texto aquí")`.
* **Placeholders:** Soporta parámetros con nombre — `__("Descargando {file}...", file="template.md")`.

Para forzar un idioma específico, define `GITPR_LANG=es_es` o `GITPR_LANG=en` en `~/.gitpr/.env`.

> 📖 **Guía completa del desarrollador:** [docs/i18n_explanation.md](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/i18n_explanation.md) — arquitectura, patrones de uso, precauciones con import circular y cómo añadir nuevos idiomas.

## 🔄 Versionado y Sincronización Automática de Scripts de Hooks

GitPR incluye un sistema automático de versionado para scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Cada vez que ejecutas `gitpr`, el sistema verifica silenciosamente si tus hooks instalados coinciden con la última versión y los actualiza automáticamente si es necesario — todo respetando tu preferencia de idioma.

**Cómo funciona:**
1. Lee `SCRIPTS_VERSION` y `SCRIPTS_LANG` desde `~/.gitpr/.env`
2. Compara con la última versión (`__scripts_version__`) incluida en tu release de GitPR
3. Si las versiones o el idioma difieren → descarga y actualiza los hooks automáticamente
4. Si todo coincide → omite completamente (lectura única del `.env`, cero E/S de red)

**Ejemplo:**
```bash
# Primera ejecución — sin hooks instalados aún
$ gitpr --installhooks
📥 Descargando pre-commit...
📥 Descargando prepare-commit-msg...
✅ ¡Scripts sincronizados con éxito!

# Ejecuciones siguientes — verificaciones silenciosas
$ gitpr  # (sin salida = hooks están actualizados)
```

El sistema soporta **5 idiomas**: Inglés (predeterminado), Portugués (Brasil), Portugués (Portugal), Francés y Español. Los scripts son thin shims — la lógica real reside en el CLI, por lo que incluso hooks ligeramente desactualizados siguen funcionando correctamente.

📚 [Documentación Completa](https://gitpr.natanfiuza.dev.br/docs/hooks-versioning?lang=es_es)

## 🔌 Integración MCP (Model Context Protocol)

GitPR puede ejecutarse como un **servidor MCP**, exponiendo sus capacidades con IA como herramientas que el asistente de IA de tu editor puede invocar directamente — sin necesidad de terminal. Esto permite un flujo de trabajo totalmente integrado donde puedes generar mensajes de commit, revisar código, ejecutar linters, rastrear orígenes de código y crear issues sin salir de tu IDE.

### Editores Compatibles

| Editor | Archivo de Configuración |
| ------ | ------------------------ |
| **VS Code** | `.vscode/mcp.json` |
| **Cursor** | `.cursor/mcp.json` |
| **Claude Code** | `.mcp.json` |
| **Claude Desktop** | `claude_desktop_config.json` |
| **Zed** | `settings.json` |

### Configuración Rápida

Usa el instalador integrado para configurar tu editor automáticamente:

```bash
gitpr-mcp --install vscode    # Crea .vscode/mcp.json
gitpr-mcp --install cursor      # Crea .cursor/mcp.json
gitpr-mcp --install claude-code # Crea .mcp.json
gitpr-mcp --install claude      # Actualiza config de Claude Desktop
gitpr-mcp --install zed         # Actualiza config de Zed
gitpr-mcp --install auto      # Auto-detectar e instalar para todos
```

El instalador crea el directorio de config si es necesario, fusiona con cualquier
config existente (nunca sobrescribe otros servidores) y es seguro ejecutarlo
múltiples veces.

> La configuración manual también está soportada — consulta [docs/mcp-integration.md](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/mcp-integration.md)
> para el formato JSON de cada editor.

Una vez configurado, usa lenguaje natural en el chat de IA de tu editor:

   * *"Revisa mis cambios actuales"* → llama a `review_code`
   * *"Genera un mensaje de commit"* → llama a `generate_commit_message`
   * *"Crea una descripción de PR"* → llama a `generate_pr_description`
   * *"Ejecuta el linter en mi diff"* → llama a `run_linter`

### Herramientas MCP Disponibles

| Herramienta | Descripción |
| ----------- | ----------- |
| `get_git_context` | Rama actual, nombre del repositorio y URL del remote |
| `analyze_diff` | Diff git de los cambios no commiteados |
| `get_full_diff` | Diff completo contra origin/main |
| `generate_commit_message` | Mensaje Conventional Commits generado por IA |
| `review_code` | Code review con IA de los cambios locales |
| `full_review` | Code review con IA de todos los cambios desde origin/main |
| `generate_pr_description` | Descripción completa de PR (título + cuerpo) |
| `run_linter` | Linter estático basado en `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + clasificación por IA |
| `generate_issue` | Issue estructurada a partir de diff, historial o blame |
| `list_unstaged_files` | Cambios no commiteados categorizados (nuevos/modificados/eliminados) |
| `analyze_unstaged_diff` | Diff solo unstaged (working tree vs index) |

### Invocación Directa por CLI

Todas las herramientas MCP de GitPR pueden invocarse directamente desde el terminal sin iniciar el servidor stdio:

```bash
# Listar todas las herramientas disponibles con sus firmas
gitpr-mcp --tool

# Invocar una herramienta específica
gitpr-mcp --tool get_git_context
gitpr-mcp --tool review_code
gitpr-mcp --tool generate_commit_message --tool-args '{"diff_text":"..."}'
gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/main.py","start_line":"270","end_line":"284"}'
```

Ideal para scripts, pipelines de CI/CD y consultas puntuales donde no necesitas un servidor MCP persistente. La salida JSON va a stdout; todos los mensajes de diagnóstico van a stderr — seguro para pipe.

📖 **Documentación completa:** [docs/mcp-integration.md](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/mcp-integration.md) — disponible en 5 idiomas (EN, PT-BR, PT-PT, ES, FR).

> 💬 **MCP Prompts** — GitPR también expone 7 plantillas de mensaje predefinidas (prompts) para flujos comunes como "Revisar PR", "Generar Mensaje de Commit" y "Crear Issue desde el Diff". Consulta la [guía de MCP Prompts](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/mcp-prompts.md) para la lista completa.

## 🎯 Smart Excludes (Optimización de Tokens)

GitPR elimina automáticamente los archivos que no son código de tu `git diff` antes de enviarlos a la IA — reduciendo el consumo de tokens y los costes de API sin necesidad de configuración.

**Dos capas de exclusiones:**
- **Lockfiles y archivos generados:** `package-lock.json`, `*.min.js`, `*.map`, `*.pyc`, `*.svg` y más de 30 otros patrones definidos en [`gitpr.smart-excludes.json`](https://github.com/gitpr-cli/gitpr.git/blob/main/templates/gitpr.smart-excludes.json)
- **Documentación en prosa:** `*.md`, `*.txt`, `*.rst`, `*.adoc`, `*.tex` y más de 20 otras extensiones definidas en [`gitpr.docs-smart-excludes.json`](https://github.com/gitpr-cli/gitpr.git/blob/main/templates/gitpr.docs-smart-excludes.json)

**Seguimiento de documentación:** Aunque el contenido de la documentación se excluye del diff, GitPR sigue informando a la IA sobre _qué_ archivos de documentación se modificaron, inyectando sus rutas como metadatos en las instrucciones del sistema. La IA tiene contexto completo sobre las actualizaciones de documentación sin consumir tokens con su contenido.

**Beneficios:**
- ✅ Hasta un **98% de reducción de tokens** en ramas con mucha documentación
- ✅ **Respuestas más rápidas de la IA** — menos texto que procesar por llamada
- ✅ **Análisis de mayor calidad** — la IA se centra en los cambios de código, no en el markup
- ✅ **Configuración cero** — funciona automáticamente en cada ejecución, gestionado remotamente

**Configuración local del proyecto:** Cada proyecto puede definir exclusiones adicionales en `.gitpr/conf/gitpr.smart-excludes.json`. El archivo se crea automáticamente en la primera ejecución y se fusiona con la lista global en tiempo de ejecución:

```json
{
  "_comment": "Exclusiones específicas del proyecto.",
  "excludes": [
    "dist/",
    "*.pyc",
    "build/",
    "node_modules/"
  ]
}
```

Añade artefactos de compilación de frameworks específicos, carpetas generadas o cualquier patrón que solo se aplique a este proyecto. El archivo se puede versionar — tu equipo recibe las mismas exclusiones.

> 📖 **Documentación completa:** [docs/smart-excludes.md](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/smart-excludes.md) — disponible en 5 idiomas (EN, PT-BR, PT-PT, FR, ES).

## 📁 Estructura de Directorios de Salida

Por defecto, GitPR guarda todos los archivos generados en el directorio `.gitpr/reports/`, organizados por tipo de artefacto:

| Artefacto | Ubicación Predeterminada |
| --------- | ------------------------- |
| Descripción de PR | `.gitpr/reports/pr_desc/` |
| Code Review | `.gitpr/reports/review/` |
| Full Review | `.gitpr/reports/full_review/` |
| File Review | `.gitpr/reports/file_review/` |
| Informe de Blame | `.gitpr/reports/blame/` |
| Borrador de Issue | `.gitpr/reports/issue/` |
| Informe del Linter | `.gitpr/reports/linter/` |

Los directorios se crean automáticamente en el primer uso. **Retrocompatible:** si tu `.env` ya contiene rutas personalizadas con separadores de directorio (ej.: `OUTPUT_FILE_NAME=/home/usuario/prs/mi_pr.md`), se respetan tal cual — GitPR solo redirige nombres de archivo simples a `.gitpr/reports/`.

## 📚 Documentación Técnica y Guías Avanzadas

Para mantener este README conciso, detallamos las implementaciones más avanzadas enfocadas en **DevOps** e **Integración Continua** en documentos separados.

Si deseas implementar GitPR como una barrera de calidad automatizada en tu equipo, consulta las guías a continuación.

> 🌐 Cada guía está disponible en **5 idiomas** — añade `.pt_br`, `.pt_pt`, `.fr_fr` o `.es_es` antes de la extensión `.md` para versiones traducidas (ej.: `docs/understanding_chat_functionality.es_es.md`). El inglés es el predeterminado sin sufijo.

### Chat y Funcionalidades Interactivas

* [**🧠 Chat Interactivo (Pair Programming)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/understanding_chat_functionality.md) — Cómo usar el chat con IA con memoria, comandos slash, auto-patch y exportación de sesión.

### DevOps & CI/CD

* [**Git Hooks Locales (Shift-Left)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/git-hooks-locais.md) — Cómo usar `gitpr --installhooks` para crear barreras de calidad en la máquina del desarrollador y usar IA para generar mensajes de commit automáticamente.
* [**Versionado y Sincronización de Scripts de Hooks**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/hooks-versioning.md) — Cómo el sistema de versionado automático y sincronización con soporte i18n mantiene tus Git hooks siempre actualizados.
* [**Linter Estático Personalizable**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/linter-regras-customizadas.md) — Cómo crear reglas de validación en `.gitpr.linter.yml`, integrar linters externos (ESLint, PHPCS, Stylelint) y generar informes Markdown para CI/CD y hooks de pre-commit.
* [**Integración CI/CD (GitHub Actions)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/github-ci-linter.md) — Cómo ejecutar GitPR en el pipeline para bloquear "Merge" de PRs con violaciones.

### Funcionalidades Principales

* [**Pull Request (Modo Predeterminado)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/pr-descricao-padrao.md) — Flujo completo para generar descripciones de PR sin flags.
* [**Publicador de Pull Request (TUI)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/pull-request-publication.es_es.md) — Cómo revisar y publicar Pull Requests directamente en GitHub desde el terminal.
* [**Code Review con IA**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/code-review-ia.md) — Guía de los modos de review (`--review`, `--fullreview`) y auditoría de archivos (`--input`).
* [**Mensajes de Commit con IA**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/commit-message-ia.md) — Cómo generar mensajes en el estándar Conventional Commits e integrar con Git Hooks.
* [**Generación de Issues e Interfaz TUI**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/issue-tui-help.md) — Cómo usar la interfaz gráfica de terminal (TUI) y los 3 motores de contexto para gestionar Issues estructuradas.
* [**Arqueólogo de Código (Git Blame)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/blame-arqueologo.md) — Cómo rastrear el origen de reglas de negocio con `git blame` e IA.
* [**Sistema de Skills y Plantillas**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/skill-template.md) — Cómo personalizar el comportamiento de la IA con archivos `.gitpr.*.md`.

### Configuración e Infraestructura

* [**Asistente de Instalación**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/install-wizard.md) — Configuración guiada paso a paso para instalar GitPR en un nuevo proyecto.
* [**Proveedores de IA**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/providers-ia.md) — Configuración y selección entre Google Gemini, DeepSeek y Ollama.
* [**Auto-Updater**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/auto-update.md) — Cómo funciona la actualización automática (hot-swap) de GitPR.
* [**Arquitectura**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/ARCHITECTURE.md) — Arquitectura del proyecto, patrones de diseño y visión general del stack técnico.
* [**Token GitHub (PAT) — Integración y Seguridad**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/github-pat-integration.md) — Entiende cómo GitPR crea issues directamente en el repositorio con autenticación.
* [**Internacionalización (i18n)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/i18n_explanation.md) — Arquitectura, patrones de uso y cómo añadir nuevos idiomas.
* [**Integración MCP**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/mcp-integration.md) — Conecta GitPR a VS Code, Cursor y Claude Desktop vía Model Context Protocol.
* [**MCP Prompts**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/mcp-prompts.md) — Plantillas de mensaje predefinidas (7 prompts, 35 variantes de idioma) para flujos comunes en el chat de IA de tu editor.
* [**MCP Tool Annotations**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/mcp-annotations.md) — Sugerencias de integración con IDEs (`readOnlyHint`, `destructiveHint`) para un comportamiento de UI más inteligente y ejecución segura de herramientas.
* [**Métricas y Telemetría**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/metricas-telemetria.md) — Analytics local offline para métricas de uso del equipo, informes CSV exportables y dashboard TUI interactivo.

## ⚡ Sistema de Caché Local (Ahorro de Cuota)

GitPR tiene un motor de caché inteligente basado en **MD5**. Cada vez que ejecutas un comando (`--review`, `--commit`, etc.), la herramienta genera un hash exacto de tu código actual (diff) y de las instrucciones.
¡Si ejecutas el mismo comando nuevamente sin alterar el código, GitPR intercepta la solicitud y devuelve el resultado instantáneamente (en milisegundos) desde la carpeta `~/.gitpr/cache/prompts/`, ahorrándote tiempo y tus cuotas de la API de Gemini!

## 🔄 Auto-Updater (Actualización Over-The-Air)

Nunca más te preocupes por descargar nuevas versiones manualmente. GitPR tiene un Guardián de Conexión y un actualizador integrado:
* Verifica la disponibilidad de red antes de iniciar para no bloquear tu flujo de trabajo offline.
* En cada ejecución, verifica silenciosamente si hay un nuevo release oficial en la API de GitHub.
* Puedes forzar la verificación e instalación ejecutando `gitpr --update` o `gitpr -u`.
* La herramienta usa la técnica de *Hot-Swap*, descargando el nuevo `.exe` y reemplazando la versión antigua de forma transparente.

## Publicación en PyPI

```bash
pipenv run python -m build
pipenv run twine upload dist/*
```
## **🤝 Cómo Contribuir**

¡Las contribuciones son muy bienvenidas! Para contribuir:

1. Haz un fork del proyecto.
2. Crea una rama para tu *feature* (git checkout -b feature/NuevaFuncionalidad).
3. Haz commit de tus cambios (git commit -m 'feat: añade nueva funcionalidad'). Consejo: ¡Usa el propio GitPR para generar este mensaje! 😄
4. Haz push a la rama (git push origin feature/NuevaFuncionalidad).
5. Abre un Pull Request.

## **✨ Agradecimientos y Autoría**

Proyecto ideado y desarrollado por:

**Natan Fiuza** - [contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br)

## **📄 Licencia**

Este proyecto está licenciado bajo la **GNU Lesser General Public License v2.1 (LGPL-2.1)**. Consulta el archivo LICENSE para más detalles.
