#!/usr/bin/env bash
# GitPR Métricas: hook post-merge (eventos de pull/merge)
# Instalado automáticamente por: gitpr --installhooks

# gitpr registra el evento y resuelve el repositorio por sí mismo:
# parse_repo_ref() conoce todas las forges, mientras que el bash que esto
# reemplaza solo conocía GitHub y caía a un nombre de carpeta suelto, que el
# dashboard luego filtraba fuera. `command -v` deja seguir funcionando a una
# máquina sin gitpr; `|| true` evita que un fallo del ledger tumbe tu git.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event post-merge 2>/dev/null || true

exit 0
