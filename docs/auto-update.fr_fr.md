# Documentation Technique : Auto-Updater (--update)

GitPR est distribué exclusivement via PyPI. L'**Auto-Updater** vérifie chaque jour si une nouvelle version a été publiée et maintient l'outil toujours sur la release la plus récente.

---

## 1. Vérification Manuelle

```bash
gitpr -u
# ou
gitpr --update
```

La commande force une vérification immédiate sur PyPI et affiche la commande de mise à jour. Elle n'installe **rien** — la mise à jour elle-même est toujours effectuée par votre gestionnaire de paquets.

---

## 2. Blocage Obligatoire de Mise à Jour

À chaque exécution de GitPR (sauf en modes `--quiet`, `--hook` et `--mcp`), l'outil vérifie si une version plus récente a été publiée. Le résultat est mis en cache pendant **24 heures** dans le fichier `~/.gitpr/update_cache.json` afin d'éviter des appels répétés à l'API.

Lorsque la version publiée est plus récente que la version locale, GitPR **bloque l'exécution** : il affiche les deux versions, indique la commande `pip install --upgrade gitpr-cli` et se termine avec un statut non nul, sans effectuer aucun travail.

Il n'existe aucun flag, fallback ou mode de compatibilité maintenant une version obsolète en fonctionnement — la mise à jour est le seul moyen de continuer.

### Exceptions

Le blocage ne se déclenche jamais pour :

| Contexte | Raison |
| --- | --- |
| `--quiet` | Scripts et automatisations qui ignorent la sortie |
| `--hook` | Git hooks (`prepare-commit-msg`, métriques) — ne doivent jamais casser un commit |
| `--mcp` / `gitpr-mcp` | Serveur MCP consommé par les IDE et les agents |
| `-u` / `--update` | C'est précisément la commande qui explique comment mettre à jour |
| `-h --<flag>` | Aide contextuelle |

`--help` et `--version` ne sont pas concernés non plus : Click les résout avant l'exécution du corps de la commande.

### Comportement Hors Ligne

Lorsque la version publiée ne peut pas être déterminée — pas d'internet et pas de cache pour le jour courant — GitPR s'exécute normalement. Un utilisateur hors ligne ne doit jamais être bloqué par une commande qu'il ne peut pas exécuter.

---

## 3. Appliquer la Mise à Jour

```bash
pip install --upgrade gitpr-cli
```

Les utilisateurs de `pipx`, `uv` ou `poetry` doivent mettre à jour avec leur propre outil (`pipx upgrade gitpr-cli`, `uv tool upgrade gitpr-cli`, …).

---

## 4. Gardien de Connexion

Avant toute opération réseau, GitPR vérifie la connectivité via le socket `8.8.8.8:53`. Sans internet, l'outil fonctionne normalement en mode hors ligne — sans se figer ni afficher d'erreurs de connexion.

---

## 5. Source de Version

| Source | Utilisation |
| --- | --- |
| **PyPI** (`pypi.org/pypi/gitpr-cli/json`) | Source unique de la version publiée |

La version locale est définie dans `src/updater.py` (`__version__`) et incrémentée à chaque release.

> **Note :** Consultez également la [documentation principale (README.md)](../README.md) pour les informations d'installation et de configuration initiale.
