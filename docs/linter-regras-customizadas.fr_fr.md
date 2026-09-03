# **Documentation technique : Linter statique personnalisable (--linter)**


GitPR CLI dispose d'un moteur d'analyse statique ultra-rapide qui s'exécute localement, sans consommer de quotas d'IA ni nécessiter de connexion internet. Il analyse uniquement les **lignes modifiées ou ajoutées** dans votre git diff, garantissant un retour instantané.

## **1. Comment exécuter le Linter**

Vous pouvez déclencher le linter de trois manières :

1. **Manuellement :** En exécutant gitpr --linter dans le terminal.  
2. **Via le Pre-commit Hook :** Automatiquement avant chaque commit (installé via gitpr -ih).  
3. **Via CI/CD :** Dans GitHub Actions, bloquant le merge si le code retourne un exit code 1.

---

## **2. Structure du fichier .gitpr.linter.yml**

Les règles du Linter résident dans le fichier .gitpr.linter.yml à la racine de votre projet. Le fichier est lu à chaque exécution et possède la structure YAML suivante :

```YAML

rules:  
  - name: "identifiant-de-la-regle"  
    extensions: ["js", "php", "py"] \# Extensions où la règle s'applique  
    regex: 'votre-expression-reguliere-ici'  
    message: "🚨 Message d'erreur qui apparaîtra dans le terminal ({file\_name}, Ligne {line\_number})"  
    ignore\_comments: true \# Ignore si la regex correspond à l'intérieur d'un commentaire (//, \#, /\*)  
    ignore\_paths: \# Optionnel : Dossiers où cette règle NE doit PAS s'exécuter  
      \- "vendor/\*"  
    require\_paths: \# Optionnel : Dossiers exclusifs où cette règle DOIT s'exécuter  
      \- "routes/\*"

external_linters:
  - name: "ESLint (JavaScript/TypeScript)"
    extensions: ["js", "ts", "vue", "jsx", "tsx"]
    command: "npx eslint --format checkstyle"

## ---

## **3. Tutoriel : Créer des règles avec des expressions régulières (Regex)**

Le moteur de GitPR utilise la bibliothèque Regex native de Python (re). Le secret d'une bonne règle de Linter est d'être suffisamment restrictive pour attraper l'erreur, mais suffisamment flexible pour ignorer les espaces blancs supplémentaires.

### **Exemple pratique 1 : Interdire les verbes dans les routes (Standard RESTful)**

**Le problème :** Dans le standard REST, les URLs ne doivent pas contenir de verbes (ex : /api/buscar-usuarios), mais plutôt des substantifs et des méthodes HTTP appropriées (GET /api/usuarios).

Voici comment configurer une règle dans Laravel (PHP) pour empêcher cela :

```YAML

  \- name: "check-route-verbs"  
    extensions: \["php"\]  
    require\_paths:  
      \- "routes/\*"  
    regex: 'Route::\[a-zA-Z\]+\\s\*\\(\\s\*\[''"\](get|get-|busca|buscar|procura|procurar|pesquisa|pesquisar|lista|listar)'  
    message: "🚨 URI inappropriée dans {file\_name} (Ligne {line\_number}). Évitez les verbes comme 'buscar' ou 'listar' dans l'URL. Utilisez le standard RESTful."  
    ignore\_comments: true

#### **Décortiquer la Regex ci-dessus :**

Pour comprendre comment créer les vôtres, voyez comment celle-ci a été construite pièce par pièce :

