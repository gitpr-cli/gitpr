#!/usr/bin/env bash
# GitPR Métriques : hook pre-push (suivi des livraisons)
# Installé automatiquement par: gitpr --installhooks

# gitpr enregistre l'événement et résout lui-même le dépôt : parse_repo_ref()
# connaît toutes les forges, là où le bash remplacé ne connaissait que GitHub
# et retombait sur un simple nom de dossier que le dashboard filtrait ensuite.
# `command -v` laisse fonctionner une machine sans gitpr ; `|| true` évite
# qu'un échec du ledger ne fasse échouer votre commande git.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event pre-push 2>/dev/null || true

exit 0
