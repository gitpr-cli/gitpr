# Documentación Técnica: Baseline y Supresiones Auditables (`gitpr baseline`)

Adoptar GitPR en un repositorio legado es el momento en que la herramienta resulta menos útil: el linter informa de cuatrocientos problemas preexistentes, el ruleset de secretos señala una clave sintética en un fixture de prueba, y el primer pull request de la migración falla en un portón que no tiene nada que ver con el cambio que contiene. El equipo tiene dos opciones, y las dos son malas — apagar el portón, o gastar un sprint corrigiendo código que nadie está tocando.

Un **baseline** es la tercera opción. Es un archivo, commiteado en Git, que registra los hallazgos que el repositorio ya tiene. A partir de ahí una ejecución clasifica cada hallazgo que encuentra: los que están en el archivo son **existing**, los que estaban y desaparecieron son **resolved**, y solo lo que *este cambio* introdujo es **new** — y solo `new` bloquea. El portón pasa a ser una afirmación sobre el diff en lugar de una afirmación sobre la historia del repositorio.

Junto con el registro viene la pista de auditoría: una supresión no es un filtro silencioso, es una decisión con un **motivo**, un autor y una fecha; la deuda aceptada tiene un **responsable** y, opcionalmente, un **plazo**; y un checksum sobre el archivo entero detecta una edición hecha fuera de GitPR. Todo lo que la herramienta decide sobre un hallazgo puede leerse de vuelta y cuestionarse.

Sin un archivo de baseline, cada comando se comporta exactamente como antes de que esta funcionalidad existiera — misma salida, mismos exit codes, mismas claves de caché.

---

## 1. Visión General

```bash
gitpr baseline create                    # Registra el diff actual como baseline
gitpr baseline show                      # Los hallazgos, las decisiones y los recuentos
gitpr baseline validate                  # Todo defecto del archivo, exit 1 en cualquiera
gitpr baseline update                    # Registra lo que el diff muestra hoy, conservando decisiones
gitpr baseline suppress <id> --reason "…"    # Una decisión sobre un hallazgo
gitpr baseline unsuppress <id>           # Deshace una decisión
```

| Comando | Escribe | Descripción |
|---|---|---|
| **`create`** | `.gitpr/baseline.json` | Registra los hallazgos del diff actual como punto de partida. `--base <ref>` registra el diff contra una ref en lugar del árbol de trabajo; `--refresh` ejecuta la revisión de IA de nuevo en vez de reutilizar la cacheada; `--format json` para CI |
| **`show`** | — | Recuentos por status y la lista de todo hallazgo que lleva una decisión, con su motivo, su escopo y su origen. `--status`, `--rule`, `--file` filtran; `--format json` emite las entradas |
| **`validate`** | — | Todo problema que el archivo y los overrides pueden tener: schema, versión de fingerprint, compatibilidad, checksum, fingerprints duplicados, campos desconocidos, deuda vencida. Exit 1 en cualquiera de ellos |
| **`update`** | `.gitpr/baseline.json` | Registra de nuevo lo que el diff muestra hoy, marcando lo que desapareció como `resolved` y conservando cada decisión. Rechaza un archivo cuyo checksum divergió, salvo que se dé `--recompute` |
| **`suppress`** | la entrada, o `.gitpr/baseline.overrides.yml` | Registra una decisión sobre un hallazgo. `--reason` es obligatorio; `--scope finding\|line\|file\|rule`; `--debt --owner <quién> [--due-date YYYY-MM-DD]` registra deuda en vez de supresión |
| **`unsuppress`** | la entrada, o el archivo de overrides | Deshace una decisión. Una decisión más amplia que ese hallazgo se *reporta*, nunca se borra — se edita donde vive |

Todo comando de escritura acepta `--yes`, que responde a la confirmación sin saltarse las comprobaciones que hay detrás. Sin terminal y sin `--yes` el comando falla con la instrucción, en lugar de bloquearse en un prompt que nadie va a leer.

### 1.1 Ids de hallazgo

Un hallazgo se nombra en la línea de comandos por un **prefijo único de su fingerprint**, que `show` imprime y `suppress` acepta:

```
sha256:ab12cd34ef56…
```

Un id que no corresponde a ningún hallazgo, o a dos, se rechaza — y el rechazo dice cuál de los dos casos fue, porque el id es la única asa que el usuario tiene sobre el hallazgo.

