# Marqueurs de Version (Ressources OTA)

GitPR distribue plusieurs ressources **en dehors** du paquet publié — traductions, mots du
spinner, listes de smart-excludes, préréglages de linter et scripts de Git hooks. Elles
résident sur GitHub et sont récupérées over the air (OTA) afin de pouvoir être corrigées
sans publier une nouvelle version.

Un **Marqueur de Version** (*Version Marker*) est le mécanisme qui détermine *quand* une
copie en cache est obsolète.

---

## 1. Fonctionnement du modèle

Chaque marqueur est une simple clé dans le fichier global `~/.gitpr/.env` de l'utilisateur.
Il enregistre **quelle version du code a téléchargé cette ressource pour la dernière fois** :

```dotenv
LANG_VERSION=v0.0.39
SMART_EXCLUDES_VERSION=v0.0.39
THINKING_WORDS_VERSION=v0.0.39
LINTER_PRESETS_VERSION=v0.0.39
SCRIPTS_VERSION=v0.0.4
```

À l'exécution, le chargeur de la ressource compare le marqueur à la constante faisant
autorité dans [`src/updater.py`](../src/updater.py) :

```python
needs_update = os.getenv("LINTER_PRESETS_VERSION") != __lang_version__
```

* **Égal** → la copie locale est à jour ; elle est utilisée sans appel réseau.
* **Différent ou absent** → télécharge le modèle distant, écrase la copie locale, puis
  réécrit le marqueur avec `set_key(...)`.

Comme le marqueur n'est écrit **qu'après** un téléchargement réussi, un échec laisse le
marqueur obsolète et l'exécution suivante réessaie. Chaque chargeur conserve également une
chaîne de repli hors ligne, de sorte qu'un échec de téléchargement bascule sur la copie
précédente au lieu d'interrompre la commande.

> Les marqueurs ne sont **pas** initialisés dans `DEFAULT_CONFIG` au sein de `src/config.py`.
> Ils sont écrits à la demande par le chargeur qui en est propriétaire. Un marqueur absent
> signifie simplement « jamais téléchargé », ce qui déclenche correctement la première récupération.

---

## 2. Les marqueurs

| Marqueur | Ressource | Cache local | Comparé à | Propriétaire |
| --- | --- | --- | --- | --- |
| `LANG_VERSION` | Dictionnaires de traduction | `~/.gitpr/langs/{lang}.json` | `__lang_version__` | [`src/i18n.py`](../src/i18n.py) |
| `SMART_EXCLUDES_VERSION` | Exclusions pathspec du diff | `~/.gitpr/conf/gitpr.smart-excludes.json` | `__lang_version__` | [`src/core.py`](../src/core.py) |
| `THINKING_WORDS_VERSION` | Mots de réflexion du spinner | `~/.gitpr/.env` (`SPINNER_THINKING_WORDS`) | `__lang_version__` | [`src/spinner.py`](../src/spinner.py) |
| `LINTER_PRESETS_VERSION` | Préréglages de linters externes | `~/.gitpr/conf/gitpr.linter-presets.json` | `__lang_version__` | [`src/linter_wizard.py`](../src/linter_wizard.py) |
| `SCRIPTS_VERSION` | Scripts de Git hooks | `.git/hooks/` | `__scripts_version__` | [`src/core.py`](../src/core.py) |

Quatre des cinq marqueurs sont comparés à `__lang_version__`, de sorte qu'une seule
incrémentation les rafraîchit en bloc. Les scripts de hooks sont versionnés indépendamment
par `__scripts_version__` car ils évoluent selon une cadence différente.

---

## 3. `LINTER_PRESETS_VERSION`

Suit [`templates/gitpr.linter-presets.json`](../templates/gitpr.linter-presets.json), le
catalogue de définitions prêtes à l'emploi de linters externes proposé par `gitpr --linter-setup`
(ponts compatibles Checkstyle : ESLint, PHPCS, Checkstyle, etc.).

Son objectif est de permettre à **de nouveaux linters d'atteindre les installations existantes sans nouvelle release**.
Ajouter un préréglage au modèle suffit — le prochain `--linter-setup` sur un client dont le
marqueur est obsolète re-télécharge le catalogue.

Chaîne de résolution dans `_load_linter_presets()` :

1. Copie locale dans `~/.gitpr/conf/gitpr.linter-presets.json`, lorsque
   `LINTER_PRESETS_VERSION == __lang_version__`.
2. Nouveau téléchargement depuis le modèle distant — copie locale écrite, marqueur mis à jour.
3. Copie locale obsolète, lorsque le téléchargement échoue (hors ligne).
4. Constante intégrée `_LINTER_PRESETS`, en dernier recours.

> **À ne pas confondre avec la version de release de GitPR.** `__version__` (`1.5.0`)
> identifie le CLI lui-même ; `LINTER_PRESETS_VERSION` enregistre uniquement quel instantané
> du catalogue de préréglages est mis en cache localement. Les deux évoluent indépendamment.

---

## 4. Incrémenter un marqueur

Les marqueurs dans `.env` sont écrits par GitPR — **ne les modifiez jamais à la main**.
Ce que vous modifiez est la constante dans [`src/updater.py`](../src/updater.py) à laquelle
ils sont comparés :

```python
__lang_version__ = "v0.0.39"     # traductions, smart excludes, thinking words, linter presets
__scripts_version__ = "v0.0.4"   # scripts de Git hooks
```

Pour publier une modification sur toute ressource adossée à `__lang_version__` :

1. **Fusionnez d'abord la modification du modèle sur `main`.** Les clients téléchargent depuis
   `raw.githubusercontent.com/natanfiuza/gitpr/main/...`, le nouveau contenu doit donc déjà
   s'y trouver.
2. **Ensuite**, incrémentez `__lang_version__` et publiez la release.

Procéder dans l'ordre inverse fige les clients sur *l'ancien* fichier sous le *nouveau*
marqueur : ils téléchargent ce que `main` sert à ce moment-là, estampillent la nouvelle
version et ne réessaient jamais — le correctif n'arrive silencieusement jamais.

### Liste de contrôle

- [ ] Modèle mis à jour et fusionné sur `main`
- [ ] `__lang_version__` (ou `__scripts_version__`) incrémenté dans `src/updater.py`
- [ ] Modification vérifiée sur un client ayant un marqueur obsolète
- [ ] Parité de `langs/*.json` toujours au vert (`pytest tests/test_i18n.py`)

---

## 5. Voir aussi

* [ARCHITECTURE.fr_fr.md](ARCHITECTURE.fr_fr.md) — §16 Marqueurs de Version
* [hooks-versioning.fr_fr.md](hooks-versioning.fr_fr.md) — spécificités de `SCRIPTS_VERSION`
* [linter-regras-customizadas.fr_fr.md](linter-regras-customizadas.fr_fr.md) — préréglages de linter et `--linter-setup`
