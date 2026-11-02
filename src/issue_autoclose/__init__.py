"""The issue-autoclose feature: remember the issue `gitpr -is` created.

Modules, in dependency order:
  - issue_registry.py — the local record at ``.gitpr/conf/github.yml``

Import the submodule you need (``from src.issue_autoclose.issue_registry
import IssueRegistry``). This package deliberately re-exports nothing: the
registry has no network dependency and must stay importable by itself.
"""
