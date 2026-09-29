# Métricas y Telemetría — Analytics Local Offline

GitPR mantiene un **registro local y offline de uso**: una fila por cada comando
ejecutado, cuánto costó y cuánto tardó. Nada sale de tu máquina — el registro es
un archivo SQLite en `~/.gitpr/metrics/telemetry.db`.

## ✨ Qué Hace

Cada comando ejecutado añade una fila al registro con:

| Campo | Descripción |
|-------|-------------|
| `timestamp` | Cuándo terminó el comando (ISO 8601) |
| `command` | Qué comando se ejecutó (`commit`, `review`, `fullreview`, `linter`, `blame`, `hook:post-checkout`, etc.) |
| `status` | Resultado (`success`, `error`, `fired`, `no_changes`) |
| `provider` | Proveedor de IA que respondió (`gemini`, `deepseek`, `ollama`) |
| `model` | Modelo con el que respondió el proveedor |
| `prompt_tokens` / `completion_tokens` | Conteo de tokens informado por el proveedor |
| `tokens_actual` / `tokens_estimated` | El conteo que vale: medido cuando el proveedor lo informa, estimado en los demás casos |
| `duration_ms` | Duración del comando en milisegundos |
| `repo` | Repositorio como `dueño/nombre`, resuelto por el mismo parser multi-forja del resto de la CLI |
| `branch` | Nombre de la rama actual |
| `author_name` | Autor Git local de la ejecución |
| `modules` | Módulos que tocó el diff, normalizados a los dos primeros segmentos de la ruta (`src/fix`, `(root)` para un archivo en la raíz del repositorio) |
| `source` | `execution` para un comando que se ejecutó, `cache_backfill` para una fila reconstruida desde la caché de IA |

Las filas también llevan `cache_hit`, `map_reduce`, `chunks_count`,
`linter_errors` y `linter_warnings`, que tienen sentido para algunos comandos y
quedan a cero en el resto. `modules` queda **vacío** en los comandos que nunca
tuvieron un diff en mano — el linter, el motor de blame y los hooks registran
ejecuciones sin diff, y la sección de módulos las suma en `(sin módulo)`
en vez de hacerlas pasar por un módulo con nombre de nada.

## 📁 Dónde se Almacenan los Datos

```
~/.gitpr/metrics/
├── telemetry.db         ← el registro: una fila por comando ejecutado (SQLite)
└── .migration_declined  ← se escribe solo si rechazaste la importación

~/.gitpr/metrics_legacy/    ← los archivos de evento anteriores al registro, movidos aquí tras la importación
~/.gitpr/cache/prompts/     ← caché de respuestas de la IA, origen de una reconstrucción
```

Las exportaciones van al repositorio en el que ejecutas el comando, nunca a tu
directorio personal:

```
./.gitpr/metrics/export/
├── gitpr_metrics_2026-09-28.csv    ← CSV consolidado
├── gitpr_metrics_2026-09-28.json   ← JSON consolidado
└── gitpr_metrics_2026-09-28.db     ← bundle escrito por `gitpr metrics bundle`
```

El registro sustituyó a archivos JSON de evento nombrados
`{uuid}_{AAAAMMDD}.json` en `~/.gitpr/metrics/{dueño}/{branch}/`. Esos archivos se
importan una vez y se **mueven, nunca se eliminan** — terminan en
`~/.gitpr/metrics_legacy/`, fuera del directorio que cuenta el resumen.

## 🚀 Comandos CLI

### Mostrar Resumen

```bash
gitpr metrics
```

Cuenta filas, no archivos: la ruta del registro, cuántas ejecuciones contiene,
cuántas filas se reconstruyeron desde la caché y el tamaño en disco. Aparece un
aviso mientras haya archivos de evento anteriores al registro esperando
importación.

Bajo el encabezado vienen las secciones, en el orden en que se leen:

| Sección | Qué responde |
|---------|--------------|
| 💰 Coste | Cuántos tokens, y cuánto costaron por modelo |
| 🧪 Calidad | Tasa de aprobación del linter y con qué frecuencia se disparó el camino map-reduce |
| 🧩 Módulos | Qué módulos tocaron las ejecuciones, y cuántos tokens llevó cada uno |
| 🤖 Proveedores | Ejecuciones y tokens por proveedor — incluidos los que nunca llaman a una IA |
| ⏱ Ciclo | Cuánto tardaron las pull requests con merge de este repositorio, leídas de la forja |

Una sección sin nada que decir se omite en lugar de imprimirse vacía. El dashboard
dibuja estas mismas líneas desde el mismo renderizador, así que el terminal y la
TUI no pueden contar dos historias sobre un mismo registro.

### La Ventana

Una ventana, un significado — las mismas flags limitan el resumen, el dashboard,
la exportación, el bundle y la tool MCP:

```bash
gitpr metrics --days 30
gitpr metrics --since 2026-01-01 --until 2026-03-31
```

La ventana es **inclusiva en ambos extremos** y se aplica a la fecha a la que se
refiere la fila. Sin ninguna flag, las secciones del registro leen el registro
completo — excepto el ciclo, que pide su respuesta a la red y por eso asume los
últimos 30 días, diciéndolo en su propio encabezado en vez de estrechar en
silencio.

### Coste y Tarifas

La sección de coste convierte tokens en dinero con dos capas, la segunda
sobreponiéndose a la primera por modelo:

1. **Una tabla incorporada** con los precios de lista publicados por los
   proveedores para los IDs de modelo fijos que GitPR acompaña
   (`deepseek-v4-flash`, `deepseek-v4-pro`, `gemini-2.5-pro`,
   `gemini-2.5-flash-lite`), para que la sección diga algo en una máquina que
   nadie configuró.
2. **El entorno**, por modelo:

```ini
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT=0.435
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT=0.87
GITPR_METRICS_CURRENCY=USD
```

`<MODEL>` es el nombre del modelo en mayúsculas, con cada secuencia de caracteres
que no sea letra o dígito colapsada en un `_`. Las dos tarifas son obligatorias:
un modelo con solo una de ellas se reporta solo en tokens, porque tarifar la otra
mitad con un cero no configurado subestimaría la cuenta.

- **La moneda por defecto es USD**, que es la moneda en la que está cotizada la
  tabla incorporada. Configura tarifas en otra moneda y apunta
  `GITPR_METRICS_CURRENCY` a ella — la tabla incorporada entonces se aparta,
  porque una tarifa en dólares impresa bajo la etiqueta de otra moneda es un
  número equivocado, no un número ausente.
- **Proveedores que corren en esta máquina** (`ollama`, `local`) cuestan cero por
  definición y no necesitan tarifa.
- **Las tarifas cambian.** Convertir tokens gastados el año pasado al precio de
  hoy es una aproximación, y la sección lo dice en la línea bajo el total.
- **Un total que deja modelos fuera lo dice** — `Total (parcial)` — en vez de
  dejar que una suma de las filas tarifadas parezca la cuenta entera.

### La Métrica de Ciclo

La sección ⏱ es la única métrica de aquí que no viene del registro, y no puede
venir: el registro anota lo que GitPR ejecutó en esta máquina, mientras que una
pull request se fusiona en la forja, por personas que nunca ejecutaron GitPR. Por
eso esta necesita token y red, y es la única sección que puede volver sin nada por
un motivo que no es "no pasó nada".

Mide `created_at → merged_at` de las pull requests que la forja reporta con merge
en la ventana — **el ciclo de la propia pull request**, de la apertura al merge.
No es el tiempo desde el primer commit de una rama hasta su pull request: el
contrato de listado no lleva commits de rama, así que ese intervalo no está
disponible aquí, y tampoco se inventa desde el registro.

El encabezado nombra el repositorio y la ventana — `⏱ Ciclo · dueño/repo · últimos
30 días` — porque esta es la única sección cuyo alcance no es el del registro:
leída junto a un resumen que dice "Todos los repositorios", un número suelto
parecería cubrirlos todos.

Todo fallo degrada a una línea, nunca a un stack trace:

