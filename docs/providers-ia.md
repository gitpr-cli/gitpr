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
| `gemini-2.5-flash` | Primary (advanced) — PRs, reviews, issues | `GEMINI_API_MODEL` |
| `gemini-2.5-flash-lite` | Secondary (simple) — blame classification | `SECONDARY_GEMINI_API_MODEL` |

### 3.2 DeepSeek

| Model | Usage | Environment Variable |
| --- | --- | --- |
| `deepseek-chat` | Primary and Secondary | `DEEPSEEK_API_MODEL` / `SECONDARY_DEEPSEEK_API_MODEL` |

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
| **Cache** | MD5 (identical responses do not consume quota) |

> **Note:** See also the [main documentation (README.md)](../README.md) for initial API key setup instructions.
