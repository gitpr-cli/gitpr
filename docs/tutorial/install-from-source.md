# Installing GitPR from Source (and Unblocking the Version Gate)

This guide is for anyone who runs GitPR from a **local checkout** instead of the
package published on PyPI, and who hits the mandatory update block while doing
so.

> If your goal is only to test a change before publishing a new PyPI version,
> the shorter recipe in [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md)
> (Portuguese) may be enough. This guide goes further: it explains **why** the
> update block still fires on a source install and what to do about it.

---

## 1. The symptom

You installed GitPR from the repository, with the editable flag:

```bash
pip install -e .
```

And yet, every time you run it, GitPR refuses to work:

```text
⚠️ A new version of GitPR is available: 1.1.0 -> 1.2.0
GitPR must be updated before it can run: pip install --upgrade gitpr-cli
```

The process exits with a non-zero status and does no work at all. Running
`pip install --upgrade gitpr-cli` is the obvious move, but it is exactly what
you do **not** want: it replaces your checkout with the published package.

---

## 2. Installing from source (editable mode)

The command is `pip install -e .` — the `-e` stands for *editable* and the dot
is the current directory.

```bash
git clone https://github.com/gitpr-cli/gitpr.git
cd gitpr
pip install -e .
```

> Mind the **space and the dot** at the end of `-e .`. The dot means "install
> the package from this directory"; without it, pip looks for a package named
> literally on PyPI and fails.

Verify that the entry point was created:

```bash
gitpr --version
```

In editable mode Python does not copy the files — it links the installed
distribution straight to your working directory. Saving a file in the editor is
enough for the change to take effect on the next `gitpr` run, with no
reinstall.

---

## 3. Why the update block still fires

This is the part that surprises people: **it is not a broken install**. It is
the update gate working as designed, on a checkout that is behind the published
release.

The gate lives in `enforce_update_required()` ([src/updater.py](../../src/updater.py))
and compares two versions:

| Version | Where it comes from |
| --- | --- |
| Remote | `https://pypi.org/pypi/gitpr-cli/json`, cached for 24h in `~/.gitpr/update_cache.json` |
| Local | `__version__` at the top of `src/updater.py` |

The run is blocked when the remote version is **greater** than the local one.
The catch is the *local* side: in an editable install, `src/updater.py` is read
from **your working tree**, not from a copy frozen at install time. Whatever
`__version__` says in the checkout you have open is the version GitPR reports —
and therefore the version the gate compares.

So the failure scenario looks like this:

| | Value |
| --- | --- |
| Published on PyPI | `1.2.0` |
| `__version__` in your checkout | `1.1.0` |
| Result | blocked on every command |

A second, subtler symptom of the same mechanism: `git stash`, `git checkout`, or
`git switch` to a branch that predates the last release cut re-blocks GitPR
immediately, because the file on disk changed even though nothing was reinstalled.

---

## 4. Unblocking — option A (recommended): stay aligned with the release

The straightforward fix is to make the tree you are working on report a version
that is **greater than or equal to** what PyPI publishes. In practice:

```bash
git switch main
git pull
pip install -e .
gitpr -u
```

`gitpr -u` (`--update`) is never blocked, so it is the safest way to confirm the
situation before running anything heavier. It prints the comparison and the
upgrade command, and installs nothing.

Also re-run `pip install -e .` after a `git pull` or a branch switch that adds or
renames modules. The editable link covers the source tree, but a newly added
entry point or dependency in `pyproject.toml` only reaches the installed
distribution on a fresh `pip install -e .`.

> **Do not hand-edit `__version__` to fake a version.** Bumping the string
> without cutting a release corrupts what `gitpr -u` reports and hides a real
> upgrade need. The version marker is set by the release process, not by the
> developer's convenience.

---

## 5. Unblocking — option B: `GITPR_SKIP_UPDATE_CHECK` (local use)

GitPR reads an environment switch that mutes the check entirely. Add one line to
the global config file `~/.gitpr/.env`:

