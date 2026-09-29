#!/usr/bin/env bash
# GitPR Métricas: hook pre-push (rastreador de entregas)
# Instalado automaticamente por: gitpr --installhooks

# O gitpr grava o evento e resolve o repositório sozinho: parse_repo_ref()
# conhece todas as forges, enquanto o bash que isto substitui só conhecia o
# GitHub e caía para um nome de pasta solto, que o dashboard depois filtrava
# fora. O `command -v` deixa uma máquina sem gitpr seguir funcionando; o
# `|| true` impede que uma falha do ledger derrube o seu comando git.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event pre-push 2>/dev/null || true

exit 0
