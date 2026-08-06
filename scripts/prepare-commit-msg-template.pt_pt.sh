#!/bin/sh
# Hook GitPR - Preenche a mensagem de commit automaticamente com IA

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Cores do terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Sem Cor

# Se o utilizador já passou uma mensagem manual com 'git commit -m', aborta a IA
if [ "$COMMIT_SOURCE" = "message" ]; then
    exit 0
fi

echo ""
echo -e "${CYAN}🤖 GitPR: A pedir sugestão de commit à IA...${NC}"


# Chama o GitPR passando o caminho do ficheiro ($1) para a nossa flag --hook
if command -v gitpr >/dev/null 2>&1; then
    gitpr --commit --quiet --hook "$COMMIT_MSG_FILE"
else
    echo -e "${RED}❌ Aviso: Comando 'gitpr' não encontrado. Prosseguindo sem IA.${NC}"
fi
