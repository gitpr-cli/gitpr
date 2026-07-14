# Internacionalización (i18n) en GitPR — Guía del Desarrollador

## Visión General

GitPR utiliza un motor de internacionalización (i18n) personalizado inspirado en el **helper `__()` de Laravel**. Todas las cadenas mostradas al usuario se escriben en **inglés** como claves, y las traducciones se cargan de archivos JSON en tiempo de ejecución. El sistema detecta automáticamente el idioma del sistema operativo y usa el inglés como fallback cuando no hay traducción disponible.

---

## Arquitectura

### Archivos principales

| Archivo | Finalidad |
|---|---|
| `src/i18n.py` | Motor de traducción: función `__()`, detección de idioma, carga de JSON |
| `src/updater.py` | Define `__lang_version__` — controla la invalidación de la caché de traducciones |
| `langs/pt_br.json` | Traducciones para portugués (Brasil) — pares clave-valor (EN → PT-BR) |
| `~/.gitpr/langs/{lang_code}.json` | Caché local de traducciones del usuario (descargada en la primera ejecución) |
| `~/.gitpr/.env` | Almacena `GITPR_LANG` (forzar idioma) y `LANG_VERSION` (versión de la caché) |

### Cómo funciona

```
1. i18n.py se carga en el momento de la importación del módulo
2. get_system_language() detecta el locale del SO (ej: pt_BR, es_ES) o lee GITPR_LANG del .env
3. get_translations() carga el archivo JSON de ~/.gitpr/langs/{lang}.json
   - Si el archivo no existe o está desactualizado (LANG_VERSION != __lang_version__) → descarga de GitHub
   - Si el idioma es inglés → devuelve un diccionario vacío (no necesita traducción)
   - Si la descarga falla y existe un archivo local → usa la versión en caché
4. El diccionario TRANSLATIONS se mantiene en memoria durante la sesión
5. Función __(): busca la clave → devuelve la traducción (o la propia clave como fallback)
```

### La función `__()`

```python
def __(key, **kwargs):
    """
    Motor de Traducción inspirado en Laravel.
    Intenta encontrar la clave en el diccionario. Si no la encuentra, devuelve la propia clave (inglés).
    """
    text = TRANSLATIONS.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
```

**Características principales:**
- **Clave = fallback en inglés** — si no existe traducción, la cadena en inglés se muestra directamente
- **Placeholders con nombre** — soporta `str.format()` de Python con argumentos nombrados
- **Formateo seguro** — si falta un placeholder, usa silenciosamente la cadena original

---

## Cómo usar `__()` en el código

### Uso básico (cadenas estáticas)

```python
from src.i18n import __

# Antes (inglés hardcodeado):
click.secho("✅ File saved successfully!", fg="green")

# Después (i18n-ready):
click.secho(__("✅ File saved successfully!"), fg="green")
```

### Con placeholders (valores dinámicos)

```python
# Placeholder único
click.echo(__("Downloading {file_name}...", file_name="template.md"))

# Múltiples placeholders
click.secho(__("🤖 GitPR is analyzing your code using {provider} ({model})...",
               provider="Gemini", model="gemini-2.5-flash"), fg="cyan")
```

### En decoradores de Click

```python
@click.option('-c', '--commit', is_flag=True,
              help=__("Generates only the commit message and displays it in the console."))
```

### En atributos de clase (cuidado con el orden de importación)

```python
class IssueApp(App):
    TITLE = __("GitPR - Issue Generator")  # ¡Funciona! __() se ejecuta en el momento de la definición de la clase
```

### En componentes Textual TUI

```python
BINDINGS = [
    Binding("f2", "save_local", __("Save Local")),
    Binding("f3", "create_issue", __("Create on GitHub")),
]
```

### Para comparaciones de cadenas (respuestas de la IA, claves de caché)

**⚠️ Importante:** ¡Nunca uses `__()` para comparaciones de cadenas! La función devuelve el valor traducido (ej.: portugués), lo que rompería las comparaciones. En su lugar, usa una lista de variaciones posibles en ambos idiomas:

```python
# CORRECTO — verifica múltiples variaciones de idioma
_no_commits = [
    "No exclusive commits",
    "No exclusive commits found",
    "Nenhum commit exclusivo",
    "Nenhum commit exclusivo encontrado",
]
_no_commits_found = any(phrase in context_text for phrase in _no_commits)
```

---

## Cómo añadir traducciones

### 1. Añade la clave de traducción a `langs/pt_br.json`

