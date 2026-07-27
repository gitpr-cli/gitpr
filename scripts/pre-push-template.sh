#!/bin/bash
# GitPR Metrics: pre-push hook
# Logs push events for team telemetry.
# Installed automatically by: gitpr --installhooks

REMOTE=$1
URL=$2

gitpr --hook-event "pre-push" --quiet 2>/dev/null || true

exit 0
