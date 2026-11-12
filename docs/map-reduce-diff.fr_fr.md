# 📦 Comment GitPR Gère les Diffs Géants (Map-Reduce)

Si GitPR a affiché le message **« 📦 Diff géant détecté ! Traitement en N lots (Map-Reduce)... »**, vos modifications étaient trop volumineuses pour être analysées par l'IA en un seul appel. Pas d'inquiétude — rien n'est perdu. Cette page explique ce qui se passe en coulisses.

## 🔍 Pourquoi une limite de taille ?

Les modèles d'IA ont une fenêtre de contexte limitée. GitPR estime la taille de votre diff avec la règle prudente de **4 caractères par token**. Lorsque l'estimation dépasse **90 000 tokens** (environ 360 000 caractères), un seul appel API pourrait échouer, tronquer l'analyse ou produire des résultats de mauvaise qualité.

## ⚙️ Comment fonctionne le pipeline Map-Reduce ?

1. **Découpage (Split) :** le diff est divisé en lots plafonnés à **50 000 tokens** chacun (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`). Bien que les limites de fichiers (`diff --git`) soient préservées dès que possible, tout fichier individuel dépassant cette limite est partitionné en cascade (limites de hunks `@@` et découpes de lignes), en répétant l'en-tête du fichier et des marqueurs contextuels sur chaque tranche afin qu'aucun lot ne dépasse les limites du modèle (comme le plafond de 1 048 576 tokens de Gemini).
2. **Map :** chaque lot est envoyé à l'IA, qui renvoie un résumé technique de ce qui a changé dans cette partie. La console affiche la progression :

   ```text
   📦 Diff géant détecté ! Traitement en 4 lots (Map-Reduce)...
   ⏳ Analyse du lot 1/4...
   ⏳ Analyse du lot 2/4...
   ```

3. **Reduce :** les résumés partiels sont unifiés et envoyés dans un appel final qui génère le résultat réel — le message de commit (`-c`), la revue de code (`-r`/`-f`) ou la description de la Pull Request (commande par défaut). Si l'ensemble des résumés dépasse le seuil de déclenchement, une réduction intermédiaire consolide proprement les résumés avant l'analyse finale.

## 💡 Bon à savoir

- **Entièrement automatique :** aucune option à activer. Le découpage ne s'active que lorsque le diff dépasse la limite de déclenchement (**90 000 tokens** par défaut) ; les diffs plus petits continuent d'utiliser un seul appel à l'IA.
- **Plafonds configurables par fournisseur :** vous pouvez personnaliser à la fois le seuil de déclenchement (`GITPR_MAP_REDUCE_MAX_TOKENS`) et la taille maximale de chaque lot (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`), globalement ou spécifiquement par fournisseur (`GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`) via `gitpr config` ou dans `~/.gitpr/.env`. Voir aussi l'[ADR-0022](adr/0022-map-reduce-per-provider-token-partitioning.md).
- **Même fournisseur et même modèle :** les lots utilisent le moteur d'IA que vous avez configuré (Gemini, DeepSeek ou Ollama), avec une pause d'une seconde entre les appels pour respecter les limites de requêtes.
- **Les smart excludes passent d'abord :** les fichiers lock, les assets minifiés et autres bruits sont retirés du diff avant l'estimation de taille — ce qui évite souvent complètement le découpage.
- **Compromis de qualité :** le résultat final est généré à partir de résumés techniques plutôt que du diff brut ; les détails très fins peuvent donc être condensés. Pour les branches géantes, découper le travail en PRs plus petites reste la meilleure matière à donner à l'IA.

🔗 Dépôt : [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
