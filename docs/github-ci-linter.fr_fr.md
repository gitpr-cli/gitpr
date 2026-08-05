# **Documentation Technique : Intégration du Linter Local avec GitHub Actions**

Cette documentation décrit le processus de mise en œuvre de `gitpr --linter` comme un "Quality Gate" dans le cycle de vie du développement, empêchant le code qui viole les règles statiques du projet d'être fusionné dans la branche principale.

---

## **1. Fonctionnement Technique**

La commande `gitpr --linter` est conçue pour fonctionner avec des **codes de sortie (exit codes)** sémantiques :

* **Code de sortie 0 :** Succès. Aucune violation détectée.  
* **Code de sortie 1 :** Échec. Violations détectées (bloque le workflow GitHub).

Contrairement aux modes IA, le mode linter ne nécessite pas de clés d'API, ce qui le rend idéal pour les environnements d'exécution éphémères.

---

## **2. Configuration du Workflow (.yml)**

Créez le fichier `.github/workflows/gitpr-linter.yml` dans votre dépôt avec la configuration ci-dessous. Cette action sera déclenchée sur toutes les Pull Requests ciblant les branches `main` ou `develop`.

```yaml
name: 🛡️ GitPR Static Analysis

on:  
  pull_request:  
    branches: [ "main", "develop" ]

jobs:  
  linter-validation:  
    runs-on: ubuntu-latest  
      
    steps:  
      - name: 📥 Extraire le Dépôt  
        uses: actions/checkout@v4  
        with:  
          # Nécessaire pour permettre le 'git diff' par rapport à la branche de base  
          fetch-depth: 0 

      - name: 🐍 Configurer l'Environnement Python  
        uses: actions/setup-python@v5  
        with:  
          python-version: '3.12'

      - name: ⚙️ Installer les Dépendances  
        run: |  
          git clone https://github.com/natanfiuza/gitpr.git /tmp/gitpr  
          pip install google-genai python-dotenv click cryptography pyyaml

      - name: 🚨 Exécuter le Linter Local  
        # Le workflow échouera automatiquement si le code de sortie est 1  
        run: python /tmp/gitpr/src/main.py --linter
```

---

## **3. Verrouillage du Bouton de Fusion (Branch Protection)**

Le simple fait de configurer le fichier `.yml` n'empêche pas physiquement la fusion ; il indique uniquement l'échec. Pour "verrouiller" le bouton de fusion, suivez ces étapes dans l'interface GitHub :

1. Allez dans **Settings** > **Branches**.  
2. Dans **Branch protection rules**, cliquez sur **Add rule** (ou Edit sur la règle de `main`).  
3. Cochez l'option : **"Require status checks to pass before merging"**.  
4. Dans la barre de recherche qui apparaît, recherchez : `linter-validation` (ou le nom du job défini dans votre YAML).  
5. Cochez également **"Require branches to be up to date before merging"** pour garantir que le diff testé soit le plus récent.  
6. Cliquez sur **Save changes**.

---

## **4. Avantages de la Mise en Œuvre**

* **Zéro Latence IA :** La validation repose sur des Regex locales et prend quelques millisecondes.  
* **Coût Zéro :** Ne consomme pas de jetons d'API Gemini.  
* **Sécurité :** Bloque les chaînes sensibles (mots de passe, IP de test, journaux de débogage) avant la revue de code humaine.
