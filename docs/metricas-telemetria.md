# Metrics & Telemetry — Local Offline Analytics

GitPR keeps a **local, offline usage ledger**: one row for every command it ran,
what it cost, and how long it took. Nothing leaves your machine — the ledger is a
SQLite file at `~/.gitpr/metrics/telemetry.db`.

## ✨ What It Does

Every executed command appends a row to the ledger recording:

| Field | Description |
|-------|-------------|
| `timestamp` | When the command finished (ISO 8601) |
| `command` | Which command ran (`commit`, `review`, `fullreview`, `linter`, `blame`, `hook:post-checkout`, etc.) |
| `status` | Outcome (`success`, `error`, `fired`, `no_changes`) |
| `provider` | AI provider that answered (`gemini`, `deepseek`, `ollama`) |
| `model` | Model the provider answered with |
| `prompt_tokens` / `completion_tokens` | Token counts as reported by the provider |
| `tokens_actual` / `tokens_estimated` | The count to read: measured when the provider reports it, estimated otherwise |
| `duration_ms` | Command duration in milliseconds |
| `repo` | Repository as `owner/name`, resolved by the same multi-forge parser as the rest of the CLI |
| `branch` | Current branch name |
| `author_name` | Local Git author of the run |
| `modules` | Modules the diff touched, normalized to the first two path segments (`src/fix`, `(root)` for a file at the repository root) |
| `source` | `execution` for a command that ran, `cache_backfill` for a row reconstructed from the AI cache |

Rows also carry `cache_hit`, `map_reduce`, `chunks_count`, `linter_errors` and
`linter_warnings`, which are meaningful for some commands and zero for the rest.
`modules` is **empty** for the commands that never had a diff in hand — the
linter, the blame engine and the hooks all record executions without one, and the
modules section adds them up under `(no module)` instead of passing them off as
a module named after nothing.

## 📁 Where Data Is Stored

```
~/.gitpr/metrics/
├── telemetry.db         ← the ledger: one row per executed command (SQLite)
└── .migration_declined  ← written only if you declined the import

~/.gitpr/metrics_legacy/    ← the pre-ledger event files, moved here after import
~/.gitpr/cache/prompts/     ← AI response cache, the source of a cache reconstruction
```

Exports go to the repository you run the command in, never to your home
directory:

```
./.gitpr/metrics/export/
├── gitpr_metrics_2026-09-28.csv    ← consolidated CSV
├── gitpr_metrics_2026-09-28.json   ← consolidated JSON
└── gitpr_metrics_2026-09-28.db     ← bundle written by `gitpr metrics bundle`
```

The ledger replaced per-event JSON files named
`{uuid}_{YYYYMMDD}.json` under `~/.gitpr/metrics/{owner}/{branch}/`. Those files
are imported once and **moved, never deleted** — they end up in
`~/.gitpr/metrics_legacy/`, outside the directory the summary counts.

## 🚀 CLI Commands

### Show Summary

```bash
gitpr metrics
```

Counts rows, not files: the ledger path, how many executions it holds, how many
rows were reconstructed from the cache, and the size on disk. A warning appears
while event files from before the ledger are still waiting to be imported.

Under the header come the sections, in the order they are read:

| Section | What it answers |
|---------|-----------------|
| 💰 Cost | How many tokens, and what they cost per model |
| 🧪 Quality | Linter pass rate, and how often the map-reduce path fired |
| 🧩 Modules | Which modules the runs touched, and how many tokens each took |
| 🤖 Providers | Runs and tokens per provider — including the ones that never call an AI |
| ⏱ Cycle | How long the merged pull requests of this repository took, read from the forge |

A section with nothing to say is left out rather than printed empty. The
dashboard draws these same lines from the same renderer, so the terminal and the
TUI cannot tell two stories about one ledger.

### The Window

One window, one meaning — the same flags limit the summary, the dashboard, the
export, the bundle and the MCP tool:

```bash
gitpr metrics --days 30
gitpr metrics --since 2026-01-01 --until 2026-03-31
```

The window is **inclusive on both ends** and lands on the date the row is about.
With no flag at all, the ledger sections read the whole ledger — except the
cycle, which asks the network for its answer and therefore defaults to the last
30 days, saying so in its own header rather than narrowing in silence.

### Cost and Rates

The cost section turns tokens into money with two layers, the second overriding
the first per model:

1. **A built-in table** of the vendors' published list prices for the fixed
   model IDs GitPR ships with (`deepseek-v4-flash`, `deepseek-v4-pro`,
   `gemini-2.5-pro`, `gemini-2.5-flash-lite`), so the section says something on
   a machine nobody configured.
2. **The environment**, per model:

```ini
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT=0.435
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT=0.87
GITPR_METRICS_CURRENCY=USD
```

`<MODEL>` is the model name uppercased, with every run of anything that is not a
letter or a digit collapsed into one `_`. Both rates are required: a model with
only one of them is reported in tokens alone, because pricing the other half at
an unconfigured zero would understate the bill.

- **The currency defaults to USD**, which is what the built-in table is quoted
  in. Configure rates in another currency and set `GITPR_METRICS_CURRENCY` to
  it — the built-in table then steps aside, because a dollar rate printed under
  another currency's label is a wrong number rather than a missing one.
- **Providers that run on this machine** (`ollama`, `local`) cost zero by
  definition and need no rate.
- **Rates move.** Converting tokens spent last year at today's price is an
  approximation, and the section says so on the line below the total.
- **A total that leaves models out says so** — `Total (partial)` — instead of
  letting a sum of the priced rows read as the whole bill.

### The Cycle Metric

The ⏱ section is the only metric here that does not come from the ledger, and it
cannot: the ledger records what GitPR ran on this machine, while a pull request
is merged on the forge, by people who never ran GitPR. So this one needs a token
and the network, and it is the one section that can come back with nothing for a
reason that is not "nothing happened".

It measures `created_at → merged_at` of the pull requests the forge reports as
merged in the window — **the pull request's own cycle**, from opening to merge.
It is not the time from the first commit of a branch to its pull request: the
listing contract carries no branch commits, so that interval is not available
here, and it is not invented from the ledger either.

The header names the repository and the window — `⏱ Cycle · owner/repo · last 30
days` — because this is the one section whose scope is not the ledger's: read
next to a summary that says "All repositories", a bare number would look like it
covered them all.

Every failure degrades to a line, never to a stack trace:

| What happened | What the section shows |
|---------------|------------------------|
| No origin remote, no usable forge, no token, no network | `Not read: <the reason>` |
| The forge publishes no merge date (Bitbucket) | Says so, without spending a network call |
| The window holds no merged pull request | `No pull request was merged in this window.` |

A merge whose date precedes its own creation is a clock the forge got wrong, not
a negative cycle: that row is dropped rather than averaged in.

### Export Data

```bash
gitpr metrics export
```

Writes the rows that were never exported before to CSV and JSON in
`./.gitpr/metrics/export/`, then marks them as exported — so a second run reports
"No new metrics to export." instead of repeating itself. The export covers the
working copy's repository.

- **CSV columns:** timestamp, day, command, status, provider, model,
  prompt_tokens, completion_tokens, tokens_actual, tokens_estimated, duration_ms,
  repo, branch, author_name, modules, cache_hit, map_reduce, linter_errors,
  linter_warnings, chunks_count, source
- **JSON:** the same rows as objects, ready to be read by a script

### Bundle and Merge (Team Roll-Up)

`export` is what a person reads; a **bundle** is what another machine reads — the
same slice of the ledger as a self-contained `.db` file:

```bash
gitpr metrics bundle --days 30
gitpr metrics bundle --since 2026-07-01 --until 2026-09-30 -o ./handover/
gitpr metrics merge ./handover/gitpr_metrics_2026-09-29.db ./handover/other.db
```

`bundle` copies the rows of the window into a standalone SQLite file, schema and
`PRAGMA user_version` included, and writes to `./.gitpr/metrics/export/` unless
`-o` says otherwise. `merge` attaches each bundle and inserts the rows it does
not already have — the UUID is the primary key, so merging the same file twice,
or two overlapping bundles, never counts a run twice.

Schema versions are handled in **one direction only**: an older bundle is
migrated up on attach, and a newer one is refused *before* anything is written,
with the version it carries and the one this GitPR understands — the local
ledger is never left half-imported. Upgrade GitPR to read a newer bundle.

This is the answer to "what did the team spend in the quarter" without a server:
each machine bundles its own window, and whoever needs the total merges the
files into a ledger of their own.

### Import Pre-Ledger Data

