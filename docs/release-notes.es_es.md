# Documentación Técnica: Notas de la Versión y Changelog (gitpr release)

`gitpr release` es el primer subcomando del GitPR CLI y genera el changelog / las notas de la versión del repositorio actual ("release notes" y "changelog" designan el mismo flujo). Una sola invocación recorre los commits recogidos entre una tag de origen y el `HEAD`, los clasifica por Conventional Commits, sugiere un bump semántico de versión, añade opcionalmente un resumen ejecutivo de IA y antepone una nueva sección de versión al changelog del repositorio. La generación es puramente local por defecto — no se publica nada y no se toca ninguna tag local ni archivo de versión; `--publish` va más allá y crea la release en la forge configurada tras una confirmación explícita.

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
| **`--since <tag>`** | Origen del rango: tag o referencia desde donde se recogen los commits (por defecto: la última tag alcanzable, o el primer commit cuando no existe tag) |
| **`--version <x.y.z>`** | Versión objetivo de la release (por defecto: sugerencia automática de bump semántico) |
| **`--publish`** | Tras generar, publica la release en la forge configurada (pide confirmación) |
| **`--draft`** | Crea la release como borrador en la forge (GitHub). Solo se aplica junto con `--publish`; GitLab no tiene concepto de borrador |
| **`--format {markdown\|json}`** | `json` imprime el resultado completo en stdout sin tocar archivos ni publicar (por defecto: `markdown`) |
| **`--force`** | Regenera la sección de versión cuando ya existe en el changelog (anulación de idempotencia) |

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Commits del rango `since..HEAD`, merges excluidos |
| **Resumen de IA** | Automático cuando hay una clave de API configurada (desactívelo con `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Archivos escritos** | Nueva sección en `CHANGELOG.md` + artefacto `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` |
| **Publicado** | Nada — la generación local es la opción por defecto |
| **Tags locales / archivos de versión** | Nunca se tocan (read-only: las sugerencias de versión provienen solo de las tags git) |

---

## 2. Rango de la Release y Sugerencia de Versión

### 2.1 Rango de Commits — `--since <tag>`

Una release cubre siempre los commits desde un origen hasta el `HEAD`. El origen es, por defecto, la última tag alcanzable, y el final del rango es siempre el `HEAD` — generar entre dos tags antiguas no está soportado en v1. Los commits de fusión (merge) nunca llegan al changelog: se excluyen en el momento de la recogida.

```bash
# Por defecto: desde la última tag alcanzable hasta el HEAD
gitpr release

# Origen explícito: todo desde v1.0.0
gitpr release --since v1.0.0
```

| Característica | Descripción |
| --- | --- |
| **Origen por defecto** | Última tag alcanzable (`git describe --tags --abbrev=0`) |
| **Sin tag en el repositorio** | Primera release: el rango comienza en el primer commit del repositorio |
| **Commits de fusión (merge)** | Excluidos de la recogida |
| **Final del rango** | Siempre `HEAD` |

### 2.2 Sugerencia de Versión Semántica

Sin `--version`, el motor sugiere un bump a partir de los commits clasificados, siguiendo el versionado semántico:

| Commits del rango | Bump sugerido |
| --- | --- |
| Cualquier commit **breaking** (cambio incompatible) | **MAJOR** |
| Ningún commit breaking, al menos una **funcionalidad** | **MINOR** |
| Solo fixes, chores u otros cambios | **PATCH** |

La sugerencia es read-only: proviene exclusivamente de las tags git — el motor nunca lee archivos de versión (como `pyproject.toml`) ni crea tags locales. El prefijo `v` de la última tag se conserva (`v1.2.3` sugiere `v1.2.4`, escrito como `## [v1.2.4]`). Cuando no existe ninguna tag de versión semántica anterior, no hay sugerencia — en una primera release, el `--version` se vuelve obligatorio para publicar.

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

Una release produce una sección de versión: el encabezado `## [x.y.z] - date`, un `### Summary` opcional, un bloque por cada categoría presente y un pie `**Contributors:**` con los nombres únicos de autores (deduplicados por e-mail, ordenados). Cada entrada se presenta como `subject (short hash)`, con el scope del commit añadido cuando está presente:

```markdown
## [1.2.0] - 2026-09-08

### Summary
Release highlights generated by the AI executive summary.

### ⚠️ Breaking Changes
- drop support for Python 3.9 (b2c3d4e) — core

### ✨ Features
- add the gitpr release subcommand (a1b2c3d) — cli
- publish releases on GitLab (#567) (d4e5f6g) — scm

### 🐛 Fixes
- handle repositories without tags (f6a7b8c) — release

**Contributors:** Ana Souza, Bob Smith
```

La sección se antepone al `CHANGELOG.md` — el archivo nunca se reescribe desde cero y las secciones anteriores se conservan. Cuando ya existe una sección `## [x.y.z]` para la misma versión, el comando aborta con código de salida 1 (véase la sección 6, Modo JSON e Idempotencia); nunca duplica ni sobrescribe silenciosamente.

### 3.3 Archivos Escritos

| Artefacto | Ruta | Notas |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Raíz del repositorio por defecto — la excepción deliberada a la convención de `.gitpr/reports/`, porque es un archivo público y commiteable. Anule con `GITPR_RELEASE_CHANGELOG_PATH` (las rutas relativas se resuelven contra la raíz del repositorio) |
| **Artefacto de notas de la versión** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Se escribe en cada ejecución markdown, best-effort: un fallo de escritura solo avisa y nunca tumba el comando. Plantilla de nombre vía `OUTPUT_FILE_NAME_RELEASE` |
| **Vista previa en el terminal** | — | Se imprime tras guardar, hasta 40 líneas |

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

El `--format json` es stdout-only, ideal para scripts y CI: no escribe nada (sin actualización del `CHANGELOG.md`, sin artefacto de la ejecución, sin descarga de skill), no publica nada y nunca pregunta (la confirmación de versión se omite). El stream de stdout permanece limpio — los avisos viajan dentro del payload JSON. La salida sigue el resultado de la release: `version`, `previous_tag`, `generated_at`, `summary`, `sections` (una lista de commits clasificados por categoría), `breaking_changes`, `contributors`, `markdown` y `warnings`.

```bash
gitpr release --format json
```

### 6.2 Sección Existente y `--force`

La escritura del changelog es idempotente por versión: cuando la sección `## [x.y.z]` de la versión objetivo ya existe, el comando aborta con código de salida 1 sin modificar el archivo — nunca duplica contenido ni lo sobrescribe silenciosamente. El `--force` regenera y reemplaza esa sección (`🔄 Existing section for version {version} regenerated.`); sin sección existente, el `--force` es una simple adición.

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
