# Documentación Técnica: Guía del Revisor (`gitpr explain` / `--explain`)

La Guía del Revisor explica un conjunto de cambios desde el punto de vista de quien va a revisar. En lugar de describir cómo es el diff (la descripción del Pull Request ya lo hace), responde a las cuatro preguntas que un revisor se plantea antes de aprobar: **qué cambia**, **por qué cambia**, **dónde centrar la revisión** y **qué riesgo de regresión conlleva**.

Está disponible como comando independiente, como sección opcional del flujo de Pull Request y a través del servidor MCP y de la extensión de VS Code.

---

## 1. Visión General

```bash
# Explica los cambios no confirmados en el repositorio actual
gitpr explain

# Fuerza un proveedor de IA concreto para esta ejecución
gitpr explain --provider deepseek

# Incluye la Guía del Revisor en la descripción del Pull Request (flujo estándar de PR)
gitpr --explain

# Lo mismo, guardando la descripción localmente sin abrir la TUI de publicación
gitpr --explain --no-publish

# Incluirla siempre, sin pasar la flag en cada ejecución
# (~/.gitpr/.env)
GITPR_EXPLAIN_BY_DEFAULT=true

# Ayuda contextual con el enlace a la documentación
gitpr -h --explain
```

---

## 2. Referencia de Comandos

| Invocación | Alcance | Escribe en disco | Publica |
|---|---|---|---|
| `gitpr explain [--provider <name>]` | Diff del árbol de trabajo (`git diff HEAD`) | No | No |
| `gitpr --explain` | Diff completo de la rama contra la base remota | Sí (fichero `.md` del PR) | Sí, cuando se publica el PR |
| `gitpr --explain --no-publish` | Diff completo de la rama contra la base remota | Sí (fichero `.md` del PR) | No |
| `gitpr --explain --no-edit` | Diff completo de la rama contra la base remota | Sí | Sí, directamente |

### `gitpr explain`

