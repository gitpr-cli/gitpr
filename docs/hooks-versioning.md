# Hook Scripts Versioning and Auto-Sync

This documentation details the architecture and operation of GitPR's automatic versioning and synchronization system for Git hook scripts. The system ensures that hook scripts installed in your repositories are always up to date with the latest version, respecting your language preferences.

---

## 1. Overview

GitPR includes an automatic versioning system for Git hook scripts (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Every time you run `gitpr`, the system silently checks whether the installed hooks match the latest version available. If a new version is detected — or if the language has changed — the hooks are automatically re-downloaded and updated.

This mechanism is independent of the main GitPR auto-updater (`--update`) and operates on a separate version cadence, since hook scripts evolve at a different pace than the CLI itself.

---

## 2. Architecture

### 2.1 Version Markers

| Marker | Location | Purpose |
|--------|----------|---------|
| `__scripts_version__` | `src/updater.py` | Single source of truth — defines the current version of hook scripts shipped with this GitPR release |
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Tracks which version is currently installed on the user's machine |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Tracks the language of the installed scripts (e.g., `pt_br`, `fr`) |

### 2.2 Auto-Sync Flow

```
gitpr execution
    │
    ├─ Read SCRIPTS_VERSION and SCRIPTS_LANG from ~/.gitpr/.env
    │
    ├─ Compare with __scripts_version__ and CURRENT_LANG
    │
    ├─ Match? → Skip (fast path — single .env read, no network)
    │
    └─ Mismatch or missing? → Download & install hooks in current language
                                 → Stamp SCRIPTS_VERSION + SCRIPTS_LANG
```

The fast path (when versions match) is a single `.env` file read with zero network I/O.

### 2.3 Supported Languages

| Language | Code | Script Suffix | Example |
|----------|------|---------------|---------|
| English (default) | `en` | *(no suffix)* | `pre-commit-template.sh` |
| Portuguese (Brazil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Portuguese (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| French | `fr` | `.fr` | `pre-commit-template.fr.sh` |
| Spanish | `es` | `.es` | `pre-commit-template.es.sh` |

English is the default and fallback language. If a language-specific script is not found on the server (HTTP 404), the system automatically falls back to the English version.

---

## 3. How It Works

### 3.1 First Run (No Hooks Installed)

When a user runs `gitpr --installhooks` or `gitpr --install` for the first time:

1. GitPR detects the current language (`CURRENT_LANG`) from the OS or `.env`
2. Downloads language-specific scripts first (e.g., `pre-commit-template.pt_br.sh`)
3. Falls back to English if the language variant is unavailable (HTTP 404)
4. Applies execution permissions (`chmod +x`)
5. Stamps `SCRIPTS_VERSION` and `SCRIPTS_LANG` in `~/.gitpr/.env`

### 3.2 Subsequent Runs (Auto-Sync)

On every `gitpr` execution:

1. `check_and_update_hooks_scripts()` reads `SCRIPTS_VERSION` and `SCRIPTS_LANG` from `.env`
2. Compares against `__scripts_version__` (from code) and `CURRENT_LANG`
3. If both match → nothing happens (fast path)
4. If version differs → hooks are re-downloaded in the current language
5. If language differs → hooks are re-downloaded to match the new language
6. On success → markers are updated so future runs skip the network

**Guarded invocations:** The auto-sync is skipped during internal CLI calls (`--quiet`, `--hook`, `--mcp`) to avoid network latency in automated contexts.

### 3.3 Stamp-Only-on-Full-Success

The `SCRIPTS_VERSION` marker is only written when **all 5 hooks** are successfully downloaded and installed. If any hook fails (network error, partial download), the marker is not updated, ensuring the failed installation is retried on the next `gitpr` execution.

---

## 4. Hook Script Types

The system manages 5 types of Git hooks:

| Hook | Script Template | Purpose |
|------|----------------|---------|
| `pre-commit` | `pre-commit-template.sh` | Runs the static linter before each commit |
| `prepare-commit-msg` | `prepare-commit-msg-template.sh` | Generates AI-powered commit messages |
| `pre-push` | `pre-push-template.sh` | Validates code before pushing to remote |
| `post-checkout` | `post-checkout-template.sh` | Actions after branch switching |
| `post-merge` | `post-merge-template.sh` | Actions after a successful merge |

All hook scripts are **thin shims** — they call the `gitpr` CLI internally. The real logic lives in the CLI code, not in the hook files. This means that even if hooks are slightly stale, they continue working correctly because they always invoke the latest installed CLI.

---

## 5. Configuration

### 5.1 Environment Variables

| Variable | File | Description |
|----------|------|-------------|
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Installed hook scripts version (auto-managed) |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Language of installed scripts (auto-managed) |
| `GITPR_LANG` | `~/.gitpr/.env` | User's preferred interface language |

### 5.2 Source Constants

| Constant | File | Description |
|----------|------|-------------|
| `__scripts_version__` | `src/updater.py` | Current hook scripts version |
| `_SCRIPT_LANG_SUFFIXES` | `src/core.py` | Set of supported language suffixes |
| `SCRIPTS_BASE_URL` | `src/core.py` | Base URL for downloading scripts |

### 5.3 Adding a New Language

To add support for a new language:

1. Create 5 translated `.sh` files in the `scripts/` directory (one per hook type)
2. Add the language code to `_SCRIPT_LANG_SUFFIXES` in `src/core.py`
3. The auto-sync system will automatically detect and serve the new language

### 5.4 Bumping the Scripts Version

When hook scripts are modified:

1. Increment `__scripts_version__` in `src/updater.py`
2. On the next `gitpr` execution, all installed clients will detect the mismatch and auto-update their hooks

---

## 6. Troubleshooting

### Hooks are not updating

**Symptom:** Running `gitpr` does not update installed hooks even though a new version exists.

**Solution:**
- Verify that the `.git/hooks` directory exists in your project
- Check `SCRIPTS_VERSION` in `~/.gitpr/.env` — if it matches `__scripts_version__`, no update is needed
- Manually delete `SCRIPTS_VERSION` from `.env` to force a re-download on the next run
- Run `gitpr --installhooks` to force a fresh installation

### Wrong language in hooks

**Symptom:** Hook scripts display messages in the wrong language.

**Solution:**
- Check `GITPR_LANG` in `~/.gitpr/.env`
- Delete `SCRIPTS_LANG` from `.env` to force language re-detection
- Run `gitpr --installhooks` to reinstall in the correct language

### Partial installation

**Symptom:** Some hooks are installed but `SCRIPTS_VERSION` is not stamped.

**Solution:**
- This is by design — the marker is only written when all 5 hooks succeed
- Check your network connection
- Run `gitpr --installhooks` again to retry the failed downloads

---

## 7. API Reference

### `check_and_update_hooks_scripts()`

```python
# src/core.py
def check_and_update_hooks_scripts():
    """Silent auto-sync of installed Git hooks (version + language gated).

    Called on every gitpr execution. Compares SCRIPTS_VERSION and
    SCRIPTS_LANG in ~/.gitpr/.env against the shipped constants. When
    they match the check is a single .env read with no network I/O.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the current language.
    On success the markers are stamped so future runs skip the network.
    """
```

### `install_git_hooks()`

```python
# src/core.py
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Detects the current language (CURRENT_LANG) and tries to download
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh).
    Falls back to the English base version when a translation is unavailable.

    After a successful install, stamps SCRIPTS_VERSION and SCRIPTS_LANG
    in ~/.gitpr/.env so the auto-sync check can skip network calls.

    Returns True when all 5 hooks installed successfully.
    """
```

---

## 8. Design Decisions

- **Independent version marker:** `__scripts_version__` is separate from `__lang_version__` because hook scripts change on a different cadence than language resources
- **`SCRIPTS_LANG` companion marker:** Prevents language flip-flop when users run `gitpr --lang fr` once — the auto-sync won't re-download unless version OR language differs
- **Whitelist approach:** Only 4 explicit suffixes (`pt_br`, `pt_pt`, `fr`, `es`) trigger language-specific downloads; any other language falls through to English (no 404 cascade)
- **Global marker (not per-project):** The `SCRIPTS_VERSION` marker lives in `~/.gitpr/.env` (global). After a version bump, the first project that runs `gitpr` gets updated and stamps the marker; other projects' hooks are updated on their next `gitpr` execution. Since hooks are thin shims, stale hooks still work — the real logic lives in the CLI
- **Guarded sync:** Auto-sync is skipped during `--quiet`, `--hook`, and `--mcp` invocations to avoid network latency in automated contexts