---

## 2. Los cinco status

| Status | Significado | Persistido |
|---|---|---|
| **`new`** | El hallazgo no está en el baseline. Es el punto entero de la funcionalidad, y el único status que bloquea | **nunca** |
| **`existing`** | El hallazgo está registrado y sigue ahí. No se dice nada sobre si es bueno o malo — es conocido | sí |
| **`resolved`** | El hallazgo estaba registrado y ya no aparece, en un archivo que el diff actual toca | sí |
| **`ignored`** | Un humano lo miró y decidió que se queda, con un motivo | sí |
| **`accepted_debt`** | Un humano decidió que se corregirá, con un responsable y un motivo declarado — y opcionalmente un plazo | sí |

`new` nunca se escribe en el archivo: una entrada guardada como "new" estaría obsoleta en la ejecución siguiente, y un archivo que registra su propia comparación es un archivo que miente.

`resolved` solo se aplica a entradas cuyo **archivo aparece en el diff actual**. Un archivo fuera del diff puede estar intacto por razones que no tienen nada que ver con el hallazgo — el diff simplemente no llega hasta él — y llamar a eso "resolved" sería una afirmación falsa en el único lugar que el equipo lee como registro. La regla más estrecha hace que un diff que encoge nunca invente una resolución.

---

## 3. Qué bloquea, y cuánto cuesta

| Superficie | Efecto del baseline |
|---|---|
| `gitpr -l` / `--linter` | Sale con 1 solo cuando un hallazgo de nivel **error** es `new`. Los hallazgos existing, ignored y accepted se muestran con su status y su motivo, y la ejecución continúa |
| `gitpr -r`, `-f`, `-i` | La revisión anota cada hallazgo con su status. La revisión nunca fue un portón, así que ningún exit code cambia |
| `gitpr risk` | Solo los hallazgos `new` puntúan. Todo lo demás se adjunta como evidencia informativa que vale **cero puntos**, con su status en `details`, para que el número de riesgo describa el cambio en lugar del repositorio |
| `gitpr review-pr` | Resuelve la política y el baseline por su cuenta, anotando los hallazgos del linter, la sección de riesgo y el comentario del PR |
| Todo lo demás (`-c`, descripción de PR, blame, issue, chat, release, split, fix) | El baseline no se consulta en absoluto |

Un aviso destructivo, una alerta ignorada o un plazo vencido nunca hacen fallar una ejecución por sí solos: un plazo vencido es un aviso, impreso junto al informe.

---

## 4. Configuración

Cuatro variables en `~/.gitpr/.env`, también editables desde `gitpr config` en la sección **Baseline**:

| Clave | Por defecto | Efecto |
|---|---|---|
| `GITPR_BASELINE_ENABLED` | `true` | `false` → ninguna ejecución lee el baseline; el comportamiento de antes de la funcionalidad, byte a byte |
| `GITPR_BASELINE_PATH` | *(vacío)* | `.gitpr/baseline.json` por defecto. Una ruta relativa se resuelve desde la raíz del repositorio — así se apunta a un monorepo o a un baseline compartido en otro lugar |
| `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` | `true` | Un checksum divergente vuelve el baseline inutilizable: la ejecución lo rechaza, imprime la instrucción y sale con código distinto de cero en los flujos que bloquean. Con él apagado el archivo se aplica y la divergencia se sigue reportando como aviso |
| `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` | `true` | `false` → `.gitpr/baseline.overrides.yml` no se lee, con un aviso. Las decisiones escritas en el archivo de baseline quedan solas |

La clave maestra falla abierta — solo `false`, `0`, `no`, `off` o `n` la apagan.

---

## 5. El archivo

`.gitpr/baseline.json`, commiteado junto con el código:

