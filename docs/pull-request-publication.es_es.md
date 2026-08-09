# Documentación Técnica: Publicación de PR en GitHub

Esta documentación describe el flujo de publicación de Pull Requests mediante la interfaz interactiva de terminal (TUI), lo que te permite revisar, editar y publicar Pull Requests directamente en GitHub sin salir del terminal.

---

## 1. ¿Qué es el Publicador de PR?

Cuando ejecutas el comando `gitpr` (comportamiento predeterminado), GitPR genera la descripción del PR con IA, guarda el archivo `.md` localmente y abre un panel interactivo directamente en el terminal. Esto te permite revisar, editar y publicar el Pull Request generado por la Inteligencia Artificial antes de enviarlo al repositorio remoto mediante la API REST.

---

## 2. Flujo de ejecución completo

```
gitpr
  ├─ Banner
  ├─ Verificación de archivos unstaged (antes de la generación del PR)
  │   ├─ GITPR_SKIP_UNSTAGED_CHECK=true → omitir
  │   ├─ Sin archivos unstaged → continuar
  │   ├─ GITPR_AUTO_STAGE=true → git add automático → continuar
  │   └─ Hay archivos unstaged → TUI StageFilesApp
  │       ├─ Stage Selected → git add → continuar
  │       ├─ Skip → continuar (sin stage)
  │       └─ Cancel → abortar
  ├─ Generación del PR (IA) → archivo .md guardado en .gitpr/reports/pr_desc/
  └─ TUI (predeterminada) o --no-publish / --no-edit
      └─ F3 Publicar PR → auto-commit (sin verificación duplicada de unstaged)
          ├─ Commit → git push → verificación del PR
          │   ├─ Sin PR existente → POST crear PR
          │   └─ PR existente encontrado → PATCH actualizar PR
          └─ Pregunta de merge (si GITPR_AUTO_MERGE no está configurado)
```

---

## 3. Modos de ejecución

El Publicador de PR tiene **3 modos de ejecución**, activados por las banderas (o la ausencia de ellas).

### 3.1 Modo interactivo (predeterminado) — `gitpr`

Ejecutar `gitpr` sin ninguna bandera genera la descripción del PR y abre la TUI para su revisión y edición antes de publicar.

```bash
gitpr
```

| Característica | Descripción |
|---|---|
| **Flujo** | Verificación de unstaged → `git fetch` → la IA genera el PR → `.md` guardado → se abre la TUI → el usuario edita → POST a GitHub |
| **Cuándo usarlo** | Flujo de trabajo estándar: control total sobre lo que se publica |
| **Resultado** | Pull Request creado en GitHub con el contenido editado |
| **Ideal para** | Desarrollo diario: revisar y ajustar el contenido del PR antes de publicar |

> **Consejo:** El archivo `.md` local se guarda antes de que se abra la TUI y se vuelve a guardar con cualquier edición antes de publicar. Siempre tienes una copia de seguridad.

---

### 3.2 Omitir el publicador — `gitpr --no-publish`

Genera el PR y lo guarda localmente sin abrir el editor interactivo.

```bash
gitpr --no-publish
```

| Característica | Descripción |
|---|---|
| **Flujo** | Verificación de unstaged → `git fetch` → la IA genera el PR → `.md` guardado → salida |
| **Cuándo usarlo** | Cuando solo necesitas el archivo de descripción del PR para documentación o revisión posterior |
| **Resultado** | Archivo Markdown guardado localmente; no se abre ninguna TUI |
| **Ideal para** | Documentación, revisión sin conexión, guardar borradores de PR para más tarde |

---

### 3.3 Publicación directa — `gitpr --no-edit`

Omite el editor interactivo, hace commit automático (auto-commit) de los cambios pendientes con validación del linter, sube los cambios al remoto (push) y publica directamente en GitHub.

```bash
gitpr --no-edit
```

| Característica | Descripción |
|---|---|
| **Flujo** | Verificación de unstaged → `git fetch` → la IA genera el PR → `.md` guardado → auto-commit (linter + mensaje de commit con IA) → git push → POST directo a GitHub |
| **Cuándo usarlo** | Cuando confías en el resultado de la IA y quieres publicar de inmediato |
| **Resultado** | Pull Request creado en GitHub sin abrir la TUI |
| **Ideal para** | Pipelines de CI/CD, correcciones rápidas, flujos de trabajo automatizados |

