# Documentación Técnica: Publicación de PR en GitHub

Esta documentación describe el flujo de publicación de Pull Requests mediante la interfaz interactiva de terminal (TUI), lo que te permite revisar, editar y publicar Pull Requests directamente en GitHub sin salir del terminal.

---

## 1. ¿Qué es el Publicador de PR?

Cuando ejecutas el comando `gitpr` (comportamiento predeterminado), GitPR genera la descripción del PR con IA, guarda el archivo `.md` localmente y abre un panel interactivo directamente en el terminal. Esto te permite revisar, editar y publicar el Pull Request generado por la Inteligencia Artificial antes de enviarlo al repositorio remoto mediante la API REST.

---

## 2. Modos de ejecución

El Publicador de PR tiene **3 modos de ejecución**, activados por las banderas (o la ausencia de ellas).

### 2.1 Modo interactivo (predeterminado) — `gitpr`

Ejecutar `gitpr` sin ninguna bandera genera la descripción del PR y abre la TUI para su revisión y edición antes de publicar.

```bash
gitpr
```

| Característica | Descripción |
|---|---|
| **Flujo** | `git fetch` → la IA genera el PR → `.md` guardado → se abre la TUI → el usuario edita → POST a GitHub |
| **Cuándo usarlo** | Flujo de trabajo estándar: control total sobre lo que se publica |
| **Resultado** | Pull Request creado en GitHub con el contenido editado |
| **Ideal para** | Desarrollo diario: revisar y ajustar el contenido del PR antes de publicar |

> **Consejo:** El archivo `.md` local se guarda antes de que se abra la TUI y se vuelve a guardar con cualquier edición antes de publicar. Siempre tienes una copia de seguridad.

---

### 2.2 Omitir el publicador — `gitpr --no-publish`

Genera el PR y lo guarda localmente sin abrir el editor interactivo.

```bash
gitpr --no-publish
```

| Característica | Descripción |
|---|---|
| **Flujo** | `git fetch` → la IA genera el PR → `.md` guardado → salida |
| **Cuándo usarlo** | Cuando solo necesitas el archivo de descripción del PR para documentación o revisión posterior |
| **Resultado** | Archivo Markdown guardado localmente; no se abre ninguna TUI |
| **Ideal para** | Documentación, revisión sin conexión, guardar borradores de PR para más tarde |

---

### 2.3 Publicación directa — `gitpr --no-edit`

Omite el editor interactivo, hace commit automático (auto-commit) de los cambios pendientes con validación del linter y publica directamente en GitHub.

```bash
gitpr --no-edit
```

| Característica | Descripción |
|---|---|
| **Flujo** | `git fetch` → la IA genera el PR → `.md` guardado → auto-commit (linter + mensaje de commit con IA) → POST directo a GitHub |
| **Cuándo usarlo** | Cuando confías en el resultado de la IA y quieres publicar de inmediato |
| **Resultado** | Pull Request creado en GitHub sin abrir la TUI |
| **Ideal para** | Pipelines de CI/CD, correcciones rápidas, flujos de trabajo automatizados |

> **Precaución:** Úsalo con cuidado: no tendrás la oportunidad de revisar ni editar el contenido antes de publicar.

---

## 3. Flujo de auto-commit (--no-edit y F3 de la TUI)

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
   └─ Display message, request confirmation
   
4. Execute: git commit -m "<message>" [--no-verify]
   └─ Proceed with PR publication
