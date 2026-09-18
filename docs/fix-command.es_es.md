# Documentación Técnica: Comando Fix (gitpr fix)

`gitpr fix` convierte los hallazgos de la última revisión de código en parches que se leen antes de que toquen el árbol. Una sola invocación localiza la revisión más reciente del repositorio y la rama actuales, pide a la IA el diff unificado más pequeño que corrija cada problema señalado por la revisión, clasifica cada parche según cuánto se puede confiar en él y — solo cuando se le indica — lo escribe en el árbol de trabajo y lo registra para poder deshacerlo. Leer es la opción por defecto: sin argumentos el comando lista los candidatos y no escribe nada, un hallazgo concreto se muestra como dry-run y escribir requiere `--apply`.

---

## 1. Descripción General

El subcomando es una adición al CLI, no un cambio en él: todas las opciones heredadas conservan su significado y `--force` aquí queda bajo el espacio de nombres de `gitpr fix` (en `gitpr release` significa "regenerar una sección de versión existente"). Todo el flujo es local — no se commitea nada, no se hace push y no se crea ninguna rama antes de confirmar una escritura.

### 1.1 Referencia del Comando — `gitpr fix`

Todas las opciones del subcomando, tal como las muestra `gitpr fix -h` (o `--help`):

```bash
gitpr fix                      # lista los candidatos de la última revisión
gitpr fix FIX-001              # dry-run: el diff de un hallazgo, nada se escribe
gitpr fix FIX-001 --apply      # escribe el parche, tras una confirmación
gitpr fix --all-safe --apply   # escribe cada parche seguro, en una rama nueva por defecto
gitpr fix --rollback FIX-001-1a2b3c4d
```

| Opción | Descripción |
| --- | --- |
| **`[<finding-id>]`** | Hallazgo al que apunta la ejecución (`FIX-001`). Sin `--apply` es un dry-run; sin id y sin `--all-safe` el comando lista en su lugar |
| **`--list`** | Lista los candidatos de corrección de la última revisión — es lo que hace el comando sin argumentos |
| **`--apply`** | Escribe el parche en el árbol de trabajo. Sin esta opción la ejecución es un dry-run que no toca nada |
| **`--all-safe`** | Selecciona todos los parches clasificados como seguros. Escribirlos todavía requiere `--apply` |
| **`--create-branch <name>`** | Crea y cambia a esta rama antes de aplicar los parches |
| **`--no-branch`** | Aplica en la rama actual incluso cuando la configuración crearía una |
| **`--yes`** | Omite la confirmación. Nunca evita `--force` |
| **`--force`** | Aplica un parche que no es seguro, tras escribir una frase de confirmación |
| **`--rollback <patch-id>`** | Deshace un parche aplicado antes, leyendo su diff del historial local |

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Revisión en caché más reciente del repositorio y la rama actuales — `gitpr -r` o `gitpr -f`, nunca la auditoría de archivo (`-i`) |
| **Llamada de IA** | Una llamada por revisión, con el modelo avanzado del proveedor configurado, cacheada en `fix/` como cualquier otra llamada de GitPR |
| **Archivos escritos** | Nada por defecto. `--apply` escribe en el árbol de trabajo y añade una entrada a `.gitpr/fix_history.json` |
| **Rama** | Solo un lote `--all-safe --apply`, y solo cuando la configuración lo pide |
| **Deshacer** | `--rollback <patch-id>` — sin commit, sin stash, sin reset |
| **Código de salida 1** | Sin revisión, sin cambios que parchear, sin clave de API, id de hallazgo desconocido, parche no seguro sin `--force`, una rama que no se puede crear |

---

## 2. De la Revisión a los Hallazgos

### 2.1 La Revisión que Lee

`gitpr fix` nunca revisa nada por sí mismo: consume la última revisión del repositorio y la rama actuales desde la caché de prompts (`~/.gitpr/cache/prompts/review/`). Entre los registros cacheados toma el más reciente cuyo `repo` y `branch` coincidan y cuyo `action_type` sea `review` o `fullreview` — los tres modos de revisión comparten esa carpeta, y un `filereview` (auditoría de archivo, `-i`) se excluye a propósito, porque la auditoría de un único archivo no tiene diff de rama que parchear.

