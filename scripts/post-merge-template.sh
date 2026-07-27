#!/bin/bash
# GitPR Metrics: post-merge hook
# Logs pull/merge events for team telemetry.
# Installed automatically by: gitpr --installhooks

IS_SQUASH=$1

gitpr --hook-event "post-merge" --quiet 2>/dev/null || true

exit 0
