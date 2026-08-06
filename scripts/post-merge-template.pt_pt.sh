#!/bin/bash
# GitPR Métricas: hook post-merge
# Regista eventos de pull/merge para telemetria da equipa.
# Instalado automaticamente por: gitpr --installhooks

IS_SQUASH=$1

gitpr --hook-event "post-merge" --quiet 2>/dev/null || true

exit 0
