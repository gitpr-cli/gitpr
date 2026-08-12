#!/bin/sh
# GitPR Hook - Preenche a mensagem de commit automaticamente com IA

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Cores para o terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Ignora a IA para mensagens geradas pelo git: -m/--file (message), merges (merge),
# squash (squash) e --amend/-c/-C (commit). A mensagem do git prevalece.
case "$COMMIT_SOURCE" in
    message|merge|squash|commit)
        exit 0
        ;;
esac

# Segurança extra: nunca toca na mensagem de merge, mesmo com uma fonte inesperada
if [ -f .git/MERGE_HEAD ]; then
    exit 0
fi

echo ""
echo -e "${CYAN}🤖 GitPR: A pedir sugestão de commit à IA...${NC}"


# Chama o GitPR repassando o caminho do arquivo ($1) para a nossa nova flag --hook
if command -v gitpr >/dev/null 2>&1; then
    gitpr --commit --quiet --hook "$COMMIT_MSG_FILE"
else
    echo -e "${RED}❌ Aviso: Comando 'gitpr' não encontrado. Prosseguindo sem IA.${NC}"
fi