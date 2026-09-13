# Journal d'Utilisation — chaque commande exécutée par GitPR

GitPR tient un registre de son propre usage : une ligne par commande, écrite au moment où la commande démarre. C'est la réponse à « qu'ai-je réellement exécuté, et quand ? » — utile quand une flag s'est comportée de façon inattendue, quand vous voulez savoir à quelle fréquence une fonctionnalité sert, ou quand vous reconstituez ce qui s'est passé dans un dépôt la semaine dernière.

Le journal est local, en texte brut, et ne quitte jamais votre machine. Rien n'est transmis où que ce soit.

---

## 1. Où Sont les Fichiers

Chaque commande ajoute une ligne dans `~/.gitpr/logs/<uuid>.log`, et il y a **un fichier par jour** :

```text
~/.gitpr/logs/
├── 4b1c8d3e-1f27-5a44-9c0b-7d2e5f8a1b30.log   ← aujourd'hui
├── 9f2a7c10-6b83-5e21-8a4d-1c9f0e7b2d55.log   ← hier
└── pr_desc/                                   ← le journal de publication de PR, une fonctionnalité distincte
```

Le nom du fichier est un UUID **dérivé de la date** — `uuid5` de `gitpr.usage.<YYYY-MM-DD>` — et non un nom aléatoire. C'est délibéré : un nom aléatoire exigerait un compteur ou un fichier d'état pour savoir quel fichier appartient à aujourd'hui, et deux processus GitPR lancés au même instant pourraient ne pas être d'accord. Dérivé de la date, le même jour résout toujours vers le même nom, donc des commandes simultanées se contentent d'ajouter au même fichier.

Un nouveau jour ouvre un nouveau fichier. GitPR ne les fait jamais tourner ni ne les supprime — purger les anciens vous revient.

---

## 2. Ce que Contient une Ligne

```text
[2026-09-12 14:32:01] | v1.0.0 | gitpr -c | gitpr-cli/gitpr | Nataniel Fiuza <natan.fiuza@gmail.com>
```

| Champ | Source | Remarques |
| --- | --- | --- |
| Date et heure | l'horloge locale, au démarrage de la commande | `YYYY-MM-DD HH:MM:SS` |
| Version | la version de GitPR en cours | |
| Commande | le nom du programme et les flags tels quels | `gitpr -c`, `gitpr-mcp --list` |
| Dépôt | `remote.origin.url`, réduite à `owner/repo` | `-` hors d'un dépôt, ou sans remote d'origine |
| Auteur | `user.name` et `user.email` de la configuration Git | `-` quand Git n'a aucune identité configurée |

Le dépôt est réduit à son chemin, quelle que soit la forge : `git@github.com:owner/repo.git`, `https://gitlab.com/group/repo` et `https://dev.azure.com/org/project/_git/repo` deviennent `owner/repo`, `group/repo` et `org/project/repo`.

Chaque invocation est enregistrée, y compris `--help` et celles qui échouent. Pour le serveur MCP, cela signifie son démarrage : `gitpr-mcp` écrit une ligne quand le serveur se lance, pas une par appel d'outil.

---

## 3. Comment le Désactiver

C'est `GITPR_SHOW_LOGS` qui le contrôle, et elle est **active** par défaut — toute installation a déjà la ligne semée dans `~/.gitpr/.env`.

| Où | Comment |
| --- | --- |
| Dans l'écran de configuration | `gitpr config` → **Général** → **Enregistrer les journaux généraux** |
| Dans le fichier | `GITPR_SHOW_LOGS=false` dans `~/.gitpr/.env` |
| Pour une seule exécution | `GITPR_SHOW_LOGS=false gitpr -c` |

L'environnement l'emporte toujours sur le fichier (voir [l'écran de configuration](config-tui.fr_fr.md) §2), donc la dernière ligne désactive cette commande précise sans rien toucher d'autre.

Le désactiver arrête les nouvelles lignes. Cela ne supprime pas ce qui est déjà là.

---

## 4. Ce qu'il N'Enregistre Pas

Le journal est délibérément mince : il enregistre *qu'*une commande a tourné et *laquelle*, et rien de ce qu'elle a lu ou produit.

Il ne contient jamais le diff, le contenu des fichiers, les chemins de fichiers, le texte des prompts ou des skills, les réponses de l'IA, les messages de commit et descriptions de PR générés, ni le moindre identifiant.

Les deux valeurs personnelles qu'il détient — le dépôt et l'auteur Git — restent sur la machine, puisque le fichier est local et que rien n'est transmis.

---

## 5. Notes pour les Développeurs

| Fichier | Rôle |
| --- | --- |
| `src/usage_log.py` | Toute la fonctionnalité : dérivation du chemin, l'unique appel à git, le format de la ligne et l'écriture |
| `src/main.py` | Un appel en tête du callback racine — le point unique que toute flag, toute sous-commande et `--help` atteignent |
| `src/mcp_server.py` | Un appel dans `main()`, car le script console `gitpr-mcp` ne charge jamais `main.py` |

Deux garanties que l'implémentation assume volontairement :

- **L'écriture est synchrone.** Un thread d'arrière-plan — comme le fait l'enregistreur de métriques locales — perd l'entrée dès que le processus se termine avant que le thread soit ordonnancé, et un journal qui abandonne des commandes en silence est pire que pas de journal.
- **Il ne peut jamais gêner une commande.** Toute défaillance — pas de git, pas de permission, pas de répertoire personnel — est absorbée : `log_usage()` revient sans écrire et la commande continue. Il n'imprime jamais rien non plus, car le serveur MCP réserve stdout à son flux JSON-RPC.

Ajouter un troisième point d'entrée, c'est y ajouter un appel. Rien n'atteint le journal tout seul.
