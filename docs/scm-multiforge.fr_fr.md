# Documentation Technique : SCM Multi-Forge (ScmProvider)

GitPR publie les Pull Requests et les issues via une abstraction unique, le `ScmProvider`, qui prend en charge quatre forges d'hébergement Git : GitHub, GitLab, Bitbucket Cloud et Azure DevOps. Chaque flux de publication — l'éditeur interactif de PR (mode par défaut), la publication directe (`--no-edit`) et la TUI des issues (`-is`) — résout le provider configuré à partir du remote `origin` du dépôt et appelle l'API du forge via celui-ci.

Sans configuration SCM, GitPR conserve le comportement hérité exclusif à GitHub — zéro migration et sortie byte-identique.

---

## 1. Forges Prises en Charge

| Forge | Clé du provider | Base d'API par défaut | Authentification |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Nom d'utilisateur + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Détection Automatique à partir du Remote Origin

Le forge actif est détecté à partir de l'URL du remote `origin` par correspondance de sous-chaîne sans tenir compte de la casse :

| L'URL du remote contient | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` ou `visualstudio.com` | `azure_devops` |
| toute autre valeur (par défaut) | `github` |

```bash
git remote get-url origin
# git@github.com:gitpr-cli/gitpr.git               -> github (par défaut)
# https://gitlab.com/acme/platform/web-app.git     -> gitlab
# https://bitbucket.org/acme/web-app               -> bitbucket
# https://dev.azure.com/acme/project/_git/web-app  -> azure_devops
```

Le dépôt est adressé via `RepoRef`, extrait de l'URL du remote. Le **workspace** est le propriétaire (owner) GitHub, le namespace GitLab (sous-groupes inclus), le workspace Bitbucket ou — sur Azure DevOps — une étiquette `{org}/{project}` à titre d'affichage uniquement, car les appels d'API utilisent le `organization` et le `project` de la configuration.

---

## 2. Configuration Initiale — `gitpr --init`

L'assistant interactif détecte le forge, valide le token d'accès et persiste la configuration :

```bash
gitpr --init
```

| Étape | Ce qui se passe |
| --- | --- |
| 1. Détection du forge | Détecte le forge à partir du remote `origin` et demande confirmation (vous pouvez choisir un autre forge) |
| 2. Extras du provider | Azure DevOps demande `organization` et `project` ; Bitbucket demande le `username`, qui fait partie de l'identifiant |
| 3. Base d'API | Base d'API personnalisée pour chaque forge sauf GitHub (GitLab/Azure DevOps self-managed, enterprise) |
| 4. Token | Demande le PAT — ou l'App Password sur Bitbucket |
| 5. Validation | `test_connection()` — jusqu'à 3 tentatives ; HTTP 401 (token expiré) redemande en jaune, les autres échecs interrompent en rouge |
| 6. Persistance | Uniquement en cas de succès : écrit `GITPR_SCM_PROVIDER`, le token chiffré Fernet et les extras dans `~/.gitpr/.env` |

Rien n'est écrit quand la validation échoue. Relancez `gitpr --init` à tout moment pour changer de forge ou renouveler un token expiré.

---

## 3. Configuration Manuelle (.env)

Alternative à l'assistant : modifiez `~/.gitpr/.env` directement. Consultez le [guide d'intégration du GitHub PAT](github-pat-integration.md) pour comprendre comment GitPR protège les tokens au repos.

