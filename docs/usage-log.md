# Usage Log — every command GitPR runs

GitPR keeps a record of its own use: one line for every command, written as the command starts. It answers "what did I actually run, and when?" — useful when a flag behaved unexpectedly, when you want to know how often a feature is used, or when you are reconstructing what happened in a repository last week.

The log is local, plain text and never leaves your machine. Nothing is sent anywhere.

---

## 1. Where the Files Live

Every command appends one line to `~/.gitpr/logs/<uuid>.log`, and there is **one file per day**:

```text
~/.gitpr/logs/
├── 4b1c8d3e-1f27-5a44-9c0b-7d2e5f8a1b30.log   ← today
├── 9f2a7c10-6b83-5e21-8a4d-1c9f0e7b2d55.log   ← yesterday
└── pr_desc/                                   ← the PR publication log, a separate feature
```

The filename is a UUID **derived from the date** — `uuid5` of `gitpr.usage.<YYYY-MM-DD>` — not a random one. That is deliberate: a random name would need a counter or a state file to know which file belongs to today, and two GitPR processes running at the same moment could disagree about it. Derived from the date, the same day always resolves to the same name, so concurrent commands simply append to the same file.

A new day starts a new file. GitPR never rotates or deletes them — clearing old files is yours to do.

---

## 2. What a Line Contains

```text
[2026-09-12 14:32:01] | v1.0.0 | gitpr -c | gitpr-cli/gitpr | Nataniel Fiuza <natan.fiuza@gmail.com>
```

| Field | Source | Notes |
| --- | --- | --- |
| Date and time | the local clock, when the command starts | `YYYY-MM-DD HH:MM:SS` |
| Version | the running GitPR version | |
| Command | the program name and the flags exactly as typed | `gitpr -c`, `gitpr-mcp --list` |
| Repository | `remote.origin.url`, reduced to `owner/repo` | `-` outside a repository, or with no origin remote |
| Author | `user.name` and `user.email` from the Git configuration | `-` when Git has no identity configured |

The repository is reduced to its path, whatever the forge: `git@github.com:owner/repo.git`, `https://gitlab.com/group/repo` and `https://dev.azure.com/org/project/_git/repo` become `owner/repo`, `group/repo` and `org/project/repo`.

Every invocation is recorded, including `--help` and the ones that fail. For the MCP server that means its start: `gitpr-mcp` writes one line when the server comes up, not one per tool call.

---

## 3. Turning It Off

`GITPR_SHOW_LOGS` controls it, and it is **on** by default — every install already has the line seeded in `~/.gitpr/.env`.

| Where | How |
| --- | --- |
| The configuration screen | `gitpr config` → **General** → **Save General Logs** |
| The file | `GITPR_SHOW_LOGS=false` in `~/.gitpr/.env` |
| A single run | `GITPR_SHOW_LOGS=false gitpr -c` |

The environment always wins over the file (see [the configuration screen](config-tui.md) §2), so the last row disables that one command without touching anything else.

Turning it off stops new lines. It does not delete what is already there.

---

## 4. What It Does Not Record

The log is deliberately thin: it records *that* a command ran and *which* one, and nothing about what it read or produced.

It never contains the diff, file contents, file paths, prompt or skill text, AI responses, the generated commit messages and PR descriptions, or any credential.

The two personal values it does hold — the repository and the Git author — stay on the machine, since the file is local and nothing is transmitted.

---

## 5. Notes for Developers

| File | Role |
| --- | --- |
| `src/usage_log.py` | The whole feature: path derivation, the single git lookup, the line format and the write |
| `src/main.py` | One call at the top of the root callback — the single point every flag, every subcommand and `--help` reaches |
| `src/mcp_server.py` | One call in `main()`, because the `gitpr-mcp` console script never loads `main.py` |

Two guarantees the implementation makes on purpose:

- **The write is synchronous.** A background thread — the way the local metrics recorder does it — loses the entry whenever the process exits before the thread is scheduled, and a log that silently drops commands is worse than no log at all.
- **It can never disturb a command.** Every failure — no git, no permission, no home directory — is swallowed: `log_usage()` returns without writing and the command continues. It also never prints, because the MCP server reserves stdout for its JSON-RPC stream.

Adding a third entry point means adding one call to it. Nothing reaches the log by itself.