```json
{
  "schema_version": 1,
  "fingerprint_version": "1",
  "policy_name": "acme/team-policy",
  "policy_version": "1.0.0",
  "gitpr_version": "0.0.37",
  "created_at": "2026-10-10T09:12:44+00:00",
  "updated_at": "2026-10-10T09:12:44+00:00",
  "checksum": "sha256:…",
  "entries": [
    {
      "fingerprint": "sha256:…",
      "rule_id": "sec-aws-key",
      "category": "security",
      "file_path": "tests/fixtures/keys.py",
      "line_start": 18,
      "line_end": 18,
      "severity": "error",
      "source": "linter",
      "status": "ignored",
      "low_confidence": false,
      "first_seen_commit": "a1b2c3d",
      "last_seen_commit": "a1b2c3d",
      "first_seen_date": "2026-10-10",
      "last_seen_date": "2026-10-10",
      "resolved_at": null,
      "suppressed": true,
      "suppression_reason": "Synthetic key in a fixture; never used to reach a service.",
      "suppression_scope": "finding",
      "suppressed_by": "alice",
      "suppressed_at": "2026-10-10",
      "accepted_debt_owner": null,
      "accepted_debt_due_date": null,
      "accepted_debt_reason": null,
      "provenance": {"origin": "local", "command": "baseline suppress", "policy": null}
    }
  ]
}
```

Tres propiedades del formato importan:

1. **Ninguna entrada guarda un mensaje, y ninguna guarda código.** La prosa que emite una regla pertenece a la regla — reescribirla parecería un cambio de baseline — y el baseline se commitea en Git, así que persistir la línea ofensora pondría en el repositorio justamente el secreto que el ruleset señaló. Solo se almacena un *digest* de esa línea.
2. **Las entradas se escriben en orden de fingerprint.** El archivo se commitea, y dos ejecuciones sobre los mismos hallazgos en dos máquinas tienen que producir el mismo diff.
3. **El checksum no se cubre a sí mismo.** Es el SHA-256 del JSON canónico (claves ordenadas, sin espacios, entradas ordenadas) de todos los demás campos. Editar una entrada a mano en un editor — cambiar un número de línea, voltear un status — lo rompe, y `gitpr baseline validate` nombra la divergencia en lugar de aplicar el archivo.

`gitpr baseline update --recompute` es la forma sancionada de aceptar un archivo editado a mano: reescribe el checksum sobre el contenido que encuentra, para que la edición se convierta en un cambio en la historia de Git con un commit detrás, en lugar de una divergencia silenciosa.

---

## 6. El fingerprint

Un hallazgo se identifica con un SHA-256 sobre ocho líneas, en este orden:

```
1  FINGERPRINT_VERSION      ("1")
2  rule_identity            el rule id, o "category:<categoría>" cuando no hay
3  category                 en minúsculas
4  normalize_path           relativo al repo, barras normales, minúsculas
5  source                   linter | ai | external | …
6  line_start
7  line_end
8  snippet_hash             digest de la línea ofensora, con espacios colapsados
```

Deliberadamente **fuera** del payload: el mensaje, el timestamp, el provider y el modelo, la branch, la ruta absoluta del checkout. Dos ejecuciones sobre la misma revisión producen el mismo fingerprint en cualquier máquina, y un build en una ruta distinta no cambia nada.

Qué significa esto en la práctica:

| Cambio | Efecto |
|---|---|
| El mensaje de la regla se reescribe | Mismo fingerprint — un mensaje no es una identidad |
| La línea se reindenta o se espacia de otra forma | Mismo fingerprint — los espacios se colapsan antes del hash |
| El contenido de la línea cambia | **Fingerprint nuevo** — una línea distinta es un hallazgo distinto |
| Se inserta una línea encima del hallazgo, desplazándolo | **Fingerprint nuevo** — los números de línea forman parte de la identidad |
| El archivo se renombra | **Fingerprint nuevo** — la ruta forma parte de la identidad |
| El análisis se ejecuta en otra máquina, otra branch, otro provider | Mismo fingerprint |
| El hallazgo viene de la IA y no lleva rule id | La identidad cae a la categoría, y `low_confidence` se marca como `true` en la entrada |

El sesgo hacia `new` es deliberado. Un `new` falso es visible en el informe y se cura con un comando (`gitpr baseline update`); un `existing` falso silenciaría un hallazgo que no es el mismo hallazgo — y el que silenciaría podría ser un secreto real. Los números de línea están en el payload por el mismo motivo.

`FINGERPRINT_VERSION` es la **primera** línea del payload, así que cambiar el algoritmo cambia todo fingerprint de golpe, invalidando todo baseline a propósito — una migración, no una reinterpretación silenciosa. El manifiesto registra la versión con la que se escribió, y un archivo escrito bajo otra versión se rechaza con la instrucción.

---

## 7. Decisiones: supresiones y deuda aceptada

