# 🎯 Smart Excludes — Optimización de Tokens

Si alguna vez has visto a GitPR reducir automáticamente tu diff antes de enviarlo a la IA, eso es **Smart Excludes** en acción. Esta página explica qué es, cómo funciona y cómo puedes personalizarlo para tu proyecto.

## 🔍 ¿Qué es Smart Excludes?

Smart Excludes es un sistema de optimización de tokens que **elimina automáticamente los archivos que no son código** de tu `git diff` antes de que se envíe a la IA para su análisis. Al descartar archivos de bloqueo (lockfiles), activos minificados, archivos binarios y prosa documental, la IA recibe un diff más limpio y relevante, lo que implica:

- **Menor consumo de tokens** (y menores costes de API)
- **Respuestas de IA más rápidas** (menos texto que procesar)
- **Análisis de mayor calidad** (la IA se centra en el código, no en el ruido)

## ⚙️ Cómo Funciona

GitPR utiliza la sintaxis nativa de **exclusión por pathspec** de Git (`:(exclude)*.md`) para filtrar archivos del diff. Esto ocurre a nivel del comando `git diff`, antes de que cualquier texto llegue a la IA, de modo que los archivos excluidos nunca consumen ni un solo token.

El sistema tiene **dos capas** de exclusiones:

### 1. Exclusiones Principales (Ruido)
Controladas por [`templates/gitpr.smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.smart-excludes.json):

- **Archivos de bloqueo (lockfiles):** `package-lock.json`, `yarn.lock`, `Cargo.lock`, `Pipfile.lock`, `uv.lock`, etc.
- **Activos minificados:** `*.min.js`, `*.min.css`, `*.bundle.js`
- **Archivos generados:** `*.map`, `*.pyc`, `*.log`
- **Archivos del sistema:** `.DS_Store`, `Thumbs.db`

### 2. Exclusiones de Documentación (Prosa)
Controladas por [`templates/gitpr.docs-smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.docs-smart-excludes.json):

- **Marcado/prosa:** `.md`, `.txt`, `.rst`, `.adoc`, `.asciidoc`, `.org`, `.textile`, `.wiki`
- **Escritura académica/técnica:** `.tex`, `.rtf`, `.pod`, `.rdoc`
- **Markdown ampliado:** `.mdx`, `.markdown`, `.rest`
- **Páginas de manual:** `.man`, `.1`–`.8`

Las dos listas se **combinan en tiempo de ejecución** en una única variable `SMART_EXCLUDES`, que se añade a todos los comandos `git diff` que ejecuta GitPR.

## 📋 Metadatos de Documentación (Documentos Modificados Sin Contenido)

Excluir la documentación del diff ahorra tokens, pero sigue siendo útil saber _qué_ documentos se modificaron. GitPR lo resuelve ejecutando un comando ligero adicional:

```bash
git diff --name-only <ref> -- <doc-paths>
```

Filtra la salida por las extensiones de documentación anteriores e **inyecta la lista de archivos como metadatos** en las instrucciones del sistema de la IA:

```
Changed documentation (content excluded from diff):
- docs/README.md
- CHANGELOG.md
- guides/setup.rst
```

De este modo, la IA sabe qué documentos cambiaron — un contexto útil para los mensajes de commit y las descripciones de PR — sin consumir tokens con el contenido completo de su prosa.

## 📁 Archivos de Configuración

| Archivo | Propósito | Gestión |
|------|---------|---------|
| `templates/gitpr.smart-excludes.json` | Exclusiones principales (lockfiles, binarios, minificados) | Remoto (GitHub) |
| `templates/gitpr.docs-smart-excludes.json` | Extensiones de documentación | Remoto (GitHub) |
| `~/.gitpr/conf/gitpr.smart-excludes.json` | Caché local de las exclusiones principales | Descarga automática |
| `~/.gitpr/conf/gitpr.docs-smart-excludes.json` | Caché local de las exclusiones de documentación | Descarga automática |

