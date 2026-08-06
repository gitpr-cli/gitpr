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
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Suit la langue des scripts installés (ex. : `fr`, `pt_br`) |

### 2.2 Flux de Synchronisation Automatique

```
exécution de gitpr
    │
    ├─ Lit SCRIPTS_VERSION et SCRIPTS_LANG depuis ~/.gitpr/.env
    │
    ├─ Compare avec __scripts_version__ et CURRENT_LANG
    │
    ├─ Correspondance ? → Ignorer (voie rapide — simple lecture du .env, sans réseau)
    │
    └─ Différence ou absence ? → Télécharger et installer les hooks dans la langue actuelle
                                   → Enregistrer SCRIPTS_VERSION + SCRIPTS_LANG
```

La voie rapide (quand les versions correspondent) est une simple lecture du fichier `.env` sans aucune E/S réseau.

### 2.3 Langues Prises en Charge

| Langue | Code | Suffixe du Script | Exemple |
|--------|------|-------------------|---------|
| Anglais (défaut) | `en` | *(sans suffixe)* | `pre-commit-template.sh` |
| Portugais (Brésil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Portugais (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Français | `fr` | `.fr` | `pre-commit-template.fr.sh` |
| Espagnol | `es` | `.es` | `pre-commit-template.es.sh` |

L'anglais est la langue par défaut et de repli. Si un script dans une langue spécifique n'est pas trouvé sur le serveur (HTTP 404), le système utilise automatiquement la version anglaise.

---

## 3. Fonctionnement

### 3.1 Première Exécution (Sans Hooks Installés)

Lorsqu'un utilisateur exécute `gitpr --installhooks` ou `gitpr --install` pour la première fois :

1. GitPR détecte la langue actuelle (`CURRENT_LANG`) depuis le système d'exploitation ou `.env`
2. Télécharge d'abord les scripts spécifiques à la langue (ex. : `pre-commit-template.fr.sh`)
3. Utilise le repli en anglais si la variante linguistique n'est pas disponible (HTTP 404)
4. Applique les permissions d'exécution (`chmod +x`)
5. Enregistre `SCRIPTS_VERSION` et `SCRIPTS_LANG` dans `~/.gitpr/.env`

### 3.2 Exécutions Suivantes (Synchronisation Automatique)

À chaque exécution de `gitpr` :

1. `check_and_update_hooks_scripts()` lit `SCRIPTS_VERSION` et `SCRIPTS_LANG` depuis `.env`
2. Compare avec `__scripts_version__` (du code) et `CURRENT_LANG`
3. Si les deux correspondent → rien ne se passe (voie rapide)
4. Si la version diffère → les hooks sont re-téléchargés dans la langue actuelle
5. Si la langue diffère → les hooks sont re-téléchargés pour correspondre à la nouvelle langue
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
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Langue des scripts installés (géré automatiquement) |
| `GITPR_LANG` | `~/.gitpr/.env` | Langue d'interface préférée de l'utilisateur |

### 5.2 Constantes du Code Source

| Constante | Fichier | Description |
|-----------|---------|-------------|
| `__scripts_version__` | `src/updater.py` | Version actuelle des scripts de hooks |
| `_SCRIPT_LANG_SUFFIXES` | `src/core.py` | Ensemble des suffixes de langue pris en charge |
| `SCRIPTS_BASE_URL` | `src/core.py` | URL de base pour le téléchargement des scripts |

### 5.3 Ajouter une Nouvelle Langue

Pour ajouter la prise en charge d'une nouvelle langue :

1. Créez 5 fichiers `.sh` traduits dans le répertoire `scripts/` (un par type de hook)
2. Ajoutez le code de langue à `_SCRIPT_LANG_SUFFIXES` dans `src/core.py`
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
- Vérifiez `GITPR_LANG` dans `~/.gitpr/.env`
- Supprimez `SCRIPTS_LANG` du `.env` pour forcer la re-détection de la langue
- Exécutez `gitpr --installhooks` pour réinstaller dans la langue correcte

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

## 8. Décisions de Conception

- **Marqueur de version indépendant :** `__scripts_version__` est séparé de `__lang_version__` car les scripts de hooks évoluent selon une cadence différente des ressources linguistiques
- **Marqueur complémentaire `SCRIPTS_LANG` :** Empêche le basculement intempestif de langue lorsqu'un utilisateur exécute `gitpr --lang pt_br` une fois — la synchronisation automatique ne re-télécharge pas sauf si la version OU la langue diffèrent
- **Approche par liste blanche :** Seuls 4 suffixes explicites (`pt_br`, `pt_pt`, `fr`, `es`) déclenchent des téléchargements spécifiques à la langue ; toute autre langue utilise l'anglais (pas de cascade 404)
- **Marqueur global (non par projet) :** Le marqueur `SCRIPTS_VERSION` réside dans `~/.gitpr/.env` (global). Après une incrémentation de version, le premier projet qui exécute `gitpr` est mis à jour et enregistre le marqueur ; les hooks des autres projets sont mis à jour lors de leur prochaine exécution de `gitpr`. Comme les hooks sont des thin shims, les hooks obsolètes fonctionnent toujours — la logique réelle réside dans le CLI
- **Synchronisation protégée :** La synchronisation automatique est ignorée lors des invocations `--quiet`, `--hook` et `--mcp` pour éviter la latence réseau dans les contextes automatisés
