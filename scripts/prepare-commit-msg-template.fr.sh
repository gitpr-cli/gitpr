#!/bin/sh
# Hook GitPR - Remplit automatiquement le message de commit avec l'IA

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Couleurs du terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Pas de couleur

# Ignorer l'IA pour les messages générés par git : -m/--file (message), fusions (merge),
# squash (squash) et --amend/-c/-C (commit). Le message de git prévaut.
case "$COMMIT_SOURCE" in
    message|merge|squash|commit)
        exit 0
        ;;
esac

# Sécurité supplémentaire : ne jamais toucher au message de fusion, même avec une source inhabituelle
if [ -f .git/MERGE_HEAD ]; then
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
