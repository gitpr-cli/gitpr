# Documentación Técnica: Generación de Pull Request (Modo Predeterminado)

Cuando se ejecuta **sin flags**, GitPR genera una descripción completa de Pull Request en Markdown con IA — lista para pegar en GitHub, GitLab o Bitbucket — y abre un panel interactivo (TUI) para revisar, editar y publicar el PR directamente en GitHub sin salir de la terminal.

---

## 1. Uso

```bash
gitpr
```

| Modo | Comando | Comportamiento |
|---|---|---|
| Interactivo (predeterminado) | `gitpr` | Genera el PR y abre la TUI para revisar y publicar |
| Solo guardar | `gitpr --no-publish` | Genera el PR y guarda el archivo `.md` localmente |
| Publicación directa | `gitpr --no-edit` | Genera el PR, hace auto-commit, push y publica sin abrir la TUI |

---

## 2. Flujo de Ejecución

```
verificación de archivos unstaged → git fetch → diff contra origin/main → IA → .md → TUI → publicar
```

1. **Verificación de archivos unstaged** — Detecta archivos sin commit y ofrece stage (stage, omitir o cancelar)
2. **`git fetch`** — Sincroniza con el repositorio remoto
3. **Diff** — Compara todos los cambios de la rama actual contra `origin/main`
4. **IA** — Genera el mensaje de commit (Conventional Commits) y la descripción del PR
5. **Output** — Guarda un archivo `.md` en `.gitpr/reports/pr_desc/`
6. **Publicar** — Abre la TUI (`F3` = publicar) o publica directamente con `--no-edit`

---

## 3. Output

El archivo generado (`{branch}_{datetime}_PR_DESC.md`) se guarda en `.gitpr/reports/pr_desc/` y contiene:

```markdown
# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
feat: short description of the change

---

## Description
...
## Changes
...
## Impact
...
```

---

## 4. Publicación del Pull Request

El publicador está disponible en 3 modos:

### 4.1 Modo Interactivo (Predeterminado)

Ejecutar `gitpr` abre la TUI después de generar la descripción. Atajos:

| Tecla | Acción |
|---|---|
| **`F1`** | Ayuda |
| **`F2`** | Guarda el archivo `.md` localmente |
| **`F3`** | Publica el PR (auto-commit → push → crea/actualiza el PR en GitHub) |
| **`Esc`** | Sale sin publicar |

### 4.2 Solo Guardar

```bash
gitpr --no-publish
```

Genera la descripción y guarda el archivo `.md` sin abrir la TUI.

### 4.3 Publicación Directa

```bash
gitpr --no-edit
```

Omite la TUI: hace auto-commit de los cambios pendientes (linter + mensaje de commit con IA), hace push y publica directamente. Úsalo con cuidado — el contenido no se revisa antes de publicar.

Para publicar, GitPR necesita un **Personal Access Token (PAT)** de GitHub con ámbito `repo`, almacenado cifrado en `~/.gitpr/.env`. La rama de destino se resuelve mediante la flag `--base` → env `PR_DEFAULT_BASE` → detección automática.

> **Nota:** Consulta la [guía completa de publicación](pull-request-publication.md) para el flujo detallado (verificación de unstaged, auto-commit, merge, manejo de errores).

---

## 5. Personalización

### 5.1 Plantilla de PR

El comportamiento de la IA se puede personalizar mediante el archivo `.gitpr.pr.md`:

```bash
gitpr -s          # Downloads the template
# Edit .gitpr.pr.md with your team's required sections
gitpr             # The AI will follow your template
```

### 5.2 Nombre del Archivo de Salida

Configura la variable de entorno `OUTPUT_FILE_NAME` en el archivo `~/.gitpr/.env`:

```ini
OUTPUT_FILE_NAME=PR_{branch}_{datetime}.md
```

Variables disponibles: `{branch}` (nombre de la rama actual) y `{datetime}` (timestamp `YYYYMMDDHHMMSS`).

---

## 6. Selección de Proveedor de IA

```bash
gitpr -p gemini       # Forces Google Gemini
gitpr -p deepseek     # Forces DeepSeek
```

Si no se especifica ningún proveedor, GitPR usa el predeterminado definido en la variable `DEFAULT_AI_PROVIDER` de `~/.gitpr/.env`.

---

## 7. Caché de Respuestas

GitPR genera un hash MD5 del diff + instrucciones de la IA. Si ejecutas `gitpr` nuevamente **sin cambiar el código**, la respuesta se devuelve desde la caché local en milisegundos, sin consumir cuotas de la API.

> **Nota:** Consulta también la [documentación principal (README.md)](../README.md) para una visión general de todas las funcionalidades.
