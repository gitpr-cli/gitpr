# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat(badge): add automatic PR badge and README snippet command
```

---

## 🎯 Summary

GitPR now ships a public badge that proves a pull request passed a local quality check, and gives projects a way to advertise that on their own README.

The motivation is trust at the point of publication: a PR body written by an AI is indistinguishable from one written by hand, and the diff's linter findings were previously visible only to the author, in a terminal that scrolled away. The badge turns that private signal into a visible, verifiable claim on the published request itself. It is deliberately a static shields.io URL — GitPR never fetches it — so publishing a pull request can never depend on a third party being reachable.

The badge is enabled by default, because a feature that only appears after configuring a variable is a feature nobody discovers, and disclosed at the moment it becomes possible (the SCM init wizard) with the exact switch that turns it off.

## 🛠️ Technical Changes

- **New `src/branding/` package** — `badge_builder.py` composes the shields.io Markdown (escaping, colour rule, style normalisation) and idempotently appends it to a PR body; `badge_data.py` counts linter alerts.
- **Honest measurement only** — `collect_linter_counts()` returns `None` when no linter rules are configured (run `gitpr --skill`), because empty alert lists mean "nothing was checked", not "nothing was found". A green badge over an unchecked diff would be a claim GitPR cannot back. The external linter bridge is skipped: it inspects the working tree, not the revision under review.
- **Badge never blocks a publish** — every failure path in the data collection is caught and degrades to no badge.
- **Single injection point** — `attach_pr_badge()` runs in `src/main.py` right after `pr_data` is complete, so both publishers (the TUI text area and `--no-edit`) read the badge from one place. The user sees it and can delete it before sending.
- **Idempotent append** — a republish or a user-moved badge is detected via a marker and left alone; no stacked badges.
- **New `gitpr badge` command** — prints the adoption snippet for a README (`--readme` for the pipe-friendly bare form, `--style` for `flat`/`flat-square`/`for-the-badge`). It only prints; the README is never modified.
- **Disclosure** — the init wizard announces the automatic badge on the PR path, and `--no-edit` prints a line naming what went into the body the user never saw.
- **i18n** — 11 new keys added to `es`, `es_es`, `fr`, `fr_fr`, `pt_br` and `pt_pt`; dictionary version bumped to `v0.0.30`.
- **Tests** — a new `tests/badge` suite covering the builder, data collection, CLI, opt-out, publish paths and an offline guard (autouse network ban, except loopback for the Windows proactor event loop); the demo runner and init wizard suites were extended.
- **Demo tour** — the PR step now shows the badge a real publish would attach, counted from the scenario's own recorded linter block so no rule is read and no diff is linted.
- **Metrics export samples** — a CSV/JSON pair under `.gitpr/metrics/export/` showing the export format.

## ⚠️ Impact/Warnings

- **New environment variable:** `GITPR_BADGE` (default `true`). It is a read-only opt-out — GitPR never auto-writes it to `~/.gitpr/.env`. It is also exposed in the config schema under the `general` category.
- **Behaviour change:** published PR bodies now carry a footer badge by default. Anyone who does not want it must set `GITPR_BADGE=false`; the wizard says so once, and `--no-edit` announces it per publish.
- **New CLI surface:** the `gitpr badge` command, documented at `docs/badge.md`. It writes nothing to disk.
- **Language dictionary version bumped to `v0.0.30`** — stale local language packs will be refreshed.
- **No database migrations, no new runtime dependencies.** The badge is pure string composition against `img.shields.io`.
- **Test-only note:** the `tests/badge` suite neutralises the linter's local metric logging so runs do not write into the developer's `~/.gitpr/metrics`.

close #179
---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)