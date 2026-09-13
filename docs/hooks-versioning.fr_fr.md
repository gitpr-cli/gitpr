# Versionnement et Synchronisation Automatique des Scripts de Hooks

Cette documentation détaille l'architecture et le fonctionnement du système de versionnement et de synchronisation automatique des scripts de Git hooks de GitPR. Le système garantit que les scripts de hooks installés dans vos dépôts sont toujours à jour avec la dernière version, en respectant vos préférences linguistiques.

---

## 1. Aperçu

GitPR inclut un système automatique de versionnement pour les scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Chaque fois que vous exécutez `gitpr`, le système vérifie silencieusement si les hooks installés correspondent à la dernière version disponible. Si une nouvelle version est détectée — ou si la langue a été modifiée — les hooks sont automatiquement téléchargés et mis à jour.

Ce mécanisme est indépendant de l'auto-updater principal de GitPR (`--update`) et fonctionne selon une cadence de version distincte, car les scripts de hooks évoluent à un rythme différent du CLI lui-même.

---

## 2. Architecture

### 2.1 Marqueurs de Version

| Marqueur | Emplacement | Objectif |
|----------|-------------|----------|
| `__scripts_version__` | `src/updater.py` | Source unique de vérité — définit la version actuelle des scripts de hooks livrés avec cette version de GitPR |
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Suit la version actuellement installée sur la machine de l'utilisateur |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | **La langue que vous avez demandée.** Vide suit la langue de l'interface. Modifiable sur l'écran `gitpr config` |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | **Ce qui se trouve sur le disque.** Écrit par l'installeur, jamais par l'utilisateur, et affiché en lecture seule sur l'écran de configuration |

Les deux marqueurs de langue sont délibérément séparés. L'auto-synchronisation doit remarquer un changement de langue, et cela exige de comparer ce qui est installé à ce qui est demandé — deux valeurs indépendantes. Un `SCRIPTS_LANG` unique écrit par l'installeur serait comparé à lui-même, ce qui ne peut jamais différer : changer de langue laisserait donc silencieusement les hooks dans l'ancienne.

### 2.2 Flux de Synchronisation Automatique

```
exécution de gitpr
    │
    ├─ Lit SCRIPTS_VERSION et SCRIPTS_INSTALLED_LANG depuis ~/.gitpr/.env
    │
    ├─ Calcule la langue voulue : SCRIPTS_LANG (le choix, depuis le fichier)
    │  ou la langue de l'interface en direct lorsqu'elle est vide
    │
    ├─ Correspondance ? → Ignorer (voie rapide — simple lecture du .env, sans réseau)
    │
    └─ Différence ou absence ? → Télécharger et installer les hooks dans la langue voulue
                                   → Enregistrer SCRIPTS_VERSION + SCRIPTS_INSTALLED_LANG
```

La voie rapide (quand les versions correspondent) est une simple lecture du fichier `.env` sans aucune E/S réseau.

La langue voulue est lue depuis le fichier plutôt que via `os.getenv()`, et la langue de l'interface est lue depuis `src.i18n` au moment de l'appel plutôt que depuis la copie figée qu'en garde ce module — `set_lang()`, que `--lang` appelle, réassigne la constante au lieu de la muter. Sans ces deux points, `gitpr --lang fr_fr` installerait les hooks dans la langue avec laquelle le processus a démarré.

### 2.3 Langues Prises en Charge

L'interface écrit une langue d'une façon et le fichier publié d'une autre, et les deux ne sont pas interchangeables : `GITPR_LANG` et `SCRIPTS_LANG` contiennent `es_es`/`fr_fr` alors que les fichiers sur le serveur sont nommés `.es`/`.fr`. `HOOK_SCRIPT_SUFFIXES` dans `src/core.py` est cette correspondance, et rien d'autre ne doit présumer que les deux côtés concordent.

