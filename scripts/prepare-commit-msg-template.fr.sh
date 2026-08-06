#!/bin/sh
# Hook GitPR - Remplit automatiquement le message de commit avec l'IA

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Couleurs du terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Pas de couleur

# Si l'utilisateur a déjà passé un message manuel avec 'git commit -m', annuler l'IA
if [ "$COMMIT_SOURCE" = "message" ]; then
    exit 0
fi

echo ""
echo -e "${CYAN}🤖 GitPR: Demande de suggestion de commit à l'IA...${NC}"


# Appeler GitPR en passant le chemin du fichier ($1) à notre flag --hook
if command -v gitpr >/dev/null 2>&1; then
    gitpr --commit --quiet --hook "$COMMIT_MSG_FILE"
else
    echo -e "${RED}❌ Avertissement: Commande 'gitpr' introuvable. Poursuite sans IA.${NC}"
fi
