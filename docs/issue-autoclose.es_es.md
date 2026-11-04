# Documentación Técnica: Cierre Automático de la Issue (`--close-issue`)

La TUI de Issues crea una issue y luego se cierra; el número que recibió se pierde, y el siguiente Pull Request es el primer lugar donde podría cerrarse. El cierre automático de issue es el puente entre esos dos momentos: un registro local lleva el número hacia adelante, y el flujo de Pull Request ofrece una línea — `close #N` — que hace que el forge cierre la issue cuando se produce el merge.

No es un gestor de issues. No edita, lista, reabre ni etiqueta nada, y nunca habla con el forge por iniciativa propia: nada se registra hasta que se crea una issue desde la TUI, y nada se decide hasta que una ejecución de Pull Request encuentra un registro que leer.

---

## 1. Visión General

La funcionalidad actúa en tres superficies:

1. **Creación.** `gitpr -is` abre la TUI de Issues; `F3` crea la issue en el forge, y la misma respuesta se escribe en `.gitpr/conf/github.yml`.
2. **La ejecución del Pull Request.** El flujo estándar `gitpr` lee el registro antes de generar cualquier cosa, pregunta al forge si la issue sigue abierta y — como máximo una vez — ofrece añadir la línea de cierre a la descripción.
3. **Ayuda contextual.** `gitpr -h --close-issue` y `gitpr -h --no-close-issue` describen las dos flags y enlazan a este documento.

### 1.1 Referencia de Comandos

```bash
gitpr -is                      # Crea una issue; F3 en GitHub la registra
gitpr                          # El flujo de PR lee el registro y puede ofrecer close #N
gitpr --close-issue            # Acepta la línea sin preguntar (la issue se sigue verificando)
gitpr --no-close-issue         # Omite la funcionalidad en esta ejecución
gitpr -h --close-issue         # El mismo resumen, con enlace a este documento
```

| Comando | Escribe | Qué hace |
|---|---|---|
| `gitpr -is` → `F3` | `.gitpr/conf/github.yml`, `.gitignore` | Crea la issue en GitHub y registra número, título, URL, fecha de creación y rama. `F2` (guardar localmente) no registra nada |
| `gitpr` (estándar) | El cuerpo del Pull Request, solo cuando se acepta la línea | Lee el registro, verifica la issue, pregunta como máximo una vez |
| `--close-issue` | Lo mismo que arriba | Acepta la línea sin la pregunta; la issue se sigue verificando |
| `--no-close-issue` | Nada | No se lee ningún registro y no se hace ninguna llamada al forge |
| `-h --close-issue` | Nada | Imprime la ayuda contextual |

Las dos flags responden a la misma pregunta, así que pasar ambas es un error de uso: la ejecución informa de que no pueden usarse juntas y sale con código `1`. El rechazo ocurre antes del prompt de migración del ledger y de la creación del archivo de proyecto, porque un error de uso no puede preguntar nada ni escribir archivos. `-h` tiene precedencia sobre el error, así que una llamada de ayuda que lleve las dos flags sigue mostrando las dos entradas.

---

## 2. El Flujo, de Extremo a Extremo

Seis pasos, en el orden en que la ejecución los recorre:

