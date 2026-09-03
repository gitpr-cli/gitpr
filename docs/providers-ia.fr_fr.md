# Documentation technique : Fournisseurs d'IA (--provider)

GitPR est **agnostique en matière d'IA** et prend actuellement en charge deux fournisseurs : **Google Gemini** et **DeepSeek**. Vous pouvez basculer entre eux dynamiquement via la ligne de commande ou une configuration persistante.

---

## 1. Sélection via la ligne de commande

```bash
gitpr -p gemini         # Force Google Gemini pour cette exécution
gitpr -p deepseek       # Force DeepSeek pour cette exécution
gitpr -c -p gemini      # Message de commit avec Gemini
gitpr -r -p deepseek    # Code review avec DeepSeek
```

Le flag `--provider` (`-p`) écrase temporairement le provider par défaut configuré.

---

## 2. Configuration persistante

Définissez le provider par défaut dans le fichier `~/.gitpr/.env` :

```ini
DEFAULT_AI_PROVIDER=gemini
# ou
DEFAULT_AI_PROVIDER=deepseek
```

---

## 3. Modèles disponibles

### 3.1 Google Gemini

| Modèle | Utilisation | Variable d'environnement |
| --- | --- | --- |
| `gemini-pro-latest` | Primaire (avancé) — PRs, reviews, issues | `GEMINI_API_MODEL_PRIMARY` |
| `gemini-flash-lite-latest` | Secondaire (simple) — classification dans le blame | `GEMINI_API_MODEL_SECONDARY` |

### 3.2 DeepSeek

| Modèle | Utilisation | Variable d'environnement |
| --- | --- | --- |
| `deepseek-v4-pro` / `deepseek-v4-flash` | Primaire et secondaire | `DEEPSEEK_API_MODEL_PRIMARY` / `DEEPSEEK_API_MODEL_SECONDARY` |

---

## 4. Configuration des clés d'API

Les clés sont stockées de manière **chiffrée** (Fernet) dans le fichier `~/.gitpr/.env` :

```ini
GEMINI_API_KEY_ENCRYPTED=<hash_criptografado>
DEEPSEEK_API_KEY_ENCRYPTED=<hash_criptografado>
```

La clé maîtresse de déchiffrement est générée automatiquement dans `~/.gitpr/secret.key`.

---

## 5. Fallback automatique

Si le provider configuré échoue (erreur réseau, quota dépassé, etc.), GitPR essaie automatiquement l'**autre provider** disponible. Ce comportement garantit que le flux de travail n'est pas interrompu par l'indisponibilité temporaire d'un service.

---

## 6. Paramètres de génération

Les deux fournisseurs sont configurés pour une sortie déterministe :

| Paramètre | Valeur |
| --- | --- |
| **Température** | 0.0 |
| **Top P** | 0.1 |
| **Format de sortie** | JSON structuré |
| **Retry** | 3 tentatives, intervalle de 2s |
| **Timeout** | 180s par appel (configurable via `GITPR_AI_TIMEOUT` dans `~/.gitpr/.env`) |
| **Cache** | MD5 (les réponses identiques ne consomment pas de quota) |

Chaque appel de modèle est limité par un **délai d'attente (timeout) de
180 secondes** (configurable via `GITPR_AI_TIMEOUT` dans `~/.gitpr/.env`),
garantissant qu'un fournisseur bloqué échoue rapidement avec une erreur visible,
au lieu de figer la CLI. Les valeurs invalides ou non positives reviennent à la
valeur par défaut de 180s.

> **Note :** Consultez également la [documentation principale (README.md)](../README.md) pour les instructions de configuration initiale des clés d'API.
