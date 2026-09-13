# Documentation technique : Système de Skills et Templates (--skill)

GitPR utilise un système de **Skills** (Prompt Engineering) qui permet de personnaliser le comportement de l'intelligence artificielle selon les règles métier de votre entreprise. Les fichiers de template agissent comme des *System Instructions* de l'IA.

---

## 1. Télécharger les templates

```bash
gitpr -s
# ou
gitpr --skill
```

Cette commande crée les fichiers suivants dans le dossier `.gitpr/skill/` du projet :

| Fichier | Fonction |
| --- | --- |
| `.gitpr.commit.md` | Règles pour la génération de messages de commit |
| `.gitpr.pr.md` | Structure exigée pour la description de Pull Request |
| `.gitpr.review.md` | Focus d'architecture pour le code review de diffs |
| `.gitpr.filereview.md` | Règles de cohésion pour l'audit d'un fichier complet |
| `.gitpr.issue.md` | Structure et détail pour la génération d'Issues |
| `.gitpr.blame.md` | Focus de l'analyse archéologique du code |
| `.gitpr.linter.yml` | Règles de regex pour la validation statique |

> **Important :** La commande `--skill` **n'écrase jamais** les fichiers locaux existants. Si un `.gitpr.*.md` existe déjà, il est préservé.

---

## 2. Comment ça fonctionne

Chaque commande de GitPR recherche automatiquement le fichier de skill correspondant :

| Commande | Fichier de skill utilisé |
| --- | --- |
| `gitpr -c` | `.gitpr.commit.md` |
| `gitpr` (padrão) | `.gitpr.pr.md` |
| `gitpr -r` / `gitpr -f` | `.gitpr.review.md` |
| `gitpr -r -i arquivo` | `.gitpr.filereview.md` |
| `gitpr -is` | `.gitpr.issue.md` |
| `gitpr -b arquivo` | `.gitpr.blame.md` |
| `gitpr -l` / `gitpr -r` | `.gitpr.linter.yml` |

Si le fichier de skill n'existe pas, GitPR utilise un template interne par défaut.

---

## 3. Exemple de personnalisation

**Fichier `.gitpr.commit.md` :**

```markdown
Tous les messages de commit DOIVENT :
- Utiliser un préfixe JIRA obligatoire : [PROJ-1234]
- Suivre Conventional Commits (feat, fix, refactor...)
- Être écrits en portugais (Brésil)
- Ne pas dépasser 72 caractères sur la ligne de sujet
```

Après avoir créé ce fichier, toutes les exécutions de `gitpr -c` suivront ces règles.

---

## 4. Templates distants

Les templates officiels sont disponibles à l'adresse :
```
https://github.com/gitpr-cli/gitpr.git/tree/main/templates/
```

La commande `--skill` télécharge la version la plus récente de chaque template depuis le dépôt officiel.

> **Note :** Les fichiers de skill peuvent être committés dans le dépôt de votre équipe pour partager les règles avec tous les développeurs.

---

## 5. Modifier depuis l'écran `gitpr config`

L'écran `gitpr config` possède une section **Skills** qui liste ces mêmes fichiers et ouvre chacun dans un éditeur, pour ajuster une règle sans quitter le terminal ([Écran de Configuration Interactif](config-tui.fr_fr.md), §1.7).

- Une entrée par skill prise en charge par GitPR — les sept fichiers `.gitpr.*.md` de la section 1 ci-dessus.
- Un skill que le projet n'a pas encore est listé comme **absent de ce projet**, avec un bouton **📥 Télécharger le template** qui récupère le template publié pour votre langue d'interface.
- `F2` enregistre les skills modifiés en même temps que les paramètres du `.env` ; `Ctrl+R` dans le panneau abandonne la modification et remet le texte du disque.
- Chaque fichier conserve ses fins de ligne d'origine : enregistrer ne transforme donc jamais une ligne intacte en modification.

Deux choses restent volontairement hors de cette liste : `.gitpr.linter.yml`, qu'aucune commande ne charge par ce mécanisme ([Règles de Linter Personnalisées](linter-regras-customizadas.fr_fr.md)), et tout autre fichier que vous gardez dans `.gitpr/skill/` — l'écran propose les skills que les commandes lisent, pas tout ce que contient le dossier.
