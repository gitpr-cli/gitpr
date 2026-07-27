# Métriques et Télémétrie — Analytics Local Hors Ligne

GitPR inclut un **système de télémétrie local et hors ligne** qui collecte des
événements d'utilisation anonymes (commandes CLI, appels IA, exécutions du linter,
git hooks) pour l'analytique d'équipe. Rien ne quitte votre machine — toutes les
données restent dans `~/.gitpr/metrics/`.

## ✨ Ce Que Cela Fait

Chaque commande GitPR génère un petit fichier JSON d'événement enregistrant :

| Champ | Description |
|-------|-------------|
| `timestamp` | Quand l'événement s'est produit (ISO 8601) |
| `command` | Quelle commande a été exécutée (`commit`, `review`, `fullreview`, `linter`, `blame`, etc.) |
| `status` | Résultat (`success`, `error`, `triggered`, `no_changes`) |
| `provider` | Fournisseur d'IA utilisé (`gemini`, `deepseek`, `ollama`, `local`) |
| `tokens_estimated` | Nombre de tokens d'après les métadonnées d'utilisation de l'IA |
| `duration_ms` | Durée de la commande en millisecondes |
| `repo` | Nom du dépôt (`propriétaire/dépôt`) |
| `branch` | Nom de la branche actuelle |

Des champs supplémentaires comme `linter_errors`, `linter_warnings`, `cache_hit`
et `map_reduce_triggered` fournissent un contexte plus approfondi pour des types
de commandes spécifiques.

## 📁 Où les Données Sont Stockées

```
~/.gitpr/metrics/
├── {owner}/{branch}/
│   ├── XXXX-XXXXX-XXXX_20260726.json   ← fichier d'événement
│   └── YYYY-YYYYY-YYYY_20260726.json
├── config.json                          ← état d'exportation
└── export/
    ├── gitpr_metrics_2026-07-26.csv     ← CSV consolidé
    └── gitpr_metrics_2026-07-26.json    ← JSON consolidé
```

Chaque fichier d'événement est nommé avec un UUID unique et une date pour éviter
les collisions.

## 🚀 Commandes CLI

### Afficher le Résumé

```bash
gitpr --metrics
```

Affiche le total des fichiers, l'utilisation disque et le chemin du répertoire
de métriques.

### Exporter les Données

```bash
gitpr --metrics --export
```

Analyse tous les fichiers d'événements non exportés, les consolide en rapports
CSV et JSON dans `~/.gitpr/metrics/export/` et suit les fichiers déjà traités.

- **Colonnes CSV :** timestamp, command, status, provider, tokens_estimated,
  duration_ms, repo, branch
- **JSON :** tableau complet des charges d'événements
- **Barre de progression :** retour visuel via `click.progressbar()`

### Purger les Données

```bash
gitpr --metrics --purge
```

Supprime tous les fichiers de métriques locaux après confirmation. Préserve
`config.json` pour le suivi futur des exportations.

### Tableau de Bord Interactif

```bash
gitpr --metrics --dashboard
```

Lance un **tableau de bord TUI** (Textual) affichant :

- **Barre de résumé :** total d'événements, erreurs, total de tokens, commandes principales, fournisseurs principaux
- **Tableau d'événements :** 100 derniers événements avec horodatage, commande, statut, fournisseur, tokens, durée
- **Raccourcis :** `F5` pour actualiser, `Esc` pour quitter

## 🔧 Git Hooks (Collecte Automatique)

Lorsqu'ils sont installés via `gitpr --installhooks`, trois hooks supplémentaires
collectent la télémétrie comportementale :

| Hook | Événement capturé |
|------|------------------|
| `post-checkout` | Changements de branche (changements de contexte) |
| `pre-push` | Événements de push (fréquence de livraison) |
| `post-merge` | Événements de pull/merge (fréquence d'intégration) |

Ces hooks utilisent `gitpr --hook-event <nom> --quiet` — un flag caché qui
enregistre l'événement silencieusement sans sortie.

## 📊 Cas d'Usage

- **Tech Lead :** Savoir si l'équipe utilise réellement les révisions IA ou ignore les hooks
- **Finance :** Comparer l'utilisation de Gemini vs. DeepSeek vs. Ollama pour optimiser les coûts d'API
- **Qualité :** Identifier les modules qui déclenchent le plus d'erreurs de linter ou d'analyses de blame
- **Processus :** Détecter si le map-reduce se déclenche souvent (PRs volumineuses — potentiel problème de processus)

## 🔒 Confidentialité

- **100% local** — aucune donnée n'est jamais envoyée à des serveurs externes
- **Anonyme** — les événements contiennent repo/branch mais aucun contenu de fichiers ou diffs
- **Contrôlé par l'utilisateur** — l'exportation et la purge sont manuelles ; rien n'est supprimé automatiquement
- **Hooks optionnels** — les git hooks ne s'installent que si vous exécutez `gitpr --installhooks`

## 📚 Documentation Connexe

- [Intégration MCP](mcp-integration.md) — Configuration du serveur MCP
- [MCP Prompts](mcp-prompts.md) — Modèles de message prédéfinis
- [MCP Tool Annotations](mcp-annotations.md) — Conseils d'intégration avec les IDEs

---
**Conseil de pro :** Combinez les exportations de métriques avec le pipeline CI
de votre équipe en exécutant `gitpr --metrics --export` de façon planifiée et
en versionnant le CSV dans votre dépôt.
