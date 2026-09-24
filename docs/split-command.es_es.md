# Documentación Técnica: Comando Split (gitpr split)

`gitpr split` lee un árbol de trabajo que contiene varios propósitos o tareas sin relación entre sí, agrupa los hunks por intención lógica mediante IA y propone un commit atómico por cada propósito — cada uno con un mensaje generado exclusivamente para ese subconjunto de cambios. La lectura es el comportamiento por defecto y la escritura es opt-in: sin argumentos el comando muestra el plan y ofrece aplicarlo, `--dry-run` imprime y se detiene sin preguntar nunca, y `--apply` solicita confirmación una sola vez, prepara en el índice (*staging*) y crea los commits grupo por grupo.

El problema que resuelve es el que todo desarrollador reconoce: la corrección de un bug, una refactorización y un ajuste de configuración que surgieron en la misma tarde, ahora inseparables en un único `git diff`, donde las únicas salidas son `git add -p` manual o un mensaje de commit que enumera tres cosas sin relación.

---

## 1. Descripción General

El subcomando es una adición a la CLI, no una alteración de su comportamiento base: todas las opciones heredadas conservan su significado y todo el flujo es local — no se crea ningún `git commit` hasta que se confirme `--apply`, nada se envía al remoto y no se crea ninguna rama.

### 1.1 Referencia del Comando — `gitpr split`

Todas las opciones del subcomando, tal como las muestra `gitpr split -h` (o `--help`):

```bash
gitpr split                    # imprime el plan y luego ofrece aplicarlo
gitpr split --dry-run          # imprime el plan y se detiene — nunca pregunta
gitpr split --apply            # imprime el plan, confirma una vez, pasa a stage y commitea
gitpr split --apply --yes      # lo mismo, sin el diálogo de confirmación
gitpr split --max-groups 3     # como máximo tres commits atómicos
```

| Opción | Descripción |
| --- | --- |
| **`--dry-run`** | Imprime el plan y se detiene. Nunca pregunta, nunca toca el índice ni el árbol de trabajo, bajo ningún estado del índice |
| **`--apply`** | Ejecuta el plan: preparación seletiva en el índice (*staging*) y un commit por grupo, en orden |
| **`--yes`** | Omite el mensaje de confirmación. Nunca elude el `--check` de cada grupo |
| **`--max-groups <n>`** | Límite superior de commits que el plan puede proponer, sobreescribiendo la configuración |
| **`--provider <name>`** | Fuerza el proveedor de IA para esta ejecución (`gemini`, `deepseek`, `ollama`) |

| Característica | Descripción |
| --- | --- |
| **Fuente de datos** | Los cambios no commiteados del árbol de trabajo — en stage (*staged*), fuera de stage (*unstaged*) o ambos a la vez, como un único diff frente a HEAD |
| **Llamadas de IA** | Una llamada para agrupar los hunks, más una llamada por grupo para redactar su mensaje de commit |
| **Archivos escritos** | Ninguno por defecto. `--apply` escribe en el índice de Git y crea commits; el árbol de trabajo nunca se modifica |
| **Índice** | Se deja limpio antes de la ejecución. `--apply` pide permiso una vez para sacar todo del stage |
| **Deshacer** | Ninguno integrado. El resultado son commits estándar — `git reset`/`git reflog` son las herramientas adecuadas |
| **Código de salida 1** | No es un repositorio Git, `--dry-run` combinado con `--apply`, árbol de trabajo vacío, falta de API key o proveedor inalcanzable, repositorio sin commits previos sobre los que construir, o plan sin grupos |

### 1.1.1 Cuándo Pregunta el Comando

`--apply` declara una intención explícita, por lo que `GITPR_SPLIT_REQUIRE_CONFIRMATION=false` puede legítimamente omitir la pregunta. No pasar ningún flag no declara intención alguna, por lo que en ese modo la pregunta **es** la esencia del comando y siempre se formula — un `gitpr split` simple no debe commitear por su cuenta solo porque un valor de configuración indique que las confirmaciones están desactivadas. `--yes` es el usuario indicándolo de forma explícita, y omite la pregunta en ambos modos.

