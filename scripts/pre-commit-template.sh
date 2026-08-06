#!/bin/sh
# GitPR Linter Hook - Pre-commit validation

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🔍 GitPR: Validating static analysis rules...${NC}"


# Try to run the command.
# Check if the global binary/pip package 'gitpr' is installed
if command -v gitpr >/dev/null 2>&1; then
    gitpr --linter --quiet
else
    echo -e "${RED}❌ Error: 'gitpr' command not found.${NC}"
    echo "Make sure GitPR is installed via pip (pip install gitpr-cli) or the executable is in your PATH."
    exit 1
fi

# 2. Capture the exit code
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo -e "${RED}🚨 COMMIT BLOCKED!${NC}"
    echo "The Linter found code violations that need fixing."
    echo "Tip: To force the commit (not recommended), use: git commit --no-verify"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Code approved! Finishing commit...${NC}"
exit 0
