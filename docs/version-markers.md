# Version Markers (OTA Resources)

GitPR ships several resources **outside** the released binary — translations, spinner
words, smart-exclude lists, linter presets and Git hook scripts. They live on GitHub
and are fetched over the air (OTA) so they can be corrected without cutting a release.

A **Version Marker** is the mechanism that decides *when* a cached copy is stale.

---

## 1. How the pattern works

Each marker is a plain key in the user's global `~/.gitpr/.env`. It records **which
version of the code last downloaded that resource**:

```dotenv
LANG_VERSION=v0.0.20
SMART_EXCLUDES_VERSION=v0.0.20
THINKING_WORDS_VERSION=v0.0.20
LINTER_PRESETS_VERSION=v0.0.20
SCRIPTS_VERSION=v0.0.3
```

At runtime the resource loader compares the marker against the authoritative constant
in [`src/updater.py`](../src/updater.py):

```python
needs_update = os.getenv("LINTER_PRESETS_VERSION") != __lang_version__
```

* **Equal** → the local copy is current; use it, no network call.
* **Different or absent** → download the remote template, overwrite the local copy,
  then write the marker back with `set_key(...)`.

Because the marker is only written **after** a successful download, a failed fetch
leaves it stale and the next run retries. Every loader also keeps an offline
fallback chain, so a download failure degrades to the previous copy rather than
breaking the command.

> Markers are **not** seeded into `DEFAULT_CONFIG` in `src/config.py`. They are
> written on demand by the loader that owns them. An absent marker simply means
> "never downloaded", which correctly triggers the first fetch.

---

## 2. The markers

| Marker | Resource | Local cache | Compared against | Owner |
| --- | --- | --- | --- | --- |
| `LANG_VERSION` | Translation dictionaries | `~/.gitpr/langs/{lang}.json` | `__lang_version__` | [`src/i18n.py`](../src/i18n.py) |
| `SMART_EXCLUDES_VERSION` | Diff pathspec exclusions | `~/.gitpr/conf/gitpr.smart-excludes.json` | `__lang_version__` | [`src/core.py`](../src/core.py) |
| `THINKING_WORDS_VERSION` | Spinner thinking words | `~/.gitpr/.env` (`SPINNER_THINKING_WORDS`) | `__lang_version__` | [`src/spinner.py`](../src/spinner.py) |
| `LINTER_PRESETS_VERSION` | External linter presets | `~/.gitpr/conf/gitpr.linter-presets.json` | `__lang_version__` | [`src/linter_wizard.py`](../src/linter_wizard.py) |
| `SCRIPTS_VERSION` | Git hook scripts | `.git/hooks/` | `__scripts_version__` | [`src/core.py`](../src/core.py) |

Four of the five compare against `__lang_version__`, so a single bump refreshes them
as a block. Hook scripts are versioned independently by `__scripts_version__`
because they change on a different cadence.

---

## 3. `LINTER_PRESETS_VERSION`

Tracks [`templates/gitpr.linter-presets.json`](../templates/gitpr.linter-presets.json),
the catalogue of ready-made external linter definitions offered by `gitpr --linter-setup`
(Checkstyle-compatible bridges: ESLint, PHPCS, Checkstyle, and so on).

Its purpose is to let **new linters reach existing installations without a release**.
Adding a preset to the template is enough — the next `--linter-setup` on a client whose
marker is stale re-downloads the catalogue.

Resolution chain in `_load_linter_presets()`:

1. Local copy at `~/.gitpr/conf/gitpr.linter-presets.json`, when
   `LINTER_PRESETS_VERSION == __lang_version__`.
2. Fresh download from the remote template — local copy written, marker updated.
3. Stale local copy, when the download fails (offline).
4. Built-in `_LINTER_PRESETS` constant, as a last resort.

> **Not to be confused with the GitPR release version.** `__version__` (`0.0.37`)
> identifies the CLI itself; `LINTER_PRESETS_VERSION` only records which preset
> catalogue snapshot is cached locally. The two move independently.

---

## 4. Incrementing a marker

Markers in `.env` are written by GitPR — **never edit them by hand**. What you change
is the constant in [`src/updater.py`](../src/updater.py) that they are compared against:

```python
__lang_version__ = "v0.0.20"     # translations, smart excludes, thinking words, linter presets
__scripts_version__ = "v0.0.3"   # Git hook scripts
```

To publish a change to any `__lang_version__`-backed resource:

1. **Merge the template change to `main` first.** Clients fetch from
   `raw.githubusercontent.com/natanfiuza/gitpr/main/...`, so the new content must
   already be there.
2. **Then** bump `__lang_version__` and release.

Doing it in the opposite order pins clients to the *old* file under the *new* marker:
they download whatever `main` currently serves, stamp the new version, and never
retry — the fix silently never arrives.

### Checklist

- [ ] Template updated and merged to `main`
- [ ] `__lang_version__` (or `__scripts_version__`) bumped in `src/updater.py`
- [ ] Change verified on a client with a stale marker
- [ ] `langs/*.json` parity still green (`pytest tests/test_i18n.py`)

---

## 5. Related

* [ARCHITECTURE.md](ARCHITECTURE.md) — §16 Version Markers
* [hooks-versioning.md](hooks-versioning.md) — `SCRIPTS_VERSION` specifics
* [linter-regras-customizadas.md](linter-regras-customizadas.md) — linter presets and `--linter-setup`
