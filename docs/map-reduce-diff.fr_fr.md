# 📦 Comment GitPR Gère les Diffs Géants (Map-Reduce)

Si GitPR a affiché le message **« 📦 Diff géant détecté ! Traitement en N lots (Map-Reduce)... »**, vos modifications étaient trop volumineuses pour être analysées par l'IA en un seul appel. Pas d'inquiétude — rien n'est perdu. Cette page explique ce qui se passe en coulisses.

## 🔍 Pourquoi une limite de taille ?

Les modèles d'IA ont une fenêtre de contexte limitée. GitPR estime la taille de votre diff avec la règle prudente de **4 caractères par token**. Lorsque l'estimation dépasse **90 000 tokens** (environ 360 000 caractères), un seul appel API pourrait échouer, tronquer l'analyse ou produire des résultats de mauvaise qualité.

## ⚙️ Comment fonctionne le pipeline Map-Reduce ?

1. **Découpage (Split) :** le diff est divisé en lots, en respectant toujours les limites de fichiers (les en-têtes `diff --git`). Un fichier n'est jamais coupé en deux.
2. **Map :** chaque lot est envoyé à l'IA, qui renvoie un résumé technique de ce qui a changé dans cette partie. La console affiche la progression :

   ```text
   📦 Diff géant détecté ! Traitement en 4 lots (Map-Reduce)...
   ⏳ Analyse du lot 1/4...
   ⏳ Analyse du lot 2/4...
   ```

3. **Reduce :** les résumés partiels sont unifiés et envoyés dans un appel final qui génère le résultat réel — le message de commit (`-c`), la revue de code (`-r`/`-f`) ou la description de la Pull Request (commande par défaut).

## 💡 Bon à savoir

- **Entièrement automatique :** aucune option à activer. Le découpage ne s'active que lorsque le diff dépasse la limite ; les diffs plus petits continuent d'utiliser un seul appel à l'IA.
- **Même fournisseur et même modèle :** les lots utilisent le moteur d'IA que vous avez configuré (Gemini, DeepSeek ou Ollama), avec une pause d'une seconde entre les appels pour respecter les limites de requêtes.
- **Les smart excludes passent d'abord :** les fichiers lock, les assets minifiés et autres bruits sont retirés du diff avant l'estimation de taille — ce qui évite souvent complètement le découpage.
- **Compromis de qualité :** le résultat final est généré à partir de résumés techniques plutôt que du diff brut ; les détails très fins peuvent donc être condensés. Pour les branches géantes, découper le travail en PRs plus petites reste la meilleure matière à donner à l'IA.

🔗 Dépôt : [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
