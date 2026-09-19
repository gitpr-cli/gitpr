# Documentación Técnica: Tour Guiado (gitpr demo)

`gitpr demo` recorre las tres cosas que GitPR hace con un cambio — el mensaje de commit, la revisión de código y la descripción de pull request — sobre un diff de ejemplo que viaja dentro del paquete. No se genera nada y no se envía nada a ningún sitio: las respuestas se grabaron una vez y se reproducen, así que el tour funciona **sin clave de API, sin repositorio Git y sin conexión**.

Existe para acortar la distancia entre el `pip install gitpr-cli` y el "ya entiendo para qué sirve esta herramienta". Cualquier otra función necesita configuración antes de mostrarte algo: un proveedor, una clave, un token de forge, un repositorio con un diff dentro. El tour no necesita ninguno, lo que lo convierte en el único comando que funciona en una máquina donde GitPR nunca se ha ejecutado.

---

## 1. Visión General

El tour es un subcomando, no un flag: `gitpr demo` nunca llega a la configuración de la clave de API, al bloqueo de actualización de PyPI ni a la comprobación de internet, porque nada después de él necesita un entorno configurado.

### 1.1 Referencia del Comando — `gitpr demo`

Todas las opciones del subcomando, tal como las muestra `gitpr demo -h` (o `--help`):

```bash
gitpr demo                                  # el escenario por defecto, en pantalla
gitpr demo --scenario security-issue        # el otro ejemplo incluido
gitpr demo --no-tui                         # texto plano, sin pantalla
gitpr demo --lang es_es --no-tui            # el tour en español
```

