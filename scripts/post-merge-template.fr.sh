#!/bin/bash
# GitPR Métriques: hook post-merge
# Enregistre les événements de pull/merge pour la télémétrie d'équipe.
# Installé automatiquement par: gitpr --installhooks

IS_SQUASH=$1

gitpr --hook-event "post-merge" --quiet 2>/dev/null || true

exit 0
