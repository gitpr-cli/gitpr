# Documentación Técnica: Notas de la Versión y Changelog (gitpr release)

Una sola ejecución resuelve dónde terminó la release anterior — la sección de la versión anterior en el changelog —, recoge los commits desde ahí hasta `HEAD`, los clasifica por Conventional Commits, descarta todo lo que una sección anterior ya listó, sugiere un bump semántico de versión, añade opcionalmente un resumen ejecutivo de IA y antepone una nueva sección de versión al changelog del repositorio. Cada entrada trae el enlace del commit y la fecha del evento, el pull request cuando el commit vino de un squash merge, y los contribuyentes se enlazan a su perfil en la forge.

---

## 1. Descripción General

El comando raíz conserva todas sus opciones heredadas sin cambios (`-r`, `-c`, `-is`, `-l`, ...) — el subcomando es una adición, no una reescritura. Ejecutado sin flags, `gitpr release` realiza el flujo local: recoge el rango de commits, clasifica, sugiere la versión, genera la sección (opcionalmente con resumen de IA), escribe el `CHANGELOG.md`, guarda el artefacto de la ejecución e imprime una vista previa en el terminal limitada a 40 líneas (`… and N more lines` cuando es mayor — v1 no tiene vista previa interactiva en TUI). Si ya existe una sección de versión en el changelog, el comando aborta en lugar de duplicarla (véase la sección 6, Modo JSON e Idempotencia).

### 1.1 Referencia del Comando — `gitpr release`

Todas las opciones del subcomando, tal como las muestra `gitpr release -h` (o `--help`):

```bash
gitpr release
gitpr release --version 2.0.0
gitpr release --publish
```