Cuando no hay ninguna revisión registrada, el comando se detiene con `❌ No review found for {repo} on branch '{branch}'. Run 'gitpr -r' first.` — "no hay revisión" y "la revisión no encontró nada" nunca deben parecer lo mismo.

### 2.2 El Diff Viene del Registro

El *texto* de la revisión viene de la caché, y el *diff* también: el registro lleva el diff sobre el que la revisión se ejecutó realmente, y es contra él que se construyen los parches — la revisión que vio el revisor, no una reconstrucción de ella.

El campo no es una comodidad. Una revisión obtenida de un pull request (`gitpr review-pr`) no tiene árbol local alguno capaz de reproducir su diff, e incluso un `-f` local recalculado después solo puede aproximar la rama tal como estaba ese día. Los registros antiguos, escritos antes de que el diff empezara a guardarse, no tienen ese campo: para ellos el diff se recalcula como antes, con `get_git_diff()` para `review` y `get_git_full_diff()` para `fullreview`, elegida según el `action_type` registrado.

Un diff vacío aborta con `❌ The working tree has no changes to apply fixes to. Make the changes and run 'gitpr -r' again.` — en un diff registrado eso significa que la propia revisión no tenía qué mirar; en uno recalculado, que el árbol avanzó y ya no contiene los cambios.

### 2.3 Una Sola Llamada de IA y los Ids que Produce

Una única llamada pide al modelo el diff unificado más pequeño para cada hallazgo de la revisión, devolviendo un objeto JSON por hallazgo. Se ejecuta a través de la infraestructura estándar de GitPR (proveedor configurado, modelo avanzado, salida JSON, reintento) y de la caché MD5 estándar en `~/.gitpr/cache/prompts/fix/` — consulte la [documentación de Proveedores de IA](providers-ia.md).

Los ids los asigna gitpr, nunca el modelo: `FIX-001`, `FIX-002`, ... en el orden en que volvieron los hallazgos. Como el prompt se construye a partir de la misma revisión y el mismo diff, la respuesta cacheada se reutiliza y **los ids se mantienen entre ejecuciones** — el id que mostró un listado es el id al que apunta `--apply`. Volver a ejecutar `gitpr -r` produce una revisión nueva, y por tanto un prompt nuevo, hallazgos nuevos e ids nuevos.

Que un modelo responda con prosa en lugar del envoltorio esperado es un resultado ordinario, no un fallo: la ejecución informa `ℹ️ The review raised no fixable findings.` y no escribe nada.

| Campo | Significado |
| --- | --- |
| **`finding_id`** | `FIX-001` — asignado por gitpr, en el orden en que volvieron los hallazgos |
| **`file_path`** | La ruta que toca el parche. El parche es la fuente de verdad; el `file_path` del propio modelo es el respaldo para un hallazgo que no tiene ningún parche |
| **`line_start` / `line_end`** | El rango de líneas al que apuntó la revisión (0 cuando el modelo no indicó ninguno) |
| **`severity` / `category`** | Tal como los declaró la revisión (`critical`, `major`, `minor`, `info` / `bug`, `security`, ...) — registrados, nunca recalculados |
| **`message`** | El hallazgo, en el idioma de la interfaz |
| **`confidence`** | `high` / `medium` / `low` según los declare el modelo; `low` fuerza la clase `experimental` |
| **`diff`** | El diff unificado que corrige el hallazgo — el parche en sí |
| **`suggested_test`** | Lo que el modelo sugiere para cubrir la corrección |
| **`patch_id`** | `FIX-001-1a2b3c4d` — el id del hallazgo más los 8 primeros dígitos hexadecimales del MD5 del diff; a esto apunta `--rollback` |

---

## 3. Clasificación de Seguridad

La clasificación es determinista y no interviene la IA: el mismo resumen de parche y los mismos ajustes producen siempre el mismo veredicto, así que un parche clasificado `safe` en un dry-run sigue siendo `safe` cuando se ejecuta `--apply`. `git apply --check` se evalúa primero — un parche que no aplica en el árbol actual nunca es otra cosa.