### 1.2 Qué Significa "Atómico" Aquí

Un commit atómico es un commit que contiene todos los cambios que requiere un propósito y ningún cambio correspondiente a otro. La unidad de división es el **hunk** — un bloque `@@` de un archivo — y nunca una fracción menor: dividir un único hunk en fragmentos menores está fuera de alcance, al igual que dividir un pull request que ya ha sido publicado en la forja.

La unidad es el hunk y no el archivo porque el caso crítico a resolver es precisamente aquel en el que un solo archivo alberga dos propósitos distintos. Un archivo cuyos hunks pertenecen todos al mismo propósito no es un caso especial: es la misma maquinaria llegando a la conclusión evidente.

### 1.3 Fuera de Alcance

- Archivos no rastreados por Git (*untracked*). No contienen hunks y `git diff HEAD` no los describe, por lo que no forman parte de ningún plan. Se indican en una advertencia y nunca se ignoran en silencio.
- Subdividir un hunk internamente.
- Deshacer una división de forma automática. El resultado son commits convencionales y Git estándar los revierte; no se construyó un rollback dedicado, a diferencia de `gitpr fix`, donde un parche aplicado no tiene commit previo al que resetear.
- Reordenar, fusionar y desmarcar grupos de forma interactiva. Planificado para una versión posterior.

---

## 2. Captura del Diff

### 2.1 Captura de Diff Propia y Justificación

Split no utiliza `get_git_diff()`, el diff que leen todos los demás flujos:

```python
SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")
```

La diferencia fundamental es `-w`, que otros flujos utilizan y que split no debe emplear. Con `-w`, una diferencia que consiste *únicamente* en espacios en blanco se formatea como contexto — y la línea de contexto emitida puede no coincidir byte a byte con el archivo real. Un parche construido a partir de dicho diff sería rechazado por `git apply` o, peor aún, aplicaría contenido que difiere del árbol de trabajo. Eso rompería la garantía sobre la que se fundamenta este comando: los archivos en disco al final son byte a byte idénticos a los archivos en disco al inicio.

`-U1` también se descarta: una sola línea de contexto deja muy poco margen para que `git apply --check` ancle un hunk. `-B`, que descompone reescrituras en eliminación más adición, se descarta por la misma razón por la que resulta inconveniente aquí: transforma un hunk aplicable en dos que tendrían que aplicarse obligatoriamente de forma sincronizada.

`-M` se **conserva**, y es estructural. Sin detección de renombramientos, un renombre llega como una eliminación más una adición, y la adición se convierte en un archivo no rastreado — fuera de alcance. Split commitearía entonces una eliminación limpia de la ruta anterior mientras el nuevo archivo quedaría sin rastreo a su lado, lo que equivale a una pérdida de datos.

`--binary` no altera el texto plano y es lo único que permite aplicar un archivo binario modificado.

### 2.2 Sin Exclusiones Inteligentes (*Smart Excludes*)

Los flujos de revisión habituales descartan lockfiles, archivos generados y binarios antes de enviar un diff a la IA. Split no descarta absolutamente nada.

La razón es que la exclusión no es inocua en este caso, es *incorrecta*. Un lockfile y su manifiesto describen un único cambio conjunto; excluir el lockfile commitea el manifiesto en solitario y deja un árbol en el que ambos difieren — un commit intermedio roto, que es exactamente lo que este comando existe para evitar. El ruido se mitiga, en su lugar, truncando cada unidad en el prompt y limitando cuántas unidades se envían en total.

### 2.3 Capturar Primero, Sacar del Stage al Final