1. **Registro.** `F3` en la TUI de Issues llama al forge, recibe la nueva issue y entrega el resultado a `register_created_issue` (`src/ui/issue_app.py`). Solo se registra GitHub; un fallo aquí se silencia, porque la issue ya existe en el forge y la contabilidad local nunca debe convertir una creación correcta en un error.
2. **Gate inicial.** `_prepare_close_issue` (`src/main.py`) se ejecuta al principio del flujo estándar de Pull Request — **antes** de la comprobación de archivos no confirmados, antes de leer el diff y antes de cualquier llamada a la IA. Vuelve inmediatamente para `--no-close-issue`, para `GITPR_ISSUE_AUTOCLOSE=false` y cuando el archivo no tiene registro ni error. Solo después de esas compuertas construye el registro — y construirlo ejecuta `git rev-parse` — y resuelve el provider SCM.
3. **Decisión.** `resolve_close_issue` (`src/issue_autoclose/resolve_close_issue.py`) lee el registro una vez, pregunta al forge una vez y pregunta al usuario como máximo una vez. Las compuertas se listan en la sección 4.
4. **Ensamblaje.** `insert_close_line` (`src/issue_autoclose/insert_close_line.py`) se ejecuta en el único punto donde se construye la descripción — después de la guía del revisor y antes del archivo `.md` local y de `pr_data`. El publicador de la TUI y el publicador directo de `--no-edit` reciben, por tanto, exactamente el mismo cuerpo.
5. **Publicación.** La TUI (`PrPublishApp`) o `_publish_pr_directly` envía el cuerpo al forge.
6. **Limpieza.** El registro se elimina solo cuando el cuerpo llegó realmente al forge: `app.body_published` en la TUI, o `_publish_pr_directly` devolviendo `True`. Una pregunta rechazada, `Esc`, una publicación fallida o simplemente abrir un Pull Request existente conservan el registro para la siguiente ejecución.

La decisión se toma antes de que exista la descripción por un motivo: preguntar una vez, al principio, mantiene la pregunta lejos de la pantalla del publicador y deja que la misma respuesta fluya al archivo, a la TUI y al publicador directo sin un segundo prompt.

### 2.1 Cuánto Cuesta Cada Paso

| Paso | Disco | Red | IA | Se omite cuando |
|---|---|---|---|---|
| 1. Registro | Escritura del registro, más una línea en `.gitignore` en la primera escritura | La llamada `create_issue` que ya estaba ocurriendo | — | Issue creada fuera de la TUI, guardado local (`F2`) o un forge distinto de GitHub |
| 2. Gate inicial | Una lectura del registro | `git rev-parse` solo con la funcionalidad activa | — | `--no-close-issue`, `GITPR_ISSUE_AUTOCLOSE=false`, ningún registro |
| 3. Decisión | Una lectura del registro | Una `get_issue`; una segunda llamada para la rama por defecto solo en el camino de la pregunta | — | Cualquiera de las compuertas de la sección 4 |
| 4. Ensamblaje | — | — | — | No se produjo ninguna decisión |
| 5. Publicación | Los artefactos habituales del PR | La llamada habitual de publicación | La generación habitual del PR | — |
| 6. Limpieza | Una eliminación de archivo | — | — | No se publicó nada |

Sin registro, la ejecución es el flujo de todas las versiones anteriores, byte a byte. El único trabajo extra es una lectura de archivo.

---

## 3. El Archivo de Registro

El registro vive en `.gitpr/conf/github.yml`, anclado en la raíz del repositorio. Es estado local, no contenido del proyecto: no está pensado para commitearse, y la primera escritura añade exactamente una línea al `.gitignore` del repositorio.

La carpeta en sí no se ignora por completo. `gitpr.config.yml` vive en el mismo `.gitpr/conf/` y se versiona a propósito (ADR-015), así que la entrada de ignore nombra específicamente el archivo de registro.

El registro guarda **una issue a la vez — la última gana.** Un flujo de Pull Request único no necesita más: la issue documentada es la que se acaba de crear. Crear una segunda issue sustituye a la primera, y no hay historial que consultar. Es también por esto que el archivo no es una caché de issues: es un marcapáginas.

### 3.1 El Formato

```yaml
schema_version: 1
last_issue:
  repo: owner/name
  number: 42
  title: "Add login rate limit"
  url: https://github.com/owner/name/issues/42
  created_at: '2026-11-03T14:22:07'
  branch: feat/login-rate-limit
```

`schema_version: 1` es la única versión que este módulo lee y la única que escribe. Un archivo con cualquier otra versión se informa como ilegible en lugar de adivinarse.

`load()` valida cada campo antes de devolverlo:

- `repo`, `title`, `url` y `created_at` deben ser texto no vacío;
- `number` debe ser un entero positivo, y un booleano se rechaza aunque Python lo trate como entero;
- `branch` es opcional y puede estar vacío.

Un **archivo ausente no es un error** — significa "ninguna issue registrada". Un archivo ilegible es un error, devuelto como dato (`RegistryLoad.error`) para que el comando dueño de la pantalla decida cómo informarlo. El módulo nunca imprime.

