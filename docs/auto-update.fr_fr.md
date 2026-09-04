# Documentation technique : Auto-Updater (--update)

GitPR possède un système de mise à jour automatique (**Auto-Updater**) qui maintient l'outil toujours dans sa version la plus récente, avec une vérification quotidienne et une mise à jour par *hot-swap*.

---

## 1. Mise à jour manuelle

```bash
gitpr -u
# ou
gitpr --update
```

La commande force la vérification et l'installation immédiate de la version la plus récente.

---

## 2. Vérification automatique quotidienne

À chaque exécution de GitPR (sauf en modes `--quiet` et `--hook`), l'outil vérifie silencieusement si une nouvelle version est disponible. Le résultat est mis en cache pendant **24 heures** dans le fichier `~/.gitpr/update_cache.json` pour éviter les appels répétés à l'API.

S'il y a une nouvelle version, une notification est affichée à la fin de l'exécution.

---

## 3. Méthodes de mise à jour

L'Auto-Updater détecte automatiquement la méthode d'installation :

### 3.1 Installation via pip

```bash
pip install --upgrade gitpr-cli
```

### 3.2 Installation via binaire (PyInstaller)

GitPR utilise la technique du **Hot-Swap** pour les binaires standalone :

1. Vérifie la version la plus récente sur les [GitHub Releases](https://github.com/gitpr-cli/gitpr.git/releases)
2. Télécharge le nouvel exécutable
3. Renomme le `.exe` actuel en `.exe.old`
4. Déplace le nouveau binaire à sa place
5. En cas d'échec, revient au `.exe.old` (rollback automatique)
6. À la prochaine exécution, supprime automatiquement le `.old` (nettoyage)

---

## 4. Gardien de connexion

Avant toute opération réseau, GitPR vérifie la connectivité via le socket `8.8.8.8:53`. S'il n'y a pas d'internet, l'outil fonctionne normalement en mode hors ligne — sans se bloquer ni afficher d'erreurs de connexion.

---

## 5. Sources de version

| Source | Utilisation |
| --- | --- |
| **PyPI** | Version pour les installations pip (`pip install gitpr-cli`) |
| **GitHub Releases** | Version pour les binaires standalone (`.exe`) |

La version locale est définie dans `src/updater.py` (`__version__`) et incrémentée à chaque release.

> **Note :** Consultez également la [documentation principale (README.md)](../README.md) pour des informations sur l'installation et la configuration initiale.
