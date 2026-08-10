# 📂 Git Status — Listado de Archivos No Commiteados y Verificación Unstaged

GitPR puede listar cambios de archivos no commiteados sin procesamiento de IA, y verifica automáticamente archivos fuera del stage antes de ejecutar cualquier comando de IA (commit, review, full review, issue y PR).

---

## 1. Flag `--status` — Listado Rápido de Archivos (Sin IA)

La flag `--status` lista todos los cambios de archivos no commiteados categorizados por tipo — **sin IA, sin red, sin git fetch**. Ejecución instantánea.

```bash
gitpr --status
```

Ejemplo de salida:
```
📂 Uncommitted changes (no AI):
  ➕ New files (2):
    - src/new_module.py
    - tests/test_new_module.py
  ✏️ Modified files (3):
    - src/core.py
    - src/main.py
    - README.md
  🗑️ Deleted files (1):
    - old_deprecated.py
```

### Categorías

| Categoría | Códigos git status | Descripción |
|-----------|-------------------|-------------|
| **Nuevos** (`➕`) | `??` | Archivos no rastreados — nunca añadidos a Git |
| **Modificados** (`✏️`) | ` M`, `MM`, `AM`, `RM` | Modificaciones no stageadas en el árbol de trabajo |
| **Eliminados** (`🗑️`) | ` D`, `MD`, `AD`, `RD` | Eliminaciones no stageadas en el árbol de trabajo |

> **Nota:** Los archivos que están stageados (añadidos vía `git add`) pero con el árbol de trabajo limpio (`M `, `A `, `D `) **no** se muestran. La flag `--status` muestra solo archivos con **cambios en el árbol de trabajo que aún no están en el área de stage**.

---

## 2. Verificación de Archivos Unstaged (Todos los Comandos)

Antes de generar cualquier análisis de IA, GitPR ahora verifica archivos fuera del stage en **todos** los comandos principales:

| Comando | Comportamiento cuando se encuentran archivos unstaged |
|---------|-------------------------------------------------------|
| `gitpr` (PR por defecto) | **Interactivo** — abre modal TUI para stage, omitir o cancelar |
| `gitpr -c` (commit) | **Advertencia** — alerta que los archivos unstaged NO estarán en el commit |
| `gitpr -r` (review) | **Informativo** — indica que los archivos unstaged aún se incluyen en el diff |
| `gitpr -f` (fullreview) | **Informativo** — indica que los archivos unstaged aún se incluyen en el diff |
| `gitpr -is` (issue, modo diff) | **Informativo** — indica que los archivos unstaged aún se incluyen en el diff |

### Comportamiento específico del commit

Al ejecutar `gitpr -c`, la advertencia es más fuerte porque los archivos unstaged **no** se incluirán en el mensaje de commit generado por la IA.

Si `GITPR_AUTO_STAGE=true` está establecido, `-c` hará auto-stage de los archivos antes de generar el mensaje de commit (mismo comportamiento que PR).

### Comportamiento Review/FullReview/Issue

Para `-r`, `-f` e `-is`, el diff ya incluye cambios unstaged, por lo que el análisis es preciso. El mensaje es solo informativo.

> **Nota:** `GITPR_AUTO_STAGE` **no** se aplica para review/fullreview/issue — hacer auto-stage como efecto secundario de un comando de análisis de solo lectura sería inesperado.

---

## 3. Flag `--no-unstaged-check`

Omite la verificación unstaged para una sola ejecución:

```bash
gitpr -c --no-unstaged-check
```

Equivalente a establecer `GITPR_SKIP_UNSTAGED_CHECK=true` pero solo para ese comando.

---

## 4. Protección en Modo Hook

Cuando GitPR se ejecuta dentro de un hook de Git (flag `--hook`, usado por `prepare-commit-msg`), la verificación unstaged se **omite completamente** — cualquier prompt o TUI bloquearía el proceso de `git commit`.

---

## 5. Variables de Entorno

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Establecer en `true` para omitir la verificación de archivos unstaged en todos los comandos |
| `GITPR_AUTO_STAGE` | `false` | Establecer en `true` para stagear automáticamente todos los archivos unstaged (solo PR y commit) |

---

## 6. Herramientas MCP

Dos nuevas herramientas MCP están disponibles para integración con IDEs:

### `list_unstaged_files`
Devuelve JSON estructurado con tres listas categorizadas:
```json
{
  "status": "changes_found",
  "new": ["no_rastreado.py"],
  "modified": ["editado.py"],
  "deleted": ["eliminado.py"],
  "total": 3,
  "message": ""
}
```

### `analyze_unstaged_diff`
Devuelve solo el diff **unstaged** (index vs árbol de trabajo), excluyendo cambios stageados.

> **Nota:** Los archivos no rastreados nunca aparecen en los diffs de git. Use `list_unstaged_files` para verlos.

La herramienta existente `analyze_diff` ha sido clarificada: devuelve el diff **no commiteado** (`git diff HEAD` — incluye tanto cambios stageados como no stageados, pero no archivos no rastreados).

---

## 7. Documentación Relacionada

- [¿Por qué GitPR ignoró mis archivos nuevos?](untracked-files.es_es.md)
- [Publicación de Pull Request](pull-request-publication.md)
- [Git Hooks Locales](git-hooks-locais.md)
