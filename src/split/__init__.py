"""The ``gitpr split`` feature: a mixed working tree into atomic commits.

Modules, in dependency order:
  - split_plan.py — the data contract (units, groups, the plan, SplitError)
  - hunk_parser.py — diff text to units and back (pure, never runs git)
  - hunk_grouper.py — the AI call that decides which units belong together
  - generate_split_plan.py — the read-only use case: diff -> plan
  - apply_split_plan.py — the only module here that mutates the repository

Selective staging itself lives in ``src/infrastructure/git/selective_stager``,
beside the ``git apply`` wrapper it is built on, because staging hunks is not a
split concern: it is how anything writes to the index.

Import the submodule you need (``from src.split.generate_split_plan import
generate_split_plan``); this package deliberately re-exports nothing, so that
reading a plan does not drag the git write path in with it.
"""
