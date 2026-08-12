#!/bin/sh
# Hook GitPR - Rellena el mensaje de commit automáticamente con IA

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Colores del terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Sin color

# Omitir la IA para mensajes generados por git: -m/--file (message), fusiones (merge),
# squash (squash) y --amend/-c/-C (commit). El mensaje de git prevalece.
case "$COMMIT_SOURCE" in
    message|merge|squash|commit)
        exit 0
        ;;
esac

# Seguridad extra: nunca tocar el mensaje de fusión, incluso con una fuente inesperada
if [ -f .git/MERGE_HEAD ]; then
    exit 0
fi

echo ""
echo -e "${CYAN}🤖 GitPR: Solicitando sugerencia de commit a la IA...${NC}"


# Llamar a GitPR pasando la ruta del archivo ($1) a nuestra flag --hook
if command -v gitpr >/dev/null 2>&1; then
    gitpr --commit --quiet --hook "$COMMIT_MSG_FILE"
else
    echo -e "${RED}❌ Aviso: Comando 'gitpr' no encontrado. Continuando sin IA.${NC}"
fi
