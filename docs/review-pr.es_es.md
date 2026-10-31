# Documentación Técnica: Revisión de Pull Request Remoto (gitpr review-pr)

`gitpr review-pr <number>` revisa un pull request que ya está abierto en la forge, obteniendo su diff directamente desde la API. La rama en revisión no necesita existir en tu máquina — nunca haces checkout de ella, nunca haces fetch y nunca tocas tu árbol de trabajo. Es el modo pensado para el revisor invitado al pull request de otra persona, donde el código a leer reside en el otro lado de la red.

La revisión en sí no es un segundo motor: es `gitpr -r` con el diff proveniente de otro lugar. La misma llamada a la IA, la misma skill `.gitpr.review.md`, las mismas reglas de linter, el mismo archivo de informe y la misma caché — razón por la cual una revisión remota y una revisión local del mismo diff se interpretan de forma idéntica.

---

## 1. Descripción General

El subcomando es una adición a la CLI, no una modificación: todas las opciones heredadas conservan su significado y los flujos locales (`gitpr -r`, `gitpr -f`, `gitpr fix`) no se ven afectados. La lectura es el comportamiento por defecto — sin ninguna opción, la forge solo se *lee*, y nada se publica en ningún sitio.

### 1.1 Referencia de Comandos — `gitpr review-pr`

Todas las opciones del subcomando, tal como las muestra `gitpr review-pr -h` (o `--help`):

```bash
gitpr review-pr 123                    # revisar el pull request y guardar el .txt
gitpr review-pr 123 --provider deepseek  # revisar con un motor de IA específico
gitpr review-pr 123 --post-comment     # publicar también la revisión en el pull request
```

| Opción | Descripción |
| --- | --- |
| **`<number>`** | El número del pull request tal como se muestra en la forge (`123`). Obligatorio y entero — un argumento no numérico es un error de uso |
| **`--provider <name>`** | Fuerza el motor de IA para esta ejecución (`gemini`, `deepseek` u `ollama`). Sin ella, se utiliza el valor por defecto configurado |
| **`--post-comment`** | Publica la revisión como comentario en el pull request. **Sin esta opción, la forge nunca se modifica** |

| Característica | Descripción |
| --- | --- |
| **Origen de los datos** | El diff servido por la API de la forge para ese pull request — nunca tu árbol de trabajo |
| **Forge** | La configurada mediante `gitpr --init` (GitHub, GitLab, Bitbucket). Azure DevOps es rechazado — ver §3 |
| **Llamada de IA** | Una llamada, en el modelo avanzado del proveedor configurado, en caché bajo `review/` como cualquier otra llamada de GitPR |
| **Archivos guardados** | `{branch}_{datetime}_PR_REVIEW.txt` en la carpeta de informes (`OUTPUT_FILE_NAME_REVIEW`) |
| **Publicación** | Ninguna, a menos que se indique `--post-comment` |
| **Árbol local** | Nunca se lee, nunca se comprueban archivos sin stage y nunca se modifica — sin checkout, sin fetch, sin cambio de rama |
| **Código de salida 1** | Ninguna forge configurada, forge sin diff revisable, pull request inexistente o cerrado, diff vacío o totalmente filtrado, API inalcanzable, clave de IA ausente |

---

## 2. Qué Es una Revisión Remota

### 2.1 El Diff Proviene de la API

A la forge se le solicitan primero los metadatos del pull request y posteriormente su diff:

| Paso | Qué establece |
| --- | --- |
| `get_pull_request` | Que el número existe, en qué estado se encuentra y qué ramas une |
| `get_pull_request_diff` | El diff unificado a revisar |

Resolver el número directamente permite distinguir "no existe" de "se fusionó la semana pasada": listar pull requests abiertos devuelve únicamente los abiertos, por lo que un número ausente podría significar cualquiera de los dos casos. Los metadatos también proporcionan las dos ramas que el informe necesita nombrar.

La solicitud de metadatos no es meramente decorativa — es lo que evita que un número obsoleto consuma tokens innecesariamente (§4.2).

### 2.2 El Diff Se Normaliza

Un diff que nunca pasó por git llega en la forma exacta en que la forge decidió enviarlo. Se realizan tres acciones antes de que la IA lo reciba:

| Paso | Motivo |
| --- | --- |
| **Finales de línea unificados a LF** | GitLab y Bitbucket entregan CRLF en ramas originadas en Windows, y el divisor fragmenta en `^diff --git a/`, lo cual fallaría con un `\r` residual |
| **El contenido se valida como diff real** | Un proveedor que afirme servir diffs pero responda con texto plano se detiene aquí, evitando ser analizado como si fuera código |
| **Aplicación de smart excludes** | Los lockfiles y recursos minificados se filtran del diff *revisado*, no de un diff local (§2.3) |

### 2.3 Smart Excludes en Ejecución Python

Cada diff local recibe sus exclusiones inteligentes aplicadas directamente por git mediante pathspecs `:(exclude)`. Un diff que llega por la API nunca pasa por git, por lo que los mismos patrones se aplican en Python, sección por sección de archivo, advirtiendo de los archivos omitidos:

```text
⚠️  3 file(s) skipped by the smart excludes: package-lock.json, poetry.lock, dist/app.min.js
```

La lista de patrones es idéntica a la que utilizan los flujos locales (`~/.gitpr/conf/gitpr.smart-excludes.json`), y `GITPR_SKIP_SMART_EXCLUDES` la desactiva aquí también. Un pull request cuyos archivos sean exclusivamente lockfiles no tiene nada que revisar, y así lo notifica en lugar de enviar un diff vacío al modelo.

### 2.4 Aislamiento en Caché Distinto de la Revisión Local

La clave MD5 de la caché se genera a partir del prompt, y el prompt se construye a partir del diff. Por tanto, una revisión remota de una rama que casualmente estuviera en checkout local produciría un prompt idéntico en bytes y sería respondida por la revisión local en caché. El flujo remoto añade un identificador de ámbito a la clave de caché:

```text
::diff-source::pr-123
```

El ámbito se añade **únicamente** a la clave de caché — nunca al texto enviado a la IA. La consecuencia para una instalación existente es nula: los flujos locales pasan un ámbito vacío, por lo que sus claves permanecen idénticas byte a byte a las de siempre, sin invalidar ninguna entrada de caché previa.

### 2.5 El Diff Revisado Queda Registrado

