#!/usr/bin/env bash
# GitPR: Post-Checkout Telemetria (Rastreador de troca de contexto)

# Executa apenas se for mudança de ramo (flag 1)
if [ "$3" != "1" ]; then exit 0; fi

PREV_BRANCH=$(git name-rev --name-only "$1" 2>/dev/null || echo "detached")
NEW_BRANCH=$(git name-rev --name-only "$2" 2>/dev/null || echo "detached")

if [ "$PREV_BRANCH" = "$NEW_BRANCH" ]; then exit 0; fi

REPO=$(git config --get remote.origin.url | grep -o 'github\.com[:/][^.]*' | sed 's/github.com[:/]//' || basename -s .git `git config --get remote.origin.url` || echo "local_repo")
OWNER=$(echo "$REPO" | cut -d'/' -f1)
if [ -z "$OWNER" ]; then OWNER=$(git config user.name | tr ' ' '_'); fi
if [ -z "$OWNER" ]; then OWNER="local_user"; fi

METRICS_DIR="$HOME/.gitpr/metrics/$OWNER/git"
mkdir -p "$METRICS_DIR"

UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || date +%s%N)
DATE_STR=$(date +'%Y-%m-%dT%H:%M:%S')
FILE_PATH="$METRICS_DIR/${UUID}_post-checkout.json"

cat <<EOF > "$FILE_PATH"
{
  "timestamp": "$DATE_STR",
  "command": "git_checkout",
  "status": "success",
  "repo": "$REPO",
  "previous_branch": "$PREV_BRANCH",
  "current_branch": "$NEW_BRANCH",
  "provider": "git_hook"
}
EOF