```bash
gitpr metrics migrate
```

Reads the event files written before the ledger existed, inserts them, and moves
the originals to `~/.gitpr/metrics_legacy/`. With a terminal it opens a wizard
that also offers to reconstruct history from the AI response cache. Those rows
are marked `source: cache_backfill` because the cache keys an answer by its
prompt and therefore counts **distinct prompts, not executions**.

### Delete Old Records

```bash
gitpr metrics prune --before 2026-01-01
```

Deletes the rows written before a date, after confirmation, and reclaims the
space with `VACUUM`. `--source cache_backfill` restricts the deletion to
reconstructed rows. There is **no automatic expiry**: the ledger answers "what
did we spend this year", and a calendar that deletes on its own would change that
answer without anyone asking.

### Purge Data

```bash
gitpr metrics purge
```

The destructive path: deletes every row and every event file still waiting to be
imported, after confirmation.

### Interactive Dashboard

```bash
gitpr metrics dashboard
```

Opens a **TUI dashboard** (Textual) scoped to the working copy's repository:

- **Summary bar:** total entries, reconstructed rows, total tokens, total duration, top commands
- **Events table:** timestamp, command, status, provider, tokens, duration
- **Sections:** cost, quality, modules, providers and the cycle — the same lines
  `gitpr metrics` prints, drawn with Textual markup instead of click colours
- **Status bar:** the time range the table covers and how many entries it holds
- **Keyboard shortcuts:** `F5` to refresh, `Esc` to exit

While the ledger does not exist yet, the dashboard reads the cache and event
files instead, shows a progress bar while it scans, and says so on the status
bar. The cycle section is drawn either way: it never read the ledger.

## 🔧 Git Hooks (Automatic Collection)

When installed via `gitpr --installhooks`, three additional hooks collect
behavioral telemetry:

| Hook | Event captured |
|------|---------------|
| `post-checkout` | Branch switches (context changes) — fires only when the branch actually changed |
| `pre-push` | Push events (delivery frequency) |
| `post-merge` | Pull/merge events (integration frequency) |

All three run `gitpr --quiet metrics hook-event <name>`, a hidden action whose
whole job is to write one row and exit. The repository is resolved by the hook
itself, through the same parser the rest of the CLI uses, so GitLab, Bitbucket
and Azure DevOps record the same `owner/name` GitHub does. A guard around the
call — `command -v gitpr`, plus a trailing `|| true` — keeps a machine without
GitPR, or a GitPR that fails, from ever breaking your Git command.

## 📊 Use Cases

- **Tech Lead:** See which repositories, branches and authors are really running AI reviews, and which hooks fire
- **Finance:** Read the cost section for the bill per model, or `gitpr metrics --since 2026-07-01` for the quarter
- **Quality:** Read `linter_errors`, `linter_warnings` and `modules` to find which part of the project generates the most findings
- **Process:** Watch `map_reduce` and `chunks_count` — large PRs firing the map-reduce path point at a process problem
- **Delivery:** Read the cycle section to see how long the merged pull requests of this repository took, and which ones took longest

## 🔒 Privacy

- **100% local** — the ledger is a file on your machine; nothing about it is ever sent to external servers
- **The one exception is the cycle section** — it asks the configured forge for the merged pull requests of the repository you are standing in. It sends no ledger row, no token count and no diff: the question is "which pull requests were merged in this window", and the answer is read-only
- **Not anonymous** — every row carries the repository, the branch and the local Git author's name. It carries no file contents and no diffs: `modules` holds the path segments a run touched, never the file names, and the author's e-mail stays in the AI cache
- **User-controlled** — `prune` and `purge` are manual and confirmed; nothing expires on its own
- **Opt-in hooks** — git hooks only install if you run `gitpr --installhooks`

## 📚 Related Documentation

- [MCP Integration](mcp-integration.md) — MCP server setup
- [MCP Prompts](mcp-prompts.md) — Pre-built message templates
- [MCP Tool Annotations](mcp-annotations.md) — IDE integration hints

---
**Pro tip:** Exports land in `./.gitpr/metrics/export/`, inside the repository you
are in — that directory belongs to your machine, not to the project, and it is
what GitPR's own `.gitignore` entry keeps out of the tree. To answer "what did
this machine spend this quarter" without a spreadsheet, ask the ledger:
`gitpr metrics --since 2026-07-01`.