| Qué pasó | Qué muestra la sección |
|----------|------------------------|
| Sin remote origin, sin forja utilizable, sin token, sin red | `No leído: <el motivo>` |
| La forja no publica fecha de merge (Bitbucket) | Lo dice, sin gastar una llamada de red |
| La ventana no tiene ninguna pull request con merge | `Ningún pull request tuvo merge en esta ventana.` |

Un merge cuya fecha precede a su propia creación es un reloj que la forja erró, no
un ciclo negativo: esa fila se descarta en vez de entrar en la media.

### Exportar Datos

```bash
gitpr metrics export
```

Escribe en CSV y JSON las filas que nunca se exportaron, en
`./.gitpr/metrics/export/`, y luego las marca como exportadas — por eso una
segunda ejecución responde "Ninguna métrica nueva para exportar." en vez de
repetirse. La exportación abarca el repositorio de la copia de trabajo.

- **Columnas CSV:** timestamp, day, command, status, provider, model,
  prompt_tokens, completion_tokens, tokens_actual, tokens_estimated, duration_ms,
  repo, branch, author_name, modules, cache_hit, map_reduce, linter_errors,
  linter_warnings, chunks_count, source
- **JSON:** las mismas filas como objetos, listas para que las lea un script

### Bundle y Merge (Consolidación de Equipo)

`export` es lo que lee una persona; un **bundle** es lo que lee otra máquina — la
misma porción del registro como un archivo `.db` autónomo:

```bash
gitpr metrics bundle --days 30
gitpr metrics bundle --since 2026-07-01 --until 2026-09-30 -o ./entrega/
gitpr metrics merge ./entrega/gitpr_metrics_2026-09-29.db ./entrega/otro.db
```

`bundle` copia las filas de la ventana a un archivo SQLite independiente, con
esquema y `PRAGMA user_version` incluidos, y escribe en `./.gitpr/metrics/export/`
salvo que `-o` diga otra cosa. `merge` adjunta cada bundle e inserta las filas que
aún no tiene — el UUID es la clave primaria, así que fusionar el mismo archivo dos
veces, o dos bundles solapados, nunca cuenta una ejecución dos veces.

Las versiones de esquema se tratan en **una sola dirección**: un bundle más
antiguo se migra hacia arriba al adjuntarse, y uno más nuevo se rechaza *antes* de
cualquier escritura, con la versión que trae y la que este GitPR entiende — el
registro local nunca queda a medio importar. Actualiza GitPR para leer un bundle
más nuevo.

Esta es la respuesta a "cuánto gastó el equipo en el trimestre" sin servidor: cada
máquina empaqueta su ventana, y quien necesita el total fusiona los archivos en un
registro propio.

### Importar Datos Anteriores al Registro

```bash
gitpr metrics migrate
```

Lee los archivos de evento escritos antes de que el registro existiera, los
inserta y mueve los originales a `~/.gitpr/metrics_legacy/`. Con un terminal, abre
un asistente que también ofrece reconstruir el historial desde la caché de
respuestas de la IA. Esas filas se marcan con `source: cache_backfill` porque la
caché indexa una respuesta por su prompt y, por tanto, cuenta **prompts
distintos, no ejecuciones**.

### Eliminar Registros Antiguos

```bash
gitpr metrics prune --before 2026-01-01
```

Elimina las filas escritas antes de una fecha, tras confirmación, y recupera el
espacio con `VACUUM`. `--source cache_backfill` restringe la eliminación a las
filas reconstruidas. **No existe expiración automática**: el registro responde
"cuánto gastamos este año", y un calendario que elimina solo cambiaría esa
respuesta sin que nadie lo pida.

### Limpiar Datos

```bash
gitpr metrics purge
```

El camino destructivo: elimina todas las filas y todos los archivos de evento que
aún esperan importación, tras confirmación.

### Dashboard Interactivo

```bash
gitpr metrics dashboard
```

Abre un **dashboard TUI** (Textual) limitado al repositorio de la copia de
trabajo:

