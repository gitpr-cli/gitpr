#!/bin/sh
# Hook Linter GitPR - Validation pré-commit

# Couleurs du terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Pas de couleur

echo -e "${CYAN}🔍 GitPR: Validation des règles d'analyse statique...${NC}"


# Essayer d'exécuter la commande.
# Vérifier si le binaire/paquet global 'gitpr' est installé
if command -v gitpr >/dev/null 2>&1; then
    gitpr --linter --quiet
else
    echo -e "${RED}❌ Erreur: Commande 'gitpr' introuvable.${NC}"
    echo "Assurez-vous que GitPR est installé via pip (pip install gitpr-cli) ou que l'exécutable est dans votre PATH."
    exit 1
fi

# 2. Capturer le code de sortie
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo -e "${RED}🚨 COMMIT BLOQUÉ!${NC}"
    echo "Le Linter a trouvé des violations de code qui doivent être corrigées."
    echo "Astuce: Pour forcer le commit (non recommandé), utilisez: git commit --no-verify"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Code approuvé! Finalisation du commit...${NC}"
exit 0
