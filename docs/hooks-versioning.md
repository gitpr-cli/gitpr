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
| `SCRIPTS_LANG` | `~/.gitpr/.env` | **The language you asked for.** Empty follows the interface language. Edited on the `gitpr config` screen |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | **What is on disk.** Written by the installer, never by the user, and shown read-only on the configuration screen |

The two language markers are deliberately separate. The auto-sync has to notice a language change, and that requires comparing what is installed against what is wanted — two independent values. A single `SCRIPTS_LANG` written by the installer would be compared against itself, which can never differ, so switching languages would silently keep the hooks in the old one.

### 2.2 Auto-Sync Flow

```
gitpr execution
    │
    ├─ Read SCRIPTS_VERSION and SCRIPTS_INSTALLED_LANG from ~/.gitpr/.env
    │
    ├─ Compute the wanted language: SCRIPTS_LANG (the choice, from the file)
    │  or the live interface language when it is empty
    │
    ├─ Match? → Skip (fast path — single .env read, no network)
    │
    └─ Mismatch or missing? → Download & install hooks in the wanted language
                                 → Stamp SCRIPTS_VERSION + SCRIPTS_INSTALLED_LANG
```

The fast path (when versions match) is a single `.env` file read with zero network I/O.

The wanted language is read from the file rather than `os.getenv()`, and the interface language is read from `src.i18n` at call time rather than from this module's frozen copy of it — `set_lang()`, which is what `--lang` calls, rebinds the constant instead of mutating it. Without both, `gitpr --lang fr_fr` would install the hooks in whatever language the process started in.

### 2.3 Supported Languages

The interface spells a language one way and the published file spells it another, and the two are not interchangeable: `GITPR_LANG` and `SCRIPTS_LANG` hold `es_es`/`fr_fr` while the files on the server are named `.es`/`.fr`. `HOOK_SCRIPT_SUFFIXES` in `src/core.py` is that map, and nothing else may assume the two sides agree.