Una decisión se registra en uno de dos lugares, del más estrecho al más amplio:

1. **En la entrada** — una supresión de escopo `finding`, o deuda aceptada. Un fingerprint, un hallazgo.
2. **En `.gitpr/baseline.overrides.yml`** — todo lo más amplio: una regla, un archivo, un rango de líneas. Este archivo es aditivo y editable a mano, y es donde un equipo declara una política sobre una *clase* de hallazgos.

```yaml
overrides:
  suppressions:
    - fingerprint: "sha256:…"
      scope: finding
      reason: "Clave sintética en un fixture; nunca se usa para alcanzar un servicio."
      by: "alice"
      date: "2026-10-10"
    - scope: rule
      rule_id: "warning-todo-fixme"
      reason: "La regla es un apoyo a la decisión, no un portón, en este árbol legado."
    - scope: file
      rule_id: "php-tabs"
      file_path: "app/Legacy/*"
      reason: "Archivos generados, reescritos en cada migración."
    - scope: line
      rule_id: "php-tabs"
      file_path: "app/Old.php"
      line_start: 100
      line_end: 120
      reason: "Bloque legado en migración este trimestre."
  accepted_debt:
    - fingerprint: "sha256:…"
      owner: "time-backend"
      reason: "Migración planificada para el próximo trimestre."
      due_date: "2026-12-31"
```

| Escopo | Alcanza | Notas |
|---|---|---|
| `finding` | Un fingerprint exacto | El más estrecho, y el único registrado en la propia entrada |
| `line` | Una regla, en un archivo, dentro de un rango de líneas que **contiene** el rango del hallazgo | Ignora el digest de contenido, así que sobrevive a ediciones dentro del bloque — por eso exige siempre un motivo |
| `file` | Una regla, en un archivo o glob de ruta | La misma idea que el linter ya tiene en `ignore_paths` |
| `rule` | Una regla, en todo el repositorio | El más amplio |

La coincidencia más específica gana y suministra el motivo que se muestra al lector. Dos invariantes se garantizan en el código, y no por configuración:

- Una supresión tiene un **motivo** no vacío. Una decisión que nadie explicó no es una decisión; es un filtro.
- La deuda aceptada tiene un **responsable**. Una deuda que nadie asume no está aceptada, está olvidada.

Un plazo es opcional. Un plazo **vencido** es un aviso impreso junto al informe y un problema para `gitpr baseline validate` — nunca un fallo de la ejecución en sí.

Existe una tercera capa que el repositorio no escribe: un **Policy Pack** activo puede llevar un bloque `baseline:` propio (ver `docs/policy-packs.md`). Esas decisiones se aplican en memoria durante la clasificación, se muestran con el origen `policy:<nombre>@<versión>`, y nunca se escriben en `.gitpr/baseline.json` — el pack es una opinión compartida, el archivo es el registro del propio repositorio. `gitpr baseline unsuppress` no borra una de ellas: dice qué pack la lleva.

---

## 8. El flujo en un repositorio legado

```bash
# 1. En la branch de migración, registra lo que ya está ahí.
gitpr baseline create --yes

# 2. Commitea el registro junto con el código que describe.
git add .gitpr/baseline.json && git commit -m "chore: record the baseline"

# 3. Trabaja. Solo lo que el cambio introduce es nuevo.
gitpr -l
gitpr -r
gitpr risk
```

El registro se revisa como cualquier otro archivo. Qué busca un revisor:

| En el diff | Lectura |
|---|---|
| Una entrada nueva con `status: "existing"` y ninguna decisión | El autor reconoció un hallazgo preexistente. Normal, pero si el recuento crece en cientos en un solo commit, el baseline se registró probablemente contra la ref equivocada |
| Una entrada nueva con `suppressed: true` y un `suppression_reason` | Una decisión. El motivo es lo que está bajo revisión — un motivo que repite la regla ("es ruidosa") no explica nada; un motivo que declara la situación ("archivo generado, reescrito por la migración") es auditable |
| Una entrada nueva con `accepted_debt_owner` | Deuda que alguien asume, con un plazo que `gitpr baseline validate` va a reclamar |
| `.gitpr/baseline.overrides.yml` añadiendo un escopo `rule` o `file` | El tipo más amplio de cambio en la postura del repositorio. Silencia una clase de hallazgos, no uno |
| Entradas pasando a `status: "resolved"` | Buena noticia, y barata de verificar: el hallazgo desapareció de un archivo que el diff toca |
| El `checksum` cambiando sin nada más | Nada más se tocó — pero una edición al lado habría sido detectada |