* Route:: → Cherche exactement l'appel de la Facade de Laravel.  
* [a-zA-Z]+ → Capture n'importe quelle méthode HTTP qui vient ensuite (ex : get, post, put).  
* \s\*(\s\* → Le \s\* signifie « zéro ou plusieurs espaces ». Cela garantit que le Linter attrape aussi bien Route::get(' que Route::get ( '.  
* [''"] → Accepte aussi bien les guillemets simples que les guillemets doubles pour ouvrir la chaîne de l'URL.  
* (get|get-|busca|buscar...) → Le groupe de capture principal. Le pipe | fonctionne comme un « OU ». Si l'un de ces mots est détecté au tout début de l'URL, la règle échoue.

### **Exemple pratique 2 : Bloquer les logs de débogage oubliés**

**Le problème :** Les développeurs oublient fréquemment des commandes de débogage dans le code avant de faire le commit.

**Règle pour PHP (dd ou dump) :**

```YAML

  \- name: "check-php-debug"  
    extensions: \["php"\]  
    regex: '\\b(dd|dump|var\_dump|print\_r)\\s\*\\('  
    message: "🚨 Code de débogage oublié ({file\_name}, Ligne {line\_number})."  
    ignore\_comments: true

*Astuce Regex :* Le \b (Word Boundary) garantit que le mot est exact. Il attrape la commande dd(), mais ignore le mot add(), évitant les faux positifs.

**Règle pour JavaScript (console.log) :**

```YAML

  - name: "check-js-console"  
    extensions: \["js", "ts", "vue"\]  
    regex: 'console\\.(log|debug|info)\\s\*\\('  
    message: "🚨 Utilisation de console.log non autorisée en production ({file\_name}, Ligne {line\_number})."  
    ignore\_comments: true

*Astuce Regex :* Le point \. a besoin d'une barre oblique inversée (échappement), car dans le langage Regex, un point seul signifie « n'importe quel caractère ».

---

## **4. Astuces en or pour la Regex dans le Linter**

1. **Échappez les caractères spéciaux :** Des symboles comme ( ) [ ] { } . \* \+ ? ^ $ ont des fonctions mathématiques dans la Regex. Si vous voulez les rechercher dans le code, placez une barre oblique devant (ex : \( pour trouver une parenthèse ouvrante).  
2. **Attention aux guillemets en YAML :** Dans le fichier .yml, entourez toujours votre regex : de guillemets simples '...'. Si votre regex a besoin d'un guillemet simple à l'intérieur, doublez-le '' ou utilisez des guillemets doubles à l'extérieur "...".  
3. **Utilisez le \s\* sans modération :** Ne présumez jamais que le formatage du code est parfait. Utilisez \s\* pour couvrir les espaces blancs, les tabulations et les sauts de ligne entre les commandes.

---

## **5. Intégration avec les Linters Externes (Bridge via Checkstyle)**

GitPR CLI n'a pas besoin de réinventer la roue. Si votre projet utilise déjà des outils comme PHP_CodeSniffer, ESLint ou Stylelint, GitPR peut servir de pont, en exécutant ces outils en arrière-plan et en filtrant les erreurs **uniquement pour les lignes que vous avez modifiées dans votre Pull Request actuel**.

Pour cela, le linter externe doit prendre en charge la sortie de rapports au format `checkstyle` (standard universel en CI/CD).

### **Délai d'Attente (Timeout) du Linter Externe**

Chaque sous-processus de linter externe est limité par un **délai d'attente
(timeout) de 120 secondes** (configurable via `GITPR_LINTER_TIMEOUT` dans
`~/.gitpr/.env`). Si un linter dépasse la limite, il est ignoré — ses
violations n'entrent pas dans le rapport — au lieu de bloquer toute la revue.
Les valeurs invalides ou non positives reviennent à la valeur par défaut de 120s.

### **Configuration rapide (--linter-setup)**

Au lieu de configurer le YAML manuellement, vous pouvez utiliser notre assistant interactif :
Exécutez dans le terminal :
`gitpr --linter-setup`

L'assistant affichera des options préconfigurées, vous guidera sur la commande d'installation dans votre projet (ex : `npm install --save-dev eslint`) et injectera automatiquement la bonne configuration dans votre `.gitpr.linter.yml`.

Les presets de l'assistant sont contrôlés à distance via le fichier `templates/gitpr.linter-presets.json` (cache local dans `~/.gitpr/conf/`), ce qui permet d'ajouter de nouveaux linters sans attendre une nouvelle version de GitPR.

---

## **6. Rapports d'Analyse (Markdown)**

Chaque fois que le linter s'exécute (que ce soit manuellement via `--linter` ou automatiquement avant le commit), il consolidera les erreurs générées par les Règles de Regex et les Linters Externes dans un rapport unique.

Ce rapport formaté en Markdown sera enregistré automatiquement, conservant un historique de vos audits locaux.

**Emplacement par défaut :** `.gitpr/reports/linter/`

**Personnalisation :** Vous pouvez modifier le nom et le dossier de ce fichier en définissant la variable `OUTPUT_FILE_NAME_LINTER` dans votre fichier `~/.gitpr/.env`.
