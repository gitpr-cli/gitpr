#!/usr/bin/env bash
# GitPR Metrics: pre-push hook (delivery tracker)
# Installed automatically by: gitpr --installhooks

# gitpr records the event and resolves the repository itself: parse_repo_ref()
# knows every forge, where the bash this replaces only knew GitHub and fell
# back to a bare folder name the dashboard then filtered out. `command -v`
# lets a machine without gitpr keep working; `|| true` keeps a ledger failure
# from failing your git command.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event pre-push 2>/dev/null || true

exit 0