`--apply` necesita un índice limpio contra el que preparar los cambios de forma selectiva, y el índice puede contener ya trabajo previo: un archivo nuevo en stage, un renombre en stage. Ese estado no es un accidente que deba limpiarse antes de leer el diff — es precisamente lo que hace que esos cambios sean *visibles*. Un archivo nuevo solo aparece en `git diff HEAD` porque el índice lo rastrea; sacarlo del stage previamente lo convierte en no rastreado, fuera de alcance, y desaparecería del plan.

Por tanto, el orden es estricto: el diff se captura contra el estado existente del índice, y todo se retira del stage inmediatamente antes del primer `git apply --cached`. Esto es sólido porque cada hunk en un `git diff HEAD` incluye una preimagen tomada de HEAD, independientemente de lo que contenga el índice. Tras retirar todo del stage, el índice coincide con HEAD, permitiendo que esas mismas preimágenes se apliquen de forma limpia. No hay re-cálculo de diff, no hay aborto por divergencia y ningún plan se altera en silencio entre su presentación y su aplicación.

### 2.4 Archivos No Rastreados (*Untracked*)

Están fuera de alcance y se reportan debidamente: el plan incluye una advertencia nombrándolos. "No hay nada que hacer aquí" y "había algo aquí y lo he omitido" nunca deben parecer la misma cosa.

---

## 3. El Plan

### 3.1 Unidades

Una unidad corresponde a una de dos cosas, y la diferencia es crucial a lo largo de todo el proceso:

| Unidad | Qué es |
| --- | --- |
| **`Hunk`** | Un bloque `@@` de un archivo, con su contenido literal, el encabezado de archivo precedente, las líneas de inicio y conteo de ambos lados, y su posición en el recorrido original |
| **`OpaqueSection`** | Una sección del diff que carece de hunks — un cambio binario, un renombre puro, un cambio de permisos/modo, la creación de un archivo vacío — preservada íntegra y de forma literal |

Las secciones opacas nunca se envían a la IA. No hay decisión de agrupamiento que solicitarle, y una unidad sobre la que el modelo no puede razonar es una unidad para la que inventaría un identificador arbitrario. Cada una se convierte en su propio grupo de una sola unidad: un commit atómico de un cambio indivisible.

El encabezado de archivo se **almacena, nunca se reconstruye**. `new file mode`, `deleted file mode`, `old mode`/`new mode` y la forma entrecomillada de Git para rutas con espacios o caracteres no ASCII son irrecuperables a partir de una ruta simple, e intentar sintetizarlos produce un parche que Git rechaza.

### 3.2 Los Límites de Hunk se Determinan Contando

Un hunk finaliza estrictamente cuando los conteos de su encabezado se agotan — nunca en el siguiente `@@`. Dentro de un hunk, una línea eliminada que comienza por `--- algo` y una línea agregada que comienza por `+++ algo` se ubican en la columna 0 y serían indistinguibles de un par de encabezados de archivo, mientras que una línea de contexto siempre lleva su espacio inicial. Contar es la única regla correcta.

El conteo actúa también como validador de entradas malformadas. Una sección cuyos conteos no cuadran con su cuerpo se degrada **por completo** a una `OpaqueSection`: nunca a una lista parcial de hunks, ya que la mitad de una sección ilegible no debe entregarse a `git apply`, y un parche que aplica la mayor parte de un archivo es peor que uno que lo rechaza.

### 3.3 Identidad de la Unidad

El identificador de una unidad es `0007-1a2b3c4d` — la posición en el recorrido, seguida de los primeros ocho dígitos hexadecimales de un MD5 sobre la ruta del archivo, el encabezado del hunk y el cuerpo.

Ambas partes son determinantes. La posición depende únicamente del orden de recorrido fijado por el texto del diff, asegurando que el mismo árbol de trabajo siempre produce los mismos identificadores y que un `--dry-run` repetido imprime exactamente lo mismo. El hash es lo que distingue dos archivos modificados de *forma idéntica* — una copia vendorizada y su original producen el mismo encabezado y cuerpo, diferenciándose solo en su ruta.

