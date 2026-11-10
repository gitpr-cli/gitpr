# Documentation Technique : SCM Multi-Forge (ScmProvider)

GitPR publie les Pull Requests et les issues via une abstraction unique, le `ScmProvider`, qui prend en charge quatre forges d'hébergement Git : GitHub, GitLab, Bitbucket Cloud et Azure DevOps. Chaque flux de publication — l'éditeur interactif de PR (mode par défaut), la publication directe (`--no-edit`) et la TUI des issues (`-is`) — résout le provider **du dépôt dans lequel il s'exécute** et appelle l'API du forge via celui-ci.

Le forge appartient au dépôt, pas à la machine : GitPR le détecte à partir du remote `origin` (ou lit un override explicite versionné avec le projet) et conserve **un token chiffré par forge** dans `~/.gitpr/.env`. Une machine peut donc travailler sur un dépôt GitLab et un dépôt GitHub en même temps, chacun avec son propre identifiant.

Sans configuration SCM, GitPR conserve le comportement hérité exclusif à GitHub — zéro migration et sortie byte-identique.

---

## 1. Forges Prises en Charge

| Forge | Clé du provider | Base d'API par défaut | Authentification |
| --- | --- | --- | --- |
| GitHub | `github` | `https://api.github.com` | Personal Access Token (PAT) |
| GitLab | `gitlab` | `https://gitlab.com/api/v4` | Personal Access Token (PAT) |
| Bitbucket Cloud | `bitbucket` | `https://api.bitbucket.org/2.0` | Nom d'utilisateur + App Password (HTTP Basic) |
| Azure DevOps | `azure_devops` | `https://dev.azure.com` | Personal Access Token (PAT) |

### 1.1 Quel Forge un Dépôt Utilise

Le forge est résolu par dépôt, dans cet ordre :

1. **Override du projet** — `scm.provider` dans `.gitpr/conf/gitpr.config.yml`, versionné avec le dépôt. Il gagne toujours, et c'est ainsi que l'on corrige un hôte self-managed dont le domaine ne nomme pas le forge.
2. **Détection du remote origin** — correspondance de sous-chaîne, insensible à la casse, sur l'URL du `origin`.
3. **`github`** — la valeur par défaut historique.

| L'URL du remote contient | Provider |
| --- | --- |
| `gitlab` | `gitlab` |
| `bitbucket` | `bitbucket` |
| `dev.azure.com` ou `visualstudio.com` | `azure_devops` |
| toute autre valeur (par défaut) | `github` |

```yaml
# .gitpr/conf/gitpr.config.yml — versionnez-le pour partager le forge avec l'équipe
scm:
  provider: gitlab
```

Une valeur inconnue dans le fichier de projet est ignorée avec un avertissement (un fichier malformé ne doit jamais faire tomber toutes les commandes), et la détection décide à sa place.

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
| 1. Détection du forge | Détecte le forge à partir du remote `origin` et demande confirmation (vous pouvez choisir un autre forge ; un hôte qui ne nomme aucun forge est demandé, jamais supposé) |
| 2. Extras du provider | Azure DevOps demande `organization` et `project` ; Bitbucket demande le `username`, qui fait partie de l'identifiant |
| 3. Base d'API | Base d'API personnalisée pour chaque forge sauf GitHub ; la valeur déjà enregistrée pour ce forge est proposée par défaut |
| 4. Token | Demande le PAT — ou l'App Password sur Bitbucket |
| 5. Validation | `test_connection()` — jusqu'à 3 tentatives ; HTTP 401 (token expiré) redemande en jaune, les autres échecs interrompent en rouge |
| 6. Persistance | Uniquement en cas de succès : écrit le token chiffré Fernet dans le slot de son forge (`GITLAB_TOKEN_ENCRYPTED`, …), la base d'API et les extras, et enregistre `scm.provider` dans le fichier de projet **uniquement quand le forge choisi diffère de celui détecté** |

Rien n'est écrit quand la validation échoue. Relancez `gitpr --init` dans chaque dépôt pour changer de forge ou renouveler un token expiré ; les tokens des autres forges restent intacts. Les valeurs des versions précédentes (`GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED`, `GITPR_SCM_BASE_URL`) sont migrées automatiquement dès la première commande après la mise à jour.

---

## 3. Configuration Manuelle (.env)

Alternative à l'assistant : modifiez `~/.gitpr/.env` directement. Consultez le [guide d'intégration du GitHub PAT](github-pat-integration.md) pour comprendre comment GitPR protège les tokens au repos.

| Variable | Forge | Description |
| --- | --- | --- |
| `GITPR_SCM_TOKEN` | tous | Token brut, réservé aux environnements CI/CD — unique et global, consulté avant tout token enregistré |
| `GITHUB_TOKEN_ENCRYPTED` | `github` | Token chiffré Fernet du forge GitHub |
| `GITLAB_TOKEN_ENCRYPTED` | `gitlab` | Token chiffré Fernet du forge GitLab |
| `BITBUCKET_TOKEN_ENCRYPTED` | `bitbucket` | Token chiffré Fernet du forge Bitbucket |
| `AZURE_DEVOPS_TOKEN_ENCRYPTED` | `azure_devops` | Token chiffré Fernet du forge Azure DevOps |
| `GITHUB_BASE_URL` / `GITLAB_BASE_URL` / `BITBUCKET_BASE_URL` / `AZURE_DEVOPS_BASE_URL` | forge propre | Base d'API personnalisée (self-managed/enterprise) ; vide = SaaS public |
| `GITPR_SCM_ORGANIZATION` | `azure_devops` | Nom de l'organisation — obligatoire (l'erreur fail-fast nomme la variable manquante) |
| `GITPR_SCM_PROJECT` | `azure_devops` | Nom du projet — obligatoire |
| `GITPR_SCM_USERNAME` | `bitbucket` | Nom d'utilisateur Bitbucket — obligatoire (App Password en HTTP Basic) |