```

### Diagrama de flujo de decisión del linter

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

---

## 4. Configuración de la rama base

La rama de destino del Pull Request se resuelve en el siguiente orden de prioridad:

| Prioridad | Origen | Cómo configurarlo |
|---|---|---|
| **1 (la más alta)** | bandera `--base` | `gitpr --base develop` |
| **2** | variable de entorno `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` en `~/.gitpr/.env` |
| **3 (predeterminada)** | Detección automática | `git symbolic-ref refs/remotes/origin/HEAD` (generalmente `main` o `master`) |

---

## 5. Atajos y navegación de la TUI

La interfaz fue diseñada para ser rápida y no requerir el uso constante del mouse. Puedes navegar por los campos con la tecla `Tab` y usar los siguientes atajos:

| Tecla | Acción | Descripción |
|---|---|---|
| **`F1`** | Ayuda | Abre un modal flotante con instrucciones rápidas de uso de la interfaz |
| **`F2`** | Guardar `.md` local | Guarda el contenido actualizado en el archivo de descripción del PR del proyecto actual. Ideal cuando quieres refinar el contenido más tarde |
| **`F3`** | Publicar PR | Ejecuta el auto-commit (linter + mensaje de IA) si hay cambios pendientes y luego crea el Pull Request en GitHub mediante la API. El enlace directo al PR recién creado se mostrará en el terminal |
| **`Esc`** | Salir | Aborta la operación y cierra la interfaz sin publicar |
| **`Tab`** | Navegar | Alterna el foco entre los campos de la interfaz |

---

## 6. Integración con GitHub (token PAT)

Para crear Pull Requests directamente en el repositorio remoto (`F3`), GitPR necesita un **Personal Access Token (PAT)** de GitHub con el ámbito `repo`.

### 6.1 Configuración del token

La primera vez que uses `F3` o `--no-edit`, GitPR:

1. Detectar que no hay ningún token configurado
2. Mostrar la URL de generación del token con los parámetros prellenados (ámbito `repo`)
3. Pedirte que pegues el token generado
4. Almacenarlo cifrado (Fernet) en el archivo `~/.gitpr/.env`

> **Nota:** La TUI de Issues (`gitpr -is`) comparte el mismo token. Si ya configuraste un token para Issues, se reutilizará automáticamente.

### 6.2 Seguridad

- El token se almacena como un hash cifrado — nunca en texto plano
- La clave maestra de descifrado se encuentra en `~/.gitpr/secret.key`
- El token se valida mediante `GET /user` antes de que se abra la TUI
- Consulta la guía completa en [github-pat-integration.md](github-pat-integration.md)

---

## 7. API de GitHub — creación de PR

El PR se crea mediante `POST https://api.github.com/repos/{owner}/{repo}/pulls` con el siguiente payload:

```json
{
  "title": "PR title (editable in TUI)",
  "body": "Full markdown PR description with commit message",
  "head": "Current branch (source)",
  "base": "Target branch (main, develop, etc.)"
}
```

---

## 8. Manejo de errores

| Error | Comportamiento |
|---|---|
| Token no válido o caducado (401) | Solicita un token nuevo (hasta 3 intentos) |
| Rama no encontrada (422) | Muestra el mensaje de error de GitHub con los detalles |
| Sin commits para fusionar (422) | Muestra un error de validación que sugiere hacer cambios primero |
| El PR ya existe (422) | Muestra el conflicto específico |
| Errores del linter | Pregunta al usuario: hacer commit con `--no-verify` o cancelar |
| Fallo del commit | Muestra el error y permite reintentar o cancelar |
| Fallo de red | Muestra el mensaje de error de conexión |
| Remote ausente | Error antes de que se abra la TUI — no se intenta ninguna llamada a la API |

---

## 9. Variables de entorno

| Variable | Predeterminado | Descripción |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(ninguno)* | Token de Acceso Personal de GitHub cifrado |
| `PR_DEFAULT_BASE` | *(vacío)* | Rama de destino predeterminada (usa detección automática cuando está vacía) |
| `GITPR_AUTO_COMMIT` | `false` | Establécelo en `true` para ejecutar commits sin pedir confirmación |
| `GITPR_SKIP_LINT` | `false` | Establécelo en `true` para omitir la validación del linter durante el auto-commit |
| `GITPR_AUTO_STAGE` | `false` | Establécelo en `true` para hacer stage automático de todos los archivos unstaged sin mostrar el modal de selección |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Establécelo en `true` para omitir completamente la verificación de archivos unstaged al inicio |

---

## 10. Ejemplos prácticos

### Ejemplo 1: Flujo de trabajo estándar — revisar y publicar

```bash
# You finished developing on the feature/login branch
gitpr
# → AI generates the PR description and opens the TUI
# → Review the title, body, and base branch
# → Press F3 to auto-commit and create the PR on GitHub
```

### Ejemplo 2: Publicación rápida sin edición

```bash
gitpr --no-edit
# → AI generates PR, auto-commits changes, and publishes immediately
# → The PR URL is displayed in the terminal
```

### Ejemplo 3: Solo guardar el archivo del PR localmente

```bash
gitpr --no-publish
# → AI generates PR description, saves .md file, exits
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
# → Auto-commit skips lint, generates message, commits, and publishes
```

### Ejemplo 6: Auto-commit sin confirmación

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → Commit message is generated and executed without asking for confirmation
```

---

## 11. Archivos relacionados

| Archivo | Función |
|---|---|
| `.gitpr.pr.md` | Template local con reglas personalizadas para la generación de la descripción del PR (descárgalo con `gitpr -s`) |
| `~/.gitpr/.env` | Configuración global: claves de API, valores predeterminados de PR y token de GitHub cifrado |
| `~/.gitpr/secret.key` | Clave maestra Fernet para el descifrado de credenciales |

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para obtener una visión general de todas las funciones de GitPR y la [guía de Descripción de PR](pr-descricao-padrao.md) para el flujo predeterminado de generación de PR.
