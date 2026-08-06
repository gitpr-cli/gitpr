#!/bin/bash
# GitPR Métricas: hook post-merge
# Registra eventos de pull/merge para telemetría del equipo.
# Instalado automáticamente por: gitpr --installhooks

IS_SQUASH=$1

gitpr --hook-event "post-merge" --quiet 2>/dev/null || true

exit 0