Chaque forge ne lit que son propre slot : un token GitLab ne répond jamais pour un dépôt GitHub. GitHub sans configuration SCM conserve `GITHUB_TOKEN_ENCRYPTED` — zéro migration.

### 3.1 Note de Migration : Provisionnement Automatisé et Slots par Forge

> [!WARNING]
> **Note de Migration pour les Scripts d'Infrastructure et de Provisionnement :**  
> Les clés globales héritées `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` et `GITPR_SCM_BASE_URL` sont définitivement abandonnées. La migration automatique à l'exécution supprime ces lignes de `~/.gitpr/.env` dès la première utilisation.  
> 
> Les scripts de provisionnement automatisé de machines (Ansible, Docker, devcontainers, dotfiles ou démarrage de VMs) doivent désormais renseigner directement les slots dédiés par forge :
> - GitHub : `GITHUB_TOKEN_ENCRYPTED` (et optionnellement `GITHUB_BASE_URL`)
> - GitLab : `GITLAB_TOKEN_ENCRYPTED` (et optionnellement `GITLAB_BASE_URL`)
> - Bitbucket : `BITBUCKET_TOKEN_ENCRYPTED` (et `GITPR_SCM_USERNAME`)
> - Azure DevOps : `AZURE_DEVOPS_TOKEN_ENCRYPTED` (et `GITPR_SCM_ORGANIZATION` + `GITPR_SCM_PROJECT`)
> 
> Pour les serveurs auto-hébergés avec des domaines personnalisés, configurez la surcharge dans le fichier du projet `.gitpr/conf/gitpr.config.yml` (`scm.provider: <forge>`) au lieu de définir un fournisseur global dans `.env`. Les environnements CI éphémères doivent continuer d'utiliser le token brut unique `GITPR_SCM_TOKEN`. Détails architecturaux dans l'[ADR-0020](adr/0020-per-repo-scm-provisioning-migration.md) et l'[ADR-016](plans/ADR-016-per-provider-scm-settings.md).

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

Quand le token est rejeté (HTTP 401), GitPR supprime le token expiré du slot **de ce** forge et en demande un nouveau — jusqu'à 3 tentatives. Privilégiez les flux interactifs (`gitpr`, `gitpr -is`) pour vous réauthentifier : `--no-edit` publie directement et ne peut pas redemander.

Une exécution non interactive (hooks git, serveur MCP, CI) ne demande jamais et ne supprime jamais l'identifiant enregistré : elle s'arrête avec un message indiquant `gitpr --init` dans ce dépôt.

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

### 6.1 Contrat pour les Fournisseurs Tiers (changement incompatible depuis la v1.2.0)

`ScmProvider.request_pull_request_reviewers()` retournait `None`. Depuis la **v1.2.0**, il retourne `list[str]` : les logins que le forge a **réellement associés**, relus dans le corps de la réponse. Une liste vide signifie « accepté mais ignoré » : c'est ainsi que GitPR détecte un relecteur écarté en silence par le forge.

| | Jusqu'à la v1.1.x | Depuis la v1.2.0 |
| --- | --- | --- |
| Type de retour | `None` | `list[str]` (logins associés) |
| `[]` | — | Demande acceptée, personne d'associé |
| Valeur par défaut de la classe de base | `ScmNotSupportedError` | `ScmNotSupportedError` (inchangé) |

**Qui est concerné :** uniquement les sous-classes qui **redéfinissent** la méthode. Celui qui ne fait que l'appeler n'est pas concerné. Une sous-classe qui ne la redéfinit pas continue de lever `ScmNotSupportedError`, comme avant.

**Comment migrer :** retournez ce que le forge a associé. Si le forge ne renvoie pas de corps, retournez la liste qu'on vous a demandé d'associer : c'est optimiste et cela désactive l'avertissement « non associé » pour ce forge.

```python
class MyForgeProvider(ScmProvider):
    def request_pull_request_reviewers(self, repo, pr_id, reviewers) -> list[str]:
        body = self._post_reviewers(repo, pr_id, reviewers)
        return [r["login"] for r in body.get("requested_reviewers", [])]
        # Le forge ne renvoie pas de corps ? Utilisez `return list(reviewers)`.
```

Une redéfinition héritée qui retourne encore `None` continue de fonctionner : l'appelant la lit comme « vérification impossible » et saute l'avertissement « non associé ». Elle est tolérée, pas recommandée. Enregistrement de la décision : [ADR-0009](adr/0009-reviewer-attach-returns-read-back.md).

Registre de décision d'architecture et vocabulaire canonique : [ADR-001 Abstraction SCM](plans/ADR-001-scm-abstraction.md) et [Glossaire SCM Multi-Forge](plans/glossary-scm-multiforge.md).

> **Note :** Consultez aussi la [documentation d'intégration du GitHub PAT](github-pat-integration.md) pour créer des tokens et comprendre le chiffrement de GitPR (Fernet).
