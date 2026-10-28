# Technical Documentation: Auto-Updater (--update)

GitPR is distributed exclusively through PyPI. The **Auto-Updater** checks on every run whether a new version has been published, keeping the answer for at most one hour, and keeps the tool always on the latest release.

---

## 1. Manual Check

```bash
gitpr -u
# or
gitpr --update
```

The command forces an immediate verification against PyPI — it ignores the update cache — and prints the upgrade command. It does **not** install anything — the update itself is always performed by your package manager.

---

## 2. Mandatory Update Block

On every GitPR execution (except `--quiet`, `--hook` and `--mcp` modes), and before interactive subcommands, the tool checks whether a newer version has been published. The result is cached for **1 hour** — a rolling window, not the local calendar day — in the `~/.gitpr/update_cache.json` file to avoid repeated API calls. `gitpr -u`/`--update` always ignores the cache.

When the published version is newer than the local one, GitPR **blocks the execution**: it prints both versions, shows the `pip install --upgrade gitpr-cli` command and exits with a non-zero status without doing any work.

Versions are compared according to PEP 440: a remote pre-release is ignored while the installed version is stable (pip does not install it without `--pre`), and an unparseable remote version counts as unknown.

There is no flag, fallback or compatibility mode that keeps an outdated **installed release** running — updating is the only way to continue. A checkout used for local development has a single escape switch, documented in [Installing GitPR from Source](tutorial/install-from-source.md).

### Exemptions

The block never fires for:

| Context | Reason |
| --- | --- |
| `--quiet` | Scripts and automation that discard the output |
| `--hook` | Git hooks (`prepare-commit-msg`, metrics) — must never break a commit |
| `--mcp` / `gitpr-mcp` | MCP server consumed by IDEs and agents |
| `-u` / `--update` | It is the very command that explains how to update |
| `-h --<flag>` | Contextual help |
| `gitpr <subcommand>` without a terminal | CI, pipes and cron must never be blocked — the subcommand gate only fires when the run can ask the user |
| `gitpr <subcommand> -h` / `--help` | Reading help must never be gated |

`--help` and `--version` are also unaffected: Click resolves them before the command body runs. Subcommand help is exempt through the raw command line. Invocations through the flag surface (`gitpr --status`, `gitpr -c`, …) keep the original behaviour and are blocked regardless of a terminal.

### Offline Behaviour

When the published version cannot be determined — no internet and no cache younger than one hour, or an answer that is not a valid version — GitPR runs normally. An offline user must never be locked into a command they cannot run.

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
