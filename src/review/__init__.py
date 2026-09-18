"""The ``gitpr review-pr`` feature: review a pull request already open on the forge.

Modules, in dependency order:
  - diff_source.py — where a review diff came from (DiffOrigin, DiffSource)
  - diff_normalizer.py — smart excludes for a diff git never saw (pure)
  - render.py — composes and writes the review artefact (shared with -r/-f)
  - remote_pr.py — the use case: resolve PR -> fetch diff -> review -> (comment)

Import the submodule you need (``from src.review.remote_pr import
review_remote_pr``); this package deliberately re-exports nothing, following
``src/fix/`` — the local review flows import ``render`` and must not drag the
SCM and AI layers in with it.
"""
