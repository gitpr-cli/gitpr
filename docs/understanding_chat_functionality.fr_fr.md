# Comprendre le Chat Interactif GitPR

Le Chat Interactif GitPR est un **assistant de pair-programming IA** qui s'exécute directement dans votre terminal. Il voit vos modifications non validées (`git diff`) et maintient une conversation contextuelle pour vous aider à comprendre, refactoriser, tester et optimiser votre code.

## Démarrer le Chat

```bash
gitpr -ch
# ou
gitpr --chat
```

Pour remplacer la langue de l'interface pour une seule session :

```bash
gitpr --lang en_us -ch
gitpr --lang fr_fr -ch
```

## Raccourcis Clavier

| Touche | Action | Description |
|--------|--------|-------------|
| **F1** | Aide | Ouvre un modal affichant tous les raccourcis et commandes slash |
| **F2** | Actualiser le Diff | Met à jour le contexte de l'IA avec les dernières modifications du code |
| **F5** | Auto-Patch | Extrait les blocs de code de la dernière réponse de l'IA et les sauvegarde |
| **F6** | Exporter | Sauvegarde toute la conversation dans un fichier Markdown structuré |
| **Esc** | Quitter | Ferme l'application de chat |

## Commandes Slash

Tapez `/` dans le champ de saisie pour voir une liste déroulante des commandes disponibles. Continuez à taper pour filtrer.

| Commande | Description |
|----------|-------------|
| `/explain` | Explique le diff actuel ligne par ligne |
| `/tests` | Génère des tests unitaires pour les fonctions modifiées |
| `/optimize` | Analyse la complexité cyclomatique et suggère des améliorations de performance |
| `/clear` | Efface la conversation et démarre une nouvelle session de chat pour le diff actuel |

Vous pouvez taper une commande partielle (ex. : `/ex`) et appuyer sur **Entrée** — elle s'auto-complète.

## Mémoire et Sessions

Le chat persiste automatiquement votre conversation et l'historique des diffs sur le disque :

- **Emplacement :** `~/.gitpr/cache/chat/<UUID>/`
- **Clé de session :** Un UUID unique de 15 caractères (format `XXXX-XXXXX-XXXX`) généré par branche et dépôt
- **Persistance :** Revenir sur la même branche rouvre la session existante avec tout l'historique de conversation
- **Suivi des diffs :** Chaque modification de code est enregistrée. L'IA sait quand vous avez modifié des fichiers et met à jour son contexte

## Auto-Patch (F5)

Lorsque l'IA suggère des modifications de code (dans des blocs Markdown), appuyez sur **F5** pour les extraire et les sauvegarder :

1. La dernière réponse de l'IA est analysée à la recherche de blocs de code avec triples backticks (` ```python ... ``` `)
2. Tous les blocs sont concaténés et sauvegardés dans `GITPR_PATCH_SUGGESTION_<clé-aléatoire>.txt`
3. Chaque clé est unique (format `aB3-xK9`), donc les patches précédents ne sont jamais écrasés

Examinez le fichier généré et appliquez les modifications manuellement à votre projet.

### Actions par Message (Ctrl+Shift+A / Ctrl+Shift+E)

Vous pouvez appliquer Auto-Patch et Exporter à **n'importe quel** message de l'IA dans la conversation, pas seulement au dernier.

Naviguez entre les messages de l'IA avec **F7** et **F8**. Le message sélectionné est mis en évidence avec une bordure gauche plus brillante, et une barre d'actions apparaît au-dessus du champ de saisie.

- **Ctrl+Shift+S** — Extrait les blocs de code uniquement du **message sélectionné** et les sauvegarde dans `GITPR_PATCH_SUGGESTION_<clé>.txt`
- **Ctrl+Shift+E** — Exporte uniquement le **message sélectionné** vers `MESSAGE_<id-session>_<clé>.md`

Le focus par défaut est toujours la réponse la plus récente de l'IA.

## Exporter (F6)

Appuyez sur **F6** pour sauvegarder toute la conversation dans un fichier Markdown structuré :

- **Nom du fichier :** `GITPR_CHAT_EXPORT_<uuid-de-session>.md`
- **Format :** Chaque message est étiqueté avec son rôle (Utilisateur / Assistant IA / Système) et séparé par des lignes horizontales
- **Cas d'usage :** Documentation, partage avec l'équipe, ou alimentation de contexte pour d'autres outils IA

## Actualiser le Diff (F2)

Pendant que vous codez dans un autre éditeur, appuyez sur **F2** pour mettre à jour le contexte du chat :

- Si de nouvelles modifications sont détectées depuis le dernier snapshot du diff, l'IA est notifiée et peut voir vos dernières éditions
- Si rien n'a changé, un message de confirmation est affiché

## Quitter le Chat

Appuyez sur **Esc** ou **Ctrl+C** pour fermer le chat. Votre session est automatiquement sauvegardée.

## Conseils

- Utilisez `/clear` pour repartir de zéro si la conversation devient trop longue ou si vous voulez changer de sujet
- Combinez `--lang` avec `--provider` pour personnaliser la langue et le modèle IA : `gitpr --lang fr_fr --provider gemini -ch`
- Les fichiers `GITPR_CHAT_EXPORT_*.md` peuvent être commités dans votre dépôt comme notes de développement
