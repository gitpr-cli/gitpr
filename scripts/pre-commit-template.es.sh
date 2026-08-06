#!/bin/sh
# Hook Linter de GitPR - Validación pre-commit

# Colores del terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Sin color

echo -e "${CYAN}🔍 GitPR: Validando reglas de análisis estático...${NC}"


# Intentar ejecutar el comando.
# Verificar si el binario/paquete global 'gitpr' está instalado
if command -v gitpr >/dev/null 2>&1; then
    gitpr --linter --quiet
else
    echo -e "${RED}❌ Error: Comando 'gitpr' no encontrado.${NC}"
    echo "Asegúrese de que GitPR esté instalado via pip (pip install gitpr-cli) o que el ejecutable esté en su PATH."
    exit 1
fi

# 2. Capturar el código de salida
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo -e "${RED}🚨 ¡COMMIT BLOQUEADO!${NC}"
    echo "El Linter encontró violaciones de código que necesitan corrección."
    echo "Consejo: Para forzar el commit (no recomendado), use: git commit --no-verify"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ ¡Código aprobado! Finalizando commit...${NC}"
exit 0