> **Precaución:** Úsalo con cuidado: no tendrás la oportunidad de revisar ni editar el contenido antes de publicar.

---

## 4. Gestión de archivos unstaged

Antes de que comience la generación del PR, GitPR verifica si hay archivos unstaged y ofrece una interfaz modal para gestionarlos. Esta verificación se ejecuta al principio mismo de la ejecución de `gitpr`, antes de cualquier llamada a la IA.

### 4.1 Flujo de verificación al inicio

```
gitpr starts
  ├─ GITPR_SKIP_UNSTAGED_CHECK=true → skip entire check, proceed
  ├─ No unstaged files detected → proceed
  ├─ GITPR_AUTO_STAGE=true → auto git add all → proceed
  └─ Unstaged files found → StageFilesApp TUI opens
      ├─ [Stage Selected] → git add <selected> → proceed
      ├─ [Skip] → proceed without staging
      └─ [Cancel] → abort (exit without generating PR)
```

### 4.2 Detección de archivos

Los archivos unstaged se detectan mediante `git status --porcelain`, buscando:
- `??` — archivos sin seguimiento (untracked)
- ` M` — modificados pero no en stage (cambios del árbol de trabajo)
- ` D` — eliminados pero no en stage

### 4.3 Variables de entorno

| Variable | Predeterminado | Descripción |
|---|---|---|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Establécelo en `true` para omitir por completo la verificación de archivos unstaged al inicio |
| `GITPR_AUTO_STAGE` | `false` | Establécelo en `true` para hacer stage automático de todos los archivos unstaged sin mostrar el modal de selección |

---

## 5. Flujo de auto-commit (--no-edit y F3 de la TUI)

Cuando usas `--no-edit` o pulsas `F3` en la TUI con cambios sin confirmar, GitPR ejecuta un flujo de commit automático:

```
1. Check for uncommitted changes (git diff HEAD --stat)
   └─ If clean → skip commit, proceed to publish

2. Run static linter (.gitpr.linter.yml rules)
   ├─ ✅ Pass → proceed
   ├─ ⚠️ Warnings → shown, proceed
   └─ 🚨 Errors:
        ├─ [Commit with --no-verify] → proceed
        └─ [Abort] → operation cancelled

3. Generate commit message via AI (Conventional Commits format)
   └─ Display message in editable field, request confirmation
   └─ Option to regenerate the message

4. Execute: git commit -m "<message>" [--no-verify]
   ├─ Success → proceed with git push + PR publication
   └─ "Nothing to commit" → treated as success, proceed to publish
```

### 5.1 Manejo de "Nothing to Commit"

Cuando `git commit` devuelve un código distinto de cero pero la salida indica que no existen cambios reales, el flujo lo trata como un éxito y continúa. Se reconocen los siguientes patrones:

- `nothing to commit`
- `nothing added to commit`
- `no changes added to commit`
- `changes not staged`
- `working tree clean`
- `no changes`

### 5.2 Diagrama de flujo de decisión del linter

```
Has uncommitted changes?
├─ No → Skip commit, publish PR
└─ Yes
   └─ GITPR_SKIP_LINT=true?
      ├─ Yes → Skip to AI commit message
      └─ No
         └─ Run linter
            ├─ No errors → Skip to AI commit message
            └─ Has errors
               └─ User confirms --no-verify?
                  ├─ Yes → Skip to AI commit message (with --no-verify)
                  └─ No → Abort
```

### 5.3 Diálogos de commit en la TUI

El flujo de auto-commit en la TUI utiliza una serie de pantallas modales:

| Pantalla | Propósito |
|---|---|
| `CommitConfirmScreen` | Confirmación antes de iniciar el flujo de commit. Etiquetas de botón personalizables para diferentes contextos |
| `FileStageScreen` | Lista de archivos alternables para `git add` selectivo antes del commit |
| `CommitProgressScreen` | Modal `RichLog` similar a un terminal que aísla los registros del commit de la TUI principal |
| `CommitMessageScreen` | Mensaje de commit editable con botón "Regenerate" para regenerar el mensaje con IA |
| `LinterErrorScreen` | Muestra los errores del linter con opciones para hacer commit con `--no-verify` o abortar |
| `ErrorScreen` | Visualización genérica de errores con `max-height: 80%` y desplazamiento para salidas de error grandes |

