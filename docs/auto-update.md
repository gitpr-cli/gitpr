# Technical Documentation: Auto-Updater (--update)

GitPR is distributed exclusively through PyPI. The **Auto-Updater** checks daily whether a new version has been published and keeps the tool always on the latest release.

---

## 1. Manual Check

```bash
gitpr -u
# or
gitpr --update
```

The command forces an immediate verification against PyPI and prints the upgrade command. It does **not** install anything — the update itself is always performed by your package manager.

---

## 2. Mandatory Update Block

On every GitPR execution (except `--quiet`, `--hook` and `--mcp` modes), the tool checks whether a newer version has been published. The result is cached for **24 hours** in the `~/.gitpr/update_cache.json` file to avoid repeated API calls.

When the published version is newer than the local one, GitPR **blocks the execution**: it prints both versions, shows the `pip install --upgrade gitpr-cli` command and exits with a non-zero status without doing any work.

There is no flag, fallback or compatibility mode that keeps an outdated version running — updating is the only way to continue.

### Exemptions

The block never fires for:

| Context | Reason |
| --- | --- |
| `--quiet` | Scripts and automation that discard the output |
| `--hook` | Git hooks (`prepare-commit-msg`, metrics) — must never break a commit |
| `--mcp` / `gitpr-mcp` | MCP server consumed by IDEs and agents |
| `-u` / `--update` | It is the very command that explains how to update |
| `-h --<flag>` | Contextual help |

`--help` and `--version` are also unaffected: Click resolves them before the command body runs.

### Offline Behaviour

When the published version cannot be determined — no internet and no cache for the current day — GitPR runs normally. An offline user must never be locked into a command they cannot run.

---

## 3. Applying the Update

```bash
pip install --upgrade gitpr-cli
```

Users of `pipx`, `uv` or `poetry` should update through their own tool instead (`pipx upgrade gitpr-cli`, `uv tool upgrade gitpr-cli`, …).

---

## 4. Connection Guardian

Before any network operation, GitPR checks connectivity via socket `8.8.8.8:53`. If there is no internet, the tool operates normally in offline mode — without freezing or showing connection errors.

---

## 5. Version Source

| Source | Usage |
| --- | --- |
| **PyPI** (`pypi.org/pypi/gitpr-cli/json`) | Single source of truth for the published version |

The local version is defined in `src/updater.py` (`__version__`) and incremented with each release.

> **Note:** See also the [main documentation (README.md)](../README.md) for installation and initial setup information.