| Langue | Code interface / `SCRIPTS_LANG` | Suffixe du Script | Exemple |
|--------|--------------------------------|-------------------|---------|
| Anglais (défaut) | `en_us` | *(sans suffixe)* | `pre-commit-template.sh` |
| Portugais (Brésil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Portugais (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Espagnol | `es_es` | `.es` | `pre-commit-template.es.sh` |
| Français | `fr_fr` | `.fr` | `pre-commit-template.fr.sh` |

Un code absent de cette correspondance installe le script de base, qui est l'anglais. L'anglais est aussi le repli lorsqu'un script spécifique à une langue est manquant sur le serveur (HTTP 404).

---

## 3. Fonctionnement

### 3.1 Première Exécution (Sans Hooks Installés)

Lorsqu'un utilisateur exécute `gitpr --installhooks` ou `gitpr --install` pour la première fois :

1. GitPR résout la langue effective : `SCRIPTS_LANG` lorsque vous en avez choisi une, la langue de l'interface en direct sinon
2. Télécharge d'abord les scripts spécifiques à la langue (ex. : `pre-commit-template.fr.sh`)
3. Utilise le repli en anglais si la variante linguistique n'est pas disponible (HTTP 404)
4. Applique les permissions d'exécution (`chmod +x`)
5. Enregistre `SCRIPTS_VERSION` et `SCRIPTS_INSTALLED_LANG` dans `~/.gitpr/.env`. `SCRIPTS_LANG` n'est **pas** écrit — c'est votre choix, et un installeur qui l'écraserait effacerait la demande qu'il est censé satisfaire

### 3.2 Exécutions Suivantes (Synchronisation Automatique)

À chaque exécution de `gitpr` :

1. `check_and_update_hooks_scripts()` lit `SCRIPTS_VERSION` et `SCRIPTS_INSTALLED_LANG` depuis `.env`
2. Compare avec `__scripts_version__` (du code) et la langue effective
3. Si les deux correspondent → rien ne se passe (voie rapide)
4. Si la version diffère → les hooks sont re-téléchargés dans la langue effective
5. Si la langue diffère → les hooks sont re-téléchargés pour correspondre à la nouvelle langue, une seule fois ; l'exécution suivante reprend la voie rapide
6. En cas de succès → les marqueurs sont mis à jour pour que les exécutions futures ignorent le réseau

**Invocation protégée :** La synchronisation automatique est ignorée lors des appels CLI internes (`--quiet`, `--hook`, `--mcp`) pour éviter la latence réseau dans les contextes automatisés.

### 3.3 Enregistrement Uniquement en Cas de Succès Total

Le marqueur `SCRIPTS_VERSION` n'est enregistré que lorsque **les 5 hooks** sont téléchargés et installés avec succès. Si un hook échoue (erreur réseau, téléchargement partiel), le marqueur n'est pas mis à jour, garantissant que l'installation échouée sera réessayée lors de la prochaine exécution de `gitpr`.

---

## 4. Types de Scripts de Hook

Le système gère 5 types de hooks Git :

| Hook | Template de Script | Objectif |
|------|-------------------|----------|
| `pre-commit` | `pre-commit-template.sh` | Exécute le linter statique avant chaque commit |
| `prepare-commit-msg` | `prepare-commit-msg-template.sh` | Génère des messages de commit avec IA |
| `pre-push` | `pre-push-template.sh` | Valide le code avant l'envoi vers le dépôt distant |
| `post-checkout` | `post-checkout-template.sh` | Actions après un changement de branche |
| `post-merge` | `post-merge-template.sh` | Actions après une fusion réussie |

Tous les scripts de hook sont des **thin shims** — ils appellent le CLI `gitpr` en interne. La logique réelle réside dans le code du CLI, pas dans les fichiers de hook. Cela signifie que même si les hooks sont légèrement obsolètes, ils continuent de fonctionner correctement car ils invoquent toujours le CLI le plus récent installé.

---

## 5. Configuration

### 5.1 Variables d'Environnement

| Variable | Fichier | Description |
|----------|---------|-------------|
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Version des scripts de hook installés (géré automatiquement) |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | Langue des scripts présents sur le disque (géré automatiquement) |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Langue que vous souhaitez pour les hooks. Vide suit `GITPR_LANG`. Modifiable sur l'écran `gitpr config`, sous **Avancé → Git Hooks** |
| `GITPR_LANG` | `~/.gitpr/.env` | Langue d'interface préférée de l'utilisateur |

### 5.2 Constantes du Code Source

| Constante | Fichier | Description |
|-----------|---------|-------------|
| `__scripts_version__` | `src/updater.py` | Version actuelle des scripts de hooks |
| `HOOK_SCRIPT_SUFFIXES` | `src/core.py` | Code de langue de l'interface → suffixe de script publié |
| `effective_hook_lang()` | `src/core.py` | `SCRIPTS_LANG` lorsqu'elle est définie, la langue de l'interface en direct sinon |
| `SCRIPTS_BASE_URL` | `src/core.py` | URL de base pour le téléchargement des scripts |

### 5.3 Ajouter une Nouvelle Langue

Pour ajouter la prise en charge d'une nouvelle langue :

1. Créez 5 fichiers `.sh` traduits dans le répertoire `scripts/` (un par type de hook)
2. Ajoutez la correspondance à `HOOK_SCRIPT_SUFFIXES` dans `src/core.py` — la clé est le code de l'interface (`es_es`), la valeur est le suffixe du fichier (`.es`)
3. Le système de synchronisation automatique détectera et servira automatiquement la nouvelle langue

### 5.4 Incrémenter la Version des Scripts

Lorsque les scripts de hook sont modifiés :

1. Incrémentez `__scripts_version__` dans `src/updater.py`
2. Lors de la prochaine exécution de `gitpr`, tous les clients installés détecteront la différence et mettront à jour leurs hooks automatiquement

---

## 6. Dépannage

### Les hooks ne se mettent pas à jour

**Symptôme :** L'exécution de `gitpr` ne met pas à jour les hooks installés même s'il existe une nouvelle version.

**Solution :**
- Vérifiez que le répertoire `.git/hooks` existe dans votre projet
- Vérifiez `SCRIPTS_VERSION` dans `~/.gitpr/.env` — s'il correspond à `__scripts_version__`, aucune mise à jour n'est nécessaire
- Supprimez manuellement `SCRIPTS_VERSION` du `.env` pour forcer un nouveau téléchargement lors de la prochaine exécution
- Exécutez `gitpr --installhooks` pour forcer une nouvelle installation

### Langue incorrecte dans les hooks

**Symptôme :** Les scripts de hook affichent des messages dans la mauvaise langue.

**Solution :**
- Vérifiez `SCRIPTS_LANG` dans `~/.gitpr/.env`, ou le champ **Langue des hooks** sous **Avancé → Git Hooks** sur l'écran `gitpr config`. Vide suit `GITPR_LANG`
- Comparez avec `SCRIPTS_INSTALLED_LANG`, qui enregistre ce qui se trouve réellement sur le disque — une différence entre les deux est le signal qu'une réinstallation est en attente
- Exécutez `gitpr --installhooks` pour réinstaller immédiatement, ou lancez simplement une commande `gitpr` : l'auto-synchronisation réinstalle une fois, puis revient à la voie rapide

### Installation partielle

**Symptôme :** Certains hooks sont installés mais `SCRIPTS_VERSION` n'est pas enregistré.

**Solution :**
- C'est intentionnel — le marqueur n'est enregistré que lorsque les 5 hooks réussissent
- Vérifiez votre connexion réseau
- Exécutez `gitpr --installhooks` à nouveau pour réessayer les téléchargements échoués

---

## 7. Référence API

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

## 8. Décisions de Conception

- **Marqueur de version indépendant :** `__scripts_version__` est séparé de `__lang_version__` car les scripts de hooks évoluent selon une cadence différente des ressources linguistiques
- **Deux marqueurs de langue, pas un seul :** `SCRIPTS_LANG` est la demande et `SCRIPTS_INSTALLED_LANG` est ce que l'installeur a laissé sur le disque. L'auto-synchronisation les compare, donc changer de langue réinstalle une fois puis se stabilise. Un marqueur unique — écrit par l'installeur et comparé à lui-même — maintenait silencieusement les utilisateurs sur la langue avec laquelle ils avaient commencé, quel que soit le nombre de fois où ils modifiaient le réglage
- **L'installeur n'écrit jamais la demande :** il écraserait la valeur même qu'il est censé satisfaire, et la comparaison deviendrait une tautologie
- **La langue de l'interface est lue en direct :** `core.py` détient une copie de `i18n.CURRENT_LANG` depuis l'import, et `set_lang()` (ce que `--lang` appelle) réassigne l'original. « Suivre la langue de l'interface » la lit au moment de l'appel, donc `gitpr --lang fr_fr` installe des hooks en français
- **Approche par liste blanche :** Seuls les 4 codes mappés (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) déclenchent des téléchargements spécifiques à la langue ; toute autre langue utilise l'anglais (pas de cascade 404). La correspondance est explicite parce que le code de l'interface et le suffixe du fichier divergent — `es_es` est publié en `.es`
- **Marqueur global (non par projet) :** Le marqueur `SCRIPTS_VERSION` réside dans `~/.gitpr/.env` (global). Après une incrémentation de version, le premier projet qui exécute `gitpr` est mis à jour et enregistre le marqueur ; les hooks des autres projets sont mis à jour lors de leur prochaine exécution de `gitpr`. Comme les hooks sont des thin shims, les hooks obsolètes fonctionnent toujours — la logique réelle réside dans le CLI
- **Synchronisation protégée :** La synchronisation automatique est ignorée lors des invocations `--quiet`, `--hook` et `--mcp` pour éviter la latence réseau dans les contextes automatisés
