#!/usr/bin/env bash
# GitPR Metrics: post-checkout hook (context switch tracker)
# Installed automatically by: gitpr --installhooks

# Only run on branch switch (flag 1)
if [ "$3" != "1" ]; then exit 0; fi

# gitpr records the event and resolves the repository itself: parse_repo_ref()
# knows every forge, where the bash this replaces only knew GitHub and fell
# back to a bare folder name the dashboard then filtered out. `command -v`
# lets a machine without gitpr keep working; `|| true` keeps a ledger failure
# from failing your git command.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event post-checkout 2>/dev/null || true

exit 0
