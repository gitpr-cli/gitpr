# Documentation Technique : Mode Mentor Junior (gitpr mentor / --mentor)

`gitpr mentor` transforme les observations de revue de code en retours pédagogiques, concrets et formateurs. Conçu pour les développeurs juniors et en apprentissage, il explique **ce qui** se passe, **pourquoi** c'est important en pratique, des **analogies** simples et des concepts clés **pour en savoir plus**.

Cette fonctionnalité est strictement **additive et optionnelle (opt-in)** : l'analyse technique d'origine n'est jamais modifiée ni supprimée.

---

## 1. Vue d'Ensemble

Le Mode Mentor Junior fonctionne sur deux surfaces :

1. **Option `-r --mentor` / `-f --mentor`** : Exécute la revue de code standard et ajoute automatiquement la section `## 🎓 Mentor (Conseils pour Juniors)` à la fin du fichier généré (`*_PR_REVIEW.txt` ou `*_PR_FULLREVIEW.txt`).
2. **Commande `gitpr mentor [--finding <id>]`** : Lit les observations de la dernière revue et affiche les explications directement dans le terminal.

### 1.1 Référence des Commandes

```bash
gitpr -r --mentor              # Exécute la revue locale et ajoute la section Mentor
gitpr -f --mentor              # Exécute la revue complète et ajoute la section Mentor
gitpr mentor                   # Explique les observations de la dernière revue dans le terminal
gitpr mentor --finding FIX-002 # Explique une observation précise selon son identifiant
gitpr mentor --provider gemini # Force un fournisseur d'IA spécifique
```

---

## 2. Configuration (`~/.gitpr/.env`)

| Clé | Type | Défaut | Description |
|---|---|---|---|
| `GITPR_REVIEW_MENTOR_MODE` | booléen | `false` | Si `true`, active automatiquement le mode mentor pour `-r` et `-f`. |
| `GITPR_MENTOR_INCLUDE_ANALOGY` | booléen | `true` | Si `false`, omet les analogies dans les explications. |

