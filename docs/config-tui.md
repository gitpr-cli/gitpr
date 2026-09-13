# Technical Documentation: Interactive Configuration Screen (`gitpr config`)

GitPR is configured through `~/.gitpr/.env`, a dotenv file with around fifty variables. Until now, changing one meant knowing its exact name, opening the file by hand, and guessing whether the value is `true`, `1` or `yes` — and a value the reader does not understand is swallowed silently, so a typo never surfaces as an error.

`gitpr config` opens a master-detail screen over that same file: categories on the left, the settings of the selected one on the right, edited in place. It is a thin layer on top of the file you already have — not a second source of configuration.

```bash
gitpr config
```

---

## 1. The Screen

```text
┌ Header ──────────────────────────────────────────────┐
│ Configurações      [/ buscar…]   ● 2 não salvas      │
├──────────────┬───────────────────────────────────────┤
│ Geral        │  Idioma da interface                  │
│ Provedores…  │  [ pt_br            ▾ ]               │
│ Pull Request │                                       │
│ …            │  Co-autor                             │
│              │  [ ●] habilitado                      │
├──────────────┴───────────────────────────────────────┤
│ F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc │
└──────────────────────────────────────────────────────┘
```

| Key | Action |
| --- | --- |
| `F1` | Help — the shortcut list and how values are read |
| `F2` | Validate and save the pending changes |
| `Ctrl+R` | Restore the default of the focused field (removes the line) |
| `/` | Search a variable name or a label across every category |
| `Esc` | Leave — or clear the search first; asks before discarding |

### 1.1 Categories

The sidebar mirrors the commands and flags of the CLI, so the setting you want is where the feature you use is. The first entry is always **General**:

| Category | Holds |
| --- | --- |
| **General** | Interface language, co-author trailer, general log |
| **AI Providers** | Default engine, AI timeout, both API keys, and the models of each provider — under a sub-section per provider, shown one at a time |
| **Pull Request** | `OUTPUT_FILE_NAME`, base branch, auto commit/stage/merge, linter skip, publish log, reviewer suggestions |
| **Code Review** | `OUTPUT_FILE_NAME_REVIEW`, `_FULLREVIEW`, `_FILEREVIEW` |
| **Issue** | `OUTPUT_FILE_NAME_ISSUE` |
| **Blame** | `OUTPUT_FILE_NAME_BLAME` |
| **Linter** | `OUTPUT_FILE_NAME_LINTER`, `GITPR_LINTER_TIMEOUT` |
| **Release** | Changelog path, AI summary, auto bump, draft by default, `OUTPUT_FILE_NAME_RELEASE` |
| **SCM / Forge** | Provider, CI/CD token, forge token, base URL; **GitHub**, **Bitbucket** and **Azure DevOps** sub-sections with what each forge needs |
| **Diff Filters** | Smart excludes switch and both filter-list paths |
| **Skills** | The seven skill files of this project — one entry per skill, edited in place (§1.7) |
| **Advanced** | Three sub-sections — **Spinner**, **Git Hooks**, **Downloads** — hidden until you turn on **Show advanced** |
| **Unknown** | Keys in the file the schema does not declare — appears only when they exist |

Each of the twelve categories links to its own technical documentation (§1.5).

### 1.2 Controls

Each field gets the control its type deserves, so an invalid value is hard to produce in the first place:

| Type | Control |
| --- | --- |
| Boolean | Switch |
| Enum | Select |
| Integer | Text input, validated |
| Filename template | Text input, validated against the placeholders |
| Path, free text | Text input |
| Secret | Masked input |
| Word list | Read-only box that scrolls on its own, with the entry count above it and a download button (§1.4) |

### 1.3 Filtered by the Selected Value

Two settings decide which other settings are on screen, and the panel follows the selection **immediately** — before anything is saved:

| When you select | You see |
| --- | --- |
| A **Default Provider** | Only that provider's models. With nothing selected, no provider section is shown at all |
| A **Forge Provider** | Only that forge's sub-section, plus the fields every forge shares |

