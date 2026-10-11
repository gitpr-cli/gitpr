# Technical Documentation: Baseline and Auditable Suppressions (`gitpr baseline`)

Adopting GitPR in a legacy repository is the moment the tool is least useful: the linter reports four hundred pre-existing problems, the secret ruleset flags a synthetic key in a test fixture, and the first pull request of the migration fails a gate that has nothing to do with the change in it. The team has two options, and both are bad — turn the gate off, or spend a sprint fixing code nobody is changing.

A **baseline** is the third option. It is a file, committed to Git, that records the findings the repository already has. From then on a run classifies every finding it meets: the ones in the file are **existing**, the ones that were there and are gone are **resolved**, and only what *this change* introduced is **new** — and only `new` blocks. The gate becomes a statement about the diff instead of about the repository's history.

Along with the record comes the audit trail: a suppression is not a silent filter, it is a decision with a **reason**, an author and a date; accepted debt has an **owner** and optionally a **deadline**; and a checksum over the whole file catches an edit made outside GitPR. Everything the tool decides about a finding can be read back and questioned.

Without a baseline file, every command behaves exactly as it did before this feature existed — same output, same exit codes, same cache keys.

---

## 1. Overview

```bash
gitpr baseline create                    # Records the current diff as the baseline
gitpr baseline show                      # The findings, the decisions and the counts
gitpr baseline validate                  # Every defect in the file, exit 1 on any
gitpr baseline update                    # Records what the diff shows today, keeping decisions
gitpr baseline suppress <id> --reason "…"    # A decision about one finding
gitpr baseline unsuppress <id>           # Takes a decision back
```

| Command | Writes | Description |
|---|---|---|
| **`create`** | `.gitpr/baseline.json` | Records the findings of the current diff as the starting point. `--base <ref>` records the diff against a ref instead of the working tree; `--refresh` runs the AI review again instead of reusing the cached one; `--format json` for CI |
| **`show`** | — | Counts by status and lists every finding that carries a decision, with its reason, scope and origin. `--status`, `--rule`, `--file` filter; `--format json` emits the entries |
| **`validate`** | — | Every problem the file and the overrides can have: schema, fingerprint version, compatibility, checksum, duplicate fingerprints, unknown fields, overdue debt. Exit 1 on any of them |
| **`update`** | `.gitpr/baseline.json` | Re-records what the diff shows today, marking what disappeared as `resolved` and keeping every decision. Refuses a file whose checksum diverges unless `--recompute` is given |
| **`suppress`** | the entry, or `.gitpr/baseline.overrides.yml` | Records a decision about one finding. `--reason` is required; `--scope finding\|line\|file\|rule`; `--debt --owner <who> [--due-date YYYY-MM-DD]` records debt instead of a suppression |
| **`unsuppress`** | the entry, or the overrides file | Takes a decision back. A decision wider than the one finding is *reported*, never deleted — it is edited where it lives |

Every writing command accepts `--yes`, which answers the confirmation prompt without skipping the checks behind it. Without a terminal and without `--yes` the command fails with the instruction instead of blocking on a prompt nobody will read.

### 1.1 Finding ids

A finding is named on the command line by a **unique prefix of its fingerprint**, which `show` prints and `suppress` accepts:

```
sha256:ab12cd34ef56…
```

An id that matches no finding, or two findings, is refused — and the refusal says which it was, because the id is the only handle the user has on the finding.

---

## 2. The five statuses

| Status | Meaning | Persisted |
|---|---|---|
| **`new`** | The finding is not in the baseline. It is the whole point of the feature, and the only status that blocks | **never** |
| **`existing`** | The finding is recorded and still there. Nothing is said about whether it is good — it is known | yes |
| **`resolved`** | The finding was recorded and no longer appears, in a file the current diff touches | yes |
| **`ignored`** | A human looked at it and decided it stays, with a reason | yes |
| **`accepted_debt`** | A human decided it will be fixed, with an owner and a stated reason — and optionally a deadline | yes |

`new` is never written to the file: an entry saved as "new" would be stale by the next run, and a file that records its own comparison is a file that lies.

`resolved` is only applied to entries whose **file appears in the current diff**. A file that is not in the diff may be untouched for reasons that have nothing to do with the finding — the diff simply does not reach it — and calling that "resolved" would be a false statement in the one place the team reads as a record. The narrower rule means a shrinking diff never invents a resolution.

