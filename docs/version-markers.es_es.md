# Marcadores de Versión (Recursos OTA)

GitPR distribuye varios recursos **fuera** del paquete publicado — traducciones, palabras del
spinner, listas de smart-excludes, presets de linter y scripts de Git hooks. Viven en
GitHub y se descargan over the air (OTA) para que puedan corregirse sin necesidad de
publicar una nueva release.

Un **Marcador de Versión** (*Version Marker*) es el mecanismo que decide *cuándo* una copia
en caché está desactualizada.

---

## 1. Cómo funciona el patrón

Cada marcador es una clave simple en el archivo global `~/.gitpr/.env` del usuario. Registra
**qué versión del código descargó ese recurso por última vez**:

```dotenv
LANG_VERSION=v0.0.39
SMART_EXCLUDES_VERSION=v0.0.39
THINKING_WORDS_VERSION=v0.0.39
LINTER_PRESETS_VERSION=v0.0.39
SCRIPTS_VERSION=v0.0.4
```

En tiempo de ejecución, el cargador del recurso compara el marcador con la constante
autoritativa en [`src/updater.py`](../src/updater.py):

```python
needs_update = os.getenv("LINTER_PRESETS_VERSION") != __lang_version__
```

* **Igual** → la copia local está actualizada; se utiliza sin realizar llamadas de red.
* **Diferente o ausente** → descarga la plantilla remota, sobrescribe la copia local y
  guarda el marcador con `set_key(...)`.

Dado que el marcador solo se escribe **después** de una descarga exitosa, una descarga
fallida lo deja desactualizado y la siguiente ejecución lo reintenta. Cada cargador también
mantiene una cadena de respaldo offline, por lo que un fallo de descarga degrada a la
copia anterior en lugar de interrumpir el comando.

> Los marcadores **no** se inicializan en `DEFAULT_CONFIG` dentro de `src/config.py`. Son
> escritos bajo demanda por el cargador propietario. Un marcador ausente significa
> simplemente "nunca descargado", lo que activa correctamente la primera descarga.

---

## 2. Los marcadores

| Marcador | Recurso | Caché local | Comparado con | Propietario |
| --- | --- | --- | --- | --- |
| `LANG_VERSION` | Diccionarios de traducción | `~/.gitpr/langs/{lang}.json` | `__lang_version__` | [`src/i18n.py`](../src/i18n.py) |
| `SMART_EXCLUDES_VERSION` | Exclusiones pathspec del diff | `~/.gitpr/conf/gitpr.smart-excludes.json` | `__lang_version__` | [`src/core.py`](../src/core.py) |
| `THINKING_WORDS_VERSION` | Palabras de pensamiento del spinner | `~/.gitpr/.env` (`SPINNER_THINKING_WORDS`) | `__lang_version__` | [`src/spinner.py`](../src/spinner.py) |
| `LINTER_PRESETS_VERSION` | Presets de linters externos | `~/.gitpr/conf/gitpr.linter-presets.json` | `__lang_version__` | [`src/linter_wizard.py`](../src/linter_wizard.py) |
| `SCRIPTS_VERSION` | Scripts de Git hooks | `.git/hooks/` | `__scripts_version__` | [`src/core.py`](../src/core.py) |

Cuatro de los cinco se comparan con `__lang_version__`, de modo que un solo incremento los
actualiza en bloque. Los scripts de hooks se versionan de forma independiente mediante
`__scripts_version__` porque cambian con una cadencia distinta.

---

## 3. `LINTER_PRESETS_VERSION`

Rastrea [`templates/gitpr.linter-presets.json`](../templates/gitpr.linter-presets.json),
el catálogo de definiciones listas para usar de linters externos que ofrece `gitpr --linter-setup`
(puentes compatibles con Checkstyle: ESLint, PHPCS, Checkstyle, etc.).

Su propósito es permitir que **nuevos linters lleguen a las instalaciones existentes sin una release**.
Basta con añadir un preset a la plantilla — el siguiente `--linter-setup` en un cliente cuyo
marcador esté desactualizado volverá a descargar el catálogo.

Cadena de resolución en `_load_linter_presets()`:

1. Copia local en `~/.gitpr/conf/gitpr.linter-presets.json`, cuando
   `LINTER_PRESETS_VERSION == __lang_version__`.
2. Descarga fresca desde la plantilla remota — se guarda la copia local y se actualiza el marcador.
3. Copia local desactualizada, cuando falla la descarga (offline).
4. Constante integrada `_LINTER_PRESETS`, como último recurso.

> **No debe confundirse con la versión de release de GitPR.** `__version__` (`1.5.0`)
> identifica al propio CLI; `LINTER_PRESETS_VERSION` solo registra qué instantánea del
> catálogo de presets está almacenada en la caché local. Ambos avanzan de forma independiente.

---

## 4. Incrementar un marcador

Los marcadores en `.env` los escribe GitPR — **nunca los edites a mano**. Lo que se cambia
es la constante en [`src/updater.py`](../src/updater.py) contra la cual se comparan:

```python
__lang_version__ = "v0.0.39"     # traducciones, smart excludes, thinking words, linter presets
__scripts_version__ = "v0.0.4"   # scripts de Git hooks
```

Para publicar un cambio en cualquier recurso respaldado por `__lang_version__`:

1. **Fusiona primero el cambio de la plantilla en `main`.** Los clientes descargan desde
   `raw.githubusercontent.com/natanfiuza/gitpr/main/...`, por lo que el contenido nuevo ya
   debe estar allí.
2. **Después** incrementa `__lang_version__` y publica la release.

Hacerlo en el orden inverso fija a los clientes al archivo *antiguo* bajo el marcador *nuevo*:
descargan lo que `main` sirva en ese momento, estampan la nueva versión y nunca vuelven a
intentarlo — la corrección silenciosamente nunca llega.

### Lista de verificación

- [ ] Plantilla actualizada y fusionada en `main`
- [ ] `__lang_version__` (o `__scripts_version__`) incrementado en `src/updater.py`
- [ ] Cambio verificado en un cliente con marcador desactualizado
- [ ] Paridad de `langs/*.json` sigue en verde (`pytest tests/test_i18n.py`)

---

## 5. Relacionado

* [ARCHITECTURE.es_es.md](ARCHITECTURE.es_es.md) — §16 Marcadores de Versión
* [hooks-versioning.es_es.md](hooks-versioning.es_es.md) — detalles de `SCRIPTS_VERSION`
* [linter-regras-customizadas.es_es.md](linter-regras-customizadas.es_es.md) — presets de linter y `--linter-setup`