| Opción | Valor por defecto | Descripción |
|---|---|---|
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Fuerza el proveedor de IA para esta ejecución (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Ayuda de Click más el enlace a esta página. |

El comando independiente imprime la guía en la terminal y termina. Nunca crea un fichero, nunca abre el editor y nunca se comunica con el forge.

### Flag raíz `--explain`

| Flag | Variable de entorno | Valor por defecto | Descripción |
|---|---|---|---|
| `--explain` | `GITPR_EXPLAIN_BY_DEFAULT` | `false` | Añade la sección de la Guía del Revisor a la descripción del Pull Request generada. |

Valores aceptados por `GITPR_EXPLAIN_BY_DEFAULT` (sin distinguir mayúsculas): `true`, `1`, `yes`, `y`. Cualquier otro valor — incluida la variable ausente — mantiene la sección desactivada. La clave se puede editar en la pantalla de configuración (`gitpr config`), en la categoría **PR**, y se puede definir manualmente en `~/.gitpr/.env`.

La flag solo participa en el **flujo estándar de Pull Request**. Los modos que terminan antes de ese flujo (`--commit`, `--review`, `--fullreview`, `--issue`, `--blame`, `--chat`, `gitpr tests generate` y el resto de subcomandos) la ignoran.

---

## 3. Orígenes del Diff

Los dos puntos de entrada no explican lo mismo:

| Punto de entrada | Comando subyacente | Abarca |
|---|---|---|
| `gitpr explain` | `git diff -U1 -w -M -B HEAD -- <smart excludes>` | Cambios staged y unstaged de ficheros rastreados, comparados con `HEAD`. Los ficheros no rastreados se advierten y **no** forman parte del prompt. |
| `--explain` (flujo de PR) | `git fetch origin` → `git merge-base origin/<base> HEAD` → `git diff -U1 -w -M -B <merge-base> -- <smart excludes>` | Todo lo que la rama cambia respecto al punto en que divergió de la rama base, incluido el estado del árbol de trabajo. |

En ambos casos el diff se captura con `-U1` (una línea de contexto), `-w` (ignora espacios en blanco), `-M` (detección de renombrados), `-B` (pares rotos) y las **smart excludes** resueltas (lockfiles, artefactos generados y otras rutas que ahogarían la señal). El mismo fichero auxiliar se puede sobrescribir con `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL` y `GITPR_SMART_EXCLUDES_LOCAL`.

Como el diff está recortado para lectura, no es un parche: no debe usarse con `git apply`. Los comandos que necesitan un parche aplicable (`gitpr fix`, `gitpr split`) capturan su propio diff.

---

## 4. Pipeline de Generación

1. **Comprobación de diff vacío.** Un diff vacío o solo con espacios devuelve de inmediato una explicación vacía; el comando independiente imprime `⚠️ No diff found...` y sale con código `1`.
2. **Proveedor y clave.** El proveedor procede de `--provider` o `DEFAULT_AI_PROVIDER`. Si no hay clave configurada, el comando imprime `❌ No API key configured for <provider>. Generate one with --install.` en **stderr** y devuelve una explicación vacía. `ollama` no necesita clave.
3. **Selección del modelo.** Se usa el modelo avanzado/primario (`get_api_model(provider, task_complexity="advanced")`): `GEMINI_API_MODEL_PRIMARY` o `DEEPSEEK_API_MODEL_PRIMARY`, con el valor por defecto incorporado correspondiente.
4. **Resolución de la skill.** La instrucción de sistema es `get_skill_context("explain", quiet=True)` — `.gitpr/skill/.gitpr.explain.md` cuando existe, un `.gitpr.md` heredado como fallback, o si no una instrucción incorporada equivalente a la plantilla en inglés. El flujo de PR pasa `quiet=True` para que el mensaje «skill cargada» nunca ensucie la descripción generada.
5. **Prompt.** El diff completo y las reglas de explicación se envían en un único prompt. La salida debe ser un objeto JSON (la capa de proveedores está configurada para respuestas JSON).
6. **Llamada a la IA.** `call_ai_model(..., action="explain")` usa temperatura `0.0` y reintenta hasta **3** veces con un intervalo de **2 s**. Si falla, devuelve `None` y el comando informa de que no se pudo generar la guía.
7. **Parseo.** `parse_explain_payload` acepta el **dict** ya parseado del proveedor y, por compatibilidad, una cadena JSON. Una cadena que no sea JSON válido se trata como prosa: rellena `what_changes`, el campo `why_it_changes` recibe un placeholder `[FILL: ...]` y `has_sufficient_evidence` pasa a `False`.
8. **Renderizado.** `build_explain_markdown` compone la sección Markdown que usa el flujo de PR; el comando independiente renderiza los mismos datos en un informe coloreado en la terminal.

El flujo **no** utiliza la caché local de respuestas de IA y **no** escribe una fila en el ledger de métricas. Cada ejecución llama al proveedor.

---

## 5. Contrato de Salida

El modelo devuelve un objeto JSON con cuatro campos:

| Campo | Tipo | Significado |
|---|---|---|
| `what_changes` | string | 2–4 frases en lenguaje sencillo que describen el cambio funcional, sin jerga. |
| `why_it_changes` | string | La motivación inferida. Cuando el diff no respalda una conclusión, el modelo debe usar `[FILL: What is the primary business motivation for this change?]` en lugar de inventarla. |
| `reviewer_focus_points` | array de objetos | 2–5 puntos concretos que inspeccionar. Cada objeto tiene `description` (obligatorio), `file_path` (opcional) y `related_line` (entero opcional). |
| `regression_risk` | string | Superficies objetivas de riesgo: código compartido crítico, migraciones de esquema, cambios de autenticación, pruebas ausentes, interfaces que rompen. |

La capa de proveedores añade `_telemetry_meta` al dict; el parser lo ignora.

### Sección Markdown

```markdown
## 🧐 Reviewer Guide (Explain My PR)

### 🔍 What changes
...

### 💡 Why it changes
...

### 🎯 Where to focus review
- **Validate token expiration** (`src/auth/tokens.py:45`)
- **Check backward compatibility of the refresh endpoint**

### ⚠️ Regression Risk
...
```

`Where to focus review` solo se emite cuando existe al menos un punto de atención, y `Regression Risk` solo cuando el campo no está vacío.

### Indicador de evidencia

`has_sufficient_evidence` es `False` cuando el diff está vacío, cuando no hay clave de API disponible o cuando `what_changes` / `why_it_changes` contienen un marcador de placeholder (`[PREENCHER`, `[FILL`, `[TODO`, `[REQUIRED`). El comando independiente imprime un aviso bajo el informe; la sección del PR no se suprime — los placeholders permanecen visibles para que el autor los complete.

---

## 6. Dónde Aparece la Guía

### Flujo de PR (`--explain`)

Después de generar el título y el cuerpo del PR, la Guía del Revisor se añade al cuerpo como un bloque separado:

```text
<descripción del PR>

---

## 🧐 Reviewer Guide (Explain My PR)
...
```

El cuerpo combinado se escribe en el fichero `.md` del PR y es lo que se publica cuando se crea el Pull Request. Activar `GITPR_EXPLAIN_BY_DEFAULT=true` produce el mismo resultado sin la flag.

### Servidor MCP

La herramienta `generate_pr_description` acepta `explain: bool = false` y añade la misma sección al `pr_description` devuelto. La herramienta calcula el diff completo de la rama por su cuenta; la guía se omite si el modelo no devuelve Markdown.

### Extensión de VS Code

El comando `gitpr.generatePrExplain` ejecuta la generación de PR con `explain: true`. El comando simple `gitpr.generatePr` deja la sección desactivada.

---

## 7. Personalizar la Guía con una Skill

Las reglas de explicación son una **skill**, no texto de prompt fijo:

- Ubicación por defecto: `.gitpr/skill/.gitpr.explain.md` en el repositorio.
- Descárgala con `gitpr --skill` (también disponible en el asistente de instalación). Existen variantes de idioma para `en`, `pt_br`, `pt_pt`, `es_es` y `fr_fr`; el fichero se descarga en el idioma de interfaz activo y **nunca se sobrescribe** si ya existe.
- Un `.gitpr.md` heredado en `.gitpr/skill/` se usa como fallback cuando falta el fichero específico.
- Cuando no existe ninguno de los dos, se usa la instrucción incorporada; es equivalente a la plantilla en inglés y también exige JSON estricto.
- El idioma del texto generado sigue la skill cargada, no el idioma de interfaz de `--lang`. Para obtener la guía en español, por ejemplo, descarga o escribe el `.gitpr.explain.md` en español.

La plantilla instruye al modelo a escribir para un revisor que no escribió el código, a no inventar nunca la motivación, a enumerar de 2 a 5 puntos de atención y a devolver solo el objeto JSON.

---

## 8. Errores y Códigos de Salida

| Situación | Comportamiento | Código de salida |
|---|---|---|
| Guía generada | Informe en la terminal (independiente) o sección añadida (flujo de PR) | `0` |
| Sin diff / sin contenido | `⚠️ No diff found...` en stdout | `1` |
| Sin clave de API | Error localizado en stderr; el comando independiente también imprime `❌ Failed to generate PR explanation.` | `1` |
| El modelo no devolvió nada útil | `❌ Failed to generate PR explanation.` | `1` |
| Flujo de PR, el modelo no devolvió nada | La sección se omite silenciosamente de la descripción; el resto del PR se produce con normalidad | `0` |
| Nombre de proveedor inválido | La capa de proveedores informa del proveedor desconocido; no se produce ninguna guía | `1` (independiente) |

---

## 9. Ejemplo

```text
$ gitpr explain

🧐 Analyzing diff from reviewer perspective...

============================================================
  REVIEWER GUIDE (Explain My PR)
============================================================

🔍 What changes:
  Adds a Redis-backed rate limiter to the login route and wires it
  into the authentication middleware.

💡 Why it changes:
  Mitigates brute-force credential stuffing without changing the
  login response contract.

🎯 Where to focus review:
  • Verify the key expiration strategy [src/auth/limiter.py:25]
  • Confirm legitimate shared-IP users are not locked out [src/auth/middleware.py]

⚠️ Regression Risk:
  Users behind shared NATs may be throttled together; no test covers
  the limit boundary yet.

⚠️ Notice: Inferred with partial context. Some fields contain placeholders to complete.
```

---

## 10. Limitaciones

- **La salida independiente es solo la terminal.** `gitpr explain` no escribe ningún fichero ni publica nada; para adjuntar la sección a un PR, usa `--explain` en el flujo de PR.
- **`--explain` es exclusiva del flujo estándar de PR.** Combinarla con modos que terminan antes no tiene efecto.
- **Sin caché, sin ledger.** Las ejecuciones repetidas vuelven a llamar al modelo, y la ejecución no queda registrada en `gitpr metrics`.
- **Los ficheros no rastreados no se explican.** Ambos orígenes del diff solo ven ficheros rastreados. El comando independiente advierte de los ficheros no rastreados, pero no los incluye; añádelos con `git add` primero.
- **Sin chunking.** El diff completo va en un único prompt. Los cambios muy grandes pueden alcanzar el límite de contexto del proveedor; divide el trabajo o revisa un rango menor.
- **Sin semántica de parche.** El diff se captura con `-w` y `-U1` para lectura. No lo reutilices para `git apply`.
- **La motivación es inferida.** El modelo tiene prohibido inventar una justificación; cuando el diff no aporta evidencia, emite un placeholder `[FILL: ...]`.
- **El idioma depende de la skill.** El idioma de la interfaz por sí solo no traduce la guía generada.

---

## 11. Documentación Relacionada

- [Publicación de Pull Request](pull-request-publication.es_es.md) — dónde se adjunta la sección y cómo se publica el PR.
- [Plantillas de Skill](skill-template.es_es.md) — cómo se resuelven, descargan y sobrescriben los ficheros `.gitpr.*.md`.
- [Proveedores de IA](providers-ia.es_es.md) — proveedores, modelos, reintentos y configuración de claves.
- [TUI de Configuración](config-tui.es_es.md) — cómo editar `GITPR_EXPLAIN_BY_DEFAULT` desde `gitpr config`.
- [Generación de Pruebas](tests-generate.es_es.md) — el otro comando de generación con IA.
- [Modo Mentor](mentor-mode.es_es.md) — las explicaciones pedagógicas añadidas a las revisiones de código.
