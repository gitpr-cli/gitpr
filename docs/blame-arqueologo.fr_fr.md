# Documentation technique : Archéologue de code avec Git Blame (--blame)

L'**Archéologue de code** de GitPR utilise `git blame` combiné à l'intelligence artificielle pour retracer l'origine et l'évolution des règles métier dans votre code. Il classe chaque commit comme **ORIGEM** (création de la règle) ou **REFATORACAO** (modification ultérieure) et génère une chronologie détaillée.

---

## 1. Syntaxe et formats

### 1.1 Mode direct (lignes spécifiques)

```bash
gitpr -b src/core.py:140-195    # Range de linhas
gitpr -b src/main.py:42          # Linha única
```

### 1.2 Mode interactif

```bash
gitpr -b src/core.py             # O GitPR perguntará quais linhas
```

Le terminal affichera :
```
📂 Arquivo selecionado: src/core.py
Quais linhas você deseja investigar? (Ex: 10-20 ou apenas 45)
```

---

## 2. Comment ça fonctionne

1. **`git blame`** capture l'auteur, la date et le hash de chaque ligne dans le range spécifié
2. L'IA **classe** chaque commit comme `ORIGEM` (a créé la règle métier) ou `REFATORACAO` (a modifié du code existant)
3. Le moteur retrace jusqu'à **4 niveaux de commits parents** pour comprendre l'évolution complète
4. Le résultat est affiché dans le terminal (en couleur) et enregistré comme rapport Markdown

### Sortie dans le terminal

- 🟢 **Vert** = Commit d'ORIGEM
- 🟡 **Jaune** = Commit de REFATORACAO

---

## 3. Intégration avec les Issues

L'Archéologue peut alimenter la génération d'**Issues de dette technique** :

```bash
gitpr -is -b src/legacy/parser.py:200-350
```

Dans ce mode, l'IA génère une issue expliquant **comment le bloc a évolué** et **pourquoi il doit être refactorisé**, en utilisant la chronologie du blame comme contexte.

---

## 4. Sélection du fournisseur d'IA

```bash
gitpr -b arquivo.py:10-50 -p gemini
gitpr -b arquivo.py:10-50 -p deepseek
```

> **Note :** L'Archéologue utilise le modèle **secondaire** (moins cher) pour la classification des commits et le modèle **primaire** (avancé) pour le résumé exécutif final, optimisant la consommation des quotas.