### 3.2 Escrituras, Corrupción y `.gitignore`

`record()` escribe en un archivo temporal hermano y lo mueve a su sitio con `os.replace`, así que una ejecución interrumpida nunca deja un registro truncado. Un archivo que `load()` informó como corrupto simplemente se sustituye por el siguiente `record()`: un marcapáginas roto vale menos que uno nuevo.

Antes de la primera escritura, `record()` pregunta `git check-ignore -q .gitpr/conf/github.yml`. Solo cuando git aún no ignora el archivo añade la entrada a `.gitignore`, y solo una vez. Fuera de un repositorio git, o cuando no se puede escribir el `.gitignore`, nada cambia y el registro sigue siendo válido — el usuario puede añadir la línea a mano.

`clear()` elimina el archivo y devuelve `False` cuando no había nada que eliminar, así que el llamador nunca tiene que distinguir "eliminado" de "no existía". Cualquier fallo real de E/S se convierte en `IssueRegistryError`; los llamadores que se ejecutan dentro del flujo de Pull Request lo capturan y siguen adelante, porque el estado local no puede romper una publicación.

---

## 4. La Decisión: Compuertas en Orden

El orden forma parte del contrato. Toda compuerta que no cuesta nada se ejecuta antes de cualquier acceso a disco o red, y solo una issue todavía abierta llega a la pregunta. `skipped_reason` es el vocabulario que informa la métrica `issue_autoclose` (sección 8).

| # | Compuerta | `skipped_reason` | Costo | Limpia el registro |
|---:|---|---|---|---|
| 1 | Se pasó `--no-close-issue` | `flag-disabled` | Ninguno | No |
| 2 | `GITPR_ISSUE_AUTOCLOSE=false` | `disabled` | Ninguno — el flujo de PR vuelve antes de llamar al caso de uso; la comprobación permanece como defensa en profundidad para llamadores que controlan el interruptor | No |
| 3 | El forge no es GitHub | `not-github` | Ninguno | No |
| 4 | El registro existe pero no puede leerse | `registry-error` | Una lectura de archivo, un aviso | No |
| 5 | No hay registro | `no-record` | Una lectura de archivo | No |
| 6 | El registro pertenece a otro repositorio | `other-repo` | Una lectura de archivo | No (ADR-007) |
| 7 | `get_issue` responde 404 | `issue-missing` | Una llamada HTTP | **Sí** |
| 8 | `get_issue` falla por otro motivo | `verify-failed` | Una llamada HTTP, un aviso | No — se conserva para la siguiente ejecución |
| 9 | El número es un Pull Request | `issue-is-pr` | Una llamada HTTP | **Sí** |
| 10 | La issue no está `open` | `issue-not-open` | Una llamada HTTP | **Sí** |
| 11 | No hay terminal y no se pasó `--close-issue` | `no-tty` | Una llamada HTTP | No |
| 12 | Se pasó `--close-issue` | — (se toma una decisión) | Una llamada HTTP, sin pregunta | No |
| 13 | El usuario responde a la pregunta | `declined` cuando la respuesta es no | Una segunda llamada HTTP para la rama por defecto, solo en este camino | No si se rechaza |

Dos detalles importan más que la tabla:

- **La comprobación de Pull Request va antes que la de estado.** El endpoint de issues de GitHub también responde a números de Pull Request, así que `is_pull_request` se examina primero. Un número que resulta ser un Pull Request no es una issue que se cerró — es un registro que nunca podrá usarse, y se olvida.
- **La comparación de repositorio ignora mayúsculas y minúsculas.** Los nombres de owner y repositorio en GitHub no distinguen mayúsculas de minúsculas, así que `matches_repo()` los compara con `casefold()`. Un registro de otro repositorio no es asunto de este flujo, y se conserva deliberadamente en lugar de limpiarse.

### 4.1 La Pregunta y el Aviso de Rama de Destino

La pregunta es:

```text
Issue #42 – Add login rate limit is open. Add "close #42" to the end of the pull request description?
```