| Clase | Criterios | Qué permite |
| --- | --- | --- |
| **`safe`** | Aplica limpiamente, un archivo, un hunk, dentro del límite de líneas cambiadas, fuera de las rutas sensibles, y no elimina ninguna línea que parezca una llamada | `--all-safe --apply` puede aplicarlo en lote |
| **`review_required`** | Aplica limpiamente, pero falló al menos una condición de `safe` | `--apply` sobre ese hallazgo, con confirmación |
| **`experimental`** | No aplica en este árbol, abarca más de un archivo, o el modelo declaró baja confianza | Nunca se aplica en lote. `--force` con una frase escrita es la única puerta |

### 3.1 Códigos de Razón

El veredicto siempre lleva una razón — la primera condición que falló, en este orden:

| Código de razón | Significado |
| --- | --- |
| `apply_check_failed` | No aplica en el árbol actual |
| `multi_file` | Cambia más de un archivo |
| `low_confidence` | La IA declaró baja confianza en él |
| `excluded_path` | Toca una ruta sensible configurada |
| `multiple_hunks` | Abarca más de un hunk |
| `too_many_lines` | Cambia más líneas que el límite configurado |
| `removes_call` | Elimina una línea que parece una llamada |
| `safe` | Ninguna condición falló |

El terminal convierte cada código en una frase traducida; la herramienta MCP informa el código en sí, para que quienes la consumen puedan comparar con una cadena estable.

### 3.2 Notas sobre los Criterios

Un hallazgo que el modelo respondió sin un parche utilizable sigue siendo un candidato, clasificado `experimental` con un diff vacío. Descartarlo ocultaría un problema señalado por la revisión, y el diff vacío es la verdad — git lo rechaza, así que nunca se puede aplicar por accidente.

La heurística de llamadas es deliberadamente tosca: cualquier línea eliminada que coincida con `\w+` seguido de un paréntesis de apertura la dispara, incluido un comentario borrado que solo mencione `foo()`. Se inclina hacia `review_required`, que es la dirección segura en la que equivocarse.

Las rutas sensibles tienen que ver con el *riesgo* (migraciones, workflows, docker, terraform), no con el ruido del diff — por eso son una configuración propia y no se comparten con la lista de smart-excludes.

---

## 4. Leer Antes de Escribir

### 4.1 Listar Candidatos

Sin id de hallazgo, `gitpr fix` (o `gitpr fix --list`) imprime todos los candidatos de la última revisión — clase, ubicación, mensaje e id del parche — y no escribe nada:

```text
🔎 Fix candidates from the last review:
  FIX-001  [safe]  src/core.py:210
     The retry loop swallows the exception.
     ↳ FIX-001-1a2b3c4d
  FIX-002  [review_required]  src/config.py:88
     The default timeout is duplicated.
     ↳ FIX-002-9f8e7d6c — it changes more lines than the configured limit
ℹ️ Apply one with 'gitpr fix <id> --apply'; the safe ones can be batched with '--all-safe --apply'.
```

La clase se colorea en verde (`safe`), amarillo (`review_required`) o rojo (`experimental`), y la frase de la razón solo aparece para las dos clases que no son seguras.

### 4.2 Dry Run — `gitpr fix <id>`

Con un id de hallazgo y sin `--apply`, la ejecución imprime el bloque del candidato, todo el diff unificado con los colores de terminal que usa el proyecto, todos los avisos, y cierra con `ℹ️ Dry run — nothing was written. Add --apply to write it.` No se toca nada del árbol. Cuando se crearía una rama, la ejecución lo indica (`ℹ️ Branch '{branch}' would be created before the patches are applied.`), y un dry-run con `--all-safe` lista además los candidatos que dejó fuera, cada uno con el id que lo recupera.

### 4.3 Escribir — `--apply`

Un parche que no esté clasificado como `safe` nunca lo escribe un `--apply` normal: la ejecución imprime el hallazgo, su clase y su razón, y sale con código 1 (`❌ {finding_id} is {safety} ({reason}) — re-run with --force to apply it anyway.`).

```bash
gitpr fix FIX-001 --apply
gitpr fix --all-safe --apply
gitpr fix FIX-002 --apply --force
```

Para un parche `safe` la ejecución pregunta `❓ Apply FIX-001 to the working tree?` (rechazar es la opción por defecto); rechazar imprime `❌ Operation cancelled by user.` y deja el árbol intacto. `--yes` o `GITPR_FIX_REQUIRE_CONFIRMATION=false` omiten ese prompt.

