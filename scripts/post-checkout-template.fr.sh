#!/usr/bin/env bash
# GitPR Métriques : hook post-checkout (suivi des changements de contexte)
# Installé automatiquement par: gitpr --installhooks

# Exécuter uniquement lors d'un changement de branche (flag 1)
if [ "$3" != "1" ]; then exit 0; fi

# gitpr enregistre l'événement et résout lui-même le dépôt : parse_repo_ref()
# connaît toutes les forges, là où le bash remplacé ne connaissait que GitHub
# et retombait sur un simple nom de dossier que le dashboard filtrait ensuite.
# `command -v` laisse fonctionner une machine sans gitpr ; `|| true` évite
# qu'un échec du ledger ne fasse échouer votre commande git.

command -v gitpr >/dev/null 2>&1 || exit 0
gitpr --quiet metrics hook-event post-checkout 2>/dev/null || true

exit 0
