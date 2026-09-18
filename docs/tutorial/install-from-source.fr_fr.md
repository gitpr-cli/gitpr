# Installer GitPR depuis les sources (et débloquer le portail de version)

Ce guide s'adresse à celles et ceux qui exécutent GitPR depuis un **checkout
local** plutôt que depuis le paquet publié sur PyPI, et qui butent pour cette
raison sur le blocage de mise à jour obligatoire.

> Si votre objectif est seulement de tester une modification avant de publier une
> nouvelle version sur PyPI, la recette plus courte de
> [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md) (en portugais) peut
> suffire. Ce guide va plus loin : il explique **pourquoi** le blocage de mise à
> jour se déclenche encore sur une installation depuis les sources, et quoi faire
> à ce sujet.

---

## 1. Le symptôme

Vous avez installé GitPR depuis le dépôt, avec l'option de mode éditable :

```bash
pip install -e .
```

Et pourtant, à chaque exécution, GitPR refuse de fonctionner :

```text
⚠️ A new version of GitPR is available: 1.1.0 -> 1.2.0
GitPR must be updated before it can run: pip install --upgrade gitpr-cli
```

Le processus se termine avec un code non nul et n'effectue aucun travail. Lancer
`pip install --upgrade gitpr-cli` est le réflexe évident, mais c'est exactement
ce qu'il ne faut **pas** faire : cela remplace votre checkout par le paquet
publié.

---

## 2. Installer depuis les sources (mode éditable)

La commande est `pip install -e .` — le `-e` vient de *editable* et le point
désigne le répertoire courant.

```bash
git clone https://github.com/gitpr-cli/gitpr.git
cd gitpr
pip install -e .
```

> Attention à l'**espace et au point** à la fin de `-e .`. Le point signifie
> « installe le paquet de ce répertoire » ; sans lui, pip cherche sur PyPI un
> paquet portant littéralement ce nom et échoue.

Vérifiez que le point d'entrée a bien été créé :

```bash
gitpr --version
```

En mode éditable, Python ne copie pas les fichiers — il relie la distribution
installée directement à votre répertoire de travail. Enregistrer un fichier dans
l'éditeur suffit pour que la modification prenne effet à la prochaine exécution
de `gitpr`, sans réinstallation.

---

## 3. Pourquoi le blocage de mise à jour se déclenche encore

C'est la partie surprenante : **ce n'est pas une installation cassée**. C'est le
portail de mise à jour qui fonctionne comme prévu, sur un checkout en retard par
rapport à la release publiée.

Le portail se trouve dans `enforce_update_required()` ([src/updater.py](../../src/updater.py))
et compare deux versions :

| Version | D'où elle vient |
| --- | --- |
| Distante | `https://pypi.org/pypi/gitpr-cli/json`, mise en cache 24h dans `~/.gitpr/update_cache.json` |
| Locale | `__version__`, en haut de `src/updater.py` |

L'exécution est bloquée lorsque la version distante est **supérieure** à la
version locale. Le piège est du côté *local* : dans une installation éditable,
`src/updater.py` est lu depuis **votre arbre de travail**, et non depuis une
copie figée au moment de l'installation. Ce que dit `__version__` dans le
checkout que vous avez ouvert est la version que GitPR annonce — et donc celle
que le portail compare.

Le scénario de panne se présente ainsi :

| | Valeur |
| --- | --- |
| Publié sur PyPI | `1.2.0` |
| `__version__` dans votre checkout | `1.1.0` |
| Résultat | bloqué à chaque commande |

Un second symptôme, plus subtil, du même mécanisme : `git stash`,
`git checkout` ou `git switch` vers une branche antérieure à la dernière release
rebloque GitPR immédiatement, parce que le fichier sur le disque a changé alors
que rien n'a été réinstallé.

---

## 4. Débloquer — option A (recommandée) : s'aligner sur la release

Le correctif direct consiste à faire en sorte que l'arbre sur lequel vous
travaillez annonce une version **supérieure ou égale** à celle publiée sur PyPI.
Concrètement :

```bash
git switch main
git pull
pip install -e .
gitpr -u
```

`gitpr -u` (`--update`) n'est jamais bloqué : c'est donc le moyen le plus sûr de
confirmer la situation avant de lancer quelque chose de plus lourd. Il affiche la
comparaison et la commande de mise à jour, et n'installe rien.

Relancez également `pip install -e .` après un `git pull` ou un changement de
branche qui ajoute ou renomme des modules. Le lien éditable couvre l'arbre
source, mais un point d'entrée ou une dépendance nouveaux dans `pyproject.toml`
n'atteignent la distribution installée qu'avec un nouveau `pip install -e .`.

> **Ne modifiez pas `__version__` à la main pour falsifier une version.**
> Augmenter la chaîne sans couper une release corrompt ce que rapporte
> `gitpr -u` et masque un réel besoin de mise à jour. Le marqueur de version est
> défini par le processus de release, non par la commodité du développeur.

---

## 5. Débloquer — option B : `GITPR_SKIP_UPDATE_CHECK` (usage local)

