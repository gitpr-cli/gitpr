# 🎯 Smart Excludes — Optimisation des tokens

Si vous avez déjà vu GitPR réduire automatiquement votre diff avant de l'envoyer à l'IA, c'est **Smart Excludes** à l'œuvre. Cette page explique ce que c'est, comment cela fonctionne et comment le personnaliser pour votre projet.

## 🔍 Qu'est-ce que Smart Excludes ?

Smart Excludes est un système d'optimisation des tokens qui **supprime automatiquement les fichiers non liés au code** de votre `git diff` avant qu'il ne soit envoyé à l'IA pour analyse. En éliminant les lockfiles, les assets minifiés, les fichiers binaires et la prose de la documentation, l'IA reçoit un diff plus propre et plus pertinent — ce qui se traduit par :

- **Une consommation de tokens réduite** (et des coûts d'API moindres)
- **Des réponses d'IA plus rapides** (moins de texte à traiter)
- **Une analyse de meilleure qualité** (l'IA se concentre sur le code, pas sur le bruit)

## ⚙️ Comment cela fonctionne

GitPR utilise la syntaxe native d'**exclusion par pathspec** de Git (`:(exclude)*.md`) pour filtrer les fichiers hors du diff. Cette opération a lieu au niveau de la commande `git diff`, avant qu'aucun texte n'atteigne l'IA — les fichiers exclus ne consomment donc jamais le moindre token.

Le système comporte **deux niveaux** d'exclusions :

### 1. Exclusions principales (bruit)
Contrôlées par [`templates/gitpr.smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.smart-excludes.json) :

- **Lockfiles :** `package-lock.json`, `yarn.lock`, `Cargo.lock`, `Pipfile.lock`, `uv.lock`, etc.
- **Assets minifiés :** `*.min.js`, `*.min.css`, `*.bundle.js`
- **Fichiers générés :** `*.map`, `*.pyc`, `*.log`
- **Fichiers système :** `.DS_Store`, `Thumbs.db`

### 2. Exclusions de documentation (prose)
Contrôlées par [`templates/gitpr.docs-smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.docs-smart-excludes.json) :

- **Balisage/prose :** `.md`, `.txt`, `.rst`, `.adoc`, `.asciidoc`, `.org`, `.textile`, `.wiki`
- **Écrits académiques/techniques :** `.tex`, `.rtf`, `.pod`, `.rdoc`
- **Markdown étendu :** `.mdx`, `.markdown`, `.rest`
- **Pages de manuel :** `.man`, `.1`–`.8`

Les deux listes sont **fusionnées à l'exécution** dans une variable unique `SMART_EXCLUDES`, ajoutée à chaque commande `git diff` exécutée par GitPR.

## 📋 Métadonnées de documentation (docs modifiées sans contenu)

Exclure la documentation du diff permet d'économiser des tokens, mais vous voulez quand même savoir _quels_ documents ont été modifiés. GitPR résout ce problème en exécutant une commande légère distincte :

```bash
git diff --name-only <ref> -- <doc-paths>
```

Il filtre la sortie selon les extensions de documentation ci-dessus et **injecte la liste des fichiers comme métadonnées** dans les instructions système de l'IA :

```
Changed documentation (content excluded from diff):
- docs/README.md
- CHANGELOG.md
- guides/setup.rst
```

Ainsi, l'IA sait quels documents ont changé — un contexte utile pour les messages de commit et les descriptions de PR — sans que l'on consomme des tokens sur le contenu intégral de leur prose.

## 📁 Fichiers de configuration

| Fichier | Rôle | Gestion |
|------|---------|---------|
| `templates/gitpr.smart-excludes.json` | Exclusions principales (lockfiles, binaires, minifiés) | Distante (GitHub) |
| `templates/gitpr.docs-smart-excludes.json` | Extensions de documentation | Distante (GitHub) |
| `~/.gitpr/conf/gitpr.smart-excludes.json` | Cache local des exclusions principales | Téléchargement automatique |
| `~/.gitpr/conf/gitpr.docs-smart-excludes.json` | Cache local des exclusions de documentation | Téléchargement automatique |
| `./.gitpr/conf/gitpr.smart-excludes.json` | Exclusions **spécifiques au projet** (optionnel) | Créé par l'utilisateur (versionnable) |

Les deux modèles distants sont **versionnés** — GitPR les re-télécharge automatiquement lorsqu'une nouvelle version est publiée (déclenché par le marqueur `__lang_version__`). Vous n'avez jamais besoin de mettre à jour ces fichiers manuellement.

### Chaîne de résolution

Au démarrage de GitPR, chaque liste d'exclusions est chargée via une chaîne de repli :

1. **Cache global** — `~/.gitpr/conf/` (le plus rapide, aucun réseau)
2. **Téléchargement distant** — depuis le dépôt GitHub officiel (délai d'expiration : 3 secondes)
3. **Copie globale périmée** — utilisée lorsque le réseau est indisponible
4. **Repli intégré** — valeurs par défaut codées en dur (garantit le fonctionnement hors ligne)
5. **Fusion locale du projet** — `.gitpr/conf/gitpr.smart-excludes.json` à la racine du projet est chargé et **fusionné** (union) avec la liste globale. Les éléments du fichier local sont additifs — ils ajoutent des exclusions supplémentaires spécifiques à votre projet

## 📊 Exemple d'utilisation

Prenons une branche où vous avez modifié `src/auth.py`, `docs/README.md` et `package-lock.json` :

**Sans Smart Excludes** (tous les fichiers dans le diff) :
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
diff --git a/docs/README.md b/docs/README.md
+ ## New Section
+ This is a long documentation update with many paragraphs...
diff --git a/package-lock.json b/package-lock.json
+ 500 lines of dependency tree changes
```
→ ~600+ lignes envoyées à l'IA (~15 000 tokens)

**Avec Smart Excludes** (seul le code dans le diff) :
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
```
→ ~10 lignes envoyées à l'IA (~250 tokens)

**Plus les métadonnées** injectées dans l'instruction système :
```
Changed documentation (content excluded from diff):
- docs/README.md
```

> **Résultat :** une réduction d'environ 98 % des tokens dans ce scénario, tout en gardant l'IA informée que la documentation a été mise à jour.

## 🎨 Personnalisation

### Ajouter de nouvelles extensions

Pour ajouter définitivement de nouveaux motifs, modifiez les fichiers modèles du [dépôt GitPR](https://github.com/natanfiuza/gitpr) :

1. Modifiez `templates/gitpr.smart-excludes.json` pour le bruit non lié au code
2. Modifiez `templates/gitpr.docs-smart-excludes.json` pour les extensions de documentation
3. Incrémentez `__lang_version__` dans `src/updater.py`
4. Les nouveaux motifs se propagent à tous les utilisateurs lors de leur prochaine exécution

### Configuration Locale du Projet (Recommandé)

Chaque projet peut avoir son propre fichier Smart Excludes dans `.gitpr/conf/gitpr.smart-excludes.json`. Ce fichier est **fusionné** avec la liste globale à l'exécution — il ajoute des exclusions supplémentaires qui ne s'appliquent qu'à votre projet (ex : `dist/`, `node_modules/`, artefacts de build spécifiques à un framework).

**Création du fichier :**

Le fichier est créé automatiquement la première fois que GitPR télécharge la liste globale Smart Excludes. Vous pouvez également le créer manuellement :

```json
{
  "_comment": "Exclusions spécifiques au projet. Fusionné avec la liste globale à l'exécution.",
  "excludes": [
    "dist/",
    "*.pyc",
    "build/"
  ]
}
```

**Pourquoi utiliser le fichier local au lieu de modifier le cache global ?**

- Le cache global (`~/.gitpr/conf/`) est écrasé à chaque mise à jour de version
- Le fichier local persiste indépendamment et peut être **versionné** dans votre dépôt
- Les membres de l'équipe reçoivent les mêmes exclusions spécifiques au projet lorsqu'ils clonent le dépôt

### Remplacement Temporaire

Vous pouvez modifier directement les fichiers en cache dans `~/.gitpr/conf/`. Ces changements persistent jusqu'au prochain incrément de `__lang_version__`, où la version distante les remplace. Préférez le fichier local du projet pour des exclusions permanentes.

### Désactiver Smart Excludes

Définissez la variable d'environnement `GITPR_SKIP_SMART_EXCLUDES=1` pour désactiver tout le filtrage Smart Excludes pour la session en cours. À utiliser avec parcimonie — cela supprime à la fois les exclusions globales et locales du projet.

## ❓ FAQ

### Pourquoi les fichiers de documentation sont-ils exclus du diff ?

La prose de la documentation (README, guides, CHANGELOG) peut compter des milliers de mots. Les inclure dans le prompt de l'IA consomme des tokens qui seraient mieux utilisés pour analyser les modifications de code. L'IA reçoit néanmoins les _noms_ des fichiers comme métadonnées, afin de savoir quels documents ont changé.

### Comment savoir quels fichiers de documentation ont été modifiés ?

GitPR injecte automatiquement la liste des fichiers de documentation modifiés dans le contexte de l'IA. Vous pouvez aussi exécuter `git diff --name-only` vous-même et filtrer selon les extensions listées ci-dessus.

### Puis-je désactiver complètement Smart Excludes ?

Smart Excludes est une optimisation essentielle mais peut être désactivé en définissant `GITPR_SKIP_SMART_EXCLUDES=1` dans votre environnement. Pour un contrôle plus fin, utilisez le fichier de configuration local du projet (`.gitpr/conf/gitpr.smart-excludes.json`) pour ajouter ou ajuster les exclusions de votre projet sans désactiver le système globalement.

### Est-ce que cela affecte le dépôt git réel ?

Non. Smart Excludes n'affecte que ce que GitPR _lit_ dans votre dépôt. Votre `git diff` réel, vos commits et votre arbre de travail restent totalement inchangés.

### Qu'en est-il du linter ?

Le linter statique (`.gitpr.linter.yml`) s'exécute sur le diff **après** le filtrage Smart Excludes. Les fichiers de documentation ne sont pas lintés.

---

📂 **Dépôt :** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
🌐 **Site web :** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