### 3.4 Agrupamiento

El agrupamiento consiste en **una sola llamada de IA, sin fragmentación por lotes**. Los lotes (*batching*) son la forma evidente de abarcar un diff demasiado grande para un prompt, pero resultan incorrectos para esta tarea: hunks de un mismo propósito que caigan en lados opuestos de un límite de lote jamás podrían reunirse, pues ningún lote ve los hunks del otro. El modelo respondería con seguridad sobre la mitad visible. Split prefiere degradar de manera transparente — las unidades que no caben quedan sin grupo y sin commitear — antes que producir un plan engañosamente completo.

Cada id que el modelo devuelve se valida contra las unidades efectivamente enviadas. Los ids desconocidos se descartan con una advertencia; los duplicados se conservan una sola vez; las unidades que el modelo no mencionó pasan a ser unidades sin grupo. Ninguna unidad inventada entra en un grupo y ninguna unidad real se descarta en silencio.

Cuando existen más unidades que las permitidas por `GITPR_SPLIT_MAX_HUNKS`, se conservan las más grandes y el resto pasa a la lista sin grupo con un aviso indicando sus ids. Se priorizan las mayores antes que los primeros N archivos: recortar por orden de archivos dejaría sistemáticamente sin procesar los últimos archivos del diff.

### 3.5 Prevalidación de Conflictos

Antes de mostrar el plan, cada grupo se valida con `git apply --cached --check` frente a un índice limpio. Un grupo que falla ve fusionadas en él todas las unidades de todos los archivos que toca — procedentes de cualquier grupo y de la lista sin grupo —, y su mensaje de commit se regenera para el parche combinado, ya que un mensaje que describe un subgrupo no reflejaría la realidad del commit consolidado.

El bucle está acotado y siempre termina. Si al forzar archivos completos la aplicación sigue fallando (por ejemplo, archivos con finales de línea CRLF o unidades binarias), esas unidades se trasladan a `ungrouped_units` con una advertencia. Nada se descarta y nada se aplica a medias.

Un conflicto a partir de un diff real con `-U3` es más infrecuente de lo que parece. Git fusiona cualquier par de cambios a menos de siete líneas de distancia en un solo hunk, dejando tres líneas de contexto intacto entre los hunks que emite, por lo que cualquier subconjunto se aplica limpiamente en un índice situado en HEAD. Las dos únicas causas de rechazo real son una discrepancia de saltos de línea y dos hunks que afectan a las mismas líneas.

### 3.6 Mensajes de Commit

El mensaje de cada grupo proviene de `generate_pr_content()` — la misma función que utiliza el flujo de commit por defecto, recibiendo únicamente el parche de ese grupo en lugar del diff completo. Nada de la canalización de mensajes se duplica: la skill `.gitpr.commit.md`, la caché MD5 de prompts y la ruta map-reduce para parches extensos se heredan intactas.

Un parche que contiene tres de los nueve hunks de un archivo se genera reconstruyendo el encabezado del archivo y esos tres hunks específicos, no cortando el texto del diff original. Un corte directo arrastra desplazamientos (*offsets*) válidos para el archivo completo pero incorrectos para el fragmento reducido.

---

## 4. Aplicación del Plan

### 4.1 La Secuencia

Para cada grupo, en el orden fijado por el plan:

1. Confirmar que el índice está limpio — nada en stage. Se comprueba antes de cada grupo, impidiendo que cambios residuales de un grupo anterior se preparen sobre el siguiente y aparezcan más tarde en un commit ajeno.
2. Reconstruir el parche del grupo y ejecutar `git apply --cached --check`, seguido de `git apply --cached`. Ambos pasan por el mismo `patch_applier` que `gitpr fix`, entregando el parche a Git como **bytes a través de stdin** — salvaguarda frente a la traducción automática de saltos de línea en Windows (`\n` a `\r\n`), que provocaría el rechazo silencioso del parche completo.
3. Verificar que lo que ha llegado al índice coincide exactamente con el grupo: el conjunto de rutas de `git diff --cached --name-only -M` debe ser idéntico al conjunto de archivos del grupo, y los conteos `(agregadas, eliminadas)` por archivo de `--numstat` deben coincidir con las líneas `+` y `-` de las unidades. Se utiliza numstat y no los encabezados de los hunks, ya que las líneas de un encabezado varían cuando un commit adyacente desplaza las líneas circundantes, lo que provocaría falsas alarmas sobre un plan correcto.
4. Crear el commit, con el mensaje generado para el grupo.
5. Confirmar nuevamente que el índice está limpio.

El árbol de trabajo físico nunca se modifica. Cada archivo en disco conserva todas sus modificaciones, preparadas o no; al final, `git status` muestra un árbol limpio y los commits contienen todo el trabajo.

### 4.2 Lo Que Queda Atrás

Las unidades en `ungrouped_units` permanecen sin commitear y fuera del stage al finalizar la ejecución. Ese es el resultado honesto para un hunk que el modelo no supo clasificar, un grupo que no pudo prepararse en el índice o una unidad descartada por exceder el presupuesto de tokens. Quedan listadas en el informe; el usuario puede commitearlas manualmente o volver a ejecutar `gitpr split` sobre los cambios restantes.

### 4.3 Si Algo Falla a Mitad de la Secuencia

**No hay rollback automático.** Un split genera commits ordinarios, y deshacerlos se realiza mediante `git reset`, herramienta estándar de Git. Lo que el comando garantiza es una parada limpia explicando con exactitud lo sucedido:

| Fallo | Estado posterior del índice |
| --- | --- |
| Al preparar un grupo (*staging*) | Todo lo preparado para ese grupo se retira del índice, y el informe indica que la ejecución se detuvo en ese grupo |
| Al commitear un grupo | El grupo permanece en stage, y el informe lo refleja explícitamente — en lugar de ocultar qué unidades estaban en curso |
| Commits 1..N-1 | Intactos. Son commits reales y válidos, y permanecen |

---

## 5. Plantilla de Skill (*Skill Template*)

Split **no tiene plantilla de skill ni consulta ninguna**.

`.gitpr.split.md` sería la estructura previsible, pero resultaría errónea. `get_skill_context()` responde a un tipo de acción no registrado con la skill de *review* (`DEFAULT_SKILL_TYPE = "review"`), por lo que una llamada previa a su registro global otorgaría silenciosamente al prompt de agrupamiento un comportamiento de revisión de código. Registrarlo formalmente requeriría una nueva entrada en `SKILL_FILES_BY_TYPE`, una nueva etiqueta con validación estricta de orden en la pantalla de configuración, un nuevo recurso en el servidor MCP y plantillas traducidas por cada idioma: una superficie desmedida para un prompt asociado a un esquema de respuesta fijo que no debe editarse a mano.

La instrucción de agrupamiento está, por tanto, integrada directamente en `hunk_grouper.py`, junto al código que valida y procesa su salida.

---

## 6. Variables de Entorno

| Variable | Valor por Defecto | Descripción |
| --- | --- | --- |
| `GITPR_SPLIT_MAX_GROUPS` | `5` | Límite superior de commits atómicos que un plan puede proponer |
| `GITPR_SPLIT_REQUIRE_CONFIRMATION` | `true` | Muestra el plan y solicita confirmación antes de crear el primer commit |
| `GITPR_SPLIT_MAX_HUNKS` | `50` | Límite superior de unidades enviadas a la llamada de agrupamiento |

Las tres variables pueden modificarse en la pantalla de configuración, en el apartado **Split**.

Cualquier valor no positivo o no interpretable para cualquiera de los límites revierte automáticamente al valor por defecto: un límite de cero transformaría silenciosamente la orden "dividir cambios" en "no dividir nada", en lugar de señalar un error visible para el usuario.