Las rutas `.gitpr/baseline.json` y `.gitpr/baseline.overrides.yml` están en `templates/gitpr.smart-excludes.json`: son registros, no código, y nunca se envían a la IA como parte de un diff.

`create` no tiene dry run: escribe el registro y `gitpr baseline show` lo lee de vuelta, que es la previsualización. Para registrar un diff contra otra ref, `create --base <ref>` y `risk --base <ref>` son la pareja que tiene que concordar — un baseline registrado desde `HEAD` clasifica casi todo como `new` cuando la ejecución de riesgo pregunta por una branch.

---

## 9. Leerlo desde un agente de IDE (MCP)

El servidor MCP expone el registro solo para lectura, para que un agente pueda preguntar lo que el repositorio ya sabe antes de leer un informe:

| Superficie | Qué responde |
|---|---|
| Tool `get_baseline_status` | El resumen en JSON: entradas por status, las reglas más ruidosas, las decisiones por origen y escopo, la deuda aceptada con responsable y plazo, la deuda vencida, y el estado del checksum |
| Resource `baseline://summary` | El mismo resumen, como resource |

Ambos devuelven `baseline_summary()`, que abre el archivo, cuenta lo que hay en él y para: ningún linter, ninguna llamada a la IA, ninguna resolución de política, ninguna escritura. Un archivo que no puede aplicarse se *reporta* — `usable: false` con los `problems` que lo explican — nunca se lanza como excepción, porque "el registro está ahí y el portón lo rechazaría" es una de las respuestas que quien llamó vino a buscar. El resumen lee las mismas capas que lee el portón, así que `.gitpr/baseline.overrides.yml` y el bloque `baseline:` del pack activo aparecen en sus recuentos.

`counts.new` es siempre `0`, y la respuesta dice por qué en `counts_note`: `new` es el resultado de comparar una ejecución contra el registro, no algo que un archivo pueda guardar.

---

## 10. Límites, dichos sin rodeos

- **Una línea desplazada es un hallazgo nuevo.** Deliberado, y explicado arriba. `gitpr baseline update` lo registra de nuevo; el registro conserva el `first_seen_date` de lo que reconoce.
- **Un hallazgo reportado por la IA es de baja confianza.** No tiene rule id, así que su identidad es su categoría y su ubicación — dos problemas distintos en la misma línea, reportados por dos ejecuciones de revisión distintas, son una sola identidad para el baseline. La entrada dice `low_confidence: true` para que el lector pueda sopesarlo.
- **La ruta map-reduce no tiene hallazgos.** Para un diff demasiado grande para una sola llamada, la IA responde en prosa, y la prosa no tiene hallazgos que registrar; `create` dice cuántos vinieron de la revisión de IA, para que la diferencia sea visible.
- **`create` solo lee la revisión cacheada cuando el diff coincide.** La caché indexa una revisión por su prompt, así que `create` compara el `diff` desde el que se hizo la revisión con el actual; una divergencia se reporta y la revisión no se consulta.
- **No existe `gitpr check`, ni exportación SARIF.** El baseline es JSON y es consumible por cualquier cosa que lea JSON; un portón de CI de primera clase y una superficie SARIF no forman parte de esta funcionalidad.
- **El baseline nunca se envía a la IA.** La clasificación ocurre después de que el modelo respondió, sobre su salida estructurada. Nada sobre el registro llega a un prompt.

---

## 11. Lectura relacionada

- `docs/policy-packs.md` — el bloque `baseline:` que un pack puede llevar, y cómo se le atribuyen las decisiones de un pack de dependencia
- `docs/mcp-integration.md` — el servidor MCP, la tool `get_baseline_status` y el resource `baseline://summary`
- `docs/linter-regras-customizadas.md` — las reglas de linter a partir de las cuales se fingerprintea un hallazgo
- `docs/config-tui.md` — la pantalla de configuración donde viven las cuatro variables
- `docs/plans/ADR-012-baseline-suppressions.md` — por qué el fingerprint hashea el contenido de la línea, por qué `new` nunca se persiste, y por qué la capa de un pack queda en memoria