---

## 6. Git push y gestión de PR existentes

Después de un commit exitoso, GitPR sube la rama (push) y verifica si existen PRs.

### 6.1 Flujo de push

```
git push origin <branch>
  ├─ Success → check for existing PRs
  └─ Failure with "upstream" / "no upstream" in error
      └─ Auto-retry: git push --set-upstream origin <branch>
```

### 6.2 Detección de PR existentes

Antes de crear un nuevo PR, GitPR verifica si ya existe un PR para la rama actual:

```
Check existing PRs (GET /repos/{owner}/{repo}/pulls?head={branch})
  ├─ No existing PR → POST create new PR
  └─ Existing PR found
      ├─ User chooses "Push to existing PR" → PATCH update PR body
      └─ User chooses "Create new PR" → POST create new PR
```

### 6.3 Actualización del PR

Al enviar a un PR existente, GitPR actualiza solo el cuerpo del PR (la descripción) mediante `PATCH /repos/{owner}/{repo}/pulls/{number}`. El título del PR permanece sin cambios. El contenido enviado es únicamente el campo Body del PR de la TUI — no se añade ningún texto envolvente ni prefijo de mensaje de commit.

---

## 7. Flujo de merge

Después de que un PR se crea o se actualiza, GitPR puede fusionarlo (merge) opcionalmente.

```
PR created/updated successfully
  ├─ GITPR_AUTO_MERGE=true → auto-merge via PUT /repos/{owner}/{repo}/pulls/{number}/merge
  ├─ GITPR_AUTO_MERGE=false → prompt user to merge
  └─ User declines → exit with PR URL displayed
```

| Variable | Predeterminado | Descripción |
|---|---|---|
| `GITPR_AUTO_MERGE` | `false` | Establécelo en `true` para fusionar automáticamente los PRs después de su creación/actualización sin preguntar |

---

## 8. Estructura del directorio de salida

De forma predeterminada, GitPR guarda todos los archivos de salida en el directorio `.gitpr/reports/`, organizados por tipo de artefacto:

| Variable de entorno | Subcarpeta en `.gitpr/reports/` |
|---|---|
| `OUTPUT_FILE_NAME` | `pr_desc` |
| `OUTPUT_FILE_NAME_REVIEW` | `review` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `full_review` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `file_review` |
| `OUTPUT_FILE_NAME_BLAME` | `blame` |
| `OUTPUT_FILE_NAME_ISSUE` | `issue` |

### 8.1 Reglas de resolución de rutas

La función `resolve_output_path()` en `src/core.py` maneja tres escenarios:

1. **La variable de entorno contiene un separador de directorio** (`/` o `\`) → se usa tal cual (ruta personalizada)
2. **La variable de entorno contiene solo un nombre de archivo** → se guarda en `.gitpr/reports/{folder}/`
3. **La variable de entorno está vacía o es la predeterminada** → se usa el patrón predeterminado en `.gitpr/reports/{folder}/`

Los directorios se crean automáticamente mediante `os.makedirs(exist_ok=True)`. Esto garantiza compatibilidad total hacia atrás: los usuarios con rutas de directorio personalizadas en su `.env` conservan su comportamiento actual.

---

## 9. Configuración de la rama base

La rama de destino del Pull Request se resuelve en el siguiente orden de prioridad:

| Prioridad | Origen | Cómo configurarlo |
|---|---|---|
| **1 (la más alta)** | bandera `--base` | `gitpr --base develop` |
| **2** | variable de entorno `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` en `~/.gitpr/.env` |
| **3 (predeterminada)** | Detección automática | `git symbolic-ref refs/remotes/origin/HEAD` (generalmente `main` o `master`) |

---

## 10. Atajos y navegación de la TUI

La interfaz fue diseñada para ser rápida y no requerir el uso constante del mouse. Puedes navegar por los campos con la tecla `Tab` y usar los siguientes atajos:

| Tecla | Acción | Descripción |
|---|---|---|
| **`F1`** | Ayuda | Abre un modal flotante con instrucciones rápidas de uso de la interfaz |
| **`F2`** | Guardar `.md` local | Guarda el contenido actualizado en el archivo de descripción del PR del proyecto actual. Ideal cuando quieres refinar el contenido más tarde |
| **`F3`** | Publicar PR | Ejecuta el auto-commit (linter + mensaje de IA + stage de archivos si es necesario) si hay cambios pendientes y luego crea o actualiza el Pull Request en GitHub mediante la API. El enlace directo al PR se mostrará en el terminal |
| **`Esc`** | Salir | Aborta la operación y cierra la interfaz sin publicar |
| **`Tab`** | Navegar | Alterna el foco entre los campos de la interfaz |

---

## 11. Integración con GitHub (token PAT)

Para crear Pull Requests directamente en el repositorio remoto (`F3`), GitPR necesita un **Personal Access Token (PAT)** de GitHub con el ámbito `repo`.

### 11.1 Configuración del token

La primera vez que uses `F3` o `--no-edit`, GitPR:

1. Detectar que no hay ningún token configurado
2. Mostrar la URL de generación del token con los parámetros prellenados (ámbito `repo`)
3. Pedirte que pegues el token generado
4. Almacenarlo cifrado (Fernet) en el archivo `~/.gitpr/.env`

> **Nota:** La TUI de Issues (`gitpr -is`) comparte el mismo token. Si ya configuraste un token para Issues, se reutilizará automáticamente.

### 11.2 Seguridad

- El token se almacena como un hash cifrado — nunca en texto plano
- La clave maestra de descifrado se encuentra en `~/.gitpr/secret.key`
- El token se valida mediante `GET /user` antes de que se abra la TUI
- Consulta la guía completa en [github-pat-integration.md](github-pat-integration.md)

---

## 12. Referencia de la API de GitHub

### 12.1 Creación de PR

`POST https://api.github.com/repos/{owner}/{repo}/pulls`

```json
{
  "title": "PR title (editable in TUI)",
  "body": "PR body content from the TUI text area",
  "head": "Current branch (source)",
  "base": "Target branch (main, develop, etc.)"
}
```

> **Nota:** Solo se envía el contenido del campo Body del PR como `body` — no se incluye ningún texto envolvente ni prefijo de mensaje de commit.

### 12.2 Actualización de PR (PR existente)

`PATCH https://api.github.com/repos/{owner}/{repo}/pulls/{number}`

```json
{
  "body": "Updated PR body content from the TUI text area"
}
```

### 12.3 Merge de PR

`PUT https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge`

```json
{
  "merge_method": "merge"
}
```

---

## 13. Manejo de errores

| Error | Comportamiento |
|---|---|
| Token no válido o caducado (401) | Solicita un token nuevo (hasta 3 intentos) |
| Rama no encontrada (422) | Muestra el mensaje de error de GitHub con los detalles |
| Sin commits para fusionar (422) | Muestra un error de validación que sugiere hacer cambios primero |
| El PR ya existe (422) | Muestra el conflicto específico; en la TUI, ofrece la opción de enviar al PR existente |
| Errores del linter | Pregunta al usuario: hacer commit con `--no-verify` o abortar |
| Fallo del commit ("nothing to commit") | Se trata como éxito: el flujo continúa hasta publicar |
| Fallo del commit (otro) | Muestra el error y permite reintentar o cancelar |
| Fallo del push (sin upstream) | Reintenta automáticamente con `--set-upstream origin <branch>` |
| Fallo del push (otro) | Muestra el mensaje de error con los detalles |
| Fallo de red | Muestra el mensaje de error de conexión |
| Remote ausente | Error antes de que se abra la TUI — no se intenta ninguna llamada a la API |

---

## 14. Variables de entorno

| Variable | Predeterminado | Descripción |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(ninguno)* | Token de Acceso Personal de GitHub cifrado |
| `PR_DEFAULT_BASE` | *(vacío)* | Rama de destino predeterminada (usa detección automática cuando está vacía) |
| `GITPR_AUTO_COMMIT` | `false` | Establécelo en `true` para ejecutar commits sin pedir confirmación |
| `GITPR_SKIP_LINT` | `false` | Establécelo en `true` para omitir la validación del linter durante el auto-commit |
| `GITPR_AUTO_STAGE` | `false` | Establécelo en `true` para hacer stage automático de todos los archivos unstaged sin mostrar el modal de selección |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Establécelo en `true` para omitir por completo la verificación de archivos unstaged al inicio |
| `GITPR_SHOW_LOGS` | `true` | Establécelo en `false` para ocultar los registros de progreso del commit/push en la TUI |
| `GITPR_AUTO_MERGE` | `false` | Establécelo en `true` para fusionar automáticamente los PRs después de su creación/actualización sin preguntar |
| `OUTPUT_FILE_NAME` | `{branch}_{datetime}_PR_DESC.md` | Patrón de nombre de archivo predeterminado para las descripciones de PR |
| `OUTPUT_FILE_NAME_REVIEW` | `{branch}_{datetime}_PR_REVIEW.txt` | Patrón de nombre de archivo predeterminado para las revisiones de código |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `{branch}_{datetime}_PR_FULLREVIEW.txt` | Patrón de nombre de archivo predeterminado para las revisiones completas |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `{branch}_{datetime}_FILE_REVIEW.txt` | Patrón de nombre de archivo predeterminado para las revisiones de archivos |
| `OUTPUT_FILE_NAME_BLAME` | `{branch}_{datetime}_BLAME_REPORT.md` | Patrón de nombre de archivo predeterminado para los informes de blame |
| `OUTPUT_FILE_NAME_ISSUE` | `{branch}_{datetime}_ISSUE.md` | Patrón de nombre de archivo predeterminado para las issues |

---

## 15. Ejemplos prácticos

### Ejemplo 1: Flujo de trabajo estándar — revisar y publicar

```bash
# You finished developing on the feature/login branch
gitpr
# → Unstaged files check (if any)
# → AI generates the PR description and opens the TUI
# → Review the title, body, and base branch
# → Press F3 to auto-commit and create the PR on GitHub
```

### Ejemplo 2: Publicación rápida sin edición

```bash
gitpr --no-edit
# → Unstaged files check (if any)
# → AI generates PR, auto-commits changes, pushes, and publishes immediately
# → The PR URL is displayed in the terminal
```

### Ejemplo 3: Solo guardar el archivo del PR localmente

```bash
gitpr --no-publish
# → AI generates PR description, saves .md file to .gitpr/reports/pr_desc/, exits
# → No TUI, no publication
```

### Ejemplo 4: Publicar contra una rama base personalizada

```bash
gitpr --base staging
# → Target branch is set to "staging" instead of "main"
```

### Ejemplo 5: Omitir el linter en el auto-commit

```bash
GITPR_SKIP_LINT=true gitpr --no-edit
# → Auto-commit skips lint, generates message, commits, pushes, and publishes
```

### Ejemplo 6: Auto-commit sin confirmación

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → Commit message is generated and executed without asking for confirmation
```

### Ejemplo 7: Omitir la verificación de archivos unstaged

```bash
GITPR_SKIP_UNSTAGED_CHECK=true gitpr --no-edit
# → Skips the startup unstaged files modal entirely
```

### Ejemplo 8: Auto-stage y auto-merge

```bash
GITPR_AUTO_STAGE=true GITPR_AUTO_MERGE=true gitpr --no-edit
# → All unstaged files are automatically staged
# → PR is automatically merged after creation
```

### Ejemplo 9: Directorio de salida personalizado

```bash
# In ~/.gitpr/.env:
OUTPUT_FILE_NAME=/home/user/prs/my_custom_pr.md
# → PR description saved to /home/user/prs/my_custom_pr.md
# → Directory paths in env vars are used as-is, never redirected to .gitpr/reports/
```

---

## 16. Archivos relacionados

| Archivo | Función |
|---|---|
| `.gitpr.pr.md` | Template local con reglas personalizadas para la generación de la descripción del PR (descárgalo con `gitpr -s`) |
| `~/.gitpr/.env` | Configuración global: claves de API, valores predeterminados de PR y token de GitHub cifrado |
| `~/.gitpr/secret.key` | Clave maestra Fernet para el descifrado de credenciales |
| `.gitpr/reports/pr_desc/` | Directorio de salida predeterminado para los archivos de descripción de PR |
| `.gitpr/reports/review/` | Directorio de salida predeterminado para los archivos de revisión de código |
| `.gitpr/reports/full_review/` | Directorio de salida predeterminado para los archivos de revisión completa |

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para obtener una visión general de todas las funciones de GitPR y la [guía de Descripción de PR](pr-descricao-padrao.md) para el flujo predeterminado de generación de PR.
