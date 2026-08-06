#!/usr/bin/env bash
# GitPR: Pre-Push Telemetria (Rastreador de entregas)

REMOTE="$1"
REPO=$(git config --get remote.origin.url | grep -o 'github\.com[:/][^.]*' | sed 's/github.com[:/]//' || basename -s .git `git config --get remote.origin.url` || echo "local_repo")
OWNER=$(echo "$REPO" | cut -d'/' -f1)
if [ -z "$OWNER" ]; then OWNER=$(git config user.name | tr ' ' '_'); fi
if [ -z "$OWNER" ]; then OWNER="local_user"; fi

METRICS_DIR="$HOME/.gitpr/metrics/$OWNER/git"
mkdir -p "$METRICS_DIR"

UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || date +%s%N)
DATE_STR=$(date +'%Y-%m-%dT%H:%M:%S')

COMMIT_COUNT=0
while read local_ref local_sha remote_ref remote_sha; do
    if [ "$local_sha" != "0000000000000000000000000000000000000000" ] && [ "$remote_sha" != "0000000000000000000000000000000000000000" ]; then
        COUNT=$(git rev-list --count $remote_sha..$local_sha 2>/dev/null || echo 0)
        COMMIT_COUNT=$((COMMIT_COUNT + COUNT))
    fi
done

FILE_PATH="$METRICS_DIR/${UUID}_pre-push.json"

cat <<EOF > "$FILE_PATH"
{
  "timestamp": "$DATE_STR",
  "command": "git_push",
  "status": "success",
  "repo": "$REPO",
  "commits_pushed": $COMMIT_COUNT,
  "remote": "$REMOTE",
  "provider": "git_hook"
}
EOF