La revisión se almacena en la caché junto con el diff del que proviene, lo que permite a `gitpr fix` aplicar parches sobre la revisión exacta que fue analizada en lugar de reconstruir un diff a partir de tu árbol. Para una revisión remota, esto no es solo una comodidad sino la única fuente correcta: la rama puede no existir en absoluto a nivel local. Consulta la [documentación del Comando Fix](https://gitpr.natanfiuza.dev.br/docs/fix-command?lang=es) para ver cómo se consume.

El registro se guarda bajo el repositorio y la rama **en la que te encuentras** — los mismos campos que acompaña cada revisión en caché, ya que es lo que `gitpr fix` resuelve para encontrarla. Las ramas del propio pull request se registran dentro de la entrada (como el `{branch}` del nombre del informe y en el origen del diff), pero no sirven de clave de búsqueda: revisar el PR #123 mientras estás en `develop` archiva la revisión bajo `develop`.

---

## 3. Forges Compatibles con Revisión

Una revisión necesita un diff unificado, y no todas las forges lo proporcionan.

| Forge | Revisión Remota | Motivo |
| --- | --- | --- |
| **GitHub** | Sí | `GET /repos/{owner}/{repo}/pulls/{n}/files` con cabecera `Accept: application/vnd.github.diff` |
| **GitLab** | Sí | `changes[].diff` por archivo, con cabeceras de archivo sintetizadas (§3.1) |
| **Bitbucket** | Sí | `GET .../pullrequests/{n}/diff` |
| **Azure DevOps** | **No** | Su API devuelve una lista de archivos modificados con recuento de líneas, no un diff unificado. Se rechaza antes de cualquier llamada de red, con un mensaje que remite a la revisión local |

La capacidad es declarada por el propio proveedor (`supports_reviewable_diff` en `ScmProvider`), de forma que una forge añadida posteriormente define su compatibilidad de manera explícita. Detrás de ese indicador opera una segunda validación: el contenido descargado se comprueba para verificar estructura real de diff, detectando proveedores que declaren soporte pero respondan con un resumen de archivos (§2.2).

### 3.1 GitLab: Síntesis de Cabeceras de Archivo

La API de GitLab devuelve el campo `diff` de cada archivo modificado como un bloque aislado, con la identidad del archivo en campos separados `old_path` / `new_path`. Leído sin procesar, la revisión recibiría bloques anónimos — la IA no sabría a qué archivo corresponde un cambio, e imposibilitaría tanto el filtro de smart excludes como el procesado por lotes, ya que ambos dependen de la línea `diff --git a/…`. El proveedor reconstruye dicha cabecera antes de cada bloque:

```diff
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,2 @@
```

GitLab también notifica cuando trunca un diff por exceder el límite de tamaño de la API (`overflow: true`). Un diff truncado no es un diff completo y se rechaza de inmediato con un mensaje que indica al revisor analizar ese merge request localmente, evitando que se revise a medias y se publique un resultado parcial como si fuera íntegro.

---

## 4. El Informe, Advertencias y Fallos

### 4.1 El Informe

La salida es el mismo archivo que genera la revisión local, mediante el mismo código de formateo — bloque de linter arriba, revisión de IA debajo — con una diferencia en el nombre: el marcador `{branch}` contiene la rama de **origen** del pull request, normalizada para el sistema de archivos (`feature/login` pasa a ser `feature-login`), ya que el informe pertenece a la revisión analizada y no a la rama que tengas activa. Un pull request sin rama nombrada utiliza `pr-123`.

```text
✅ Code Review successfully generated: 'feature-login_20260917143210_PR_REVIEW.txt'
```

No se imprime nada más: la revisión nunca se muestra en la terminal, exactamente igual que en los flujos locales. La ruta del informe se configura mediante `OUTPUT_FILE_NAME_REVIEW`, la misma variable que usa la revisión local — el modo remoto no introduce nuevas configuraciones.

### 4.2 Rechazos Sin Coste de Tokens

Todo lo que el usuario puede solucionar se rechaza **antes** de llamar a la IA, garantizando que un número erróneo, un pull request cerrado o una forge con un token inválido no gasten tokens:

| Situación | Mensaje |
| --- | --- |
| La forge no entrega un diff revisable | `{provider} does not serve a reviewable diff: … Review this pull request locally, or use a forge that serves diffs.` |
| El número no existe | `Pull request #123 was not found in {repo}.` |
| El token no tiene permisos de lectura (401/403) | `No permission to read pull request #123 in {repo}. Check the token configured for {provider} (gitpr --init).` |
| Está cerrado o fusionado | `Pull request #123 is not open (state: closed). Only open pull requests can be reviewed.` |
| El diff volvió vacío | `Pull request #123 has no diff to review.` |
| Volvió como resumen de archivos | `{provider} returned a file summary instead of a diff for pull request #123. It cannot be reviewed.` |
| Todos los archivos coincidieron con smart excludes | `Every file of pull request #123 matches the smart excludes — nothing left to review.` |
| El modelo no devolvió nada utilizable | `The AI returned no review for pull request #123.` |

Los cuatro estados de apertura entre las forges soportadas — GitHub `open`, GitLab `opened`, Azure `active`, Bitbucket `OPEN` — se comparan ignorando mayúsculas y minúsculas. Un proveedor que no reporte estado se acepta, evitando bloqueos por propiedades no garantizadas.

### 4.3 Advertencias

Las advertencias notifican situaciones relevantes que no impidieron la ejecución. Se imprimen antes del informe y, al usar `--post-comment`, se incluyen dentro del comentario — quien lea el pull request tiene derecho a saber si la revisión omitió lockfiles.

| Advertencia | Cuándo ocurre |
| --- | --- |
| `{count} file(s) skipped by the smart excludes: {files}` | El filtro descartó al menos un archivo |
| `Large diff: processed in {count} batches (map-reduce).` | El diff es lo bastante grande como para que el motor lo divida |

El recuento de lotes se solicita al procesador de fragmentación en lugar de extraerse de la terminal, garantizando compatibilidad con herramientas MCP. Si el procesador no devuelve el dato, la ejecución continúa con normalidad: la advertencia es informativa y nunca causa la caída del comando.

### 4.4 Una Ejecución Fallida No Escribe Archivos

Cualquier fallo finaliza con código de salida 1, muestra el motivo en stderr y **no escribe ningún informe** — la presencia de un `.txt` en disco garantiza que existe una revisión válida, impidiendo que un fallo se confunda con una revisión limpia. El comando tampoco reintenta: las excepciones se lanzan antes del motor de IA, evitando cobros secundarios.

---

## 5. Publicación — `--post-comment`

Con `--post-comment`, la revisión se publica como comentario en el propio pull request. Es un comentario único, creado tras completarse con éxito la revisión y ejecutarse el linter, y es **siempre un comentario nuevo** — revisiones previas realizadas por la herramienta permanecen intactas, evitando sobrescribir comentarios a los que alguien haya respondido.

El cuerpo contiene el informe junto con un pie de página:

```markdown
## 🚨 Local Static Analysis Alerts (YAML Rules)

- 🚨 console.log usage detected in app.js (Line 42)

---

## 🤖 AI Code Review

…

---

*Automated review by GitPR 1.1.0 — AI provider: Gemini. AI-generated content: verify before acting on it.*
```

El pie de página garantiza la transparencia en el pull request de **otra persona**: un lector que no ejecutó la CLI dispone de una indicación clara de que el texto proviene de un modelo. Las alertas se componen mediante la misma función exacta que genera el `.txt`, asegurando total coherencia entre el archivo y el comentario.

No aparece ningún SHA de commit. La forge no lo incluye en el diff entregado, e inventar uno en un comentario público sería menos fiable que omitirlo.

Si la revisión falla, no se publica nada — el comentario solo existe tras una revisión que produjo contenido. Si falla la publicación del comentario (por ejemplo, un token que lee pero no escribe), el error se reporta como fallo de forge y el proceso finaliza con código 1: la revisión se generó, pero no pudo publicarse.

---

## 6. Plantilla de Skill — `.gitpr.review.md`

La revisión remota utiliza la misma instrucción de sistema que la local: `.gitpr.review.md` (rol y enfoque de la revisión), descargada mediante `gitpr --skill` — adaptada al idioma activo y sin sobrescribir archivos preexistentes. No existe un tipo de skill exclusivo para remoto; que la revisión analizara de forma distinta según el origen del diff invalidaría el propósito de compartir el mismo motor.

---

## 7. Integración MCP

`review_remote_pr` es la 14ª herramienta MCP y opera en modo de **solo lectura**: revisa un pull request abierto y devuelve la revisión y las alertas del linter, sin capacidad de publicación. Carece intencionadamente del argumento `post_comment` — una herramienta que un agente invoca de forma autónoma no debe poder escribir directamente en el pull request de nadie.

```json
{"status": "success", "pr_number": 123, "pr_url": "…", "head_branch": "feature/login",
 "base_branch": "main", "origin": "remote_pr", "linter": {…}, "warnings": [], "review": "…"}
```

A diferencia de la CLI, no escribe ningún archivo `.txt` — las herramientas MCP no generan artefactos en disco — y resuelve la forge por sí misma, respondiendo en repositorios sin forge con un error JSON que sugiere `gitpr --init` en vez de mensajes de terminal. El estado devuelto es `error` con su correspondiente `message` para cada caso detallado en §4.2. Consulta la [documentación de Integración MCP](https://gitpr.natanfiuza.dev.br/docs/mcp-integration?lang=es).

---

## 8. Variables de Entorno

La revisión remota **no introduce ninguna configuración nueva**. Emplea las mismas variables que la revisión local:

| Variable | Propósito |
| --- | --- |
| `GITPR_SCM_PROVIDER` / `GITPR_SCM_TOKEN` / `GITPR_SCM_TOKEN_ENCRYPTED` | La forge y su token, configurados mediante `gitpr --init` |
| `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` | Ajustes adicionales de forge (GitLab autoalojado, Azure, Bitbucket) |
| `OUTPUT_FILE_NAME_REVIEW` | Nombre del informe (por defecto `{branch}_{datetime}_PR_REVIEW.txt`) |
| `DEFAULT_AI_PROVIDER` | Motor de IA utilizado cuando no se pasa `--provider` |
| `GITPR_SKIP_SMART_EXCLUDES` | Desactiva el filtro de smart excludes, local o remoto |

> **Nota:** Consulta también la [documentación de Code Review con IA](https://gitpr.natanfiuza.dev.br/docs/code-review-ia?lang=es) para conocer los modos de revisión y la [documentación del Comando Fix](https://gitpr.natanfiuza.dev.br/docs/fix-command?lang=es) para entender cómo se aprovecha el diff registrado.