Search ignores the filter on purpose: searching `deepseek` with Gemini selected still finds the DeepSeek models, so you can pre-fill a provider you are about to switch to. A hidden field with a pending edit is still saved — visibility is a view, not a permission.

### 1.4 Download Buttons

Four lists are served from the GitPR repository and refreshed when their version marker changes. **📥 Force download** next to a version marker re-downloads it on demand, and **📥 Download the word list** does the same for the spinner words. This is the manual escape hatch for the case the automatic check cannot see: the list is present, current, and still not what you want.

The button reports the outcome honestly, because a download can fail and fall back to the copy already on disk without any way to tell the two apart from the outside:

| Feedback | Meaning |
| --- | --- |
| `✔ v0.0.24` and *"{name} is up to date ({version})."* | The file now carries the current version — either freshly downloaded or a copy that was already current |
| `✖ not updated` and *"Could not download {name}. The previous copy stays in use."* | The download failed. Nothing was lost: the previous copy is intact and still in use |
| *"English needs no translation pack — there is nothing to download."* | The translation pack has no English edition to fetch, since English is built in |

The verdict comes from re-reading `~/.gitpr/.env` after the download, never from `os.getenv()`: `load_dotenv()` runs with `override=False`, so the process still holds the value it started with.

### 1.5 Documentation Link

**📚 Documentation** at the top of the right pane opens the technical documentation of the category you are looking at, and the URL is printed next to the button so you can read or copy it first.

| Category | Document |
| --- | --- |
| General | `config-tui.md` |
| AI Providers | `providers-ia.md` |
| Pull Request | `pull-request-publication.md` |
| Code Review | `code-review-ia.md` |
| Issue | `gitpr-issue-option.md` |
| Blame | `blame-arqueologo.md` |
| Linter | `linter-regras-customizadas.md` |
| Release | `release-notes.md` |
| SCM / Forge | `scm-multiforge.md` |
| Diff Filters | `smart-excludes.md` |
| Skills | `skill-template.md` |
| Advanced | `version-markers.md` |

The link follows the interface language (`?lang=pt_br`), and the line disappears in the search view and in **Unknown**, which is not a category GitPR owns.

### 1.6 The Advanced Toggle

**Show advanced** in the toolbar reveals the `Advanced` category and every field marked internal. Most of it is version markers GitPR maintains itself while downloading translations, linter presets, spinner words and filter lists; they are shown for transparency, not for editing. The toggle is off on every launch.

Two of those fields are not markers and are worth knowing about:

- **Hooks Language** (`SCRIPTS_LANG`) — the language the Git hooks are installed in. Empty means "follow the interface language", which is what most users want; picking one installs the hooks in that language on the next run. **Installed Hooks Language** next to it is read-only and records what is actually on disk, so the two are never confused.
- **Spinner Words** — the list itself, read-only, in the box described in §1.2.

### 1.7 The Skills Section

The screen edits `~/.gitpr/.env` everywhere else. **Skills** is the one section that does not: it edits the project's own skill files — the AI instructions read from `./.gitpr/skill/` ([Skills and Templates System](skill-template.md)).

The list holds one entry per skill GitPR supports: **Commit**, **Pull Request**, **Code Review**, **File Review**, **Issue**, **Blame**, **Release**. It is the list of skills the commands load, not a listing of the folder — a file in `.gitpr/skill/` that no command reads is not offered here.

| The entry shows | Meaning |
| --- | --- |
| nothing | The file is there and writable — edit it in the box on the right and press `F2` |
| **● edited** | An edit of yours is still unsaved |
| **not in this project** | The file does not exist. The box shows *"This project has no {name} file yet."* and the editor is disabled — an empty box would read as "this skill is empty", which is the opposite of what is true |
| **read only** | The file exists but cannot be written. It is shown, locked, and has nothing to save |

**📥 Download the template** appears for an absent skill and fetches the template published for your interface language, like the download buttons of §1.4. When even that cannot be written — an unwritable `.gitpr/skill/` folder — the button stays disabled with the reason next to it.