- **Barra de resumen:** total de entradas, filas reconstruidas, total de tokens, duración total, top comandos
- **Tabla de eventos:** timestamp, comando, estado, proveedor, tokens, duración
- **Secciones:** coste, calidad, módulos, proveedores y el ciclo — las mismas líneas
  que `gitpr metrics` imprime, dibujadas con markup de Textual en vez de los colores
  de click
- **Barra de estado:** el intervalo de tiempo que cubre la tabla y cuántas entradas tiene
- **Atajos:** `F5` para actualizar, `Esc` para salir

Mientras el registro aún no exista, el dashboard lee la caché y los archivos de
evento, muestra una barra de progreso durante el escaneo y lo indica en la barra
de estado.

La sección de ciclo se dibuja de todos modos: nunca leyó el registro.

## 🔧 Git Hooks (Recolección Automática)

Cuando se instalan mediante `gitpr --installhooks`, tres hooks adicionales
recolectan telemetría de comportamiento:

| Hook | Evento capturado |
|------|-----------------|
| `post-checkout` | Cambios de rama (cambios de contexto) — se dispara solo cuando la rama cambió de verdad |
| `pre-push` | Eventos de push (frecuencia de entrega) |
| `post-merge` | Eventos de pull/merge (frecuencia de integración) |

Los tres ejecutan `gitpr --quiet metrics hook-event <nombre>`, una acción oculta
cuya única tarea es escribir una fila y salir. El repositorio lo resuelve el
propio hook, con el mismo parser que usa el resto de la CLI, así que GitLab,
Bitbucket y Azure DevOps registran el mismo `dueño/nombre` que GitHub. Una guarda
alrededor de la llamada — `command -v gitpr`, más un `|| true` al final — impide
que una máquina sin GitPR, o con un GitPR que falla, rompa tu comando Git.

## 📊 Casos de Uso

- **Tech Lead:** Ver qué repositorios, ramas y autores usan realmente las revisiones de IA, y qué hooks se disparan
- **Finanzas:** Leer la sección de coste para la cuenta por modelo, o `gitpr metrics --since 2026-07-01` para el trimestre
- **Calidad:** Leer `linter_errors`, `linter_warnings` y `modules` para encontrar qué parte del proyecto genera más hallazgos
- **Proceso:** Observar `map_reduce` y `chunks_count` — PRs grandes disparando el camino map-reduce apuntan a un problema de proceso
- **Entrega:** Leer la sección de ciclo para ver cuánto tardaron las pull requests con merge de este repositorio, y cuáles tardaron más

## 🔒 Privacidad

- **100% local** — el registro es un archivo en tu máquina; nada de él se envía a servidores externos
- **La única excepción es la sección de ciclo** — pide a la forja configurada las pull requests con merge del repositorio en el que estás. No envía ninguna fila del registro, ningún recuento de tokens y ningún diff: la pregunta es "qué pull requests tuvieron merge en esta ventana", y la respuesta es de solo lectura
- **No es anónimo** — cada fila lleva el repositorio, la rama y el nombre del autor Git local. No lleva contenido de archivos ni diffs: `modules` guarda los segmentos de ruta que tocó una ejecución, nunca los nombres de los archivos, y el correo del autor se queda en la caché de IA
- **Control del usuario** — `prune` y `purge` son manuales y confirmados; nada expira solo
- **Hooks opcionales** — los git hooks solo se instalan si ejecutas `gitpr --installhooks`

## 📚 Documentación Relacionada

- [Integración MCP](mcp-integration.md) — Configuración del servidor MCP
- [MCP Prompts](mcp-prompts.md) — Plantillas de mensaje predefinidas
- [MCP Tool Annotations](mcp-annotations.md) — Sugerencias de integración con IDEs

---
**Consejo profesional:** Las exportaciones quedan en `./.gitpr/metrics/export/`,
dentro del repositorio en el que estás — ese directorio pertenece a tu máquina,
no al proyecto, y es lo que la entrada del `.gitignore` del propio GitPR mantiene
fuera del árbol. Para responder "cuánto gastó esta máquina este trimestre" sin
hoja de cálculo, pregúntale al registro: `gitpr metrics --since 2026-07-01`.
