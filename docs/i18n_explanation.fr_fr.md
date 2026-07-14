# Internationalisation (i18n) dans GitPR — Guide du développeur

## Vue d'ensemble

GitPR utilise un moteur d'internationalisation (i18n) personnalisé inspiré du **helper `__()` de Laravel**. Toutes les chaînes affichées à l'utilisateur sont écrites en **anglais** comme clés, et les traductions sont chargées à partir de fichiers JSON au moment de l'exécution. Le système détecte automatiquement la langue du système d'exploitation et utilise l'anglais comme fallback lorsqu'aucune traduction n'est disponible.

---

## Architecture

### Fichiers principaux

| Fichier | Finalité |
|---|---|
| `src/i18n.py` | Moteur de traduction : fonction `__()`, détection de langue, chargement de JSON |
| `src/updater.py` | Définit `__lang_version__` — contrôle l'invalidation du cache de traductions |
| `langs/pt_br.json` | Traductions pour le portugais (Brésil) — paires clé-valeur (EN → PT-BR) |
| `~/.gitpr/langs/{lang_code}.json` | Cache local des traductions de l'utilisateur (téléchargé à la première exécution) |
| `~/.gitpr/.env` | Stocke `GITPR_LANG` (forcer la langue) et `LANG_VERSION` (version du cache) |

### Comment ça fonctionne

```
1. i18n.py se charge au moment de l'importation du module
2. get_system_language() détecte le locale du SE (ex : pt_BR, es_ES) ou lit GITPR_LANG depuis .env
3. get_translations() charge le fichier JSON depuis ~/.gitpr/langs/{lang}.json
   - Si le fichier n'existe pas ou est obsolète (LANG_VERSION != __lang_version__) → télécharge depuis GitHub
   - Si la langue est l'anglais → retourne un dictionnaire vide (pas besoin de traduction)
   - Si le téléchargement échoue et qu'un fichier local existe → utilise la version en cache
4. Le dictionnaire TRANSLATIONS est conservé en mémoire pendant la session
5. Fonction __() : cherche la clé → retourne la traduction (ou la clé elle-même comme fallback)
```

### La fonction `__()`

```python
def __(key, **kwargs):
    """
    Moteur de traduction inspiré de Laravel.
    Tente de trouver la clé dans le dictionnaire. Si elle est introuvable, retourne la clé elle-même (anglais).
    """
    text = TRANSLATIONS.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
```

**Caractéristiques principales :**
- **Clé = fallback en anglais** — s'il n'existe pas de traduction, la chaîne en anglais est affichée directement
- **Placeholders nommés** — prend en charge `str.format()` de Python avec des arguments nommés
- **Formatage sûr** — si un placeholder est manquant, utilise silencieusement la chaîne originale

---

## Comment utiliser `__()` dans le code

### Utilisation de base (chaînes statiques)

```python
from src.i18n import __

# Avant (anglais en dur) :
click.secho("✅ File saved successfully!", fg="green")

# Après (prêt pour i18n) :
click.secho(__("✅ File saved successfully!"), fg="green")
```

### Avec placeholders (valeurs dynamiques)

```python
# Placeholder unique
click.echo(__("Downloading {file_name}...", file_name="template.md"))

# Plusieurs placeholders
click.secho(__("🤖 GitPR is analyzing your code using {provider} ({model})...",
               provider="Gemini", model="gemini-2.5-flash"), fg="cyan")
```

### Dans les décorateurs de Click

```python
@click.option('-c', '--commit', is_flag=True,
              help=__("Generates only the commit message and displays it in the console."))
```

### Dans les attributs de classe (attention à l'ordre d'importation)

```python
class IssueApp(App):
    TITLE = __("GitPR - Issue Generator")  # Fonctionne ! __() s'exécute au moment de la définition de la classe
```

### Dans les composants Textual TUI

```python
BINDINGS = [
    Binding("f2", "save_local", __("Save Local")),
    Binding("f3", "create_issue", __("Create on GitHub")),
]
```

### Pour les comparaisons de chaînes (réponses de l'IA, clés de cache)

**⚠️ Important :** N'utilisez jamais `__()` pour les comparaisons de chaînes ! La fonction renvoie la valeur traduite (ex : portugais), ce qui casserait les comparaisons. Utilisez plutôt une liste de variations possibles dans les deux langues :

```python
# CORRECT — vérifie plusieurs variations de langue
_no_commits = [
    "No exclusive commits",
    "No exclusive commits found",
    "Nenhum commit exclusivo",
    "Nenhum commit exclusivo encontrado",
]
_no_commits_found = any(phrase in context_text for phrase in _no_commits)
```

