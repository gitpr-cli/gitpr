# Versionado y Sincronización Automática de Scripts de Hooks

Esta documentación detalla la arquitectura y el funcionamiento del sistema de versionado y sincronización automática de los scripts de Git hooks de GitPR. El sistema garantiza que los scripts de hooks instalados en tus repositorios estén siempre actualizados con la última versión, respetando tus preferencias de idioma.

---

## 1. Descripción General

GitPR incluye un sistema automático de versionado para scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Cada vez que ejecutas `gitpr`, el sistema verifica silenciosamente si los hooks instalados coinciden con la última versión disponible. Si se detecta una nueva versión — o si el idioma ha cambiado — los hooks se descargan y actualizan automáticamente.

Este mecanismo es independiente del auto-updater principal de GitPR (`--update`) y opera en una cadencia de versión separada, ya que los scripts de hooks evolucionan a un ritmo diferente al CLI en sí.

---

## 2. Arquitectura

### 2.1 Marcadores de Versión

| Marcador | Ubicación | Propósito |
|----------|-----------|-----------|
| `__scripts_version__` | `src/updater.py` | Fuente única de verdad — define la versión actual de los scripts de hooks enviados con esta release de GitPR |
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Rastrea qué versión está instalada actualmente en la máquina del usuario |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | **El idioma que pediste.** Vacío sigue el idioma de la interfaz. Se edita en la pantalla `gitpr config` |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | **Lo que está en disco.** Lo escribe el instalador, nunca el usuario, y se muestra en solo lectura en la pantalla de configuración |

Los dos marcadores de idioma están separados a propósito. La auto-sincronización tiene que notar un cambio de idioma, y eso exige comparar lo que está instalado con lo que se quiere — dos valores independientes. Un único `SCRIPTS_LANG` escrito por el instalador se compararía consigo mismo, y eso nunca puede diferir, así que cambiar de idioma mantendría los hooks en el antiguo en silencio.

### 2.2 Flujo de Sincronización Automática

```
ejecución de gitpr
    │
    ├─ Lee SCRIPTS_VERSION y SCRIPTS_INSTALLED_LANG desde ~/.gitpr/.env
    │
    ├─ Calcula el idioma deseado: SCRIPTS_LANG (la elección, desde el archivo)
    │  o el idioma vivo de la interfaz cuando está vacío
    │
    ├─ ¿Coinciden? → Omitir (vía rápida — lectura única del .env, sin red)
    │
    └─ ¿Difieren o faltan? → Descargar e instalar hooks en el idioma deseado
                              → Grabar SCRIPTS_VERSION + SCRIPTS_INSTALLED_LANG
```

La vía rápida (cuando las versiones coinciden) es una única lectura del archivo `.env` con cero E/S de red.

El idioma deseado se lee del archivo y no de `os.getenv()`, y el idioma de la interfaz se lee de `src.i18n` en el momento de la llamada y no de la copia congelada que este módulo tiene de él — `set_lang()`, que es lo que llama `--lang`, reasigna la constante en lugar de mutarla. Sin las dos cosas, `gitpr --lang fr_fr` instalaría los hooks en el idioma con el que arrancó el proceso.

### 2.3 Idiomas Soportados

La interfaz escribe un idioma de una forma y el archivo publicado lo escribe de otra, y las dos no son intercambiables: `GITPR_LANG` y `SCRIPTS_LANG` contienen `es_es`/`fr_fr` mientras que los archivos del servidor se llaman `.es`/`.fr`. `HOOK_SCRIPT_SUFFIXES` en `src/core.py` es ese mapa, y nada más puede asumir que los dos lados coinciden.

