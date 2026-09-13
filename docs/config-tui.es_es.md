# Documentación Técnica: Pantalla de Configuración Interactiva (`gitpr config`)

GitPR se configura mediante `~/.gitpr/.env`, un archivo dotenv con alrededor de cincuenta variables. Hasta ahora, cambiar una exigía saber su nombre exacto, abrir el archivo a mano y adivinar si el valor es `true`, `1` o `yes` — y un valor que el lector no entiende se traga en silencio, así que un error de escritura nunca aparece como error.

`gitpr config` abre una pantalla master-detail sobre ese mismo archivo: categorías a la izquierda, los ajustes de la seleccionada a la derecha, editados en el sitio. Es una capa fina sobre el archivo que ya tiene — no una segunda fuente de configuración.

```bash
gitpr config
```

---

## 1. La Pantalla

```text
┌ Header ──────────────────────────────────────────────┐
│ Configuración      [/ buscar…]   ● 2 sin guardar     │
├──────────────┬───────────────────────────────────────┤
│ General      │  Idioma de la interfaz                │
│ Proveedores… │  [ es_es            ▾ ]               │
│ Pull Request │                                       │
│ …            │  Coautor                              │
│              │  [ ●] habilitado                      │
├──────────────┴───────────────────────────────────────┤
│ F1 Ayuda · F2 Guardar · ^R Restaurar · / Buscar ·    │
└──────────────────────────────────────────────────────┘
```

| Tecla | Acción |
| --- | --- |
| `F1` | Ayuda — la lista de atajos y cómo se leen los valores |
| `F2` | Valida y guarda los cambios pendientes |
| `Ctrl+R` | Restaura el valor por defecto del campo enfocado (elimina la línea) |
| `/` | Busca un nombre de variable o una etiqueta en todas las categorías |
| `Esc` | Sale — o limpia la búsqueda primero; pregunta antes de descartar |

### 1.1 Categorías

El menú lateral refleja los comandos y flags de la CLI, así que el ajuste que busca está donde está la funcionalidad que usa. La primera entrada es siempre **General**:

| Categoría | Contiene |
| --- | --- |
| **General** | Idioma de la interfaz, trailer de coautor, registro general |
| **Proveedores de IA** | Motor por defecto, timeout de la IA, las dos claves de API, y los modelos de cada proveedor — bajo una subsección por proveedor, mostrada de una en una |
| **Pull Request** | `OUTPUT_FILE_NAME`, branch base, auto commit/stage/merge, omitir linter, log de publicación, sugerencia de revisores |
| **Revisión de Código** | `OUTPUT_FILE_NAME_REVIEW`, `_FULLREVIEW`, `_FILEREVIEW` |
| **Issue** | `OUTPUT_FILE_NAME_ISSUE` |
| **Blame** | `OUTPUT_FILE_NAME_BLAME` |
| **Linter** | `OUTPUT_FILE_NAME_LINTER`, `GITPR_LINTER_TIMEOUT` |
| **Release** | Ruta del changelog, resumen por IA, bump automático, borrador por defecto, `OUTPUT_FILE_NAME_RELEASE` |
| **SCM / Forge** | Proveedor, token de CI/CD, token de la forge, URL base; subsecciones **GitHub**, **Bitbucket** y **Azure DevOps** con lo que necesita cada forge |
| **Filtros de Diff** | Interruptor de smart excludes y las dos rutas de lista de filtros |
| **Skills** | Los siete archivos de skill de este proyecto — una entrada por skill, editadas ahí mismo (§1.7) |
| **Avanzado** | Tres subsecciones — **Spinner**, **Git Hooks**, **Descargas** — ocultas hasta activar **Mostrar avanzadas** |
| **Desconocidas** | Claves del archivo que el schema no declara — aparece solo cuando existen |

Cada una de las doce categorías enlaza con su propia documentación técnica (§1.5).

### 1.2 Controles

Cada campo recibe el control que su tipo merece, para que un valor inválido sea difícil de producir de entrada:

| Tipo | Control |
| --- | --- |
| Booleano | Switch |
| Enum | Select |
| Entero | Campo de texto, validado |
| Plantilla de nombre de archivo | Campo de texto, validado contra los placeholders |
| Ruta, texto libre | Campo de texto |
| Secreto | Campo enmascarado |
| Lista de palabras | Cuadro de solo lectura que se desplaza por sí mismo, con el recuento de entradas encima y un botón de descarga (§1.4) |

### 1.3 Filtrado por el Valor Seleccionado

Dos ajustes deciden qué otros ajustes están en pantalla, y el panel sigue la selección **de inmediato** — antes de que se guarde nada:

| Cuando selecciona | Ve |
| --- | --- |
| Un **Proveedor por defecto** | Solo los modelos de ese proveedor. Sin nada seleccionado, no se muestra ninguna sección de proveedor |
| Un **Proveedor de la forge** | Solo la subsección de esa forge, más los campos que todas las forges comparten |

La búsqueda ignora el filtro a propósito: buscar `deepseek` con Gemini seleccionado sigue encontrando los modelos de DeepSeek, así que puede prellenar un proveedor al que está a punto de cambiar. Un campo oculto con una edición pendiente se guarda igualmente — la visibilidad es una vista, no un permiso.

### 1.4 Botones de Descarga

Cuatro listas se sirven desde el repositorio de GitPR y se refrescan cuando cambia su marcador de versión. **📥 Forzar descarga** junto a un marcador de versión lo vuelve a descargar a demanda, y **📥 Descargar la lista de palabras** hace lo mismo con las palabras del spinner. Es la salida manual para el caso que la comprobación automática no puede ver: la lista está presente, actualizada, y aun así no es la que quiere.

El botón informa del resultado con honestidad, porque una descarga puede fallar y caer de vuelta a la copia que ya está en disco sin que desde fuera haya forma de distinguir una cosa de la otra:

| Respuesta | Significado |
| --- | --- |
| `✔ v0.0.24` y *"{name} está actualizado ({version})."* | El archivo lleva ahora la versión actual — recién descargado o una copia que ya estaba al día |
| `✖ no actualizado` y *"No se pudo descargar {name}. La copia anterior sigue en uso."* | La descarga falló. No se perdió nada: la copia anterior está intacta y sigue en uso |
| *"El inglés no necesita paquete de traducción — no hay nada que descargar."* | El paquete de traducción no tiene edición en inglés que buscar, porque el inglés va incorporado |

El veredicto sale de releer `~/.gitpr/.env` tras la descarga, nunca de `os.getenv()`: `load_dotenv()` se ejecuta con `override=False`, así que el proceso sigue con el valor con el que arrancó.

### 1.5 Enlace a la Documentación

**📚 Documentación** en la parte superior del panel derecho abre la documentación técnica de la categoría que está viendo, y la URL se imprime junto al botón para que pueda leerla o copiarla antes.

| Categoría | Documento |
| --- | --- |
| General | `config-tui.md` |
| Proveedores de IA | `providers-ia.md` |
| Pull Request | `pull-request-publication.md` |
| Revisión de Código | `code-review-ia.md` |
| Issue | `gitpr-issue-option.md` |
| Blame | `blame-arqueologo.md` |
| Linter | `linter-regras-customizadas.md` |
| Release | `release-notes.md` |
| SCM / Forge | `scm-multiforge.md` |
| Filtros de Diff | `smart-excludes.md` |
| Skills | `skill-template.md` |
| Avanzado | `version-markers.md` |

El enlace sigue el idioma de la interfaz (`?lang=pt_br`), y la línea desaparece en la vista de búsqueda y en **Desconocidas**, que no es una categoría que GitPR posea.

### 1.6 El Conmutador de Avanzadas

**Mostrar avanzadas** en la barra superior revela la categoría `Avanzado` y todo campo marcado como interno. La mayoría son marcadores de versión que GitPR mantiene por su cuenta al descargar traducciones, presets de linter, palabras del spinner y listas de filtros; se muestran por transparencia, no para editarlos. El conmutador está desactivado en cada apertura.

Dos de esos campos no son marcadores y conviene conocerlos:

- **Idioma de los hooks** (`SCRIPTS_LANG`) — el idioma en el que se instalan los Git hooks. Vacío significa "seguir el idioma de la interfaz", que es lo que quiere la mayoría de los usuarios; elegir uno instala los hooks en ese idioma en la siguiente ejecución. **Idioma de los hooks instalados**, a su lado, es de solo lectura y registra lo que hay realmente en disco, así que los dos nunca se confunden.
- **Palabras del spinner** — la lista en sí, de solo lectura, en el cuadro descrito en §1.2.

### 1.7 La Sección Skills

En todo lo demás, la pantalla edita `~/.gitpr/.env`. **Skills** es la única sección que no: edita los archivos de skill del propio proyecto — las instrucciones de IA leídas de `./.gitpr/skill/` ([Sistema de Skills y Plantillas](skill-template.es_es.md)).

La lista tiene una entrada por skill soportada por GitPR: **Commit**, **Pull Request**, **Code Review**, **File Review**, **Issue**, **Blame**, **Release**. Es la lista de las skills que cargan los comandos, no un espejo de la carpeta — un archivo en `.gitpr/skill/` que ningún comando lee no se ofrece aquí.

| La entrada muestra | Significado |
| --- | --- |
| nada | El archivo existe y se puede escribir — edítelo en el cuadro de la derecha y pulse `F2` |
| **● editado** | Una edición suya sigue sin guardar |
| **no está en este proyecto** | El archivo no existe. El cuadro muestra *"Este proyecto todavía no tiene el archivo {name}."* y el editor queda deshabilitado — un cuadro vacío se leería como "esta skill está vacía", que es lo contrario de lo que es cierto |
| **solo lectura** | El archivo existe pero no se puede escribir. Se muestra, bloqueado, y no hay nada que guardar |

**📥 Descargar la plantilla** aparece para una skill ausente y trae la plantilla publicada para su idioma de interfaz, como los botones de descarga de la §1.4. Cuando ni eso se puede escribir — una carpeta `.gitpr/skill/` sin permiso de escritura — el botón queda deshabilitado con el motivo al lado.

`F2` guarda los campos del `.env` **y** los archivos de skill en la misma pasada, y el contador de pendientes cubre ambos. Dentro del panel, `Ctrl+R` descarta la edición y devuelve el texto del disco — lo más parecido a un valor por defecto que tiene un archivo — y `Esc` pregunta antes de descartarla, como en todo lo demás.

Cada archivo conserva los finales de línea que ya tenía, así que un archivo `CRLF` sigue siendo `CRLF` y su diff muestra solo las líneas que editó.

---

## 2. Cómo Se Leen los Valores

**La pantalla muestra lo que hay en el archivo, no lo que el proceso está usando.** La diferencia importa, porque `load_dotenv()` se ejecuta con `override=False` en todo GitPR: cuando una variable también está exportada en su shell, el entorno gana y el archivo se ignora en tiempo de ejecución.

Un campo en esa situación se marca con **⚠ en el entorno**, y el valor en pantalla sigue siendo el del archivo. Editarlo está permitido — simplemente no surtirá efecto mientras la variable no se elimine del entorno. Esto es deliberado: sin la marca vería un valor que en silencio no es el que está en uso, que es el fallo más confuso que puede producir este archivo.

Los valores se leen con un parser que mira solo el archivo, nunca con `os.getenv()`, así que nada del proceso actual se filtra a la pantalla.

---

## 3. Edición y Guardado

No se escribe nada hasta que pulse `F2`. Mientras edita, `F2` muestra un contador de cambios pendientes y `Esc` pide confirmación antes de salir:

- **Guardar** escribe solo los campos que realmente cambió, así que las líneas no relacionadas conservan sus comentarios y su posición en el archivo.
- **Archivos de skill** se escriben en el mismo guardado: un `F2` cubre los campos pendientes del `.env` y las skills editadas (§1.7). Una skill que no se puede escribir se reporta por su nombre y mantiene su edición pendiente — los demás archivos se guardan igualmente.
- **`Ctrl+R`** en un campo **no** reescribe el valor por defecto incorporado — marca la línea para **eliminación**, de modo que el valor vuelve a lo que el código define por defecto. El campo muestra `— se eliminará —` y un nuevo `Ctrl+R` deshace la marca. Este es el reset honesto: escribir el valor por defecto actual lo congelaría en el archivo e interrumpiría el seguimiento de cambios futuros.
- **Vaciar un campo** limpia la sobrescritura.
- Tras guardar, la pantalla permanece abierta, relee el archivo e informa cuántos ajustes se guardaron.