`F2` saves the `.env` fields **and** the skill files in the same pass, and the pending counter covers both. Inside the pane, `Ctrl+R` drops the edit and restores the text on disk — the closest thing to a default a file has — and `Esc` asks before discarding it, as everywhere else.

Each file keeps the line endings it already had, so a `CRLF` file stays `CRLF` and your diff shows only the lines you edited.

---

## 2. How Values Are Read

**The screen shows what is in the file, not what the process is using.** The difference matters, because `load_dotenv()` runs with `override=False` throughout GitPR: when a variable is also exported in your shell, the environment wins and the file is ignored at runtime.

A field in that situation is flagged with **⚠ in environment**, and the value on screen is still the one from the file. Editing it is allowed — it just will not take effect until the variable is unset in the environment. This is deliberate: without the flag you would see a value that silently is not the one in use, which is the most confusing failure this file can produce.

Values are read with a file-only parser, never from `os.getenv()`, so nothing from the current process leaks into the screen.

---

## 3. Editing and Saving

Nothing is written until you press `F2`. While you edit, `F2` shows a counter of pending changes and `Esc` asks for confirmation before leaving:

- **Save** writes only the fields you actually changed, so unrelated lines keep their comments and their position in the file.
- **Skill files** are written by the same save: one `F2` covers the pending `.env` fields and the edited skills (§1.7). A skill that fails to write is reported by name and keeps its edit pending — the other files are still saved.
- **`Ctrl+R`** on a field does **not** rewrite the built-in default — it marks the line for **removal**, so the value falls back to whatever the code defaults to. The field renders `— will be removed —` and pressing `Ctrl+R` again undoes the mark. This is the honest reset: writing the current default would freeze it into the file and stop tracking future default changes.
- **Emptying a field** clears the override.
- After a successful save the screen stays open, re-reads the file, and reports how many settings were saved.

### 3.1 Validation

`F2` validates before writing anything. A field that fails gets a red border and an inline message, nothing is saved, and the screen jumps to the first offending field — switching category and turning on **Show advanced** if that is where it lives.

| Rule | Why |
| --- | --- |
| `true` / `false` only, plus `1`/`0`, `yes`/`no`, `y`/`n`, `off` | GitPR has two boolean readers that disagree outside this set. `on` looks symmetric with `off` but is read as **false** by one and **true** by the other |
| Integers must be greater than zero | An unparseable timeout is silently replaced by the default, so a typo never shows up as an error |
| Enums must be one of the declared choices | An unknown provider name is not rejected at startup, it just does not work |
| Templates must use known placeholders and keep `{datetime}` | An unknown placeholder is a `KeyError` on the next command; without `{datetime}` every run resolves to the same filename and overwrites the previous report |

### 3.2 Credential Validation

A secret (API key, forge token) is validated against its provider before being saved, because a wrong credential is only discovered later, in the middle of a real command. Validation runs in the background so the screen never freezes, and the result decides:

| Result | Behaviour |
| --- | --- |
| Accepted | Saved |
| Refused (HTTP 401/403, or an "invalid API key" reply) | **Blocked** — the credential is wrong and storing it helps nobody |
| Network failure, timeout, unreachable provider | **Saved with a warning** — a correct key typed behind a proxy must not be rejected |

Only the secrets you changed in this session are revalidated. A key that was already in the file and left untouched is not re-probed on every save.

Secret values are **never displayed back**. The field is empty when nothing is stored, and shows a fixed placeholder (`•••••••• (set — type to replace)`) when a value exists — the same mask regardless of the secret, because the real value is never read into the screen. It enters the save only when you type something into it. Secrets are encrypted at rest with the local Fernet key in `~/.gitpr/secret.key`; the screen encrypts at write time and never decrypts to fill a field.

---

## 4. Search, and Keys Outside the Schema