```json
{
    "✅ File saved successfully!": "✅ Arquivo salvo com sucesso!",
    "Downloading {file_name}...": "A baixar {file_name}..."
}
```

La clave es la **cadena exacta en inglés** usada en el código. El valor es la traducción en portugués.

### 2. Los placeholders deben corresponder

Si la clave en inglés tiene `{file_name}`, la traducción en portugués también debe usar `{file_name}`:

```json
{
    "Downloading {file_name}...": "A baixar {file_name}..."
}
```

### 3. Sin claves duplicadas

JSON no soporta claves duplicadas. Usa el script de verificación:

```bash
python -c "
import json, re
from collections import Counter
with open('langs/pt_br.json', 'r') as f: content = f.read()
keys = []
for i, line in enumerate(content.splitlines(), 1):
    m = re.match(r'^\s*\"(.+?)\"\s*:', line)
    if m: keys.append((m.group(1), i))
dupes = {k: v for k, v in Counter(k for k, _ in keys).items() if v > 1}
print(f'Duplicates: {dupes}' if dupes else 'No duplicates!')
"
```

---

## Cómo añadir un nuevo idioma

1. Crea el archivo JSON: `langs/{lang_code}.json` (ej.: `langs/es_ES.json`)
2. Añade todos los pares clave-valor con claves en inglés y valores traducidos
3. Haz commit del archivo — se servirá desde `https://raw.githubusercontent.com/natanfiuza/gitpr/main/langs/`
4. El motor i18n lo descarga automáticamente en el primer uso para ese locale

---

## Prioridad de detección de idioma

1. **`.env` `GITPR_LANG`** — si está definido, fuerza un idioma específico (ej.: `GITPR_LANG=pt_br`)
2. **Locale del SO** — detectado automáticamente mediante `locale.getdefaultlocale()` (ej.: `pt_BR`, `es_ES`)
3. **Fallback** — `"en_us"` (inglés, no necesita archivo de traducción)

Para forzar el inglés: define `GITPR_LANG=en` en `~/.gitpr/.env` o elimina la variable.

---

## Control de versión de las traducciones

- `__lang_version__` en `src/updater.py` se incrementa cuando las traducciones cambian
- En cada ejecución, si el `LANG_VERSION` local != `__lang_version__`, el archivo de traducción se vuelve a descargar
- Esto garantiza que los usuarios tengan siempre las traducciones más recientes sin actualizaciones manuales

---

## Precauciones con importaciones circulares

El módulo i18n importa `__lang_version__` de `updater.py`. Por lo tanto:

- **`updater.py`** NO debe importar `__` en la parte superior — usa lazy imports dentro de las funciones
- **`cache.py`** NO debe importar `__` en la parte superior — usa lazy imports dentro de las funciones que lo necesitan
- Otros módulos pueden importar `__` en la parte superior con seguridad

```python
# NO hagas esto en updater.py o cache.py:
from src.i18n import __

# HAZ esto en su lugar (dentro de la función que lo necesita):
def some_function():
    from src.i18n import __  # lazy import
    click.secho(__("message"))
```

---

## i18n en las URLs de documentación

La función `get_doc_url()` en `core.py` construye URLs de documentación con sufijo de idioma:

```python
from src.i18n import CURRENT_LANG

def get_doc_url(filename):
    if CURRENT_LANG.startswith("en"):
        return f"https://github.com/.../docs/{filename}"
    else:
        base, ext = filename.rsplit(".", 1)
        return f"https://github.com/.../docs/{base}.{CURRENT_LANG}.{ext}"

# Uso:
get_doc_url("issue-tui-help.md")
# EN → "https://github.com/.../docs/issue-tui-help.md"
# PT → "https://github.com/.../docs/issue-tui-help.pt_br.md"
```

---

## Checklist resumen para nuevas funcionalidades

Al añadir nuevo texto mostrado al usuario:

- [ ] Usar `__("English text here")` para TODAS las llamadas click.secho, click.echo, click.prompt
- [ ] Añadir el par inglés→portugués a `langs/pt_br.json`
- [ ] Usar el formato `{placeholder}` con argumentos nombrados (nunca f-strings dentro de `__()`)
- [ ] Para comparaciones de cadenas, usar listas de variaciones en múltiples idiomas (no `__()`)
- [ ] Garantizar que `updater.py` y `cache.py` usen lazy imports de `__`
- [ ] Probar con `GITPR_LANG=pt_br` y `GITPR_LANG=en` para verificar ambos idiomas
- [ ] Incrementar `__lang_version__` en `updater.py` si las traducciones cambian significativamente