### 3.1 Validación

`F2` valida antes de escribir nada. Un campo que falla recibe borde rojo y un mensaje inline, no se guarda nada, y la pantalla salta al primer campo problemático — cambiando de categoría y activando **Mostrar avanzadas** si es ahí donde vive.

| Regla | Por qué |
| --- | --- |
| Solo `true` / `false`, más `1`/`0`, `yes`/`no`, `y`/`n`, `off` | GitPR tiene dos lectores de booleano que discrepan fuera de este conjunto. `on` parece simétrico a `off`, pero uno lo lee como **false** y el otro como **true** |
| Los enteros deben ser mayores que cero | Un timeout que no se puede interpretar se sustituye por el valor por defecto en silencio, así que un error de escritura nunca aparece como error |
| Los enums deben ser una de las opciones declaradas | Un nombre de proveedor desconocido no se rechaza al arrancar, simplemente no funciona |
| Las plantillas deben usar placeholders conocidos y conservar `{datetime}` | Un placeholder desconocido es un `KeyError` en el siguiente comando; sin `{datetime}` cada ejecución resuelve al mismo nombre de archivo y sobrescribe el informe anterior |

### 3.2 Validación de Credenciales

Un secreto (clave de API, token de la forge) se valida contra su proveedor antes de guardarse, porque una credencial equivocada solo se descubre después, en medio de un comando real. La validación se ejecuta en segundo plano para que la pantalla nunca se bloquee, y el resultado decide:

| Resultado | Comportamiento |
| --- | --- |
| Aceptada | Se guarda |
| Rechazada (HTTP 401/403, o una respuesta "invalid API key") | **Bloquea** — la credencial es incorrecta y guardarla no ayuda a nadie |
| Fallo de red, timeout, proveedor inalcanzable | **Se guarda con aviso** — una clave correcta escrita detrás de un proxy no puede ser rechazada |

Solo se revalidan los secretos que cambió en esta sesión. Una clave que ya estaba en el archivo y no se tocó no se sondea en cada guardado.

Los valores de secreto **nunca se vuelven a mostrar**. El campo queda vacío cuando no hay nada guardado, y muestra un placeholder fijo (`•••••••• (definido — escriba para reemplazar)`) cuando existe un valor — la misma máscara sea cual sea el secreto, porque el valor real nunca se lee hacia la pantalla. Solo entra en el guardado cuando escribe algo en él. Los secretos se cifran en reposo con la clave Fernet local en `~/.gitpr/secret.key`; la pantalla cifra al escribir y nunca descifra para rellenar un campo.

---

## 4. Búsqueda y Claves Fuera del Schema

Escribir en la caja de búsqueda filtra por nombre de variable **y** por etiqueta, en todas las categorías a la vez — `timeout` encuentra los timeouts de la IA y del linter sin que sepa en qué categoría están. Mientras hay una búsqueda activa, el área principal muestra los resultados como una lista plana, con un recuento, en lugar de los campos de la categoría seleccionada; el menú lateral se queda donde está. `Esc` limpia la búsqueda — y devuelve el foco al menú lateral — antes de poder salir de la pantalla.

Las variables presentes en el archivo que GitPR no declara caen en una categoría **Desconocidas** que solo aparece cuando existen tales claves. Son de solo lectura: la pantalla nunca escribe una clave que no es suya. Cambiar una significa editar el archivo a mano.

---

## 5. Deliberadamente No Editables

Estas claves no reciben campo editable. La pantalla nunca oculta una clave que está en su archivo — solo se niega a **escribir** en una que no es suya — así que todas menos la última siguen apareciendo, solo lectura, en **Desconocidas** (ver §4).

