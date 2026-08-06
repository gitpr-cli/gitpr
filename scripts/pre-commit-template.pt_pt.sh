#!/bin/sh
# Hook Linter do GitPR - Validação de pré-commit

# Cores do terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # Sem Cor

echo -e "${CYAN}🔍 GitPR: A validar regras de análise estática...${NC}"


# Tenta executar o comando.
# Verifica se o binário/pacote global 'gitpr' está instalado
if command -v gitpr >/dev/null 2>&1; then
    gitpr --linter --quiet
else
    echo -e "${RED}❌ Erro: Comando 'gitpr' não encontrado.${NC}"
    echo "Certifique-se de que o GitPR está instalado via pip (pip install gitpr-cli) ou que o executável está no seu PATH."
    exit 1
fi

# 2. Captura o código de saída
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo -e "${RED}🚨 COMMIT BLOQUEADO!${NC}"
    echo "O Linter encontrou violações de código que precisam de correção."
    echo "Dica: Para forçar o commit (não recomendado), use: git commit --no-verify"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Código aprovado! A finalizar commit...${NC}"
exit 0