| Opción | Descripción |
| --- | --- |
| **`--scenario <name>`** | Qué ejemplo recorrer. Sin él se usa el primer escenario registrado. Un nombre desconocido sale con código 1 y lista los que existen |
| **`--lang <code>`** | Idioma de la interfaz en esta ejecución (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`). Anula `GITPR_LANG` en esta ejecución y no se persiste |
| **`--no-tui`** | Imprime el tour como texto plano en lugar de abrir la pantalla. Para CI, para terminales limitados y para grabaciones |
| **`-h` / `--help`** | Ayuda más el enlace de la documentación en el idioma actual |

| Característica | Descripción |
| --- | --- |
| **Contenido** | Respuestas grabadas una vez por GitPR y embarcadas como código en el paquete — reproducidas, nunca regeneradas |
| **Proveedor de IA** | No se instancia ninguno y no se lee ninguna clave. El pipeline se ejecuta de verdad, con la llamada al modelo sustituida |
| **Red** | Ninguna. Ninguna petición HTTPS, ningún DNS, ningún socket |
| **Git** | Ninguno. No hace falta ningún repositorio; el tour no ejecuta un solo comando `git` propio |
| **Archivos escritos** | Ninguno. Ningún `.md`, ningún `.txt`, ninguna entrada de caché, ninguna métrica |
| **Pantalla** | Una app Textual, o texto plano con `--no-tui` (contenido idéntico en ambos) |
| **Código de salida 1** | Un nombre de `--scenario` desconocido |

---

## 2. Las Seis Etapas

El tour es lineal: seis pantallas, en este orden, cada una con un título, una línea de texto de contexto y el artefacto del que habla.

| # | Etapa | Qué muestra |
| --- | --- | --- |
| 1 | **Bienvenido a GitPR** | Qué hace la herramienta y la promesa del tour: un ejemplo grabado, sin clave, sin repositorio, sin conexión |
| 2 | **El cambio de ejemplo** | El diff unificado — código, en inglés, en todos los idiomas |
| 3 | **Mensaje de commit** | Lo que `gitpr -c` escribe para ese diff: un asunto en Conventional Commits más el razonamiento que no cabe en él |
| 4 | **Revisión de código** | Lo que reporta `gitpr -r`, compuesto exactamente como se compone la revisión local: los avisos del linter primero, la revisión debajo |
| 5 | **Descripción del pull request** | Lo que `gitpr` escribe para la rama: qué cambió, por qué y qué debe mirar el revisor — más la insignia que añade una publicación, contada de las alertas grabadas del linter |
| 6 | **Próximos pasos** | `gitpr --init` para lo de verdad, el enlace de la documentación y cómo volver a ejecutar el tour |

### 2.1 Teclas

| Tecla | Acción |
| --- | --- |
| `n`, `→`, `Enter` | Etapa siguiente. En la última etapa, sale del tour |
| `p`, `←` | Etapa anterior. En la primera etapa no hace nada (un pitido, no una salida) |
| `F1` | Ventana de ayuda: las teclas y sobre qué está corriendo el tour |
| `Esc` | Sale del tour, desde cualquier etapa — y desde dentro de la ventana de ayuda |

Volver es gratis: los tres artefactos se generan una vez, antes de la primera pantalla, así que volver nunca regenera nada y el tour no puede mostrar una respuesta distinta la segunda vez. Una etapa cuenta como vista cuando la dejas hacia delante, así que releer una anterior no la desmarca.

---

## 3. De Dónde Vienen las Respuestas

El tour no es una presentación de pantallas fijas: llama al mismo `generate_pr_content()` que llaman `gitpr -c`, `gitpr -r` y `gitpr`, y al mismo `compose_review_content()` que renderiza la revisión local. Solo se sustituye la llamada al modelo — por un fake que devuelve la respuesta grabada del escenario — y eso es lo que impide que el tour se aleje de lo que imprimen los comandos reales.

Todo lo que el pipeline buscaría fuera queda neutralizado mientras dura el tour:

| Sustituido | Por qué |
| --- | --- |
| **`call_ai_model`** | El origen de los datos: un fake que reproduce la respuesta grabada y registra la llamada |
| **`get_cached_response` / `save_cached_response`** | Una lectura de caché reproduciría *tu* revisión antigua de una rama real, y una escritura archivaría la respuesta del demo bajo un prompt real — el tour no lee ni escribe nada |
| **`log_command_metric` / `log_local_metric`** | La telemetría escribe en `~/.gitpr/metrics/` sin interruptor, y un tour no es uso de una función |
| **`get_api_key` / `get_api_model`** | El pipeline de PR se rinde *antes* de llamar al modelo cuando falta la clave o el modelo, así que hay que responderlo |
| **`get_skill_context`** | Determinismo: un archivo local en `.gitpr/skill/` cambiaría lo que muestra el tour, e imprimiría su línea de "plantilla cargada" en medio de él |

El diff en sí es código del repositorio y permanece en inglés en todos los idiomas — traducir `Rule::unique()` tergiversaría lo que lee la herramienta. La prosa alrededor, las revisiones y las descripciones de PR sí están traducidas.

Un escenario que no consigue producir uno de los tres artefactos lanza un error en lugar de renderizar una pantalla en blanco: un tour vacío parece que la herramienta no encontró nada, cuando la causa real es que el pipeline nunca llegó al proveedor.

---

## 4. Los Escenarios Incluidos

| Escenario | Stack | El cambio |
| --- | --- | --- |
| **`laravel-bug-fix`** (por defecto) | PHP / Laravel | Una actualización de perfil que rechaza el propio correo del usuario — `unique:users,email` sin `ignore()`, donde el arreglo añade la regla de ignore |
| **`security-issue`** | TypeScript / Express | Un IDOR en la descarga de facturas: la fila se resuelve solo por clave primaria, así que cualquier usuario autenticado descarga la factura de otra organización |

Cada uno es un módulo Python en `src/demo/scenarios/` que expone tres nombres:

```python
NAME = "laravel-bug-fix"   # el valor que recibe --scenario
DIFF = """..."""           # el diff unificado — código, nunca traducido
TEXT = {"en": {...}, "pt_br": {...}, ...}   # la prosa y las respuestas grabadas
```

Los escenarios son módulos y no archivos de datos JSON porque el paquete no embarca ningún archivo que no sea `.py`: `pyproject.toml` recoge `src` y `src.*` mediante `packages.find` y no tiene `package_data`, así que un archivo de datos se quedaría fuera de la wheel sin que nada fallara en la build.

Para añadir uno, coloca un módulo en ese directorio, regístralo en `src/demo/scenarios/__init__.py` y copia la forma de arriba. `TEXT["en"]` es obligatorio y es el fallback para todos los demás idiomas; las pruebas exigen que cada idioma presente cargue `title`, `description`, `commit_message`, `review`, `linter` y `pr_description`, no vacíos, con las cabeceras de hunk del `DIFF` cuadrando.

---

## 5. Idiomas

El tour tiene dos mitades y se traducen por separado:

| Mitad | Dónde vive | Idiomas |
| --- | --- | --- |
| **Chrome** — títulos de las etapas, prosa de contexto, ventana de ayuda, próximos pasos | `langs/*.json`, como cualquier otra cadena de la herramienta | `pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr` |
| **Prosa de los escenarios** — título del ejemplo, revisión, mensaje de commit, descripción del PR | Dentro de cada módulo de escenario, en `TEXT` | `en`, `pt_br`, `pt_pt`, `es_es`, `fr_fr` |

Un escenario cuyo idioma no tiene entrada en `TEXT` cae al inglés en esa mitad, en lugar de fallar o mezclar — un idioma parcialmente traducido degrada en vez de romperse. El escenario informa en qué idioma corrió realmente.

`--lang` lo declara el propio subcomando, porque el callback raíz retorna antes de su propio handler de `--lang` para cualquier subcomando. Sin el flag, el tour sigue `GITPR_LANG` / el idioma detectado del sistema, el mismo de la interfaz que lo rodea, así que ambas mitades coinciden siempre.

---

## 6. Lo Que el Tour No Toca

| No toca | Porque |
| --- | --- |
| Tu proveedor de IA y tus claves | La llamada al modelo está sustituida; no se lee ninguna clave, y ninguna hace falta que exista |
| `~/.gitpr/cache/prompts/` | Las dos llamadas de caché están sustituidas, así que el tour no lee una revisión real en caché ni envenena la caché con una grabada |
| `~/.gitpr/metrics/` | Las dos llamadas de métrica están sustituidas |
| Tu árbol de trabajo y tu repositorio | Ningún comando `git` del propio tour se ejecuta, y no se escribe ningún archivo — ningún informe, ningún `.md`, ningún `.txt` |
| `.gitpr/skill/` | La búsqueda de skill está sustituida, así que una plantilla local nunca cambia lo que muestra el tour |
| La forge | Ningún token, ninguna llamada de API, ningún repositorio |

**Una línea sí se escribe.** El log de invocaciones (`~/.gitpr/logs/`) registra la ejecución como cualquier otro comando, desde el callback raíz de la CLI por el que pasan todos los comandos y todos los `-h`, junto con la única consulta a `git config` que etiqueta la línea con el repositorio y el autor. Es local y best-effort — un home de solo lectura o un `git` ausente nunca se convierten en un comando fallido — y `GITPR_SHOW_LOGS=false` lo desactiva. Nada más del tour deja rastro.

---

## 7. Variables de Entorno

El tour no introduce **ninguna configuración nueva**. Lee lo que ya lee el resto de la herramienta:

| Variable | Para qué |
| --- | --- |
| `GITPR_LANG` | Idioma de la interfaz, cuando no se da `--lang` |
| `GITPR_SHOW_LOGS` | Desactiva el log de invocaciones (`false`), para cualquier comando |

No se lee ninguna variable de clave, token, modelo o ruta: en una máquina con el `~/.gitpr/` vacío, `gitpr demo` es el único comando que sigue funcionando.

> **Nota:** Consulta también la [documentación de Revisión de Código](code-review-ia.es_es.md) para lo que previsualiza la cuarta etapa, la de [Mensajes de Commit](commit-message-ia.es_es.md) para la tercera, y la de la [Insignia](badge.es_es.md) para la marca al pie de la quinta.