Tiene "sí" como valor por defecto. `ask` se llama fuera de todo bloque `try`: el `Abort` de `click` es un `RuntimeError`, y `Ctrl+C` debe dejar el flujo exactamente como cualquier otro prompt, en lugar de ser tragado como funcionalidad omitida.

En el camino de la pregunta — y solo en él — el flujo también obtiene la rama por defecto del repositorio. Cuando el destino configurado difiere de la rama por defecto, la pregunta lleva una línea extra:

> Warning: the pull request targets `"develop"` but the default branch is `"main"`. GitHub only closes the issue when the merge lands on the default branch.

Una consulta de la rama por defecto que falla o vuelve vacía degrada en silencio. El forge solo dice "desconocido", y un aviso que el llamador no sabe formular correctamente es peor que ningún aviso.

### 4.2 Lo Que el Resultado Lleva

`CloseIssueOutcome` tiene cinco campos, y todos pueden ignorarse con seguridad:

| Campo | Significado |
|---|---|
| `decision` | El número, el título y la línea exacta a insertar — `None` cuando no se ofreció nada o el usuario rechazó |
| `warning` | Un mensaje de una línea para imprimir; nunca se define cuando se hizo una pregunta |
| `skipped_reason` | La compuerta que terminó la decisión; vacío cuando se tomó una decisión |
| `asked` | Si el usuario vio realmente una pregunta |
| `accepted` | Si la línea se insertará |

Una decisión nunca limpia el registro — limpiar es tarea del llamador, una vez que el Pull Request existe (ADR-007), porque una publicación fallida debe conservar el registro para la siguiente ejecución. `target_branch_warning` se repite en la decisión solo para que el llamador lo conserve junto a la línea; ya formó parte de la pregunta y no debe imprimirse de nuevo.

---

## 5. Inserción e Idempotencia

El cuerpo se construye una sola vez. `insert_close_line` se llama desde ese punto y desde ningún otro, así que ningún publicador puede recibir un cuerpo sin la línea o con la línea añadida dos veces.

Una decisión `None` devuelve el cuerpo sin cambios. En caso contrario, la línea se añade como párrafo propio:

```text

close #42
```

La función es idempotente entre las grafías de las palabras clave. GitHub acepta `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` y `resolved`, sin distinguir mayúsculas de minúsculas, y la misma issue puede nombrarse como `owner/repo#42`. Si el cuerpo ya menciona **el mismo número de issue** en cualquiera de esas formas, no se añade nada — el forge cerrará la issue de todos modos, y una segunda referencia solo sería ruido.

La insignia se adjunta después y siempre al final del cuerpo, así que añadir aquí es lo que deja la línea de cierre inmediatamente antes de ella. Este módulo nunca tiene que buscar una insignia.

---

## 6. El Contrato SCM y los Otros Forges

Tres métodos de `ScmProvider` existen para esta funcionalidad:

| Método | GitHub | Clase base |
|---|---|---|
| `get_issue(repo, number, timeout=5)` | `GET /repos/{owner}/{repo}/issues/{n}` | Lanza `ScmNotSupportedError` |
| `get_default_branch(repo, timeout=5)` | `GET /repos/{owner}/{repo}` → `default_branch` | Lanza `ScmNotSupportedError` |
| `closing_line(number)` | `close #N` | Lanza `ScmNotSupportedError` |

Ninguno de los tres es abstracto. Es deliberado: GitLab, Bitbucket y Azure DevOps siguen compilando y siguen funcionando en todas las demás funcionalidades, y el cierre automático es exclusivo de GitHub (ADR-003). El llamador lee `ScmNotSupportedError` como "funcionalidad inactiva", nunca como un fallo.

`closing_line` es sintaxis del forge, no una cadena genérica. GitHub lee `close #N`; una línea construida en cualquier otro lugar podría estar escrita correctamente y aun así no significar nada para el forge. El timeout corto de cinco segundos también forma parte del contrato: la respuesta solo decide si se hará una pregunta, y un forge lento no puede retener el flujo de Pull Request.

`provider_is_github()` se comprueba antes de todo esto, así que los otros forges omiten la funcionalidad sin lectura de disco y sin aviso.

---

## 7. Configuración