---

## 3. What blocks, and what it costs

| Surface | Effect of the baseline |
|---|---|
| `gitpr -l` / `--linter` | Exits 1 only when an **error-level** finding is `new`. Existing, ignored and accepted findings are shown with their status and their reason, and the run continues |
| `gitpr -r`, `-f`, `-i` | The review annotates each finding with its status. The review was never a gate, so no exit code changes |
| `gitpr risk` | Only `new` findings score. Everything else is attached as informational evidence worth **zero points**, with its status in `details`, so the risk number describes the change rather than the repository |
| `gitpr review-pr` | Resolves the policy and the baseline on its own, annotating the linter findings, the risk section and the PR comment |
| Everything else (`-c`, PR description, blame, issue, chat, release, split, fix) | The baseline is not consulted at all |

A destructive warning, an ignored alert or a past deadline never fails a run on their own: an overdue deadline is a warning, printed beside the report.

---

## 4. Configuration

Four variables in `~/.gitpr/.env`, also editable through `gitpr config` in the **Baseline** section:

| Key | Default | Effect |
|---|---|---|
| `GITPR_BASELINE_ENABLED` | `true` | `false` → no run ever reads the baseline; the pre-feature behaviour, byte for byte |
| `GITPR_BASELINE_PATH` | *(empty)* | `.gitpr/baseline.json` by default. A relative path resolves against the repository root — this is how a monorepo or a shared baseline elsewhere is pointed at |
| `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` | `true` | A divergent checksum makes the baseline unusable: the run refuses, prints the instruction and exits non-zero in the flows that block. With it off the file is applied and the divergence is still reported as a warning |
| `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` | `true` | `false` → `.gitpr/baseline.overrides.yml` is not read, with a warning. The decisions written in the baseline file stand alone |

The master switch fails open — only `false`, `0`, `no`, `off` or `n` turn it off.

---

## 5. The file

`.gitpr/baseline.json`, committed with the code:

```json
{
  "schema_version": 1,
  "fingerprint_version": "1",
  "policy_name": "acme/team-policy",
  "policy_version": "1.0.0",
  "gitpr_version": "0.0.37",
  "created_at": "2026-10-10T09:12:44+00:00",
  "updated_at": "2026-10-10T09:12:44+00:00",
  "checksum": "sha256:…",
  "entries": [
    {
      "fingerprint": "sha256:…",
      "rule_id": "sec-aws-key",
      "category": "security",
      "file_path": "tests/fixtures/keys.py",
      "line_start": 18,
      "line_end": 18,
      "severity": "error",
      "source": "linter",
      "status": "ignored",
      "low_confidence": false,
      "first_seen_commit": "a1b2c3d",
      "last_seen_commit": "a1b2c3d",
      "first_seen_date": "2026-10-10",
      "last_seen_date": "2026-10-10",
      "resolved_at": null,
      "suppressed": true,
      "suppression_reason": "Synthetic key in a fixture; never used to reach a service.",
      "suppression_scope": "finding",
      "suppressed_by": "alice",
      "suppressed_at": "2026-10-10",
      "accepted_debt_owner": null,
      "accepted_debt_due_date": null,
      "accepted_debt_reason": null,
      "provenance": {"origin": "local", "command": "baseline suppress", "policy": null}
    }
  ]
}
```

Three properties of the format matter:

1. **No entry holds a message, and none holds code.** The prose a rule emits belongs to the rule — rewording it would look like a baseline change — and the baseline is committed to Git, so persisting the offending line would put the very secret the ruleset flagged into the repository. Only a *digest* of that line is stored.
2. **Entries are written in fingerprint order.** The file is committed, and two runs over the same findings on two machines have to produce the same diff.
3. **The checksum does not cover itself.** It is the SHA-256 of the canonical JSON (sorted keys, no whitespace, entries ordered) of every other field. Editing an entry by hand in an editor — changing a line number, flipping a status — breaks it, and `gitpr baseline validate` names the divergence instead of applying the file.

`gitpr baseline update --recompute` is the sanctioned way to accept a hand-edited file: it rewrites the checksum over the content it finds, so the edit becomes a change in the Git history with a commit behind it, rather than a silent divergence.

---

## 6. The fingerprint

A finding is identified by a SHA-256 over eight lines, in this order:

```
1  FINGERPRINT_VERSION      ("1")
2  rule_identity            the rule id, or "category:<category>" when there is none
3  category                 lowercased
4  normalize_path           repo-relative, forward slashes, lowercase
5  source                   linter | ai | external | …
6  line_start
7  line_end
8  snippet_hash             digest of the offending line, whitespace collapsed
```

Deliberately **not** in the payload: the message, the timestamp, the provider and the model, the branch, the absolute path of the checkout. Two runs over the same revision produce the same fingerprint on any machine, and a build on a different path changes nothing.

What this means in practice:

| Change | Effect |
|---|---|
| The rule's message is reworded | Same fingerprint — a message is not an identity |
| The line is re-indented or spaced differently | Same fingerprint — whitespace is collapsed before hashing |
| The line's content changes | **New fingerprint** — a different line is a different finding |
| A line is inserted above the finding, shifting it down | **New fingerprint** — line numbers are part of the identity |
| The file is renamed | **New fingerprint** — the path is part of the identity |
| The analysis runs on another machine, another branch, another provider | Same fingerprint |
| The finding comes from the AI and carries no rule id | Identity falls back to the category, and `low_confidence` is set to `true` on the entry |

The bias towards `new` is deliberate. A false `new` is visible in the report and cured in one command (`gitpr baseline update`); a false `existing` would silence a finding that is not the same finding at all — and the one it would silence could be a real secret. The line numbers are in the payload for the same reason.

`FINGERPRINT_VERSION` is the **first** line of the payload, so changing the algorithm changes every fingerprint at once, invalidating every baseline on purpose — a migration rather than a silent reinterpretation. The manifest records the version it was written with, and a file written under another version is refused with the instruction.

---

## 7. Decisions: suppressions and accepted debt

A decision is recorded in one of two places, from narrowest to widest:

1. **On the entry** — a `finding`-scope suppression, or accepted debt. One fingerprint, one finding.
2. **In `.gitpr/baseline.overrides.yml`** — everything wider: a rule, a file, a range of lines. This file is additive and hand-editable, and it is where a team states a policy about a *class* of findings.

```yaml
overrides:
  suppressions:
    - fingerprint: "sha256:…"
      scope: finding
      reason: "Synthetic key in a fixture; never used to reach a service."
      by: "alice"
      date: "2026-10-10"
    - scope: rule
      rule_id: "warning-todo-fixme"
      reason: "The rule is a decision aid, not a gate, in this legacy tree."
    - scope: file
      rule_id: "php-tabs"
      file_path: "app/Legacy/*"
      reason: "Generated files, rewritten on every migration."
    - scope: line
      rule_id: "php-tabs"
      file_path: "app/Old.php"
      line_start: 100
      line_end: 120
      reason: "Legacy block being migrated this quarter."
  accepted_debt:
    - fingerprint: "sha256:…"
      owner: "time-backend"
      reason: "Migration planned for the next quarter."
      due_date: "2026-12-31"
```

| Scope | Reaches | Notes |
|---|---|---|
| `finding` | One exact fingerprint | The narrowest, and the only one recorded on the entry itself |
| `line` | A rule, in one file, inside a line range that **contains** the finding's range | Ignores the content digest, so it survives edits inside the block — which is why it always demands a reason |
| `file` | A rule, in one file or path glob | The same idea the linter already has in `ignore_paths` |
| `rule` | A rule, everywhere in the repository | The widest |

The most specific match wins and supplies the reason shown to the reader. Two invariants are enforced in code rather than by configuration:

- A suppression has a **non-empty reason**. A decision nobody explained is not a decision; it is a filter.
- Accepted debt has an **owner**. A debt nobody owns is not accepted, it is forgotten.

A deadline is optional. A **past** deadline is a warning printed beside the report and a problem for `gitpr baseline validate` — never a failure of the run itself.

A third layer exists that the repository does not write: an active **Policy Pack** may carry a `baseline:` block of its own (see `docs/policy-packs.md`). Those decisions are applied in memory during classification, displayed with the origin `policy:<name>@<version>`, and never written into `.gitpr/baseline.json` — the pack is a shared opinion, the file is the repository's own record. `gitpr baseline unsuppress` will not delete one: it says which pack holds it instead.

---

## 8. The workflow on a legacy repository

