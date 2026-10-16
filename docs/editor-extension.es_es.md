# Extensión de Editor de GitPR (VS Code & Cursor)

La **Extensión de Editor de GitPR** lleva la generación de mensajes Conventional Commits con IA, revisiones de código, creación y publicación de Pull Requests y diagnósticos unificados de `gitpr check` directamente a **VS Code** y **Cursor** como un **cliente ligero (thin client) MCP**.

---

## Arquitectura: Thin Client Real sobre MCP

En lugar de duplicar plantillas de prompts, analizadores de diff o gestión de credenciales en TypeScript, la extensión se comunica por `stdio` con su servidor local `gitpr-mcp` (`@modelcontextprotocol/sdk`):

- **Una Sesión por Carpeta de Workspace**: La extensión inicia `gitpr-mcp` bajo demanda (lazy) en el primer comando (con `cwd` apuntando a la raíz de la carpeta) y mantiene la sesión persistente, reconectándose automáticamente si el proceso termina.
- **Verificación de Contrato (Handshake)**: Al conectarse, la extensión llama a `listTools` y comprueba que todas las herramientas requeridas (`get_git_context`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_check`, `publish_pull_request`) estén disponibles. Si su `gitpr-cli` está desactualizado, muestra un aviso de actualización (`pip install --upgrade gitpr-cli`).
- **Cero Configuración Paralela**: Las claves de API, tokens SCM y preferencias permanecen en `~/.gitpr/.env` cifrados con Fernet. La extensión nunca pide ni almacena secretos.
- **Enmascaramiento de Secretos en Profundidad**: Tanto el servidor MCP en Python (`mask_sensitive_text`) como la extensión en TypeScript (`maskSensitiveText`) enmascaran tokens (`ghp_*`, `glpat-*`, `sk-*`, `AIza*`, `Bearer *`, claves privadas) antes de mostrar notificaciones o escribir en el OutputChannel `GitPR`.

---

## Instalación

### 1. Requisito previo: `gitpr-cli`

Asegúrese de tener `gitpr-cli` instalado y configurado en su máquina:

```bash
pip install --upgrade gitpr-cli
gitpr --install
```

### 2. Instale la Extensión (VS Code & Cursor)

Tanto VS Code como Cursor comparten el mismo paquete VSIX (`natanfiuza.gitpr`):

- **VS Code Marketplace**: Busque `GitPR` (`natanfiuza.gitpr`).
- **Cursor / Open VSX**: Busque `GitPR` o instale desde el archivo `.vsix`.
- **Desde el Código Fuente (VSIX Local)**:
  ```bash
  cd extensions/vscode
  npm install
  npm run compile
  npm run package
  code --install-extension gitpr-0.1.0.vsix
  ```

---

## Comandos y Flujos de Trabajo

Todos los comandos están disponibles en la **Paleta de Comandos** (`Ctrl+Shift+P` / `Cmd+Shift+P`), y los 4 accesos directos principales (**Commit**, **Review**, **PR**, **Check**) están fijados en la **Barra de Estado**.

| Comando | Tool MCP Llamada | Comportamiento |
|---|---|---|
| `GitPR: Commit (Generar Mensaje)` | `generate_commit_message` | Genera un borrador Conventional Commits y rellena el cuadro de **Control de Código Fuente** (con opción de copiar al portapapeles). Nunca hace commit automáticamente. |
| `GitPR: Review (Cambios Locales)` | `review_code(mentor=false)` | Revisa cambios locales (`git diff HEAD`) y abre una vista previa Markdown. |
| `GitPR: Full Review (Contra Rama Base)` | `full_review(mentor=false)` | Ejecuta `git fetch` y revisa toda la rama contra `origin/main`, abriendo vista previa Markdown. |
| `GitPR: Review (Modo Mentor Junior)` | `review_code(mentor=true)` | Añade explicaciones didácticas del Modo Mentor Junior a la revisión de código. |
| `GitPR: Generar Borrador de PR` | `generate_pr_description(explain=false)` | Abre un documento Markdown editable de borrador de PR (`línea 1` = título, resto = cuerpo). |
| `GitPR: Generar Borrador de PR (con Guía del Revisor)` | `generate_pr_description(explain=true)` | Genera el borrador editable de PR incluyendo la sección **Explain my PR** (Guía del Revisor). |
| `GitPR: Publicar PR desde el Borrador Activo` | `publish_pull_request` | Lee el borrador Markdown editado activo, solicita confirmación modal (`Publicar` o `Publicar como Borrador`) y crea el PR en la forja configurada (GitHub, GitLab, Bitbucket, Azure DevOps). |
| `GitPR: Check (Diagnósticos Unificados de Linter y Seguridad)` | `run_check` | Ejecuta el pipeline unificado de verificación y rellena el panel **Problems** con diagnósticos clicables por archivo, línea y severidad. |

### Publicación de Pull Request en Dos Pasos

La publicación nunca ocurre a ciegas:
1. Ejecute **`GitPR: Generar Borrador de PR`** (o **`Generar Borrador de PR (con Guía del Revisor)`**).
2. Revise y edite el documento Markdown abierto. La primera línea no vacía se utiliza como título del Pull Request y el resto como cuerpo.
3. Haga clic en el botón **`Publicar PR`** en la barra superior del editor (o ejecute **`GitPR: Publicar PR desde el Borrador Activo`**).
4. Confirme en el cuadro de diálogo modal. El servidor devuelve estados estructurados:
   - `needs_push` → ofrece el botón **Push y Publicar** mediante `vscode.git`.
   - `already_exists` → ofrece abrir el PR existente en el navegador.
   - `auth_required` → ofrece abrir una terminal ejecutando `gitpr` para autenticar.
   - `success` → ofrece abrir el PR recién creado en el navegador.

---

## Configuración de la Extensión

Configure en `settings.json` de VS Code / Cursor:

```json
{
  "gitpr.mcpCommand": "gitpr-mcp",
  "gitpr.mcpArgs": [],
  "gitpr.provider": "",
  "gitpr.check.useAI": false
}
```

| Ajuste | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `gitpr.mcpCommand` | `string` | `"gitpr-mcp"` | Ejecutable usado para iniciar el servidor MCP de GitPR. |
| `gitpr.mcpArgs` | `string[]` | `[]` | Argumentos adicionales pasados al ejecutable del servidor MCP. |
| `gitpr.provider` | `string` | `""` | Proveedor de IA opcional (`gemini`, `deepseek`, `ollama`). Vacío hereda de `~/.gitpr/.env`. |
| `gitpr.check.useAI` | `boolean` | `false` | Activa la revisión con IA dentro de `GitPR: Check`. Desactivado por defecto para mantener las verificaciones rápidas en el editor. |

---

## Internacionalización (i18n) y Telemetría

- **Idiomas de la Interfaz**: Empaquetada con traducciones `en`, `pt-br`, `es` y `fr` (`package.nls.*.json` y `l10n/bundle.l10n.*.json`).
- **Solo Telemetría Local**: La extensión no emite telemetría externa ni abre conexiones de red. El servidor MCP local registra los eventos `mcp:check` y `mcp:publish_pr` en el ledger SQLite local (`~/.gitpr/metrics/telemetry.db`).