`--force` se abre con una frase escrita en lugar de un y/n: la ejecución imprime la clase y la razón y pide que se escriba exactamente la frase `apply FIX-001` (sin espacios sobrantes y sin distinguir mayúsculas). Una discrepancia aborta con `❌ The confirmation phrase does not match. Nothing was applied.` y código de salida 1 — `--yes` no elude este prompt. `--force` junto con `--all-safe` solo avisa de que no tiene efecto, ya que únicamente se seleccionan los parches seguros. `gitpr fix --apply` sin id de hallazgo y sin `--all-safe` avisa (`⚠️ Nothing was selected: name a finding id or add --all-safe.`) y en su lugar lista los candidatos.

Un parche que git rechaza se informa como un fallo con el mensaje propio de git y el lote continúa — que un candidato no se pueda aplicar no dice nada sobre el siguiente. No se registra nada en el historial por él: el registro existe para deshacer lo aplicado, y no se aplicó nada. Cada parche escrito se informa como `✅ Patch applied: FIX-001-1a2b3c4d (src/core.py)`.

### 4.4 Manejo de Ramas

| Situación | Comportamiento |
| --- | --- |
| `--all-safe --apply` con `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE=true` | Crea `GITPR_FIX_BRANCH_NAME_TEMPLATE` (por defecto `fix/gitpr-{datetime}`) desde el `HEAD` actual y aplica el lote allí; la rama original queda intacta |
| `--create-branch <name>` | Crea esa rama en su lugar (cualquier ejecución) |
| `--no-branch` | Aplica en la rama actual incluso cuando la configuración crearía una |
| Un solo hallazgo, o un dry-run | Nunca crea una rama |

La rama se crea una sola vez, antes del primer parche y solo en una ejecución real. Una rama que no se puede crear aborta el lote — continuar aplicaría los parches a la rama de la que el usuario intentaba salir.

### 4.5 Un Archivo que Ya Está Sucio

Cuando un parche apunta a un archivo que ya tiene cambios sin commitear, la ejecución avisa exactamente sobre esos archivos (`⚠️ These files already have uncommitted changes: ...`) antes de escribir. Avisar de todos los archivos sucios del repositorio se dispararía en casi todas las ejecuciones reales; solo la coincidencia entre el parche y los cambios pendientes es el caso en el que aplicar puede sorprender al usuario.

---

## 5. Historial y Rollback

### 5.1 `.gitpr/fix_history.json`

Cada parche aplicado se registra en `<root>/.gitpr/fix_history.json`, **rastreado en git** — el diff completo se guarda ahí precisamente para poder deshacer el parche sin un commit. El archivo se escribe de forma atómica (un archivo temporal hermano que se renombra sobre él), de modo que una escritura interrumpida nunca deja un historial a medias. La consecuencia de rastrearlo es deliberada y conocida: aplicar una corrección ensucia un archivo rastreado, así que aparece en `gitpr -c` y en las descripciones de PR hasta que se commitea — por eso `.gitpr/fix_history.json` viene en la lista de smart-excludes y queda fuera de los diffs de la IA.

| Campo | Significado |
| --- | --- |
| **`patch_id`** | `FIX-001-1a2b3c4d` — a esto apunta `--rollback` |
| **`finding_id`** | `FIX-001` |
| **`file_path`** | El archivo al que apuntó la revisión |
| **`files_changed`** | Todas las rutas que toca el diff |
| **`safety`** | `safe` / `review_required` / `experimental` en el momento de aplicarlo |
| **`branch`** | La rama en la que se aplicó el parche (`null` cuando se aplicó en el lugar) |
| **`applied_at`** | Marca de tiempo, en el formato de caché del proyecto |
| **`diff`** | El diff unificado completo, literal |
| **`provenance`** | Proveedor, modelo, versión del prompt, versión de gitpr, marca de tiempo de generación |
| **`rolled_back_at`** | Marca de tiempo una vez deshecho; en caso contrario, `null` |

### 5.2 `--rollback <patch-id>`

