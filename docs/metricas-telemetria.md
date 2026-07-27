# Metrics & Telemetry — Local Offline Analytics

GitPR includes a **local, offline telemetry system** that collects anonymous
usage events (CLI commands, AI calls, linter runs, git hooks) for team
analytics. Nothing leaves your machine — all data stays under `~/.gitpr/metrics/`.

## ✨ What It Does

Every GitPR command generates a small JSON event file recording:

| Field | Description |
|-------|-------------|
| `timestamp` | When the event occurred (ISO 8601) |
| `command` | Which command ran (`commit`, `review`, `fullreview`, `linter`, `blame`, etc.) |
| `status` | Outcome (`success`, `error`, `triggered`, `no_changes`) |
| `provider` | AI provider used (`gemini`, `deepseek`, `ollama`, `local`) |
| `tokens_estimated` | Token count from AI usage metadata |
| `duration_ms` | Command duration in milliseconds |
| `repo` | Repository name (`owner/repo`) |
| `branch` | Current branch name |

Additional fields like `linter_errors`, `linter_warnings`, `cache_hit`, and
`map_reduce_triggered` provide deeper context for specific command types.

## 📁 Where Data Is Stored

```
~/.gitpr/metrics/
├── {owner}/{branch}/
│   ├── XXXX-XXXXX-XXXX_20260726.json   ← event file
│   └── YYYY-YYYYY-YYYY_20260726.json
├── config.json                          ← export state
└── export/
    ├── gitpr_metrics_2026-07-26.csv     ← consolidated CSV
    └── gitpr_metrics_2026-07-26.json    ← consolidated JSON
```

Each event file is named with a unique UUID and date to avoid collisions.

## 🚀 CLI Commands

### Show Summary

```bash
gitpr --metrics
```

Displays total files, disk usage, and the metrics directory path.

### Export Data

```bash
gitpr --metrics --export
```

Scans all unexported event files, consolidates them into CSV and JSON reports
in `~/.gitpr/metrics/export/`, and tracks which files have been processed.

- **CSV columns:** timestamp, command, status, provider, tokens_estimated,
  duration_ms, repo, branch
- **JSON:** full array of event payloads
- **Progress bar:** visual feedback via `click.progressbar()`

### Purge Data

```bash
gitpr --metrics --purge
```

Deletes all local metric files after confirmation. Preserves `config.json`
for future export tracking.

### Interactive Dashboard

```bash
gitpr --metrics --dashboard
```

Launches a **TUI dashboard** (Textual) showing:

- **Summary bar:** total events, errors, total tokens, top commands, top providers
- **Events table:** last 100 events with timestamp, command, status, provider, tokens, duration
- **Keyboard shortcuts:** `F5` to refresh, `Esc` to exit

## 🔧 Git Hooks (Automatic Collection)

When installed via `gitpr --installhooks`, three additional hooks collect
behavioral telemetry:

| Hook | Event captured |
|------|---------------|
| `post-checkout` | Branch switches (context changes) |
| `pre-push` | Push events (delivery frequency) |
| `post-merge` | Pull/merge events (integration frequency) |

These hooks use `gitpr --hook-event <name> --quiet` — a hidden flag that logs
the event silently without output.

## 📊 Use Cases

- **Tech Lead:** See if the team is actually using AI reviews or ignoring hooks
- **Finance:** Compare Gemini vs. DeepSeek vs. Ollama usage to optimize API costs
- **Quality:** Identify which modules trigger the most linter errors or blame analysis
- **Process:** Detect if map-reduce is firing often (large PRs — potential process issue)

## 🔒 Privacy

- **100% local** — no data is ever sent to external servers
- **Anonymous** — events contain repo/branch but no file contents or diffs
- **User-controlled** — export and purge are manual; nothing is auto-deleted
- **Opt-in hooks** — git hooks only install if you run `gitpr --installhooks`

## 📚 Related Documentation

- [MCP Integration](mcp-integration.md) — MCP server setup
- [MCP Prompts](mcp-prompts.md) — Pre-built message templates
- [MCP Tool Annotations](mcp-annotations.md) — IDE integration hints

---
**Pro tip:** Combine metrics exports with your team's CI pipeline by running
`gitpr --metrics --export` on a schedule and versioning the CSV in your repo.