---

## Comment ajouter des traductions

### 1. Ajoutez la clé de traduction au `langs/pt_br.json`

```json
{
    "✅ File saved successfully!": "✅ Arquivo salvo com sucesso!",
    "Downloading {file_name}...": "A baixar {file_name}..."
}
```

La clé est la **chaîne exacte en anglais** utilisée dans le code. La valeur est la traduction en portugais.

### 2. Les placeholders doivent correspondre

Si la clé en anglais a `{file_name}`, la traduction en portugais doit également utiliser `{file_name}` :

```json
{
    "Downloading {file_name}...": "A baixar {file_name}..."
}
```

### 3. Pas de clés dupliquées

JSON ne prend pas en charge les clés dupliquées. Utilisez le script de vérification :

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

## Comment ajouter une nouvelle langue

1. Créez le fichier JSON : `langs/{lang_code}.json` (ex : `langs/es_ES.json`)
2. Ajoutez toutes les paires clé-valeur avec des clés en anglais et des valeurs traduites
3. Faites un commit du fichier — il sera servi depuis `https://raw.githubusercontent.com/natanfiuza/gitpr/main/langs/`
4. Le moteur i18n le télécharge automatiquement à la première utilisation pour ce locale

---

## Priorité de détection de langue

1. **`.env` `GITPR_LANG`** — s'il est défini, force une langue spécifique (ex : `GITPR_LANG=pt_br`)
2. **Locale du SE** — détecté automatiquement via `locale.getdefaultlocale()` (ex : `pt_BR`, `es_ES`)
3. **Fallback** — `"en_us"` (anglais, ne nécessite pas de fichier de traduction)

Pour forcer l'anglais : définissez `GITPR_LANG=en` dans `~/.gitpr/.env` ou supprimez la variable.

---

## Contrôle de version des traductions

- `__lang_version__` dans `src/updater.py` est incrémenté lorsque les traductions changent
- À chaque exécution, si le `LANG_VERSION` local != `__lang_version__`, le fichier de traduction est re-téléchargé
- Cela garantit que les utilisateurs ont toujours les traductions les plus récentes sans mises à jour manuelles

---

## Précautions avec les importations circulaires

Le module i18n importe `__lang_version__` depuis `updater.py`. Par conséquent :

- **`updater.py`** NE doit PAS importer `__` en haut — utilise des lazy imports à l'intérieur des fonctions
- **`cache.py`** NE doit PAS importer `__` en haut — utilise des lazy imports à l'intérieur des fonctions qui en ont besoin
- Les autres modules peuvent importer `__` en haut en toute sécurité

```python
# NE faites PAS ceci dans updater.py ou cache.py :
from src.i18n import __

# FAITES plutôt ceci (à l'intérieur de la fonction qui en a besoin) :
def some_function():
    from src.i18n import __  # lazy import
    click.secho(__("message"))
```

---

## i18n dans les URLs de documentation

La fonction `get_doc_url()` dans `core.py` construit des URLs de documentation avec un suffixe de langue :

```python
from src.i18n import CURRENT_LANG

def get_doc_url(filename):
    if CURRENT_LANG.startswith("en"):
        return f"https://github.com/.../docs/{filename}"
    else:
        base, ext = filename.rsplit(".", 1)
        return f"https://github.com/.../docs/{base}.{CURRENT_LANG}.{ext}"

# Utilisation :
get_doc_url("issue-tui-help.md")
# EN → "https://github.com/.../docs/issue-tui-help.md"
# PT → "https://github.com/.../docs/issue-tui-help.pt_br.md"
```

---

## Checklist résumé pour les nouvelles fonctionnalités

Lors de l'ajout de nouveau texte affiché à l'utilisateur :

- [ ] Utiliser `__("English text here")` pour TOUS les appels click.secho, click.echo, click.prompt
- [ ] Ajouter la paire anglais→portugais au `langs/pt_br.json`
- [ ] Utiliser le format `{placeholder}` avec des arguments nommés (jamais de f-strings à l'intérieur de `__()`)
- [ ] Pour les comparaisons de chaînes, utiliser des listes de variations dans plusieurs langues (pas `__()`)
- [ ] Garantir que `updater.py` et `cache.py` utilisent des lazy imports de `__`
- [ ] Tester avec `GITPR_LANG=pt_br` et `GITPR_LANG=en` pour vérifier les deux langues
- [ ] Incrémenter `__lang_version__` dans `updater.py` si les traductions changent significativement
