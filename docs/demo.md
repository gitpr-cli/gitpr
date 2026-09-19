# Technical Documentation: Guided Tour (gitpr demo)

`gitpr demo` walks through the three things GitPR does with a change — the commit message, the code review and the pull request description — over an example diff that ships inside the package. Nothing is generated and nothing is sent anywhere: the answers were recorded once and are replayed, so the tour runs with **no API key, no Git repository and no connection**.

It exists to collapse the distance between `pip install gitpr-cli` and "I understand what this tool is for". Every other feature needs configuration before it will show you anything: a provider, a key, a forge token, a repository with a diff in it. The tour needs none of them, which makes it the one command that works on a machine where GitPR has never run before.

---

## 1. Overview

The tour is a subcommand, not a flag: `gitpr demo` never reaches the API-key setup, the PyPI update gate or the internet check, because nothing downstream of it needs a configured environment.

### 1.1 Command Reference — `gitpr demo`

All options of the subcommand, as shown by `gitpr demo -h` (or `--help`):

```bash
gitpr demo                                  # the default scenario, in the screen
gitpr demo --scenario security-issue        # the other shipped example
gitpr demo --no-tui                         # plain text, no screen
gitpr demo --lang pt_br --no-tui            # the tour in Portuguese
```

| Option | Description |
| --- | --- |
| **`--scenario <name>`** | Which example to walk through. Without it the first registered scenario is used. An unknown name exits 1 and lists the ones that exist |
| **`--lang <code>`** | Interface language for this run (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`). Overrides `GITPR_LANG` for the run and is not persisted |
| **`--no-tui`** | Prints the tour as plain text instead of opening the screen. For CI, for limited terminals and for recordings |
| **`-h` / `--help`** | Help plus the documentation link for the current language |

| Characteristic | Description |
| --- | --- |
| **Content** | Answers recorded once by GitPR and shipped as source in the package — replayed, never regenerated |
| **AI provider** | None is instantiated and no key is read. The pipeline runs for real, with the model call replaced |
| **Network** | None. No HTTPS request, no DNS, no socket |
| **Git** | None. No repository is required; the tour does not run a single `git` command of its own |
| **Files written** | None. No `.md`, no `.txt`, no cache entry, no metric |
| **Screen** | A Textual app, or plain text with `--no-tui` (identical content either way) |
| **Exit code 1** | An unknown `--scenario` name |

---

## 2. The Six Steps

The tour is linear: six screens, in this order, each with a heading, a line of framing prose and the artifact it is about.

| # | Step | What it shows |
| --- | --- | --- |
| 1 | **Welcome to GitPR** | What the tool does, and the promise of the tour: a recorded example, no key, no repository, no connection |
| 2 | **The example change** | The unified diff — code, in English, in every language |
| 3 | **Commit message** | What `gitpr -c` writes for that diff: a Conventional Commits subject plus the reasoning that does not fit in it |
| 4 | **Code review** | What `gitpr -r` reports, composed exactly as the local review is: the linter alerts first, the review below |
| 5 | **Pull request description** | What `gitpr` writes for the branch: what changed, why, and what the reviewer should look at |
| 6 | **Next steps** | `gitpr --init` for the real thing, the documentation link, and how to run the tour again |

### 2.1 Keys

| Key | Action |
| --- | --- |
| `n`, `→`, `Enter` | Next step. On the last step it leaves the tour |
| `p`, `←` | Previous step. On the first step it does nothing (a bell, not an exit) |
| `F1` | Help modal: the keys, and what the tour is running on |
| `Esc` | Leaves the tour, from any step — and from inside the help modal |

Going back is free: the three artifacts are generated once, before the first screen, so stepping back never regenerates anything and the tour cannot show a different answer the second time. A step counts as seen when you leave it forward, so re-reading an earlier one does not un-see it.

---

## 3. Where the Answers Come From

The tour is not a slideshow with hard-coded screens: it calls the same `generate_pr_content()` that `gitpr -c`, `gitpr -r` and `gitpr` call, and the same `compose_review_content()` that renders the local review. Only the model call is replaced — by a fake that returns the scenario's recorded answer — which is what keeps the tour from drifting away from what the real commands print.

Everything the pipeline would otherwise reach outward for is neutralized for the duration of the tour:

| Replaced | Why |
| --- | --- |
| **`call_ai_model`** | The source of the data: a fake that replays the recorded answer and records the call |
| **`get_cached_response` / `save_cached_response`** | A cache read would replay *your* old review of a real branch, and a cache write would file the demo's answer under a real prompt — the tour reads and writes nothing |
| **`log_command_metric` / `log_local_metric`** | Telemetry writes to `~/.gitpr/metrics/` with no off switch, and a tour is not usage of a feature |
| **`get_api_key` / `get_api_model`** | The PR pipeline gives up *before* calling the model when the key or the model is missing, so it must be answered |
| **`get_skill_context`** | Determinism: a local `.gitpr/skill/` file would change what the tour shows, and print its "template loaded" line into the middle of it |

The diff itself is repository code and stays in English in every language — translating `Rule::unique()` would misrepresent what the tool reads. The prose around it, the reviews and the PR descriptions are translated.

A scenario that fails to produce one of the three artifacts raises instead of rendering a blank screen: an empty tour looks like the tool found nothing, when the real cause is that the pipeline never reached the provider.

---

## 4. The Shipped Scenarios

| Scenario | Stack | The change |
| --- | --- | --- |
| **`laravel-bug-fix`** (default) | PHP / Laravel | A profile update that rejects the user's own e-mail address — `unique:users,email` with no `ignore()`, where the fix adds the ignore rule |
| **`security-issue`** | TypeScript / Express | An IDOR in an invoice download: the row is resolved by primary key alone, so any authenticated user can download another organisation's invoice |

Each is a Python module under `src/demo/scenarios/` exposing three names:

```python
NAME = "laravel-bug-fix"   # the value --scenario takes
DIFF = """..."""           # the unified diff — code, never translated
TEXT = {"en": {...}, "pt_br": {...}, ...}   # the prose and the recorded answers
```

Scenarios are modules rather than JSON data files because the package ships zero non-`.py` files: `pyproject.toml` collects `src` and `src.*` through `packages.find` and has no `package_data`, so a data file would be missing from the wheel with nothing failing at build time.

To add one, drop a module in that directory, register it in `src/demo/scenarios/__init__.py`, and copy the shape above. `TEXT["en"]` is required and is the fallback for every other language; the tests enforce that each language present carries `title`, `description`, `commit_message`, `review`, `linter` and `pr_description`, non-empty, with the hunk headers of `DIFF` adding up.

---

## 5. Languages

The tour has two halves and they are translated separately:

| Half | Where it lives | Languages |
| --- | --- | --- |
| **Chrome** — step titles, framing prose, help modal, next steps | `langs/*.json`, like every other string in the tool | `pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr` |
| **Scenario prose** — the example's own title, review, commit message, PR description | Inside each scenario module, under `TEXT` | `en`, `pt_br`, `pt_pt`, `es_es`, `fr_fr` |

A scenario whose language has no `TEXT` entry falls back to English for that half rather than failing or mixing — a partially translated language degrades instead of breaking. The scenario reports which language it actually used.

`--lang` is declared by the subcommand itself, because the root callback returns before its own `--lang` handler runs for any subcommand. Without the flag, the tour follows `GITPR_LANG` / the detected system language, the same one the surrounding interface is in, so both halves always agree.

---

## 6. What the Tour Does Not Touch

| Not touched | Because |
| --- | --- |
| Your AI provider and keys | The model call is replaced; no key is read, and none needs to exist |
| `~/.gitpr/cache/prompts/` | Both cache calls are replaced, so the tour cannot read a real cached review or poison the cache with a recorded one |
| `~/.gitpr/metrics/` | Both metric calls are replaced |
| Your working tree and your repository | No `git` command of the tour's own runs, and no file is written — no report, no `.md`, no `.txt` |
| `.gitpr/skill/` | The skill lookup is replaced, so a local template never changes what the tour shows |
| The forge | No token, no API call, no repository |

**One line is still written.** The invocation log (`~/.gitpr/logs/`) records the run like any other command, from the root CLI callback that every command and every `-h` goes through, together with the one `git config` lookup that labels the line with the repository and the author. It is local and best-effort — a read-only home or a missing `git` never turns into a failed command — and `GITPR_SHOW_LOGS=false` turns it off. Nothing else about the tour leaves a trace.

---

## 7. Environment Variables

The tour introduces **no new configuration**. It reads what the rest of the tool already reads:

| Variable | Purpose |
| --- | --- |
| `GITPR_LANG` | Interface language, when `--lang` is not given |
| `GITPR_SHOW_LOGS` | Turns the invocation log off (`false`), for any command |

No key, token, model or path variable is read: on a machine with an empty `~/.gitpr/`, `gitpr demo` is the one command that still works.

> **Note:** See also the [Code Review documentation](code-review-ia.md) for what the fourth step is previewing, and the [Commit Messages documentation](commit-message-ia.md) for the third.
