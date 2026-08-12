# Documentation technique : Intégration des Git Hooks locaux (GitPR)

Cette documentation détaille l'architecture et l'utilisation de la fonctionnalité de Git Hooks automatiques de GitPR CLI. L'implémentation adopte la pratique du ****Shift Left****, en amenant la validation du code et la génération de messages (IA) au moment exact du commit, avant toute intégration avec le serveur distant.

---

## 1. Installation automatisée

Pour installer les hooks dans votre dépôt local, naviguez jusqu'à la racine du projet (là où réside le dossier caché `.git`) et exécutez :

```bash  
gitpr --installhooks  
# ou  
gitpr -ih  
```

**Ce que cette commande fait sous le capot :**

1. Vérifie l'intégrité du répertoire .git/hooks.  
2. Télécharge la version la plus récente des scripts pre-commit et prepare-commit-msg directement depuis le dépôt officiel de GitPR.  
3. Applique automatiquement les permissions d'exécution POSIX (chmod +x) aux fichiers, garantissant la compatibilité entre Linux, macOS et les environnements Git Bash sous Windows.

---

## **2. Hook : pre-commit (Linter statique)**

Le hook pre-commit agit comme un « garde du corps » local. Il est déclenché instantanément lors de l'exécution de git commit, avant que le message de commit ne soit demandé.

### **Comment ça fonctionne :**

* Le script invoque la commande gitpr --linter.  
* GitPR analyse le diff actuel (fichiers en *stage*) par rapport aux règles définies dans le fichier .gitpr.linter.yml.  
* **Exit Code 0 :** S'il n'y a pas de violations, le flux de Git continue normalement.  
* **Exit Code 1 :** Si des chaînes interdites (ex : console.log, mots de passe, localhost) sont détectées, le script intercepte l'action, affiche les alertes dans le terminal et **interrompt le commit**.

### **Voie de secours (Bypass)**

S'il existe un besoin strict de contourner la validation du Linter local (par exemple, lors de la publication d'un code de débogage temporaire dans une branche isolée), utilisez le flag natif de Git :

Bash

git commit --no-verify -m "Votre message ici"

---

## **3. Hook : prepare-commit-msg (IA Auto-Commit)**

Ce hook élimine le besoin d'écrire manuellement les messages de commit. Il intègre l'intelligence artificielle de Gemini directement dans le cycle de vie de Git, générant des messages au format *Conventional Commits* basés sur votre code.

### **Comment ça fonctionne :**

1. Ajoutez vos fichiers au stage (git add .).  
2. Exécutez uniquement la commande de base de commit, sans passer le message :  
   ```bash  
   git commit
   ```

3. Le hook entre en action en affichant le message : 🤖 GitPR : Demande de suggestion de commit à l'IA...  
4. GitPR exécute le flag caché --hook, en envoyant votre *diff* à Gemini.  
5. L'IA génère le message et le script injecte proprement le résultat dans la première ligne du fichier temporaire de Git.  
6. Votre éditeur de texte par défaut (Vim, Nano, VS Code) s'ouvrira avec le message déjà rempli. Il vous suffit d'enregistrer et de fermer pour confirmer le commit.

### **Préservation du flux manuel**

Le script est suffisamment intelligent pour ne pas écraser votre intention. Si vous exécutez le commit en passant le flag de message explicite (-m), le hook reconnaît l'origine comme « message » et **désactive silencieusement le traitement de l'IA** :

```bash

# L'IA NE sera PAS déclenchée dans ce cas, respectant votre message.  
git commit -m "fix: corrige un problème de concurrence dans l'API"
```

Les messages de fusion et générés par git sont également préservés. Lorsque le message provient
de git lui-même — `git pull`/`git merge` (origine « merge »), `git merge --squash`
(origine « squash ») ou `git commit --amend`/`-c`/`-C` (origine « commit ») — le hook
**désactive silencieusement l'IA**, sans jamais toucher au message de fusion.

---

## **4. Résolution de problèmes (Troubleshooting)**

* **Le Hook ne s'exécute pas (Linux/macOS) :** Assurez-vous que les fichiers dans .git/hooks ont la permission d'exécution. Vous pouvez la forcer avec chmod \+x .git/hooks/pre-commit.  
* **Commande introuvable :** Les scripts des hooks sont configurés pour chercher aussi bien l'installation globale (gitpr) que l'exécution locale via environnement virtuel (pipenv run python run.py). Si vous utilisez un gestionnaire de dépendances différent (comme Poetry), il pourra être nécessaire d'éditer les scripts à l'intérieur du dossier .git/hooks pour refléter votre environnement.
