#!/bin/bash
# GitPR Metrics: post-checkout hook
# Logs branch switch events for team telemetry.
# Installed automatically by: gitpr --installhooks

PREV_HEAD=$1
NEW_HEAD=$2
BRANCH_SWITCH=$3

# Only log actual branch switches (not file checkouts)
if [ "$BRANCH_SWITCH" = "1" ]; then
    FROM_BRANCH=$(git name-rev --name-only "$PREV_HEAD" 2>/dev/null || echo "unknown")
    TO_BRANCH=$(git name-rev --name-only "$NEW_HEAD" 2>/dev/null || echo "unknown")
    gitpr --hook-event "post-checkout" --quiet 2>/dev/null || true
fi