```bash
# ~/.gitpr/.env
GITPR_SKIP_UPDATE_CHECK=1
```

Save the file and run GitPR again — the block is gone.

**Use this for local and offline development only.** It is not a substitute for
updating a released installation: while the switch is on, a genuinely outdated
GitPR runs silently, with no warning and no protection against behaviour that
was already fixed upstream.

Four details worth knowing before you rely on it:

- **Any non-empty value disables the check** — including `0`, `false` and `no`.
  The switch is read as a plain flag (`bool(os.environ.get(..., "").strip())`),
  not parsed as a boolean. Only an empty or whitespace-only value leaves the
  check enabled. Setting `GITPR_SKIP_UPDATE_CHECK=` therefore does **nothing**.
- **It is not a `DEFAULT_CONFIG` key.** It does not appear in the configuration
  TUI and is not created by the setup wizard — you have to add the line to
  `~/.gitpr/.env` by hand.
- **It takes effect through the dotenv load.** `~/.gitpr/.env` is loaded at
  import time, before the gate runs, which is why writing it to the file works
  exactly like exporting it in the shell. Exporting it for a single command also
  works:

  ```bash
  GITPR_SKIP_UPDATE_CHECK=1 gitpr -c
  ```

- **To turn the check back on**, delete the line from `~/.gitpr/.env` (or
  overwrite it with an empty value) and restart GitPR.

---

## 6. What never blocks

Not every invocation goes through the gate. The check is skipped for:

| Context | Reason |
| --- | --- |
| `--quiet` | Scripts and automation that discard the output |
| `--hook` | Git hooks — must never break a commit |
| `--mcp` / `gitpr-mcp` | MCP server consumed by IDEs and agents |
| `-u` / `--update` | It is the very command that explains how to update |
| `-h --<flag>` | Contextual help |
| `--help` / `--version` | Click resolves both before the command body runs |
| **Any subcommand** | `gitpr fix`, `gitpr review-pr`, `gitpr release`, `gitpr init` dispatch before the gate |
| Offline | When the remote version is unknown, the run proceeds — an offline user must never be locked out of a command they cannot fix |

In a blocked checkout, `gitpr -u` and the subcommands are therefore still usable
for diagnosis, even without the environment switch.

---

## 7. Verifying the installation

Confirm which mode is active:

```bash
pip list --editable
```

`gitpr-cli` should be listed. On an older pip, look for a `gitpr_cli.egg-info/`
directory at the root of the repository — its presence is the signature of an
editable install.

> Seeing `WARNING: Ignoring invalid distribution ~itpr-cli`? Those are
> `~itpr_cli-*.dist-info` directories left in `site-packages` by an interrupted
> `pip` operation — pip renames a distribution to `~<name>` before deleting it,
> and an aborted run leaves the rename behind. They are inert leftovers that pip
> ignores; remove them by hand if the warning bothers you.

Then confirm the reported version:

```bash
gitpr -u
```

Compare the local version printed there with the `__version__` line in
`src/updater.py` of the checkout you have open. If they differ, the install is
pointing somewhere other than the tree you think you are editing.

---

## 8. Returning to the PyPI installation

When you are done developing locally:

```bash
pip uninstall gitpr-cli
pip install --upgrade gitpr-cli
```

Then clean up what the editable mode left behind:

- remove the `GITPR_SKIP_UPDATE_CHECK` line from `~/.gitpr/.env`;
- delete the `gitpr_cli.egg-info/` directory at the root of the repository (it is
  disposable build metadata);
- confirm with `pip list --editable`, which should no longer list `gitpr-cli`.

---

## See also

- [auto-update.md](../auto-update.md) — the auto-updater and the mandatory update block
- [testar_sem_usar_pypi.md](../testar_sem_usar_pypi.md) — testing without spending a PyPI version (Portuguese)
- [ARCHITECTURE.md](../ARCHITECTURE.md) — module map and command flow
