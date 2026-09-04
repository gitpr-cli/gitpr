# Technical Documentation: Auto-Updater (--update)

GitPR has an automatic update system (**Auto-Updater**) that keeps the tool always on the latest version, with daily verification and *hot-swap* updates.

---

## 1. Manual Update

```bash
gitpr -u
# or
gitpr --update
```

The command forces immediate verification and installation of the latest version.

---

## 2. Automatic Daily Verification

On every GitPR execution (except `--quiet` and `--hook` modes), the tool silently checks if a new version is available. The result is cached for **24 hours** in the `~/.gitpr/update_cache.json` file to avoid repeated API calls.

If a new version is available, a notification is displayed at the end of the execution.

---

## 3. Update Methods

The Auto-Updater automatically detects the installation method:

### 3.1 pip Installation

```bash
pip install --upgrade gitpr-cli
```

### 3.2 Binary Installation (PyInstaller)

GitPR uses the **Hot-Swap** technique for standalone binaries:

1. Checks the latest version on [GitHub Releases](https://github.com/gitpr-cli/gitpr.git/releases)
2. Downloads the new executable
3. Renames the current `.exe` to `.exe.old`
4. Moves the new binary into place
5. In case of failure, reverts to `.exe.old` (automatic rollback)
6. On the next execution, removes `.old` automatically (cleanup)

---

## 4. Connection Guardian

Before any network operation, GitPR checks connectivity via socket `8.8.8.8:53`. If there is no internet, the tool operates normally in offline mode — without freezing or showing connection errors.

---

## 5. Version Sources

| Source | Usage |
| --- | --- |
| **PyPI** | Version for pip installations (`pip install gitpr-cli`) |
| **GitHub Releases** | Version for standalone binaries (`.exe`) |

The local version is defined in `src/updater.py` (`__version__`) and incremented with each release.

> **Note:** See also the [main documentation (README.md)](../README.md) for installation and initial setup information.