| Language | Interface / `SCRIPTS_LANG` code | Script suffix | Example |
|----------|--------------------------------|---------------|---------|
| English (default) | `en_us` | *(no suffix)* | `pre-commit-template.sh` |
| Portuguese (Brazil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Portuguese (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Spanish | `es_es` | `.es` | `pre-commit-template.es.sh` |
| French | `fr_fr` | `.fr` | `pre-commit-template.fr.sh` |

A code outside the map installs the base script, which is English. English is also the fallback when a language-specific script is missing on the server (HTTP 404).

---

## 3. How It Works

### 3.1 First Run (No Hooks Installed)

When a user runs `gitpr --installhooks` or `gitpr --install` for the first time:

1. GitPR resolves the effective language: `SCRIPTS_LANG` when you chose one, the live interface language otherwise
2. Downloads language-specific scripts first (e.g., `pre-commit-template.pt_br.sh`)
3. Falls back to English if the language variant is unavailable (HTTP 404)
4. Applies execution permissions (`chmod +x`)
5. Stamps `SCRIPTS_VERSION` and `SCRIPTS_INSTALLED_LANG` in `~/.gitpr/.env`. `SCRIPTS_LANG` is **not** written — it is your choice, and an installer that overwrote it would erase the request it is supposed to satisfy

### 3.2 Subsequent Runs (Auto-Sync)

On every `gitpr` execution:

1. `check_and_update_hooks_scripts()` reads `SCRIPTS_VERSION` and `SCRIPTS_INSTALLED_LANG` from `.env`
2. Compares against `__scripts_version__` (from code) and the effective language
3. If both match → nothing happens (fast path)
4. If version differs → hooks are re-downloaded in the effective language
5. If language differs → hooks are re-downloaded to match the new language, once; the next run is a fast path again
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
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | Language of the scripts on disk (auto-managed) |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Language you want for the hooks. Empty follows `GITPR_LANG`. Edited on the `gitpr config` screen, under **Advanced → Git Hooks** |
| `GITPR_LANG` | `~/.gitpr/.env` | User's preferred interface language |

### 5.2 Source Constants

| Constant | File | Description |
|----------|------|-------------|
| `__scripts_version__` | `src/updater.py` | Current hook scripts version |
| `HOOK_SCRIPT_SUFFIXES` | `src/core.py` | Interface language code → published script suffix |
| `effective_hook_lang()` | `src/core.py` | `SCRIPTS_LANG` when set, the live interface language otherwise |
| `SCRIPTS_BASE_URL` | `src/core.py` | Base URL for downloading scripts |

### 5.3 Adding a New Language

To add support for a new language:

1. Create 5 translated `.sh` files in the `scripts/` directory (one per hook type)
2. Add the mapping to `HOOK_SCRIPT_SUFFIXES` in `src/core.py` — the key is the interface code (`es_es`), the value is the file suffix (`.es`)
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
- Check `SCRIPTS_LANG` in `~/.gitpr/.env`, or the **Hooks Language** field under **Advanced → Git Hooks** on the `gitpr config` screen. Empty follows `GITPR_LANG`
- Compare with `SCRIPTS_INSTALLED_LANG`, which records what is actually on disk — the two differing is the signal that a reinstall is pending
- Run `gitpr --installhooks` to reinstall immediately, or just run any `gitpr` command: the auto-sync reinstalls once and then goes back to the fast path

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
    SCRIPTS_INSTALLED_LANG in ~/.gitpr/.env against the shipped version
    and the wanted language. When they match the check is a single
    .env read with no network I/O.

    The language comparison is between what is ON DISK and what is
    WANTED, two independent sources: switching SCRIPTS_LANG on the
    configuration screen reinstalls once, and the next run goes back to
    the fast path.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the wanted language.
    On success the markers are stamped so future runs skip the network.
    """
```

### `install_git_hooks()`

```python
# src/core.py
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Installs the hooks in the effective language — SCRIPTS_LANG when the
    user chose one, the interface language otherwise — trying the
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh)
    and falling back to the English base version when a translation is
    unavailable.

    After a successful install, stamps SCRIPTS_VERSION and
    SCRIPTS_INSTALLED_LANG in ~/.gitpr/.env so the auto-sync check can
    skip network calls. SCRIPTS_LANG is NOT written here: it is the
    user's choice, and comparing a choice against itself could never
    detect a language change.
    """
```

### `effective_hook_lang()`

```python
# src/core.py
def effective_hook_lang():
    """The language the hooks should be installed in.

    SCRIPTS_LANG is the user's choice, set on the configuration screen;
    empty means "follow the interface language". It is read from the FILE
    rather than os.getenv() because load_dotenv(override=False) lets a
    variable exported in the shell beat the value the user just edited.
    """
```

---

## 8. Design Decisions

- **Independent version marker:** `__scripts_version__` is separate from `__lang_version__` because hook scripts change on a different cadence than language resources
- **Two language markers, not one:** `SCRIPTS_LANG` is the request and `SCRIPTS_INSTALLED_LANG` is what the installer left on disk. The auto-sync compares them, so switching languages reinstalls once and then stabilises. A single marker — written by the installer and compared against itself — silently kept users on the language they started with, however many times they changed the setting
- **The installer never writes the request:** it would overwrite the very value it is meant to satisfy, and the comparison would become a tautology
- **The interface language is read live:** `core.py` holds a copy of `i18n.CURRENT_LANG` from import time, and `set_lang()` (what `--lang` calls) rebinds the original. "Follow the interface language" reads it at call time, so `gitpr --lang fr_fr` installs French hooks
- **Whitelist approach:** Only the 4 mapped codes (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) trigger language-specific downloads; any other language falls through to English (no 404 cascade). The map is explicit because the interface code and the file suffix disagree — `es_es` is published as `.es`
- **Global marker (not per-project):** The `SCRIPTS_VERSION` marker lives in `~/.gitpr/.env` (global). After a version bump, the first project that runs `gitpr` gets updated and stamps the marker; other projects' hooks are updated on their next `gitpr` execution. Since hooks are thin shims, stale hooks still work — the real logic lives in the CLI
- **Guarded sync:** Auto-sync is skipped during `--quiet`, `--hook`, and `--mcp` invocations to avoid network latency in automated contexts
