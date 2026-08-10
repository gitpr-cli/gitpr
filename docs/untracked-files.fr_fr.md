# ⚠️ Pourquoi GitPR a-t-il ignoré mes nouveaux fichiers ?

Si vous avez exécuté GitPR et reçu un avertissement indiquant que des **fichiers non suivis (untracked)** ont été détectés, ne vous inquiétez pas ! Il s'agit d'un comportement de sécurité et d'optimisation natif du système.

## 🔍 Que signifie « Non suivi » ?

Lorsque vous créez un nouveau fichier dans votre projet, Git ne le suit pas automatiquement. Il reste dans l'état *Untracked*. La commande que GitPR utilise pour lire votre code (`git diff HEAD`) n'analyse que les fichiers que Git connaît déjà ou qui ont été préparés pour le commit (*Staged*).

## 🛡️ Pourquoi GitPR ne lit-il pas ces fichiers automatiquement ?

Nous avons conçu GitPR autour de trois piliers :
1. **Sécurité (prévention des fuites) :** Imaginez que vous créiez un fichier `.env.local` avec les mots de passe de la base de données de production et que vous oubliiez de le placer dans le `.gitignore`. Si GitPR lisait tout automatiquement, il enverrait vos mots de passe à l'API de l'IA.
2. **Économie de tokens (argent) :** Certains frameworks génèrent d'énormes dossiers de cache ou des fichiers compilés. Envoyer des déchets à l'IA consommerait vos tokens inutilement et rendrait la réponse extrêmement lente.
3. **Standard Git :** GitPR respecte le cycle de vie officiel de Git. L'IA n'analyse que ce que vous, en tant que développeur, décidez d'avoir de la valeur.

## ✅ Comment résoudre le problème ?

La solution est très simple. Il vous suffit d'indiquer à Git quels nouveaux fichiers font partie de votre prochain commit à l'aide de la commande `add` :

```bash
# Pour ajouter un fichier spécifique :
git add src/meu_novo_arquivo.py

# OU pour ajouter tous les nouveaux fichiers d'un coup :
git add .

```

Après avoir exécuté `git add`, il vous suffit de relancer la commande **GitPR**. L'IA verra désormais vos nouveautés et générera l'analyse parfaitement ! 🚀

## 🔎 Vérification Rapide : Quels fichiers ne sont pas en stage ?

Vous pouvez vérifier rapidement quels fichiers ne sont pas en stage en utilisant la flag `--status` — **sans IA, sans réseau, instantané** :

```bash
gitpr --status
```

Cela affiche toutes les modifications non commitées en 3 catégories : nouveaux (non suivis), modifiés et supprimés. Consultez la [documentation Git Status](git-status.fr_fr.md) pour plus de détails.

## 🛑 Ignorer la vérification unstaged

Si vous souhaitez ignorer la vérification des fichiers unstaged qui s'exécute avant les commandes IA, utilisez :

```bash
gitpr -c --no-unstaged-check
```

Ou définissez `GITPR_SKIP_UNSTAGED_CHECK=true` dans votre fichier `~/.gitpr/.env` pour l'ignorer définitivement.

> 📖 **Documentation complète :** [docs/git-status.fr_fr.md](git-status.fr_fr.md) — couvre `--status`, `--no-unstaged-check`, les outils MCP et la vérification unstaged qui s'exécute désormais sur toutes les commandes (`-c`, `-r`, `-f`, `-is`).
