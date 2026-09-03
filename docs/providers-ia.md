# Technical Documentation: AI Providers (--provider)

GitPR is **AI-agnostic** and currently supports two providers: **Google Gemini** and **DeepSeek**. You can switch between them dynamically via command line or persistent configuration.

---

## 1. Command Line Selection

```bash
gitpr -p gemini         # Force Google Gemini for this execution
gitpr -p deepseek       # Force DeepSeek for this execution
gitpr -c -p gemini      # Commit message with Gemini
gitpr -r -p deepseek    # Code review with DeepSeek
```

The `--provider` (`-p`) flag temporarily overrides the configured default provider.

---

## 2. Persistent Configuration

Set the default provider in the `~/.gitpr/.env` file:

```ini
DEFAULT_AI_PROVIDER=gemini
# or
DEFAULT_AI_PROVIDER=deepseek
```

---

## 3. Available Models

### 3.1 Google Gemini

| Model | Usage | Environment Variable |
| --- | --- | --- |
| `gemini-pro-latest` | Primary (advanced) — PRs, reviews, issues | `GEMINI_API_MODEL_PRIMARY` |
| `gemini-flash-lite-latest` | Secondary (simple) — blame classification | `GEMINI_API_MODEL_SECONDARY` |

### 3.2 DeepSeek

| Model | Usage | Environment Variable |
| --- | --- | --- |
| `deepseek-v4-pro` / `deepseek-v4-flash` | Primary and Secondary | `DEEPSEEK_API_MODEL_PRIMARY` / `DEEPSEEK_API_MODEL_SECONDARY` |

---

## 4. API Key Configuration

Keys are stored in **encrypted** form (Fernet) in the `~/.gitpr/.env` file:

```ini
GEMINI_API_KEY_ENCRYPTED=<encrypted_hash>
DEEPSEEK_API_KEY_ENCRYPTED=<encrypted_hash>
```

The master decryption key is automatically generated at `~/.gitpr/secret.key`.

---

## 5. Automatic Fallback

If the configured provider fails (network error, quota exceeded, etc.), GitPR automatically tries the **other available provider**. This behavior ensures that the workflow is not interrupted by temporary service unavailability.

---

## 6. Generation Parameters

Both providers are configured for deterministic output:

| Parameter | Value |
| --- | --- |
| **Temperature** | 0.0 |
| **Top P** | 0.1 |
| **Output format** | Structured JSON |
| **Retry** | 3 attempts, 2s interval |
| **Timeout** | 180s per call (configurable via `GITPR_AI_TIMEOUT` in `~/.gitpr/.env`) |
| **Cache** | MD5 (identical responses do not consume quota) |

Each model call is bounded by a **180-second timeout** (configurable via
`GITPR_AI_TIMEOUT` in `~/.gitpr/.env`), so a hung provider fails fast with a
visible error instead of freezing the CLI. Invalid or non-positive values fall
back to the 180s default.

> **Note:** See also the [main documentation (README.md)](../README.md) for initial API key setup instructions.