Dos variables en `~/.gitpr/.env`, también editables en `gitpr config` en la sección **Issue**. Ninguna se escribe automáticamente.

| Clave | Valor por defecto | Efecto |
|---|---|---|
| `GITPR_ISSUE_AUTOCLOSE` | `true` | Solo `false`, `0`, `no`, `off` o `n` desactivan la funcionalidad; cualquier otro valor — incluido uno que no pueda interpretarse — la mantiene activa |
| `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` | `5` | Segundos de espera al forge al leer la issue. Cero, un número negativo o un valor no entero vuelven a `5` |

La precedencia es:

```text
--no-close-issue  >  GITPR_ISSUE_AUTOCLOSE=false  >  --close-issue
```

`--close-issue` **no anula** `GITPR_ISSUE_AUTOCLOSE=false`. El interruptor es la decisión del usuario sobre la máquina, y una flag por ejecución que la revirtiera en silencio haría que la configuración no fuera digna de confianza. No existe configuración por repositorio para esta funcionalidad.

---

## 8. Métricas

Toda decisión que alcanza el caso de uso se informa una vez al ledger local (`gitpr metrics`) como una fila `issue_autoclose`:

| Campo del payload | Valor |
|---|---|
| `command` | `issue_autoclose` |
| `asked` | Si se mostró la pregunta |
| `accepted` | Si la línea se insertará |
| `skipped_reason` | La compuerta de la sección 4, o vacío cuando se tomó una decisión |

Los cortocircuitos del propio helper — flag desactivada, configuración desactivada, ningún registro, ningún provider — nunca activaron la funcionalidad y quedan fuera del ledger. No son decisiones; son ejecuciones en las que no había nada que decidir.

Los campos viajan en el payload JSON. La exportación CSV lleva las columnas que el ledger define para todos los comandos, no un formato por funcionalidad.

---

## 9. Límites, Dichos con Claridad

- **Una issue a la vez.** Crear una segunda issue sustituye el primer registro; la primera ya no puede cerrarse con esta funcionalidad.
- **El registro solo ocurre en la TUI.** Una issue creada con `gh`, mediante la API o por cualquier otro camino es invisible para la funcionalidad.
- **Solo GitHub.** Los otros forges omiten la funcionalidad en silencio, sin aviso y sin registro.
- **El registro es por clon.** Es estado local y no se commitea, así que el clon de un colega no lo hereda, y un clon nuevo empieza sin nada que cerrar.
- **Borrar la línea en el editor no conserva el registro.** Si el cuerpo se publicó, el registro se limpia porque la publicación llevó el cuerpo — aunque la línea se haya editado fuera antes del envío.
- **Actualizar un Pull Request existente también limpia el registro.** La TUI informa "created" también para ese camino; lo que decide la limpieza es que el cuerpo llegó al forge.
- **Las palabras clave son solo en inglés.** `close`, `fix` y `resolve` y sus flexiones son lo que lee GitHub; un cuerpo que diga `cierra #42` no es una referencia de cierre, y la línea se añadirá junto a ella.
- **La comprobación de estado confía en el forge.** Una issue cerrada entre la lectura y el merge no puede detectarse aquí; la línea de cierre simplemente ya no tiene nada que cerrar.

---

## 10. Lectura Relacionada

- `docs/issue-tui-help.md` — la TUI de Issues, `F2`/`F3` y el resumen corto de esta funcionalidad para el usuario.
- `docs/config-tui.md` — la pantalla de configuración, incluida la sección **Issue**.
- `docs/metricas-telemetria.md` — el ledger local y la métrica `issue_autoclose`.
- `docs/scm-multiforge.md` — la abstracción de providers y por qué solo GitHub implementa el cierre.
- `docs/github-pat-integration.md` — el token que `F3` necesita para crear la issue.
- `docs/pull-request-publication.md` — el publicador que recibe el cuerpo ensamblado.
- `docs/specs/issue-autoclose/adrs/ADR-001` a `ADR-007` — las decisiones detrás del registro, las compuertas, la inserción y la limpieza.
- `CONTEXT.md` — los términos del glosario *Issue registry*, *Closing line* y *Close issue decision*.