| Idioma | Código de interfaz / `SCRIPTS_LANG` | Sufijo del Script | Ejemplo |
|--------|--------------------------------------|-------------------|---------|
| Inglés (predeterminado) | `en_us` | *(sin sufijo)* | `pre-commit-template.sh` |
| Portugués (Brasil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Portugués (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Español | `es_es` | `.es` | `pre-commit-template.es.sh` |
| Francés | `fr_fr` | `.fr` | `pre-commit-template.fr.sh` |

Un código fuera del mapa instala el script base, que es el inglés. El inglés también es el respaldo cuando falta en el servidor un script específico de idioma (HTTP 404).

---

## 3. Cómo Funciona

### 3.1 Primera Ejecución (Sin Hooks Instalados)

Cuando un usuario ejecuta `gitpr --installhooks` o `gitpr --install` por primera vez:

1. GitPR resuelve el idioma efectivo: `SCRIPTS_LANG` cuando se eligió uno, el idioma vivo de la interfaz en caso contrario
2. Descarga primero los scripts específicos del idioma (ej.: `pre-commit-template.es.sh`)
3. Utiliza el respaldo en inglés si la variante de idioma no está disponible (HTTP 404)
4. Aplica permisos de ejecución (`chmod +x`)
5. Graba `SCRIPTS_VERSION` y `SCRIPTS_INSTALLED_LANG` en `~/.gitpr/.env`. `SCRIPTS_LANG` **no** se escribe — es tu elección, y un instalador que lo sobrescribiera borraría la petición que debe satisfacer

### 3.2 Ejecuciones Siguientes (Sincronización Automática)

En cada ejecución de `gitpr`:

1. `check_and_update_hooks_scripts()` lee `SCRIPTS_VERSION` y `SCRIPTS_INSTALLED_LANG` desde `.env`
2. Compara con `__scripts_version__` (del código) y el idioma efectivo
3. Si ambos coinciden → no ocurre nada (vía rápida)
4. Si la versión difiere → los hooks se vuelven a descargar en el idioma efectivo
5. Si el idioma difiere → los hooks se vuelven a descargar para coincidir con el nuevo idioma, una sola vez; la ejecución siguiente vuelve a ser la vía rápida
6. En caso de éxito → los marcadores se actualizan para que futuras ejecuciones omitan la red

**Invocaciones protegidas:** La sincronización automática se omite durante llamadas internas del CLI (`--quiet`, `--hook`, `--mcp`) para evitar latencia de red en contextos automatizados.

### 3.3 Grabación Solo con Éxito Total

El marcador `SCRIPTS_VERSION` solo se graba cuando **los 5 hooks** se descargan e instalan con éxito. Si algún hook falla (error de red, descarga parcial), el marcador no se actualiza, garantizando que la instalación fallida se reintente en la próxima ejecución de `gitpr`.

---

## 4. Tipos de Scripts de Hook

El sistema gestiona 5 tipos de hooks de Git:

| Hook | Plantilla de Script | Propósito |
|------|---------------------|-----------|
| `pre-commit` | `pre-commit-template.sh` | Ejecuta el linter estático antes de cada commit |
| `prepare-commit-msg` | `prepare-commit-msg-template.sh` | Genera mensajes de commit con IA |
| `pre-push` | `pre-push-template.sh` | Valida el código antes de enviar al remoto |
| `post-checkout` | `post-checkout-template.sh` | Acciones después de cambiar de rama |
| `post-merge` | `post-merge-template.sh` | Acciones después de una fusión exitosa |

Todos los scripts de hook son **thin shims** — llaman al CLI `gitpr` internamente. La lógica real reside en el código del CLI, no en los archivos de hook. Esto significa que, incluso si los hooks están ligeramente desactualizados, siguen funcionando correctamente porque siempre invocan el CLI más reciente instalado.

---

## 5. Configuración

### 5.1 Variables de Entorno

| Variable | Archivo | Descripción |
|----------|---------|-------------|
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Versión de los scripts de hook instalados (gestionado automáticamente) |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | Idioma de los scripts que están en disco (gestionado automáticamente) |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Idioma que quieres para los hooks. Vacío sigue `GITPR_LANG`. Se edita en la pantalla `gitpr config`, en **Avanzado → Git Hooks** |
| `GITPR_LANG` | `~/.gitpr/.env` | Idioma de interfaz preferido del usuario |

### 5.2 Constantes del Código Fuente

| Constante | Archivo | Descripción |
|-----------|---------|-------------|
| `__scripts_version__` | `src/updater.py` | Versión actual de los scripts de hooks |
| `HOOK_SCRIPT_SUFFIXES` | `src/core.py` | Código del idioma de la interfaz → sufijo del script publicado |
| `effective_hook_lang()` | `src/core.py` | `SCRIPTS_LANG` cuando está definido, el idioma vivo de la interfaz en caso contrario |
| `SCRIPTS_BASE_URL` | `src/core.py` | URL base para descarga de scripts |

### 5.3 Agregar un Nuevo Idioma

Para agregar soporte para un nuevo idioma:

1. Crea 5 archivos `.sh` traducidos en el directorio `scripts/` (uno por tipo de hook)
2. Agrega la correspondencia a `HOOK_SCRIPT_SUFFIXES` en `src/core.py` — la clave es el código de la interfaz (`es_es`), el valor es el sufijo del archivo (`.es`)
3. El sistema de sincronización automática detectará y servirá automáticamente el nuevo idioma

### 5.4 Incrementar la Versión de los Scripts

Cuando se modifiquen los scripts de hook:

1. Incrementa `__scripts_version__` en `src/updater.py`
2. En la próxima ejecución de `gitpr`, todos los clientes instalados detectarán la diferencia y actualizarán sus hooks automáticamente

---

## 6. Solución de Problemas

### Los hooks no se actualizan

**Síntoma:** Ejecutar `gitpr` no actualiza los hooks instalados aunque exista una nueva versión.

**Solución:**
- Verifica que el directorio `.git/hooks` exista en tu proyecto
- Verifica `SCRIPTS_VERSION` en `~/.gitpr/.env` — si coincide con `__scripts_version__`, no se necesita actualización
- Elimina manualmente `SCRIPTS_VERSION` del `.env` para forzar una nueva descarga en la próxima ejecución
- Ejecuta `gitpr --installhooks` para forzar una instalación nueva

### Idioma incorrecto en los hooks

**Síntoma:** Los scripts de hook muestran mensajes en el idioma incorrecto.

**Solución:**
- Verifica `SCRIPTS_LANG` en `~/.gitpr/.env`, o el campo **Idioma de los hooks** en **Avanzado → Git Hooks** de la pantalla `gitpr config`. Vacío sigue `GITPR_LANG`
- Compáralo con `SCRIPTS_INSTALLED_LANG`, que registra lo que hay realmente en disco — que los dos difieran es la señal de que hay una reinstalación pendiente
- Ejecuta `gitpr --installhooks` para reinstalar de inmediato, o simplemente ejecuta cualquier comando `gitpr`: la auto-sincronización reinstala una vez y después vuelve a la vía rápida

### Instalación parcial

**Síntoma:** Algunos hooks están instalados pero `SCRIPTS_VERSION` no se ha grabado.

**Solución:**
- Esto es intencional — el marcador solo se graba cuando los 5 hooks son exitosos
- Verifica tu conexión de red
- Ejecuta `gitpr --installhooks` nuevamente para reintentar las descargas fallidas

---

## 7. Referencia de la API

### `check_and_update_hooks_scripts()`

```python
# src/core.py
def check_and_update_hooks_scripts():
    """Silent auto-sync of installed Git hooks (version + language gated).

    Called on every gitpr execution. Compares SCRIPTS_VERSION and
    SCRIPTS_INSTALLED_LANG in ~/.gitpr/.env against the shipped version
    and the wanted language. When they match the check is a single
    .env read with no network I/O.

    The language comparison is between what is ON DISK and what is
    WANTED, two independent sources: switching SCRIPTS_LANG on the
    configuration screen reinstalls once, and the next run goes back to
    the fast path.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the wanted language.
    On success the markers are stamped so future runs skip the network.
    """
```

### `install_git_hooks()`

```python
# src/core.py
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Installs the hooks in the effective language — SCRIPTS_LANG when the
    user chose one, the interface language otherwise — trying the
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh)
    and falling back to the English base version when a translation is
    unavailable.

    After a successful install, stamps SCRIPTS_VERSION and
    SCRIPTS_INSTALLED_LANG in ~/.gitpr/.env so the auto-sync check can
    skip network calls. SCRIPTS_LANG is NOT written here: it is the
    user's choice, and comparing a choice against itself could never
    detect a language change.
    """
```

### `effective_hook_lang()`

```python
# src/core.py
def effective_hook_lang():
    """The language the hooks should be installed in.

    SCRIPTS_LANG is the user's choice, set on the configuration screen;
    empty means "follow the interface language". It is read from the FILE
    rather than os.getenv() because load_dotenv(override=False) lets a
    variable exported in the shell beat the value the user just edited.
    """
```

---

## 8. Decisiones de Diseño

- **Marcador de versión independiente:** `__scripts_version__` está separado de `__lang_version__` porque los scripts de hooks cambian en una cadencia diferente a los recursos de idioma
- **Dos marcadores de idioma, no uno:** `SCRIPTS_LANG` es la petición y `SCRIPTS_INSTALLED_LANG` es lo que el instalador dejó en disco. La auto-sincronización los compara, así que cambiar de idioma reinstala una vez y después se estabiliza. Un único marcador — escrito por el instalador y comparado consigo mismo — mantenía a los usuarios en el idioma con el que empezaron, por muchas veces que cambiaran el ajuste
- **El instalador nunca escribe la petición:** sobrescribiría justo el valor que debe satisfacer, y la comparación se convertiría en una tautología
- **El idioma de la interfaz se lee en vivo:** `core.py` guarda una copia de `i18n.CURRENT_LANG` desde el momento de la importación, y `set_lang()` (lo que llama `--lang`) reasigna el original. "Seguir el idioma de la interfaz" lo lee en el momento de la llamada, así que `gitpr --lang fr_fr` instala hooks en francés
- **Enfoque de lista blanca:** Solo los 4 códigos mapeados (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) activan descargas específicas de idioma; cualquier otro idioma utiliza el inglés (sin cascada 404). El mapa es explícito porque el código de la interfaz y el sufijo del archivo no coinciden — `es_es` se publica como `.es`
- **Marcador global (no por proyecto):** El marcador `SCRIPTS_VERSION` reside en `~/.gitpr/.env` (global). Después de un incremento de versión, el primer proyecto que ejecuta `gitpr` se actualiza y graba el marcador; los hooks de otros proyectos se actualizan en su próxima ejecución de `gitpr`. Como los hooks son thin shims, los hooks desactualizados siguen funcionando — la lógica real reside en el CLI
- **Sincronización protegida:** La sincronización automática se omite durante invocaciones `--quiet`, `--hook` y `--mcp` para evitar latencia de red en contextos automatizados