```bash
# 1. On the migration branch, record what is already there.
gitpr baseline create --yes

# 2. Commit the record with the code it describes.
git add .gitpr/baseline.json && git commit -m "chore: record the baseline"

# 3. Work. Only what the change introduces is new.
gitpr -l
gitpr -r
gitpr risk
```

The record is reviewed like any other file. What a reviewer looks for:

| In the diff | Reading |
|---|---|
| A new entry with `status: "existing"` and no decision | The author acknowledged a pre-existing finding. Normal, but if the count grows by hundreds in one commit, the baseline was probably recorded against the wrong ref |
| A new entry with `suppressed: true` and a `suppression_reason` | A decision. The reason is the thing under review — a reason that restates the rule ("it's noisy") explains nothing; a reason that states the situation ("generated file, rewritten by the migration") is auditable |
| A new entry with `accepted_debt_owner` | Debt someone owns, with a deadline that `gitpr baseline validate` will check |
| `.gitpr/baseline.overrides.yml` adding a `rule` or `file` scope | The widest kind of change in the repository's posture. It silences a class of findings, not one |
| Entries flipping to `status: "resolved"` | Good news, and cheap to verify: the finding is gone from a file the diff touches |
| The `checksum` changing with nothing else | Nothing else was touched — but an edit next to it would have been caught |

The `.gitpr/baseline.json` and `.gitpr/baseline.overrides.yml` paths are in `templates/gitpr.smart-excludes.json`: they are records, not code, and they are never sent to the AI as part of a diff.

`create` has no dry run: it writes the record and `gitpr baseline show` reads it back, which is the preview. To record a diff against another ref, `create --base <ref>` and `risk --base <ref>` are the pair that has to agree — a baseline recorded from `HEAD` classifies almost everything as `new` when the risk run asks about a branch.

---

## 9. Reading it from an IDE agent (MCP)

The MCP server exposes the record read-only, so an agent can ask what the repository already knows before it reads a report:

| Surface | What it answers |
|---|---|
| Tool `get_baseline_status` | The digest as JSON: entries per status, the noisiest rules, the decisions by origin and scope, the accepted debt with owner and deadline, the late debt, and the checksum state |
| Resource `baseline://summary` | The same digest, as a resource |

Both return `baseline_summary()`, which opens the file, counts what is in it and stops: no linter, no AI call, no policy resolution, no write. A file that cannot be applied is *reported* — `usable: false` with the `problems` that explain it — never raised, because "the record is there and the gate would refuse it" is one of the answers the caller came for. The digest reads the same layers the gate reads, so `.gitpr/baseline.overrides.yml` and the active pack's `baseline:` block are reflected in its counts.

`counts.new` is always `0`, and the answer says why in `counts_note`: `new` is the result of comparing a run against the record, not something a file can hold.

---

## 10. Limits, stated plainly

- **A moved line is a new finding.** Deliberate, and explained above. `gitpr baseline update` re-records it; the record keeps the `first_seen_date` of what it recognises.
- **A finding the AI reported is low-confidence.** It has no rule id, so its identity is its category and its location — two different problems on the same line, reported by two different review runs, are one identity to the baseline. The entry says `low_confidence: true` so the reader can weigh it.
- **The map-reduce path has no findings.** For a diff too large to review in one call, the AI answers in prose, and prose has no findings to record; `create` says how many came from the AI review so the difference is visible.
- **`create` reads the cached review only when the diff matches.** The cache keys a review by its prompt, so `create` checks the `diff` the review was made from against the current one; a mismatch is reported and the review is not consulted.
- **There is no `gitpr check`, and no SARIF export.** The baseline is JSON and is consumable by anything that reads JSON; a first-class CI gate and a SARIF surface are not part of this feature.
- **The baseline is never sent to the AI.** Classification happens after the model answered, over its structured output. Nothing about the record reaches a prompt.

---

## 11. Related reading

- `docs/policy-packs.md` — the `baseline:` block a pack may carry, and how a dependency pack's decisions are attributed to it
- `docs/mcp-integration.md` — the MCP server, the `get_baseline_status` tool and the `baseline://summary` resource
- `docs/linter-regras-customizadas.md` — the linter rules a finding is fingerprinted from
- `docs/config-tui.md` — the configuration screen the four variables live in
- `docs/plans/ADR-012-baseline-suppressions.md` — why the fingerprint hashes the line's content, why `new` is never persisted, and why a pack's layer is in memory
