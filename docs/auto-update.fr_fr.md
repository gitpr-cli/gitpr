# Documentation Technique : Auto-Updater (--update)

GitPR est distribué exclusivement via PyPI. L'**Auto-Updater** vérifie à chaque exécution si une nouvelle version a été publiée, en conservant la réponse pendant au plus une heure, et maintient l'outil toujours sur la release la plus récente.

---

## 1. Vérification Manuelle

```bash
gitpr -u
# ou
gitpr --update
```

La commande force une vérification immédiate sur PyPI — elle ignore le cache — et affiche la commande de mise à jour. Elle n'installe **rien** — la mise à jour elle-même est toujours effectuée par votre gestionnaire de paquets.

---

## 2. Blocage Obligatoire de Mise à Jour

À chaque exécution de GitPR (sauf en modes `--quiet`, `--hook` et `--mcp`), et avant les sous-commandes interactives, l'outil vérifie si une version plus récente a été publiée. Le résultat est mis en cache pendant **1 heure** — une fenêtre glissante, pas le jour calendaire local — dans le fichier `~/.gitpr/update_cache.json` afin d'éviter des appels répétés à l'API. `gitpr -u`/`--update` ignore toujours le cache.

Lorsque la version publiée est plus récente que la version locale, GitPR **bloque l'exécution** : il affiche les deux versions, indique la commande `pip install --upgrade gitpr-cli` et se termine avec un statut non nul, sans effectuer aucun travail.

Les versions sont comparées selon PEP 440 : une pré-release distante est ignorée tant que la version installée est stable (pip ne l'installe pas sans `--pre`), et une version distante illisible compte comme inconnue.

Il n'existe aucun flag, fallback ou mode de compatibilité maintenant une **release installée** obsolète en fonctionnement — la mise à jour est le seul moyen de continuer. Un checkout utilisé pour le développement local dispose d'une unique variable d'échappement, documentée dans [Installer GitPR depuis les sources](tutorial/install-from-source.fr_fr.md).

### Exceptions

Le blocage ne se déclenche jamais pour :

| Contexte | Raison |
| --- | --- |
| `--quiet` | Scripts et automatisations qui ignorent la sortie |
| `--hook` | Git hooks (`prepare-commit-msg`, métriques) — ne doivent jamais casser un commit |
| `--mcp` / `gitpr-mcp` | Serveur MCP consommé par les IDE et les agents |
| `-u` / `--update` | C'est précisément la commande qui explique comment mettre à jour |
| `-h --<flag>` | Aide contextuelle |
| `gitpr <sous-commande>` sans terminal | CI, pipes et cron ne doivent jamais être bloqués — la barrière des sous-commandes ne se déclenche que lorsque l'exécution peut interroger l'utilisateur |
| `gitpr <sous-commande> -h` / `--help` | La lecture de l'aide ne doit jamais être bloquée |

`--help` et `--version` ne sont pas concernés non plus : Click les résout avant l'exécution du corps de la commande. L'aide des sous-commandes est exemptée via la ligne de commande brute. Les invocations par la surface de flags (`gitpr --status`, `gitpr -c`, …) conservent le comportement d'origine et sont bloquées quel que soit le terminal.

### Comportement Hors Ligne

Lorsque la version publiée ne peut pas être déterminée — pas d'internet et pas de cache de moins d'une heure, ou une réponse qui n'est pas une version valide — GitPR s'exécute normalement. Un utilisateur hors ligne ne doit jamais être bloqué par une commande qu'il ne peut pas exécuter.

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