El rollback lee el diff guardado y lo reproduce con `git apply --reverse` — sin commit, sin stash, sin reset y sin depender de que el árbol de trabajo siga coincidiendo con lo aplicado. Git mismo verifica la reversión contra el archivo: si el árbol avanzó, la reversión falla, se informa el error y no queda ningún archivo a medias. En caso de éxito la ejecución imprime `ℹ️ Undone patch {patch_id}: {files} restored.` y marca la entrada como deshecha.

| Rechazo | Mensaje |
| --- | --- |
| No existe ese id de parche en este repositorio | `❌ No applied patch with id '{patch_id}' was recorded here.` |
| Ya deshecho | `❌ Patch '{patch_id}' was already rolled back at {when}.` — deshacer dos veces es un error, no una operación sin efecto |
| Aplicado en otra rama | `❌ Patch '{patch_id}' was applied on branch '{branch}': switch back to it to undo the patch.` — el archivo que hay que restaurar no está aquí |
| El árbol avanzó de forma incompatible | `❌ Could not undo patch '{patch_id}': {error}` — el mensaje propio de git, sin dejar ningún archivo a medias |

`--rollback` no acepta id de hallazgo y no se puede combinar con `--apply` ni `--all-safe`.

---

## 6. Plantilla de Skill — `.gitpr.fix.md`

La llamada de hallazgos usa el archivo `.gitpr.fix.md` como system instruction de la IA (persona: **Senior Software Engineer**, que normaliza la revisión en parches mínimos). La plantilla la descarga `gitpr --skill` — respeta el idioma actual (`gitpr.fix.md` para inglés, `gitpr.fix.pt_br.md` para PT-BR) y nunca sobrescribe un archivo local existente. Sin ella se usa la persona integrada.

La plantilla enuncia el contrato del que depende el pipeline: el parche es la fuente de verdad, un hunk en un archivo, nunca reformatear código no tocado, nunca eliminar una llamada o una guarda existente, declarar una `confidence` honesta y dejar el `diff` vacío cuando el hallazgo necesita una decisión humana. Edítela localmente para cambiar cómo se escriben los parches; el prompt se construye a partir de ella, así que un cambio produce un prompt nuevo y una llamada de IA nueva. Consulte la [documentación de Skills y Templates](skill-template.md) para conocer el mecanismo general.

---

## 7. Integración MCP

`list_fix_candidates` es la decimotercera herramienta MCP y es **read-only**: informa lo que `gitpr fix` podría aplicar, parche incluido, y nunca escribe en el árbol de trabajo. El argumento opcional `finding_id` limita la respuesta a un solo hallazgo.

```json
{"status": "success", "finding_count": 2, "candidates": [ ... ]}
```

Cada candidato lleva `finding_id`, `patch_id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`, `safety`, `safety_reason` (el código estable, no una frase), `confidence`, `suggested_test` y `diff`. El estado es `no_data` cuando la revisión no señaló nada que pudiera convertirse en un parche, y `error` con un `message` cuando no hay ninguna revisión que leer o el pipeline no puede ejecutarse en absoluto. Consulte la [documentación de Integración MCP](mcp-integration.md).

---

## 8. Variables de Entorno

La configuración de fix se lee del archivo global `~/.gitpr/.env` (formato dotenv). Los dos booleanos siguen la convención de "false desactiva": no definido o cualquier valor distinto de `false` / `0` / `no` / `off` / `n` significa activado — los valores por defecto de la tabla aplican cuando la variable no está definida.

| Variable | Valor por defecto | Finalidad |
| --- | --- | --- |
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | `5` | Líneas añadidas + eliminadas que un parche puede llevar y seguir siendo `safe`; un valor no positivo o no interpretable vuelve a `5` |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | `database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**` | Rutas sensibles, separadas por `;`. Un parche que toque una todavía aplica, pero nunca es `safe` |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | `true` | Pide confirmación antes de escribir un parche seguro; `false` la omite (`--yes` hace lo mismo en una ejecución) |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `true` | `--all-safe --apply` crea una rama antes de escribir; `--no-branch` lo anula en una ejecución |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | `fix/gitpr-{datetime}` | Nombre de esa rama. Marcadores: `{branch}` (rama actual) y `{datetime}` |

> **Nota:** Consulte también la [documentación de Skills y Templates](skill-template.md) para personalizar los archivos de plantilla de IA de GitPR.