| Variable | Por qué |
| --- | --- |
| `GITPR_SCM_TOKEN` | El token crudo de CI/CD tiene precedencia sobre el cifrado y se guarda en texto plano. Tiene una fila en **SCM / Forge** — de solo lectura y nunca mostrada — que apunta a `gitpr --init`, que es lo único que debería escribirlo; un campo editable invitaría a ensombrecer el token que configuró allí |
| `PR_AUTO_PUBLISH` | Resto de antes de que publicar fuera el flujo por defecto. No se lee en ninguna parte: lo que la sustituyó es la flag `--no-edit`. Una instalación antigua puede seguir llevando su línea en el `.env`, y por eso aparece en **Desconocidas** |
| `CI`, `GITHUB_ACTIONS` | Marcadores del entorno del proceso, nunca escritos en este archivo, así que nunca aparecen |

---

## 6. Para Desarrolladores

La pantalla se construye a partir de un schema declarativo, así que añadir un ajuste es un cambio de datos y no de interfaz.

| Archivo | Papel |
| --- | --- |
| `src/config_schema.py` | Dato puro: `ConfigField`, `Category`, `Group`, `CATEGORIES`, `GROUPS`, `FIELDS` (56 campos), más `fields_of()`, `validate_field_value()` y los auxiliares de búsqueda. Fuente única de verdad para menú, widgets, valores por defecto, subsecciones, visibilidad y validación |
| `src/doc_links.py` | `doc_url(filename)` — la URL base de la documentación y la regla de `?lang=`. Separado de `core.py` porque la pantalla no puede importar `src.core`, que arrastra los SDK de IA en cada apertura |
| `src/ui/config_app.py` | `ConfigApp` más los modales de ayuda y confirmación. Layout master-detail, dirty state, búsqueda, el conmutador de avanzadas, el filtro de visibilidad, los workers de descarga, el panel de Skills (§1.7) y el pipeline de guardado |
| `src/config.py` | Cuatro funciones nuevas: `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()`. También guarda el registro de skills (`SKILL_FILES_BY_TYPE`, `SKILL_TYPES`) y los auxiliares de archivo (`read_skill_file()`, `write_skill_file()`, `skill_file_status()`) que leen tanto `get_skill_context()` como la sección Skills (§1.7) |
| `src/main.py` | El subcomando `config` — sin `setup_environment()`, para que nada pueda pedir entrada por stdin dentro de la app a pantalla completa |

Tres atributos de un `ConfigField` sostienen el layout: `group` pone el campo bajo un subencabezado, `show_if` lo oculta a menos que otro campo tenga uno de los valores listados, y `action` le adjunta un botón de descarga. `version_source` dice qué constante mostrar cuando un marcador de versión todavía no está en el archivo — un `LINTER_PRESETS_VERSION` vacío muestra la versión incluida en el código en lugar de una caja vacía.

**Añadir un ajuste:** declare un `ConfigField` con etiqueta y descripción literales `__("…")`, añada la clave a `DEFAULT_CONFIG` si es un nuevo valor por defecto de sembrado, y traduzca las claves nuevas en los seis `langs/*.json`. `tests/test_config_schema.py` falla mientras el schema y `DEFAULT_CONFIG` no coincidan — y hasta que un nuevo `group`, `show_if` o `action` apunte a algo que exista — y `tests/test_i18n.py` falla mientras cada archivo de idioma no lleve las claves nuevas.

**Modelo de estado:** las ediciones pendientes viven en un diccionario indexado por el nombre de la variable, no en los widgets. El conjunto de filas visibles cambia según navega o busca, y un valor leído de vuelta de un control oculto sería frágil — por eso `F2` es independiente de lo que hay en pantalla en ese momento.

**Las escrituras en disco** pasan por `set_key()`/`unset_key()` de `python-dotenv`, que escriben un archivo temporal y lo renombran, preservando comentarios y orden. La pantalla nunca reescribe el archivo entero.

Vocabulario de arquitectura: [Glosario de la Configuración](plans/glossary-config-tui.md).

> **Nota:** `gitpr -h config` abre la pantalla e ignora el `-h`, porque el callback raíz retorna pronto para todo subcomando. Use `gitpr config -h` para el texto de ayuda.
