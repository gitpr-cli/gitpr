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
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Rastrea el idioma de los scripts instalados (ej.: `es`, `pt_br`) |

### 2.2 Flujo de Sincronización Automática

```
ejecución de gitpr
    │
    ├─ Lee SCRIPTS_VERSION y SCRIPTS_LANG desde ~/.gitpr/.env
    │
    ├─ Compara con __scripts_version__ y CURRENT_LANG
    │
    ├─ ¿Coinciden? → Omitir (vía rápida — lectura única del .env, sin red)
    │
    └─ ¿Difieren o faltan? → Descargar e instalar hooks en el idioma actual
                              → Grabar SCRIPTS_VERSION + SCRIPTS_LANG
```

La vía rápida (cuando las versiones coinciden) es una única lectura del archivo `.env` con cero E/S de red.

### 2.3 Idiomas Soportados

| Idioma | Código | Sufijo del Script | Ejemplo |
|--------|--------|-------------------|---------|
| Inglés (predeterminado) | `en` | *(sin sufijo)* | `pre-commit-template.sh` |
| Portugués (Brasil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Portugués (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Francés | `fr` | `.fr` | `pre-commit-template.fr.sh` |
| Español | `es` | `.es` | `pre-commit-template.es.sh` |

El inglés es el idioma predeterminado y de respaldo. Si un script en un idioma específico no se encuentra en el servidor (HTTP 404), el sistema utiliza automáticamente la versión en inglés.

---

## 3. Cómo Funciona

### 3.1 Primera Ejecución (Sin Hooks Instalados)

Cuando un usuario ejecuta `gitpr --installhooks` o `gitpr --install` por primera vez:

1. GitPR detecta el idioma actual (`CURRENT_LANG`) desde el SO o `.env`
2. Descarga primero los scripts específicos del idioma (ej.: `pre-commit-template.es.sh`)
3. Utiliza el respaldo en inglés si la variante de idioma no está disponible (HTTP 404)
4. Aplica permisos de ejecución (`chmod +x`)
5. Graba `SCRIPTS_VERSION` y `SCRIPTS_LANG` en `~/.gitpr/.env`

### 3.2 Ejecuciones Siguientes (Sincronización Automática)

En cada ejecución de `gitpr`:

1. `check_and_update_hooks_scripts()` lee `SCRIPTS_VERSION` y `SCRIPTS_LANG` desde `.env`
2. Compara con `__scripts_version__` (del código) y `CURRENT_LANG`
3. Si ambos coinciden → no ocurre nada (vía rápida)
4. Si la versión difiere → los hooks se vuelven a descargar en el idioma actual
5. Si el idioma difiere → los hooks se vuelven a descargar para coincidir con el nuevo idioma
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
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Idioma de los scripts instalados (gestionado automáticamente) |
| `GITPR_LANG` | `~/.gitpr/.env` | Idioma de interfaz preferido del usuario |

### 5.2 Constantes del Código Fuente

| Constante | Archivo | Descripción |
|-----------|---------|-------------|
| `__scripts_version__` | `src/updater.py` | Versión actual de los scripts de hooks |
| `_SCRIPT_LANG_SUFFIXES` | `src/core.py` | Conjunto de sufijos de idioma soportados |
| `SCRIPTS_BASE_URL` | `src/core.py` | URL base para descarga de scripts |

### 5.3 Agregar un Nuevo Idioma

Para agregar soporte para un nuevo idioma:

1. Crea 5 archivos `.sh` traducidos en el directorio `scripts/` (uno por tipo de hook)
2. Agrega el código de idioma a `_SCRIPT_LANG_SUFFIXES` en `src/core.py`
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
- Verifica `GITPR_LANG` en `~/.gitpr/.env`
- Elimina `SCRIPTS_LANG` del `.env` para forzar la redetección del idioma
- Ejecuta `gitpr --installhooks` para reinstalar en el idioma correcto

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
    SCRIPTS_LANG in ~/.gitpr/.env against the shipped constants. When
    they match the check is a single .env read with no network I/O.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the current language.
    On success the markers are stamped so future runs skip the network.
    """
```

### `install_git_hooks()`

```python
# src/core.py
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Detects the current language (CURRENT_LANG) and tries to download
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh).
    Falls back to the English base version when a translation is unavailable.

    After a successful install, stamps SCRIPTS_VERSION and SCRIPTS_LANG
    in ~/.gitpr/.env so the auto-sync check can skip network calls.

    Returns True when all 5 hooks installed successfully.
    """
```

---

## 8. Decisiones de Diseño

- **Marcador de versión independiente:** `__scripts_version__` está separado de `__lang_version__` porque los scripts de hooks cambian en una cadencia diferente a los recursos de idioma
- **Marcador complementario `SCRIPTS_LANG`:** Evita el cambio de idioma cuando los usuarios ejecutan `gitpr --lang fr` una vez — la sincronización automática no vuelve a descargar a menos que la versión O el idioma difieran
- **Enfoque de lista blanca:** Solo 4 sufijos explícitos (`pt_br`, `pt_pt`, `fr`, `es`) activan descargas específicas de idioma; cualquier otro idioma utiliza el inglés (sin cascada 404)
- **Marcador global (no por proyecto):** El marcador `SCRIPTS_VERSION` reside en `~/.gitpr/.env` (global). Después de un incremento de versión, el primer proyecto que ejecuta `gitpr` se actualiza y graba el marcador; los hooks de otros proyectos se actualizan en su próxima ejecución de `gitpr`. Como los hooks son thin shims, los hooks desactualizados siguen funcionando — la lógica real reside en el CLI
- **Sincronización protegida:** La sincronización automática se omite durante invocaciones `--quiet`, `--hook` y `--mcp` para evitar latencia de red en contextos automatizados