| Opción | Descripción |
| --- | --- |
| **`--since <tag>`** | Origen del rango: tag o referencia desde donde se recogen los commits (por defecto: la release anterior — vea la Sección 2.1) |
| **`--version <x.y.z>`** | Versión objetivo de la release (por defecto: sugerencia automática de bump semántico) |
| **`--publish`** | Tras generar, publica la release en la forge configurada (pide confirmación) |
| **`--draft`** | Crea la release como borrador en la forge (GitHub). Solo se aplica junto con `--publish`; GitLab no tiene concepto de borrador |
| **`--format {markdown\|json}`** | `json` imprime el resultado completo en stdout sin tocar archivos ni publicar (por defecto: `markdown`) |
| **`--force`** | Regenera la sección de versión cuando ya existe en el changelog (anulación de idempotencia) |

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Commits del rango `origin..HEAD` (origen = la release anterior), merges excluidos, menos lo que una sección anterior ya listó |
| **Resumen de IA** | Automático cuando hay una clave de API configurada (desactívelo con `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Archivos escritos** | Nueva sección en `CHANGELOG.md` + artefacto `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` |
| **Publicado** | Nada — la generación local es la opción por defecto |
| **Tags locales / archivos de versión** | Nunca se tocan (read-only: las sugerencias de versión provienen de la versión anterior en el changelog, con la última tag como alternativa) |

---

## 2. Rango de la Release y Sugerencia de Versión

### 2.1 Rango de Commits — `--since <tag>`

Una release siempre cubre los commits desde un origen hasta `HEAD`. El origen es, por defecto, **la release anterior registrada en el changelog**, de modo que cada versión lista solo su propio delta y nada que ya se publicó; el fin del rango es siempre `HEAD` — generar entre dos tags antiguas no está soportado en la v1. Los commits de merge nunca llegan al changelog: se excluyen en el momento de la recolección.

```bash
# Por defecto: desde la release anterior en el changelog hasta HEAD
gitpr release

# Origen explícito: todo desde v1.0.0
gitpr release --since v1.0.0
```

El origen por defecto se resuelve recorriendo esta cadena, deteniéndose en el primer paso que produzca una referencia utilizable (todo candidato debe ser ancestro de `HEAD`):

| # | Origen | Cuándo aplica |
| --- | --- | --- |
| 1 | **`--since <ref>`** | La flag siempre se respeta, y una referencia desconocida aborta la ejecución |
| 2 | **Hash del commit más reciente de la sección de la versión anterior** | El caso normal: los hashes de commit no dependen de las tags, así que el rango es exacto incluso cuando las tags de versión viven solo en otra rama |
| 3 | **La versión de esa sección, como tag (`1.2.0` o `v1.2.0`)** | Secciones escritas a mano, o generadas antes de que se emitieran los hashes |
| 4 | **Última tag alcanzable (`git describe --tags --abbrev=0`)** | Nada de lo anterior pudo usarse. Este rango puede listar commits ya publicados, así que viene con un aviso visible y una entrada en `warnings` |

Una sección cuyos commits ya fueron listados se descarta una segunda vez mediante un **filtro de seguridad**: antes de renderizar, cualquier commit cuyo hash corto aparezca en *otra* sección de versión del changelog se elimina, y el conteo se reporta (`{count} commit(s) already released in a previous version were skipped.`). El ancla ya lo evita; el filtro mantiene honesto un changelog editado a mano. Cuando todos los commits del rango ya fueron publicados, la ejecución aborta en lugar de escribir una sección vacía (`❌ Nothing new to release: every commit of the range is already in {path}.`).

| Característica | Descripción |
| --- | --- |
| **Origen por defecto** | La sección de la versión anterior en el changelog (vea la cadena anterior) |
| **Sin sección anterior** | Primera release: el rango comienza en la última tag, o en el primer commit del repositorio cuando no hay tag |
| **Commits de merge** | Excluidos de la recolección |
| **Commits ya publicados** | Eliminados por el filtro de seguridad, con conteo |
| **Fin del rango** | Siempre `HEAD` |

### 2.2 Sugerencia de Versión Semántica

Sin `--version`, el motor sugiere un bump a partir de los commits clasificados, siguiendo el versionado semántico:

| Commits del rango | Bump sugerido |
| --- | --- |
| Cualquier commit **breaking** (cambio incompatible) | **MAJOR** |
| Ningún commit breaking, al menos una **funcionalidad** | **MINOR** |
| Solo fixes, chores u otros cambios | **PATCH** |

La sugerencia es de solo lectura: proviene exclusivamente de la release anterior — la versión de la sección anterior del changelog, con la última tag git como respaldo — así que el motor nunca lee archivos de versión (como `pyproject.toml`) ni crea tags locales. El prefijo `v` de la versión anterior se conserva (`v1.2.3` sugiere `v1.2.4`, escrito como `## [v1.2.4]`). Cuando no existe ninguna versión semántica anterior, no hay sugerencia — en una primera release, el `--version` se vuelve obligatorio para publicar.

Cuando la versión proviene de la sugerencia, el comando pide confirmación antes de la llamada de IA: `❓ Use the suggested version {version}?` (aceptar es la opción por defecto). El prompt se omite con un `--version` explícito, en `--format json`, en terminales silenciosos o no interactivos, y con `GITPR_RELEASE_AUTO_BUMP=false` (que exige un `--version` explícito en cada ejecución).

### 2.3 Versión Explícita — `--version <x.y.z>`

El `--version` anula la sugerencia (sin prompt de confirmación) y es la única fuente de la tag publicada en la forge. Pase un `x.y.z` simple — el prefijo `v` no es necesario.

```bash
gitpr release --version 2.0.0
gitpr release --since v1.0.0 --version 1.1.0
```

---

## 3. Estructura del Changelog y Archivos

### 3.1 Clasificación de Commits

Cada commit del rango se analiza con las reglas de Conventional Commits: `type`, `scope` opcional, marcadores de breaking (`!` tras el type/scope o una línea `BREAKING CHANGE:` en el cuerpo) y la cola de squash-merge de PR `(#123)`. Los commits que no siguen la convención nunca se rechazan — caen en **OTHER** con un aviso, y los duplicados del mismo PR se reconocen y se deduplican.

| Categoría | Disparador | Encabezado (respaldo en inglés) |
| --- | --- | --- |
| **BREAKING** | Marcador de breaking en cualquier type (`feat!`, `refactor!`, `BREAKING CHANGE:` ...) | `⚠️ Breaking Changes` |
| **FEATURE** | `feat:` | `✨ Features` |
| **FIX** | `fix:` | `🐛 Fixes` |
| **PERFORMANCE** | `perf:` | `⚡ Performance` |
| **DOCS** | `docs:` | `📚 Docs` |
| **REFACTOR** | `refactor:` | `♻️ Refactoring` |
| **CHORE** | `chore:` | `🔧 Chores` |
| **OTHER** | Cualquier otra cosa (no conformes o tipos desconocidos) | `📦 Other Changes` |

Los bloques de categoría siguen el orden fijo FEATURE, FIX, PERFORMANCE, DOCS, REFACTOR, CHORE, OTHER (los bloques vacíos se omiten). Los commits breaking aparecen solo bajo `⚠️ Breaking Changes`, nunca duplicados dentro de su propia categoría. Los encabezados pasan por el motor de localización de GitPR, de modo que el archivo generado sigue el idioma de la interfaz, con inglés como respaldo.

### 3.2 Anatomía de una Sección de Versión

Una release produce una sección de versión: el encabezado `## [x.y.z] - date`, un `### Summary` opcional, un bloque por cada categoría presente y un pie `**Contributors:**` con los nombres únicos de autores (deduplicados por correo, ordenados). Cada entrada sigue este formato:

```text
- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}
```

| Parte | Regla |
| --- | --- |
| `({short_hash})` | Siempre presente, enlazado al commit en la forge. La forma corta permanece visible como texto del enlace |
| `— {scope}` | Solo cuando el Conventional Commit declara un scope (posición sin cambios) |
| `· [#{n}]({pr_url})` | Solo cuando el commit lleva un número de PR (sufijo `(#123)` de squash merge) |
| `· {YYYY-MM-DD}` | Siempre presente — la fecha de autoría del commit |

```markdown
## [1.2.0] - 2026-09-08

### Summary
Release highlights generated by the AI executive summary.

### ⚠️ Breaking Changes
- drop support for Python 3.9 ([b2c3d4e](https://github.com/acme/app/commit/b2c3d4e…)) — core · 2026-09-02

### ✨ Features
- add the gitpr release subcommand ([a1b2c3d](https://github.com/acme/app/commit/a1b2c3d…)) — cli · 2026-09-01
- publish releases on GitLab ([d4e5f6a](https://github.com/acme/app/commit/d4e5f6a…)) — scm · [#567](https://github.com/acme/app/pull/567) · 2026-09-03

### 🐛 Fixes
- handle repositories without tags ([f6a7b8c](https://github.com/acme/app/commit/f6a7b8c…)) — release · 2026-09-04

**Contributors:** [@anasouza](https://github.com/anasouza), Bob Smith
```

Los contribuyentes se enlazan a su perfil cuando la forge expone uno: el correo del autor se resuelve a un login, y el pie renderiza `[@login]({profile_url})` en lugar del nombre visible. La resolución es best-effort y nunca bloquea la release — un nombre que no pueda mapearse (sin token, offline, dirección privada, o una forge sin perfiles simples como Azure DevOps) conserva su nombre visible. Los aciertos se guardan en caché en `~/.gitpr/cache/contributors.json` (`email → login`); solo se escriben los aciertos, así que una ejecución limitada por rate limit lo intenta de nuevo en la próxima release.

Sin contexto de enlaces de la forge — sin remote `origin`, o un remote cuyo host no es una de las forges soportadas — la sección degrada a texto plano: los hashes quedan sin enlace y la fecha y el número de PR permanecen. Una sección nunca se pierde por un fallo de enlace.

La sección se antepone al `CHANGELOG.md` — el archivo nunca se reescribe desde cero y las secciones anteriores se preservan. Cuando ya existe una sección `## [x.y.z]` de la misma versión, el comando aborta con código de salida 1 (vea la Sección 6, Modo JSON e Idempotencia); nunca duplica ni sobrescribe silenciosamente.

### 3.3 Archivos Escritos

| Artefacto | Ruta | Notas |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Raíz del repositorio por defecto — la excepción deliberada a la convención de `.gitpr/reports/`, porque es un archivo público y commiteable. Anule con `GITPR_RELEASE_CHANGELOG_PATH` (las rutas relativas se resuelven contra la raíz del repositorio) |
| **Artefacto de notas de la versión** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Se escribe en cada ejecución markdown, best-effort: un fallo de escritura solo avisa y nunca tumba el comando. Plantilla de nombre vía `OUTPUT_FILE_NAME_RELEASE` |
| **Vista previa en el terminal** | — | Se imprime tras guardar, hasta 40 líneas |
| **Caché de contribuyentes** | `~/.gitpr/cache/contributors.json` | Mapa `email → login` compartido por todos los repositorios; se escribe solo en aciertos, best-effort (un fallo de escritura solo significa que la próxima ejecución vuelve a resolver) |

---

## 4. Resumen Ejecutivo de IA

El párrafo `### Summary` opcional lo genera la IA a partir de los commits clasificados del rango y se escribe en el idioma actual de la interfaz.

### 4.1 Plantilla de Skill en el Primer Uso — `.gitpr.release.md`

```bash
# La primera ejecución en modo markdown descarga la plantilla (language-aware, nunca sobrescribe)
gitpr release
```

En la primera ejecución en modo markdown, el CLI descarga la plantilla de skill `.gitpr.release.md` de las plantillas del proyecto. La descarga respeta el idioma actual de la interfaz (las variantes remotas como `gitpr.release.es_es.md` se guardan localmente como `.gitpr.release.md`), nunca sobrescribe un archivo local existente y nunca falla por un error de red — la ejecución continúa con la persona integrada. La descarga se omite por completo en `--format json`, que es stdout-only. El archivo se carga como system instruction de la IA (persona: **Release Manager**, contrato estricto de JSON) — edítelo localmente para personalizar el resumen ejecutivo. Consulte la [documentación de Skills y Templates](skill-template.md) para conocer el mecanismo general.

### 4.2 Generación y Degradación Controlada

Los rangos con más de 200 commits se resumen en lotes (Map-Reduce, con un aviso como `📦 Large commit range detected!`), y las respuestas pasan por la caché MD5 estándar de GitPR, de modo que las ejecuciones sin cambios no repiten llamadas de IA. Dos notas: la caché tiene como clave el prompt — editar `.gitpr.release.md` no invalida los resúmenes en caché — y el resumen usa siempre la misma infraestructura de IA que los demás comandos de GitPR (proveedor configurado, salida JSON, reintento automático). Consulte la [documentación de Proveedores de IA](providers-ia.md).

El resumen nunca bloquea el comando: sin clave de API configurada, o cuando la llamada de IA falla, el comando avisa (`AI summary failed: changelog generated without a summary.`) y genera la sección solo con las listas clasificadas. `GITPR_RELEASE_AI_SUMMARY=false` desactiva el resumen por completo.

---

## 5. Publicación en la Forge

### 5.1 Confirmación y Salvaguardas — `--publish`

La publicación solo ocurre en el flujo markdown, tras la generación local y la vista previa, detrás de una confirmación explícita: `❓ Publish release {version} on {provider}?` — rechazar (la opción por defecto) conserva el changelog e imprime `⏭️ Publication skipped — the changelog was generated locally.` El cuerpo de la release enviado a la forge es la sección generada sin el encabezado `## [x.y.z] - date` (el título de la release lleva la versión).

```bash
gitpr release --publish
gitpr release --since v1.0.0 --version 1.2.0 --publish
```

Salvaguardas: sin un remote git `origin`, el comando se niega a publicar (`❌ No git remote 'origin' found. Cannot publish the release.`, código de salida 1); combinado con `--format json`, el `--publish` solo avisa de que se ignora (`⚠️ --format json is stdout-only: --publish is ignored.`) — el modo JSON nunca publica; tras una ejecución local simple, el CLI sugiere `ℹ️ To publish this release on the forge, run again with --publish.`

### 5.2 Forges Soportadas

La publicación apunta a la forge configurada en los ajustes SCM (`gitpr --init` o `GITPR_SCM_PROVIDER`). Consulte la [documentación Multi-Forge SCM](scm-multiforge.md) para la configuración del proveedor.

| Forge | Release | Notas |
| --- | --- | --- |
| **GitHub** | Sí | Una tag ausente se crea automáticamente por la API, apuntando a la rama por defecto del repositorio (no al `HEAD` local); los borradores se respetan |
| **GitLab** | Sí | La tag ya debe existir en la forge; no hay concepto nativo de borrador |
| **Bitbucket Cloud** | No | Sin API de release — el comando avisa y mantiene el changelog local para la publicación manual |
| **Azure DevOps** | No | Sin API de release — el comando avisa y mantiene el changelog local para la publicación manual |

Cuando la publicación no está soportada, el aviso es `⚠️ Release publishing is not supported on {provider}. The changelog was generated locally — publish it manually.`

### 5.3 Borradores — `--draft`

El `--draft` solo importa junto con `--publish` (aislado, avisa `⚠️ --draft only applies together with --publish: generating the changelog locally.`). GitHub es la única forge con concepto de borrador y, por defecto, un `--publish` en GitHub ya crea un **borrador** (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`); pase `--draft` para forzar un borrador cuando ese valor por defecto esté desactivado. GitLab no tiene borradores: una petición de borrador solo avisa y publica directamente.

```bash
gitpr release --publish --draft
```

---

## 6. Modo JSON e Idempotencia

### 6.1 Salida JSON Pura — `--format json`

El `--format json` es stdout-only, ideal para scripts y CI: no escribe nada (sin actualización del `CHANGELOG.md`, sin artefacto de la ejecución, sin descarga de skill), no publica nada y nunca pregunta (la confirmación de versión se omite). El stream de stdout permanece limpio — los avisos viajan dentro del payload JSON. La salida sigue el resultado de la release: `version`, `previous_version` (la versión leída del changelog), `previous_tag` (el origen del rango resuelto, que es un hash de commit cuando el ancla vino de una sección), `generated_at`, `summary`, `sections` (una lista de commits clasificados por categoría), `breaking_changes`, `contributors`, `markdown` y `warnings`.

```bash
gitpr release --format json
```

### 6.2 Sección Existente y `--force`

La escritura del changelog es idempotente por versión: cuando la sección `## [x.y.z]` de la versión objetivo ya existe, el comando aborta con código de salida 1 sin modificar el archivo — nunca duplica contenido ni lo sobrescribe silenciosamente. El `--force` regenera y reemplaza esa sección **por completo**, desde su encabezado hasta el siguiente encabezado de versión, manteniendo intactas las secciones vecinas (`🔄 Existing section for version {version} regenerated.`); sin sección existente, el `--force` es una simple adición.

```bash
gitpr release --force
gitpr release --since v1.0.0 --version 1.2.0 --force
```

---

## 7. Variables de Entorno

La configuración de la release se lee del archivo global `~/.gitpr/.env` (formato dotenv). Los booleanos siguen la convención de "false desactiva": no definido o cualquier valor distinto de `false` / `0` / `no` / `off` / `n` significa activado — los valores por defecto de la tabla aplican cuando la variable no está definida.

| Variable | Valor por defecto | Finalidad |
| --- | --- | --- |
| `GITPR_RELEASE_CHANGELOG_PATH` | `CHANGELOG.md` | Archivo del changelog; rutas relativas resueltas contra la raíz del repositorio, rutas absolutas respetadas |
| `GITPR_RELEASE_AI_SUMMARY` | `true` | Activa el resumen ejecutivo de IA; `false` genera solo las listas clasificadas |
| `GITPR_RELEASE_AUTO_BUMP` | `true` | Activa el bump semántico automático; `false` exige un `--version` explícito |
| `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` | `true` | GitHub: `--publish` crea la release como borrador por defecto |
| `OUTPUT_FILE_NAME_RELEASE` | `{branch}_{datetime}_RELEASE.md` | Plantilla de nombre del artefacto de la ejecución en `.gitpr/reports/release/` |

> **Nota:** Consulte también la [documentación de Skills y Templates](skill-template.md) para personalizar los archivos de plantilla de IA de GitPR.