| Variable | Forge | Description |
| --- | --- | --- |
| `GITPR_SCM_PROVIDER` | tous | Clé du provider actif (`github`, `gitlab`, `bitbucket`, `azure_devops`) ; vide = comportement hérité GitHub |
| `GITPR_SCM_TOKEN` | tous | Token brut, réservé aux environnements CI/CD |
| `GITPR_SCM_TOKEN_ENCRYPTED` | tous | Token chiffré Fernet, écrit par `gitpr --init` et par le flux de réauthentification |
| `GITPR_SCM_BASE_URL` | tous | Base d'API personnalisée (self-managed/enterprise) ; vide = SaaS public |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Nom de l'organisation — obligatoire (l'erreur fail-fast nomme la variable manquante) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Nom du projet — obligatoire |
| `GITPR_SCM_USERNAME` | `bitbucket` | Nom d'utilisateur Bitbucket — obligatoire (App Password en HTTP Basic) |

GitHub sans configuration SCM conserve le stockage hérité `GITHUB_TOKEN_ENCRYPTED` — zéro migration.

---

## 4. Utiliser GitPR avec le Forge Configuré

### 4.1 Publication de Pull Requests

```bash
gitpr                # Éditeur interactif (TUI) — révisez et confirmez la PR
gitpr --no-edit      # Publie directement, avec auto-commit (ignore la TUI)
gitpr --no-publish   # Génère uniquement le fichier de description de la PR (.md), sans TUI
```

L'éditeur résout le provider à partir du remote `origin`, convertit le dépôt en `RepoRef` et crée le pull request via `provider.create_pull_request()`. Le numéro, l'URL et l'état de la PR renvoyés par le forge sont affichés dans la TUI et enregistrés dans le fichier de sortie.

### 4.2 Issues

```bash
gitpr -is            # Flux d'issue : brouillon IA -> TUI -> F3 crée l'issue sur le forge
```

F3 appelle `provider.create_issue()` sur le forge configuré. Azure DevOps n'a pas de ressource d'API pour les issues (les Work Items dépendent du modèle de processus du projet) ; GitPR vous invite donc à enregistrer le brouillon localement avec F2. Bitbucket exige que l'**Issue Tracker** du dépôt soit activé, sinon l'API répond 404.

### 4.3 Expiration du Token et Réauthentification (HTTP 401)

Quand le token est rejeté (HTTP 401), GitPR supprime le token expiré du `.env` et en demande un nouveau — jusqu'à 3 tentatives. Privilégiez les flux interactifs (`gitpr`, `gitpr -is`) pour vous réauthentifier : `--no-edit` publie directement et ne peut pas redemander.

---

## 5. Notes et Limites par Forge

### 5.1 GitHub

- Les installations existantes conservent un comportement exact (byte-parity) : payload, en-tête `Authorization: token` et stockage hérité `GITHUB_TOKEN_ENCRYPTED` inchangés.
- Les suggestions de relecteurs sont natives (`requested_reviewers`) ; désactivez-les avec `--no-suggest-reviewers`.

### 5.2 GitLab

- Merge requests : l'identifiant d'API est le `iid` du MR — jamais l'id global à l'échelle du projet.
- Brouillons : GitLab n'a pas de flag draft à la création d'un MR ; GitPR préfixe donc le titre avec `"Draft: "`.
- Les chemins de dépôt (groupes et sous-groupes) sont toujours URL-quoted.
- Le paramètre de stratégie de merge est ignoré — GitLab fusionne avec son action native.

### 5.3 Bitbucket Cloud

- Les identifiants reposent sur HTTP Basic : nom d'utilisateur + App Password. Le username est obligatoire (`GITPR_SCM_USERNAME`) et fait partie de l'identifiant.
- Les issues exigent l'Issue Tracker activé sur le dépôt.
- Stratégies de merge : `merge` -> `merge_commit`, `squash` et `fast_forward`.

### 5.4 Azure DevOps

- `organization` et `project` sont obligatoires — l'erreur fail-fast nomme les variables d'environnement manquantes.
- Chaque appel REST porte `api-version=7.1`.
- Les refs de branche utilisent le préfixe `refs/heads/`.
- Pas de diff unifié de PR via REST : `get_pull_request_diff()` renvoie un résumé textuel par fichier (`path (+adds −dels)`) de la dernière itération.
- Les issues ne sont pas prises en charge (`ScmNotSupportedError`) — enregistrez le brouillon localement avec F2.
- Les remotes hérités `*.visualstudio.com` sont acceptés par le détecteur.

---

## 6. Pour les Développeurs et les Plugins

L'abstraction vit dans `src/infrastructure/scm/` : le contrat `ScmProvider` dans `base.py`, un provider concret par forge et le registre dans `factory.py`. Le code interne résout les providers uniquement via `resolve_scm_provider()` et n'importe jamais les classes concrètes directement. Les méthodes des providers lèvent `ScmProviderError(provider, http_status, message)` — `http_status` vaut `0` en cas d'échec réseau — ou `ScmNotSupportedError` quand le forge n'a pas d'opération équivalente. Elles ne renvoient jamais les tuples hérités `(ok, data, status)`.

`src/github_api.py` est un **shim obsolète** : il expose encore les quatre fonctions héritées avec leurs retours en tuple pour les intégrations tierces, mais chaque appel lève un `DeprecationWarning`. Le nouveau code et les plugins doivent utiliser `resolve_scm_provider()`.

Registre de décision d'architecture et vocabulaire canonique : [ADR-001 Abstraction SCM](plans/ADR-001-scm-abstraction.md) et [Glossaire SCM Multi-Forge](plans/glossary-scm-multiforge.md).

> **Note :** Consultez aussi la [documentation d'intégration du GitHub PAT](github-pat-integration.md) pour créer des tokens et comprendre le chiffrement de GitPR (Fernet).
