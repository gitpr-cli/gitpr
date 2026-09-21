"""The ``gitpr fix`` feature: turn a review finding into a reviewable patch.

Modules, in dependency order:
  - patch_provenance.py — the data contract (safety classes, candidates, results)
  - patch_extractor.py — reading the code an AI hands back (shared with the chat)
  - patch_safety_classifier.py — SAFE / REVIEW_REQUIRED / EXPERIMENTAL, pure logic
  - patch_applier.py — re-export shim; the git wrapper moved to src/infrastructure/git/
  - fix_history.py — the applied-patch record that makes --rollback deterministic
  - apply_fix.py — the use case: review -> AI findings -> classify -> dry-run/apply
  - rollback_fix.py — the use case that undoes an applied patch

Import the submodule you need (``from src.fix.apply_fix import apply_fix``); this
package deliberately re-exports nothing, because the chat imports
``src.fix.patch_extractor`` on every session and must not drag the AI and git
layers in with it.
"""