Typing in the search box filters by variable name **and** by label, across every category at once — `timeout` finds the AI and the linter timeouts without you knowing which category holds them. While a search is active the main area shows the matches as one flat list, with a count, instead of the selected category's fields; the sidebar stays where it is. `Esc` clears the search — and returns the focus to the sidebar — before it can leave the screen.

Variables present in the file that GitPR does not declare land in an **Unknown** category that only appears when such keys exist. They are read-only: the screen never writes a key it does not own. Changing one means editing the file by hand.

---

## 5. Deliberately Not Editable

These keys get no editable field. The screen never hides a key that is in your file — it only refuses to **write** to one it does not own — so all but the last still show up, read-only, under **Unknown** (see §4).

| Variable | Why not |
| --- | --- |
| `GITPR_SCM_TOKEN` | The raw CI/CD token takes precedence over the encrypted one and is stored in plain text. It has a row in **SCM / Forge** — read-only and never displayed — pointing at `gitpr --init`, which is the only thing that should write it; a writable field would invite shadowing the token you set up there |
| `PR_AUTO_PUBLISH` | A leftover from before publishing became the default flow. Read nowhere: what replaced it is the `--no-edit` flag. An older install may still carry its line in `.env`, which is why it shows up under **Unknown** |
| `CI`, `GITHUB_ACTIONS` | Process environment markers, never written to this file, so they never appear at all |

---

## 6. For Developers

The screen is built from a declarative schema, so adding a setting is a data change and not a UI change.

| File | Role |
| --- | --- |
| `src/config_schema.py` | Pure data: `ConfigField`, `Category`, `Group`, `CATEGORIES`, `GROUPS`, `FIELDS` (56 fields), plus `fields_of()`, `validate_field_value()` and the lookup helpers. Single source of truth for menu, widgets, defaults, sub-sections, visibility and validation |
| `src/doc_links.py` | `doc_url(filename)` — the documentation base URL and the `?lang=` rule. Separate from `core.py` because the screen may not import `src.core`, which pulls the AI SDKs on every launch |
| `src/ui/config_app.py` | `ConfigApp` plus the help and confirm modals. Master-detail layout, dirty state, search, the advanced toggle, the visibility filter, the download workers, the Skills pane (§1.7) and the save pipeline |
| `src/config.py` | Four added functions: `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()`. It also holds the skill registry (`SKILL_FILES_BY_TYPE`, `SKILL_TYPES`) and the file helpers (`read_skill_file()`, `write_skill_file()`, `skill_file_status()`) that `get_skill_context()` and the Skills section both read (§1.7) |
| `src/main.py` | The `config` subcommand — no `setup_environment()`, so nothing can prompt on stdin inside the full-screen app |

Three attributes of a `ConfigField` carry the layout: `group` puts the field under a sub-heading, `show_if` hides it unless another field holds one of the listed values, and `action` attaches a download button. `version_source` says which constant to display when a version marker is not in the file yet — an empty `LINTER_PRESETS_VERSION` shows the version shipped in the code instead of an empty box.

**Adding a setting:** declare a `ConfigField` with a literal `__("…")` label and description, add the key to `DEFAULT_CONFIG` if it is a new seeding default, and translate the new keys into the six `langs/*.json`. `tests/test_config_schema.py` fails until the schema and `DEFAULT_CONFIG` agree — and until a new `group`, `show_if` or `action` points at something that exists — and `tests/test_i18n.py` fails until every language file carries the new keys.

**State model:** pending edits live in a dictionary keyed by variable name, not in the widgets. The visible row set changes as you navigate or search, and a value read back from a hidden control would be fragile — so `F2` is independent of what is on screen at that moment.

**Filesystem writes** go through `python-dotenv`'s `set_key()`/`unset_key()`, which write a temporary file and rename it, and preserve comments and ordering. The screen never rewrites the file wholesale.

Architecture vocabulary: [Configuration Glossary](plans/glossary-config-tui.md).

> **Note:** `gitpr -h config` opens the screen and ignores the `-h`, because the root callback returns early for every subcommand. Use `gitpr config -h` for the help text.
