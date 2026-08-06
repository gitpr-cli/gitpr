#!/bin/sh
# GitPR Hook - Auto-fill commit message with AI

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# If user already passed a manual message with 'git commit -m', skip AI
if [ "$COMMIT_SOURCE" = "message" ]; then
    exit 0
fi

echo ""
echo -e "${CYAN}🤖 GitPR: Requesting AI commit suggestion...${NC}"


# Call GitPR passing the commit file path ($1) to our --hook flag
if command -v gitpr >/dev/null 2>&1; then
    gitpr --commit --quiet --hook "$COMMIT_MSG_FILE"
else
    echo -e "${RED}❌ Warning: 'gitpr' command not found. Proceeding without AI.${NC}"
fi