GitPR lit une variable d'environnement qui fait taire la vérification
entièrement. Ajoutez une ligne au fichier de configuration global
`~/.gitpr/.env` :

```bash
# ~/.gitpr/.env
GITPR_SKIP_UPDATE_CHECK=1
```

Enregistrez le fichier et relancez GitPR — le blocage a disparu.

**À réserver au développement local et hors ligne.** Ce n'est pas un substitut à
la mise à jour d'une installation de release : tant que la variable est active,
un GitPR réellement obsolète s'exécute en silence, sans avertissement et sans
protection contre un comportement déjà corrigé en amont.

Quatre détails à connaître avant de vous y fier :

- **Toute valeur non vide désactive la vérification** — y compris `0`, `false`
  et `no`. La variable est lue comme un simple drapeau
  (`bool(os.environ.get(..., "").strip())`), elle n'est pas interprétée comme un
  booléen. Seule une valeur vide ou composée uniquement d'espaces laisse la
  vérification active. Définir `GITPR_SKIP_UPDATE_CHECK=` ne fait donc **rien**.
- **Ce n'est pas une clé de `DEFAULT_CONFIG`.** Elle n'apparaît pas dans l'interface
  de configuration et n'est pas créée par l'assistant d'installation — vous devez
  ajouter la ligne à `~/.gitpr/.env` à la main.
- **Elle agit via le chargement du dotenv.** `~/.gitpr/.env` est chargé au moment
  de l'import, avant l'exécution du portail, et c'est pourquoi l'écrire dans le
  fichier fonctionne exactement comme l'exporter dans le shell. L'exporter pour
  une seule commande fonctionne aussi :

  ```bash
  GITPR_SKIP_UPDATE_CHECK=1 gitpr -c
  ```

- **Pour réactiver la vérification**, supprimez la ligne de `~/.gitpr/.env` (ou
  remplacez-la par une valeur vide) et redémarrez GitPR.

---

## 6. Ce qui n'est jamais bloqué

Toutes les invocations ne passent pas par le portail. La vérification est omise
pour :

| Contexte | Raison |
| --- | --- |
| `--quiet` | Scripts et automatisation qui ignorent la sortie |
| `--hook` | Hooks git — ne doivent jamais casser un commit |
| `--mcp` / `gitpr-mcp` | Serveur MCP consommé par les IDE et les agents |
| `-u` / `--update` | C'est précisément la commande qui explique comment mettre à jour |
| `-h --<flag>` | Aide contextuelle |
| `--help` / `--version` | Click résout les deux avant l'exécution du corps de la commande |
| **Toute sous-commande** | `gitpr fix`, `gitpr review-pr`, `gitpr release`, `gitpr init` sont dispatchées avant le portail |
| Hors ligne | Quand la version distante est inconnue, l'exécution se poursuit — un utilisateur hors ligne ne doit jamais être enfermé hors d'une commande qu'il ne peut pas corriger |

Sur un checkout bloqué, `gitpr -u` et les sous-commandes restent donc utilisables
pour le diagnostic, même sans la variable d'environnement.

---

## 7. Vérifier l'installation

Confirmez quel mode est actif :

```bash
pip list --editable
```

`gitpr-cli` doit figurer dans la liste. Sur un pip plus ancien, cherchez un
répertoire `gitpr_cli.egg-info/` à la racine du dépôt — sa présence est la
signature d'une installation éditable.

> Vous voyez `WARNING: Ignoring invalid distribution ~itpr-cli` ? Ce sont des
> répertoires `~itpr_cli-*.dist-info` laissés dans `site-packages` par une
> opération `pip` interrompue — pip renomme une distribution en `~<nom>` avant de
> la supprimer, et une exécution avortée laisse le renommage derrière elle. Ce
> sont des restes inertes que pip ignore ; supprimez-les à la main si
> l'avertissement vous gêne.

Confirmez ensuite la version annoncée :

```bash
gitpr -u
```

Comparez la version locale affichée avec la ligne `__version__` de
`src/updater.py` dans le checkout que vous avez ouvert. Si elles diffèrent,
l'installation pointe ailleurs que vers l'arbre que vous croyez modifier.

---

## 8. Revenir à l'installation PyPI

Lorsque vous avez terminé le développement local :

```bash
pip uninstall gitpr-cli
pip install --upgrade gitpr-cli
```

Nettoyez ensuite ce que le mode éditable a laissé derrière lui :

- supprimez la ligne `GITPR_SKIP_UPDATE_CHECK` de `~/.gitpr/.env` ;
- supprimez le répertoire `gitpr_cli.egg-info/` à la racine du dépôt (ce sont des
  métadonnées de build jetables) ;
- confirmez avec `pip list --editable`, qui ne doit plus lister `gitpr-cli`.

---

## Voir aussi

- [auto-update.md](../auto-update.fr_fr.md) — le module de mise à jour automatique et le blocage obligatoire
- [testar_sem_usar_pypi.md](../testar_sem_usar_pypi.md) — tester sans dépenser une version PyPI (en portugais)
- [ARCHITECTURE.md](../ARCHITECTURE.md) — carte des modules et flux des commandes