Ambas plantillas remotas tienen **control de versiones** — GitPR las vuelve a descargar automáticamente cuando se publica una nueva versión (activado por el marcador `__lang_version__`). Nunca necesitas actualizar estos archivos manualmente.

### Cadena de Resolución

Al iniciarse, GitPR carga cada lista de exclusiones mediante una cadena de respaldo de 4 pasos:

1. **Caché local** — `~/.gitpr/conf/` (la más rápida, sin red)
2. **Descarga remota** — desde el repositorio oficial de GitHub (tiempo de espera: 3 segundos)
3. **Copia local obsoleta** — se utiliza cuando la red no está disponible
4. **Respaldo integrado** — valores predeterminados fijos (garantiza el funcionamiento sin conexión)

## 📊 Ejemplo de Uso

Considera una rama en la que has modificado `src/auth.py`, `docs/README.md` y `package-lock.json`:

**Sin Smart Excludes** (todos los archivos en el diff):
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
diff --git a/docs/README.md b/docs/README.md
+ ## New Section
+ This is a long documentation update with many paragraphs...
diff --git a/package-lock.json b/package-lock.json
+ 500 lines of dependency tree changes
```
→ ~600+ líneas enviadas a la IA (~15,000 tokens)

**Con Smart Excludes** (solo código en el diff):
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
```
→ ~10 líneas enviadas a la IA (~250 tokens)

**Además, los metadatos** inyectados en la instrucción del sistema:
```
Changed documentation (content excluded from diff):
- docs/README.md
```

> **Resultado:** ~98% de reducción de tokens en este escenario, con la IA aún informada de que se actualizó documentación.

## 🎨 Personalización

### Añadir Nuevas Extensiones

Para añadir patrones nuevos de forma permanente, edita los archivos de plantilla en el [repositorio de GitPR](https://github.com/natanfiuza/gitpr):

1. Edita `templates/gitpr.smart-excludes.json` para el ruido que no es código
2. Edita `templates/gitpr.docs-smart-excludes.json` para las extensiones de documentación
3. Incrementa `__lang_version__` en `src/updater.py`
4. Los nuevos patrones se propagan a todos los usuarios en su siguiente ejecución

### Anulación Local (Temporal)

Puedes editar directamente los archivos en caché de `~/.gitpr/conf/`. Estos cambios persisten hasta el siguiente incremento de `__lang_version__`, cuando la versión remota los sobrescribe.

### Desactivar Extensiones Específicas

No existe un indicador de desactivación por proyecto. Smart Excludes está diseñado como una optimización global. Si necesitas que ciertos archivos de documentación permanezcan en el diff, elimina su extensión de la lista de exclusiones (mediante un PR al repositorio de plantillas).

## ❓ FAQ

### ¿Por qué se excluyen los archivos de documentación del diff?

La prosa documental (READMEs, guías, CHANGELOGs) puede tener miles de palabras. Incluirla en el prompt de la IA consume tokens que es mejor emplear en el análisis de los cambios de código. La IA sigue recibiendo los _nombres_ de los archivos como metadatos, por lo que sabe qué documentos cambiaron.

### ¿Cómo sé qué archivos de documentación se modificaron?

GitPR inyecta automáticamente la lista de archivos de documentación modificados en el contexto de la IA. También puedes ejecutar `git diff --name-only` por tu cuenta y filtrar por las extensiones enumeradas anteriormente.

### ¿Puedo desactivar Smart Excludes por completo?

Smart Excludes es una optimización principal y no se puede desactivar. Si crees que un tipo de archivo no debería excluirse, abre una issue o un PR en el [repositorio de GitPR](https://github.com/natanfiuza/gitpr).

### ¿Esto afecta al repositorio git real?

No. Smart Excludes solo afecta a lo que GitPR _lee_ de tu repositorio. Tu `git diff` real, tus commits y tu árbol de trabajo permanecen completamente sin cambios.

### ¿Qué ocurre con el Linter?

El linter estático (`.gitpr.linter.yml`) se ejecuta sobre el diff **después** del filtrado de Smart Excludes. Los archivos de documentación no se lintan.

---

📂 **Repositorio:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
🌐 **Sitio web:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
