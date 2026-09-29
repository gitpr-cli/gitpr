#!/usr/bin/env bash
# GitPR Métricas: hook post-checkout (rastreador de troca de ramo)
# Instalado automaticamente por: gitpr --installhooks

# Executa apenas se for mudança de ramo (flag 1)
if [ "$3" != "1" ]; then exit 0; fi

# O gitpr grava o evento e resolve o repositório sozinho: parse_repo_ref()
# conhece todas as forges, enquanto o bash que isto substitui só conhecia o
# GitHub e caía para um nome de pasta solto, que o dashboard depois filtrava
# fora. O `command -v` deixa uma máquina sem gitpr continuar a funcionar; o
# `|| true` impede que uma falha do ledger derrube o seu comando git.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event post-checkout 2>/dev/null || true

exit 0
